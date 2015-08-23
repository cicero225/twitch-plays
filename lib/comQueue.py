import time
from queue import *

class comQueue:
    lag=0 #Additional time to lag commands, if desired
    dropTime=10 #Time in seconds stacked up commands will be kept before being dropped, in anarchy
    
    def __init__(self):
        self.thisqueue=Queue() 
        self.status=""
        self.democracy=True #Democracy is default on. If False, will be Anarchy. It is the responsibility of lib.bot to keep this updated
        
    def getCom(self):
        comList=[]
        userList=[]
        notComList=[]
        curtime=time.time()
        while not self.thisqueue.empty():
            curCom=self.thisqueue.get(True,1)
            try:
                self.status=curCom[1]
                if self.democracy:
                    comList.append(curCom[0])
                    userList.append(curCom[2])
                elif curCom[1]>curtime-self.lag-self.dropTime: #ensures commands get dropped if they're *really* piling up
                    if curCom[1]<curtime-self.lag:
                        comList.append(curCom[0])
                        userList.append(curCom[2])
                    else:
                        notComList.append(curCom)
            except TypeError:
                continue

        if not self.democracy:
            for curCom in notComList:
                self.thisqueue.put(curCom)
        return comList,userList
        
    def addCom(self,com):
        self.thisqueue.put([com[0], time.time(),com[1]],True,1) #gives up if blocked for 1 second
        #print(self.thisqueue.qsize())
        
    def getStatus(self):
        return self.status