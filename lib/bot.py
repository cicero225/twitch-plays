import time
import threading

from config.config import config
from lib.irc import Irc
from lib.game import Game
from lib.comQueue import comQueue
from os import system
from queue import *
#from lib.misc import pbutton

class Bot:
    voteTime=20 #Length of vote time
    checkTime=0.1 #Don't check for more commands more frequently than every 0.1s
    voteLength=5 #Number of votes to show
    bufferLength=5 #Number of recent commands to show
    commandDisplayLength=21 #max number of characters visible on command screen
    demVotePool=10 #size of Democracy/Anarchy vote pool (keeps last N such votes)
    messageUpdateTime=0.5 #update screen every N seconds
    voteThresh=75 #percentage of votes that must be reached to switch command modes

    def __init__(self):
        self.config = config
        self.irc = Irc(config)
        self.game = Game()
        self.message_buffer = []
        self.curQueue=comQueue()
        self.queueStatus="Nominal"
        self.lastButton=""
        self.voteCount={}
        self.lastPushed=""
        self.voteItems=self.voteCount.items() #Dynamically changing list in python 3 that keeps up with voteCount
        self.democracy=True #Anarchy is default on.
        self.curQueue.democracy=self.democracy #Queue also needs this information
        self.game.democracy=self.democracy
        self.demVotes=Queue()
        self.demVoteRatio=50 #50/50 at the start
        oscil=True #this is a cheesy way of doing this...
        for x in range(0,self.demVotePool-1): #this is stupid...note that if the pool size is not even, this becomes inaccurate
            self.demVotes.put(oscil,True)
            oscil=not oscil

    def update_message_buffer(self, message):
        self.message_buffer.append(message)
        if len(self.message_buffer)>self.bufferLength:
            self.message_buffer.pop(0)
        
    def update_message(self,timeleft):
        system('cls')
        if self.democracy:
            votes=self.sortVote()
            print ('\n\n')
            print ('Democracy: '+str(int(self.demVoteRatio))+'%\nAnarchy: '+str(100-int(self.demVoteRatio))+'%\n\nDemocracy!\nTime Remaining: '+str(int(timeleft))+' s\nLast Pushed: '+self.lastPushed+'\n')
            if votes:
                print ('Top Votes:\n')
                for y in votes[0:min(len(votes),self.voteLength)]: #show at most 5 votes
                    print (str(y[1])+" "+y[0])
                print ('\n')
            for y in self.message_buffer:
                print (y)
        else:
            print ('\n\n')
            print ('Democracy: '+str(int(self.demVoteRatio))+'%\nAnarchy: '+str(100-int(self.demVoteRatio))+'%\n\nAnarchy!\n')
            for y in self.message_buffer:
                print (y)
    
    def commandQueue(self):    
        while True:
            #Toggles Anarchy/Democracy state
            if self.democracy and self.demVoteRatio<100-self.voteThresh:
                self.democracy=False
                self.curQueue.democracy=False
                self.game.democracy=False
            elif not self.democracy and self.demVoteRatio>self.voteThresh:
                self.democracy=True
                self.curQueue.democracy=True
                self.game.democracy=True
            if self.democracy: #this is Democracy
                lastvotetime=time.time()
                self.queueStatus="Adding Votes"
                while time.time()-lastvotetime<self.voteTime: #collect commands for voteTime seconds
                    self.update_message(self.voteTime-time.time()+lastvotetime)
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
                    #TODO: Print a count of votes somewhere (but not too frequently, because it requires sorting to display and I'm not implementing a custom sorted-value hashmap >_<)
                    if time.time()-timetaken<self.checkTime: #don't check more frequently than once every 0.1
                        self.queueStatus="Sleeping"
                        time.sleep(self.checkTime)
                self.queueStatus="Running Command"
                votes=self.sortVote() #running the command after voteTime seconds
                if votes:
                    #print("Pressing "+votes[0][0])
                    self.lastPushed=votes[0][0]
                    words=votes[0][0].split("+") #input-time check should have already made sure it's a valid command
                    for y in words:
                        try:
                            self.game.push_button(y)
                        except:
                            time.sleep(0.01) #this is just to feel this catch block. It's bad, yes.
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
                if time.time()-timetaken<self.checkTime: #don't check more frequently than once every 0.1
                    self.queueStatus="Sleeping"
                    time.sleep(self.checkTime)
                    
    def addVote(self,vote):
        if vote in self.voteCount:
            self.voteCount[vote]=self.voteCount[vote]+1
        else:
            self.voteCount[vote]=1
            
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
        
        while True:
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
                    if not self.demVotes.get(True): #If replacing an anarchy vote at the front of the line
                        self.demVoteRatio=self.demVoteRatio+int(100/self.demVotePool)
                    self.demVotes.put(True,True)
                elif button=='anarchy':
                    if self.demVotes.get(True): #If replacing a democracy vote at the front of the line
                        self.demVoteRatio=self.demVoteRatio-int(100/self.demVotePool)
                    self.demVotes.put(False,True)
                
                if not self.game.is_valid_command(button):
                    continue
                #print("Adding command")
                self.curQueue.addCom([button,username])