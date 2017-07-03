#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical
from capsim_functions    import get_superfont
from database            import Database

class LayerEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, layer, layers, editflag):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master     = master
        self.fonttype   = system.fonttype
        self.version    = system.version
        self.superfont  = get_superfont(self.fonttype) #superscript font
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.top        = None                   #flag for existence of toplevel#

        self.system     = system
        self.lengthunit = system.lengthunit

        self.layer      = layer
        self.layers     = layers
        self.types      = []
        self.tort_types = []

        self.torts      = layer.torts
        self.h          = DoubleVar(value = 10.0)
        self.alpha      = DoubleVar(value = 1.0)
        self.doc        = DoubleVar(value = 0.0)

        for matrix in system.matrices:
            self.types.append(matrix.name)
            self.tort_types.append(matrix.components[0].tort)

        self.type       = StringVar(value = self.types[0])
        self.tort       = StringVar(value = self.tort_types[0])

        self.editflag   = editflag
        self.cancelflag = 0

        if self.editflag == 1:
            self.type.set(layer.type)
            self.tort.set(layer.tort)
            self.h.set(layer.h)
            self.alpha.set(layer.alpha)
            self.doc.set(layer.doc)
            
        self.names    = []
        if len(layers) == 0:
            self.names.append('Deposition')
            self.names.append('Layer 1')
        else:
            for layer in self.layers: self.names.append(layer.name)
            self.names.append('Layer ' + str(layers[-1].number + 1))
            if self.names[0] == 'Deposition': self.names.remove(self.names[0])
            else:                             self.names.insert(0, 'Deposition')

        if self.editflag == 0:     self.name     = StringVar(value = self.names[-1])
        else:                      self.name     = StringVar(value =  self.layer.name)

        
    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor       = self.frame.cget('bg')
        self.instructions  = Label(self.frame, text = ' Please input the following information about the layer properties:                    ')
                
        self.namelabel     = Label(self.frame,  text = 'Layer')
        self.typelabel     = Label(self.frame,  text = 'Material')
        self.tortlabel     = Label(self.frame,  text = 'Tortuosity Correction')
        self.hlabel        = Label(self.frame,  text = 'Thickness')
        self.alphalabel    = Label(self.frame,  text = 'Hydrodynamic\n' +'Dispersivity')
        self.doclabel      = Label(self.frame,  text = 'Dissolved organic\n'+'matter concentration  ')

        if self.editflag == 0: self.namewidget = OptionMenu(self.frame, self.name, *self.names, command = self.click_type)
        else:                  self.namewidget = Label(self.frame, textvariable = self.name, justify = 'center' )
        self.typewidget    = OptionMenu(self.frame, self.type,   *self.types,   command = self.click_tortuosity)
        self.hwidget       = Entry(self.frame, textvariable = self.h,     width = 8, justify = 'center')
        self.alphawidget   = Entry(self.frame, textvariable = self.alpha, width = 8, justify = 'center')          
        self.docwidget     = Entry(self.frame, textvariable = self.doc,   width = 8, justify = 'center')          
        
        self.thickunits    = Label(self.frame, text = self.lengthunit)
        self.depthickunits = Label(self.frame, text = self.lengthunit + '/yr')
        self.alphaunits    = Label(self.frame, text = self.lengthunit)
        self.docunits      = Label(self.frame, text = 'mg/L')

        self.blankcolumn   = Label(self.frame, text = ' ', width = 2)
        self.namecolumn    = Label(self.frame, text = ' ', width = 14)
        self.typecolumn    = Label(self.frame, text = ' ', width = 18)
        self.tortcolumn    = Label(self.frame, text = ' ', width = 20)
        self.thickcolumn   = Label(self.frame, text = ' ', width = 12)
        self.alphacolumn   = Label(self.frame, text = ' ', width = 12)
        self.doccolumn     = Label(self.frame, text = ' ', width = 12)

        self.okbutton      = Button(self.frame, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton  = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1        = Label(self.frame, text = ' ')
        self.blank2        = Label(self.frame, text = ' ')

        #show the widgets on the grid

        self.instructions.grid( row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')
        
        self.blankcolumn.grid(  row = 1,  column = 0)
        self.namecolumn.grid(   row = 1,  column = 1)
        self.typecolumn.grid(   row = 1,  column = 2)
        self.tortcolumn.grid(   row = 1,  column = 3)
        self.thickcolumn.grid(  row = 1,  column = 4)
        self.alphacolumn.grid(  row = 1,  column = 5)
        self.doccolumn.grid(    row = 1,  column = 6)

        self.namelabel.grid(    row = 2, column = 1, sticky = 'WE', padx = 4, pady = 1)
        self.typelabel.grid(    row = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.tortlabel.grid(    row = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.hlabel.grid(       row = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.alphalabel.grid(   row = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.doclabel.grid(     row = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        
        self.namewidget.grid(   row = 4, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.hwidget.grid(      row = 4, column = 4, padx = 1, pady = 1)
        self.alphawidget.grid(  row = 4, column = 5, padx = 1, pady = 1)
        self.docwidget.grid(    row = 4, column = 6, padx = 1, pady = 1)
        
        self.thickunits.grid(   row = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.alphaunits.grid(   row = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.docunits.grid(     row = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)
        
        self.blank1.grid(       row    = 5)
        self.okbutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank2.grid(       row    = 8)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        #if self.editflag == 0: self.click_type()
        self.click_type()

    def click_type(self, event = None):

        try:
            self.thickunits.grid_forget()
            self.depthickunits.grid_forget()
        except:pass

        if self.name.get() == 'Deposition': self.depthickunits.grid(   row = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        else:                               self.thickunits.grid(   row = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)


        self.typewidget.grid(   row = 4, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.click_tortuosity(event = 1)
            
    def click_tortuosity(self, event = None):
        """Give the default tortuosity model corresponding to the selected layer type."""

        #try:
        if event != 1: self.tort.set(self.tort_types[self.types.index(self.type.get())])

        self.tortwidget = OptionMenu(self.frame, self.tort, *self.torts)
        self.tortwidget.grid_forget()
        self.tortwidget.grid(row = 4, column = 3, padx =2, pady = 1, sticky = 'WE')
            
        
    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
  
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def chemicals_error(self):

        tkmb.showerror(title = self.version, message = 'This chemical has already been selected!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.number.set(self.layer.number)
            self.type.set(self.layer.type)
            self.tort.set(self.layer.tort)
            self.h.set(self.layer.h)
            self.alpha.set(self.layer.alpha)
            self.doc.set(self.layer.doc)
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
class LayerDeleter:
    
    def __init__(self, master, system, layer):
        
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
                
        self.type       = layer.type
        self.tort       = layer.tort
        self.h          = layer.h
        self.alpha      = layer.alpha
        self.doc        = layer.doc

        self.layer      = layer
        self.cancelflag = 0

    def make_widgets(self):
    
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Are you sure to delete the following layer?                   ')
                
        self.namelabel     = Label(self.frame,  text = 'Layer')
        self.typelabel     = Label(self.frame,  text = 'Material')
        self.tortlabel     = Label(self.frame,  text = 'Tortuosity Correction')
        self.hlabel        = Label(self.frame,  text = 'Thickness')
        self.alphalabel    = Label(self.frame,  text = 'Hydrodynamic\n' +'Dispersivity')
        self.doclabel      = Label(self.frame,  text = 'Dissolved organic\n'+'matter concentration   ')

        if self.layer.number == 0: self.namewidget    = Label(self.frame, text = 'Deposition')
        else:                      self.namewidget    = Label(self.frame, text = 'Layer '+ str(self.layer.number))

        self.typewidget    = Label(self.frame, text = self.type)
        self.tortwidget    = Label(self.frame, text = self.tort)
        self.hwidget       = Label(self.frame, text = self.h,     width = 10)          
        self.alphawidget   = Label(self.frame, text = self.alpha, width = 10)          
        self.docwidget     = Label(self.frame, text = self.doc,   width = 10)
        
        self.thickunits    = Label(self.frame, text = 'cm')
        self.depthickunits = Label(self.frame, text = 'cm/yr')
        self.alphaunits    = Label(self.frame, text = 'cm')
        self.docunits      = Label(self.frame, text = 'mg/L')

        self.blankcolumn   = Label(self.frame, text = ' ', width = 2)
        self.namecolumn    = Label(self.frame, text = ' ', width = 14)
        self.typecolumn    = Label(self.frame, text = ' ', width = 18)
        self.tortcolumn    = Label(self.frame, text = ' ', width = 20)
        self.thickcolumn   = Label(self.frame, text = ' ', width = 12)
        self.alphacolumn   = Label(self.frame, text = ' ', width = 12)
        self.doccolumn     = Label(self.frame, text = ' ', width = 12)

        self.deletebutton = Button(self.frame, text = 'Delete', width = 20, command = self.Delete)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')

        self.blankcolumn.grid(  row = 1,  column = 0)
        self.namecolumn.grid(   row = 1,  column = 1)
        self.typecolumn.grid(   row = 1,  column = 2)
        self.tortcolumn.grid(   row = 1,  column = 3)
        self.thickcolumn.grid(  row = 1,  column = 4)
        self.alphacolumn.grid(  row = 1,  column = 5)
        self.doccolumn.grid(    row = 1,  column = 6)

        self.namelabel.grid(    row = 2, column = 1, sticky = 'WE', padx = 4, pady = 1)
        self.typelabel.grid(    row = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)        
        self.tortlabel.grid(    row = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.hlabel.grid(       row = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.alphalabel.grid(   row = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.doclabel.grid(     row = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        
        if self.layer.number == 0: self.depthickunits.grid( row = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        else:                      self.thickunits.grid(    row = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.alphaunits.grid(   row = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.docunits.grid(     row = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)
        
        self.namewidget.grid(   row = 4, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.typewidget.grid(   row = 4, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.tortwidget.grid(   row = 4, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.hwidget.grid(      row = 4, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.alphawidget.grid(  row = 4, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.docwidget.grid(    row = 4, column = 6, sticky = 'WE', padx = 1, pady = 1)
                
        self.blank1.grid(       row    = 5)
        self.deletebutton.grid( row    = 6, columnspan = 11)
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
            self.number.set(self.layer.number)
            self.type.set(self.layer.type)
            self.tort.set(self.layer.tort)
            self.h.set(self.layer.h)
            self.alpha.set(self.layer.alpha)
            self.doc.set(self.layer.doc)
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
