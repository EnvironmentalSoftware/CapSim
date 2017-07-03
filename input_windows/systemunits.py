#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical
from capsim_functions    import get_superfont

class UnitProperties:

    def __init__(self, master, system):
        """Constructor method.  Defines the parameters to be obtained in this window."""

        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype)       #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                               #flag for existence of toplevel#

        self.lengthunits = [u'\u03BCm', 'cm', 'm']
        self.concunits   = [u'\u03BCg/L', 'mg/L', 'g/L', u'\u03BCmol/L', 'mmol/L', 'mol/L']
        self.timeunits   = ['s', 'min', 'hr', 'day', 'yr']
        self.diffunits   = [u'cm\u00B2/s', u'cm\u00B2/yr']


        self.lengthunit  = StringVar(value = self.lengthunits[1])
        self.concunit    = StringVar(value = self.concunits[0])
        self.timeunit    = StringVar(value = self.timeunits[4])
        self.diffunit    = StringVar(value = self.diffunits[0])

        self.system    = system

    def make_widgets(self):

        self.instructions   = Label(self.tframe, text = 'Please choose the appropriate units for the system:\n')

        self.blankcolumn    = Label(self.tframe,  text =' ', width = 2)
        self.labelcolumn    = Label(self.tframe,  text =' ', width = 20)
        self.valuecolumn    = Label(self.tframe,  text =' ', width = 20)
        self.endcolumn      = Label(self.tframe,  text =' ', width = 2)

        self.blank1         = Label(self.frame,  text =' ', width = 2)
        self.blank2         = Label(self.frame,  text =' ', width = 2)

        self.lengthlabel    = Label(self.frame,  text = 'Length',                   width = 20)
        self.conclabel      = Label(self.frame,  text = 'Concentration',            width = 20)
        self.timelabel      = Label(self.frame,  text = 'Time',                     width = 20)
        self.difflabel      = Label(self.frame,  text = 'Diffusion Coefficient',    width = 20)

        self.lengthwidget   = OptionMenu(self.frame, self.lengthunit, *self.lengthunits)
        self.concwidget     = OptionMenu(self.frame, self.concunit,   *self.concunits)
        self.timewidget     = OptionMenu(self.frame, self.timeunit,   *self.timeunits)
        self.diffwidget     = OptionMenu(self.frame, self.diffunit,   *self.diffunits)

        self.lengthwidget.config(width = 15)
        self.concwidget.config(  width = 15)
        self.timewidget.config(  width = 15)
        self.diffwidget.config(  width = 15)

        self.instructions.grid( row = 0, column = 0, columnspan = 4, padx = 6, sticky = 'W')

        self.blankcolumn.grid(       row = 1, column = 0)
        self.labelcolumn.grid(       row = 1, column = 1)
        self.valuecolumn.grid(       row = 1, column = 2)
        self.endcolumn.grid(         row = 1, column = 3)

        self.lengthlabel.grid(       row = 2, column = 1, sticky = 'E', padx = 4)
        self.lengthwidget.grid(      row = 2, column = 2, sticky = 'W', padx = 4)

        self.conclabel.grid(         row = 3, column = 1, sticky = 'E', padx = 4)
        self.concwidget.grid(        row = 3, column = 2, sticky = 'W', padx = 4)

        self.timelabel.grid(         row = 4, column = 1, sticky = 'E', padx = 4)
        self.timewidget.grid(        row = 4, column = 2, sticky = 'W', padx = 4)

        self.difflabel.grid(         row = 5, column = 1, sticky = 'E', padx = 4)
        self.diffwidget.grid(        row = 5, column = 2, sticky = 'W', padx = 4)

        self.blank1.grid(            row = 6, column = 1, sticky = 'E', padx = 4)

        self.blank2.grid(            row = 7, column = 1, sticky = 'E', padx = 4)

        self.focusbutton = None


def get_systemunits(system, step):
    """Get flow and system parameters."""

    root = CapSimWindow(buttons = 1)
    root.make_window(UnitProperties(root, system))
    root.mainloop()
    if root.main.get() == 0 and root.step.get() == 1:
        system.get_systemunits(root.window)
    else:                    system = None

    root.destroy()

    return system, step + root.step.get()
