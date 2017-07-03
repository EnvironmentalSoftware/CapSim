#! /usr/bin/env python
#
#This file is used to make the GUI for the general layer properties of the cap. 

from Tkinter             import Frame, Label, Button, IntVar, StringVar, \
                                DoubleVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow, Layer
from layereditor         import LayerEditor, LayerDeleter

import tkMessageBox as tkmb

class LayerProperties:
    """Input the parameters for each of the layers in the system."""

    def __init__(self, master, system, editflag = None):
        """Constructor method. Used to defines the layers."""
        
        self.fonttype     = system.fonttype
        self.version      = system.version
        self.master       = master
        self.frame        = Frame(master.frame)
        self.tframe       = Frame(master.tframe)
        self.bframe       = Frame(master.bframe)
        self.superfont    = get_superfont(self.fonttype)
        self.top          = None

        self.system       = system
        self.lengthunit   = system.lengthunit

        if system.layers is None:
            self.layers  = []
            self.nlayers = 0
        else:
            self.layers  = system.layers
            self.nlayers = system.nlayers

        self.editflag = editflag

        print(editflag)
        if editflag == 1:
            self.num_record         = [j for j in range(self.nlayers)]

    def make_widgets(self):
        """Make the widgets for the window."""
  
        self.instructions = Label(self.tframe,  text = 'Starting with the layer nearest the overlying water, please ' +
                                  'provide the following information for each layer:' + ' '*20, justify = 'left')

        self.blankcolumn    = Label(self.tframe, text = '', font = 'courier 10', width = 1)
        self.editcolumn     = Label(self.tframe, text = '', font = 'courier 10', width = 6)
        self.delcolumn      = Label(self.tframe, text = '', font = 'courier 10', width = 6)
        self.namecolumn     = Label(self.tframe, text = '', font = 'courier 10', width = 12)
        self.typecolumn     = Label(self.tframe, text = '', font = 'courier 10', width = 15)
        self.tortcolumn     = Label(self.tframe, text = '', font = 'courier 10', width = 20)
        self.thickcolumn    = Label(self.tframe, text = '', font = 'courier 10', width = 10)
        self.alphacolumn    = Label(self.tframe, text = '', font = 'courier 10', width = 15)
        self.doccolumn      = Label(self.tframe, text = '', font = 'courier 10', width = 20)
        self.endcolumn      = Label(self.tframe, text = '', font = 'courier 10', width = 2)
        #Title Widgets

        self.material    = Label(self.tframe, text = 'Material')
        self.tortuosity  = Label(self.tframe, text = 'Tortuosity Correction ')
        self.thickness   = Label(self.tframe, text = 'Thickness')
        self.alpha       = Label(self.tframe, text = 'Hydrodynamic\n'+'Dispersivity')
        self.doclabel    = Label(self.tframe, text = 'Dissolved organic\n'+'matter concentration   ')
        
        #Unit Widgets
        
        self.thickunits  = Label(self.tframe, text = self.lengthunit)
        self.alphaunits  = Label(self.tframe, text = self.lengthunit)
        self.docunits    = Label(self.tframe, text = 'mg/L')
        
        self.botblankcolumn    = Label(self.frame, text = '', font = 'courier 10', width = 1)
        self.boteditcolumn     = Label(self.frame, text = '', font = 'courier 10', width = 6)
        self.botdelcolumn      = Label(self.frame, text = '', font = 'courier 10', width = 6)
        self.botnamecolumn     = Label(self.frame, text = '', font = 'courier 10', width = 12)
        self.bottypecolumn     = Label(self.frame, text = '', font = 'courier 10', width = 15)
        self.bottortcolumn     = Label(self.frame, text = '', font = 'courier 10', width = 20)
        self.botthickcolumn    = Label(self.frame, text = '', font = 'courier 10', width = 10)
        self.botalphacolumn    = Label(self.frame, text = '', font = 'courier 10', width = 15)
        self.botdoccolumn      = Label(self.frame, text = '', font = 'courier 10', width = 20)
        self.botendcolumn      = Label(self.frame, text = '', font = 'courier 10', width = 2)
        #a special OK button is needed to check bioturbation depth
        
        self.blank1 = Label(self.bframe, text = ' ')
        self.blank2 = Label(self.bframe, text = ' ')

        self.addwidget  = Button(self.bframe, text = 'Add layers', command = self.addlayer, width = 20)

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, padx = 6, sticky = 'W', columnspan = 10)
        
        self.blankcolumn.grid(  row = 1,  column = 0)
        self.editcolumn.grid(   row = 1,  column = 1)
        self.delcolumn.grid(    row = 1,  column = 2)
        self.namecolumn.grid(   row = 1,  column = 3)
        self.typecolumn.grid(   row = 1,  column = 5)
        self.tortcolumn.grid(   row = 1,  column = 4)
        self.thickcolumn.grid(  row = 1,  column = 6)
        self.alphacolumn.grid(  row = 1,  column = 7)
        self.doccolumn.grid(    row = 1,  column = 8)
        self.endcolumn .grid(   row = 1,  column = 9)

        self.material.grid(     row = 2,  column = 4, padx = 0, sticky = 'N')
        self.tortuosity.grid(   row = 2,  column = 5, padx = 0, sticky = 'N')
        self.thickness.grid(    row = 2,  column = 6, padx = 0, sticky = 'N')
        self.alpha.grid(        row = 2,  column = 7, padx = 0, sticky = 'N')
        self.doclabel.grid(     row = 2,  column = 8, padx = 0, sticky = 'N')

        self.thickunits.grid(   row = 3,  column = 6, padx = 0)
        self.alphaunits.grid(   row = 3,  column = 7, padx = 0)
        self.docunits.grid(     row = 3,  column = 8, padx = 0)

        #make entry widgets for each of the layers
        self.updatelayers()
       
    def updatelayers(self):

        self.addwidget.grid_forget()
        self.blank1.grid_forget()
        self.blank2.grid_forget()

        namelabellength = 20

        for layer in self.layers:
            try: layer.remove_propertywidgets()
            except: pass
            if self.layers[0].number == 0:  layer.number = self.layers.index(layer)
            else:                           layer.number = self.layers.index(layer) + 1
            if layer.number == 0:           layer.name   = 'Deposition'
            else:                           layer.name   = 'Layer ' + str(layer.number)

        row = 4
        for layer in self.layers:
            layer.propertywidgets(self.frame, row, self.master)
            row = row + 1
            if namelabellength < layer.typelabel.winfo_reqwidth()/8:  namelabellength = int(layer.typelabel.winfo_reqwidth()/8) + 1

        self.typecolumn.config(width = namelabellength)
        self.bottypecolumn.config(width = namelabellength)

        self.botblankcolumn.grid(  row = row,  column = 0)
        self.boteditcolumn.grid(   row = row,  column = 1)
        self.botdelcolumn.grid(    row = row,  column = 2)
        self.botnamecolumn.grid(   row = row,  column = 3)
        self.bottypecolumn.grid(   row = row,  column = 5)
        self.bottortcolumn.grid(   row = row,  column = 4)
        self.botthickcolumn.grid(  row = row,  column = 6)
        self.botalphacolumn.grid(  row = row,  column = 7)
        self.botdoccolumn.grid(    row = row,  column = 8)
        self.botendcolumn .grid(   row = row,  column = 9)

        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1

        self.addwidget.bind('<Return>', self.addlayer)

        if self.nlayers == 0:   self.focusbutton = self.addwidget#self.okbutton
        else:                   self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def addlayer(self, default = None):

        self.nlayers = self.nlayers + 1
        layertemp = Layer(1)

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(LayerEditor(self.top, self.system, layertemp, self.layers, editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                layertemp.get_layer(self.top.window)
                if self.layers == []:            self.layers.append(layertemp)
                elif self.layers[0].number == 0: self.layers.insert( layertemp.number,    layertemp)
                elif layertemp.number == 0:      self.layers.insert( 0,                   layertemp)
                else:                            self.layers.insert( layertemp.number-1,  layertemp)

                if self.editflag == 1:
                    if self.layers[0].number == 0:
                        self.num_record.insert( layertemp.number,    -1)
                    elif layertemp.number == 0:
                        self.num_record.insert( 0,                   -1)
                    else:
                        self.num_record.insert( layertemp.number-1,  -1)

            else:
                self.nlayers = self.nlayers - 1
                layertemp = 0

            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()


        self.updatelayers()

    def editlayer(self, number):
        
        if self.layers[0].number == 0: layertemp = self.layers[number]
        else:                          layertemp = self.layers[number-1]

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(LayerEditor(self.top, self.system, layertemp, self.layers, editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                layertemp.get_layer(self.top.window)
               
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatelayers()
        
    def deletelayer(self, number):

        if self.layers[0].number == 0: layer = self.layers[number]
        else:                          layer = self.layers[number - 1]
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(LayerDeleter(self.top, self.system, layer))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                layer.remove_propertywidgets()
                if self.editflag == 1:
                    new_record      = self.num_record[:self.layers.index(layer)] + self.num_record[self.layers.index(layer)+1:]
                    self.num_record = new_record
                self.layers.remove(layer)
                self.nlayers = self.nlayers - 1

            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatelayers()

    def error_check(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error = 0
        if self.nlayers == 0: error = 1
        elif self.nlayers == 1 and self.layers[0].number ==0: error = 1

        return error

    def warning(self):

        tkmb.showerror(title = self.version, message = 'No layer has been created, please add layers by pressing the button "Add layers"')
        self.focusbutton = None
        self.master.tk.lift()

def get_layerproperties(system, step):
    """Get some basic parameters for each layer."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(LayerProperties(root, system))
    root.mainloop()

    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_layerproperties(root.window)
            for layer in system.layers: layer.remove_propertywidgets()
        else:
            system.layers = None
            system.nlayers  = 0
            system.dep  = 0
            system.Vdep = 0

    root.destroy()

    return system, step + root.step.get()
