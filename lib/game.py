import win32api
import win32con
import time
from win32api import GetSystemMetrics
from win32con import *

class Game:
    ccLengthAnarchy=1 #Max Command chain length
    ccLengthDem=3
    democracy=True #It is reponsibility of lib.bot to set this correctly
    #width=GetSystemMetrics(0)
    #height=GetSystemMetrics(1)
    width=1920
    height=1080
    macros={    #This aliases some buttons into other commands
        'back':'L100,1060',
        'research':'L800,30',
        'engineering':'L1000,30',
        'barracks':'L1150,30',
        'hangar':'L1250,30',
        'enginback':'L600,900',
        'launch':'L1800,1050',
    }
    keymap = {
       #'backspace':0x08,
       'tab':0x09,
       #'next':0x09,
       #'clear':0x0C,
       'enter':0x0D,
       'space':0x0D, #look up actual space bar, but should be okay for this
       #'shift':0x10,
       #'end':0x23,
       'home':0x24,
       #'center':0x24,
       '0':0x30,
       '1':0x31,
       '2':0x32,
       '3':0x33,
       '4':0x34,
       '5':0x35,
       '6':0x36,
       '7':0x37,
       '8':0x38,
       '9':0x39,
       'a':0x41,
       'left':0x41,
       'b':0x42,
       #'hunker':0x42,
       'c':0x43,
       'd':0x44,
       'right':0x44,
       'e':0x45,
       'f':0x46,
       'g':0x47,
       'h':0x48,
       'i':0x49,
       'j':0x4A,
       'k':0x4B,
       'l':0x4C,
       'm':0x4D,
       'n':0x4E,
       'o':0x4F,
       'p':0x50,
       'q':0x51,
       'r':0x52,
       #'reload':0x52,
       's':0x53,
       'down':0x53,
       't':0x54,
       'u':0x55,
       'v':0x56,
       'w':0x57,
       'up':0x57,
       'x':0x58,
       #'weapon':0x58,
       'y':0x59,
       #'overwatch':0x59,
       'z':0x5A,
       'F1':0x70,
       'F2':0x71,
       'F3':0x72,
       'F4':0x73,
       'F5':0x74,
       'F6':0x75,
       'F7':0x76,
       'F8':0x77,
       'F9':0x78,
       'F10':0x79,
       'F11':0x7A,
       #'previous':0xA0,
       'shift':0xA0,
    }
        
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
            if button[0].lower()=='c' and not button.lower().startswith('m'):
                return True
            words = button[1:].split(",")
            try:  #So very pythonic
                x=int(words[0])
                y=int(words[1])
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
            if len(words)>self.ccLengthDem:
                return False
        else:
            if len(words)>self.ccLengthAnarchy:
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
        xjitter=x-1
        if x==1: #This tiny correction enables 1,1 to work. It's honestly fine even without it, but I imagine some people will intuitively try to R1,1 to exit a menu, for example
            xjitter=x+1 
        if (x>self.width) or (x<1) or (y<1) or (y>self.height):
            return
        #XCOM requires seeing the mouse move slightly before it will actually show the unit movement cursor, grenade curson, etc.
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(xjitter/self.width*65535.0), int(y/self.height*65535.0))
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x/self.width*65535.0), int(y/self.height*65535.0))
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN,x,y,0,0)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP,x,y,0,0)
        
    def clickM(self,button):
        words = button.split(",")
        try:  #So very pythonic
            x=int(words[0])
            y=int(words[1])
        except:
            return
        xjitter=x-1
        if x==1: #This tiny correction enables 1,1 to work. It's honestly fine even without it, but I imagine some people will intuitively try to R1,1 to exit a menu, for example
            xjitter=x+1 
        if (x>self.width) or (x<1) or (y<1) or (y>self.height):
            return
        # x=x-2464; #correction for monitor location; also coordinates hard-coded because I can't be arsed to try harder than that
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(xjitter/self.width*65535.0), int(y/self.height*65535.0))
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x/self.width*65535.0), int(y/self.height*65535.0))
        #win32api.SetCursorPos((x,y))
        if (x>self.width-100) or (x<100) or (y<100) or (y>self.height-1): #This prevents mouse from getting stuck at the edge of the screen; there are other ways to move the camera if necessary
            time.sleep(1)
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int((0.5-1/self.width)*65535.0), 32767) #middle of screen
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, 32767, 32767)
        
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
        xjitter=x-1
        if x==1: #This tiny correction enables 1,1 to work. It's honestly fine even without it, but I imagine some people will intuitively try to R1,1 to exit a menu, for example
            xjitter=x+1 
        if (x>self.width) or (x<1) or (y<1) or (y>self.height):
            return
        #XCOM requires seeing the mouse move slightly before it will actually show the unit movement cursor, grenade curson, etc.
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(xjitter/self.width*65535.0), int(y/self.height*65535.0))
        win32api.mouse_event(win32con.MOUSEEVENTF_MOVE | win32con.MOUSEEVENTF_ABSOLUTE, int(x/self.width*65535.0), int(y/self.height*65535.0))
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN,x,y,0,0)
        time.sleep(.15)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP,x,y,0,0)
        
    def clickW(self,button):
        x, y=win32api.GetCursorPos()
        if button.lower()==('up'):
            win32api.mouse_event(MOUSEEVENTF_WHEEL, x, y, 10, 0)
        elif button.lower()==('down'):
            win32api.mouse_event(MOUSEEVENTF_WHEEL, x, y, -10, 0)
        
    def mleft(self):
        x, y=win32api.GetCursorPos()
        nx = int(x*65535/self.width)
        ny = int(y*65535/self.height)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx-3267,ny)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx-3277,ny)
        
    def mup(self):
        x, y=win32api.GetCursorPos()
        nx = int(x*65535/self.width)
        ny = int(y*65535/self.height)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx,ny-3267)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx,ny-3277)
        
    def mdown(self):
        x, y=win32api.GetCursorPos()
        nx = int(x*65535/self.width)
        ny = int(y*65535/self.height)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx,ny+3267)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx,ny+3277)

    def mright(self):
        x, y=win32api.GetCursorPos()
        nx = int(x*65535/self.width)
        ny = int(y*65535/self.height)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx+3267,ny)
        win32api.mouse_event(win32con.MOUSEEVENTF_ABSOLUTE|win32con.MOUSEEVENTF_MOVE,nx+3277,ny)