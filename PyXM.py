import Tkinter

try:
    import serial
except:
    print "Serial Library not available"

import time
import threading

xm_cmd_header = "\x5A\xA5"
xm_cmd_footer = "\xED\xED" 

logWin = None

def test_thread():
    time.sleep(1)
    iters = 10
    while iters != 0:
#        if (logWin != None):
#            logWin.insert(Tkinter.END,"Tick\n",("Activity"))
        print "Tick"
        time.sleep(2)
        iters -= 1

class xmapp_tk(Tkinter.Tk):  
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()
        
        self.quitThread = False
        self.idleFrames = 0
        
        # start com port read thread
        
        self.comThread = threading.Thread(None,self.com_thread,"ComThread")
        self.comThread.start()
        
    def com_thread(self):
        # Keep calling the read method for the port
        if self.logText != None:
            self.logText.insert(Tkinter.END,"COM port thread started\n",("Activity"))
        while True:
            (return_code,data) = self.receiveXMPacket();
            if self.quitThread:
                return
            if return_code == None:
                continue
            code_val = ord(return_code)
            
            # check return codes

            if code_val == 0xF2:
                self.idleFrames += 1
            elif code_val == 0xF4:
                if self.logText != None:
                    self.logText.insert(Tkinter.END,"Command Acknowledged\n",("Activity"))
            if code_val == 0xB1:
                self.print_radio_id(data)
            elif code_val == 0x80:
                self.print_status1(data)
            elif code_val == 0xC3:
                self.print_signal_data(data)
            elif code_val == 0x93:
                self.print_mute_state(data)
            else:
                if self.logText != None:
                    self.logText.insert(Tkinter.END,"Unknown return code 0x%02X\n"%code_val,("Warning"))
                

    def initialize(self):
        self.grid()
        
        self.ioText = None
        self.serialPort = None
        
        # text field for IO to/from radio
        self.ioText = Tkinter.Text(self.parent,height=20,width=80,wrap=Tkinter.NONE)
        self.ioText_vertScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.VERTICAL)
        self.ioText_vertScrollbar.config(command=self.ioText.yview)
        self.ioText_horizScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.HORIZONTAL)
        self.ioText_horizScrollbar.config(command=self.ioText.xview)
        self.ioText.configure(yscrollcommand=self.ioText_vertScrollbar.set)
        self.ioText.configure(xscrollcommand=self.ioText_horizScrollbar.set)
        
        self.ioText.grid(column=0,row=0,sticky='EWNS')
        
        self.ioText_horizScrollbar.grid(column=0,row=1,sticky='EW')
        self.ioText_vertScrollbar.grid(column=1,row=0,sticky='NS')
        
        self.ioText.tag_config("SentBytes",foreground="red")
        self.ioText.tag_config("ReceivedBytes",foreground="blue")

        # Text window for debugging outpu
        
        self.logText = Tkinter.Text(self.parent,height=10,width=80,wrap=Tkinter.NONE)

        self.logText_vertScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.VERTICAL)
        self.logText_vertScrollbar.config(command=self.logText.yview)
        self.logText_horizScrollbar = Tkinter.Scrollbar(self.parent,orient=Tkinter.HORIZONTAL)
        self.logText_horizScrollbar.config(command=self.logText.xview)
        self.logText.configure(yscrollcommand=self.logText_vertScrollbar.set)
        self.logText.configure(xscrollcommand=self.logText_horizScrollbar.set)
        
        self.logText.grid(column=0,row=3,sticky='EWNS')
        
        self.logText_horizScrollbar.grid(column=0,row=4,sticky='EW')
        self.logText_vertScrollbar.grid(column=1,row=3,sticky='NS')

        self.logText.tag_config("Critical",foreground="red")
        self.logText.tag_config("Warning",foreground="orange")
        self.logText.tag_config("Activity",foreground="black")
        
        logWin = self.logText
        
        # frame for command buttons
        self.buttonFrame = Tkinter.Frame(self.parent)
        
        self.resetXmButton = Tkinter.Button(self.buttonFrame,text="ResetXM",command=self.reset_xm)       
        self.resetXmButton.grid(column=0,row=0)

        self.turnOn33VButton = Tkinter.Button(self.buttonFrame,text="Turn on 3.3V",command=self.turn_on_33V)       
        self.turnOn33VButton.grid(column=1,row=0)
        
        self.unmuteDacButton = Tkinter.Button(self.buttonFrame,text="Unmute DAC",command=self.unmute_dac)       
        self.unmuteDacButton.grid(column=2,row=0)
        
        self.powerOnButton = Tkinter.Button(self.buttonFrame,text="Power On",command=self.power_on)       
        self.powerOnButton.grid(column=3,row=0)
        
        self.powerOffButton = Tkinter.Button(self.buttonFrame,text="Power Off",command=self.power_off)       
        self.powerOffButton.grid(column=4,row=0)
        
        self.getRadioIDButton = Tkinter.Button(self.buttonFrame,text="Get Radio ID",command=self.get_radio_id)       
        self.getRadioIDButton.grid(column=5,row=0)
        
        muteoffcmd = lambda: self.set_mute(False)
        self.UnmuteButton = Tkinter.Button(self.buttonFrame,text="Unmute",command=muteoffcmd)       
        self.UnmuteButton.grid(column=6,row=0)

        muteoncmd = lambda: self.set_mute(True)
        self.MuteButton = Tkinter.Button(self.buttonFrame,text="Mute",command=muteoncmd)       
        self.MuteButton.grid(column=7,row=0)

        self.GetSignalDataButton = Tkinter.Button(self.buttonFrame,text="Get Sig Data",command=self.get_signal_data)
        self.GetSignalDataButton.grid(column=8,row=0)

        # field for com port 
        self.comEntry = Tkinter.Entry(self.buttonFrame)
        self.comEntry.grid(column=0,row=1)
        #self.comEntry.set("COM3")
        
        # button for opening port
        self.OpenButton = Tkinter.Button(self.buttonFrame,text="Open",command=self.open_com_port)       
        self.OpenButton.grid(column=1,row=1)
        
        # button for closing port
        self.CloseButton = Tkinter.Button(self.buttonFrame,text="Close",command=self.close_com_port)       
        self.CloseButton.grid(column=2,row=1)

        # button for killing com thread
        self.KillThreadButton = Tkinter.Button(self.buttonFrame,text="Kill COM thread",command=self.kill_thread)       
        self.KillThreadButton.grid(column=3,row=1)

        self.buttonFrame.grid(column=0, row=5)
        
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())
    
    def kill_thread(self):
        self.quitThread = True
        self.comThread.join(None)
        self.logText.insert(Tkinter.END,"COM thread killed.\n",("Activity"))    
            
    def print_bin(self,buf,tag):
        bin_text = ""
        for byte in range(len(buf)):
            bin_text += "%02X "%ord(buf[byte])
        bin_text += "\n"
        self.ioText.insert(Tkinter.END,bin_text,tag)
    
    def sendXMPacket(self,cmd):
        packet = ""
        packet += xm_cmd_header + '\x00'
        packet += cmd
        packet += xm_cmd_footer
        if self.serialPort != None:
            self.serialPort.write(packet)
        if (self.ioText != None):
            self.print_bin(packet,("SentBytes")) 
        
    def receiveXMPacket(self):
        if self.serialPort == None:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"No serial port to read\n",("Warning"))
            # wait for port to be connected
            time.sleep(1)
            return (None, None)
            
        # read header 
        # first two bytes are 5AA5, like command
        # second two bytes are size.
        packet = ""
        read_so_far = 0
        while read_so_far < 5:
            chunk = ""
            chunk = self.serialPort.read(5-read_so_far)
            packet += chunk
            read_so_far += len(chunk)
            #print "%d %d:" % (len(chunk),read_so_far)
            if (self.quitThread):
                return (None,None)
            
        if len(packet) != 5:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Packet header size not as expected (5). %d\n"%len(packet),("Warning"))
                return (None, None)
        # verify it is the header
        if packet[:2] != xm_cmd_header:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Packet header not found: %s\n"%packet[:2],("Warning"))
                return (None, None)
        size = ord(packet[2])*256 + ord(packet[3])
        # read the rest of the packet
        rest_of_packet = self.serialPort.read(size+1)
        if len(rest_of_packet) != size+1:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Packet payload size not as expected(%d). %d\n"%(size,len(rest_of_packet)),("Warning"))
                return (None, None)
        # return tuple with return code and data
        if self.ioText != None:
            self.print_bin(packet+rest_of_packet,"ReceivedBytes")
        return (packet[4],rest_of_packet[:size-1])
    
    def reset_xm(self):
        cmd = '\x03\x74\x00\x01'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Resetting radio\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def turn_on_33V(self):
        cmd = '\x04\x74\x02\x01\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Turning on 3.3\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def unmute_dac(self):
        cmd = '\x03\x74\x0B\x00'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Unmuting DAC\n",("Activity"))
        self.sendXMPacket(cmd)
    
    def power_on(self):
        cmd = '\x05\x00\x16\x16\x24\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering on radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def power_off(self):
        cmd = '\x02\x01\x01'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Powering off radio\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_radio_id(self):
        cmd = '\x01\x31'    
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting Radio ID\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def set_mute(self, on = False):
        cmd = '\x02\x13'
        
        if (on == True):
            logText = "Muting radio\n"
            cmd += '\x01'
        else:
            logText = "Unmuting radio\n"
            cmd += '\x00'
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,logText,("Activity"))
            
        self.sendXMPacket(cmd)
    
    def change_channel(self,channel):
        cmd = '\x06\x10\x02' + channel + '\x00\x00\x01'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Changing Channel to %d\n"%channel,("Activity"))
        self.sendXMPacket(cmd)
        
    def get_this_channel_info(self):
        cmd = '\0x02\x25\x08'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_next_channel_info(self):
        cmd = '\0x02\x25\x09'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting next channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_previous_channel_info(self):
        cmd = '\0x02\x25\x10'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting previous channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_extended_channel_info(self,channel):
        cmd = '\x02\x22' + channel
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting extended channel info\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def get_signal_data(self):
        cmd = '\x01\x43'
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Getting signal data\n",("Activity"))
        self.sendXMPacket(cmd)
        
    def open_com_port(self):
        # get com port
        comPort = self.comEntry.get()
        self.serialPort = serial.Serial(port=comPort,timeout=0.5)

    def close_com_port(self):
        if self.serialPort != None:
            self.serialPort.close()
            self.serialPort = None

    def print_radio_id(self,data):
        if len(data) != 11:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Radio id not correct length. Exp: 14 Act: %d\n"%len(data),("Warning"))
            return
        # if good, print ascii characters
        if self.logText != None:
            self.logText.insert(Tkinter.END,"Radio ID: " + data[3:11] + "\n",("Activity"))
                                
    def print_status1(self,data):
        if len(data) != 26:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Status1 not correct length. Exp: 11 Act: %d\n"%len(data),("Warning"))
            #return
        # if good, print ascii characters
        status = "Radio Status: "
        if ord(data[0]) == 0x3:
            status + "NOT Activated "
        status += "Version: %d.%d "%(ord(data[1]),ord(data[2]))
        status += "RX Date: %d%d:%d%d:%d%d%d%d "%(ord(data[2]),ord(data[3]),ord(data[4]),ord(data[5]),ord(data[6]),ord(data[7]),ord(data[8]),ord(data[9]))
        status += "CMB Version: %d "%ord(data[10])
        status += "%s "%data[12:20]
        if self.logText != None:
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))
        
    def print_signal_data(self,data):
        if len(data) != 25:
            if self.logText != None:
                self.logText.insert(Tkinter.END,"Signal data not correct length. Exp: 26 Act: %d\n"%len(data),("Warning"))
            #return
        status = "Receiver: Sat: "
        if (ord(data[2]) == 0x0):
            status += "None "
        elif (ord(data[2]) == 0x1):
            status += "Fair "
        elif (ord(data[2]) == 0x2):
            status += "Good "
        elif (ord(data[2]) == 0x3):
            status += "Exc "
        else:
            status += "?(%d)" % ord(data[2])
            
        status += "Ant: "
        if (ord(data[3]) == 0x0):
            status += "Dis "
        elif (ord(data[3]) == 0x1):
            status += "Con "
        else:
            status += "?(%d) " % ord(data[3])
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))

    def print_mute_state(self,data):
        status = "Mute: "
        if (ord(data[2]) == 0x00):
            status += "Off"
        elif (ord(data[2]) == 0x01):
            status += "On"            
        else:
            status += "?(%d)" % ord(data[2])
            
        if self.logText != None:
            self.logText.insert(Tkinter.END,status + "\n",("Activity"))
        
if __name__ == "__main__":
    app = xmapp_tk(None)
    app.title('PyXM')
    app.mainloop()
        
              
        
        
