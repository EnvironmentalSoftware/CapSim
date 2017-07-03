#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical
from capsim_functions    import get_superfont
from database            import Database
from chemicaleditor      import ChemicalEditor, ChemicalDeleter

class ChemicalProperties:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, database):
        
        """Constructor method. Defines the parameters to be obtained in this window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                   #flag for existence of toplevel#

        self.system    = system
        self.database  = database        
        self.diffunit  = system.diffunit
        self.concunit  = system.concunit
        self.concunits = system.concunits

        if system.chemicals is None:
            self.chemicals  = []
            self.nchemicals = 0
        else:
            self.chemicals  = system.chemicals
            self.nchemicals = system.nchemicals


    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')

        # Construct all label widgets used in the problem
        self.instructions = Label(self.tframe, text = ' Please provide the following chemical properties:                    ')

        self.blankcolumn  = Label(self.tframe,  text ='', width = 1)
        self.editcolumn   = Label(self.tframe,  text ='', width = 6)
        self.delcolumn    = Label(self.tframe,  text ='', width = 6)
        self.numbercolumn = Label(self.tframe,  text ='', width = 6)
        self.namecolumn   = Label(self.tframe,  text ='', width = 18)
        self.MWcolumn     = Label(self.tframe,  text ='', width = 8)
        self.tempcolumn   = Label(self.tframe,  text ='', width = 10)
        self.Dwcolumn     = Label(self.tframe,  text ='', width = 16)
        self.Koccolumn    = Label(self.tframe,  text ='', width = 16)
        self.Kdoccolumn   = Label(self.tframe,  text ='', width = 18)
        self.Refcolumn    = Label(self.tframe,  text ='', width = 17)
        self.endcolumn    = Label(self.tframe,  text ='', width = 1)

        self.botblankcolumn  = Label(self.frame,  text ='', width = 1)
        self.boteditcolumn   = Label(self.frame,  text ='', width = 6)
        self.botdelcolumn    = Label(self.frame,  text ='', width = 6)
        self.botnumbercolumn = Label(self.frame,  text ='', width = 6)
        self.botnamecolumn   = Label(self.frame,  text ='', width = 18)
        self.botMWcolumn     = Label(self.frame,  text ='', width = 8)
        self.bottempcolumn   = Label(self.frame,  text ='', width = 10)
        self.botDwcolumn     = Label(self.frame,  text ='', width = 16)
        self.botKoccolumn    = Label(self.frame,  text ='', width = 16)
        self.botKdoccolumn   = Label(self.frame,  text ='', width = 18)
        self.botRefcolumn    = Label(self.frame,  text ='', width = 17)
        self.botendcolumn    = Label(self.frame,  text ='', width = 1)

        self.numberlabel  = Label(self.tframe,  text = 'Number')
        self.namelabel    = Label(self.tframe,  text = 'Chemical name')
        self.MWlabel      = Label(self.tframe,  text = 'Molecular\n Weight')
        self.templabel    = Label(self.tframe,  text = 'Temperature')
        self.Dwlabel      = Label(self.tframe,  text = 'Molecular diffusivity\n in water')
        self.Koclabel     = Label(self.tframe,  text = 'Organic carbon\n partition coefficient')
        self.Kdoclabel    = Label(self.tframe,  text = 'Dissolved organic carbon\n partition coefficient')
        self.Reflabel     = Label(self.tframe,  text = 'Reference')

        self.tempunits    = Label(self.tframe,  text = unichr(176) + 'C')
        self.Dwunits      = Label(self.tframe,  text = self.diffunit)
        self.Kocunits     = Label(self.tframe,  text = 'log(L/kg)')
        self.Kdocunits    = Label(self.tframe,  text = 'log(L/kg)')
        
        self.blank1 = Label(self.frame,  text = ' ')
        self.blank2 = Label(self.bframe, text = ' ')

        self.addwidget  = Button(self.bframe, text = 'Add chemicals', command = self.addchemical, width = 20)

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 9, padx = 1, sticky = 'W')
        
        self.blankcolumn.grid(  row    = 1, column = 0,  sticky = 'WE', padx = 1, pady = 1)
        self.editcolumn.grid(   row    = 1, column = 1,  sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(    row    = 1, column = 2,  sticky = 'WE', padx = 1, pady = 1)
        self.numbercolumn.grid( row    = 1, column = 3,  sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(   row    = 1, column = 4,  sticky = 'WE', padx = 1, pady = 1)
        self.MWcolumn.grid(     row    = 1, column = 5,  sticky = 'WE', padx = 1, pady = 1)
        self.tempcolumn.grid(   row    = 1, column = 6,  sticky = 'WE', padx = 1, pady = 1)
        self.Dwcolumn.grid(     row    = 1, column = 7,  sticky = 'WE', padx = 1, pady = 1)
        self.Koccolumn.grid(    row    = 1, column = 8,  sticky = 'WE', padx = 1, pady = 1)
        self.Kdoccolumn.grid(   row    = 1, column = 9,  sticky = 'WE', padx = 1, pady = 1)
        self.Refcolumn.grid(    row    = 1, column = 10, sticky = 'WE', padx = 1, pady = 1)
        self.endcolumn.grid(    row    = 1, column = 11, sticky = 'WE', padx = 1, pady = 1)

        self.numberlabel.grid(  row    = 2, column = 3,  sticky = 'WE', padx = 1, pady = 1)
        self.namelabel.grid(    row    = 2, column = 4,  sticky = 'WE', padx = 1, pady = 1)
        self.MWlabel.grid(      row    = 2, column = 5,  sticky = 'WE', padx = 1, pady = 1)
        self.templabel.grid(    row    = 2, column = 6,  sticky = 'WE', padx = 1, pady = 1)
        self.Dwlabel  .grid(    row    = 2, column = 7,  sticky = 'WE', padx = 1, pady = 1)
        self.Koclabel .grid(    row    = 2, column = 8,  sticky = 'WE', padx = 1, pady = 1)
        self.Kdoclabel.grid(    row    = 2, column = 9,  sticky = 'WE', padx = 1, pady = 1)
        self.Reflabel.grid(     row    = 2, column = 10, sticky = 'WE', padx = 1, pady = 1)

        self.tempunits.grid(    row    = 3, column = 6,  sticky = 'WE', padx = 1, pady = 1)
        self.Dwunits.grid  (    row    = 3, column = 7,  sticky = 'WE', padx = 1, pady = 1)
        self.Kocunits.grid (    row    = 3, column = 8,  sticky = 'WE', padx = 1, pady = 1)
        self.Kdocunits.grid(    row    = 3, column = 9,  sticky = 'WE', padx = 1, pady = 1)
        
        self.updatechemicals()
        

    def updatechemicals(self):

        try:
            self.botblankcolumn.grid_forget()
            self.boteditcolumn.grid_forget()
            self.botdelcolumn.grid_forget()
            self.botnumbercolumn.grid_forget()
            self.botnamecolumn.grid_forget()
            self.botMWcolumn.grid_forget()
            self.bottempcolumn.grid_forget()
            self.botDwcolumn.grid_forget()
            self.botKoccolumn.grid_forget()
            self.botKdoccolumn.grid_forget()
            self.botRefcolumn.grid_forget()
            self.botendcolumn.grid_forget()
        except: pass

        chemicals_list = self.database.keys()
        for chemical in self.chemicals:
            if chemical.soluable == 1:
                try: chemicals_list.remove(chemical.name)
                except: pass
            
        self.addwidget.grid_forget()

        namelabellength = 18
        reflabellength  = 18

        row = 0

        for chemical in self.chemicals:
            try: chemical.remove_chemicalwidgets()
            except:pass
            chemical.number = self.chemicals.index(chemical) + 1
            chemical.chemicalwidgets(self.frame, row, self.master)
            row = row + 1

            if namelabellength < chemical.namelabel.winfo_reqwidth()/8:               namelabellength = int(chemical.namelabel.winfo_reqwidth()/8) + 1
            if reflabellength  < chemical.Reflabel.winfo_reqwidth()/8*1.1424219345:   reflabellength  = int(chemical.Reflabel.winfo_reqwidth()/8*1.1424219345) + 1

        self.namecolumn.config(width = namelabellength)
        self.Refcolumn.config( width = reflabellength)
        self.botnamecolumn.config(width = namelabellength)
        self.botRefcolumn.config( width = reflabellength)

        self.botblankcolumn.grid(   row   = row, column = 0,  sticky = 'WE', padx = 1, pady = 1)
        self.boteditcolumn.grid(   row    = row, column = 1,  sticky = 'WE', padx = 1, pady = 1)
        self.botdelcolumn.grid(    row    = row, column = 2,  sticky = 'WE', padx = 1, pady = 1)
        self.botnumbercolumn.grid( row    = row, column = 3,  sticky = 'WE', padx = 1, pady = 1)
        self.botnamecolumn.grid(   row    = row, column = 4,  sticky = 'WE', padx = 1, pady = 1)
        self.botMWcolumn.grid(     row    = row, column = 5,  sticky = 'WE', padx = 1, pady = 1)
        self.bottempcolumn.grid(   row    = row, column = 6,  sticky = 'WE', padx = 1, pady = 1)
        self.botDwcolumn.grid(     row    = row, column = 7,  sticky = 'WE', padx = 1, pady = 1)
        self.botKoccolumn.grid(    row    = row, column = 8,  sticky = 'WE', padx = 1, pady = 1)
        self.botKdoccolumn.grid(   row    = row, column = 9,  sticky = 'WE', padx = 1, pady = 1)
        self.botRefcolumn.grid(    row    = row, column = 10, sticky = 'WE', padx = 1, pady = 1)
        self.botendcolumn.grid(    row    = row, column = 11, sticky = 'WE', padx = 1, pady = 1)

        row = 0
        self.blank2.grid(row = row)
        row = row + 1
        if len(chemicals_list) > 0:
            self.addwidget.grid(row = row, columnspan = 11)
            row = row + 1

        self.addwidget.bind('<Return>', self.addchemical)

        if self.nchemicals == 0: self.focusbutton = self.addwidget
        else:                    self.focusbutton = None

        self.master.geometry()
        self.master.center()


    def addchemical(self, event = None):

        self.nchemicals = self.nchemicals + 1
        self.chemicals.append(Chemical(self.nchemicals, soluable = 1))

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ChemicalEditor(self.top, self.system, self.chemicals[-1], self.chemicals, self.database, editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.chemicals[-1].get_chemical(self.top.window)
            else:
                self.chemicals.remove(self.chemicals[-1])
                self.nchemicals = self.nchemicals - 1
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatechemicals()

    def editchemical(self, number):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ChemicalEditor(self.top, self.system, self.chemicals[number-1], self.chemicals, self.database, editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.chemicals[number-1].get_chemical(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatechemicals()
        
    def deletechemical(self, number):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ChemicalDeleter(self.top, self.system, self.chemicals[number-1]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.chemicals[number-1].remove_chemicalwidgets()
                self.chemicals.remove(self.chemicals[number-1])
                self.nchemicals = self.nchemicals - 1
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        self.updatechemicals()


    def error_check(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error = 0
        if self.nchemicals == 0: error = 1

        return error

    def warning(self):

        tkmb.showerror(title = self.version, message = 'No chemical has been selected, please add chemicals by pressing the button "Add chemicals"')
        self.focusbutton = None
        self.master.tk.lift()
                    
def get_chemicalproperties(system, database, step):
    """Get some basic parameters for each layer."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(ChemicalProperties(root, system, database))
    root.mainloop()
    
    if root.main.get() == 1:    system = None
    else:
        if root.step.get() == 1:
            system.get_chemicalproperties(root.window)
            for chemical in system.chemicals: chemical.remove_chemicalwidgets()
        else:
            system.chemicals = None
            system.nchemical =  0
        
    root.destroy()

    return system, step + root.step.get()

        
        
