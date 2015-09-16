import time
from queue import *

#One of the purposes of this class is to guard against command "traffic jams" as much as possible. It achieves this by only calling Queue.get() and put() with a 1 second timeout and properly handling timeout. This may occasionally drop commands under extreme load conditions, but guards against some kind of unforeseen infinite block contingency (and 1 second is a really long time to wait). It also drops commands that are too old.

#Threadsafeness: Achieved (for now) by the fact that the only function that more than a one-line call to a Queue method (Queue is guaranteed threadsafe by python) is getCom.

class comQueue:
    dropTime=10 #Time in seconds stacked up commands will be kept before being dropped, in anarchy
    
    def __init__(self):
        self.thisqueue=Queue() 
        self.status=""
        
    def getCom(self):
        comList=[]
        userList=[]
        curtime=time.time()
        while not self.thisqueue.empty():
            try:
                curCom=self.thisqueue.get(True,1) #gives up if blocked for 1 second
            except Empty:
                break
            try:
                self.status=curCom[1]
                if curCom[1]>curtime-self.dropTime: #ensures commands get dropped if they're *really* piling up
                    comList.append(curCom[0])
                    userList.append(curCom[2])
            except: #This is one of those Bad try/excepts, that are only there to keep the code running in case of something unanticipated. Note, though, that in principle whatever triggers the error should not recur and infinite loop - the .get() at the beginning of the while loop should either have removed the entry or have already broken the loop
                continue

        return comList,userList
        
    def addCom(self,com):
        try:
            self.thisqueue.put([com[0], time.time(),com[1]],True,1) #gives up if blocked for 1 second
        except Full:
            return
        #print(self.thisqueue.qsize())
        
    def getStatus(self):
        return self.status