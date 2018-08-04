#!/usr/bin/env python3

import tkinter as tk
import array
import struct
import fcntl
import socket
import re
import subprocess
import os
from datetime import datetime
from io import open
from configparser import ConfigParser, MissingSectionHeaderError


CONFIG_PATH = '~/.config/internet'
CONFIG_SECTION_NAME = 'Settings'


# taken from here: https://gist.github.com/pklaus/289646
def all_interfaces():
    max_possible = 128
    bytes = max_possible * 32
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    names = array.array('B')
    for i in range(0, bytes):
        names.extend([0, ])
    outbytes = struct.unpack('iL', fcntl.ioctl(s.fileno(),
                                               0x8912,  # SIOCGIFCONF
                                               struct.pack('iL', bytes, names.buffer_info()[0])))[0]
    namestr = names.tostring()

    for i in range(0, outbytes, 40):
        yield namestr[i:i + 16].decode().split('\0', 1)[0]


def get_config():
    """
    Get config file
    """
    temp = {'login': '', 'password': '', 'is_old_ip': True}
    path = os.path.expanduser(CONFIG_PATH)

    if not os.path.exists(path):
        return temp

    try:
        config = ConfigParser()
        config.read(path)
        temp['login'] = config.get(CONFIG_SECTION_NAME, 'login')
        temp['password'] = config.get(CONFIG_SECTION_NAME, 'password')
        temp['is_old_ip'] = config.getboolean(CONFIG_SECTION_NAME, 'is_old_ip')
    except MissingSectionHeaderError:
        with open(path, 'r', encoding='UTF-8') as fp:
            for line in fp:
                key, value = line.rstrip().split('=', 1)
                temp[str(key).lower()] = value
    except BaseException:
        pass

    return temp


def save_config(config_dict):
    """
    Save config file
    """
    config = ConfigParser()
    config.add_section(CONFIG_SECTION_NAME)
    config.set(CONFIG_SECTION_NAME, 'login', config_dict['login'])
    config.set(CONFIG_SECTION_NAME, 'password', config_dict['password'])
    config.set(CONFIG_SECTION_NAME, 'is_old_ip', str(config_dict['is_old_ip']))
    path = os.path.expanduser(CONFIG_PATH)

    with open(path, 'w', encoding='UTF-8') as config_file:
        config.write(config_file)


class Application(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.password = tk.StringVar()
        self.login = tk.StringVar()
        self.is_old_ip = tk.BooleanVar()
        self.connect_process = None
        self.disconnect_process = None
        self.config_changed = False
        self.widget = master
        #
        self.pack(expand=True, fill="both")
        self.create_widgets()
        self.config = get_config()
        self.init_config()
        self.init_trace()
        self.connection_check()

    def init_config(self):
        self.password.set(self.config['password'])
        self.login.set(self.config['login'])
        self.is_old_ip.set(self.config['is_old_ip'])

    def init_trace(self):
        def changed(var_name):
            def wrapped(*args):
                self.config[var_name] = self.__dict__[var_name].get()
                self.config_changed = True
            return wrapped
        self.password.trace("wa", changed('password'))
        self.login.trace("wa", changed('login'))
        self.is_old_ip.trace("wa", changed('is_old_ip'))

    def create_widgets(self):
        fullysticky = tk.N + tk.S + tk.E + tk.W

        for i in range(0, 3):
            self.rowconfigure(i, weight=0)
        self.rowconfigure(3, weight=1, pad=0)
        for i in range(0, 3):
            self.columnconfigure(i, weight=0)

        self.columnconfigure(1, weight=1)
        self.label_username = tk.Label(self, text="Username:")
        self.entry_username = tk.Entry(self, textvariable=self.login)
        self.label_password = tk.Label(self, text="Password:")
        self.entry_password = tk.Entry(self, textvariable=self.password, show="*")
        self.button_connect = tk.Button(self, text="Connect", command=self.connect)
        self.button_disconnect = tk.Button(self, text="Disconnect", command=self.disconnect)
        self.label_interface = tk.Label(self, text="Connection log:")
        self.label_onlinestatus = tk.Label(self, text="Offline", fg="red", bitmap='gray50', compound='left')
        self.text_ppplog = tk.Text(self)
        self.check_is_old_ip = tk.Checkbutton(self, text='Set old ip', variable=self.is_old_ip)

        self.label_username.grid(row=0, column=0, sticky=fullysticky)
        self.entry_username.grid(row=0, column=1, sticky=fullysticky)
        self.label_password.grid(row=1, column=0, sticky=fullysticky)
        self.entry_password.grid(row=1, column=1, sticky=fullysticky)
        self.button_connect.grid(row=0, column=2, sticky=fullysticky)
        self.button_disconnect.grid(row=1, column=2, sticky=fullysticky)
        self.label_interface.grid(row=2, column=0, sticky=fullysticky)
        self.label_onlinestatus.grid(row=2, column=2, sticky=fullysticky)
        self.text_ppplog.grid(row=3, column=0, columnspan=3, sticky=fullysticky)
        self.check_is_old_ip.grid(row=4, column=0, columnspan=3, sticky=fullysticky)

    def connection_check(self):
        r = re.compile('ppp[0-9]*')
        if any(r.match(line) for line in all_interfaces()):
            self.label_onlinestatus['fg'] = "green"
            self.label_onlinestatus['text'] = "Online"
            self.button_connect_disconnect_toggle(True)
        else:
            self.label_onlinestatus['fg'] = "red"
            self.label_onlinestatus['text'] = "Offline"
            self.button_connect_disconnect_toggle(False)
        self.after(2000, self.connection_check)

    def button_connect_disconnect_toggle(self, connect=True):
        if connect:
            self.button_connect.configure(state=tk.DISABLED)
            self.button_disconnect.configure(state=tk.NORMAL)
        else:
            self.button_connect.configure(state=tk.NORMAL)
            self.button_disconnect.configure(state=tk.DISABLED)

    @property
    def internet_name(self):
        if bool(self.is_old_ip.get()):
            return 'internet_old'
        else:
            return 'internet'

    def connect(self):
        if self.connect_process:
            self.connect_process.kill()
            self.delete_file_handlers(self.connect_process)
            self.connect_process = None

        self.connect_process = subprocess.Popen(['pon', self.internet_name, 'user', self.config['login'], 'password',
                                                 self.config['password'], 'nodetach', 'debug', 'passive'],
                                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.create_file_handlers(self.connect_process)
        self.button_connect_disconnect_toggle(True)
        self.connect_disconnect_output(True)

        if self.config_changed:
            save_config(self.config.copy())
        # See event tracking here:
        # https://stackoverflow.com/questions/3348757/how-to-make-tkinter-repond-events-while-waiting-socket-data
        # should first start /usr/sbin/pptp 172.16.1.254 --nolaunchpppd and kill it after 3 seconds, then kill it
        # then start /usr/bin/pon internet user "username" password "passwd" nodetach debug passive

    def connect_disconnect_output(self, connect=True):
        if connect:
            status_text = 'Connecting'
        else:
            status_text = 'Disconnecting'
        pos_end = float(self.text_ppplog.index('end'))
        self.text_ppplog.insert(tk.END, "{0}{1}...\n\n".format('\n\n' if pos_end > 2.0 else '',
                                                               status_text))
        self.text_ppplog.insert(tk.END, str(datetime.now()))
        self.text_ppplog.insert(tk.END, "\n\n")

    def read_output(self, pipe, process, mask=1 << 20):
        """Read subprocess' output, pass it to the GUI."""
        data = os.read(pipe.fileno(), mask)
        if not data:  # clean up
            self.delete_file_handlers(process)
            return
        self.text_ppplog.insert(tk.END, data.decode())
        self.text_ppplog.see(tk.END)

    def delete_file_handlers(self, process):
        if process is None:
            return
        self.widget.tk.deletefilehandler(process.stdout)
        self.widget.tk.deletefilehandler(process.stderr)

    def create_file_handlers(self, process):
        def dec(fn):
            def wrapped(pipe, mask):
                return fn(pipe, process, mask=mask)
            return wrapped
        self.widget.tk.createfilehandler(process.stdout, tk.READABLE, dec(self.read_output))
        self.widget.tk.createfilehandler(process.stderr, tk.READABLE, dec(self.read_output))

    def disconnect(self):
        """
        Then start /usr/bin/poff internet
        :return:
        """
        if self.disconnect_process:
            self.disconnect_process.kill()
            self.delete_file_handlers(self.disconnect_process)
            self.disconnect_process = None
        self.disconnect_process = subprocess.Popen(['poff', self.internet_name, 'nodetach', 'debug', 'passive'],
                                                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.create_file_handlers(self.disconnect_process)
        self.button_connect_disconnect_toggle(False)
        self.connect_disconnect_output(False)


root = tk.Tk()
root.grid_columnconfigure(0, weight=1)
root.grid_rowconfigure(0, weight=1)
app = Application(master=root)
app.master.title("Internet")
app.mainloop()
