#!/usr/bin/env python
#
#This file is used to make the GUI for the general layer properties of the cap. 

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow, Coefficient
from coefficienteditor   import CoefficientEditor

import tkFont

import tkMessageBox as tkmb

class ReactionCoefficients:
    """Gets the model types for each of the layers in the system."""

    def __init__(self, master, system, editflag):
        """Constructor method. Used to defines the layers."""
        
        self.master         = master
        self.version        = system.version
        self.fonttype       = system.fonttype
        self.formulatype    = system.formulatype
        self.superfont      = get_superfont(self.fonttype)
        self.subfont        = get_superfont(self.formulatype)
        self.tframe         = Frame(master.tframe)
        self.frame          = Frame(master.frame)
        self.bframe         = Frame(master.bframe)
        self.bgcolor        = self.frame.cget('bg')
        self.top            = None

        self.system         = system
        self.concunit       = system.concunit
        self.timeunit       = system.timeunit

        self.concunits      = system.concunits

        # Convert mass concentration units to corresponding molar concentration units
        if self.concunit == system.concunits[0]:    self.concunit = system.concunits[3]
        if self.concunit == system.concunits[1]:    self.concunit = system.concunits[4]
        if self.concunit == system.concunits[2]:    self.concunit = system.concunits[5]

        self.reactions      = system.reactions
        self.layers         = system.layers
        self.coefficients   = system.coefficients
            
        if system.coefficients == None:
            self.coefficients = {}
            for layer in self.layers:
                layerindex  = self.layers.index(layer)
                self.coefficients[layer.name] = {}
                for reaction in self.reactions:
                    self.coefficients[layer.name][reaction.name] = Coefficient(layer, reaction)

        self.name_max    = 0
        self.formula_max = 0
        self.rate_max    = 0
        self.value_max   = 0
        unitindex       = 0

        tkfont      = tkFont.Font(font = self.formulatype)
        tksubfont   = tkFont.Font(font = self.superfont)
        tksuperfont = tkFont.Font(font = self.subfont)

        for reaction in self.reactions:
            if tkfont.measure(reaction.name) > self.name_max: self.name_max = tkfont.measure(reaction.name)
            if tkfont.measure(reaction.equation) > self.formula_max: self.formula_max = tkfont.measure(reaction.equation)

            rate_len  = tkfont.measure(u'r = \u03BB')
            rate_len  = rate_len + tksubfont.measure(str(reaction.number)+ ',')
            rate_len  = rate_len + tksubfont.measure(str(10))
            for reactant in reaction.reactants:
                if reactant.index <> 0:
                    rate_len = rate_len + tkfont.measure('C')
                    rate_len = rate_len + tksubfont.measure(reactant.formula)
                    if reactant.index == int(reactant.index): index = int(reactant.index)
                    else:                                     index = reactant.index

                    if index <> 1.: rate_len = rate_len + tksuperfont.measure(str(index) + ' ')
                    unitindex = unitindex + reactant.index

            lam_len   = tkfont.measure(u'\u03BB')
            lam_len   = lam_len + tksubfont.measure(str(reaction.number)+ ',')
            lam_len  = lam_len + tksubfont.measure(str(10))
            lam_len  = lam_len + tkfont.measure(' = '+str(1000) + ' ')

            if unitindex == int(unitindex): unitindex = int(unitindex)
            if (unitindex - 1) != 0:
                if (unitindex - 1) != 1:
                    lam_len  = lam_len + tkfont.measure('('+self.concunit+')')
                    lam_len  = lam_len + tksuperfont.measure(str(-(unitindex - 1)))
                else:
                    lam_len  = lam_len + tkfont.measure(self.concunit)
            lam_len  = lam_len + tkfont.measure(self.timeunit)
            lam_len  = lam_len + tksuperfont.measure('-1')

            if self.rate_max < rate_len: self.rate_max = rate_len
            if self.value_max < lam_len: self.value_max = lam_len


    def make_widgets(self):
        """Makes the widgets for the GUI."""

        self.instructions   = Label(self.tframe,  text  = 'Please input the reaction information in each layer:        ')

        self.blankcolumn    = Label(self.tframe,  text = '',  font = 'courier 10', width = 1 )
        self.editcolumn     = Label(self.tframe,  text = '',  font = 'courier 10', width = 6 )
        self.delcolumn      = Label(self.tframe,  text = '',  font = 'courier 10', width = 6 )
        self.layercolumn    = Label(self.tframe,  text = '',  font = 'courier 10', width = 10 )
        self.namecolumn     = Label(self.tframe,  text = '',  font = 'courier 10', width = max(int(self.name_max/8)+1,    15))
        self.equationcolumn = Label(self.tframe,  text = '',  font = 'courier 10', width = max(int(self.formula_max/8)+1, 20))
        self.ratecolumn     = Label(self.tframe,  text = '',  font = 'courier 10', width = max(int(self.rate_max/8)+1,    10))
        self.coefcolumn     = Label(self.tframe,  text = '',  font = 'courier 10', width = max(int(self.value_max/8)+1,   10))
        self.endcolumn      = Label(self.tframe,  text = '',  font = 'courier 10', width = 1 )

        self.layerlabel     = Label(self.tframe,  text = 'Layer')
        self.namelabel      = Label(self.tframe,  text = 'Reaction')
        self.equationlabel  = Label(self.tframe,  text = 'Chemical equation')
        self.ratelabel      = Label(self.tframe,  text = 'Rate equation')
        self.coeflabel      = Label(self.tframe,  text = 'Coefficient')
        
        self.botblankcolumn    = Label(self.frame,  text = '',  font = 'courier 10', width = 1 )
        self.boteditcolumn     = Label(self.frame,  text = '',  font = 'courier 10', width = 6 )
        self.botdelcolumn      = Label(self.frame,  text = '',  font = 'courier 10', width = 6 )
        self.botlayercolumn    = Label(self.frame,  text = '',  font = 'courier 10', width = 10 )
        self.botnamecolumn     = Label(self.frame,  text = '',  font = 'courier 10', width = max(int(self.name_max/8)+1,    15))
        self.botequationcolumn = Label(self.frame,  text = '',  font = 'courier 10', width = max(int(self.formula_max/8)+1, 20))
        self.botratecolumn     = Label(self.frame,  text = '',  font = 'courier 10', width = max(int(self.rate_max/8)+1,    10))
        self.botcoefcolumn     = Label(self.frame,  text = '',  font = 'courier 10', width = max(int(self.value_max/8)+1,   10))
        self.botendcolumn      = Label(self.frame,  text = '',  font = 'courier 10', width = 1 )

        
        self.addwidget      = Button(self.bframe, text = 'Add reactions', command = self.addcoefficient, width = 20)
        self.blank1         = Label (self.bframe, text = ' ')
        self.blank2         = Label (self.bframe, text = ' ')
        #self.blank3         = Label (self.frame, text = ' ')
        self.blank4         = Label (self.bframe, text = ' ')
        self.topline        = Label (self.frame, width = 10, text = '-' * 1000)

        #show the widgets on the grid

        self.instructions.grid( row = 0, column = 0, padx = 8, columnspan = 6, sticky = 'W')

        self.blankcolumn.grid(      row = 1, column = 0, sticky = 'WE', padx = 1)
        self.layercolumn.grid(      row = 1, column = 1, sticky = 'WE', padx = 4)
        self.editcolumn.grid(       row = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(        row = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(       row = 1, column = 4, sticky = 'WE', padx = 4)
        self.equationcolumn.grid(   row = 1, column = 5, sticky = 'WE', padx = 4)
        self.ratecolumn.grid(       row = 1, column = 6, sticky = 'WE', padx = 4)
        self.coefcolumn.grid(       row = 1, column = 7, sticky = 'WE', padx = 4)
        self.endcolumn.grid(        row = 1, column = 8, sticky = 'WE', padx = 4)
        
        
        self.layerlabel.grid(       row = 2, column = 1, padx = 1, sticky = 'WE', pady = 4)
        self.namelabel.grid(        row = 2, column = 4, padx = 1, sticky = 'WE', pady = 4)
        self.equationlabel.grid(    row = 2, column = 5, padx = 1, sticky = 'WE', pady = 4)
        self.ratelabel.grid(        row = 2, column = 6, padx = 1, sticky = 'WE', pady = 4)
        self.coeflabel.grid(        row = 2, column = 7, padx = 1, sticky = 'WE', pady = 4)

        #self.blank3.grid(row = 3)

        self.updatecoefficients()
        
    def updatecoefficients(self):
        
        self.addwidget.grid_forget()
        self.blank1.grid_forget()
        self.blank2.grid_forget()
        self.topline.grid_forget()

        namelabellength         = 15

        full_check = 1
        self.topline.grid(        row = 0,    column = 1,     columnspan = 7,  sticky = 'WE', pady = 1)

        row = 1
        for layer in self.layers:
            row_layer = row
            try: layer.remove_reactionwidgets()
            except: pass
            for reaction in self.reactions:
                try: self.coefficients[layer.name][reaction.name].remove_propertieswidgets()
                except:pass
                if self.coefficients[layer.name][reaction.name].lam <> 0:
                    self.coefficients[layer.name][reaction.name].propertieswidgets(self.frame, row, self.master, self.formulatype, self.superfont, self.subfont, self.timeunit, self.concunit)
                    row = row + 1
                else: full_check = 0
            layer.reactionwidgets(self.frame, row, row_layer)
            row = row + 2

        self.botblankcolumn.grid(      row = row, column = 0, sticky = 'WE', padx = 1)
        self.botlayercolumn.grid(      row = row, column = 1, sticky = 'WE', padx = 4)
        self.boteditcolumn.grid(       row = row, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.botdelcolumn.grid(        row = row, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.botnamecolumn.grid(       row = row, column = 4, sticky = 'WE', padx = 4)
        self.botequationcolumn.grid(   row = row, column = 5, sticky = 'WE', padx = 4)
        self.botratecolumn.grid(       row = row, column = 6, sticky = 'WE', padx = 4)
        self.botcoefcolumn.grid(       row = row, column = 7, sticky = 'WE', padx = 4)
        self.botendcolumn.grid(        row = row, column = 8, sticky = 'WE', padx = 4)
        row = row + 1

        self.blank1.grid(row = row, columnspan = 11, sticky = 'WE')
        row = row + 1
        self.blank2.grid(row = row, columnspan = 11)
        row = row + 1
        if full_check ==0:
            self.addwidget.grid(row = row, columnspan = 11)
            row = row + 1
        else:
            self.blank4.grid(row = row, columnspan = 11)
            row = row + 1

        self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def addcoefficient(self, event = None):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(CoefficientEditor(self.top, self.system, self.coefficients[self.layers[0].name][self.reactions[0].name], self.coefficients, editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.coefficients[self.top.window.layer.get()][self.top.window.reaction.get()].get_coefficients(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatecoefficients()
            
        
    def editcoefficient(self, layername, reactionname):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(CoefficientEditor(self.top, self.system, self.coefficients[layername][reactionname], self.coefficients, editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.coefficients[layername][reactionname].get_coefficients(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatecoefficients()
        

    def delcoefficient(self, layername, reactionname):

        self.coefficients[layername][reactionname].lam = 0
        
        self.updatecoefficients()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

def get_reactioncoefficients(system, step):
    """Get some basic parameters for each layer."""

    root_step = 0

    if len(system.reactions) > 0:
        root = CapSimWindow(master = None, buttons = 1)
        root.make_window(ReactionCoefficients(root, system, editflag = 0))
        root.mainloop()

        if root.main.get() == 1:    system = None
        else:
            root_step = root.step.get()
            if root.step.get() == 1:
                system.get_reactioncoefficients(root.window)
                for layer in system.layers:
                    layer.remove_reactionwidgets()
                    for reaction in system.reactions:
                        system.coefficients[layer.name][reaction.name].remove_propertieswidgets()
            else:
                system.coefficients = None
        root.destroy()

    else:
        if system.coefficients == None:
            root_step = 1
            system.coefficients = {}
            for layer in system.layers: system.coefficients[layer.name] = {}
        else:
            system.coefficients = None
            root_step = -1

    return system, step + root_step
