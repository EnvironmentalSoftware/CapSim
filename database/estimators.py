#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter          import Frame, Label, Entry, Button, Text, OptionMenu, \
                             StringVar, DoubleVar
from capsim_functions import HaydukLaudieDw, BakerKoc, PAHKoc, PCBKoc, PAHKdoc, PCBKdoc,\
                             BurkhardKdoc, h20viscosity, MVol

class Estimators:
    """Used to make a window to compute the values of parameters for 
    the database."""

    def __init__(self, master, temp, MW, Kow, density, sfont):
        """Constructor method."""

        self.version        = 'CapSim 3.3'  #system.version
        self.fonttype       = 'Arial 10'    #system.fonttype
        self.master         = master
        self.tframe         = Frame(master.tframe)
        self.frame          = Frame(master.frame)
        self.bframe         = Frame(master.bframe)
        self.sfont          = sfont
        self.temp           = temp
        self.MW             = MW
        self.Kow            = Kow
        self.density        = density
        
        self.Dw             = DoubleVar()
        self.Dwoptions      = ['Hayduk and Laudie', 'None']
        self.Dwoption       = StringVar(value = self.Dwoptions[0])

        self.Koc            = DoubleVar()
        self.Kocoptions     = ['Baker', 'PAH', 'PCB', 'None']
        self.Kocoption      = StringVar(value = self.Kocoptions[0])

        self.Kdoc           = DoubleVar()
        self.Kdocoptions    = ['Burkhard', 'PAH', 'PCB', 'None']
        self.Kdocoption     = StringVar(value = self.Kdocoptions[0])

        self.top         = None

    def make_widgets(self):
        """Makes the widgets for the window."""

        self.instructions = Label(self.frame, text = ' Please choose the appropriate methods to estimate the properties for CapSim:\n')
        self.headings1  = Label(self.frame, text = 'Parameter  ')
        self.headings2  = Label(self.frame, text = 'Model')
        self.headings3  = Label(self.frame, text = '    Value')
        self.headings4  = Label(self.frame, text = 'units')

        self.Dwlabel    = Label(self.frame, text = 'Molecular Diffusion Coefficient: ')
        self.Dwmenu     = OptionMenu(self.frame, self.Dwoption,  
                                     *self.Dwoptions)
        self.Dwentry    = Entry(self.frame, textvariable = self.Dw, justify = 'center', width = 9)
        self.Dwunits    = Label(self.frame,  text = u'cm\u00B2/s')

        self.Koclabel   = Label(self.frame, text = 'Organic Carbon Partition Coefficient: ')
        self.Kocmenu    = OptionMenu(self.frame, self.Kocoption, *self.Kocoptions)
        self.Kocentry   = Entry(self.frame, textvariable = self.Koc, justify = 'center', width = 9)
        self.Kocunits   = Label(self.frame,  text = 'log (L/kg)')

        self.Kdoclabel  = Label(self.frame, text = 'Dissolved Organic Carbon Partition Coefficient: ')
        self.Kdocmenu   = OptionMenu(self.frame, self.Kdocoption, *self.Kdocoptions)
        self.Kdocentry  = Entry(self.frame, textvariable = self.Kdoc,
                                justify = 'center', width = 9)
        self.Kdocunits  = Label(self.frame,  text = 'log (L/kg)            ')

        self.blank1     = Label(self.frame, text = ' ' * 75)
        self.blank2     = Label(self.frame, text = ' ' * 40)
        self.blank3     = Label(self.frame, text = ' ' * 19)
        self.calcbutton = Button(self.frame, text = 'Calculate', width = 20, command = self.calculate)

        self.instructions.grid(row = 0, columnspan = 4, sticky = 'W')
        self.headings1.grid(row    = 1, column = 0, sticky = 'E')
        self.headings2.grid(row    = 1, column = 1)
        self.headings3.grid(row    = 1, column = 2, sticky = 'W')
        self.headings4.grid(row    = 1, column = 3, sticky = 'W')

        self.Dwlabel.grid(row      = 2, column = 0, sticky = 'E')
        self.Dwmenu.grid(row       = 2, column = 1, sticky = 'WE')
        self.Dwentry.grid(row      = 2, column = 2, sticky = 'WNS', padx = 4, pady = 2)
        self.Dwunits.grid(row      = 2, column = 3, sticky = 'W')

        self.Koclabel.grid(row     = 3, column = 0, sticky = 'E')
        self.Kocmenu.grid(row      = 3, column = 1, sticky = 'WE')
        self.Kocentry.grid(row     = 3, column = 2, sticky = 'WNS', padx = 4, pady = 2)
        self.Kocunits.grid(row     = 3, column = 3, sticky = 'W')

        self.Kdoclabel.grid(row    = 4, column = 0, sticky = 'E')
        self.Kdocmenu.grid(row     = 4, column = 1, sticky = 'WE')
        self.Kdocentry.grid(row    = 4, column = 2, sticky = 'WNS', padx = 4, pady = 2)
        self.Kdocunits.grid(row    = 4, column = 3, sticky = 'W')

        self.blank1.grid(row = 5, column = 0)
        self.blank2.grid(row = 5, column = 1)
        self.blank3.grid(row = 5, column = 2)
        self.calcbutton.grid(row = 10, columnspan = 4)

        self.calcbutton.bind('<Return>', self.calculate)

        self.focusbutton = self.calcbutton

    def calculate(self, event = None): 
        """Finish and move on."""

        if self.Dwoption.get() == 'Hayduk and Laudie':
            try: self.Dw.set(float('%.2e' % HaydukLaudieDw(h20viscosity(self.temp), MVol(self.MW, self.density))))
            except: self.math_error('Dw')

        if self.Kocoption.get() == 'Baker':
            try:    self.Koc.set(float('%.2f' % BakerKoc(self.Kow)))
            except: self.math_error('Koc')

        elif self.Kocoption.get() == 'PAH':
            try:    self.Koc.set(float('%.2f' % PAHKoc(self.Kow)))
            except: self.math_error('Koc')

        elif self.Kocoption.get() == 'PCB':
            try:    self.Koc.set(float('%.2f' % PCBKoc(self.Kow)))
            except: self.math_error('Koc')

        if self.Kdocoption.get() == 'Burkhard':
            try:    self.Kdoc.set(float('%.2f' % BurkhardKdoc(self.Kow)))
            except: self.math_error('Kdoc')

        if self.Kdocoption.get() == 'PAH':
            try:    self.Kdoc.set(float('%.2f' % PAHKdoc(self.Kow)))
            except: self.math_error('Kdoc')

        if self.Kdocoption.get() == 'PCB':
            try:    self.Kdoc.set(float('%.2f' % PCBKdoc(self.Kow)))
            except: self.math_error('Kdoc')

        self.focusbutton = self.master.okbutton

    def math_error(self, variable):
            tkmb.showerror(title = 'Math Error', message = 
                           'The parameters you have entered for %s produce ' %
                           variable + 'a math error.  Please change the '    +
                           'parameters and recalculate.')

