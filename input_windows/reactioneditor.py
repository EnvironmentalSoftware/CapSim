#! /usr/bin/env python
#
#This file is used to make the GUI to add reaction information to the system

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow

import tkFont

class ReactionEditor:
    """Gets the chemical reaction information for each layer."""

    def __init__(self, master, system, reaction, editflag):
        """Constructor method.  Makes the GUI using the list of "Layer" objects
        "layers." """

        # Read the Tkinter information
        self.master     = master
        self.fonttype   = system.fonttype
        self.formulatype= system.formulatype
        self.version    = system.version
        self.superfont  = get_superfont(self.fonttype)
        self.subfont    = get_superfont(self.formulatype)
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.bgcolor    = self.frame.cget('bg')
        self.top        = None
        
        self.system     = system

        # Read the system information
        self.chemicals  = system.chemicals
        self.reaction   = reaction
        self.editflag   = editflag

        # Define the reaction chemical information
        self.chemical_list = [chemical.name     for chemical in self.chemicals]
        self.formula_list  = [chemical.formula  for chemical in self.chemicals]
        self.MW_list       = [chemical.MW       for chemical in self.chemicals]

        self.models     = ['Fundamental', 'User-defined']

        self.name       = StringVar(value = 'Reaction ' + str(reaction.number))
        self.model      = StringVar(value = self.models[0])
        self.reactants  = []
        self.products   = []
               
        #self.stoichcoef = reaction.stoichcoef
        if editflag == 1:
            
            self.name      = StringVar( value = reaction.name)
            self.model     = StringVar( value = reaction.model)
            self.reactants = [reactant.copy() for reactant in reaction.reactants]
            self.products  = [product.copy()  for product  in reaction.products]

            for reactant in self.reactants:
                reactant.coef       = DoubleVar(value = reactant.coef)
                reactant.index      = DoubleVar(value = reactant.index)
                reactant.name       = StringVar(value = reactant.name)
                reactant.formula    = StringVar(value = reactant.formula)
                reactant.MW         = DoubleVar(value = reactant.MW)

            for product in self.products:
                product.coef       = DoubleVar(value = product.coef)
                product.name       = StringVar(value = product.name)
                product.formula    = StringVar(value = product.formula)
                product.MW         = DoubleVar(value = product.MW)

        self.cancelflag = 0

    def make_widgets(self):
        
        self.instructions       = Label(self.frame,  text  = 'Please input the following information for the added kinetic process:        ')

        self.reactblankcolumn   = Label(self.frame,  text  = ' ', width = 2)
        self.reactdelcolumn     = Label(self.frame,  text  = ' ', width = 6)
        self.reactcoefcolumn    = Label(self.frame,  text  = ' ', width = 6)
        self.reactnamecolumn    = Label(self.frame,  text  = ' ', width = 20)
        self.reactformcolumn    = Label(self.frame,  text  = ' ', width = 10)
        self.middlecolumn       = Label(self.frame,  text  = ' ', width = 14)
        self.proddelcolumn      = Label(self.frame,  text  = ' ', width = 6)
        self.prodcoefcolumn     = Label(self.frame,  text  = ' ', width = 6)
        self.prodnamecolumn     = Label(self.frame,  text  = ' ', width = 20)
        self.prodformcolumn     = Label(self.frame,  text  = ' ', width = 10)
        self.prodblankcolumn    = Label(self.frame,  text  = ' ', width = 2)

        self.nameblank          = Label(self.frame,  text  = ' ', width = 10)
        self.namelabel          = Label(self.frame,  text  = 'Name:', width = 10)
        self.namewidget         = Entry(self.frame,  textvariable  = self.name, width = 15)

        self.modellabel         = Label(self.frame,  text  = 'Kinetic model:', width = 10)
        self.modelwidget        = OptionMenu(self.frame,  self.model, *self.models, command = self.click_model)

        self.ratelabel          = Label(self.frame,  text  = 'Rate equation:', width = 10)

        self.reactlabel         = Label(self.frame,  text  = 'Reactants')
        self.prodlabel          = Label(self.frame,  text  = 'Products')
       
        self.reactcoeflabel     = Label(self.frame,  text  = 'Stoichiometric\ncoefficient')
        self.reactnamelabel     = Label(self.frame,  text  = 'Chemical')
        self.reactformlabel     = Label(self.frame,  text  = 'Formula')
        self.prodcoeflabel      = Label(self.frame,  text  = 'Stoichiometric\ncoefficient')
        self.prodnamelabel      = Label(self.frame,  text  = 'Chemical')
        self.prodformlabel      = Label(self.frame,  text  = 'Formula')

        self.addreactwidget     = Button(self.frame, text  = 'Add reactant', width = 20, command = self.addreactant)
        self.addprodwidget      = Button(self.frame, text  = 'Add product',  width = 20, command = self.addproduct)
        self.okbutton           = Button(self.frame, text  = 'OK',           width = 20, command = self.OK)
        self.cancelbutton       = Button(self.frame, text  = 'Cancel',       width = 20, command = self.Cancel)
        self.blank1             = Label (self.frame, text  = ' ')
        self.blank2             = Label (self.frame, text  = ' ')

        self.instructions.grid(     row = 0, column = 0,  padx = 8, sticky = 'W',  columnspan = 11)
        
        self.nameblank.grid(        row = 1, column = 0,  padx = 2, sticky = 'WE', columnspan = 4)
        
        self.namelabel.grid(        row = 2, column = 0,  padx = 2, sticky = 'E',  columnspan = 3)
        self.namewidget.grid(       row = 2, column = 3,  padx = 2, sticky = 'W' )
        
        self.modellabel.grid(       row = 2, column = 4,  padx = 2, sticky = 'E')
        self.modelwidget.grid(      row = 2, column = 5,  padx = 2, sticky = 'W',  columnspan = 2)

        self.ratelabel.grid(        row = 2, column = 7,  padx = 2, sticky = 'E')
        
        self.reactblankcolumn.grid( row = 3, column = 0 , padx = 2, sticky = 'WE')
        self.reactdelcolumn.grid(   row = 3, column = 1 , padx = 2, sticky = 'WE')        
        self.reactcoefcolumn.grid(  row = 3, column = 2 , padx = 2, sticky = 'WE')
        self.reactnamecolumn.grid(  row = 3, column = 3 , padx = 2, sticky = 'WE')
        self.reactformcolumn.grid(  row = 3, column = 4 , padx = 2, sticky = 'WE')
        self.middlecolumn.grid(     row = 3, column = 5 , padx = 2, sticky = 'WE')
        self.proddelcolumn.grid(    row = 3, column = 6 , padx = 2, sticky = 'WE')
        self.prodcoefcolumn.grid(   row = 3, column = 7 , padx = 2, sticky = 'WE')
        self.prodnamecolumn.grid(   row = 3, column = 8 , padx = 2, sticky = 'WE')
        self.prodformcolumn.grid(   row = 3, column = 9 , padx = 2, sticky = 'WE')
        self.prodblankcolumn.grid(  row = 3, column = 10, padx = 2, sticky = 'WE')

        self.reactlabel.grid(       row = 4, column = 2 , padx = 2, sticky = 'WE', columnspan = 3)
        self.prodlabel.grid(        row = 4, column = 7 , padx = 2, sticky = 'WE', columnspan = 3)

        self.reactcoeflabel.grid(   row = 5, column = 2 , padx = 2, sticky = 'WE')
        self.reactnamelabel.grid(   row = 5, column = 3 , padx = 2, sticky = 'WE')
        self.reactformlabel.grid(   row = 5, column = 4 , padx = 2, sticky = 'WE')
        
        self.prodcoeflabel.grid(    row = 5, column = 7 , padx = 2, sticky = 'WE')
        self.prodnamelabel.grid(    row = 5, column = 8 , padx = 2, sticky = 'WE')
        self.prodformlabel.grid(    row = 5, column = 9 , padx = 2, sticky = 'WE')
        

        self.updatereaction()
        
        # Build a frame for Reaction rate
        
        self.focusbutton = None
        
    def click_model(self, event = None):

        check = 0
        reactant_list = [reactant.name.get() for reactant in self.reactants]
        for name in reactant_list:
            if reactant_list.count(name) > 1:
                check = 1
            
        if len(self.reactants) == 0:
            tkmb.showerror(title = self.system.version, message = 'Please firstly input the information of reactants.')
            self.model.set('Fundamental')
            self.focusbutton     = self.okbutton
            self.master.tk.lift()
            
        elif check == 1:
            tkmb.showerror(title = self.system.version, message = 'At least one chemical is replicated in the reactant list, please check')
            self.model.set('Fundamental')
            self.focusbutton     = self.okbutton
            self.master.tk.lift()

        else:
            if self.model.get() == 'User-defined':
                
                if self.top is None:
                    self.top = CapSimWindow(master = self.master, buttons = 2)
                    self.top.make_window(UserDefined(self.top, self.system, self.reactants))
                    self.top.tk.mainloop()
                    
                    if self.top is not None:
                        self.top.destroy()
                        self.top = None
                                                           
                elif self.top is not None:
                    tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
                    self.top.tk.focus()
        
            self.updaterateequation()
        
    def updaterateequation(self):

        try:    self.ratewidget.grid_forget()
        except: pass

        font      = tkFont.Font(font = self.formulatype)
        subfont   = tkFont.Font(font = self.subfont)
        superfont = tkFont.Font(font = self.superfont)

        if self.model.get() == 'Fundamental':

            rate_len  = font.measure(u'r = \u03BB')
            for reactant in self.reactants:
                rate_len = rate_len + font.measure('C')
                rate_len = rate_len + subfont.measure(reactant.formula.get())
                if reactant.coef.get() == int(reactant.coef.get()): coef = int(reactant.coef.get())
                else:                                               coef = reactant.coef.get()
                if coef <> 1.:  rate_len = rate_len + superfont.measure(str(coef)+' ')
            self.ratewidget  = Text(self.frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
            self.ratewidget.insert('end', u'r = \u03BB')
            for reactant in self.reactants:
                self.ratewidget.insert('end', 'C')
                self.ratewidget.insert('end', reactant.formula.get(), 'sub')
                if reactant.coef.get() == int(reactant.coef.get()): coef = int(reactant.coef.get())
                else:                                               coef = reactant.coef.get()
                if coef <> 1.:   self.ratewidget.insert('end', str(coef)+' ', 'super')


        if self.model.get() == 'User-defined':

            rate_len  = font.measure(u'r = \u03BB')
            for reactant in self.reactants:
                if reactant.index.get() <> 0:
                    rate_len = rate_len + font.measure('C')
                    rate_len = rate_len + subfont.measure(reactant.formula.get())
                    if reactant.index.get() == int(reactant.index.get()): index = int(reactant.index.get())
                    else:                                                 index = reactant.index.get()
                    if index <> 1.:   rate_len = rate_len + superfont.measure(str(index)+' ')

            self.ratewidget  = Text(self.frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font = self.formulatype)
            self.ratewidget.insert('end', u'r = \u03BB')
            for reactant in self.reactants:
                if reactant.index.get() <> 0:
                    self.ratewidget.insert('end', 'C')
                    self.ratewidget.insert('end', reactant.formula.get(), 'sub')
                    if reactant.index.get() == int(reactant.index.get()): index = int(reactant.index.get())
                    else:                                                 index = reactant.index.get()
                    if index <> 1.:   self.ratewidget.insert('end', str(index) + ' ', 'super')

        self.ratewidget.tag_config('sub', offset = -4, font = self.subfont)
        self.ratewidget.tag_config('super', offset = 5, font = self.superfont)
        self.ratewidget.tag_config('right', justify = 'right')
        self.ratewidget.config(state = 'disabled', background = self.bgcolor, borderwidth = 0, spacing3 = 3)

        self.ratewidget.grid(        row = 2, column = 8,  padx = 2, sticky = 'W', columnspan = 3)

    def updatereaction(self):

        try:
            self.addreactwidget.grid_forget()
            self.addprodwidget.grid_forget()
            self.okbutton.grid_forget()
            self.cancelbutton.grid_forget()
        except: pass

        self.updaterateequation()
        
        row = 6

        for reactant in self.reactants:
            try: reactant.remove_propertieswidgets()
            except: pass
            reactant.propertieswidgets(self.frame, row, self.master, self.chemical_list, self.formula_list, self.MW_list)
            row = row + 1

        row_reactant = row
        
        row = 6
        
        for product in self.products:
            try: product.remove_propertieswidgets()
            except: pass
            product.propertieswidgets(self.frame, row, self.master, self.chemical_list, self.formula_list, self.MW_list)
            row = row + 1
            
        if row < row_reactant: row = row_reactant
        
        self.blank1.grid(        row = row)
        row = row + 1
        self.addreactwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.addprodwidget.grid( row = row, columnspan = 11)
        row = row + 1
        self.okbutton.grid(      row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(  row = row, columnspan = 11)
        row = row + 1
        self.blank2.grid(        row = row)
        
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        self.master.geometry()
        
    def addreactant(self):

        self.reactants.append(Reactant(len(self.reactants)+ 1))

        self.reactants[-1].coef     = DoubleVar(value = 1)
        self.reactants[-1].name     = StringVar(value = self.chemical_list[0])
        self.reactants[-1].formula  = StringVar(value = self.formula_list[0])
        self.reactants[-1].index    = DoubleVar(value = 1)
        self.reactants[-1].MW       = DoubleVar(value = self.MW_list[0])

        self.updatereaction()
        
    def addproduct(self):

        self.products.append(Product(len(self.products)+ 1))

        self.products[-1].coef     = DoubleVar(value = 1)
        self.products[-1].name     = StringVar(value = self.chemical_list[0])
        self.products[-1].formula  = StringVar(value = self.formula_list[0])
        self.products[-1].MW       = StringVar(value = self.MW_list[0])

        self.updatereaction()

    def delreactant(self, number):

        self.reactants[number - 1].remove_propertieswidgets()
        self.reactants.remove(self.reactants[number - 1])

        self.updatereaction()
        
    def delproduct(self, number):

        self.products[number - 1].remove_propertieswidgets()
        self.products.remove(self.products[number - 1])

        self.updatereaction()
        
    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        if self.model.get() == 'Fundamental':
            for reactant in self.reactants:
                reactant.index.set(reactant.coef.get())
        
        check = 0
        
        chemicals = []
        for reactant in self.reactants: chemicals.append(reactant.name.get())
        for product in self.products:   chemicals.append(product.name.get())

        for chemical in chemicals:
            if chemicals.count(chemical) > 1:
                check = 1
        
        if self.master.window.top is not None: self.master.open_toplevel()
        elif check == 1: self.reaction_error()
        else:
            for reactant in self.reactants:
                reactant.get_reactant()
                reactant.remove_propertieswidgets()

            for product in self.products:
                product.get_product()
                product.remove_propertieswidgets()

            if (len(self.reactants)+len(self.products)) == 0: self.cancelflag = 1
            self.master.tk.quit()
            
    def reaction_error(self):

        tkmb.showerror(title = self.version, message = 'At least one chemical has been replicated in the reaction!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Cancel(self):
        
        try:
            self.reactants = self.reaction.reactants
            self.products  = self.reaction.products
            
        except:

            self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
       
class Reactant:

    def __init__(self, number):

        self.number   = number
        self.soluable = 1

        
    def copy(self):

        reactant = Reactant(self.number)

        reactant.coef     = self.coef
        reactant.index    = self.index
        reactant.name     = self.name
        reactant.formula  = self.formula
        reactant.MW       = self.MW
        reactant.soluable = self.soluable

        return reactant

    def propertieswidgets(self, frame, row, master, chemical_list, formula_list, MW_list):

        self.master = master
        
        self.chemical_list  = chemical_list
        self.formula_list   = formula_list
        self.MW_list        = MW_list


        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_reactant)
        self.namewidget     = OptionMenu(frame, self.name, *chemical_list, command = self.click_name)
        self.coefwidget     = Entry (frame, width = 8,  justify = 'center', textvariable = self.coef)
        self.fwidget        = Entry( frame, width = 8,  justify = 'center', textvariable = self.formula, font = 'Calibri 11')
        self.middlelabel    = Label( frame, width = 8,  justify = 'center', text = ' || ')

        self.delwidget.grid(     row  = row, column = 1, padx = 2 ,pady = 1)
        self.coefwidget.grid(    row  = row, column = 2, padx = 2 ,pady = 1)
        self.namewidget.grid(    row  = row, column = 3, padx = 2, pady = 1, sticky = 'WE')
        self.fwidget.grid(       row  = row, column = 4, padx = 2, pady = 1, sticky = 'WE')
        self.middlelabel.grid(   row  = row, column = 5, padx = 2, pady = 1, sticky = 'WE')           

    def click_name(self, event = None):
        
        self.formula.set(self.formula_list[self.chemical_list.index(self.name.get())])
        self.MW.set(self.MW_list[self.chemical_list.index(self.name.get())])

        self.master.window.updaterateequation()
        
    def del_reactant(self):
        
        self.master.window.delreactant(self.number)

    def get_reactant(self):
        
        self.coef       = self.coef.get()
        self.name       = self.name.get()
        self.formula    = self.formula.get()
        self.MW         = self.MW.get()
        self.index      = self.index.get()

    def indexwidgets(self, frame, row):

        self.label =  Label(frame, text = self.name.get())
        self.widget = Entry(frame, textvariable = self.index, width = 6, justify = 'center')

        self.label.grid( row = row, column = 0, padx = 6, pady = 2)
        self.widget.grid(row = row, column = 1, padx = 6, pady = 2)
        
    def remove_indexwidgets(self):
        
        self.label.grid_forget()
        self.widget.grid_forget()

        self.label = 0
        self.widget = 0
    
    def remove_propertieswidgets(self):

        self.delwidget.grid_forget()
        self.namewidget.grid_forget()
        self.coefwidget.grid_forget()
        self.fwidget.grid_forget()
        self.middlelabel.grid_forget()
        try:
            self.label.grid_forget()
            self.widget.grid_forget()
        except: pass
        
        self.master = 0 
        self.delwidget  = 0
        self.namewidget = 0
        self.coefwidget = 0
        self.fwidget    = 0
        self.middlelabel= 0

        self.label      = 0
        self.widget     = 0
        
    def get_dynamic_sorption(self, chemical, index):

        self.coef     = 1
        self.index    = index
        self.name     = chemical.name
        self.formula  = ''
        self.MW       = chemical.MW
        self.soluable = 1

    def get_dynamic_desorption(self, chemical, index):

        self.coef     = 1
        self.index    = index
        self.name     = chemical.name
        self.formula  = ''
        self.MW       = chemical.MW
        self.soluable = 0

class Product:

    def __init__(self, number):

        self.number   = number
        self.soluable = 1

    def copy(self):

        product = Product(self.number)

        product.coef    = self.coef
        product.MW      = self.MW
        product.name    = self.name
        product.formula = self.formula
        product.soluable = self.soluable

        return product
        
    def propertieswidgets(self, frame, row, master, chemical_list, formula_list, MW_list):

        self.master         = master
        
        self.chemical_list  = chemical_list
        self.formula_list   = formula_list
        self.MW_list        = MW_list

        self.middlelabel    = Label( frame, width = 8,  justify = 'center', text = ' || ')
        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_product)
        self.namewidget     = OptionMenu(frame, self.name, *chemical_list, command = self.click_name)
        self.coefwidget     = Entry (frame, width = 8,  justify = 'center', textvariable = self.coef)
        self.fwidget        = Entry( frame, width = 8,  justify = 'center', textvariable = self.formula, font = 'Calibri 11')

        self.middlelabel.grid(   row  = row, column = 5, padx = 2, pady = 1, sticky = 'WE')
        self.delwidget.grid(     row  = row, column = 6, padx = 2 ,pady = 1)
        self.coefwidget.grid(    row  = row, column = 7, padx = 2 ,pady = 1)
        self.namewidget.grid(    row  = row, column = 8, padx = 2, pady = 1, sticky = 'WE')
        self.fwidget.grid(       row  = row, column = 9, padx = 2, pady = 1, sticky = 'WE')
        
    def click_name(self, event = None):
        
        self.formula.set(self.formula_list[self.chemical_list.index(self.name.get())])
        self.MW.set(self.MW_list[self.chemical_list.index(self.name.get())])

    def del_product(self):
        
        self.master.window.delproduct(self.number)

    def get_product(self):
        
        self.coef       = self.coef.get()
        self.name       = self.name.get()
        self.formula    = self.formula.get()
        self.MW         = self.MW.get()

    def remove_propertieswidgets(self):
            
        self.master = 0 
        self.delwidget.grid_forget()
        self.namewidget.grid_forget()
        self.coefwidget.grid_forget()
        self.fwidget.grid_forget()
        self.middlelabel.grid_forget()
        
        self.delwidget  = 0
        self.namewidget = 0
        self.coefwidget = 0
        self.fwidget    = 0
        self.middlelabel= 0

    def get_dynamic_sorption(self, chemical):

        self.coef     = 1
        self.index    = 1
        self.MW       = chemical.MW
        self.name     = chemical.name
        self.formula  = ''
        self.soluable = 0

    def get_dynamic_desorption(self, chemical):

        self.coef     = 1
        self.index    = 1
        self.name     = chemical.name
        self.formula  = ''
        self.MW       = chemical.MW
        self.soluable = 1


class UserDefined:

    def __init__(self, master, system, reactants):
        """Constructor method.  Makes the GUI using the list of "Layer" objects
        "layers." """

        self.master     = master
        self.fonttype   = system.fonttype
        self.version    = system.version
        self.superfont  = get_superfont(self.fonttype)
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.bgcolor    = self.frame.cget('bg')
        self.top        = None

        
        self.reactants     = reactants
         
    def make_widgets(self):
        
        self.instructions = Label(self.frame, text = ' Please input the rate index of each chemical in the reaction kinetic equation               ')
        self.label        = Label(self.frame, text = 'Reactants')
        self.widget       = Label(self.frame, text = 'Rate index')
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')
        self.blank3       = Label(self.frame, text = ' ', width = 2)
        self.blank4       = Label(self.frame, text = ' ', width = 2)

        self.okbutton    = Button(self.frame, text = 'OK', width = 20, command = self.OK)

        self.instructions.grid(row = 0, column = 0, columnspan = 2)
        self.blank1.grid(      row = 1, column = 0, columnspan = 2)
        self.label.grid(       row = 2, column = 0, padx = 4, pady = 2)
        self.widget.grid(      row = 2, column = 1, padx = 4, pady = 2)

        row = 3
        for reactant in self.reactants:
            try: reactant.remove_indexwidgets()
            except: pass
            reactant.indexwidgets(self.frame, row)
            row = row + 1
                    
        self.blank2.grid(      row = row, column = 0, columnspan = 2)
        row = row + 1
        self.okbutton.grid(    row = row, columnspan = 2)

        self.focusbutton = self.okbutton

    def OK(self, event = None):

        self.master.tk.quit()

    
class ReactionDeleter:
    """Gets the chemical reaction information for each layer."""

    def __init__(self, master, system, reaction):
        """Constructor method.  Makes the GUI using the list of "Layer" objects
        "layers." """

        self.master     = master
        self.fonttype   = system.fonttype
        self.version    = system.version
        self.superfont  = get_superfont(self.fonttype)
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.bgcolor    = self.frame.cget('bg')
        self.top        = None
                                        
        self.number     = reaction.number        
        self.name       = reaction.name
        self.equation   = reaction.equation
        
        self.cancelflag = 0
        
    def make_widgets(self):

        self.instructions = Label(self.frame, text = ' Are you sure to delete the following reaction?                   ')

        self.blankcolumn    = Label(self.frame,  text = ' ',  width = 1 )
        self.numbercolumn   = Label(self.frame,  text = ' ',  width = 5 )
        self.namecolumn     = Label(self.frame,  text = ' ',  width = 15)
        self.equationcolumn = Label(self.frame,  text = ' ',  width = 50)

        self.numberlabel    = Label(self.frame,  text = 'Number')
        self.namelabel      = Label(self.frame,  text = 'Name')
        self.equationlabel  = Label(self.frame,  text = 'Chemical equation')

        self.numberwidget   = Label(self.frame,  text = self.number)     
        self.namewidget     = Label(self.frame,  text = self.name  )     
        self.equationwidget = Label(self.frame,  text = self.equation, font = 'Calibri 11')

        self.instructions.grid(     row    = 0, column = 1, sticky = 'WE', padx = 1, pady = 1, columnspan = 4)

        self.blankcolumn.grid(      row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.numbercolumn.grid(     row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(       row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.equationcolumn.grid(   row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)

        self.numberlabel.grid(      row    = 2, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.namelabel.grid(        row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.equationlabel.grid(    row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)

        self.numberwidget.grid(     row    = 3, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.namewidget.grid(       row    = 3, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.equationwidget.grid(   row    = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)

        self.deletebutton = Button(self.frame, text = 'Delete', width = 20, command = self.Delete)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label( self.frame, text = ' ')
        self.blank2       = Label( self.frame, text = ' ')

        self.blank1.grid(           row    = 4                )
        self.deletebutton.grid(     row    = 5, columnspan = 4)
        self.cancelbutton.grid(     row    = 6, columnspan = 4)
        self.blank2.grid(           row    = 7                )
        
        self.deletebutton.bind('<Return>', self.Delete)
        self.focusbutton = self.deletebutton

    def Delete(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
        
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def Cancel(self):
        
        self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

        
        
