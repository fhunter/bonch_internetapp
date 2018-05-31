#!/usr/bin/env python3

import tkinter as tk

class Application(tk.Frame):
    def __init__(self, master = None):
        super().__init__(master)
        self.pack(expand=True,fill="both")
        self.create_widgets()
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
        self.entry_username=tk.Entry(self)
        self.label_password=tk.Label(self,text="Password:")
        self.entry_password=tk.Entry(self)
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
        print("Connection check called!")
        self.after(1000, self.connection_check)

    def connect(self):
        print("Connect called")
    
    def disconnect(self):
        print("Disconnect called")


root = tk.Tk()
root.grid_columnconfigure(0,weight=1)
root.grid_rowconfigure(0,weight=1)
app = Application(master=root)
app.master.title("Internet")
#app.master.maxsize(640,480)
app.mainloop()
