#! /usr/bin/env python
#
#This file is used to make the GUI to add reaction information to the system

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow

import tkFont

class CoefficientEditor:
    """Gets the chemical reaction information for each layer."""

    def __init__(self, master, system, coefficient, coefficients, editflag):
        """Constructor method.  Makes the GUI using the list of "Layer" objects
        "layers." """

        # Read the Tkinter information
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

        self.concunit       = system.concunit
        self.timeunit       = system.timeunit

        self.concunits      = system.concunits

        # Convert mass concentration units to corresponding molar concentration units
        if self.concunit == system.concunits[0]:    self.concunit = system.concunits[3]
        if self.concunit == system.concunits[1]:    self.concunit = system.concunits[4]
        if self.concunit == system.concunits[2]:    self.concunit = system.concunits[5]

        # Read the system information
        self.coefficient  = coefficient
        self.coefficients = coefficients
        self.layers       = system.layers
        self.editflag     = editflag
                
        if self.editflag == 0:
            
            self.layer_full_list    = []
            self.reaction_full_list = []
            for layer in system.layers:
                self.layer_full_list.append(layer.name)
            for reaction in system.reactions:
                self.reaction_full_list.append(reaction.name)
                
            self.layer_list    = []
            self.reaction_list = []
            
            for layer in system.layers:
                coef_check         = 0
                for reaction in system.reactions:
                    if coefficients[layer.name][reaction.name].lam == 0:
                        coef_check = 1
                if coef_check == 1:
                    self.layer_list.append(layer.name)
                    self.reaction_list.append([])
                    for reaction in system.reactions:
                        if coefficients[layer.name][reaction.name].lam == 0:
                            self.reaction_list[-1].append(reaction.name)

            self.layer      = StringVar(value = self.layer_list[0])
            self.reaction   = StringVar(value = self.reaction_list[0][0])
            self.equation   = StringVar(value = '')

        else:
            self.layer      = coefficient.layer.name
            self.reaction   = coefficient.reaction.name
            self.equation   = coefficient.reaction.equation
            self.reactants  = coefficient.reaction.reactants

        self.lam     = DoubleVar(value = coefficient.lam)

        self.cancelflag = 0

    def make_widgets(self):
        
        self.instructions       = Label(self.frame,  text  = 'Please input the following information for the added kinetic process:        ')

        self.blankcolumn        = Label(self.frame,  text  = ' ', width = 2)
        self.layercolumn        = Label(self.frame,  text = ' ',  width = 15 )
        self.namecolumn         = Label(self.frame,  text = ' ',  width = 15 )
        self.equationcolumn     = Label(self.frame,  text = ' ',  width = 20 )
        self.ratecolumn         = Label(self.frame,  text = ' ',  width = 10 )
        self.coef1column        = Label(self.frame,  text = ' ',  width = 10 )
        self.unit1column        = Label(self.frame,  text = ' ',  width = 3 )
        self.endcolumn          = Label(self.frame,  text = ' ',  width = 2 )


        self.layerlabel         = Label(self.frame,  text = 'Layer')
        self.namelabel          = Label(self.frame,  text = 'Reaction')
        self.equationlabel      = Label(self.frame,  text = 'Chemical equation')
        self.ratelabel          = Label(self.frame,  text = 'Rate equation')
        self.lamcoeflabel       = Label(self.frame,  text = 'Coefficient  ' + u'\u03BB')

        self.blank1             = Label (self.frame, text  = ' ')

        self.instructions.grid(     row = 0, column = 0,  padx = 8, sticky = 'W',  columnspan = 11)
        
        self.blankcolumn.grid(      row = 1, column = 0 , padx = 2, sticky = 'WE')
        self.layercolumn.grid(      row = 1, column = 1 , padx = 2, sticky = 'WE')        
        self.namecolumn.grid(       row = 1, column = 2 , padx = 2, sticky = 'WE')
        self.equationcolumn.grid(   row = 1, column = 3 , padx = 2, sticky = 'WE')
        self.ratecolumn.grid(       row = 1, column = 4 , padx = 2, sticky = 'WE')
        self.coef1column.grid(      row = 1, column = 5 , padx = 2, sticky = 'WE')
        self.unit1column.grid(      row = 1, column = 6 , padx = 2, sticky = 'WE')
        self.endcolumn.grid(        row = 1, column = 7 , padx = 2, sticky = 'WE')

        self.layerlabel.grid(       row = 2, column = 1 , padx = 2, sticky = 'WE')        
        self.namelabel.grid(        row = 2, column = 2 , padx = 2, sticky = 'WE')
        self.equationlabel.grid(    row = 2, column = 3 , padx = 2, sticky = 'WE')
        self.ratelabel.grid(        row = 2, column = 4 , padx = 2, sticky = 'WE')

        self.blank1.grid(           row = 3, column = 0 , padx = 2, sticky = 'WE', columnspan = 11)

        if self.editflag == 1:
            
            self.layerwidget    = Label(self.frame, text = self.layer)
            self.namewidget     = Label(self.frame, text = self.reaction)
            self.equationwidget = Label(self.frame, text = self.equation, font = self.formulatype)
            
            self.layerwidget.grid(      row = 4, column = 1 , padx = 2)
            self.namewidget.grid(       row = 4, column = 2 , padx = 2)
            self.equationwidget.grid(   row = 4, column = 3 , padx = 10)


            if self.coefficient.reaction.model == 'User-defined' or self.coefficient.reaction.model == 'Fundamental':
                
                unitindex       = 0

                tkfont      = tkFont.Font(font = self.formulatype)
                tksubfont   = tkFont.Font(font = self.subfont)
                tksuperfont = tkFont.Font(font = self.superfont)

                # Measure the width of rate and lambda expression
                rate_len  = tkfont.measure(u'r = \u03BB')
                rate_len  = rate_len + tksubfont.measure(str(self.coefficient.reaction.number)+ ',')
                if self.coefficient.layer.number == 0: rate_len  = rate_len + tksubfont.measure('D')
                else:                                  rate_len  = rate_len + tksubfont.measure(str(self.coefficient.layer.number))
                for reactant in self.coefficient.reaction.reactants:
                    if reactant.index <> 0:
                        rate_len = rate_len + tkfont.measure('C')
                        rate_len = rate_len + tksubfont.measure(reactant.formula)
                        if reactant.index == int(reactant.index):             index = int(reactant.index)
                        else:                                                 index = reactant.index

                        if index <> 1.: rate_len = rate_len + tksuperfont.measure(str(index) + ' ')
                        unitindex = unitindex + reactant.index
                print(unitindex)
                lam_len   = tkfont.measure('')
                if unitindex == int(unitindex): unitindex = int(unitindex)
                print(unitindex)
                if (unitindex - 1) != 0:
                    if (unitindex - 1) != -1:
                        lam_len  = lam_len + tkfont.measure('('+self.concunit+')')
                        lam_len  = lam_len + tksuperfont.measure(str(-(unitindex - 1)))
                    else:
                        lam_len  = lam_len + tkfont.measure(self.concunit + ' ')
                lam_len  = lam_len + tkfont.measure(self.timeunit)
                lam_len  = lam_len + tksuperfont.measure('-1')
                
                self.ratewidget  = Text(self.frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
                self.ratewidget.insert('end', u'r')
                self.ratewidget.insert('end', ' = ')
                self.ratewidget.insert('end', u'\u03BB')
                self.ratewidget.insert('end', str(self.coefficient.reaction.number) + ',', 'sub')
                if self.coefficient.layer.number == 0: self.ratewidget.insert('end', 'D', 'sub')
                else:                                  self.ratewidget.insert('end', str(self.coefficient.layer.number), 'sub')
                for reactant in self.coefficient.reaction.reactants:
                    if reactant.index <> 0:
                        self.ratewidget.insert('end', 'C')
                        self.ratewidget.insert('end', reactant.formula, 'sub')
                        if reactant.index == int(reactant.index): index = int(reactant.index)
                        else:                                     index = reactant.index
                        if index <> 1.:             self.ratewidget.insert('end', str(index) + ' ', 'super')

                self.ratewidget.tag_config('sub', offset = -4, font = self.subfont)
                self.ratewidget.tag_config('super', offset = 5, font = self.superfont)
                self.ratewidget.tag_config('right', justify = 'right')
                self.ratewidget.config(state = 'disabled', background = self.bgcolor, borderwidth = 0, spacing3 = 3)

                self.lamcoefwidget     = Entry(self.frame, textvariable = self.lam, justify = 'center', width = 8)

                self.lamunitlabel  = Text(self.frame, width = int(lam_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
                if (unitindex - 1) != 0:
                    if (unitindex - 1) != -1:
                        self.lamunitlabel.insert('end', '(' + self.concunit +')')
                        self.lamunitlabel.insert('end', str(-(unitindex - 1)), 'super')
                    else:
                        self.lamunitlabel.insert('end', self.concunit + ' ')
                self.lamunitlabel.insert('end', self.timeunit)
                self.lamunitlabel.insert('end', '-1', 'super')
                self.lamunitlabel.tag_config('sub', offset = -4, font = self.subfont)
                self.lamunitlabel.tag_config('super', offset = 5, font = self.superfont)
                self.lamunitlabel.tag_config('right', justify = 'right')
                self.lamunitlabel.config(state = 'disabled', background = self.bgcolor, borderwidth = 0, spacing3 = 3)


                self.lamcoeflabel.grid(       row = 2, column = 5 , padx = 2, sticky = 'WE', columnspan = 4)
                
                self.ratewidget.grid(       row = 4, column = 4 , padx = 5)
                self.lamcoefwidget.grid(    row = 4, column = 5 , padx = 2, sticky = 'E')
                self.lamunitlabel.grid(     row = 4, column = 6 , padx = 2, sticky = 'W')

        else:
            self.layerwidget    = OptionMenu(self.frame, self.layer, *self.layer_list, command = self.click_layer)
            self.layerwidget.grid(       row = 4, column = 1 , padx = 2, sticky = 'WE')
            self.click_layer()
                            
        self.okbutton           = Button(self.frame, text  = 'OK',           width = 20, command = self.OK)
        self.cancelbutton       = Button(self.frame, text  = 'Cancel',       width = 20, command = self.Cancel)
        self.blank2             = Label (self.frame, text  = ' ')
        self.blank3             = Label (self.frame, text  = ' ')
        self.blank4             = Label (self.frame, text  = ' ')
        self.focusbutton = None

        self.blank3.grid(       row    = 5)
        self.okbutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank4.grid(       row    = 8)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton
        
    def click_layer(self, event = None):

        try: self.namewidget.grid_forget()
        except: pass
        
        self.reaction.set(self.reaction_list[self.layer_list.index(self.layer.get())][0])
        self.namewidget = OptionMenu(self.frame, self.reaction, *self.reaction_list[self.layer_list.index(self.layer.get())], command = self.click_reaction)
        self.namewidget.grid(       row = 4, column = 2 , padx = 2, sticky = 'WE')

        self.click_reaction()
        
    def click_reaction(self, event = None):
        
        try:
            self.equationwidget.grid_forget()
            self.ratewidget.grid_forget()
        except: pass
        
        try:
            self.lamcoeflabel.grid_forget()
            self.lamcoefwidget.grid_forget()
            self.lamunitlabel.grid_forget()
        except: pass

        coefficient = self.coefficients[self.layer.get()][self.reaction.get()]
        self.lam.set(coefficient.lam)

        self.equation = coefficient.reaction.equation
        self.equationwidget = Label(self.frame, text = self.equation, font=self.formulatype)
        self.equationwidget.grid(   row = 4, column = 3 , padx = 5)
        
        if coefficient.reaction.model == 'User-defined' or coefficient.reaction.model == 'Fundamental':
            
            unitindex       = 0

            tkfont      = tkFont.Font(font = self.formulatype)
            tksubfont   = tkFont.Font(font = self.subfont)
            tksuperfont = tkFont.Font(font = self.superfont)

            # Measure the width of rate and lambda expression
            rate_len  = tkfont.measure(u'r = \u03BB')
            rate_len  = rate_len + tksubfont.measure(str(coefficient.reaction.number)+ ',')
            if coefficient.layer.number == 0: rate_len  = rate_len + tksubfont.measure('D')
            else:                             rate_len  = rate_len + tksubfont.measure(str(coefficient.layer.number))
            for reactant in coefficient.reaction.reactants:
                if reactant.index <> 0:
                    rate_len = rate_len + tkfont.measure('C')
                    rate_len = rate_len + tksubfont.measure(reactant.formula)
                    if reactant.index == int(reactant.index): index = int(reactant.index)
                    else:                                     index = reactant.index

                    if index <> 1.: rate_len = rate_len + tksuperfont.measure(str(index) + ' ')
                    unitindex = unitindex + reactant.index

            lam_len   = tkfont.measure('')
            if unitindex == int(unitindex): unitindex = int(unitindex)
            if (unitindex - 1) != 0:
                if (unitindex - 1) != 1:
                    lam_len  = lam_len + tkfont.measure('('+self.concunit+')')
                    lam_len  = lam_len + tksuperfont.measure(str(-(unitindex - 1)))
                else:
                    lam_len  = lam_len + tkfont.measure(self.concunit)
            lam_len  = lam_len + tkfont.measure(self.timeunit)
            lam_len  = lam_len + tksuperfont.measure('-1')
            
            self.ratewidget  = Text(self.frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
            self.ratewidget.insert('end', u'r = \u03BB')
            self.ratewidget.insert('end', str(coefficient.reaction.number) + ',', 'sub')
            if coefficient.layer.number == 0: self.ratewidget.insert('end', 'D', 'sub')
            else:                             self.ratewidget.insert('end', str(coefficient.layer.number), 'sub')
            for reactant in coefficient.reaction.reactants:
                if reactant.index <> 0:
                    self.ratewidget.insert('end', 'C')
                    self.ratewidget.insert('end', reactant.formula, 'sub')
                    if reactant.index == int(reactant.index): index = int(reactant.index)
                    else:                                     index = reactant.index
                    if index <> 1.:    self.ratewidget.insert('end', str(index) + ' ', 'super')

            self.ratewidget.tag_config('sub', offset = -4, font = self.subfont)
            self.ratewidget.tag_config('super', offset = 5, font = self.superfont)
            self.ratewidget.tag_config('right', justify = 'right')
            self.ratewidget.config(state = 'disabled', background = self.bgcolor, borderwidth = 0, spacing3 = 3)

            self.lamcoefwidget     = Entry(self.frame, textvariable = self.lam, justify = 'center', width = 8)

            self.lamunitlabel  = Text(self.frame, width = int(lam_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
            if unitindex == int(unitindex): unitindex = int(unitindex)
            if (unitindex - 1) != 0:
                if (unitindex - 1) != 1:
                    self.lamunitlabel.insert('end', '(' + self.concunit +')')
                    self.lamunitlabel.insert('end', str(-(unitindex - 1)), 'super')
                else:
                    self.lamunitlabel.insert('end', self.concunit)
            self.lamunitlabel.insert('end', self.timeunit)
            self.lamunitlabel.insert('end', '-1', 'super')
            self.lamunitlabel.tag_config('sub', offset = -4, font = self.subfont)
            self.lamunitlabel.tag_config('super', offset = 5, font = self.superfont)
            self.lamunitlabel.tag_config('right', justify = 'right')
            self.lamunitlabel.config(state = 'disabled', background = self.bgcolor, borderwidth = 0, spacing3 = 3)
        
            self.lamcoeflabel.grid(     row = 2, column = 5 , padx = 2, sticky = 'WE', columnspan = 4)
            
            self.ratewidget.grid(       row = 4, column = 4 , padx = 5)
            self.lamcoefwidget.grid(    row = 4, column = 5 , padx = 2, sticky = 'E')
            self.lamunitlabel.grid(     row = 4, column = 6 , padx = 2, sticky = 'W')

        self.frame.update()
        self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        if self.editflag == 0:
            self.layerindex     = self.layer_full_list.index(self.layer.get())
            self.reactionnumber = self.reaction_full_list.index(self.reaction.get()) + 1
        
        if self.master.window.top is not None: self.master.open_toplevel()
        elif self.lam == 0: self.coefficient_error()
        else: self.master.tk.quit()
            
    def coefficient_error(self):

        tkmb.showerror(title = self.version, message = 'At least one chemical has been replicated in the reaction!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.reactants = self.reaction.reactants
            self.products  = self.reaction.products
            
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()


        
