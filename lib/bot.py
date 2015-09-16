import time
import threading

from config.config import config
from lib.irc import Irc
from lib.game import Game
from lib.comQueue import comQueue
from os import system
from queue import *
import random
import configparser
#from lib.misc import pbutton

#Threadsafeness: is a big concern in this project, because of the use of multithreading and the potential for high loads, etc. This comment is a discussion of some aspects of the implementation here and things to watch out for:

#Generally speaking, there are two threads here, the while loop directly under self.run that handles irc tasks and places commands from irc into the curQueue command storage object, and the while loop that is labeled def self.CommandQueue, which handles the execution of commands and the output to the stream command window. This is done to minimize the overhead on the thread that handles irc tasks, preventing timeout etc. as much as possible.

#threadsafeness here is maintained by the use of only Atomic Operations on instances or objects that are used by both threads. This is monitored with the observation that the irc thread should be kept AS SMALL AS POSSIBLE, and any additions to it should be viewed with skepticism. Besides keeping the irc working optimally, this also has the advantage of minimizing the resources shared by it, so that threadsafeness can be achieved by keeping a careful eye on those few resources from self used by the irc thread, which are listed here:

#self.irc: Only used by the irc thread, and should never be touched elsewhere

#self.game.is_valid_command: Checks input beforehand to keep a handle on the size of curQueue. By design the methods of the game object never modify its attributes and are on their own threadsafe, with the exception of is_valid_command and is_valid_button, which *should* be safe. However for safety it is only ever called in the irc thread and should not be called elsewhere if avoidable.

#self.demVoteRatio and self.botConfig['demvotepool']: This is delicate, because it could be handled outside of the irc thread, but handling it here helps to control the size of self.curQueue. Modifying this value should be avoided elsewhere if at all possible.

#self.curQueue.addCom(): Not a concern. The Queue object is designed to be threadsafe; here it is embedded into the comQueue() object type, whose methods are assumed to be threadsafe for the purposes of this object; discussion of comQueue threadsafeness is contained in the corresponding py file. Note that by design comQueue will drop commands if it detects lag under high load. In any case addCom() is (within the comQueue class) a one-line call to a method in the Queue class, and is threadsafe if the python designers did their jobs correctly.

#Besides this, many configuration attributes are of course implicitly used by these functions. These are static *most* of the time, but the function readConfigText checks the values in an ini thread every 60 seconds to allow for "hot" changing of some stream configuration properties. This carries obvious risks, and consequently readConfigText is coded CAREFULLY, and these configuration values should never be modified elsewhere.

#Additional threadsafing commentary is contained in the Command thread. and readConfigText.

class Bot:
    voteLength=5 #Number of votes to show
    bufferLength=5 #Number of recent commands to show
    commandDisplayLength=21 #max number of characters visible on command screen

    def __init__(self):
        self.config = config
        self.irc = Irc(config)
        self.game = Game()
        self.extConfig=configparser.ConfigParser()
        self.readConfigText() #read in config file
        self.message_buffer = []
        self.curQueue=comQueue() #Based on Queue object, and therefore threadsafe
        self.queueStatus="Nominal"
        self.lastButton=""
        self.voteCount={}
        self.lastPushed=""
        self.voteItems=self.voteCount.items() #Dynamically changing list in python 3 that keeps up with voteCount
        self.democracy=True #Anarchy is default on.
        self.game.democracy=self.democracy #Command processor needs this information due to slightly different processing in democracy vs. anarchy
        self.demVoteRatio=50 #50/50 at the start
        self.lastConfigTime=time.time() #Timer on config file updates
        self.configUpdateFreq=60 #config file updates every 60 seconds
        
    def readConfigText(self): #the operations performed are threadsafe (attributes changed are either only ever changed here, or changed in one atomic operation)
        try:
            self.extConfig.read(self.config['configPath']) #Note that nothing from extConfig is directly accessed by any other function.
        except:
            return #In case of read fail of some sort. In principle, this should throw a warning, but for the stream I don't want errors going to stdout, and it will not matter unless I try to edit the .ini and it somehow causes a permanent failure of the read (i.e. I messed up the formatting). By design, the stream will continue to run based on the old configuration; hopefully I will notice that the changes are not taking effect. Best practice would be to output the causative error to a log file; that can be implemented later if necessary
        tempkeymap=dict(self.extConfig['Keymap'])
        for sub in tempkeymap.keys():
            tempkeymap[sub] = int(tempkeymap[sub],16) #convert from the hex to integer
        self.game.keymap=tempkeymap #Note that the operations above are performed separately before being placed in the self object; this is for threadsafeness. This is an atomic operation.
        self.game.macros=dict(self.extConfig['Macros']) #this is okay because it doesn't get changed after this. This is an atomic operation.
        tempbotconfig=dict(self.extConfig['Bot'])
        for sub in tempbotconfig.keys():
            tempbotconfig[sub] = float(tempbotconfig[sub])
        self.botConfig=tempbotconfig #Note that the operations above are performed separately before being placed in the self object; this is for threadsafeness. This is an atomic operation.
        tempgameconfig=dict(self.extConfig['Game'])
        for sub in tempgameconfig.keys():
            tempgameconfig[sub] = float(tempgameconfig[sub])
        self.game.gameConfig=tempgameconfig #Note that the operations above are performed separately before being placed in the self object; this is for threadsafeness. This is an atomic operation.
        

    def update_message_buffer(self, message):
        self.message_buffer.append(message)
        if len(self.message_buffer)>self.bufferLength:
            self.message_buffer.pop(0)
        
    def update_message(self,timeleft):
        system('cls')
        demvoteper=round(self.demVoteRatio) #minimizing the number of times this attribute gets read, in case it changes midway #demVoteRatio is only read, not modified. #
        if self.democracy:
            votes=self.sortVote() #It's inefficient to do this every time, yes, but the alternative is to implement a custom sorted value hashmap, and I hope that's not necessary...
            print ('\n\n')
            print ('Democracy: '+str(demvoteper)+'%\nAnarchy: '+str(100-demvoteper)+'%\n\nDemocracy!\nTime Remaining: '+str(int(timeleft))+' s\nLast Pushed: '+self.lastPushed+'\n')
            if votes:
                print ('Top Votes:\n')
                for y in votes[0:min(len(votes),self.voteLength)]: #show at most 5 votes
                    print (str(y[1])+" "+y[0])
                print ('\n')
            for y in self.message_buffer:
                print (y)
        else:
            print ('\n\n')
            print ('Democracy: '+str(demvoteper)+'%\nAnarchy: '+str(100-demvoteper)+'%\n\nAnarchy!\n')
            for y in self.message_buffer:
                print (y)
    
    def commandQueue(self):    
        while True:
            #update config file if necessary...see readConfigText regarding threadsafeness
            if time.time()-self.lastConfigTime>self.configUpdateFreq:
                self.readConfigText() #Only place this should ever get called
                self.lastConfigTime=time.time()
            #Toggles Anarchy/Democracy state
            demvoteper=self.demVoteRatio #minimizing the number of times this attribute gets read, in case it changes midway due to the other thread #demVoteRatio is only read, not modified.
            if self.democracy and demvoteper<100-self.botConfig['votethresh']: #Note that the attribute changes here are all atomic operations and threadsafe
                self.democracy=False
                self.game.democracy=False
            elif not self.democracy and demvoteper>self.botConfig['votethresh']:
                self.democracy=True
                self.game.democracy=True
            if self.democracy: #this is Democracy
                lastvotetime=time.time()
                self.queueStatus="Adding Votes"
                while time.time()-lastvotetime<self.botConfig['votetime']: #collect commands for votetime seconds
                    self.update_message(self.botConfig['votetime']-time.time()+lastvotetime)
                    comList,userList=self.curQueue.getCom()
                    self.lastButton=comList
                    timetaken=time.time()
                    index=0;
                    for button in comList:
                        username=userList[index]
                        index +=1
                        self.queueStatus="Adding Votes"
                        
                        self.addVote(button)
                        userLength=self.commandDisplayLength-len(button)-2
                        printusername=username
                        if len(username)>userLength:
                            printusername=username[0:userLength-3]+'...'
                        self.update_message_buffer(printusername+': '+button)
                        #pbutton(self.message_buffer)
                    if time.time()-timetaken<self.botConfig['checktime']: #don't check more frequently than once every 0.1
                        self.queueStatus="Sleeping"
                        time.sleep(self.botConfig['checktime'])
                self.queueStatus="Running Command"
                vote=self.topVote() #running the command after votetime seconds
                if vote:
                    self.lastPushed=vote
                    words=vote.split("+") #input-time check should have already made sure it's a valid command
                    for y in words:
                        try:
                            self.game.push_button(y)
                        except:
                            time.sleep(0.01) #this is just to fill this catch block. It's bad, yes.
                        time.sleep(.15)
                    self.clearVote()
                self.update_message(0)
            else: #this is Anarchy
                self.queueStatus="Pushing buttons"
                self.update_message(0)
                comList,userList=self.curQueue.getCom()
                self.lastButton=comList
                timetaken=time.time()
                index=0;
                for button in comList:
                    username=userList[index]
                    index +=1
                    words=button.split("+") #input-time check should have already made sure it's a valid command
                    
                    for y in words:
                        if y in self.config['throttled_buttons']:
                            if time.time() - throttle_timers[y] < self.config['throttled_buttons'][y]:
                                continue

                            throttle_timers[y] = time.time()
                        try: #Just in case of weird edge case
                            self.game.push_button(y)
                        except:
                            time.sleep(0.01) #this is just to fill this catch block. It's bad, yes.
                        time.sleep(.05) #Anarchy is a bit more jumpy than Democracy
                    userLength=self.commandDisplayLength-len(button)-2
                    printusername=username
                    if len(username)>userLength:
                        printusername=username[0:userLength-3]+'...'
                    self.update_message_buffer(printusername+': '+button)
                if time.time()-timetaken<self.botConfig['checktime']: #don't check more frequently than once every 0.1
                    self.queueStatus="Sleeping"
                    time.sleep(self.botConfig['checktime'])
                    
    def addVote(self,vote):
        if vote in self.voteCount:
            self.voteCount[vote]=self.voteCount[vote]+1
        else:
            self.voteCount[vote]=1
            
    def topVote(self): #Gets top vote, applying rng to choose among ties
        top=[k for k,v in self.voteItems if v == max(self.voteCount.values())]
        if not top:
            return None
        return random.choice(top)
            
    def sortVote(self):
        sortedItems=sorted(self.voteItems,key=lambda tup: tup[1], reverse=True) #sort using the values, biggest to smallest
        return sortedItems
        
    def clearVote(self):
        self.voteCount.clear()
        
    def run(self):
        #print("New Version!")
        throttle_timers = {button:0 for button in config['throttled_buttons'].keys()}
        t=threading.Thread(target=self.commandQueue, args=()) 
        t.daemon=True
        t.start()
        
        while True: #For threadsafeness see discussion at the top of this file
            #print(self.queueStatus)
            #print(self.lastButton)
            #print(self.curQueue.getStatus())
            #print("Checking for new messages")
            new_messages = self.irc.recv_messages(1024)
            
            if not new_messages:
                continue

            for message in new_messages: 
                button = message['message'].lower()
                username = message['username'].lower()
                words = button.split(" ") #basic input cleanup
                button=words[0]
                
                #Anarchy/Democracy vote
                if button=='democracy':
                    self.demVoteRatio=min(100,self.demVoteRatio+self.botConfig['demvotepool']) #mmm signed values
                elif button=='anarchy':
                    self.demVoteRatio=max(0,self.demVoteRatio-self.botConfig['demvotepool'])
                
                if not self.game.is_valid_command(button):
                    continue
                #print("Adding command")
                self.curQueue.addCom([button,username])