#! /usr/bin/env python
#
#This script is used to display the main menu for CapSim.  It also contains a
#function to center the window on the screen.

import tkMessageBox as tkmb, tkFileDialog as tkfd, sys, os
import _winreg as wreg

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)
CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
Filepath =wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
CapSimKey.Close()

from Tkinter             import Frame, Label, Button, IntVar, StringVar
from capsim_object_types import CapSimWindow

class MainMenu:
    """Creates the main menu for CapSim."""

    def __init__(self, master, system):
        """Constructor method."""

        self.version  = system.version
        self.fonttype = system.fonttype

        self.master   = master
        self.tframe   = Frame(master.tframe)
        self.frame    = Frame(master.frame)
        self.bframe   = Frame(master.bframe)
        self.option   = IntVar(value = 0)
        self.filename = StringVar()
        self.top      = None

    def make_widgets(self):
        """Create the widgets for the window."""

        self.intro      = Label(self.tframe, text = 'Welcome to CapSim: '      +
                                'Software for Simulating Contaminant '        +
                                'Transport\nthrough a Sediment Capping '      +
                                'Environment (CapSim ' + self.version + ')\n\n(c)'   +
                                ' 2017 Xiaolong Shen, David Lampert, Xin Zhang and '     +
                                'Danny Reible\n\n'    +
                                'Unauthorized use prohibited\n\n Last Updates Apr 27 2017\n', justify = 'left')
        self.inst       = Label(self.frame, text = 'Please choose from the '  +
                                'following selections:\n')
        self.newbutton  = Button(self.frame, text = 'Create new input file',
                                 width = 20, command = self.master.OK)
        self.loadbutton = Button(self.frame, text = 'Load existing input file', width = 20, command = self.load)
        self.graphbutton= Button(self.frame, text = 'Load existing results',
                                 width = 20, command = self.graph)
        self.batchbutton= Button(self.frame, text = 'Run a batch file',
                                 width = 20, command = self.batch)
        self.databutton = Button(self.frame, text = 'Edit chemical database',
                                 width = 20, command = self.data)
        self.solidbutton= Button(self.frame, text = 'Edit material database', 
                                 width = 20, command = self.soliddata)
        self.exitbutton = Button(self.frame, text = 'Exit CapSim',
                                 width = 20, command = self.master.exit)
        self.blank1      = Label(self.frame, text = '')
        self.blank2      = Label(self.frame, text = '')

        #display the widgets

        self.intro.grid(row = 0, sticky = 'W', padx = 8)
        self.inst.grid(row = 2, padx = 8, pady = 1)
        self.newbutton.grid(row = 4, pady = 1)
        self.loadbutton.grid(row = 5, pady = 1)
        self.graphbutton.grid(row = 6, pady = 1)
        self.batchbutton.grid(row = 7, pady = 1)
        self.databutton.grid(row = 8, pady = 1)
        self.solidbutton.grid(row = 9, pady = 1)
        self.exitbutton.grid(row = 10, pady = 1)
        self.blank1.grid(row = 11)
        self.blank2.grid(row = 12)

        #bind the commands to the keyboard

        self.newbutton.bind('<Return>',  self.master.OK)
        self.loadbutton.bind('<Return>', self.load)
        self.batchbutton.bind('<Return>', self.batch)
        self.databutton.bind('<Return>', self.data)
        self.solidbutton.bind('<Return>', self.soliddata)
        self.exitbutton.bind('<Return>',  self.master.exit)

        self.focusbutton = self.newbutton

    def load(self, event = None):
        """Get input file choice."""

        self.option.set(1)
        filename = tkfd.askopenfilename(initialdir = Filepath + 
                                        r'/input_cpsm_files', 
                                        filetypes = [('CPSM files', '*.cpsm')])
        if filename == '': self.option.set(6)
        self.filename.set(filename)
        self.frame.quit()

    def batch(self, event = None):
        """Run a batch file."""

        self.option.set(2)
        self.frame.quit()

    def graph(self, event = None):
        """Run a batch file."""

        self.option.set(3)
        self.frame.quit()

    def data(self, event = None):
        """Add new compound to database."""

        self.option.set(4)
        self.frame.quit()
        
    def soliddata(self, event = None):
        """Add new compound to database."""

        self.option.set(5)
        self.frame.quit()

    def help(self, event = None):
        """Show the help file."""

        self.option.set(6)
        self.frame.quit()

def show_mainmenu(system):
    """Shows the main menu."""

    root = CapSimWindow(master = None, buttons = None)
    root.make_window(MainMenu(root, system))
    root.mainloop()

    option   = root.window.option.get()
    filename = root.window.filename.get()
        
    root.destroy()

    return option, filename
