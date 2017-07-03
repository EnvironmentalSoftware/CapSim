#! /usr/bin/env python
#
#This file is used to make the GUI to get chemical properties of each layer.

import sys, os, cPickle as pickle

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar, FLAT, RAISED
from capsim_object_types import CapSimWindow, SolidIC
from capsim_functions    import get_superfont
import tkMessageBox as tkmb

class SolidLayerConditions:
    """Gets the chemical properties for each layer."""

    def __init__(self, master, system):
        """Constructor method.  Makes the GUI using the list of "Layer" objects
        "layers." """

        self.master         = master
        self.version        = system.version
        self.fonttype       = system.fonttype
        self.superfont      = get_superfont(self.fonttype)
        self.tframe         = Frame(master.tframe)
        self.frame          = Frame(master.frame)
        self.bframe         = Frame(master.bframe)
        self.lframe         = Frame(master.lframe)

        self.bgcolor        = self.frame.cget('bg')
        self.top            = None

        self.nchemicals     = system.nchemicals
        self.chemicals      = system.chemicals
        self.layers         = system.layers
        self.matrices       = system.matrices
        self.components     = system.components
        self.sorptions      = system.sorptions

        self.concunit       = system.concunit

        self.topline        = Label (self.frame, width = 10, text = '-' * 1000)

        if system.SolidICs == None:
            self.SolidICs = {}
            for layer in system.layers:
                self.SolidICs[layer.name] = {}
                for component in system.matrices[layer.type_index].components:
                    self.SolidICs[layer.name][component.name] = {}
                    for chemical in self.chemicals:
                        self.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)
        else:
            self.SolidICs        = system.SolidICs

    def make_widgets(self):
        """Makes the widgets for the GUI."""

        self.instructions   = Label(self.tframe,  text  = 'Please input the initial solid concentrations ('+self.concunit[:-1]+'kg):        ')
        self.blank1         = Label(self.tframe,  text  = '')
        self.blank2         = Label(self.tframe,  text  = '')

        self.blankcolumn    = Label(self.tframe, width = 2,  text = ' ' )
        self.layercolumn    = Label(self.tframe, width = 10, text = ' ' )
        self.compcolumn     = Label(self.tframe, width = 10, text = ' ' )
        self.chemcolumn     = Label(self.tframe, width = 25, text = ' ' )
        self.endcolumn      = Label(self.tframe, width = 4,  text = ' ' )

        self.layerlabel     = Label(self.tframe, width = 10, text = 'Layer' )
        self.complabel      = Label(self.tframe, width = 10, text = 'Material' )
        self.chemlabel      = Label(self.tframe, width = 10, text = 'Chemical', justify = 'center')

        self.botblankcolumn = Label(self.frame, width = 2,  text = ' ' )
        self.botlayercolumn = Label(self.frame, width = 10, text = ' ' )
        self.botcompcolumn  = Label(self.frame, width = 10, text = ' ' )
        self.botchemcolumn  = Label(self.frame, width = 25, text = ' ' )
        self.botendcolumn   = Label(self.frame, width = 4,  text = ' ' )

        self.blank1         = Label (self.frame, text = ' ')
        self.blank2         = Label (self.frame, text = ' ')
        self.blank3         = Label (self.frame, text = ' ')
        self.blank4         = Label (self.frame, text = ' ')

        #show the widgets on the grid

        self.instructions.grid( row = 0, column = 0, padx = 8, columnspan = 6, sticky = 'W')

        self.blankcolumn.grid(      row = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.layercolumn.grid(      row = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.compcolumn.grid(       row = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.chemcolumn.grid(       row = 1, column = 3, sticky = 'WE', padx = 1, pady = 1, columnspan = self.nchemicals)
        self.endcolumn.grid(        row = 1, column = 3+self.nchemicals, sticky = 'WE', padx = 1, pady = 1)

        self.layerlabel.grid(       row = 2, column = 1, padx = 4, sticky = 'WE')
        self.complabel.grid(        row = 2, column = 2, padx = 4, sticky = 'WE')
        self.chemlabel.grid(        row = 2, column = 3, padx = 4, sticky = 'WE', columnspan = self.nchemicals)

        self.botblankcolumn.grid(      row = 0, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.botlayercolumn.grid(      row = 0, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.botcompcolumn.grid(       row = 0, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.botchemcolumn.grid(       row = 0, column = 3, sticky = 'WE', padx = 1, pady = 1, columnspan = self.nchemicals)
        self.botendcolumn.grid(        row = 0, column = 3+self.nchemicals, sticky = 'WE', padx = 1, pady = 1)

        namelabellength      = 0
        layerlabellength     = 0
        componentlabellength = 0

        column = 3
        chemical_flag = []
        for chemical in self.chemicals:
            chemical.ICwidgets(self.frame, column)
            namelabellength = namelabellength + int(chemical.ICwidget.winfo_reqwidth()/8*1.1424219345) + 1
            column = column + 1
        self.endcolumn.grid(        row = 2, column = column, sticky = 'WE', padx = 1, pady = 1)

        if namelabellength > 25:
            self.chemcolumn.config(   width = namelabellength)
            self.chemcolumn.config(   width = namelabellength)


        row_layer   = 4
        for layer in self.layers:
            row = row_layer
            for component in self.matrices[layer.type_index].components:
                column = 3
                for chemical in self.chemicals:
                    if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                        self.SolidICs[layer.name][component.name][chemical.name].propertieswidgets(self.frame, row, column)
                    else:
                        self.SolidICs[layer.name][component.name][chemical.name].blankwidgets(self.frame, row, column)
                    column = column + 1
                component.SolidICswidgets(self.frame, row)
                if (int(component.SolidICswidget.winfo_reqwidth()/8*1.1424219345) + 1) > componentlabellength: componentlabellength = int(component.SolidICswidget.winfo_reqwidth()/8*1.1424219345) + 1
                row = row + 1
            layer.SolidICwidgets(self.frame, row_layer, row, self.nchemicals + 2)
            if (int(layer.solidlayerlabel.winfo_reqwidth()/8*1.1424219345) + 1) > layerlabellength: layerlabellength = int(layer.solidlayerlabel.winfo_reqwidth()/8*1.1424219345) + 1

            row = row + 2
            row_layer = row

        if layerlabellength > 10:
            self.layercolumn.config(   width = layerlabellength)
            self.botlayercolumn.config(width = layerlabellength)
        if componentlabellength > 10:
            self.compcolumn.config(   width = componentlabellength)
            self.botcompcolumn.config(width = componentlabellength)

        self.topline.grid(        row = 3,    column = 1,     columnspan = self.nchemicals + 2,  sticky = 'WE', pady = 1)


        self.blank1.grid(  row = row)
        row = row + 1
        self.blank2.grid(  row = row)
        self.focusbutton = None

def get_solidlayerconditions(system, step):

    root_step = 0

    solid_check = 0
    for chemical in system.chemicals:
        for component in system.components:
            if system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                solid_check = 1

    if solid_check == 1:
        root = CapSimWindow(buttons = 1)
        root.make_window(SolidLayerConditions(root, system))
        root.okbutton.focus_set()
        root.mainloop()

        if root.main.get() == 1: system = None
        else:
            root_step = root.step.get()
            if root.step.get() == 1:
                system.get_solidlayerconditions(root.window)
                for layer in system.layers:
                    layer.remove_SolidICwidgets()
                    for component in system.matrices[layer.type_index].components:
                        component.remove_SolidICswidgets()
                        for chemical in system.chemicals:
                            system.SolidICs[layer.name][component.name][chemical.name].remove_widgets()


                for chemical in system.chemicals:
                    try:    chemical.remove_ICwidgets()
                    except: pass
            else:
                system.SolidICs = None

        root.destroy()

    else:
        if system.SolidICs == None:
            root_step = 1
            system.SolidICs = {}
            for layer in system.layers:
                system.SolidICs[layer.name] = {}
                for component in system.matrices[layer.type_index].components:
                    system.SolidICs[layer.name][component.name] = {}
                    for chemical in system.chemicals:
                        system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)

        else:
            system.SolidICs = None
            root_step = -1

    return system, step + root_step
