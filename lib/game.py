import win32api
import win32con
import time
from win32api import GetSystemMetrics
from win32con import *

class Game:
    democracy=True #It is reponsibility of lib.bot to set this correctly
    #width=GetSystemMetrics(0)
    #height=GetSystemMetrics(1)
    width=1920
    height=1080

    def __init__(self): #Well... this is an awkward one-liner
        self.prevEndTime=time.time() #For throttling end turn presses
        
    def get_valid_buttons(self):
        return [button for button in self.keymap.keys()]

    def is_valid_button(self, button):
        if not button:
            return False
        if button in self.keymap.keys():
            return True
        elif button in self.macros.keys():    
            return True
        elif button.lower()==('mup') or button.lower()==('mdown') or button.lower()==('mleft') or button.lower()==('mright') or button.lower()=='wait':
            return True
        elif button.lower().startswith('r') or button.lower().startswith('l') or button.lower().startswith('m'):
            if len(button)<2: #Actually, this particular scenario is ruled out by l/m/r being in the key map for typing letters, so this is just being fastidious
                return False
            if button[1].lower()=='c' and not button.lower().startswith('m'):
                return True
            words = button[1:].split(",")
            try:  #So very pythonic
                x=int(words[0])
                y=int(words[1])
                #Special coordinate throttle for end turn    #This can be made more generic if necessary
                if x>90 and x<160 and y>775 and y<850:
                    if time.time()-self.prevEndTime<self.gameConfig['endblocktime']:
                        return False
                    self.prevEndTime=time.time()
            except:
                return False
            if (x>self.width) or (x<1) or (y<1) or (y>self.height):
                return False
            return True
        elif button.lower().startswith('w') and len(button)>1:
            if button[1:]=='up' or button[1:]=='down':
                return True
            return False
            
    def is_valid_command(self,button): #checks if command is in the correct command+command+command format, then checks each individual part for validity. Note that at this point we are only looking at the first segment of a message, space delimited
        words=button.split("+")
        if self.democracy:
            if len(words)>self.gameConfig['cclengthdem']:
                return False
        else:
            if len(words)>self.gameConfig['cclengthanarchy']:
                return False
        for y in words:
            if not self.is_valid_button(y):
                return False
        return True

    def button_to_key(self, button):
        return self.keymap[button]
    
    def push_button(self, button):
        #print(button)
        if button in self.macros.keys(): #convert macro to something else
            button=self.macros[button]
        if button in self.keymap.keys():
            win32api.keybd_event(self.button_to_key(button), 0, 0, 0)
            time.sleep(.15)
            win32api.keybd_event(self.button_to_key(button), 0, win32con.KEYEVENTF_KEYUP, 0)
        elif button.lower()=='mup': #I could have done this better but too lazy to fix now
            self.mup()
        elif button.lower()=='mdown':
            self.mdown()
        elif button.lower()=='mleft':
            self.mleft()
        elif button.lower()=='mright':
            self.mright()
        elif button.lower()=='wait':
            time.sleep(3)
        elif button.lower().startswith('r'):
            self.clickR(button[1:])
        elif button.lower().startswith('l'):
            self.clickL(button[1:]) 
        elif button.lower().startswith('m'):
            self.clickM(button[1:])
        elif button.lower().startswith('w'):
            self.clickW(button[1:])    
    
    def clickR(self,button):
        if button[0].lower()=='c':
            x, y=win32api.GetCursorPos()
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,x,y,0,0)
            time.sleep(.15)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,x,y,0,0)
            return
        words = button.split(",")
        try:  #So very pythonic
            x=int(words[0])
            y=int(words[1])
        except:
            return
        #if (x>self.width) or (x<1) or (y<1) or (y>self.height): #In theory this has been checked by the input checker before this...
            #return
        self.mousetocoor(x,y)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,x,y,0,0)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,x,y,0,0)
        self.mouseoffedge(x,y)
        
    def clickM(self,button):
        words = button.split(",")
        try:  #So very pythonic
            x=int(words[0])
            y=int(words[1])
        except:
            return
        #if (x>self.width) or (x<1) or (y<1) or (y>self.height): #In theory this has been checked by the input checker before this...
            #return
        self.mousetocoor(x,y)
        #win32api.SetCursorPos((x,y))
        self.mouseoffedge(x,y)
        
    def clickL(self,button):
        if button[0].lower()=='c':
            x, y=win32api.GetCursorPos()
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
            time.sleep(.15)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
            return
        words = button.split(",")
        try:  #So very pythonic
            x=int(words[0])
            y=int(words[1])
        except:
            return
        #if (x>self.width) or (x<1) or (y<1) or (y>self.height): #In theory this has been checked by the input checker before this...
            #return
        self.mousetocoor(x,y)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
        self.mouseoffedge(x,y)
        
    def clickW(self,button):
        x, y=win32api.GetCursorPos()
        if button.lower()==('up'):
            win32api.mouse_event(MOUSEEVENTF_WHEEL, x, y, 10, 0)
        elif button.lower()==('down'):
            win32api.mouse_event(MOUSEEVENTF_WHEEL, x, y, -10, 0)
        
    def mleft(self):
        x, y=win32api.GetCursorPos()
        xmove=max(1,x-100)
        self.mousetocoor(xmove,y)
        self.mouseoffedge(xmove,y)
 
    def mup(self):
        x, y=win32api.GetCursorPos()
        ymove=max(1,y-100)
        self.mousetocoor(x,ymove)
        self.mouseoffedge(x,ymove)
        
    def mdown(self):
        x, y=win32api.GetCursorPos()
        ymove=min(self.height,y+100)
        self.mousetocoor(x,ymove)
        self.mouseoffedge(x,ymove)

    def mright(self):
        x, y=win32api.GetCursorPos()
        xmove=min(self.width,x+100)
        self.mousetocoor(xmove,y)
        self.mouseoffedge(xmove,y)
        
    def mouseoffedge(self,x,y):
        if (x>self.width-25) or (x<25) or (y<25) or (y>self.height-25): #This prevents mouse from getting stuck at the edge of the screen; there are other ways to move the camera if necessary
            time.sleep(1)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(min(max(26,x),self.width-26)/self.width*65535.0), int(min(max(25,y),self.height-25)/self.height*65535.0)) 
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(min(max(25,x),self.width-25)/self.width*65535.0), int(min(max(25,y),self.height-25)/self.height*65535.0))
            
    def mousetocoor(self,x,y):
        xjitter=x-1
        if x==1: #This tiny correction enables 1,1 to work. It's honestly fine even without it, but I imagine some people will intuitively try to R1,1 to exit a menu, for example
            xjitter=x+1 
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(xjitter/self.width*65535.0), int(y/self.height*65535.0))
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x/self.width*65535.0), int(y/self.height*65535.0))