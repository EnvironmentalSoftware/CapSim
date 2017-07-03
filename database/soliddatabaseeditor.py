#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical, Solid
from capsim_functions    import get_superfont
from database            import Database
import tkFont

class SolidDatabaseEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, solid, solid_database, editflag):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                   #flag for existence of toplevel#

        
        self.solid     = solid
        self.solid_database  = solid_database
        
        self.torts     = ['Millington & Quirk', 'Boudreau', 'None']
        self.sorps     = ['Linear--Kd specified', 'Linear--Kocfoc', 'Freundlich', 'Langmuir']

        self.name          = StringVar(value = 'Solid '+str(solid_database[-1].number))     #stores the chemical name
        self.e             = DoubleVar(value = 0.5)                                         #stores the porosity
        self.rho           = DoubleVar(value = 1.0)                                         #stores the bulk density
        self.foc           = DoubleVar(value = 0.01)                                        #stores the organic carbon fraction
        self.tort          = StringVar(value = self.torts[0])                               #stores the default tortuosity correction
        self.sorp          = StringVar(value = self.sorps[0])                               #stores the default sorption correction
        self.Ref           = StringVar(value = '')                                          #stores the density

        self.editflag   = editflag
        self.cancelflag = 0
        
        if editflag == 1:                       #Detemine whether the chemical is added or edited
            
            self.name.set(solid.name)
            self.e.set(   solid.e)
            self.rho.set( solid.rho)
            self.foc.set( solid.foc)
            self.tort.set(solid.tort)
            self.sorp.set(solid.sorp)
            self.Ref.set(solid.Ref)

    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Please provide the following properties for the solid/mixture:                    ')
                
        self.blankcolumn  = Label(self.frame,  text =' ', width = 1)
        self.namecolumn   = Label(self.frame,  text =' ', width = 18)
        self.ecolumn      = Label(self.frame,  text =' ', width = 10)
        self.rhocolumn    = Label(self.frame,  text =' ', width = 10)
        self.foccolumn    = Label(self.frame,  text =' ', width = 10)
        self.tortcolumn   = Label(self.frame,  text =' ', width = 18)
        self.sorpcolumn   = Label(self.frame,  text =' ', width = 20)
        self.refcolumn    = Label(self.frame,  text =' ', width = 18)
        self.endcolumn    = Label(self.frame,  text =' ', width = 2)

        self.namelabel    = Label(self.frame,  text = 'Material')
        self.elabel       = Label(self.frame,  text = 'Porosity')
        self.rholabel     = Label(self.frame,  text = 'Bulk density')
        self.foclabel     = Label(self.frame,  text = 'Organic carbon fraction')
        self.tortlabel    = Label(self.frame,  text = 'Tortruosity correction')
        self.sorplabel    = Label(self.frame,  text = 'Sorption isotherms')
        self.reflabel     = Label(self.frame,  text = 'Reference')

        self.rhounitlabel = Label(self.frame,  text = u'g/cm\u00B3')

        self.namewidget   = Entry(self.frame, width = 16, justify = 'center', textvariable = self.name)
        self.ewidget      = Entry(self.frame, width = 8, justify = 'center', textvariable = self.e)
        self.rhowidget    = Entry(self.frame, width = 8, justify = 'center', textvariable = self.rho)
        self.focwidget    = Entry(self.frame, width = 8, justify = 'center', textvariable = self.foc)
        self.tortwidget   = OptionMenu(self.frame, self.tort, *self.torts)
        self.sorpwidget   = OptionMenu(self.frame, self.sorp, *self.sorps)
        self.refwidget    = Entry(self.frame, width = 15, justify = 'center', textvariable = self.Ref)

        self.okbutton     = Button(self.frame, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 7, padx = 8, sticky = 'W')
        
        self.blankcolumn.grid(  row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)        
        self.namecolumn.grid(   row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.ecolumn.grid(      row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.rhocolumn.grid(    row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foccolumn.grid(    row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.tortcolumn.grid(   row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.sorpcolumn.grid(   row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.refcolumn.grid(    row    = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.endcolumn.grid(    row    = 1, column = 8, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.elabel.grid(       row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.rholabel  .grid(   row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.tortlabel.grid(    row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.sorplabel.grid(    row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.reflabel.grid(     row    = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)

        self.rhounitlabel.grid(    row = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)

        self.namewidget.grid(   row    = 4, column = 1, padx = 1, pady = 1)
        self.ewidget.grid  (    row    = 4, column = 2, padx = 1 ,pady = 1)
        self.rhowidget.grid (   row    = 4, column = 3, padx = 1 ,pady = 1)
        self.focwidget.grid(    row    = 4, column = 4, padx = 1 ,pady = 1)
        self.tortwidget.grid (  row    = 4, column = 5, padx = 1 ,pady = 1, sticky = 'WE')
        self.sorpwidget.grid(   row    = 4, column = 6, padx = 1 ,pady = 1, sticky = 'WE')
        self.refwidget.grid(    row    = 4, column = 7, padx = 1 ,pady = 1)

        self.blank1.grid(       row    = 5)
        self.okbutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank2.grid(       row    = 8)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton
                   
    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
        
        if self.editflag == 0:
           check =[(solid.name == self.name.get()) for solid in self.solid_database[0:-1]]
        if self.editflag == 1:
           check =[(solid.name == self.name.get() and self.solid.name != self.name.get()) for solid in self.solid_database[0:-1]]
            
        if self.master.window.top is not None: self.master.open_toplevel()
        elif self.e.get() > 1 or self.e.get() < 0:
             tkmb.showinfo(self.version, 'The porosity of a solid can not be larger than 1 or smaller than 0')
             self.e.set(0.5)
        elif self.rho.get() < 0:
            tkmb.showinfo(self.version, 'The bulk density of a solid can not be negative')
            self.e.set(1.0)
        elif self.foc.get() > 1 or self.foc.get() < 0: 
            tkmb.showinfo(self.version, 'The organic carbon fraction of a solid can not be larger than 1 or smaller than 0')
            self.e.set(1.0)
        elif sum(check) >= 1 or self.name.get() == '': self.solids_error()
        else: self.master.tk.quit()
        
    def solids_error(self):

        tkmb.showerror(title = self.version, message = 'This solid material has already been added to the database!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.name.set(self.solid.name)
            self.e.set(   self.solid.e)
            self.rho.set( self.solid.rho)
            self.foc.set( self.solid.foc)
            self.tort.set(self.solid.tort)
            self.sorp.set(self.solid.sorp)
            self.Ref.set(self.solid.Ref)
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
class SolidDatabaseDeleter:
    
    def __init__(self, master, system, solid):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master        = master
        self.fonttype      = system.fonttype
        self.version       = system.version
        self.superfont     = get_superfont(self.fonttype) #superscript font
        self.tframe        = Frame(master.tframe)
        self.frame         = Frame(master.frame)
        self.bframe        = Frame(master.bframe)
        self.top       = None                   #flag for existence of toplevel#
                
        self.name          = StringVar(value = solid.name)      #stores the chemical name
        self.e             = DoubleVar(value = solid.e)         #stores the porosity
        self.rho           = DoubleVar(value = solid.rho)       #stores the bulk density
        self.foc           = DoubleVar(value = solid.foc)       #stores the organic carbon fraction
        self.tort          = StringVar(value = solid.tort)      #stores the default tortuosity correction
        self.sorp          = StringVar(value = solid.sorp)      #stores the default sorption correction
        self.Ref           = StringVar(value = solid.Ref)      #stores the default sorption correction

        self.cancelflag = 0

    def make_widgets(self):
    
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Are you sure to delete the following solid from database?        ')
                
        self.namelabel    = Label(self.frame,  text = 'Material')
        self.elabel       = Label(self.frame,  text = 'Porosity')
        self.rholabel     = Label(self.frame,  text = 'Bulk density\n (kg/L')
        self.foclabel     = Label(self.frame,  text = 'Organic carbon\n fraction')
        self.tortlabel    = Label(self.frame,  text = 'Tortruosity correction')
        self.sorplabel    = Label(self.frame,  text = 'Sorption isotherms')
        self.Reflabel     = Label(self.frame,  text = 'Reference')

        self.rhounitlabel = Label(self.frame,  text = u'g/cm\u00B3')

        self.namewidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.name)
        self.ewidget      = Label(self.frame, width = 8, justify = 'center', textvariable = self.e)
        self.rhowidget    = Label(self.frame, width = 8, justify = 'center', textvariable = self.rho)
        self.focwidget    = Label(self.frame, width = 8, justify = 'center', textvariable = self.foc)
        self.tortwidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.tort)
        self.sorpwidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.sorp)
        self.Refwidget    = Label(self.frame, width = 10, justify = 'center', textvariable = self.Ref)

        self.blankcolumn  = Label(self.frame,  text =' ', width = 1)
        self.namecolumn   = Label(self.frame,  text =' ', width = 18)
        self.ecolumn      = Label(self.frame,  text =' ', width = 10)
        self.rhocolumn    = Label(self.frame,  text =' ', width = 10)
        self.foccolumn    = Label(self.frame,  text =' ', width = 10)
        self.tortcolumn   = Label(self.frame,  text =' ', width = 18)
        self.sorpcolumn   = Label(self.frame,  text =' ', width = 18)
        self.Refcolumn    = Label(self.frame,  text =' ', width = 18)
        self.endcolumn    = Label(self.frame,  text =' ', width = 2)

        self.deletebutton = Button(self.frame, text = 'Delete', width = 20, command = self.Delete)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')
        
        self.blankcolumn.grid(  row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)        
        self.namecolumn.grid(   row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.ecolumn.grid(      row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.rhocolumn.grid(    row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foccolumn.grid(    row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.tortcolumn.grid(   row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.sorpcolumn.grid(   row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Refcolumn.grid(    row    = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.endcolumn.grid(    row    = 1, column = 8, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.elabel.grid(       row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.rholabel  .grid(   row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.tortlabel.grid(    row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.sorplabel.grid(    row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Reflabel.grid(     row    = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)

        self.rhounitlabel.grid( row    = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)

        self.namewidget.grid(   row    = 4, column = 1, padx = 1, pady = 1, sticky = 'WE')
        self.ewidget.grid  (    row    = 4, column = 2, padx = 1 ,pady = 1)
        self.rhowidget.grid (   row    = 4, column = 3, padx = 1 ,pady = 1)
        self.focwidget.grid(    row    = 4, column = 4, padx = 1 ,pady = 1)
        self.tortwidget.grid (  row    = 4, column = 5, padx = 1 ,pady = 1)
        self.sorpwidget.grid(   row    = 4, column = 6, padx = 1 ,pady = 1)
        self.Refwidget.grid(    row    = 4, column = 7, padx = 1, pady = 1)

        self.blank1.grid(       row    = 5)
        self.deletebutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank2.grid(       row    = 8)
        self.deletebutton.bind('<Return>', self.Delete)
        self.focusbutton = self.deletebutton
        
    def Delete(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
        
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def Cancel(self):
        
        try:
            self.name.set(self.solid.name)
            self.e.set(   self.solid.e)
            self.rho.set( self.solid.rho)
            self.foc.set( self.solid.foc)
            self.tort.set(self.solid.tort)
            self.sorp.set(self.solid.sorp)
            self.Ref.set(self.solid.Ref)
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

class SolidDatabaseImporter:

    def __init__(self, master, system, database_imported):
        """The constructor method."""

        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.tframe        = Frame(master.tframe)
        self.frame         = Frame(master.frame)
        self.bframe        = Frame(master.bframe)
        self.tkfont        = tkFont.Font(font = system.fonttype)

        solids_list = database_imported.keys()
        solids_list.sort()

        self.solids_list = solids_list

        self.name_width    = 10

        for chemical_name in self.solids_list:
            if (self.tkfont.measure(chemical_name) + 10) > self.name_width: self.name_width = self.tkfont.measure(chemical_name) + 10

        if self.name_width < 150: self.name_width = 150


        self.solids = []
        for solidname in self.solids_list:
            self.solids.append(Solid(solids_list.index(solidname)))
            self.solids[-1].read_database(database_imported[solidname])

        self.sname     = StringVar(self.frame, value = '')

        self.cancelflag      = 0

    def make_widgets(self):

        self.instructions     = Label(self.tframe,  text = 'Please select the chemical you would like to added to the database       ')

        self.leftcolumn       = Label(self.tframe,  text = ' ', font = 'courier 10', width = 2)
        self.checkcolumn      = Label(self.tframe,  text = ' ', font = 'courier 10', width = 5)
        self.orinamecolumn    = Label(self.tframe,  text = ' ', font = 'courier 10', width = int(self.name_width*1.1424219345/8)+1)
        self.impnamecolumn1   = Label(self.tframe,  text = ' ', font = 'courier 10', width = int(self.name_width*1.1424219345/8/2)+1)
        self.impnamecolumn2   = Label(self.tframe,  text = ' ', font = 'courier 10', width = int(self.name_width*1.1424219345/8/2)+1)
        self.rightcolumn      = Label(self.tframe,  text = ' ', font = 'courier 10', width = 2)

        self.search_label     = Label( self.tframe,  text          = 'Search:')
        self.search_entry     = Entry( self.tframe,  textvariable  = self.sname)

        self.orinamelabel     = Label(self.tframe,  text = 'Original Name')
        self.impnamelabel     = Label(self.tframe,  text = 'Imported Name')
        self.blank1           = Label(self.tframe, text = ' ')

        self.botleftcolumn       = Label(self.frame,  text = ' ', width = 2)
        self.botcheckcolumn      = Label(self.frame,  text = ' ', width = 5)
        self.botorinamecolumn    = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8)+1)
        self.botimpnamecolumn1   = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.botimpnamecolumn2   = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.botrightcolumn      = Label(self.frame,  text = ' ', width = 2)

        self.allbutton        = Button(self.bframe, text = 'Select All',   command = self.selectall,      width = 20)
        self.unallbutton      = Button(self.bframe, text = 'Unselect All', command = self.unselectall,    width = 20)
        self.importbutton     = Button(self.bframe, text = 'Import',       command = self.OK,             width = 20)
        self.cancelbutton     = Button(self.bframe, text = 'Cancel',       command = self.cancel,         width = 20)

        self.blank2           = Label(self.bframe, text = ' ')
        self.blank3           = Label(self.bframe, text = ' ')
        self.blank4           = Label(self.frame,  text = ' ')

        #show the widgets on the grid (top to bottom and left to right)


        self.instructions.grid(     row = 0, columnspan = 5, sticky = 'W', padx = 8)

        self.leftcolumn.grid(       row = 1, column = 0, sticky = 'WE')
        self.checkcolumn.grid(      row = 1, column = 1, sticky = 'WE')
        self.orinamecolumn.grid(    row = 1, column = 2, sticky = 'WE')
        self.impnamecolumn1.grid(   row = 1, column = 3, sticky = 'WE')
        self.impnamecolumn2.grid(   row = 1, column = 4, sticky = 'WE')
        self.rightcolumn.grid(      row = 1, column = 5, sticky = 'WE')

        self.search_label.grid(     row = 2, column = 1, sticky = 'E'                 , padx = 4)
        self.search_entry.grid(     row = 2, column = 2, columnspan = 3, sticky = 'WE', padx = 4)

        self.blank1.grid(row = 3)

        self.orinamelabel.grid(        row = 4, column = 2,                 sticky = 'WE')
        self.impnamelabel.grid(        row = 4, column = 3, columnspan = 2, sticky = 'WE')

        self.botleftcolumn.grid(       row = 1, column = 0, sticky = 'WE')
        self.botcheckcolumn.grid(      row = 1, column = 1, sticky = 'WE')
        self.botorinamecolumn.grid(    row = 1, column = 2, sticky = 'WE')
        self.botimpnamecolumn1.grid(   row = 1, column = 3, sticky = 'WE')
        self.botimpnamecolumn2.grid(   row = 1, column = 4, sticky = 'WE')
        self.botrightcolumn.grid(      row = 1, column = 5, sticky = 'WE')

        self.searchname()

        self.sname.trace('w', self.searchname)

    def searchname(self, event = None, *args):

        row = 2

        for solid in self.solids:
            try: solid.remove_importedsolidwidgets()
            except: pass

        if self.sname.get() == '':
            for solid in self.solids:
                if solid.check == 1:
                    solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                    row = row + 1

            for solid in self.solids:
                if solid.check == 0:
                    solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                    row = row + 1
        else:
            for solid in self.solids:
                if solid.name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                    if solid.check == 1:
                        solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                        row = row + 1

            for solid in self.solids:
                if solid.name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                    if solid.check == 0:
                        solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                        row = row + 1
                else:
                    solid.check = IntVar(value = solid.check)

        self.blank4.grid(row = row)

        row = 2

        self.blank2.grid(row = row)
        row = row + 1
        self.allbutton.grid(   row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.unallbutton.grid( row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.importbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.cancelbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.blank3.grid(      row = row)

        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.cancelbutton


    def updatename(self, event = None):

        row = 2

        for solid in self.solids:
            try: solid.remove_importedsolidwidgets()
            except: pass

        for solid in self.solids:
            if solid.check == 1:
                solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                row = row + 1

        for solid in self.solids:
            if solid.check == 0:
                solid.importedsolidwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                row = row + 1

        self.blank4.grid(row = row)

        row = 2

        self.blank2.grid(row = row)
        row = row + 1
        self.updatebutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.allbutton.grid(   row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.unallbutton.grid( row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.importbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.cancelbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.blank3.grid(      row = row)

        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.cancelbutton

    def selectall(self, event = None):

        for solid in self.solids:
            if solid.name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                solid.check.set(1)

    def unselectall(self, event = None):

        for solid in self.solids:
            if solid.name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                solid.check.set(0)

    def OK(self, event = None):

        for solid in self.solids:
            solid.get_importedsolid()

        self.frame.quit()

    def cancel(self, event = None):

        self.cancelflag = 1
        self.frame.quit()
