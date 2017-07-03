#!/usr/bin/env python
#
#This file is used to make the GUI for inputing a new chemical into the database
#of compounds for CapSim.

import tkMessageBox as tkmb, cPickle as pickle, sys

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                StringVar, DoubleVar, IntVar, FLAT, RAISED
from capsim_object_types import CapSimWindow, ChemicalDatabase, ChemicalData
from capsim_functions    import get_superfont
from estimators          import Estimators

import tkFont

class DatabaseEditor:
    """Opens a window for inputing the properties of a compound."""

    def __init__(self, master, system, chemicaldata, chemicaldatas, editflag, tempflag):
        """The constructor method."""
        
        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.frame         = Frame(master.frame)
        self.tframe        = Frame(master.tframe)
        self.bframe        = Frame(master.bframe)
        self.top           = None

        self.chemicaldata  = chemicaldata
        self.chemicaldatas = chemicaldatas
        self.editflag      = editflag
        self.tempflag      = tempflag

        self.name          = StringVar() #stores the chemical name
        self.formula       = StringVar()
        self.temp          = DoubleVar() #stores the temperature
        self.MW            = DoubleVar() #stores the molecular weight
        self.Kow           = DoubleVar() #stores the log Kow
        self.density       = DoubleVar() #stores the density
        self.Ref           = StringVar() #stores the density
        self.estimate      = StringVar() #stores how to compute coefficients
        self.Dw            = DoubleVar() #stores the molecular diffusivity
        self.Koc           = DoubleVar() #stores the log Koc
        self.Kdoc          = DoubleVar() #stores the log Kdoc
        self.Kf            = DoubleVar() #stores the log Koc
        self.N             = DoubleVar() #stores the log Kdoc

        self.chemicals_list = self.chemicaldatas.keys()
        self.chemicals_list.sort()

        if editflag == 1:
            
            self.temps     = [temp for temp in self.chemicaldata.temps]
    
            self.densitys  = self.chemicaldata.density.copy()
            self.Refs      = self.chemicaldata.Ref.copy()
            self.Dws       = self.chemicaldata.Dw.copy()
            self.Kows      = self.chemicaldata.Kow.copy()
            self.Kocs      = self.chemicaldata.Koc.copy()
            self.Kdocs     = self.chemicaldata.Kdoc.copy()
            self.Kfs       = self.chemicaldata.Kf.copy()
            self.Ns        = self.chemicaldata.N.copy()

            self.name.set(self.chemicaldata.name)
            self.temp.set(self.temps[0])
            self.formula.set(self.chemicaldata.formula)
            self.MW.set(self.chemicaldata.MW)
            self.density.set(self.densitys[self.temp.get()])
            self.Ref.set(self.Refs[self.temp.get()])
            self.Dw.set(self.Dws[self.temp.get()])
            self.Kow.set(self.Kows[self.temp.get()])
            self.Koc.set(self.Kocs[self.temp.get()])
            self.Kdoc.set(self.Kdocs[self.temp.get()])
            self.Kf.set(self.Kfs[self.temp.get()])
            self.N.set(self.Ns[self.temp.get()])
            self.old_temp       = self.temps[0]
             
        else:
            if tempflag == 1:

                self.name.set(self.chemicaldata.name)
                self.temps     = [temp for temp in self.chemicaldata.temps]
        
                self.densitys  = self.chemicaldata.density.copy()
                self.Refs      = self.chemicaldata.Ref.copy()
                self.Dws       = self.chemicaldata.Dw.copy()
                self.Kows      = self.chemicaldata.Kow.copy()
                self.Kocs      = self.chemicaldata.Koc.copy()
                self.Kdocs     = self.chemicaldata.Kdoc.copy()
                self.Kfs       = self.chemicaldata.Kf.copy()
                self.Ns        = self.chemicaldata.N.copy()

                self.formula.set(self.chemicaldata.formula)
                self.MW.set(self.chemicaldata.MW)

            else:
                
                self.temps     = []
                
                self.densitys  = {}
                self.Refs      = {}
                self.Dws       = {}
                self.Kows      = {}
                self.Kocs      = {}
                self.Kdocs     = {}
                self.Kfs       = {}
                self.Ns        = {}


        self.cancelflag     = 0
        
        self.estimators = ['Supply Manually', 'Estimate from Correlations']
        self.estimate.set(self.estimators[0])

    def make_widgets(self):

        self.instructions2 = Label(self.frame,  text = 'Please provide the following fundamental properties for the chemical:\n')
        self.namelabel     = Button(self.frame,  text = 'Name:', command = self.edit_name, relief = FLAT, overrelief = RAISED)
        
        self.templabel     = Label(self.frame,  text = 'Temperature:')
        self.tempunits     = Label(self.frame,  text = unichr(176) + 'C')

        if self.editflag == 0 and self.tempflag == 0:
            self.namewidget  = Entry(self.frame,  textvariable = self.name, justify = 'center', width = 28, font = 'Calibri 11')
            self.tempwidget  = Entry(self.frame,  textvariable = self.temp, justify = 'center', width = 9)
            
        elif self.editflag == 0 and self.tempflag == 1:
            self.namewidget  = OptionMenu(self.frame, self.name, *self.chemicals_list, command = self.click_name)
            self.tempwidget  = Entry(self.frame,  textvariable = self.temp, justify = 'center', width = 9, font = 'Calibri 11')
            
        elif self.editflag == 1:
            self.namewidget  = Label(self.frame,  textvariable = self.name, justify = 'left',  width = 28, font = 'Calibri 11')
            self.tempwidget  = OptionMenu(self.frame, self.temp, *self.temps, command = self.click_temp)

        self.formlabel     = Button(self.frame,  text = 'Abbreviation/Formula:', command = self.edit_formula, relief = FLAT, overrelief = RAISED)
        self.formentry     = Entry( self.frame,  textvariable = self.formula, justify = 'center', width = 9, font = 'Calibri 11')

        self.MWlabel       = Label(self.frame,  text = 'Molecular Weight:')
        self.MWwidget      = Entry(self.frame,  textvariable = self.MW, justify = 'center', width = 9)
        self.MWunits       = Label(self.frame,  text = 'amu')
        
        self.Kowlabel      = Label(self.frame,  text = 'Octanol-Water Partition Coefficient:')
        self.Kowentry      = Entry(self.frame,  textvariable = self.Kow, justify = 'center', width = 9)
        self.Kowunits      = Label(self.frame,  text = 'log(L/kg)')
        
        self.densitylabel  = Label(self.frame,  text = 'Density:')
        self.densityentry  = Entry(self.frame,  textvariable = self.density, justify = 'center', width = 9)
        self.densityunits  = Label(self.frame,  text = 'kg/L')

        self.Referlabel    = Label(self.frame,  text = 'Reference')
        self.Referentry    = Entry(self.frame,  textvariable = self.Ref, justify = 'center',  width = 28)

        self.instructions3 = Label(self.frame,  text = 'Please provide the following properties for simulating contaminant transport through various\n'  +
                                   'materials, or estimate them using correlations with fundamental properties:\n', justify = 'left')
        
        self.estimatelabel = Label(self.frame,  text = 'Click here to estimate from empirical correlations:')
        self.estimatemenu  = OptionMenu(self.frame, self.estimate, *self.estimators, command = self.estimate_options)

        self.Dwlabel       = Label(self.frame,  text = 'Molecular Diffusion Coefficient:')
        self.Dwentry       = Entry(self.frame,  textvariable = self.Dw, justify = 'center', width = 9)
        self.Dwunits       = Label(self.frame,  text = u'cm\u00B2/s')
        
        self.Koclabel      = Label(self.frame,  text = 'Organic Carbon Partition Coefficient:')
        self.Kocentry      = Entry(self.frame,  textvariable = self.Koc, justify = 'center', width = 9)
        self.Kocunits      = Label(self.frame,  text = 'log (L/kg)')
        
        self.Kdoclabel     = Label(self.frame,  text = 'Dissolved Organic Carbon Partition Coefficient:')
        self.Kdocentry     = Entry(self.frame,  textvariable = self.Kdoc, justify = 'center', width = 9)
        self.Kdocunits     = Label(self.frame,  text = 'log (L/kg)            ')

        self.Kflabel       = Text(self.frame, width = 28, height = 1)
        self.Kflabel.insert('end', '   ', 'sub')
        self.Kflabel.insert('end', u'Activated Carbon Freundlich K')
        self.Kflabel.insert('end', 'F', 'sub')
        self.Kflabel.insert('end', ':')
        self.Kflabel.tag_config('sub', offset = -4, font = self.sfont)
        self.Kflabel.tag_config('right', justify = 'right')
        self.Kflabel.config(state = 'disabled', background = self.frame.cget('bg'), borderwidth = 0, spacing3 = 3)

        self.Kfentry       = Entry(self.frame,  textvariable = self.Kf, justify = 'center', width = 9)

        self.Kfunits  = Text(self.frame, width = 12, height = 1)
        self.Kfunits.insert('end', u'\u00B5g/kg/(\u00B5g/L)')
        self.Kfunits.insert('end', 'N', 'super')
        self.Kfunits.tag_config('super', offset = 5, font = self.sfont)
        self.Kfunits.config(state = 'disabled', background = self.frame.cget('bg'), borderwidth = 0)

        self.Nlabel        = Label(self.frame,  text = 'Activated Carbon Freundlich N:')
        self.Nentry        = Entry(self.frame,  textvariable = self.N, justify = 'center', width = 9)

        self.savebutton    = Button(self.frame, text = 'Save',     command = self.save,   width = 20)
        self.cancelbutton  = Button(self.frame, text = 'Cancel',   command = self.cancel, width = 20)

        self.blank1        = Label(self.frame, text = 8 * ' ')
        self.blank2        = Label(self.frame, text = 50 * ' ')
        self.blank3        = Label(self.frame, text = 10 * ' ', width = 10)
        self.blank4        = Label(self.frame, text = 33 * ' ')
        self.blank5        = Label(self.frame, text = 2 * ' ')
        self.blank6        = Label(self.frame, text = '')
        self.blank7        = Label(self.frame, text = '')
        self.blank8        = Label(self.frame, text = '')

        #show the widgets on the grid (top to bottom and left to right)

        self.blank1.grid(row = 1, column = 0, sticky = 'W')
        self.blank2.grid(row = 1, column = 1, sticky = 'W')
        self.blank3.grid(row = 1, column = 2, sticky = 'W')
        self.blank4.grid(row = 1, column = 3, sticky = 'W')
        self.blank5.grid(row = 1, column = 4, sticky = 'W')
        
        self.instructions2.grid(row = 2, columnspan = 4, sticky = 'W', padx = 8)
        self.namelabel.grid( row = 4,  column = 0, sticky = 'E', padx = 4, pady = 6, columnspan = 2)
        self.namewidget.grid(row = 4,  column = 2, sticky = 'WE',padx = 4, pady = 6, columnspan = 2)
        
        self.templabel.grid( row = 5,  column = 0, sticky = 'E', padx = 4, pady = 6, columnspan = 2)
        self.tempwidget.grid(row = 5,  column = 2, sticky = 'WE',padx = 4, pady = 6)
        self.tempunits.grid( row = 5,  column = 3, sticky = 'W', padx = 4)
        
        i = 6

        self.formlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.formentry.grid(row = i,   column = 2, sticky = 'WE',padx = 4,  pady = 6)
        i = i + 1


        self.MWlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.MWwidget.grid(row = i,  column = 2, sticky = 'WE',padx = 4,  pady = 6)
        self.MWunits.grid(row = i,   column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kowlabel.grid(row = i,  column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.Kowentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4,  ipady = 2)
        self.Kowunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.densitylabel.grid(row = i,  column = 0, sticky = 'E', padx = 4, pady = 6,  columnspan = 2)
        self.densityentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.densityunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Referlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.Referentry.grid(row = i,   column = 2, sticky = 'WE',padx = 4,  pady = 6, columnspan = 2)
        i = i + 1

        self.blank6.grid(row = i)
        i = i + 1

        self.instructions3.grid(row = i, column = 0, columnspan = 5, sticky = 'W', padx = 6)
        i = i + 1

        self.estimatelabel.grid(row = i, column = 0, sticky = 'E',  padx = 4, pady = 2, columnspan = 2)
        self.estimatemenu.grid(row  = i, column = 2, sticky = 'WE', padx = 4, pady = 2, columnspan = 2)
        i = i + 1

        self.Dwlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4, pady = 2,  columnspan = 2)
        self.Dwentry.grid(row = i,   column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Dwunits.grid(row = i,   column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Koclabel.grid(row = i,  column = 0, sticky = 'E', padx = 4, pady = 2, columnspan = 2)
        self.Kocentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kocunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kdoclabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Kdocentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kdocunits.grid(row = i, column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kflabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Kfentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kfunits.grid(row = i, column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Nlabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Nentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        i = i + 1

        self.blank7.grid(row = i)
        self.savebutton.grid(row   = i + 1,column = 0, columnspan = 5, pady = 1)
        self.cancelbutton.grid(row = i + 2,column = 0, columnspan = 5, pady = 1)
        self.blank8.grid(row       = i + 4)

        self.savebutton.bind('<Return>',   self.save)
        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.cancelbutton

    def edit_name (self, event = None):

        self.edit_formula()
        self.name.set(self.formula.get())

        self.frame.update()


    def edit_formula (self, event = None):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(FormulaEditor(self.top, self.version, self.fonttype))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.formula.set(self.top.window.formula.get())
                self.MW.set(self.top.window.MW.get())

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.frame.update()

    def click_name(self, event = None):
        """Modifies widgets for the specific temp."""

        self.chemicaldata = self.chemicaldatas[self.name.get()]

        self.temps     = [temp for temp in self.chemicaldata.temps]

        self.densitys  = self.chemicaldata.density.copy()
        self.Refs      = self.chemicaldata.Ref.copy()
        self.Dws       = self.chemicaldata.Dw.copy()
        self.Kows      = self.chemicaldata.Kow.copy()
        self.Kocs      = self.chemicaldata.Koc.copy()
        self.Kdocs     = self.chemicaldata.Kdoc.copy()
        self.Kfs       = self.chemicaldata.Kf.copy()
        self.Ns        = self.chemicaldata.N.copy()

        self.formula.set(self.chemicaldata.formula)
        self.MW.set(self.chemicaldata.MW)

        self.frame.update()


    def click_temp(self, event = None): 
        """Modifies widgets for the specific temp."""

        self.densitys[self.old_temp]  = self.density.get()
        self.Refs[self.old_temp]      = self.Ref.get()
        self.Dws[self.old_temp]       = self.Dw.get()
        self.Kows[self.old_temp]      = self.Kow.get()
        self.Kocs[self.old_temp]      = self.Koc.get()
        self.Kdocs[self.old_temp]     = self.Kdoc.get()
        self.Kfs[self.old_temp]        = self.Kf.get()
        self.Ns[self.old_temp]         = self.N.get()

        
        self.density.set(self.densitys[self.temp.get()])
        self.Ref.set(self.Refs[self.temp.get()])
        self.Dw.set(self.Dws[self.temp.get()])
        self.Kow.set(self.Kows[self.temp.get()])
        self.Koc.set(self.Kocs[self.temp.get()])
        self.Kdoc.set(self.Kdocs[self.temp.get()])
        self.Kf.set(self.Kfs[self.temp.get()])
        self.N.set(self.Ns[self.temp.get()])

        self.old_temp = self.temp.get()

        self.frame.update()
        
    def estimate_options(self, event):
        """Choose how to calculate coefficients."""

        if event == self.estimators[1]:
            self.top = CapSimWindow(master = self.master, buttons = 1)
            self.top.make_window(Estimators(self.top, self.temp.get(), self.MW.get(), self.Kow.get(), self.density.get(), self.sfont))
            
            self.top.window.Dw.set(self.Dw.get())
            self.top.window.Koc.set(self.Koc.get())
            self.top.window.Kdoc.set(self.Kdoc.get())

            self.top.tk.mainloop()

            if self.top is not None: 
                self.Dw.set(self.top.window.Dw.get())
                self.Koc.set(self.top.window.Koc.get())
                self.Kdoc.set(self.top.window.Kdoc.get())
                self.top.destroy()
                self.top = None

    def save(self, event = None):
        """Saves the properties to the database."""
        
        if self.editflag == 1:            
            self.densitys[self.old_temp]  = self.density.get()
            self.Refs[self.old_temp]      = self.Ref.get()
            self.Dws[self.old_temp]       = self.Dw.get()
            self.Kows[self.old_temp]      = self.Kow.get()
            self.Kocs[self.old_temp]      = self.Koc.get()
            self.Kdocs[self.old_temp]     = self.Kdoc.get()
            self.Kfs[self.old_temp]       = self.Kf.get()
            self.Ns[self.old_temp]        = self.N.get()
        else:
            self.temps.append(self.temp.get())

            self.densitys[self.temp.get()]  = self.density.get()
            self.Refs[self.temp.get()]      = self.Ref.get()
            self.Dws[self.temp.get()]       = self.Dw.get()
            self.Kows[self.temp.get()]      = self.Kow.get()
            self.Kocs[self.temp.get()]      = self.Koc.get()
            self.Kdocs[self.temp.get()]     = self.Kdoc.get()
            self.Kfs[self.temp.get()]       = self.Kf.get()
            self.Ns[self.temp.get()]        = self.N.get()

        Koc_check = 0
        Kdoc_check = 0
        for temp in self.temps:
        
            if self.Kocs[temp] > 20: 
                self.Kocs[temp] = 20
                Koc_check = 1

            if self.Kdocs[temp] > 20: 
                self.Kdocs[temp]= 20
                Kdoc_check = 1
                
        if Koc_check == 1:  tkmb.showinfo(self.version, 'The units of the organic carbon partition coefficient are log (L/kg)!  The value will be set the maximum of 20.')
        if Kdoc_check == 1: tkmb.showinfo(self.version, 'The units of the dissolved organic carbon partition coefficient are log (L/kg)!  The value will be set the maximum of 20.')

        name_check = []
        temp_check = []
        
        if self.editflag == 0 and self.tempflag == 0 :
           name_check =[(name == self.name.get()) for name in self.chemicals_list]
        
        if self.editflag == 0 and self.tempflag == 1 :
           temp_check =[(temp == self.temp.get()) for temp in self.chemicaldata.temps]
           
        if sum(name_check) >= 1:   tkmb.showerror(title = self.version, message = 'The input chemical already exists!')
        elif sum(temp_check) >= 1: tkmb.showerror(title = self.version, message = 'The input temperature already exists!')
        else:                      self.frame.quit()

    def cancel(self, event = None): 

        self.cancelflag = 1
        self.frame.quit()

class FormulaEditor:
    """Used to make a window to compute the value of "kbl" for Rivers."""

    def __init__(self, master, version, fonttype):
        """Constructor method."""

        self.version     = version
        self.fonttype    = fonttype
        self.frame       = Frame(master.frame)
        self.tframe      = Frame(master.tframe)
        self.bframe      = Frame(master.bframe)
        self.superfont   = get_superfont(self.fonttype)

        self.cancelflag  = 0
        self.master      = master

        self.elements    = []
        self.charge      = StringVar()
        self.formula     = StringVar()
        self.MW          = DoubleVar()

    def make_widgets(self):
        """Makes the widgets for the window."""

        self.bgcolor       = self.frame.cget('bg')
        self.instruction   = Label(self.frame,  text = 'Use Button "Add Element" to construct a chemical formula:')


        self.blank1        = Label(self.frame,  text = '')
        self.blank2        = Label(self.frame,  text = '')
        self.blank3        = Label(self.frame,  text = '')
        self.blank4        = Label(self.frame,  text = '')
        self.blank5        = Label(self.frame,  text = '')
        self.blank6        = Label(self.frame,  text = '')

        self.leftcolumn    = Label(self.frame, text = ' ', width = 2)
        self.delcolumn     = Label(self.frame, text = ' ', width = 6)
        self.elementcolumn = Label(self.frame, text = ' ', width = 20)
        self.numbercolumn  = Label(self.frame, text = ' ', width = 20)
        self.MWcolumn      = Label(self.frame, text = ' ', width = 20)
        self.rightcolumn   = Label(self.frame, text = ' ', width = 2)

        self.formulalabel  = Label(self.frame, text = 'Formula:')
        self.formulawidget = Label(self.frame, textvariable = self.formula, font = 'Calibri 11')

        self.chargelabel   = Label(self.frame, text = 'Charge:')
        self.chargewidght  = Entry(self.frame, textvariable = self.charge, width = 10, justify = 'center')

        self.symbollabel     = Label(self.frame, text = 'Element symbols')
        self.numberlabel    = Label(self.frame, text = 'Element numbers')
        self.MWlabel     = Label(self.frame, text = 'Molecular Weight')

        self.addwidget     = Button(self.frame, text = 'Add Element',    width = 20, command = self.add_element)
        self.updatewidget  = Button(self.frame, text = 'Update Formula', width = 20, command = self.updateformula)
        self.okbutton      = Button(self.frame, text = 'OK',             width = 20, command = self.OK)
        self.cancelbutton  = Button(self.frame, text = 'Cancel',         width = 20, command = self.cancel)

        self.addwidget.bind('<Return>', self.add_element)
        self.updatewidget.bind('<Return>', self.updateformula)
        self.okbutton.bind('<Return>', self.OK)
        self.cancelbutton.bind('<Return>', self.cancel)

        self.instruction.grid(      row = 0, columnspan = 5, padx = 8)

        self.leftcolumn.grid(       row = 2, column = 0, sticky = 'WE')
        self.delcolumn.grid(        row = 2, column = 1, sticky = 'WE')
        self.elementcolumn.grid(    row = 2, column = 2, sticky = 'WE')
        self.numbercolumn.grid(     row = 2, column = 3, sticky = 'WE')
        self.MWcolumn.grid(         row = 2, column = 4, sticky = 'WE')
        self.rightcolumn.grid(      row = 2, column = 5, sticky = 'WE')

        self.formulalabel .grid(    row = 3, column = 2, sticky = 'E')
        self.formulawidget .grid(   row = 3, column = 3, sticky = 'WE')

        self.blank2.grid(row = 4)

        self.chargelabel .grid(     row = 5, column = 2, sticky = 'E')
        self.chargewidght .grid(    row = 5, column = 3)

        self.blank3.grid(row = 6)

        self.symbollabel.grid(    row = 7, column = 2, sticky = 'WE')
        self.numberlabel.grid(   row = 7, column = 3, sticky = 'WE')
        self.MWlabel.grid(    row = 7, column = 4, sticky = 'WE')

        self.blank4.grid(row = 8)

        self.updateelements()

    def updateformula(self, event = None):

        formula = ''
        MW      = 0

        for element in self.elements:
            symbol = element.symbol.get()
            number = str(element.number.get())

            if len(symbol) > 0 and element.number.get() <> 0:
                symbol_length = len(symbol)
                number_length = len(number)
                for i in range(symbol_length):
                    if   symbol[i] == '0':  formula = formula + u'\u2080'
                    elif symbol[i] == '1':  formula = formula + u'\u2081'
                    elif symbol[i] == '2':  formula = formula + u'\u2082'
                    elif symbol[i] == '3':  formula = formula + u'\u2083'
                    elif symbol[i] == '4':  formula = formula + u'\u2084'
                    elif symbol[i] == '5':  formula = formula + u'\u2085'
                    elif symbol[i] == '6':  formula = formula + u'\u2086'
                    elif symbol[i] == '7':  formula = formula + u'\u2087'
                    elif symbol[i] == '8':  formula = formula + u'\u2088'
                    elif symbol[i] == '9':  formula = formula + u'\u2089'
                    else:                   formula = formula + symbol[i]

                if number_length > 0 and element.number.get() <> 1:
                    for i in range(number_length):
                        if   number[i] == '0':  formula = formula + u'\u2080'
                        elif number[i] == '1':  formula = formula + u'\u2081'
                        elif number[i] == '2':  formula = formula + u'\u2082'
                        elif number[i] == '3':  formula = formula + u'\u2083'
                        elif number[i] == '4':  formula = formula + u'\u2084'
                        elif number[i] == '5':  formula = formula + u'\u2085'
                        elif number[i] == '6':  formula = formula + u'\u2086'
                        elif number[i] == '7':  formula = formula + u'\u2087'
                        elif number[i] == '8':  formula = formula + u'\u2088'
                        elif number[i] == '9':  formula = formula + u'\u2089'
                        else:                   formula = formula + number[i]

                MW = round(MW + element.MW.get() * element.number.get(), 2)
        charge = self.charge.get()
        if len(charge) > 0:
            for i in range(len(charge)):
                if   charge[i] == '0':  formula = formula + u'\u2070'
                elif charge[i] == '2':  formula = formula + u'\u00B2'
                elif charge[i] == '3':  formula = formula + u'\u00B3'
                elif charge[i] == '4':  formula = formula + u'\u2074'
                elif charge[i] == '5':  formula = formula + u'\u2075'
                elif charge[i] == '6':  formula = formula + u'\u2076'
                elif charge[i] == '7':  formula = formula + u'\u2077'
                elif charge[i] == '8':  formula = formula + u'\u2078'
                elif charge[i] == '9':  formula = formula + u'\u2079'
                elif charge[i] == '+':  formula = formula + u'\u207A'
                elif charge[i] == '-':  formula = formula + u'\u207B'

        self.formula.set(formula)
        self.MW.set(MW)

    def updateelements(self, event = None):

        try:
            self.addwidget.grid_forget()
            self.updatewidget.grid_forget()
            self.okbutton.grid_forget()
            self.cancelbutton.grid_forget()
        except: pass

        row = 9

        for element in self.elements:
            try: element.remove_propertieswidgets()
            except: pass
            element.propertieswidgets(self.frame, row, self.master)
            row = row + 1

        self.blank5.grid(        row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 6)
        row = row + 1
        self.updatewidget.grid( row = row, columnspan = 6)
        row = row + 1
        self.okbutton.grid(      row = row, columnspan = 6)
        row = row + 1
        self.cancelbutton.grid(  row = row, columnspan = 6)
        row = row + 1
        self.blank6.grid(        row = row)

        self.focusbutton = self.okbutton

        self.master.geometry()

    def add_element(self, event = None):
        """Finish and move on."""

        self.elements.append(Element(len(self.elements)+ 1))

        self.elements[-1].symbol     = StringVar()
        self.elements[-1].number     = IntVar()
        self.elements[-1].MW         = DoubleVar()

        self.updateelements()

    def del_element(self, number):

        self.elements[number - 1].remove_propertieswidgets()
        self.elements.remove(self.elements[number - 1])

        self.updateelements()

    def OK(self, event = None):

        self.frame.quit()

    def cancel(self, event = None):
        """Used to close the window without computing kbl."""

        self.cancelflag = 1

        self.frame.quit()

class Element:

    def __init__(self, number):

        self.count = number

    def propertieswidgets(self, frame, row, master):

        self.master = master

        self.delwidget    = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_element)
        self.symbolwidget = Entry( frame, textvariable = self.symbol, width = 10, justify = 'center')
        self.numberwidget = Entry (frame, textvariable = self.number, width = 10, justify = 'center')
        self.MWwidget     = Entry( frame, textvariable = self.MW,     width = 10, justify = 'center')

        self.delwidget.grid(     row  = row, column = 1, padx = 2 ,pady = 1)
        self.symbolwidget.grid(  row  = row, column = 2, padx = 2 ,pady = 1)
        self.numberwidget.grid(  row  = row, column = 3, padx = 2, pady = 1)
        self.MWwidget.grid(      row  = row, column = 4, padx = 2, pady = 1)

    def remove_propertieswidgets(self):

        self.delwidget.grid_forget()
        self.symbolwidget.grid_forget()
        self.numberwidget.grid_forget()
        self.MWwidget.grid_forget()

        self.master = 0
        self.delwidget  = 0
        self.symbolwidget = 0
        self.numberwidget = 0
        self.MWwidget    = 0

    def del_element(self):

        self.master.window.del_element(self.number)


class DatabaseDeleter:
    """Opens a window for inputing the properties of a compound."""

    def __init__(self, master, system, chemicaldata):
        """The constructor method."""
        
        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.frame         = Frame(master.frame)
        self.tframe        = Frame(master.tframe)
        self.bframe        = Frame(master.bframe)

        self.chemicaldata  = chemicaldata

        self.name          = StringVar(value = chemicaldata.name)   #stores the chemical name
        self.formula       = StringVar()
        self.temp          = DoubleVar()                            #stores the temperature
        self.MW            = DoubleVar() #stores the molecular weight
        self.Kow           = DoubleVar() #stores the log Kow
        self.density       = DoubleVar() #stores the density
        self.Ref           = StringVar() #stores the density
        self.Dw            = DoubleVar() #stores the molecular diffusivity
        self.Koc           = DoubleVar() #stores the log Koc
        self.Kdoc          = DoubleVar() #stores the log Kdoc
        self.Kf            = DoubleVar() #stores the log Koc
        self.N             = DoubleVar() #stores the log Kdoc

        self.temps     = [temp for temp in self.chemicaldata.temps]       
        self.Kows      = self.chemicaldata.Kow.copy()
        self.densitys  = self.chemicaldata.density.copy()
        self.Refs      = self.chemicaldata.Ref.copy()
        self.Dws       = self.chemicaldata.Dw.copy()
        self.Kocs      = self.chemicaldata.Koc.copy()
        self.Kdocs     = self.chemicaldata.Kdoc.copy()
        self.Kfs       = self.chemicaldata.Kf.copy()
        self.Ns        = self.chemicaldata.N.copy()

        self.temp.set(self.temps[0])
        self.formula.set(self.chemicaldata.formula)
        self.MW.set(self.chemicaldata.MW)
        self.density.set(self.densitys[self.temp.get()])
        self.Ref.set(self.Refs[self.temp.get()])
        self.Dw.set(self.Dws[self.temp.get()])
        self.Kow.set(self.Kows[self.temp.get()])
        self.Koc.set(self.Kocs[self.temp.get()])
        self.Kdoc.set(self.Kdocs[self.temp.get()])
        self.Kf.set(self.Kfs[self.temp.get()])
        self.N.set(self.Ns[self.temp.get()])

        self.cancelflag      = 0
        
    def make_widgets(self):

        self.instructions  = Label(self.frame,  text = 'Are you sure to delete the following chemical from the database?      ')
        self.namelabel     = Label(self.frame,  text = 'Name:')
        self.namewidget    = Label(self.frame,  textvariable = self.name, justify = 'left',   width = 28)
        
        self.templabel     = Label(self.frame,  text = 'Temperature:')
        self.tempwidget    = OptionMenu(self.frame, self.temp, *self.temps, command = self.click_temp)
        self.tempunits     = Label(self.frame,  text = unichr(176) + 'C')
        
        self.formlabel     = Label(self.frame,  text = 'Abbreviation:')
        self.formentry     = Label(self.frame,  textvariable = self.formula, justify = 'center', width = 9)
        
        self.MWlabel       = Label(self.frame,  text = 'Molecular Weight:')
        self.MWwidget      = Label(self.frame,  textvariable = self.MW, justify = 'center', width = 9)
        self.MWunits       = Label(self.frame,  text = 'amu')
        
        self.Kowlabel      = Label(self.frame,  text = 'Octanol-Water Partition Coefficient:')
        self.Kowentry      = Label(self.frame,  textvariable = self.Kow, justify = 'center', width = 9)
        self.Kowunits      = Label(self.frame,  text = 'log(L/kg)')
        
        self.densitylabel  = Label(self.frame,  text = 'Density:')
        self.densityentry  = Label(self.frame,  textvariable = self.density, justify = 'center', width = 9)
        self.densityunits  = Label(self.frame,  text = 'kg/L')

        self.Dwlabel       = Label(self.frame,  text = 'Molecular Diffusion Coefficient:')
        self.Dwentry       = Label(self.frame,  textvariable = self.Dw, justify = 'center', width = 9)
        self.Dwunits       = Label(self.frame,  text = u'cm\u00B2/s')
        
        self.Koclabel      = Label(self.frame,  text = 'Organic Carbon Partition Coefficient:')
        self.Kocentry      = Label(self.frame,  textvariable = self.Koc, justify = 'center', width = 9)
        self.Kocunits      = Label(self.frame,  text = 'log (L/kg)')
        
        self.Kdoclabel     = Label(self.frame,  text = 'Dissolved Organic Carbon Partition Coefficient:')
        self.Kdocentry     = Label(self.frame,  textvariable = self.Kdoc, justify = 'center', width = 9)
        self.Kdocunits     = Label(self.frame,  text = 'log (L/kg)            ')

        self.Kflabel       = Text(self.frame, width = 28, height = 1)
        self.Kflabel.insert('end', '   ', 'sub')
        self.Kflabel.insert('end', u'Activated Carbon Freundlich K')
        self.Kflabel.insert('end', 'F', 'sub')
        self.Kflabel.insert('end', ':')
        self.Kflabel.tag_config('sub', offset = -4, font = self.sfont)
        self.Kflabel.tag_config('right', justify = 'right')
        self.Kflabel.config(state = 'disabled', background = self.frame.cget('bg'), borderwidth = 0, spacing3 = 3)

        self.Kfentry       = Label(self.frame,  textvariable = self.Kf, justify = 'center', width = 9)

        self.Kfunits  = Text(self.frame, width = 12, height = 1)
        self.Kfunits.insert('end', u'\u00B5g/kg/(\u00B5g/L)')
        self.Kfunits.insert('end', 'N', 'super')
        self.Kfunits.tag_config('super', offset = 5, font = self.sfont)
        self.Kfunits.config(state = 'disabled', background = self.frame.cget('bg'), borderwidth = 0)

        self.Nlabel        = Label(self.frame,  text = 'Activated Carbon Freundlich N:')
        self.Nentry        = Label(self.frame,  textvariable = self.N, justify = 'center', width = 9)

        self.tempbutton    = Button(self.frame, text = 'Delete Temperature', command = self.deletetemp,     width = 20)
        self.chembutton    = Button(self.frame, text = 'Delete Chemical',    command = self.deletechemical, width = 20)
        self.cancelbutton  = Button(self.frame, text = 'Cancel',             command = self.cancel,         width = 20)

        self.blank1        = Label(self.frame, text = 8 * ' ')
        self.blank2        = Label(self.frame, text = 50 * ' ')
        self.blank3        = Label(self.frame, text = '')
        self.blank4        = Label(self.frame, text = 33 * ' ')
        self.blank5        = Label(self.frame, text = 2 * ' ')
        self.blank6        = Label(self.frame, text = '')
        self.blank7        = Label(self.frame, text = '')
        self.blank8        = Label(self.frame, text = '')
        self.blank9        = Label(self.frame, text = ' ')
        #show the widgets on the grid (top to bottom and left to right)

        self.blank1.grid(row = 1, column = 0, sticky = 'W')
        self.blank2.grid(row = 1, column = 1, sticky = 'W')
        self.blank3.grid(row = 1, column = 2, sticky = 'W')
        self.blank4.grid(row = 1, column = 3, sticky = 'W')
        self.blank5.grid(row = 1, column = 4, sticky = 'W')
        
        self.instructions.grid(row = 2, columnspan = 4, sticky = 'W', padx = 8)
        self.namelabel.grid( row = 4,  column = 0, sticky = 'E', padx = 4, pady = 6, columnspan = 2)
        self.namewidget.grid(row = 4,  column = 2, sticky = 'W', padx = 4, pady = 6, columnspan = 2)
        
        self.templabel.grid( row = 5,  column = 0, sticky = 'E', padx = 4, pady = 6, columnspan = 2)
        self.tempwidget.grid(row = 5,  column = 2, sticky = 'WE',padx = 4, pady = 6)
        self.tempunits.grid( row = 5,  column = 3, sticky = 'W', padx = 4)
        
        i = 6
        self.formlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.formentry.grid(row = i,   column = 2, sticky = 'WE',padx = 4,  pady = 6)
        
        i = i + 1
        self.MWlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.MWwidget.grid(row = i,  column = 2, sticky = 'WE',padx = 4,  pady = 6)
        self.MWunits.grid(row = i,   column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kowlabel.grid(row = i,  column = 0, sticky = 'E', padx = 4,  pady = 6,  columnspan = 2)
        self.Kowentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4,  ipady = 2)
        self.Kowunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.densitylabel.grid(row = i,  column = 0, sticky = 'E', padx = 4, pady = 6,  columnspan = 2)
        self.densityentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.densityunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.blank6.grid(row = i)
        i = i + 1

        self.Dwlabel.grid(row = i,   column = 0, sticky = 'E', padx = 4, pady = 2,  columnspan = 2)
        self.Dwentry.grid(row = i,   column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Dwunits.grid(row = i,   column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Koclabel.grid(row = i,  column = 0, sticky = 'E', padx = 4, pady = 2, columnspan = 2)
        self.Kocentry.grid(row = i,  column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kocunits.grid(row = i,  column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kdoclabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Kdocentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kdocunits.grid(row = i, column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Kflabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Kfentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        self.Kfunits.grid(row = i, column = 3, sticky = 'W', padx = 4)
        i = i + 1

        self.Nlabel.grid(row = i, column = 0, sticky = 'E', padx = 4, pady = 2,columnspan = 2)
        self.Nentry.grid(row = i, column = 2, sticky = 'WE', padx = 4, ipady = 2)
        i = i + 1

        self.blank7.grid(row = i)
        if len(self.temps) > 1:
            self.tempbutton.grid(row   = i+1,column = 0, columnspan = 5, pady = 1)
        else:
            self.blank9.grid(row   = i+1,column = 0, columnspan = 5, pady = 1)
        self.chembutton.grid(row   = i+2,column = 0, columnspan = 5, pady = 1)
        self.cancelbutton.grid(row = i+4,column = 0, columnspan = 5, pady = 1)
        self.blank8.grid(row       = i+5)

        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.cancelbutton

    def update_temp(self):

        self.tempwidget.grid_forget()
        self.tempwidget    = OptionMenu(self.frame, self.temp, *self.temps, command = self.click_temp)
        self.tempwidget.grid(row = 5,  column = 2, sticky = 'WE',padx = 4, pady = 6)

    def click_temp(self, event = None): 
        """Modifies widgets for the specific temp."""

        self.density.set(self.densitys[self.temp.get()])
        self.Dw.set(self.Dws[self.temp.get()])
        self.Kow.set(self.Kows[self.temp.get()])
        self.Koc.set(self.Kocs[self.temp.get()])
        self.Kdoc.set(self.Kdocs[self.temp.get()])
        self.Kf.set(self.Kfs[self.temp.get()])
        self.N.set(self.Ns[self.temp.get()])

        self.frame.update()
        
    def deletechemical(self, event = None):

        self.cancelflag = 2
        
        self.frame.quit()

    def deletetemp(self, event = None):


        self.old_temp = self.temp.get()
        
        self.temps.remove(self.old_temp)        
        self.temp.set(self.temps[0])
        
        self.density.set(self.densitys[self.temp.get()])
        self.Dw.set(self.Dws[self.temp.get()])
        self.Kow.set(self.Kows[self.temp.get()])
        self.Koc.set(self.Kocs[self.temp.get()])
        self.Kdoc.set(self.Kdocs[self.temp.get()])
        self.Kf.set(self.Kfs[self.temp.get()])
        self.N.set(self.Ns[self.temp.get()])

        del self.densitys[self.old_temp]
        del self.Dws[self.old_temp]
        del self.Kows[self.old_temp]
        del self.Kocs[self.old_temp]
        del self.Kdocs[self.old_temp]
        del self.Kfs[self.old_temp]
        del self.Ns[self.old_temp]

        if len(self.temps) == 1:
            self.tempbutton.grid_forget()
            self.blank9.grid(row   = 14,column = 0, columnspan = 5, pady = 1)

        self.update_temp()
        self.frame.update()
        self.frame.quit()

    def cancel(self, event = None): 

        self.cancelflag = 1
        self.frame.quit()

class DatabaseImporter:

    def __init__(self, master, system, database_imported):
        """The constructor method."""

        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.frame         = Frame(master.frame)
        self.tframe        = Frame(master.tframe)
        self.bframe        = Frame(master.bframe)
        self.tkfont        = tkFont.Font(font = system.fonttype)

        self.chemicals_list = database_imported.keys()
        self.chemicals_list.sort()

        self.name_width    = 10

        for chemical_name in self.chemicals_list:
            if (self.tkfont.measure(chemical_name) + 10) > self.name_width: self.name_width = self.tkfont.measure(chemical_name) + 10

        if self.name_width < 150: self.name_width = 150

        self.importedchemicals = {}
        for name in self.chemicals_list:
            self.importedchemicals[name] = ChemicalData(name)
            self.importedchemicals[name].read_database(database_imported[name])

        self.cancelflag      = 0

        self.sname     = StringVar(self.frame, value = '')

    def make_widgets(self):

        self.instructions     = Label( self.tframe,  text = 'Please select the chemical you would like to add to the database       ')

        self.leftcolumn       = Label( self.tframe,  text = ' ', width = 2)
        self.checkcolumn      = Label( self.tframe,  text = ' ', width = 5)
        self.orinamecolumn    = Label( self.tframe,  text = ' ', width = int(self.name_width*1.1424219345/8)+1)
        self.impnamecolumn1   = Label( self.tframe,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.impnamecolumn2   = Label( self.tframe,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.rightcolumn      = Label( self.tframe,  text = ' ', width = 2)

        self.search_label     = Label( self.tframe,  text          = 'Search:')
        self.search_entry     = Entry( self.tframe,  textvariable  = self.sname)

        self.orinamelabel     = Label( self.tframe,  text = 'Original Name')
        self.impnamelabel     = Label( self.tframe,  text = 'Imported Name')

        self.botleftcolumn       = Label(self.frame,  text = ' ', width = 2)
        self.botcheckcolumn      = Label(self.frame,  text = ' ', width = 5)
        self.botorinamecolumn    = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8)+1)
        self.botimpnamecolumn1   = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.botimpnamecolumn2   = Label(self.frame,  text = ' ', width = int(self.name_width*1.1424219345/8/2)+1)
        self.botrightcolumn      = Label(self.frame,  text = ' ', width = 2)

        self.allbutton        = Button(self.bframe, text = 'Select All',     command = self.selectall,      width = 20)
        self.unallbutton      = Button(self.bframe, text = 'Unselect All',   command = self.unselectall,    width = 20)
        self.importbutton     = Button(self.bframe, text = 'Import',         command = self.OK,             width = 20)
        self.cancelbutton     = Button(self.bframe, text = 'Cancel',         command = self.cancel,         width = 20)

        self.blank1           = Label(self.tframe, text = ' ')
        self.blank2           = Label(self.bframe, text = ' ')
        self.blank3           = Label(self.bframe, text = ' ')
        self.blank4           = Label(self.frame,  text = ' ')
        self.blank5           = Label(self.tframe, text = ' ')

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

        self.blank5.grid(row = 3)

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

        for name in self.chemicals_list:
            try: self.importedchemicals[name].remove_importedchemicalwidgets()
            except: pass

        if self.sname.get() == '':
            for name in self.chemicals_list:
                if self.importedchemicals[name].check == 1:
                    self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                    row = row + 1

            for name in self.chemicals_list:
                if self.importedchemicals[name].check == 0:
                    self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                    row = row + 1
        else:
            for name in self.chemicals_list:
                if name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                    if self.importedchemicals[name].check == 1:
                        self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                        row = row + 1

            for name in self.chemicals_list:
                if name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                    if self.importedchemicals[name].check == 0:
                        self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                        row = row + 1
                else:
                    self.importedchemicals[name].check = IntVar(value = self.importedchemicals[name].check)

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

        for name in self.chemicals_list:
            try: self.importedchemicals[name].remove_importedchemicalwidgets()
            except: pass

        for name in self.chemicals_list:
            if self.importedchemicals[name].check == 1:
                self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
                row = row + 1

        for name in self.chemicals_list:
            if self.importedchemicals[name].check == 0:
                self.importedchemicals[name].importedchemicalwidgets(self.frame, row = row, namewidth=int(self.name_width*1.1424219345/8)+1)
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

        for name in self.chemicals_list:
            if name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                self.importedchemicals[name].check.set(1)

    def unselectall(self, event = None):

        for name in self.chemicals_list:
            if name.lower()[:len(self.sname.get())].count(self.sname.get().lower()) >= 1:
                self.importedchemicals[name].check.set(0)

    def OK(self, event = None):

        for name in self.chemicals_list:
            self.importedchemicals[name].get_importedchemical()

        self.frame.quit()

    def cancel(self, event = None):

        self.cancelflag = 1
        self.frame.quit()


