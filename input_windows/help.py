#! /usr/bin/env python
#
#This script is used to display the main menu for CapSim.  It also contains a
#function to center the window on the screen.

import tkMessageBox as tkmb, tkFileDialog as tkfd, sys, os

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

from Tkinter             import Frame, Label, Text
from capsim_object_types import CapSimWindow

class Help:
    """Creates the main menu for CapSim."""

    def __init__(self, master, system):
        """Constructor method."""

        self.version  = system.version
        self.fonttype = system.fonttype

        self.master   = master
        self.frame    = Frame(master.frame)
        self.top      = None

    def make_widgets(self):
        """Create the widgets for the window."""

        self.instructions = Label(self.frame, text = 'Welcome to CapSim Help')
        self.blank        = Label(self.frame, text = '')
        
        #display the widgets

        self.instructions.grid(row = 0, sticky = 'W', padx = 8)
        self.blank.grid(row = 2)

        self.focusbutton = None

def show_help(system):
    """Shows the main menu."""

    root = CapSimWindow(buttons = 2)
    root.make_window(Help(root, system))
    root.mainloop()

    flag = root.main.get()
        
    root.destroy()

    return flag
