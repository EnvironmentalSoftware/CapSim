#! /usr/bin/env python
#
#This is the Tkinter GUI for the summary window for the simulation.

import tkMessageBox as tkmb, cPickle as pickle, sys, os
import _winreg as wreg

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)
CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
Filepath =wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
CapSimKey.Close()

from Tkinter              import Tk, Toplevel, Canvas, Frame, Label, Entry, Text, Button, Scrollbar, OptionMenu, StringVar, DoubleVar, IntVar, FLAT, RAISED, Checkbutton
from capsim_object_types  import CapSimWindow, Chemical, Matrix, MatrixComponent, Layer, Sorption, Coefficient, IC, BC, SolidIC
from chemicalproperties   import ChemicalProperties
from matrixproperties     import MatrixProperties
from layerproperties      import LayerProperties
from sorptionproperties   import SorptionProperties
from reactionproperties   import ReactionProperties
from reactioncoefficients import ReactionCoefficients
from systemproperties     import SystemProperties
from layerconditions      import LayerConditions
from solidlayerconditions import SolidLayerConditions
from solveroptions        import SolverOptions
from inputoptions         import InputOptions

from capsim_functions     import text_converter


class Summary:
    """Summary window of all the input file simulation."""

    def __init__(self, master, system, database, materials):
        """The parameters that are to be displayed by the GUI are defined here
        first, then set by the main program."""

        self.system    = system           #stores the system data
        self.version   = system.version   #CapSim version
        self.fonttype  = system.fonttype  #font for summary window
        self.database  = database
        self.materials = materials
        
        self.systemrow = max(14, len(self.system.layers) + 6)
        self.chemrow   = max(10, len(self.system.chemicals) + 2)
        
        self.master    = master
        self.bframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.tframe    = Frame(master.bframe)

        self.bgcolor   = self.frame.cget('bg')
        self.top       = None             #existence of toplevel widget flag

    def make_widgets(self):
        """Make and grid all the widgets for the summary GUI window."""
        self.frame_width = 80

        self.intro        = Label(self.frame, text = 'The following summarizes the information you have provided for ' +
                                  'this simulation. Please verify that it is correct and update as necessary.\n', justify = 'left')

        self.rowcolumn     = Label(self.frame, text = '', font = 'courier 10', width = 2)
        self.titelcolumn   = Label(self.frame, text = '', font = 'courier 10', width = 10)
        self.framecolumn   = Label(self.frame, text = '', font = 'courier 10', width = self.frame_width)
        self.blank2column  = Label(self.frame, text = '', font = 'courier 10', width = 2)
        self.buttoncolumn  = Label(self.frame, text = '', font = 'courier 10', width = 18)
        self.blank3column  = Label(self.frame, text = '', font = 'courier 10', width = 2)

        self.chemicallabel = Label(self.frame, text = 'Chemicals:')
        self.reactionlabel = Label(self.frame, text = 'Reactions:')
        self.layerlabel    = Label(self.frame, text = 'Layers:')
        self.systemlabel   = Label(self.frame, text = 'System:')
        self.solverlabel   = Label(self.frame, text = 'Solver:')

        self.chemicalbutton    = Button(self.frame, text = 'Edit Chemical Properties',   command = self.edit_chemicalproperties)
        self.reactionbutton    = Button(self.frame, text = 'Edit Reaction Properties',   command = self.edit_reactionproperties)
        self.matrixbutton      = Button(self.frame, text = 'Edit Material Properties',   command = self.edit_matrixproperties)
        self.sorptionbutton    = Button(self.frame, text = 'Edit Sorption Properties',   command = self.edit_sorptionproperties)
        self.layerbutton       = Button(self.frame, text = 'Edit Layer Properties',      command = self.edit_layerproperties)
        self.coefficientbutton = Button(self.frame, text = 'Edit Reaction Coefficients', command = self.edit_reactioncoefficients)
        self.systembutton      = Button(self.frame, text = 'Edit System Parameters',     command = self.edit_systemproperties)
        self.conditionbutton   = Button(self.frame, text = 'Edit Auxiliary Conditions',  command = self.edit_layerconditions)
        self.solverbutton      = Button(self.frame, text  = 'Edit Solver Options',       command = self.edit_solveroptions)
        self.inputbutton       = Button(self.frame, text  = 'Edit File Options',         command = self.edit_inputoptions)

        row_number = 21
        self.rowlabels          = []
        for i in range(row_number):
            self.rowlabels.append(Label(self.frame, text = '', width = 1))

        row = 2
        for rowlabel in self.rowlabels:
            rowlabel.grid(row = row,  column = 0, sticky = 'WE', padx = 1, pady = 1)
            row = row + 1

        self.intro.grid(row = 0, columnspan = 6, pady = 2, sticky = 'W', padx = 10)
        
        self.rowcolumn.grid(     row = 1,  column = 0,  pady = 1, sticky = 'WE', padx = 1)
        self.titelcolumn.grid(   row = 1,  column = 1,  pady = 1, sticky = 'WE', padx = 1)
        self.framecolumn.grid(   row = 1,  column = 2,  pady = 1, sticky = 'WE', padx = 1)
        self.blank2column.grid(  row = 1,  column = 3,  pady = 1, sticky = 'WE', padx = 1)
        self.buttoncolumn.grid(  row = 1,  column = 4,  pady = 1, sticky = 'WE', padx = 1)
        self.blank3column.grid(  row = 1,  column = 5,  pady = 1, sticky = 'WE', padx = 1)

        self.chemical_row = 2
        self.reaction_row = 3
        self.layer_row    = 8
        self.system_row   = 4
        self.solver_row   = 4

        row = 2
        self.chemicallabel.grid(        row = row,      column = 1,  sticky = 'WE', padx = 1,  pady = 1 )
        self.chemicalbutton.grid(       row = row,      column = 4,  sticky = 'WE', padx = 1)
        row = row + self.chemical_row
        self.reactionlabel.grid(        row = row,      column = 1,  sticky = 'WE', padx = 1,  pady = 1)
        self.reactionbutton.grid(       row = row,      column = 4,  sticky = 'WE', padx = 1)
        row = row + self.reaction_row
        self.layerlabel.grid(           row = row,      column = 1,  sticky = 'WE', padx = 1,  pady = 1)
        self.matrixbutton.grid(         row = row    ,  column = 4,  sticky = 'WE', padx = 1)
        self.sorptionbutton.grid(       row = row + 2,  column = 4,  sticky = 'WE', padx = 1)
        self.layerbutton.grid(          row = row + 4,  column = 4,  sticky = 'WE', padx = 1)
        self.coefficientbutton.grid(    row = row + 6,  column = 4,  sticky = 'WE', padx = 1)
        row = row + self.layer_row
        self.systemlabel.grid(          row = row,      column = 1,  sticky = 'WE', padx = 1,  pady = 1)
        self.systembutton.grid(         row = row    ,  column = 4,  sticky = 'WE', padx = 1)
        self.conditionbutton.grid(      row = row + 2,  column = 4,  sticky = 'WE', padx = 1)

        row = row + self.system_row
        self.solverlabel.grid(          row = row,      column = 1,  sticky = 'WE', padx = 1,  pady = 1)
        self.solverbutton.grid(         row = row,      column = 4,  sticky = 'WE', padx = 1)
        self.inputbutton.grid(          row = row + 2,  column = 4,  sticky = 'WE', padx = 1)

        #bind the "Return" key to the appropriate methods (listed next)

        self.chemicalbutton.bind('<Return>',    self.edit_chemicalproperties)
        self.reactionbutton.bind('<Return>',    self.edit_reactionproperties)
        self.matrixbutton.bind('<Return>',      self.edit_matrixproperties)
        self.sorptionbutton.bind('<Return>',    self.edit_sorptionproperties)
        self.layerbutton.bind('<Return>',       self.edit_layerproperties)
        self.coefficientbutton.bind('<Return>', self.edit_reactioncoefficients)
        self.systembutton.bind('<Return>',      self.edit_systemproperties)
        self.conditionbutton.bind('<Return>',   self.edit_layerconditions)
        self.solverbutton.bind('<Return>',      self.edit_solveroptions)

        self.updatesummary()

    def updatesummary(self):

        self.update_chemicals_widgets(row = 2)
        self.update_reactions_widgets(row = 2 + self.chemical_row)
        self.update_layers_widgets(row = 2 + self.chemical_row+ self.reaction_row)
        self.update_system_widgets(row = 2 + self.chemical_row+ self.reaction_row+ self.layer_row)
        self.update_solver_widgets(row = 2 + self.chemical_row+ self.reaction_row+ self.layer_row+ self.system_row)

        self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def edit_chemicalproperties(self, event = None):
        """Makes a window to edit simulation parameters."""

        if self.top is None:

            chemicals = [chemical.copy() for chemical in self.system.chemicals]
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(ChemicalProperties(self.top, self.system, self.database))
            self.top.mainloop()

            if self.top is not None:

                self.system.get_chemicalproperties(self.top.window)
                for chemical in self.system.chemicals: chemical.remove_chemicalwidgets()
                self.top.destroy()
                self.top = None
                
            #update the summary screen
            #need to update reactions, sorptions and auxiliary conditions if the chemicals of layers changes
            property_check = 0
            
            add_list    = []
            remove_list = []
            
            for chemical in chemicals: remove_list.append(chemical.number)
            for new_chemical in self.system.chemicals: add_list.append(new_chemical.number)
            
            for chemical in chemicals:
                for new_chemical in self.system.chemicals:
                    if new_chemical.name == chemical.name:
                        remove_list.remove(chemical.number)
                        add_list.remove(new_chemical.number)

                        if chemical.number != new_chemical.number:  property_check = 1
                        if chemical.temp   != new_chemical.temp:    property_check = 1
                        if chemical.Dw     != new_chemical.Dw:      property_check = 1
                        if chemical.Koc    != new_chemical.Koc:     property_check = 1
                        if chemical.Kdoc   != new_chemical.Kdoc:    property_check = 1
                        
            for add_chemical in add_list:
                chemical = self.system.chemicals[add_chemical - 1]
                for component in self.system.components:
                    self.system.sorptions[component.name][chemical.name] = Sorption(component, chemical)

                self.system.BCs[chemical.name] = BC(chemical.name, chemical.soluable)
                for layer in self.system.layers:
                    self.system.ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
                    for component in self.system.matrices[layer.type_index].components:
                        self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)

            for remove_chemical in remove_list:
                chemical = chemicals[remove_chemical - 1]
                for component in self.system.components:
                    del self.system.sorptions[component.name][chemical.name]
                reactions_remove = []
                for reaction in self.system.reactions:
                    reactant_list = [reactant.name for reactant in reaction.reactants]
                    product_list  = [product.name for product in reaction.products]
                    if (reactant_list.count(chemical.name)+product_list.count(chemical.name)) > 0:
                        reactions_remove.append(self.system.reactions.index(reaction))
                        for layer in self.system.layers:
                            del self.system.coefficients[layer.name][reaction.name]
                if len(reactions_remove) > 0:
                    reactions_remove.reverse()
                    for reaction_index in reactions_remove:
                        self.system.reactions.remove(self.system.reactions[reaction_index])

                del self.system.BCs[chemical.name]

                for layer in self.system.layers:
                    del self.system.ICs[layer.name][chemical.name]
                    for component in self.system.matrices[layer.type_index].components:
                        del self.system.SolidICs[layer.name][component.name][chemical.name]

            if len(add_list) != 0:
                self.edit_sorptionproperties(flag = 1)
                self.edit_layerconditions()

            elif property_check != 0:
                self.edit_sorptionproperties(flag = 1)

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()
        
    def edit_reactionproperties(self, flag = None, event = None):
        """Makes a window to edit flow and system parameters."""

        if self.top is None:
            
            reactions = [reaction.copy() for reaction in self.system.reactions] 
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(ReactionProperties(self.top, self.system))
            self.top.mainloop()

            if self.top is not None: 
                
                self.system.get_reactionproperties(self.top.window)
                for reaction in self.system.reactions:
                    reaction.remove_propertieswidgets()
                self.top.destroy()
                self.top = None
                              
            add_list    = []
            remove_list = []
            
            for reaction in reactions: remove_list.append(reaction.number)
            for new_reaction in self.system.reactions: add_list.append(new_reaction.number)

            for reaction in reactions:
                for new_reaction in self.system.reactions:
                    reaction_check = 0
                    if new_reaction.name            != reaction.name:           reaction_check = 1
                    if new_reaction.equation        != reaction.equation:       reaction_check = 1
                    if new_reaction.model           != reaction.model:          reaction_check = 1
                    if len(new_reaction.reactants)  != len(reaction.reactants): reaction_check = 1
                    else:
                        for r_index in range(len(new_reaction.reactants)):
                            if new_reaction.reactants[r_index].coef    != reaction.reactants[r_index].coef:     reaction_check = 1
                            if new_reaction.reactants[r_index].name    != reaction.reactants[r_index].name:     reaction_check = 1
                            if new_reaction.reactants[r_index].formula != reaction.reactants[r_index].formula:  reaction_check = 1
                            if new_reaction.reactants[r_index].index   != reaction.reactants[r_index].index:    reaction_check = 1
                    if len(new_reaction.products)   != len(reaction.products):  reaction_check = 1
                    else:
                        for r_index in range(len(new_reaction.products)):
                            if new_reaction.products[r_index].coef     != reaction.products[r_index].coef:      reaction_check = 1
                            if new_reaction.products[r_index].name     != reaction.products[r_index].name:      reaction_check = 1
                            if new_reaction.products[r_index].formula  != reaction.products[r_index].formula:   reaction_check = 1
                                        
                    if reaction_check == 0:
                        remove_list.remove(reaction.number)
                        add_list.remove(new_reaction.number)
                        
            for remove_reaction in remove_list:
                reaction = reactions[remove_reaction - 1]
                for layer in self.system.layers:
                    del self.system.coefficients[layer.name][reaction.name]
                    
            for add_reaction in add_list:
                reaction = self.system.reactions[add_reaction - 1]
                for layer in self.system.layers:
                    self.system.coefficients[layer.name][reaction.name] = Coefficient(layer, reaction)

            if len(add_list) != 0 or len(remove_list) != 0 or flag == 1:

                self.edit_reactioncoefficients()

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

    def edit_matrixproperties(self, event = None):

        
        if self.top is None:

            matrices   = [matrix.copy()     for matrix      in self.system.matrices]
            components = [component.copy()  for component   in self.system.components]
            component_list = self.system.component_list

            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(MatrixProperties(self.top, self.system, self.materials))
            self.top.mainloop()

            if self.top is not None: #update the screen
                
                self.system.get_matricesproperties(self.top.window)
                for matrix in self.system.matrices:
                    matrix.remove_propertieswidgets()
                self.top.destroy()
                self.top = None
                
            property_check = 0
            layer_check    = 0

            matrix_list = [matrix.name for matrix in self.system.matrices]
            for layer in self.system.layers:
                if matrix_list.count(layer.type) == 0:
                    layer.type = matrix_list[0]
                    layer_check = 1
                layer.type_index = matrix_list.index(layer.type)

            add_list    = []
            remove_list = []

            for component_name in component_list:                remove_list.append(component_list.index(component_name))
            for component_name in self.system.component_list:    add_list.append(self.system.component_list.index(component_name))

            indeces     = []
            new_indeces = []
            
            for index in remove_list:
                for new_index in add_list:
                    if component_list[index] == self.system.component_list[new_index]:
                        indeces.append(index)
                        new_indeces.append(new_index)
            for index in indeces:
                remove_list.remove(index)
            for new_index in new_indeces:
                add_list.remove(new_index)

            for remove_index in remove_list:
                component = components[remove_index]
                del self.system.sorptions[component.name]

                for layer in self.system.layers:
                    for layer_component in self.system.matrices[layer.type_index].components:
                        if layer_component.name == component.name:
                            del self.system.SolidICs[layer.name][component.name]
            
            for add_index in add_list:
                component = self.system.components[add_index]
                self.system.sorptions[component.name] = {}
                for chemical in self.system.chemicals:
                    self.system.sorptions[component.name][chemical.name] = Sorption(component, chemical)

                for layer in self.system.layers:
                    for layer_component in self.system.matrices[layer.type_index].components:
                        if layer_component.name == component.name:
                            self.system.SolidICs[layer.name][component.name] = {}
                            for chemical in self.system.chemicals:
                                self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)

            for component in self.system.components:
                for chemical in self.system.chemicals:
                    self.system.sorptions[component.name][chemical.name].matrix = component
                    self.system.sorptions[component.name][chemical.name].foc    = component.foc
                    self.system.sorptions[component.name][chemical.name].update_material()

            if len(add_list) != 0 or len(remove_list) != 0:

                self.edit_sorptionproperties(flag = 1)
                
            if layer_check == 1:

                self.edit_layerproperties()

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

    def edit_layerproperties(self, flag = None, event = None):
        """Makes a window to get some basic parameters for each layer."""

        
        if self.top is None:
            
            layers          = [layer.copy() for layer in self.system.layers]
            players         = [player for player in self.system.players]
            coefficients    = self.system.coefficients
            ICs             = self.system.ICs
            SolidICs        = self.system.SolidICs
            dep             = self.system.dep

            num_record = [j for j in range(self.system.nlayers)]
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(LayerProperties(self.top, self.system, editflag = 1))
            self.top.mainloop()

            if self.top is not None:
                self.system.get_layerproperties(self.top.window)
                num_record = self.top.window.num_record
                for layer in self.system.layers:
                    layer.remove_propertywidgets()
                self.top.destroy()
                self.top = None
                
            #update the summary screen
            self.updatesummary()
            self.master.geometry()

            #Name_check = 0
            type_check  = 0
            num_check   = 0
            h_check     = 0
            dep_check   = 0

            if len(num_record) != len(layers): num_check = 1
            else:
                for j in range(len(layers)):
                    if num_record[j] != j:     num_check = 1

            if num_check == 1:

                self.system.coefficients = {}
                self.system.ICs          = {}
                self.system.SolidICs     = {}
                self.system.players      = []

                for layer in self.system.layers:
                    if num_record[self.system.layers.index(layer)] >= 0:
                        self.system.coefficients[layer.name] = coefficients[layers[num_record[self.system.layers.index(layer)]].name]
                        self.system.ICs[layer.name]          = ICs[layers[num_record[self.system.layers.index(layer)]].name]
                        self.system.SolidICs[layer.name]     = {}
                        for component in self.system.matrices[layer.type_index].components:
                            if [M_component.name for M_component in self.system.matrices[layers[num_record[self.system.layers.index(layer)]].type_index].components].count(component.name) > 0:
                                self.system.SolidICs[layer.name][component.name]     = SolidICs[layers[num_record[self.system.layers.index(layer)]].name][component.name]
                            else:
                                self.system.SolidICs[layer.name][component.name]     = {}
                                for chemical in self.system.chemicals:
                                    self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)
                        self.system.players.append(players[num_record[self.system.layers.index(layer)]])
                    else:
                        self.system.coefficients[layer.name]    = {}
                        self.system.ICs[layer.name]             = {}
                        self.system.SolidICs[layer.name]        = {}
                        for reaction in self.system.reactions:
                            self.system.coefficients[layer.name][reaction.name] = Coefficient(layer, reaction)
                        for chemical in self.system.chemicals:
                            self.system.ICs[layer.name][chemical.name]          = IC(layer.name, chemical.name)
                        for component in self.system.matrices[layer.type_index].components:
                            self.system.SolidICs[layer.name][component.name] = {}
                            for chemical in self.system.chemicals:
                                self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)
                        self.system.players.append(10)
            else:
                self.system.SolidICs     = {}
                for layer in self.system.layers:
                    component_list = [M_component.name for M_component in self.system.matrices[layers[self.system.layers.index(layer)].type_index].components]
                    self.system.SolidICs[layer.name] = {}
                    for component in self.system.matrices[layer.type_index].components:
                        if component_list.count(component.name) > 0:
                            self.system.SolidICs[layer.name][component.name]     = SolidICs[layers[num_record[self.system.layers.index(layer)]].name][component.name]
                        else:
                            self.system.SolidICs[layer.name][component.name]     = {}
                            for chemical in self.system.chemicals:
                                self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)
                            type_check = 1
                    if layer.h <> layers[self.system.layers.index(layer)].h:
                        self.system.players[self.system.layers.index(layer)] = 10

            if dep != self.system.dep: dep_check = 1

            if num_check == 1:
                self.edit_reactioncoefficients()
                self.edit_layerconditions()
                self.edit_solveroptions(editflag = 1)
            else:
                if type_check == 1:                 self.edit_layerconditions()
                if h_check == 1 or dep_check == 1:  self.edit_solveroptions()

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()
        
    def edit_sorptionproperties(self, flag = None, event = None):
        
        #coefficients = self.system.coefficients
        old_dynamic_flags = []
        dynamic_flags     = []


        for component in self.system.components:
            for chemical in self.system.chemicals:
                if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                    old_dynamic_flags.append(1)
                else:
                    old_dynamic_flags.append(0)

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 1)
            self.top.make_window(SorptionProperties(self.top, self.system))
            self.top.mainloop()

            if self.top is not None: #update the screen
                
                self.system.get_sorptionproperties(self.top.window)
                for component in self.system.components:
                    component.remove_sorptionwidgets()
                for chemical in self.system.chemicals:
                    if chemical.soluable == 1:
                        chemical.remove_sorptionwidgets()
                for component in self.system.components:
                    for chemical in self.system.chemicals:
                        if chemical.soluable == 1:
                            self.system.sorptions[component.name][chemical.name].remove_propertieswidgets()
                        if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                            dynamic_flags.append(1)
                        else:
                            dynamic_flags.append(0)
                self.top.destroy()
                self.top = None

            dynamic_check = 0
            for flag_index in range (len(dynamic_flags)):
                if dynamic_flags[flag_index] != old_dynamic_flags[flag_index]:
                    dynamic_check = 1

            if dynamic_check == 1:
                self.system.SolidICs = {}
                for layer in self.system.layers:
                    self.system.SolidICs[layer.name] = {}
                    for component in self.system.matrices[layer.type_index].components:
                        self.system.SolidICs[layer.name][component.name] = {}
                        for chemical in self.system.chemicals:
                            self.system.SolidICs[layer.name][component.name][chemical.name] = SolidIC(layer.name, component.name, chemical.name)

                self.edit_layerconditions()
                self.edit_solveroptions()

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

        
    def edit_reactioncoefficients(self, event = None):
        
        #coefficients = self.system.coefficients

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(ReactionCoefficients(self.top, self.system, editflag = 1))
            self.top.mainloop()

            if self.top is not None: #update the screen
                
                self.system.get_reactioncoefficients(self.top.window)
                for layer in self.system.layers:
                    layer.remove_reactionwidgets()
                    for reaction in self.system.reactions:
                        self.system.coefficients[layer.name][reaction.name].remove_propertieswidgets()
                self.top.destroy()
                self.top = None

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()
        

    def edit_systemproperties(self, flag = None, event = None):
        """Makes a window to get models for the layers."""

        adv     = self.system.adv
        bio     = self.system.bio
        con     = self.system.con
        hbio    = self.system.hbio
        ptidal  = self.system.ptidal


        if self.top is None:

            self.adv    = self.system.adv
            self.bio    = self.system.bio
            self.con    = self.system.con
            
            self.Vdar   = self.system.Vdar
            self.Vtidal = self.system.Vtidal
            self.ptidal = self.system.ptidal        
            self.hbio   = self.system.hbio
            self.Dbiop  = self.system.Dbiop
            self.Dbiopw = self.system.Dbiopw
            self.hcon   = self.system.hcon
            self.t90    = self.system.t90
            
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(SystemProperties(self.top, self.system))
            self.top.mainloop()

            if self.top is not None:
                self.system.get_systemproperties(self.top.window)
                self.top.destroy()
                self.top = None

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

        if self.system.adv != 'Period oscillation': self.system.averageoption = 'Instaneous'

        if adv != self.system.adv or bio != self.system.bio or con != self.system.con or hbio != self.system.hbio or ptidal != self.system.ptidal:

            self.edit_solveroptions()

    def edit_layerconditions(self, event = None):
        
        
        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(LayerConditions(self.top, self.system))
            self.top.mainloop()

            if self.top is not None: #update the screen
                
                self.system.get_layerconditions(self.top.window)
                
                for layer in self.system.layers:
                    layer.get_layerconditions()
                    layer.remove_ICwidgets()
                    for chemical in self.system.chemicals:
                        if chemical.soluable == 1:
                            self.system.ICs[layer.name][chemical.name].remove_widgets()

                for chemical in self.system.chemicals:
                    if chemical.soluable == 1:
                        chemical.remove_ICwidgets()
                        self.system.BCs[chemical.name].remove_widgets()

                self.top.destroy()
                self.top = None

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

        solid_check = 0

        for chemical in self.system.chemicals:
            for component in self.system.components:
                if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                    solid_check = 1

        if solid_check > 0:

            if self.top is None:
                self.top = CapSimWindow(master = self.master, buttons = 3)
                self.top.make_window(SolidLayerConditions(self.top, self.system))
                self.top.mainloop()

                if self.top is not None: #update the screen

                    self.system.get_solidlayerconditions(self.top.window)

                    for layer in self.system.layers:
                        layer.remove_SolidICwidgets()
                        for component in self.system.matrices[layer.type_index].components:
                            component.remove_SolidICswidgets()
                            for chemical in self.system.chemicals:
                                self.system.SolidICs[layer.name][component.name][chemical.name].remove_widgets()

                    for chemical in self.system.chemicals:
                        try:    chemical.remove_ICwidgets()
                        except: pass

                    self.top.destroy()
                    self.top = None

                    self.updatesummary()
                    self.master.geometry()
                    self.master.center()


            else: self.master.open_toplevel()

    def edit_solveroptions(self, event = None, editflag = 0):
        """Makes a window to edit output options."""

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(SolverOptions(self.top, self.system, editflag))
            self.top.mainloop()

            if self.top is not None:
                self.system.get_solveroptions(self.top.window)
                self.top.destroy()
                self.top = None
            
            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

    def edit_inputoptions(self, event = None):
        """Makes a window to edit output options."""

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 3)
            self.top.make_window(InputOptions(self.top, self.system))
            self.top.mainloop()

            if self.top is not None:
                self.system.get_inputoptions(self.top.window)
                self.top.destroy()
                self.top = None

            self.updatesummary()
            self.master.geometry()
            self.master.center()

        else: self.master.open_toplevel()

    def update_chemicals_widgets(self, row):

        try:
            for chemicalnamelabel in self.chemicalnamelabels: chemicalnamelabel.grid_forget()
            self.chemical_frame.grid_forget()
            self.chemical_canvas.grid_forget()
            self.chemical_vscrollbar.grid_forget()
        except: pass

        self.chemical_frame      = Frame(self.frame)
        self.chemical_canvas     = Canvas(self.chemical_frame, height = 22 * self.chemical_row)

        self.chemical_frame.grid_rowconfigure(0, weight=1)
        self.chemical_frame.grid_columnconfigure(0, weight=1)

        self.chemical_vscrollbar = Scrollbar(self.chemical_frame)
        self.chemical_canvas.config(yscrollcommand = self.chemical_vscrollbar.set)
        self.chemical_vscrollbar.config(command = self.chemical_canvas.yview)

        self.chemical_canvas.grid(row     = 0, column = 0, sticky = 'NSWE')

        self.chemical_content   = Frame(self.chemical_canvas)

        self.chemicalnamelabels = [Label(self.chemical_content, text = chemical.name, width = 18) for chemical in self.system.chemicals]
        rows = int(self.system.nchemicals/4)
        lastrows = self.system.nchemicals-rows*4
        for i in range(rows):
            for column in range(4):
                self.chemicalnamelabels[i*4+column].grid(row = i, column = column, pady = 1)
        for column in range(lastrows):
            self.chemicalnamelabels[rows*4+column].grid(row = rows, column = column, pady = 1)

        if (self.system.nchemicals) > self.chemical_row*4:
            self.chemical_vscrollbar.grid(row = 0, column = 1, sticky = 'NS')
        self.chemical_canvas.create_window(0, 0, anchor = 'nw', window = self.chemical_content)
        self.chemical_canvas.config(scrollregion = (0,0,59,(rows+(lastrows > 0)*1)*23))

        self.chemical_frame.grid( row     = row, column = 2, sticky = 'NWE', rowspan = self.chemical_row)

        self.chemical_frame.update()


    def update_reactions_widgets(self, row):

        try:
            for i in range(len(self.system.reactions)):
                self.reactionnamelabels[i].grid_forget()
                self.reactionequalabels[i].grid_forget()
            self.reaction_frame.grid_forget()
            self.reaction_canvas.grid_forget()
            self.reaction_vscrollbar.grid_forget()
            self.reaction_hscrollbar.grid_forget()
        except: pass

        self.reaction_frame      = Frame(self.frame)
        self.reaction_canvas     = Canvas(self.reaction_frame, height = 22 * self.reaction_row)

        self.reaction_frame.grid_rowconfigure(0, weight=1)
        self.reaction_frame.grid_columnconfigure(0, weight=1)

        self.reaction_vscrollbar = Scrollbar(self.reaction_frame)
        self.reaction_canvas.config(yscrollcommand = self.reaction_vscrollbar.set)
        self.reaction_vscrollbar.config(command = self.reaction_canvas.yview)

        self.reaction_hscrollbar = Scrollbar(self.reaction_frame, orient = 'horizontal')
        self.reaction_canvas.config(xscrollcommand = self.reaction_hscrollbar.set)
        self.reaction_hscrollbar.config(command = self.reaction_canvas.xview)

        self.reaction_canvas.grid(row     = 0, column = 0, sticky = 'NSWE')

        self.reaction_content  = Frame(self.reaction_canvas)

        #self.reactionnumberlabels = [Label(self.reaction_content, text = reaction.number,   width = 3)                  for reaction in self.system.reactions]
        self.reactionnamelabels   = [Label(self.reaction_content, text = reaction.name,  width = 18, justify = 'left')              for reaction in self.system.reactions]
        self.reactionequalabels   = [Label(self.reaction_content, text = reaction.equation, font = 'Calibri 11')  for reaction in self.system.reactions]

        for i in range(len(self.system.reactions)):
            #self.reactionnumberlabels[i].grid(row = i, column = 0, pady = 1)
            self.reactionnamelabels[i].grid(row = i, column = 0, pady = 1, sticky = 'W')
            self.reactionequalabels[i].grid(row = i, column = 1, pady = 1)

        vscrollbar_check = 0
        vscrollbar_width = 0
        for i in range(len(self.reactionequalabels)):
            if self.reactionequalabels[i].winfo_reqwidth() + self.reactionnamelabels[i].winfo_reqwidth() + 16  > self.frame_width * 8:
                self.reaction_hscrollbar.grid(row = 1, column = 0, sticky = 'WE')
                vscrollbar_check = 1
            if (self.reactionequalabels[i].winfo_reqwidth() + self.reactionnamelabels[i].winfo_reqwidth()) > vscrollbar_width:
                vscrollbar_width = self.reactionequalabels[i].winfo_reqwidth() + self.reactionnamelabels[i].winfo_reqwidth()

        if (len(self.system.reactions) + vscrollbar_check) >= self.reaction_row:
            self.reaction_vscrollbar.grid(row = 0, column = 1, sticky = 'NS')

        self.reaction_canvas.create_window(0, 0, anchor = 'nw', window = self.reaction_content)
        self.reaction_canvas.config(scrollregion = (0,0,vscrollbar_width+16,sum([reactionequalabel.winfo_reqheight() for reactionequalabel in self.reactionequalabels])+16))

        self.reaction_frame.grid( row     = row, column = 2, sticky = 'NWE', rowspan = self.reaction_row)

        self.reaction_frame.update()

    def update_layers_widgets(self, row):

        try:
            for i in range(len(self.system.layers)):
                self.layernamelabels[i].grid_forget()
                self.layertypelabels[i].grid_forget()
                self.layerthicklabels[i].grid_forget()
            self.layer_frame.grid_forget()
            self.layer_canvas.grid_forget()
            self.layer_vscrollbar.grid_forget()
            self.layer_hscrollbar.grid_forget()

        except: pass

        self.layer_frame     = Frame(self.frame)
        self.layer_canvas    = Canvas(self.layer_frame, height = 22 * self.layer_row)

        self.layer_frame.grid_rowconfigure(0, weight=1)
        self.layer_frame.grid_columnconfigure(0, weight=1)

        self.layer_vscrollbar = Scrollbar(self.layer_frame)
        self.layer_canvas.config(yscrollcommand = self.layer_vscrollbar.set)
        self.layer_vscrollbar.config(command = self.layer_canvas.yview)

        self.layer_hscrollbar = Scrollbar(self.layer_frame, orient = 'horizontal')
        self.layer_canvas.config(xscrollcommand = self.layer_hscrollbar.set)
        self.layer_hscrollbar.config(command = self.layer_canvas.xview)

        self.layer_canvas.grid(row     = 0, column = 0, sticky = 'NSWE')

        self.layer_content  = Frame(self.layer_canvas)

        self.layernamelabels        = [Label(self.layer_content, text = layer.name,     width = 14)            for layer in self.system.layers]
        self.layertypelabels        = [Label(self.layer_content, text = layer.type)                            for layer in self.system.layers]
        self.layerthicklabels       = [Label(self.layer_content, text = str(layer.h) + ' ' + self.system.lengthunit, width = 15, justify = 'center') for layer in self.system.layers]

        if self.system.layers[0].name == 'Deposition':
            self.layerthicklabels[0] = Label(self.layer_content, text = str(self.system.layers[0].h) + ' ' + self.system.lengthunit + '/' + self.system.timeunit, width = 15, justify = 'center')

        for i in range(len(self.system.layers)):
            self.layernamelabels[i].grid(       row = i, column = 0)
            self.layertypelabels[i].grid(       row = i, column = 1)
            self.layerthicklabels[i].grid(      row = i, column = 2)

        vscrollbar_check = 0
        vscrollbar_width = 0
        for i in range(len(self.layernamelabels)):
            if self.layernamelabels[i].winfo_reqwidth() + self.layertypelabels[i].winfo_reqwidth()+ self.layerthicklabels[i].winfo_reqwidth()  > self.frame_width * 8:
                self.layer_hscrollbar.grid(row = 1, column = 0, sticky = 'WE')
                vscrollbar_check = 1
            if (self.layernamelabels[i].winfo_reqwidth() + self.layertypelabels[i].winfo_reqwidth()+self.layerthicklabels[i].winfo_reqwidth()) > vscrollbar_width:
                vscrollbar_width = self.layernamelabels[i].winfo_reqwidth() + self.layertypelabels[i].winfo_reqwidth() + self.layerthicklabels[i].winfo_reqwidth()

        if (len(self.system.layers) + vscrollbar_check) > self.layer_row:  self.layer_vscrollbar.grid(row = 0, column = 1, sticky = 'NS')

        self.layer_canvas.create_window(0, 0, anchor = 'nw', window = self.layer_content)
        self.layer_canvas.config(scrollregion = (0,0,vscrollbar_width,sum([layernamelabel.winfo_reqheight() for layernamelabel in self.layernamelabels])+16))

        self.layer_frame.grid( row     = row, column = 2, sticky = 'NWE', rowspan = self.layer_row)

        self.layer_frame.update()


    def update_system_widgets(self, row):

        try:
            self.system_frame.grid_forget()
            self.system_canvas.grid_forget()
            self.system_content.grid_forget()

            self.NoVdarwidget.grid_forget()
            self.UniVdarlabel.grid_forget()
            self.UniVdarwidget.grid_forget()
            self.TidalVdarlabel.grid_forget()
            self.TidalVdarwidget.grid_forget()
            self.ptidallabel.grid_forget()
            self.ptidalwidget.grid_forget()

            self.Nobiolabel.grid_forget()
            self.biolabel.grid_forget()
            self.tBClabel.grid_forget()
            self.tBCwidget.grid_forget()
            self.bBClabel.grid_forget()
            self.bBCwidget.grid_forget()

        except: pass

        self.system_frame     = Frame(self.frame)
        self.system_canvas    = Canvas(self.system_frame, height = 23 * self.system_row)

        self.system_frame.grid_rowconfigure(0, weight=1)
        self.system_frame.grid_columnconfigure(0, weight=1)

        self.system_canvas.grid(row     = 0, column = 0, sticky = 'NSWE')

        self.system_content  = Frame(self.system_canvas)

        self.blanklabel         = Label(self.system_content,  text = '       ')

        self.NoVdarwidget       = Label(self.system_content,  text = 'No advection flow')
        self.UniVdarlabel       = Label(self.system_content,  text = 'Darcy velocity:')
        self.UniVdarwidget      = Label(self.system_content,  text = '%.1f %s/%s' %(self.system.Vdar, self.system.lengthunit,self.system.timeunit))
        self.TidalVdarlabel     = Label(self.system_content,  text = 'Darcy velocity:')
        self.TidalVdarwidget    = Label(self.system_content,  text = '%.1f' %(self.system.Vdar) + u'\u00B1' + '%.1f %s/%s' %(self.system.Vtidal, self.system.lengthunit,self.system.timeunit))
        self.ptidallabel        = Label(self.system_content,  text = 'Oscillation period:', width = 25)
        self.ptidalwidget       = Label(self.system_content,  text = '%.4f %s' % (self.system.ptidal, self.system.timeunit))

        self.Nobiolabel         = Label(self.system_content,  text = 'Ignore the bioturbation')
        self.biolabel           = Label(self.system_content,  text = 'Model the bioturbation')

        self.tBClabel           = Label(self.system_content, text = 'Benthic surface boundary:  ')
        self.tBCwidget          = Label(self.system_content, text = str(self.system.topBCtype))
        
        self.bBClabel           = Label(self.system_content, text = 'Underlying sediment boundary:  ')
        self.bBCwidget          = Label(self.system_content, text = str(self.system.botBCtype))

        self.blanklabel.grid(row      = 0,      column = 0, sticky= 'W')

        if self.system.adv == 'None':
            
            self.NoVdarwidget.grid(row      = 0,      column = 1, sticky= 'W',    columnspan = 2)

        elif self.system.adv == 'Steady flow':
            
            self.UniVdarlabel.grid(row      = 0,      column = 1, sticky= 'W')
            self.UniVdarwidget.grid(row     = 0,      column = 2, sticky= 'W')

        elif self.system.adv == 'Period oscillation':
            
            self.TidalVdarlabel.grid(row    = 0,      column = 1, sticky= 'W')
            self.TidalVdarwidget.grid(row   = 0,      column = 2, sticky= 'W')

            self.ptidallabel.grid(row       = 0 ,     column = 3, sticky= 'W')
            self.ptidalwidget.grid(row      = 0 ,     column = 4, sticky= 'W')

        if self.system.bio == 'None': self.Nobiolabel.grid( row       = 1,  column = 1, sticky = 'W', columnspan = 2, pady = 1)
        else:                         self.biolabel.grid( row         = 1,  column = 1, sticky = 'W', columnspan = 2, pady = 1)

        self.tBClabel.grid( row             = 2  ,  column = 1, sticky = 'W', pady = 1)
        self.tBCwidget.grid( row            = 2  ,  column = 2, sticky = 'W', pady = 1)

        self.bBClabel.grid( row             = 3  ,  column = 1, sticky = 'W', pady = 1)
        self.bBCwidget.grid( row            = 3  ,  column = 2, sticky = 'W', pady = 1)
        
        self.system_canvas.create_window(0, 0, anchor = 'nw', window = self.system_content)

        self.system_frame.grid( row     = row, column = 2, sticky = 'WE', rowspan = self.system_row)

        self.system_frame.update()


    def update_solver_widgets(self, row):

        try:
            self.solver_frame.grid_forget()
            self.solver_canvas.grid_forget()
            self.solver_content.grid_forget()

        except: pass

        self.solver_frame     = Frame(self.frame, height = 23 *self.solver_row)
        self.solver_canvas    = Canvas(self.solver_frame, height = 23 *self.solver_row)

        self.solver_frame.grid_rowconfigure(0, weight=1)
        self.solver_frame.grid_columnconfigure(0, weight=1)

        self.solver_canvas.grid(row     = 0, column = 0, sticky = 'NSWE')

        self.solver_content  = Frame(self.solver_canvas)

        self.blanksolverlabel = Label(self.solver_content,  text = '       ')

        self.durationwidget  = Label(self.solver_content,  text  = 'Run a simulation of %.1f %s' %(self.system.tfinal, self.system.timeunit))
        self.nonlinearlabel  = Label(self.solver_content,  text  = 'Non-linear solver')
        self.nonlineariwdget = Label(self.solver_content,  text  = self.system.nonlinear)

        self.blanksolverlabel.grid(row    = 0,        column = 0,     sticky=  'W',  pady = 1)
        self.durationwidget.grid(  row    = 0,        column = 1,     sticky = 'W', pady = 1)
        self.nonlinearlabel.grid(  row    = 1,        column = 1,     sticky = 'W', pady = 1)
        self.nonlineariwdget.grid( row    = 1,        column = 2,     sticky = 'W', pady = 1)

        self.solver_canvas.create_window(0, 0, anchor = 'nw', window = self.solver_content)

        self.solver_frame.grid( row     = row, column = 2, sticky = 'WE', rowspan = self.solver_row)

        self.solver_frame.update()

    def make_csv_file(self, Filepath):

        lengthunits = ['um', 'cm', 'm']
        concunits   = ['ug/L', 'mg/L', 'g/L', 'umol/L', 'mmol/L', 'mol/L']
        timeunits   = ['s', 'min', 'hr', 'day', 'yr']
        diffunits   = ['cm^2/s', 'cm^2/yr']

        lengthunit  = lengthunits[self.system.lengthunits.index(self.system.lengthunit)]
        concunit    = concunits[self.system.concunits.index(self.system.concunit)]
        timeunit    = timeunits[self.system.timeunits.index(self.system.timeunit)]
        diffunit    = diffunits[self.system.diffunits.index(self.system.diffunit)]

        file = open(Filepath + '/batch_files/'+ self.system.csvfilename + '.csv', 'w')                              # Create a csv file
        file.write('CapSim,' + self.system.version + '\n')                                        # 1
        file.write('Separate/Continuous,Separate,' + '\n')                                        # 1

        file.write('\n')
        file.write('File\n')

        file.write(',Output file name,'+self.system.csvfilename+'\n')

        file.write('\n\n')                                        # 1
                                                                                        # 2
        file.write('System Units' + '\n')
        file.write(',Length: ,'         + lengthunit      + '\n')         # 4
        file.write(',Concentration: ,'  + concunit    + '\n')         # 5
        file.write(',Time: ,'           + timeunit      + '\n')         # 6
        file.write(',Diffusivity: ,'    + diffunit      + '\n')         # 7
        file.write('\n')

                                                                     # 8
        file.write('Chemicals,'+str(self.system.nchemicals)  + '\n')                     # 9
        file.write(', Name, Formula, MW, Temperature, Dw, Koc, Kdoc, Reference\n') # 10
        for chemical in self.system.chemicals:
            file.write(',' + text_converter(chemical.name) + ',')
            file.write(text_converter(chemical.formula) + ',')
            file.write(str(chemical.MW) + ',')
            file.write(str(chemical.temp) + ',')
            file.write(str(chemical.Dw) + ',')
            file.write(str(chemical.Koc) + ',')
            file.write(str(chemical.Kdoc) + ',')
            file.write(str(chemical.Ref) + ',')
            file.write('\n')                                                            # 10 + nchemicals
        file.write('\n')                                                                # 11 + nchemicals

        file.write('Matrices,' + str(self.system.nmatrices)+ '\n')                       # 12 + nchemicals
        file.write(', Name, Components, Porosity, Bulk density(L/kg), foc, Mixture\n') # 13 + nchemicals
        for matrix in self.system.matrices:
            file.write(',' + matrix.name            + ',')
            file.write(str(len(matrix.components))  + ',')
            file.write(str(matrix.e)                + ',')
            file.write(str(matrix.rho)              + ',')
            file.write(str(matrix.foc)              + ',')
            file.write(matrix.model                 + ',')
            file.write('\n')                                                                     # 13 + nchemicals + nmatrices
        file.write('\n')

        file.write('Matrix Components\n')                       # 12 + nchemicals
        file.write(',Matrix, Component, Weight fraction, Porosity, Bulk density(L/kg), foc\n') # 14 + nchemicals + nmatrices
        for matrix in self.system.matrices:
            for component in matrix.components:
                file.write( ',' + str(matrix.name)  + ',')
                file.write(component.name           + ',')
                file.write(str(component.mfraction) + ',')
                file.write(str(component.e)         + ',')
                file.write(str(component.rho)       + ',')
                file.write(str(component.foc)       + ',')
                file.write('\n')
        file.write('\n')

        file.write('Sorptions,'+ '\n')          # 15 + nchemicals + nmatrices + ncomponents
        file.write(',Component, Chemical, Isotherm, Kinetic, Kd/Koc/Kf/qmax, foc/N/b, ksorp, kdesorp, equilibrium time\n') # 14 + nchemicals + nmatrices
        for component in self.system.components:
            for chemical in self.system.chemicals:
                file.write(',' + component.name + ',')
                file.write(text_converter(chemical.name) + ',')
                file.write(self.system.sorptions[component.name][chemical.name].isotherm         + ',')
                file.write(self.system.sorptions[component.name][chemical.name].kinetic          + ',')
                if self.system.sorptions[component.name][chemical.name].isotherm == self.system.sorptions[component.name][chemical.name].isotherms[0]:
                    file.write(str(self.system.sorptions[component.name][chemical.name].K)      + ',')
                    file.write(',')
                elif self.system.sorptions[component.name][chemical.name].isotherm == self.system.sorptions[component.name][chemical.name].isotherms[1]:
                    file.write(str(self.system.sorptions[component.name][chemical.name].Koc)     + ',')
                    file.write(str(self.system.sorptions[component.name][chemical.name].foc)     + ',')
                elif self.system.sorptions[component.name][chemical.name].isotherm == self.system.sorptions[component.name][chemical.name].isotherms[2]:
                    file.write(str(self.system.sorptions[component.name][chemical.name].Kf)      + ',')
                    file.write(str(self.system.sorptions[component.name][chemical.name].N)       + ',')
                else:
                    file.write(str(self.system.sorptions[component.name][chemical.name].qmax)    + ',')
                    file.write(str(self.system.sorptions[component.name][chemical.name].b)       + ',')

                file.write(str(self.system.sorptions[component.name][chemical.name].ksorp)   + ',')
                file.write(str(self.system.sorptions[component.name][chemical.name].kdesorp) + ',')
                file.write(str(self.system.sorptions[component.name][chemical.name].thalf)   + ',')
                file.write('\n')
        file.write('\n')

        file.write('Layers,'+str(self.system.nlayers)  + '\n')                     # 9
        file.write(', Name, Matrix, Thickness, Tortuosity, Hydraulic Dispersivity, DOC concentration\n') # 10
        for layer in self.system.layers:
            file.write(',' + layer.name + ',')
            file.write(layer.type + ',')
            file.write(str(layer.h) + ',')
            file.write(layer.tort + ',')
            file.write(str(layer.alpha) + ',')
            file.write(str(layer.doc) + ',')
            file.write('\n')                                                            # 10 + nchemicals
        file.write('\n')                                                                # 11 + nchemicals


        file.write('Reactions,'+str(len(self.system.reactions))  + '\n')                     # 9
        for reaction in self.system.reactions:
            file.write(',' + str(reaction.number) + ',')
            file.write(reaction.name  + ',')
            file.write(reaction.model + ',')
            file.write(text_converter(reaction.equation) + ',')
            file.write('\n')
            file.write(',,Reactants,'+str(len(reaction.reactants)) + ',' * (len(reaction.reactants))  + 'Products,' + str(len(reaction.products))+ '\n')

            file.write(',Name,')
            for reactant in reaction.reactants:
                file.write(text_converter(reactant.name) + ',')
            file.write('-->,')
            for product in reaction.products:
                file.write(text_converter(product.name) + ',')
            file.write('\n')

            file.write(',Formula,')
            for reactant in reaction.reactants:
                file.write(text_converter(reactant.formula) + ',')
            file.write('-->,')
            for product in reaction.products:
                file.write(text_converter(product.formula) + ',')
            file.write('\n')

            file.write(',MW,')
            for reactant in reaction.reactants:
                file.write(str(reactant.MW) + ',')
            file.write('-->,')
            for product in reaction.products:
                file.write(str(product.MW) + ',')
            file.write('\n')

            file.write(',Coef,')
            for reactant in reaction.reactants:
                file.write(str(reactant.coef) + ',')
            file.write('-->,')
            for product in reaction.products:
                file.write(str(product.coef) + ',')
            file.write('\n')

            file.write(',Index,')
            for reactant in reaction.reactants:
                file.write(str(reactant.index) + ',')
            file.write('-->,')
            file.write('\n')
        file.write('\n')


        file.write('Reaction Coefficients,'+str(len(self.system.reactions))  + '\n')
        file.write(',Layer, Reaction, Coefficient\n')
        for layer in self.system.layers:
            for reaction in self.system.reactions:
                file.write(',' + layer.name + ',')
                file.write(reaction.name + ',')
                file.write(str(self.system.coefficients[layer.name][reaction.name].lam) + ',')
                file.write('\n')                                                                    # 10 + nchemicals
        file.write('\n')

        file.write('System Properties\n')
        file.write(',Advection,'            +self.system.adv+'\n')
        file.write(',Darcy Velocity,'       +str(self.system.Vdar)+'\n')
        file.write(',Tidal Max Velocity,'   +str(self.system.Vtidal)+'\n')
        file.write(',Tidal Period,'         +str(self.system.ptidal)+'\n')
        file.write(',Bioturbation,'         +self.system.bio+'\n')
        file.write(',Bioturbation Depth,'   +str(self.system.hbio)+'\n')
        file.write(',Gaussian model coefficient,'   +str(self.system.sigma)+'\n')
        file.write(',Particle Dbio,'        +str(self.system.Dbiop)+'\n')
        file.write(',Porewater Dbio,'       +str(self.system.Dbiopw)+'\n')
        file.write(',Consolidation,'        +self.system.con+'\n')
        file.write(',Consolidation h,'      +str(self.system.hcon)+'\n')
        file.write(',Consolidation 90% time,'+str(self.system.t90)+'\n')
        file.write('\n')

        file.write('Auxiliary Conditions\n')
        file.write(',Layer, Type, Parameter,')
        for chemical in self.system.chemicals:
            file.write(text_converter(chemical.name) + ',')
        solidcheck = 0
        for component in self.system.components:
            for chemical in self.system.chemicals:
                if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                    file.write(component.name +'_'+text_converter(chemical.name) + ',')
        file.write('\n')

        file.write(', Benthic,'+ self.system.topBCtype + ',')
        if self.system.topBCtype == 'Fixed Concentration':
            file.write('Surface concentration,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].Co) + ',')
        elif self.system.topBCtype == 'Mass transfer':
            file.write('Mass transfer coefficient,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].k) + ',')
            file.write('\n')
            file.write(',,,Water concentration,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].Cw) + ',')
        else:
            file.write('Mass transfer coefficient,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].k) + ',')
            file.write('\n')
            file.write(',,,Water column retention time,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].tau) + ',')

        file.write('\n\n')

        for layer in self.system.layers:
            file.write(','+layer.name+','+ layer.ICtype + ',')
            if layer.ICtype == 'Uniform':
                file.write('Initial concentration,')
                for chemical in self.system.chemicals:
                    file.write(str(self.system.ICs[layer.name][chemical.name].uniform) + ',')
                for component in self.system.matrices[layer.type_index].components:
                    for chemical in self.system.chemicals:
                        if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                            file.write(str(self.system.SolidICs[layer.name][component.name][chemical.name].uniform) + ',')
            else:
                file.write('Top concentration,')
                for chemical in self.system.chemicals:
                    file.write(str(self.system.ICs[layer.name][chemical.name].top) + ',')
                for component in self.system.matrices[layer.type_index].components:
                    for chemical in self.system.chemicals:
                        if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                            file.write(str(self.system.SolidICs[layer.name][component.name][chemical.name].uniform) + ',')
                file.write('\n')
                file.write(',,,Bottom concentration,')
                for chemical in self.system.chemicals:
                    file.write(str(self.system.ICs[layer.name][chemical.name].bot) + ',')
                for component in self.system.matrices[layer.type_index].components:
                    for chemical in self.system.chemicals:
                        if self.system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                            file.write(str(self.system.SolidICs[layer.name][component.name][chemical.name].uniform) + ',')
            file.write('\n')
        file.write('\n')

        file.write(', Underlying,'+ self.system.botBCtype + ',')
        if self.system.botBCtype == 'Fixed Concentration' or self.system.botBCtype == 'Flux-matching':
            file.write('Concentration,')
            for chemical in self.system.chemicals:
                file.write(str(self.system.BCs[chemical.name].Cb) + ',')
        else:
            file.write('No flux')
        file.write('\n\n')

        file.write('Solver Options, 1\n')
        file.write(',Start time,'+str(0)+'\n')
        file.write(',End time,'+str(self.system.tfinal)+'\n')
        file.write(',Output time steps,'+str(self.system.outputsteps)+'\n')
        file.write(',Discrete time option,'+str(self.system.timeoption)+'\n')
        file.write(',Discrete,'+self.system.discrete + '\n')
        file.write(',Total number of grid points,'+str(self.system.ptotal)+'\n')
        file.write(',Time step,'+str(self.system.delt)+'\n')
        file.write(',Grid option,'+self.system.ptype+'\n')
        file.write(',Time step option,'+self.system.tvariable+'\n')
        file.write(',,')
        for i in range(self.system.nlayers):
            file.write(self.system.layers[i].name + ',')
        file.write('\n')
        file.write(',Layer Grid size,')
        for i in range(self.system.nlayers):
            file.write(str(self.system.delz[i]) +',')
        file.write('\n')
        file.write(',Layer Number of Grids,')
        for i in range(self.system.nlayers):
            file.write( str(self.system.players[i]) + ',')
        file.write('\n')
        file.write(',Time step in a tidal circle,'+str(self.system.tidalsteps)+'\n')
        file.write(',nonlinear options,'+self.system.nonlinear+'\n')
        file.write(',nonlinear error(%),'+str(self.system.nlerror)+'\n')
        file.write(',Deposition option:,'+str(self.system.depoption)+'\n')
        file.write(',Steps in deposition grid,'+str(self.system.depgrid)+'\n')
        file.write(',Oscillation output options,'+str(self.system.averageoption)+'\n')

        file.write('\n\n')

        file.write('Overlying Water Column Properties,')
        if self.system.topBCtype == 'Finite mixing water column':   file.write('Involved\n')
        else:                                                       file.write('Not applicable\n')
        file.write(',Inflow rate (m^3/s),'+str(self.system.taucoefs['Q'])+'\n')
        file.write(',Water body volume (m^3),'+str(self.system.taucoefs['V'])+'\n')
        file.write(',Water body depth (m),'+str(self.system.taucoefs['h'])+'\n')
        file.write(',Water evaporation rate (m^3/s),'+str(self.system.taucoefs['Qevap'])+'\n')
        file.write(',Water body DOC concentration (mg/L),'+str(self.system.taucoefs['DOC']) + '\n')
        file.write(',,')
        for chemical in self.system.chemicals:
            file.write(chemical.name + ',')
        file.write('\n')
        file.write(',Contaminant decay ('+timeunit+'),')
        for chemical in self.system.chemicals:
            file.write(str(self.system.BCs[chemical.name].kdecay) + ',')
        file.write('\n')
        file.write(',Contaminant evaporation ('+ lengthunit+ '/'+ timeunit + '),')
        for chemical in self.system.chemicals:
            file.write(str(self.system.BCs[chemical.name].kevap)+ ',')
        file.write('\n')


def get_summary(system, database, materials):
    """Takes the system, shows the summary and allows user to modify."""

    root = CapSimWindow(buttons = 3)
    root.make_window(Summary(root, system, database, materials))
    root.mainloop()

    if root.main.get() == 0:
        check = 1
        try:
            pickle.dump(root.window.system, open(Filepath + '/temp_test_file.cpsm', 'w'))
        except:
            check = 0

        if check == 1:
            pickle.dump(root.window.system, open(Filepath + '/input_cpsm_files/%s.cpsm' %system.cpsmfilename, 'w'))
            if root.window.system.csvfileoption == 'csv file':  root.window.make_csv_file(Filepath)

        else:
            report_check = 0

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.chemicals, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to chemical properties in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.matrices, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to material properties in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.sorptions, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to sorption properties in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.layers, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to layer properties in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.reactions, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to reaction properties in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.coefficients, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to reaction coefficients in saving your input file. Please re-try it.')

            if report_check == 0:
                try:
                    pickle.dump(root.window.system.ICs, open(Filepath + '/temp_test_file.cpsm', 'w'))
                    pickle.dump(root.window.system.BCs, open(Filepath + '/temp_test_file.cpsm', 'w'))
                    pickle.dump(root.window.system.SolidICs, open(Filepath + '/temp_test_file.cpsm', 'w'))
                except:
                    report_check = 1
                    tkmb.showwarning('Administrator Error', 'It appears you have a problem related to auxiliary conditions in saving your input file. Please re-try it.')

            if report_check == 0:
                tkmb.showwarning('Administrator Error', 'It appears you have a problem related to system parameters or solver options in saving your input file. Please re-try it.')

        if check == 0:   system = None

    else: system = None

    root.destroy()

    return system
