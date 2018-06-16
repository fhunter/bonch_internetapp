#!/usr/bin/env python3

import tkinter as tk
import array
import struct
import fcntl
import socket
import re
import subprocess
import os

# taken from here: https://gist.github.com/pklaus/289646
def all_interfaces():
    max_possible = 128
    bytes = max_possible * 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B')
    for i in range(0, bytes):
        names.extend([0,])
    outbytes = struct.unpack('iL', fcntl.ioctl(s.fileno(),
                             0x8912, # SIOCGIFCONF
                             struct.pack('iL',bytes, names.buffer_info()[0])))[0]
    namestr = names.tostring()
    lst = []
    for i in range(0, outbytes, 40):
        name = namestr[i:i+16].decode().split('\0',1)[0]
        lst.append(name)
    return lst

def get_login_password():
    temp = { 'username': '', 'password': '' }
    try :
        pwd = open(os.path.expanduser('~/.config/internet'),'r')
        txt = pwd.read().split('\n')
        for i in txt:
            j=i.split('=')
            key=j[0]
            value=j[1]
            if key == "LOGIN":
                temp['username'] = value
            if key == "PASSWORD":
                temp['password'] = value
    except:
        pass
    return temp

def save_login_password(login,  password):
    pass

class Application(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.passwd = tk.StringVar()
        self.username = tk.StringVar()
        self.connect_process = None
        self.disconnect_process = None
        self.widget = master
        #
        self.pack(expand=True,fill="both")
        self.create_widgets()
        t = get_login_password()
        self.username.set(t['username'])
        self.passwd.set(t['password'])
        self.after(1000, self.connection_check)

    def create_widgets(self):
        fullysticky=tk.N+tk.S+tk.E+tk.W
        for i in range(0,3):
            self.rowconfigure(i, weight=0)
        self.rowconfigure(3,weight=1)
        for i in range(0,3):
            self.columnconfigure(i,weight=0)
        self.columnconfigure(1,weight=1)
        self.label_username=tk.Label(self,text="Username:")
        self.entry_username=tk.Entry(self,  textvariable=self.username)
        self.label_password=tk.Label(self,text="Password:")
        self.entry_password=tk.Entry(self,  textvariable=self.passwd,  show="*")
        self.button_connect=tk.Button(self,text="Connect",command=self.connect)
        self.button_disconnect=tk.Button(self,text="Disconnect",command=self.disconnect)
        self.label_interface=tk.Label(self,text="Connection:")
        self.label_onlinestatus=tk.Label(self,text="Offline",fg="red",bitmap='gray50',compound='left')
        self.text_ppplog=tk.Text(self)
        #packing
        self.label_username.grid(row=0,column=0,sticky=fullysticky)
        self.entry_username.grid(row=0,column=1,sticky=fullysticky)
        self.label_password.grid(row=1,column=0,sticky=fullysticky)
        self.entry_password.grid(row=1,column=1,sticky=fullysticky)
        self.button_connect.grid(row=0,column=2,sticky=fullysticky)
        self.button_disconnect.grid(row=1,column=2,sticky=fullysticky)
        self.label_interface.grid(row=2,column=0,sticky=fullysticky)
        self.label_onlinestatus.grid(row=2,column=2,sticky=fullysticky)
        self.text_ppplog.grid(row=3,column=0,columnspan=3,sticky=fullysticky)

    def connection_check(self):
        r = re.compile('ppp[0-9]*')
        if any(r.match(line) for line in all_interfaces()):
            #print("Connected")
            self.label_onlinestatus['fg']="green"
            self.label_onlinestatus['text']="Online"
        else:
            #print("Disconnected")
            self.label_onlinestatus['fg']="red"
            self.label_onlinestatus['text']="Offline"
        self.after(1000, self.connection_check)

    def connect(self):
        print("Connect called")
        print(self.username.get(),self.passwd.get())
        # Add starting code
        if self.connect_process:
            self.connect_process.kill()
            self.deletefilehandler(self.connect_process.stdout)
            self.deletefilehandler(self.connect_process.stderr)
            self.connect_process = None 
        self.connect_process = subprocess.Popen(['pon','internet', 'user', self.username.get(), 'password',  self.passwd.get(), 'nodetach',  'debug',  'passive'],stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        self.widget.tk.createfilehandler(self.connect_process.stdout, tk.READABLE, self.dataavailable)
        self.widget.tk.createfilehandler(self.connect_process.stderr, tk.READABLE, self.dataavailable)            
        # See event tracking here: https://stackoverflow.com/questions/3348757/how-to-make-tkinter-repond-events-while-waiting-socket-data
        # should first start /usr/sbin/pptp 172.16.1.254 --nolaunchpppd and kill it after 3 seconds, then kill it
        # then start /usr/bin/pon internet user "username" password "passwd" nodetach debug passive
 
    
    def disconnect(self):
        print("Disconnect called")
        print(self.username.get(),self.passwd.get())
        # then start /usr/bin/poff internet
        if self.disconnect_process:
            self.disconnect_process.kill()
            self.widget.tk.deletefilehandler(self.disconnect_process.stdout)
            self.widget.tk.deletefilehandler(self.disconnect_process.stderr)
            self.disconnect_process = None
        self.disconnect_process = subprocess.Popen(['poff','internet'],stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        self.widget.tk.createfilehandler(self.disconnect_process.stdout, tk.READABLE, self.dataavailable)
        self.widget.tk.createfilehandler(self.disconnect_process.stderr, tk.READABLE, self.dataavailable)

root = tk.Tk()
root.grid_columnconfigure(0,weight=1)
root.grid_rowconfigure(0,weight=1)
app = Application(master=root)
app.master.title("Internet")
app.mainloop()
