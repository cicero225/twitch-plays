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
        self.curQueue=comQueue()
        self.queueStatus="Nominal"
        self.lastButton=""
        self.voteCount={}
        self.lastPushed=""
        self.voteItems=self.voteCount.items() #Dynamically changing list in python 3 that keeps up with voteCount
        self.democracy=True #Anarchy is default on.
        self.curQueue.democracy=self.democracy #Queue also needs this information
        self.game.democracy=self.democracy
        self.demVoteRatio=50 #50/50 at the start
        self.lastConfigTime=time.time() #Timer on config file updates
        self.configUpdateFreq=60 #config file updates every 60 seconds
        
    def readConfigText(self):
        self.extConfig.read(self.config['configPath'])
        self.game.keymap=dict(self.extConfig['Keymap'])
        for sub in self.game.keymap.keys():
            self.game.keymap[sub] = int(self.game.keymap[sub],16) #convert from the hex to integer
        self.game.macros=dict(self.extConfig['Macros'])
        self.botConfig=dict(self.extConfig['Bot'])
        for sub in self.botConfig.keys():
            self.botConfig[sub] = float(self.botConfig[sub])
        self.game.gameConfig=dict(self.extConfig['Game'])
        for sub in self.game.gameConfig.keys():
            self.game.gameConfig[sub] = float(self.game.gameConfig[sub])

    def update_message_buffer(self, message):
        self.message_buffer.append(message)
        if len(self.message_buffer)>self.bufferLength:
            self.message_buffer.pop(0)
        
    def update_message(self,timeleft):
        system('cls')
        if self.democracy:
            votes=self.sortVote() #It's inefficient to do this every time, yes, but the alternative is to implement a custom sorted value hashmap, and I hope that's not necessary...
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
            #update config file if necessary...hopefully this doesn't cause threading issues with the other thread
            if time.time()-self.lastConfigTime>self.configUpdateFreq:
                self.readConfigText()
                self.lastConfigTime=time.time()
            #Toggles Anarchy/Democracy state
            if self.democracy and self.demVoteRatio<100-self.botConfig['votethresh']:
                self.democracy=False
                self.curQueue.democracy=False
                self.game.democracy=False
            elif not self.democracy and self.demVoteRatio>self.botConfig['votethresh']:
                self.democracy=True
                self.curQueue.democracy=True
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
                    self.demVoteRatio=min(100,self.demVoteRatio+self.botConfig['demvotepool']) #mmm signed values
                elif button=='anarchy':
                    self.demVoteRatio=max(0,self.demVoteRatio-self.botConfig['demvotepool'])
                
                if not self.game.is_valid_command(button):
                    continue
                #print("Adding command")
                self.curQueue.addCom([button,username])