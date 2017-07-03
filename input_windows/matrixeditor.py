#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, MatrixComponent
from capsim_functions    import get_superfont
    
class MatrixEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, matrix, matrices, materials, editflag, newflag):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype)                                       #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                                                               #flag for existence of toplevel#

        
        self.matrix    = matrix
        self.matrices  = matrices
        self.materials = materials
                
        self.matrices_list = self.materials.keys()
        self.matrices_list.sort()
        for matrix in (self.matrices):
            if matrix.number <> self.matrix.number and len(matrix.components) == 1 and self.matrices_list.count(matrix.name) > 0: self.matrices_list.remove(matrix.name)

        self.model         = StringVar(value = 'Linear')                                    #Define the imaginary model for the components
    
        self.name          = StringVar(value = self.matrices_list[0])                       #matrix name
        self.e             = DoubleVar(value = 0.5)                                         #stores the porosity
        self.rho           = DoubleVar(value = 1.0)                                         #stores the bulk density
        self.foc           = DoubleVar(value = 0.01)                                        #stores the organic carbon fraction

        self.editflag   = editflag
        self.newflag    = newflag
        self.cancelflag = 0

        if editflag == 0:
            self.components         = [MatrixComponent(1)]                                      #Define components

        if editflag == 1:                                                                   #Detemine whether the chemical is added or edited

            self.components = self.matrix.components
            self.name.set(    self.matrix.name)
            self.model.set(   self.matrix.model)
            self.e.set(       self.matrix.e)
            self.rho.set(     self.matrix.rho)
            self.foc.set(     self.matrix.foc)
        
    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Please provide the following properties for the matrix:                    ')
                
        self.blankcolumn  = Label(self.frame,  text =' ', width = 1)
        self.namecolumn   = Label(self.frame,  text =' ', width = 20)
        self.ecolumn      = Label(self.frame,  text =' ', width = 14)
        self.rhocolumn    = Label(self.frame,  text =' ', width = 15)
        self.foccolumn    = Label(self.frame,  text =' ', width = 15)

        self.namelabel    = Label(self.frame,  text = 'Material')
        self.elabel       = Label(self.frame,  text = 'Porosity')
        self.rholabel     = Label(self.frame,  text = 'Bulk density ('+u'g/cm\u00B3'+')')
        self.foclabel     = Label(self.frame,  text = 'Organic carbon fraction')

        if self.editflag  == 1: 
            self.namewidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.name)
        else:
            if self.newflag == 0:
                self.namewidget   = OptionMenu(self.frame, self.name, *self.matrices_list, command = self.click_matrix)
            else:
                self.name.set('Matrix')
                self.namewidget   = Entry(self.frame, width = 16, justify = 'center', textvariable = self.name)
        self.ewidget      = Entry(self.frame, width = 10, justify = 'center', textvariable = self.e)
        self.rhowidget    = Entry(self.frame, width = 10, justify = 'center', textvariable = self.rho)
        self.focwidget    = Entry(self.frame, width = 10, justify = 'center', textvariable = self.foc)
        
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

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 4, pady = 1)
        self.elabel.grid(       row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.rholabel  .grid(   row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)

        if self.newflag == 0: self.namewidget.grid(   row    = 4, column = 1, sticky = 'WE', padx = 6, pady = 1)
        else:                 self.namewidget.grid(   row    = 4, column = 1,                padx = 6, pady = 1)
        self.ewidget.grid  (    row    = 4, column = 2, padx = 6 ,pady = 1)
        self.rhowidget.grid (   row    = 4, column = 3, padx = 6 ,pady = 1)
        self.focwidget.grid(    row    = 4, column = 4, padx = 6 ,pady = 1)
        
        self.blank1.grid(       row    = 5)
        self.okbutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank2.grid(       row    = 8)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton
        
        if self.editflag == 0 and self.newflag == 0: self.click_matrix()
                   
    def click_matrix(self, event = None):
        """Pulls up the contaminant properties from the database after selecting
        a compound."""

        self.tort = self.materials[self.name.get()].tort
        self.sorp = self.materials[self.name.get()].sorp
        self.e.set  (self.materials[self.name.get()].e)
        self.rho.set(self.materials[self.name.get()].rho)
        self.foc.set(self.materials[self.name.get()].foc)

        self.frame.update()
        self.master.geometry()
        self.master.center()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
        
        if self.editflag == 0:
           check =[(matrix.name == self.name.get()) for matrix in self.matrices[0:-1]]
        if self.editflag == 1:
           check =[0]
            
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
        elif sum(check) >= 1 or self.name.get() == '': self.matrix_error()
        else:
            self.components[0].name      = self.name.get()
            self.components[0].mfraction = 1.
            self.components[0].fraction  = 1.
            self.components[0].e         = self.e.get()
            self.components[0].rho       = self.rho.get()
            self.components[0].foc       = self.foc.get()

            if self.editflag == 0:
                if self.newflag == 0:
                    self.components[0].tort = self.materials[self.name.get()].tort
                    self.components[0].sorp = self.materials[self.name.get()].sorp
                else:
                    self.components[0].tort = 'Millington & Quirk'
                    self.components[0].sorp = 'Linear--Kd specified'

            self.master.tk.quit()
        
    def matrix_error(self):

        tkmb.showerror(title = self.version, message = 'This solid material has already been added to the database!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.name.set(self.matrix.name)
            self.model.set(self.matrix.model)
            self.e.set(   self.matrix.e)
            self.rho.set( self.matrix.rho)
            self.foc.set( self.matrix.foc)
            self.components = self.matrix.components
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
class MatrixDeleter:
    
    def __init__(self, master, system, matrix):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master        = master
        self.fonttype      = system.fonttype
        self.version       = system.version
        self.superfont     = get_superfont(self.fonttype) #superscript font
        self.tframe        = Frame(master.tframe)
        self.frame         = Frame(master.frame)
        self.bframe        = Frame(master.bframe)
        self.top           = None                   #flag for existence of toplevel#

        self.matrix        = matrix                
        self.name          = StringVar(value = matrix.name)      #stores the chemical name
        self.model         = StringVar(value = matrix.model)      #stores the chemical name
        self.e             = DoubleVar(value = matrix.e)         #stores the porosity
        self.rho           = DoubleVar(value = matrix.rho)       #stores the bulk density
        self.foc           = DoubleVar(value = matrix.foc)       #stores the organic carbon fraction
        
        self.cancelflag = 0

    def make_widgets(self):
    
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Are you sure to delete the following matrix?        ')
                
        self.namelabel    = Label(self.frame,  text = 'Material')
        self.elabel       = Label(self.frame,  text = 'Porosity')
        self.rholabel     = Label(self.frame,  text = 'Bulk density ('+ u'g/cm\u00B3'+')')
        self.foclabel     = Label(self.frame,  text = 'Organic carbon\n fraction')

        self.namewidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.name)                
        self.ewidget      = Label(self.frame, width = 16, justify = 'center', textvariable = self.e)
        self.rhowidget    = Label(self.frame, width = 16, justify = 'center', textvariable = self.rho)
        self.focwidget    = Label(self.frame, width = 16, justify = 'center', textvariable = self.foc)

        self.blankcolumn  = Label(self.frame,  text =' ', width = 1)
        self.namecolumn   = Label(self.frame,  text =' ', width = 20)
        self.ecolumn      = Label(self.frame,  text =' ', width = 14)
        self.rhocolumn    = Label(self.frame,  text =' ', width = 15)
        self.foccolumn    = Label(self.frame,  text =' ', width = 15)

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

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 4, pady = 1)
        self.elabel.grid(       row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.rholabel  .grid(   row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)

        self.namewidget.grid(   row    = 4, column = 1, padx = 2, pady = 1, sticky = 'WE')
        self.ewidget.grid  (    row    = 4, column = 2, padx = 2 ,pady = 1)
        self.rhowidget.grid (   row    = 4, column = 3, padx = 2 ,pady = 1)
        self.focwidget.grid(    row    = 4, column = 4, padx = 2 ,pady = 1)
        
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
            self.name.set(self.matrix.name)
            self.model.set(self.matrix.model)
            self.e.set(   self.matrix.e)
            self.rho.set( self.matrix.rho)
            self.foc.set( self.matrix.foc)
            self.components = self.matrix.components
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

class MixtureEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, matrix, matrices, materials, editflag):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype)                                       #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                                                               #flag for existence of toplevel#

        
        self.matrix    = matrix
        self.matrices  = matrices
        self.materials = materials
        
        self.mixing_models = ['Linear', 'None']
        
        self.name          = StringVar(value = 'Mixture')                                   #matrix name
        self.model         = StringVar(value = self.mixing_models[0])                       #model name
        self.e             = DoubleVar()                                                    #stores the porosity
        self.rho           = DoubleVar()                                                    #stores the bulk density
        self.foc           = DoubleVar()                                                    #stores the organic carbon fraction

        self.components    = []                                                             #components

        self.editflag   = editflag
        self.cancelflag = 0
        
        if editflag == 1:                       #Detemine whether the chemical is added or edited
            
            for component in self.matrix.components:
                self.components.append(component.copy())
                self.components[-1].name      = StringVar(value = self.components[-1].name)
                self.components[-1].mfraction = DoubleVar(value = self.components[-1].mfraction)

            self.name.set(    self.matrix.name)
            self.model.set(   self.matrix.model)
            self.e.set(       self.matrix.e)
            self.rho.set(     self.matrix.rho)
            self.foc.set(     self.matrix.foc)

    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = 'Please provides the following information about the mixture:                    ')

        self.blank1  = Label(self.frame,  text =' ', width = 15)


        self.blankcolumn  = Label(self.frame,  text ='   ', width = 1)
        self.delcolumn    = Label(self.frame,  text =' ', width = 6)
        self.compcolumn   = Label(self.frame,  text =' ', width = 18)
        self.fraccolumn   = Label(self.frame,  text =' ', width = 10)
        self.ecolumn      = Label(self.frame,  text =' ', width = 10)
        self.rhocolumn    = Label(self.frame,  text =' ', width = 15)
        self.foccolumn    = Label(self.frame,  text =' ', width = 20)

        self.namelabel    = Label(self.frame,  text = 'Name')
        self.elabel       = Label(self.frame,  text = 'Porosity')
        self.rholabel     = Label(self.frame,  text = 'Bulk density ('+ u'g/cm\u00B3'+')')
        self.foclabel     = Label(self.frame,  text = 'Organic carbon fraction')

        self.namewidget   = Entry(self.frame,  textvariable = self.name, justify = 'center', width = 16)
        self.ewidget      = Entry(self.frame,  textvariable = self.e ,   justify = 'center', width = 10)
        self.rhowidget    = Entry(self.frame,  textvariable = self.rho , justify = 'center', width = 10)
        self.focwidget    = Entry(self.frame,  textvariable = self.foc , justify = 'center', width = 10)

        self.complabel    = Label(self.frame,  text = 'Component')
        self.compflabel   = Label(self.frame,  text = 'Weight fraction')
        self.compelabel   = Label(self.frame,  text = 'Porosity')
        self.comprholabel = Label(self.frame,  text = 'Bulk density ('+u'g/cm\u00B3'+')')
        self.compfoclabel = Label(self.frame,  text = 'Organic carbon fraction')

        self.addwidget    = Button(self.frame, text = 'Add components', width = 20, command = self.add_components)
        self.loadwidget   = Button(self.frame, text = 'Load components', width = 20, command = self.load_components)
        self.esitimator   = Button(self.frame, text = 'Estimate Mixture Properties', width = 20, command = self.estimate_mixture)
        self.okbutton     = Button(self.frame, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label( self.frame, text = ' ')
        self.blank2       = Label( self.frame, text = ' ')
        self.blank3       = Label( self.frame, text = ' ')

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 7, padx = 8, sticky = 'W')
                
        self.blank1.grid(    row    = 1, column = 0, columnspan = 2)

        self.blankcolumn.grid(  row    = 3, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(    row    = 3, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.compcolumn.grid(   row    = 3, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.fraccolumn.grid(   row    = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.ecolumn.grid(      row    = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.rhocolumn.grid(    row    = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.foccolumn.grid(    row    = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 4, column = 2, sticky = 'WE', padx = 4, pady = 1)
        self.elabel.grid(       row    = 4, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.rholabel  .grid(   row    = 4, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel .grid(    row    = 4, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.namewidget.grid(   row    = 5, column = 2, padx = 4, pady = 1)
        self.ewidget.grid(      row    = 5, column = 4, padx = 1, pady = 1)
        self.rhowidget.grid(    row    = 5, column = 5, padx = 1, pady = 1)
        self.focwidget.grid(    row    = 5, column = 6, padx = 1, pady = 1)

        self.blank3.grid(       row    = 6, column = 0, columnspan = 2)

        self.complabel.grid(    row    = 7, column = 2, sticky = 'WE', padx = 4, pady = 1)
        self.compflabel.grid(   row    = 7, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.compelabel.grid(   row    = 7, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.comprholabel.grid( row    = 7, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.compfoclabel.grid( row    = 7, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.update_components()
        
    def update_components(self):

        try:
            self.addwidget.grid_forget()
            self.okbutton.grid_forget()
            self.cancelbutton.grid_forget()
        except: pass

        row = 8
        for component in self.components:
            try:
                component.get_component()                
                component.remove_propertieswidgets()
            except: pass
            component.number = self.components.index(component) + 1
            component.propertieswidgets(self.frame, row, self.master, self.materials, self.matrices)
            row = row + 1
                
        self.blank1.grid(       row    = row)
        row = row + 1
        self.addwidget.grid(    row    = row, columnspan = 11)
        row = row + 1
        self.loadwidget.grid(   row    = row, columnspan = 11)
        row = row + 1
        self.esitimator.grid(   row    = row, columnspan = 11)
        row = row + 1
        self.okbutton.grid(     row    = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid( row    = row, columnspan = 11)
        row = row + 1
        self.blank2.grid(       row    = row)
        
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton
        self.master.geometry()

    def add_components(self, event = None):

        total_fraction = 0
        for component in self.components:
            total_fraction = total_fraction + component.mfraction.get()

        self.components.append(MatrixComponent(len(self.components)+ 1))

        self.components[-1].name          = ' '
        if total_fraction > 1:        self.components[-1].mfraction     = 0
        else:                         self.components[-1].mfraction     = 1-total_fraction
        self.components[-1].fraction      = 0
        self.components[-1].e             = 0
        self.components[-1].rho           = 0
        self.components[-1].foc           = 0

        self.update_components()

    def load_components(self, event = None):


        total_fraction = 0
        for component in self.components:
            total_fraction = total_fraction + component.mfraction.get()

        self.components.append(MatrixComponent(len(self.components)+ 1))

        self.components[-1].name          = ' '
        if total_fraction > 1:        self.components[-1].mfraction     = 0
        else:                         self.components[-1].mfraction     = 1-total_fraction

        self.update_components()

    def del_component(self, number):

        self.components[number - 1].remove_propertieswidgets()
        self.components.remove(self.components[number - 1])

        self.update_components()

    def estimate_mixture(self):

        total_fraction = 0
        for component in self.components:
            total_fraction = total_fraction + component.mfraction.get()

        if    total_fraction <> 1.:                     self.fraction_error()
        else: self.calculate_matrix()

        self.frame.update()
        self.update_components()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""


        components_check = 0
        component_list = [component.name for component in self.components]

        for name in component_list:
            if component_list.count(name) > 1:
                components_check = 1

        if self.editflag == 0: check =[(matrix.name == self.name.get()) for matrix in self.matrices[0:-1]]
        else:                  check =[0]

        total_fraction = 0
        rho_flag       = 0
        for component in self.components:
            total_fraction = total_fraction + component.mfraction.get()
            if component.rho.get() <= 0:
                rho_flag = 1

        if self.master.window.top is not None:         self.master.open_toplevel()
        elif sum(check) >= 1 or self.name.get() == '': self.matrix_error()
        elif len(self.components) < 2:                 self.empty_component()
        elif total_fraction <> 1.:                     self.fraction_error()
        elif rho_flag == 1:                            self.rho_error()
        elif components_check == 1:                    self.replicate_error()
        else:
            self.calculate_matrix()
            self.master.tk.quit()
        
    def matrix_error(self):

        tkmb.showerror(title = self.version, message = 'This matrix has already been added to the matrix list!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def empty_component(self):

        tkmb.showerror(title = self.version, message = 'The mixture must consist at least two components')
        self.focusbutton = self.okbutton
        self.master.tk.lift()
        
    def fraction_error(self):

        tkmb.showinfo(self.version, 'The sum of the weight fraction is not 1, please check')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def rho_error(self):

        tkmb.showinfo(self.version, 'The bulk density of a component must be a positive value')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def replicate_error(self):

        tkmb.showinfo(self.version, 'At least one component is replicated in the mixture')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.name.set(self.matrix.name)
            self.model.set(self.matrix.model)
            self.e.set(   self.matrix.e)
            self.rho.set( self.matrix.rho)
            self.foc.set( self.matrix.foc)
            self.components = self.matrix.components
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def calculate_matrix(self):

        rho_flag  = 0

        e         = 0
        rho       = 0
        moc       = 0
        foc       = 0
        fractions = 0

        volume = 0

        for component in self.components:
            if component.rho.get() <= 0:
                rho_flag = 1

        if rho_flag == 1:
            self.rho_error()
        else:
            for component in self.components:

                component.get_component()
                component.remove_propertieswidgets()

                volume = volume + component.mfraction / component.rho


            for component in self.components:

                component.fraction = component.mfraction / component.rho / volume

                e         = e         + component.fraction * component.e
                rho       = rho       + component.fraction * component.rho
                moc       = moc       + component.fraction * component.rho * component.foc

            foc = moc/rho

            self.e.set(round(e,6))
            self.rho.set(round(rho,6))
            self.foc.set(round(foc,6))
