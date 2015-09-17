import time
from collections import deque 
import itertools

#Implements a democracy/anarchy voting queue that adapts to some degree to the number of commanders; With fewer viewers, a minimum number of votes is kept. With more viewers, votes are kept for a maximum amount of time. These parameters are specified in the config ini file.

#By convention here (and convention), oldest votes will go to the lowest indices of the deque. 1=Democracy, 0=Anarchy, 0-1=Ambiguous vote used for internal bookkeeping

#Unlike Queue, deque doesn't support timeout in case of extended blocking. Hopefully that just never happens...

#threadsafing: As in comQueue, this is threadsafed by only having attributes changed by updateQueue() which is only called by the Command thread in bot.py. addVote *can* call comQueue if the second argument is set to non-default, but that's just hypothetical functionality that is not currently used

class demAnQueue:
    def __init__(self):
        self.thisqueue=deque()
        self.demVotePerc=50 #Initial Democracy Percentage
        ###DEFAULT VALUES: Should be overwritten by config.ini in bot###
        self.demAnQueueConfig={'minlen':10,
            'maxtime':300}
        ###END DEFAULT VALUES###
    
    def updateQueue(self):
        #First dump any old elements that are "too old"...but only if there are more elements than the minimum. Note that extra dummy votes are dropped immediately because they have time set to 0.
        curtime=time.time()
        minLen=self.demAnQueueConfig['minlen'] #It is best for threadsafeness to extract these ahead of time so they're consistent in the function (in case config parameters update midfunction)
        maxTime=self.demAnQueueConfig['maxtime']
        lenQueue=len(self.thisqueue)
        lenDiff=max(0,lenQueue-minLen) #Explicitly precalculating how many elements to check, because AddVote may be lengthening the list as we are shortening it (threadsafing) so a while loop over length is risky. Because this is all timed, we'd certainly run into too recent a vote before getting stuck in infinite loop, but good practice is good practice. Also, don't want this particular value being negative...
        for dummy in range(0,lenDiff):
            if curtime-self.thisqueue[0][1]>maxTime:
                self.thisqueue.popleft() #this should never error, since I explicitly check the length...
        
        lenQueue=len(self.thisqueue)
        lenDiff=max(0,lenQueue-minLen) #Now this number may be different...
        
        if self.thisqueue: #If not-empty...necessary because on first initialization it *is* empty
            #calculate DemVote Percentage. Weights of each vote are based on how new it is relative to the maximum vote age. However, the weights of the most recent minLen votes is ALWAYS 1 (to prevent one vote having 100% in slow voting situations)
            #threadsafeness: we make a local copy of the queue, since we just need to perform a calculation but need to check a lot of values
            tempqueue=self.thisqueue
            weightedsum=0
            sumofweights=0
            for dummy in range(0,lenDiff):
                weight=1-min((curtime-tempqueue[dummy][1])/maxTime,1)
                weightedsum=weightedsum+weight*tempqueue[dummy][0]
                sumofweights=sumofweights+weight
            for dummy in range(lenDiff,lenQueue):
                weightedsum=weightedsum+tempqueue[dummy][0]
                sumofweights=sumofweights+1
            self.demVotePerc=weightedsum/sumofweights*100
            
        #Finally, check if the length of the queue is at least the minimum length. If not, it is populated on the LEFT (old) end with non-integer votes equal to the current voting ratio (so as not to shift the average). This is necessary both after object creation (once configuration properties are input) and in case the minimum length parameter gets changed
        if len(self.thisqueue)<minLen:
            self.thisqueue.extendleft(itertools.repeat((self.demVotePerc/100,0),int(minLen)-len(self.thisqueue)))
        
    def addVote(self,vote,update=None):
        if update is None: #Python is weird...
            update=False
        self.thisqueue.append((vote,time.time()))
        if update:
            self.updateQueue()