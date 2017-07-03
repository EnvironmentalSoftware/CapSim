#!/usr/bin/env python
#
#This file is used to make the GUI for the general sorption model of the cap. 

from Tkinter             import Frame, Label, IntVar, StringVar, DoubleVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow, Sorption
from sorptioneditor      import SorptionEditor
import tkMessageBox as tkmb

class SorptionProperties:
    """Gets the model types for each of the layers in the system."""

    def __init__(self, master, system):
        """Constructor method. Used to defines the layers."""
        
        self.fonttype     = system.fonttype
        self.version      = system.version
        self.master       = master
        self.frame        = Frame(master.frame)
        self.tframe       = Frame(master.tframe)
        self.bframe       = Frame(master.bframe)
        self.sfont        = get_superfont(self.fonttype)
        self.top          = None

        self.system       = system
        self.chemicals    = system.chemicals
        self.matrices     = system.matrices
        self.timeunit     = system.timeunit
        self.concunit     = system.concunit

        self.defaults     = 0
        if master.master is None: self.defaults = 1
        
        self.components     = system.components
        self.component_list = system.component_list
        
        if system.sorptions is None:
            self.sorptions = {}
            for component in self.components:
                self.sorptions[component.name] = {}
                for chemical in self.chemicals:
                    self.sorptions[component.name][chemical.name] = Sorption(component, chemical, unit = system.concunit)
        else: self.sorptions = system.sorptions

    def make_widgets(self):
        """Make the widgets for the window."""

        #Title Widgets
        self.leftcolumn        = Label(self.frame, width = 2,  text = ' ' )
        self.matrixcolumn      = Label(self.frame, width = 10, text = ' ' )
        self.chemicalcolumn    = Label(self.frame, width = 18, text = ' ' )
        self.editcolumn        = Label(self.frame, width = 1,  text = ' ' )
        self.isothermcolumn    = Label(self.frame, width = 20, text = ' ' )
        self.rightcolumn       = Label(self.frame, width = 2,  text = ' ' )

        self.coef1labelcolumn  = Label(self.frame, width = 7,  text = ' ')
        self.coef1valuecolumn  = Label(self.frame, width = 3,  text = ' ')
        self.coef1unitcolumn   = Label(self.frame, width = 10, text = ' ')

        self.coef2labelcolumn  = Label(self.frame, width = 7,  text = ' ')
        self.coef2valuecolumn  = Label(self.frame, width = 3,  text = ' ')
        self.coef2unitcolumn   = Label(self.frame, width = 10, text = ' ')

        self.coef3labelcolumn  = Label(self.frame, width = 7,  text = ' ')
        self.coef3valuecolumn  = Label(self.frame, width = 3,  text = ' ')
        self.coef3unitcolumn   = Label(self.frame, width = 10, text = ' ')

        self.instructions   = Label(self.frame, text = 'Please input the sorption isotherms and corresponding coefficients for chemicals in each layer:', justify = 'left')
        self.matrixlabel    = Label(self.frame, text = 'Matrix')
        self.chemicallabel  = Label(self.frame, text = 'Chemical')
        self.isothermlabel  = Label(self.frame, text = 'Sorption Isotherm')
        self.coeflabel      = Label(self.frame, text = 'Isotherm coefficients')
        self.kineticlabel   = Label(self.frame, text = 'Kinetic options')

        self.blank1         = Label(self.frame, text = ' ')

        #show the title widgets on the grid

        self.instructions.grid(         row = 0, column = 0, columnspan = 14, padx = 2, pady = 8, sticky = 'W')
        
        self.leftcolumn.grid   (        row = 1, column = 0,  padx = 1, pady = 1, sticky = 'WE')
        self.matrixcolumn.grid   (      row = 1, column = 1,  padx = 1, pady = 1, sticky = 'WE')
        self.chemicalcolumn.grid (      row = 1, column = 2,  padx = 1, pady = 1, sticky = 'WE')
        self.editcolumn.grid (          row = 1, column = 3,  padx = 1, pady = 1, sticky = 'WE')
        self.isothermcolumn.grid (      row = 1, column = 4,  padx = 1, pady = 1, sticky = 'WE')
        self.coef1labelcolumn.grid (    row = 1, column = 5,  padx = 1, pady = 1, sticky = 'WE')
        self.coef1valuecolumn.grid (    row = 1, column = 6,  padx = 1, pady = 1, sticky = 'WE')
        self.coef1unitcolumn.grid (     row = 1, column = 7,  padx = 1, pady = 1, sticky = 'WE')
        self.coef2labelcolumn.grid (    row = 1, column = 8,  padx = 1, pady = 1, sticky = 'WE')
        self.coef2valuecolumn.grid (    row = 1, column = 9,  padx = 1, pady = 1, sticky = 'WE')
        self.coef2unitcolumn.grid (     row = 1, column = 10, padx = 1, pady = 1, sticky = 'WE')
        self.coef3labelcolumn.grid (    row = 1, column = 11, padx = 1, pady = 1, sticky = 'WE')
        self.coef3valuecolumn.grid (    row = 1, column = 12, padx = 1, pady = 1, sticky = 'WE')
        self.coef3unitcolumn.grid (     row = 1, column = 13, padx = 1, pady = 1, sticky = 'WE')
        self.rightcolumn.grid   (       row = 1, column = 14, padx = 1, pady = 1, sticky = 'WE')


        self.matrixlabel.grid   (       row = 2, column = 1,  padx = 1, pady = 1, sticky = 'WE')
        self.chemicallabel.grid (       row = 2, column = 2,  padx = 1, pady = 1, sticky = 'WE')
        self.isothermlabel.grid (       row = 2, column = 4,  padx = 1, pady = 1, sticky = 'WE')
        self.coeflabel.grid (           row = 2, column = 5,  padx = 1, pady = 1, sticky = 'WE', columnspan = 6)
        self.kineticlabel.grid (        row = 2, column = 11, padx = 1, pady = 1, sticky = 'WE', columnspan = 3)

        #show the layer and chemical widgets on the grid        

        row = 3
                    
        for component in self.components:
            component.sorptionwidgets(self.frame, row = row)
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    chemical.sorptionwidgets(self.frame, row = row)
                    self.sorptions[component.name][chemical.name].propertieswidgets(self.frame, row, self.master, self.timeunit, self.concunit)
                    row = row + 1
                        
        self.focusbutton = None
        self.blank1.grid(row = row)

    def editsorption(self, component, chemical):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(SorptionEditor(self.top, self.system, self.sorptions[component][chemical]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.sorptions[component][chemical].get_sorption(self.top.window)
                row = self.sorptions[component][chemical].row
                self.sorptions[component][chemical].remove_propertieswidgets()
                self.sorptions[component][chemical].propertieswidgets(self.frame, row, self.master, self.timeunit, self.concunit)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus(component, chemical)

    def error_check(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error = 0

        return error

    def warning(self):

        self.focusbutton = None
        self.master.tk.lift()

def get_sorptionproperties(system, step):
    """Get some basic parameters for each layer."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(SorptionProperties(root, system))
    root.mainloop()

    if root.main.get() == 1:    system = None
    else:
        if root.step.get() == 1:
            system.get_sorptionproperties(root.window)
            for component in system.components:
                component.remove_sorptionwidgets()
            for chemical in system.chemicals:
                if chemical.soluable == 1:
                    chemical.remove_sorptionwidgets()
            for component in system.components:
                for chemical in system.chemicals:
                    if chemical.soluable == 1:
                        system.sorptions[component.name][chemical.name].remove_propertieswidgets()
        else:
            system.sorptions = None

    root.destroy()

    return system, step + root.step.get()
