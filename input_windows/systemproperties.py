#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow
from capsim_functions    import get_superfont

class SystemProperties:
    """Gets the flow and contaminant properties."""

    def __init__(self, master, system):
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master    = master
        self.system    = system
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)

        self.advs      = ['None', 'Steady flow', 'Period oscillation']
        self.bios      = ['None', 'Uniform', 'Depth-dependent']
        self.cons      = ['None', 'Consolidation']
        
        self.adv       = StringVar(value = self.advs[0])       #tidal flag
        self.bio       = StringVar(value = self.bios[0])       #bioturbation flag
        self.con       = StringVar(value = self.cons[0])       #consolidation flag
        
        self.hbio      = DoubleVar(value = 10.)             #bioturbation depth
        self.sigma     = DoubleVar(value = 10.)             #bioturbation depth
        self.Dbiop     = DoubleVar(value = 1.)              #particle bioturbation coeff
        self.Dbiopw    = DoubleVar(value = 100.)            #pore water bioturbation coeff
        self.Vdar      = DoubleVar(value = 0.)              #Darcy velocity
        self.Vtidal    = DoubleVar(value = 0.)              #Tidal velocity
        self.ptidal    = DoubleVar(value = 0.0014)          #Tidal frequency
        self.hcon      = DoubleVar(value = 0)               #total consolidation
        self.t90       = DoubleVar(value = 1.)              #time to 90% consolidation
        self.top       = None                               #flag for existence of toplevel

        if system.layers[0].number == 0: self.toplayer_h = system.layers[1].h
        else:                            self.toplayer_h = system.layers[0].h

        self.lengthunit = system.lengthunit
        self.timeunit   = system.timeunit
        self.diffunit   = system.diffunit
        self.diffunits  = system.diffunits

        try:
            self.adv.set(system.adv)            
            self.bio.set(system.bio)
            self.con.set(system.con)
            self.Vdar.set(system.Vdar)
            
            self.hbio.set(system.hbio)
            self.sigma.set(system.sigma)
            self.Dbiop.set(system.Dbiop)
            self.Dbiopw.set(system.Dbiopw)
            
            self.Vtidal.set(system.Vtidal)
            self.ptidal.set(system.ptidal)            

            self.hcon.set(system.hcon)
            self.t90.set(system.t90)
        except: pass
        
    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Please provide the information of the following system properties:  ')

        self.blank1       = Label(self.frame,  width = 30)
        self.blank2       = Label(self.frame,  width = 20)
        self.blank3       = Label(self.frame,  width = 15)
        self.blank4       = Label(self.frame,  width = 20)
        
        self.headings1    = Label(self.frame,  text = 'Parameter')
        self.headings2    = Label(self.frame,  text = 'Value')
        self.headings3    = Label(self.frame,  text = 'Units')

        self.advlabel     = Label(self.frame,  text = 'Upwelling groundwater flow')
        self.advwidget    = OptionMenu(self.frame, self.adv, *self.advs, command = self.updatesystem)
        self.Vdarlabel    = Label(self.frame,  text = 'Darcy velocity:')
        self.Vtidallabel  = Label(self.frame,  text = 'Oscillation maximum velocity:')
        self.ptidallabel  = Label(self.frame,  text = 'Oscillation period:')
        self.Vdarwidget   = Entry(self.frame, width = 10,textvariable = self.Vdar,  justify = 'center')
        self.Vtidalwidget = Entry(self.frame, width = 10,textvariable = self.Vtidal,justify = 'center')
        self.ptidalwidget = Entry(self.frame, width = 10,textvariable = self.ptidal,justify = 'center')
        self.Vdarunits    = Label(self.frame, text = self.lengthunit + '/' + self.timeunit)
        self.Vtidalunits  = Label(self.frame, text = self.lengthunit + '/' + self.timeunit)
        self.ptidalunits  = Label(self.frame, text = self.timeunit)
        
        self.biolabel     = Label(self.frame,  text = 'Modeling bioturbation')
        self.biowidget    = OptionMenu(self.frame, self.bio, *self.bios, command = self.updatesystem)
        self.hbiolabel    = Label(self.frame,  text = 'Bioturbation depth:')
        self.sigmalabel   = Label(self.frame,  text = 'Gaussian model coefficient:')
        self.Dbioplabel   = Label(self.frame,  text = 'Particle biodiffusion coefficient:')
        self.Dbiopwlabel  = Label(self.frame,  text = 'Pore water biodiffusion coefficient:')
        self.hbiowidget   = Entry(self.frame, width = 10,textvariable = self.hbio,  justify = 'center')
        self.sigmawidget  = Entry(self.frame, width = 10,textvariable = self.sigma,  justify = 'center')
        self.Dbiopwidget  = Entry(self.frame, width = 10,textvariable = self.Dbiop, justify = 'center')
        self.Dbiopwwidget = Entry(self.frame, width = 10,textvariable = self.Dbiopw,justify = 'center')
        self.hbiounits    = Label(self.frame, text = self.lengthunit)
        self.Dbiopunits   = Label(self.frame, text = self.diffunits[1])
        self.Dbiopwunits  = Label(self.frame, text = self.diffunits[1])

        self.conlabel     = Label(self.frame,  text = 'Modeling consolidation')
        self.conwidget    = OptionMenu(self.frame, self.con, *self.cons, command = self.updatesystem)
        self.hconlabel    = Label(self.frame,  text = 'Maximum consolidation depth:')
        self.t90label     = Label(self.frame,  text = 'Time to 90% consolidation:')
        self.hconwidget   = Entry(self.frame, width = 10,textvariable = self.hcon,  justify = 'center')
        self.t90widget    = Entry(self.frame, width = 10,textvariable = self.t90,   justify = 'center')
        self.hconunits    = Label(self.frame, text = self.lengthunit)
        self.t90units     = Label(self.frame, text = self.timeunit)

        self.advwidget.config(width = 20)
        self.biowidget.config(width = 20)
        self.conwidget.config(width = 20)
        
        #self.okbutton   = Button(self.frame, text = 'OK',         command = self.OK,       width = 20)

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 3, padx = 6, sticky = 'W')
        self.blank1.grid(row = 1, column = 0)
        self.blank2.grid(row = 1, column = 1)
        self.blank3.grid(row = 1, column = 2)
    
        self.row = 3
        
        self.focusbutton = None
        
        self.updatesystem()
            

    def updatesystem(self, event = None):

        try:
            self.advlabel.grid_forget()
            self.advwidget.grid_forget()
            self.Vdarlabel.grid_forget()
            self.Vdarwidget.grid_forget()
            self.Vdarunits.grid_forget()
            self.Vtidallabel.grid_forget()
            self.Vtidalwidget.grid_forget()
            self.Vtidalunits.grid_forget()
            self.ptidallabel.grid_forget()
            self.ptidalwidget.grid_forget()
            self.ptidalunits.grid_forget()
            
            self.biolabel.grid_forget()
            self.biowidget.grid_forget()
            self.sigmalabel.grid_forget()
            self.sigmawidget.grid_forget()
            self.hbiolabel.grid_forget()
            self.hbiowidget.grid_forget()
            self.hbiounits.grid_forget()
            self.Dbioplabel.grid_forget()
            self.Dbiopwidget.grid_forget()
            self.Dbiopunits.grid_forget()
            self.Dbiopwlabel.grid_forget()
            self.Dbiopwwidget.grid_forget()
            self.Dbiopwunits.grid_forget()

            self.conlabel.grid_forget()
            self.conwidget.grid_forget()
            self.hconlabel.grid_forget()
            self.hconwidget.grid_forget()
            self.hconunits.grid_forget()
            self.t90label.grid_forget()
            self.t90widget.grid_forget()
            self.t90units.grid_forget()
            
        except: pass

        row = self.row
        
        self.advlabel.grid(         row = row, column = 0, sticky = 'E', padx = 4)
        self.advwidget.grid(        row = row, column = 1, sticky = 'W', padx = 4, columnspan = 2)
        
        row = row + 1

        if self.adv.get() == self.advs[1] or self.adv.get() == self.advs[2]:
            
            self.Vdarlabel.grid(    row = row, column = 0, sticky = 'E', padx = 4)
            self.Vdarwidget.grid(   row = row, column = 1, pady = 1)
            self.Vdarunits.grid(    row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1
            
        if self.adv.get() == self.advs[2]:

            self.Vtidallabel.grid(  row = row, column = 0, sticky = 'E', padx = 4)
            self.Vtidalwidget.grid( row = row, column = 1, pady = 1)
            self.Vtidalunits.grid(  row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1
            
            self.ptidallabel.grid(  row = row, column = 0, sticky = 'E', padx = 4)
            self.ptidalwidget.grid( row = row, column = 1, pady = 1)
            self.ptidalunits.grid(  row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1
            
            
        self.biolabel.grid(         row = row, column = 0, sticky = 'E', padx = 4)
        self.biowidget.grid(        row = row, column = 1, sticky = 'W', padx = 4, columnspan = 2)

        row = row + 1
        
        if self.bio.get() == self.bios[1]:
            
            self.hbiolabel.grid(    row = row, column = 0, sticky = 'E', padx = 4)
            self.hbiowidget.grid(   row = row, column = 1, pady = 1)
            self.hbiounits.grid(    row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1

        if self.bio.get() == self.bios[2]:

            self.sigmalabel.grid(   row = row, column = 0, sticky = 'E', padx = 4)
            self.sigmawidget.grid(  row = row, column = 1, pady = 1)
            self.hbiounits.grid(    row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1

        if self.bio.get() == self.bios[1] or self.bio.get() == self.bios[2]:

            self.Dbioplabel.grid(   row = row, column = 0, sticky = 'E', padx = 4)
            self.Dbiopwidget.grid(  row = row, column = 1, pady = 1)
            self.Dbiopunits.grid(   row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1

            self.Dbiopwlabel.grid(  row = row, column = 0, sticky = 'E', padx = 4)
            self.Dbiopwwidget.grid( row = row, column = 1, pady = 1)
            self.Dbiopwunits.grid(  row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1

        self.conlabel.grid(         row = row, column = 0, sticky = 'E', padx = 4)
        self.conwidget.grid(        row = row, column = 1, sticky = 'W', padx = 4, columnspan = 2)

        row = row + 1
        
        if self.con.get() == self.cons[1]:
            self.hconlabel.grid(    row = row, column = 0, sticky = 'E', padx = 4)
            self.hconwidget.grid(   row = row, column = 1, pady = 1)
            self.hconunits.grid(    row = row, column = 2, sticky = 'W', padx = 4)

            row = row + 1

            self.t90label.grid(     row = row,   column = 0, sticky = 'E', padx = 4)
            self.t90widget.grid(    row = row,   column = 1, pady = 1)
            self.t90units.grid(     row = row,   column = 2, sticky = 'W', padx = 4)

            row = row + 1
            
        self.blank4.grid(           row = row)

        row = row + 1
        
        self.focusbutton = None
        
        self.master.geometry()

    def error_check(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error = 0
        #if self.bio.get() == self.bios[1] and self.hbio.get() > self.toplayer_h: error = 1

        return error

    def warning(self):

        tkmb.showerror(title = self.version, message = 'The bioturbation '   +
                       'depth (%.1f cm) ' % self.hbio.get() + 'cannot exceed the ' +
                       'thickness of the top layer (%.1f). ' %self.toplayer_h + 'Automatically increasing '  +
                       'the thickness of the top layer to the bioturbation ' +
                       'depth.')
        self.hbio.set(self.toplayer_h)
        self.focusbutton = None
        self.master.tk.lift()

def get_systemproperties(system, step):
    """Get flow and system parameters."""

    root = CapSimWindow(buttons = 1)
    root.make_window(SystemProperties(root, system))
    root.mainloop()
    
    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_systemproperties(root.window)
        else:
            system.adv    = 'None'
            system.bio    = 'None'
            system.con    = 'None'

            system.Vdar   = 0
            system.Vtidal = 0
            system.ptidal = 1
            system.sigma  = 10
            system.hbio   = 10
            system.Dbiop  = 1
            system.Dbiopw = 100
            system.hcon   = 0
            system.t90    = 1

    root.destroy()
    
    return system, step + root.step.get()
