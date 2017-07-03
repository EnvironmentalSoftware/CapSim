#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb
import tkFont

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical
from capsim_functions    import get_superfont
from database            import Database
from numpy               import exp

class SorptionEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, sorption):
        
        """Constructor method.  Defines the parameters to be obtained in this
        window."""
        
        self.master     = master
        self.fonttype   = system.fonttype
        self.version    = system.version
        self.sfont      = get_superfont(self.fonttype)  #superscript font
        self.frame      = Frame(master.frame)
        self.tframe     = Frame(master.tframe)
        self.bframe     = Frame(master.bframe)
        self.top        = None                   #flag for existence of toplevel#

        self.system     = system

        self.isotherms      = ['Linear--Kd specified', 'Linear--Kocfoc', 'Freundlich', 'Langmuir']
        self.kinetics       = ['Equilibrium', 'Transient']

        self.sorption   = sorption
            
        self.isotherm   = StringVar(value = sorption.isotherm)
        self.kinetic    = StringVar(value = sorption.kinetic)
        self.K          = DoubleVar(value = sorption.K)
        self.Koc        = DoubleVar(value = sorption.Koc)
        self.Kf         = DoubleVar(value = sorption.Kf)
        self.N          = DoubleVar(value = sorption.N)
        self.qmax       = DoubleVar(value = sorption.qmax)
        self.b          = DoubleVar(value = sorption.b)
        self.ksorp      = DoubleVar(value = sorption.ksorp)

        self.cinit      = sorption.cinit
        self.qinit      = sorption.qinit
        self.thalf      = sorption.thalf

        self.concunit   = system.concunit
        self.timeunit   = system.timeunit

        self.tkfont      = tkFont.Font(font = self.fonttype)

        self.cancelflag = 0
        
    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Please provide the following sorption properties:                    ')

        self.leftcolumn     = Label(self.frame, width = 2,  text = '' )
        self.matrixcolumn   = Label(self.frame, width = 10, text = '' )
        self.chemicalcolumn = Label(self.frame, width = 10, text = '' )
        self.isothermcolumn = Label(self.frame, width = 20, text = '' )
        self.kineticcolumn  = Label(self.frame, width = 15, text = '' )
        self.equacolumn     = Label(self.frame, width = 17, text = '' )
        self.coefcolumn1    = Label(self.frame, width = 6,  text = '' )
        self.coefcolumn2    = Label(self.frame, width = 9,  text = '' )
        self.coefcolumn3    = Label(self.frame, width = int(self.tkfont.measure(self.concunit[:-1]+'/kg/('+ self.concunit +')'+ u'\u1d3a')/8)+1, text = '' )
        self.coefcolumn4    = Label(self.frame, width = 4,  text = '' )
        self.coefcolumn5    = Label(self.frame, width = 9,  text = '' )
        self.coefcolumn6    = Label(self.frame, width = int(self.tkfont.measure(self.concunit)/8)+1,  text = '' )
        self.coefcolumn7    = Label(self.frame, width = 7,  text = '' )
        self.coefcolumn8    = Label(self.frame, width = 9,  text = '' )
        self.coefcolumn9    = Label(self.frame, width = 10, text = '' )
        self.rightcolumn    = Label(self.frame, width = 2,  text = '' )

        self.matrixlabel    = Label(self.frame, text = 'Matrix')
        self.chemicallabel  = Label(self.frame, text = 'Chemical')
        self.isothermlabel  = Label(self.frame, text = 'Sorption Isotherm')
        self.kineticlabel   = Label(self.frame, text = 'Kinetics')

        self.matrixwidget   = Label(self.frame, text = self.sorption.matrix.name)
        self.chemicalwidget = Label(self.frame, text = self.sorption.chemical.name)
        self.isothermwidget = OptionMenu(self.frame, self.isotherm, *self.isotherms, command = self.click_isotherm)
        self.kineticwidget  = OptionMenu(self.frame, self.kinetic,  *self.kinetics,  command = self.click_kinetic)
        
        self.okbutton     = Button(self.frame, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')
        
        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 15, padx = 2, pady = 8, sticky = 'W')

        self.leftcolumn.grid(    row = 1, column = 0,   padx = 2, pady = 1, sticky = 'WE')
        self.matrixcolumn.grid(  row = 1, column = 1,   padx = 2, pady = 1, sticky = 'WE')
        self.chemicalcolumn.grid(row = 1, column = 2,   padx = 2, pady = 1, sticky = 'WE')
        self.isothermcolumn.grid(row = 1, column = 3,   padx = 2, pady = 1, sticky = 'WE')
        self.kineticcolumn.grid( row = 1, column = 4,   padx = 2, pady = 1, sticky = 'WE')
        self.equacolumn.grid(    row = 1, column = 5,   padx = 2, pady = 1, sticky = 'WE')
        self.coefcolumn1.grid(   row = 1, column = 6,   padx = 0, pady = 1)
        self.coefcolumn2.grid(   row = 1, column = 7,   padx = 0, pady = 1)
        self.coefcolumn3.grid(   row = 1, column = 8,   padx = 0, pady = 1)
        self.coefcolumn4.grid(   row = 1, column = 9,   padx = 0, pady = 1)
        self.coefcolumn5.grid(   row = 1, column = 10,  padx = 0, pady = 1)
        self.coefcolumn6.grid(   row = 1, column = 11,  padx = 0, pady = 1)
        self.coefcolumn7.grid(   row = 1, column = 12,  padx = 0, pady = 1)
        self.coefcolumn8.grid(   row = 1, column = 13,  padx = 0, pady = 1)
        self.coefcolumn9.grid(   row = 1, column = 14,  padx = 0, pady = 1)
        self.rightcolumn.grid(   row = 1, column = 15,  padx = 0, pady = 1)

        self.matrixlabel.grid(   row = 2, column = 1,  padx = 2, pady = 4, sticky = 'WE')
        self.chemicallabel.grid( row = 2, column = 2,  padx = 2, pady = 4, sticky = 'WE')
        self.isothermlabel.grid( row = 2, column = 3,  padx = 2, pady = 4, sticky = 'WE')
        self.kineticlabel.grid(  row = 2, column = 4,  padx = 2, pady = 4, sticky = 'WE')

        self.matrixwidget.grid(  row = 3, column = 1,  padx = 2, pady = 1, sticky = 'WE')
        self.chemicalwidget.grid(row = 3, column = 2,  padx = 2, pady = 1, sticky = 'WE')
        self.isothermwidget.grid(row = 3, column = 3,  padx = 2, pady = 1, sticky = 'WE')
        self.kineticwidget.grid( row = 3, column = 4,  padx = 2, pady = 1, sticky = 'WE')

        self.blank1.grid(       row    = 4)
        self.okbutton.grid(     row    = 5, columnspan = 15)
        self.cancelbutton.grid( row    = 6, columnspan = 15)
        self.blank2.grid(       row    = 7)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        self.click_isotherm()
        self.click_kinetic()

    def click_kinetic(self, event = None):

        bgcolor = self.frame.cget('bg')

        try:
            self.klabel.grid_forget()
            self.ksorplabel.grid_forget()
            self.ksorpwidget.grid_forget()
            self.ksorpunits.grid_forget()
        except: pass

        if self.kinetic.get() == self.kinetics[1]:

            if self.isotherm.get() == self.isotherms[3]:
                self.klabel  = Label(self.frame, text = 'Kinetic rate coefficient:')
            else:
                self.klabel  = Button(self.frame, text = 'Kinetic rate coefficient:', command = self.k_estimator)

            self.ksorplabel = Text(self.frame, width = 7, height = 1)
            self.ksorplabel.insert('end', u'k')
            self.ksorplabel.insert('end', 'sorp', 'sub')
            self.ksorplabel.insert('end', u' =')
            self.ksorplabel.tag_config('sub', offset = -2, font = 'Arial 8')
            self.ksorplabel.tag_config('right', justify = 'right')
            self.ksorplabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

            self.ksorpwidget = Entry(self.frame, textvariable = self.ksorp, justify = 'center', width = 10)

            if self.isotherm.get() == self.isotherms[0] or self.isotherm.get() == self.isotherms[1]:
                self.ksorpunits   = Label(self.frame, text = self.timeunit +u'\u207B\u00b9')
            if self.isotherm.get() == self.isotherms[2]:
                self.ksorpunits   = Label(self.frame, text = self.timeunit +u'\u207B\u00b9')
            if self.isotherm.get() == self.isotherms[3]:
                self.ksorpunits   = Label(self.frame, text = '(' + self.concunit[:-1] +'kg)'+u'\u207B\u00b9 ' +self.timeunit + u'\u207B\u00b9')

            self.klabel.grid(     row  = 2, column = 12, padx = 1, pady = 1, sticky = 'WE', columnspan = 3)
            self.ksorplabel.grid( row  = 3, column = 12, padx = 1, pady = 5, sticky = 'SE')
            self.ksorpwidget.grid(row  = 3, column = 13, padx = 1, pady = 1)
            self.ksorpunits.grid( row  = 3, column = 14, padx = 1, sticky = 'W')

    def k_estimator(self, event = None):

        k_error = 0
        coef = []
        coef.append(self.cinit)
        coef.append(self.qinit)
        coef.append(self.thalf)
        coef.append(self.ksorp.get())
        if self.isotherm.get() == self.isotherms[0]:
            coef.append(self.K.get())
            coef.append(0)
            if self.K.get() == 0:
                K_error = 1
        if self.isotherm.get() == self.isotherms[1]:
            coef.append(self.Koc.get())
            coef.append(self.sorption.matrix.foc)
            if self.Koc.get() == 0:
                K_error = 1
        if self.isotherm.get() == self.isotherms[2]:
            coef.append(self.Kf.get())
            coef.append(self.N.get())
            if self.Kf.get() == 0 or self.N.get() == 0:
                K_error = 1
        if self.isotherm.get() == self.isotherms[3]:
            coef.append(self.qmax.get())
            coef.append(self.b.get())
            if self.qmax.get() == 0 or self.b.get() == 0:
                K_error = 1

        coef.append(self.sorption.matrix.e)
        coef.append(self.sorption.matrix.rho)

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(K_Estimator(self.top, self.system, self.isotherm.get(), coef))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.ksorp.set(self.top.window.ksorp.get())
                self.cinit = self.top.window.cinit.get()
                self.qinit = self.top.window.qinit.get()
                self.thalf = self.top.window.thalf.get()

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()


    def click_isotherm(self, event = None):

        try:
            self.equalabel.grid_forget()
            self.coeflabel.grid_forget()
            self.eqwidget.grid_forget()
        except: pass

        try:
            self.Klabel.grid_forget()
            self.Kwidget.grid_forget()   
            self.Kunits.grid_forget()  
        except: pass

        try:
            self.Koclabel.grid_forget()
            self.Kocwidget.grid_forget()
            self.Kocunits.grid_forget()
        except: pass
        
        try:
            self.Kflabel.grid_forget()      
            self.Nlabel.grid_forget()    
            self.Kfwidget.grid_forget() 
            self.Nwidget.grid_forget()          
            self.Kfunits.grid_forget()     
        except: pass
        
        try:
            self.qmaxlabel.grid_forget() 
            self.qmaxwidget.grid_forget()
            self.qmaxunits.grid_forget() 
            self.blabel.grid_forget()    
            self.bwidget.grid_forget()   
            self.bunits.grid_forget()
        except: pass
        

        bgcolor = self.frame.cget('bg')
        
        if self.isotherm.get() == self.isotherms[0]:
            
            self.equalabel  = Label(self.frame, text = 'Isotherm Equation')
            self.eqwidget = Text(self.frame, width = 7, height = 1)
            self.eqwidget.insert('end', u'q = K')
            self.eqwidget.insert('end', 'd', 'sub')
            self.eqwidget.insert('end', 'C')
            self.eqwidget.tag_config('sub', offset = -2, font = 'Arial 8')
            self.eqwidget.tag_config('right', justify = 'center')
            self.eqwidget.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
            
            self.coeflabel  = Label(self.frame, text = 'Matrix-water partition coefficient')
            
            self.Klabel   = Text(self.frame, width = 4, height = 1)
            self.Klabel.insert('end', 'K')
            self.Klabel.insert('end', 'd', 'sub')
            self.Klabel.insert('end', ' =')
            self.Klabel.tag_config('sub', offset = -2, font = 'Arial 8')
            self.Klabel.tag_config('right', justify = 'right')
            self.Klabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
            
            self.Kwidget  = Entry(self.frame, textvariable = self.K, justify = 'center', width = 10)
            self.Kunits   = Label(self.frame, text = 'L/kg')

            self.equalabel.grid( row  = 2, column = 5, padx = 2, pady = 1, sticky = 'WE')
            self.coeflabel.grid( row  = 2, column = 6, padx = 2, pady = 1, sticky = 'WE', columnspan = 6)
            self.eqwidget.grid(  row  = 3, column = 5, padx = 1, pady = 5, sticky = 'S')
            self.Klabel.grid(    row  = 3, column = 6, padx = 0, pady = 5, sticky = 'SE')
            self.Kwidget.grid(   row  = 3, column = 7, padx = 0)
            self.Kunits.grid(    row  = 3, column = 8, padx = 0, sticky = 'W')
            
        elif self.isotherm.get() == self.isotherms[1]:
            
            self.equalabel  = Label(self.frame, text = 'Isotherm Equation')
            self.eqwidget = Text(self.frame, width = 10, height = 1)
            self.eqwidget.insert('end', u'q = K')
            self.eqwidget.insert('end', 'oc', 'sub')
            self.eqwidget.insert('end', 'f')
            self.eqwidget.insert('end', 'oc', 'sub')
            self.eqwidget.insert('end', 'C')
            self.eqwidget.tag_config('sub', offset = -2, font = 'Arial 8')
            self.eqwidget.tag_config('right', justify = 'right')
            self.eqwidget.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
            
            self.coeflabel     = Label(self.frame, text = 'Organic carbon partition coefficient:')
            
            self.Koclabel  = Text(self.frame, width = 5, height = 1)
            self.Koclabel.insert('end', 'K')
            self.Koclabel.insert('end', 'oc', 'sub')
            self.Koclabel.insert('end', ' =')
            self.Koclabel.tag_config('sub', offset = -2, font = 'Arial 8')
            self.Koclabel.tag_config('right', justify = 'right')
            self.Koclabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
            
            self.Kocwidget = Entry(self.frame, textvariable = self.Koc, justify = 'center', width = 10)
            self.Kocunits  = Label(self.frame, text = 'log(L/kg)')

            self.equalabel.grid(    row  = 2, column = 5, padx = 2, pady = 1, sticky = 'WE')
            self.coeflabel.grid(    row  = 2, column = 6, padx = 2, pady = 1, sticky = 'WE', columnspan = 6)
            self.eqwidget.grid(     row  = 3, column = 5, padx = 1, pady = 5, sticky = 'S')
            self.Koclabel.grid (    row  = 3, column = 6, padx = 0, pady = 5, sticky = 'SE')
            self.Kocwidget.grid(    row  = 3, column = 7, padx = 0)
            self.Kocunits.grid(     row  = 3, column = 8, padx = 0, sticky = 'W')
        
        elif self.isotherm.get() == self.isotherms[2]:

            self.equalabel  = Label(self.frame, text = 'Isotherm Equation')
            self.eqwidget = Text(self.frame, width = 8, height = 1)
            self.eqwidget.insert('end', u'q = K')
            self.eqwidget.insert('end', 'F', 'sub')
            self.eqwidget.insert('end', 'C')
            self.eqwidget.insert('end', 'N', 'super')
            self.eqwidget.tag_config('sub', offset = -2, font = 'Arial 8')
            self.eqwidget.tag_config('super', offset = 5, font = self.sfont)
            self.eqwidget.tag_config('right', justify = 'right')
            self.eqwidget.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

            self.coeflabel  = Label(self.frame, text = 'Freudlich isotherm coefficient:')
            self.Kflabel = Text(self.frame, width = 4, height = 1)
            self.Kflabel.insert('end', u'K')
            self.Kflabel.insert('end', 'F', 'sub')
            self.Kflabel.insert('end', u' =')
            self.Kflabel.tag_config('sub', offset = -2, font = 'Arial 8')
            self.Kflabel.tag_config('right', justify = 'right')
            self.Kflabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
            self.Nlabel   = Label(self.frame, text = 'N =')
            self.Kfwidget = Entry(self.frame, textvariable = self.Kf,justify = 'center', width = 10)
            self.Nwidget  = Entry(self.frame, textvariable = self.N, justify = 'center', width = 10)

            self.Kfunits  = Label(self.frame, text = self.concunit[:-1]+'/kg/('+ self.concunit +')'+ u'\u1d3a')

            self.equalabel.grid(    row  = 2, column = 5,  padx = 2, pady = 1, sticky = 'WE')
            self.coeflabel.grid(    row  = 2, column = 6,  padx = 2, pady = 1, sticky = 'WE', columnspan = 6)
            self.eqwidget.grid(     row  = 3, column = 5,  padx = 1, pady = 5, sticky = 'S')
            self.Kflabel.grid(      row  = 3, column = 6,  padx = 0, pady = 5, sticky = 'SE')
            self.Kfwidget.grid(     row  = 3, column = 7,  padx = 0)
            self.Kfunits.grid(      row  = 3, column = 8,  padx = 0, sticky = 'W')
            self.Nlabel.grid (      row  = 3, column = 9,  padx = 0, sticky = 'E')
            self.Nwidget.grid(      row  = 3, column = 10, padx = 0)
            
        elif self.isotherm.get() == self.isotherms[3]:
            
            self.equalabel  = Label(self.frame, text = 'Isotherm Equation')
            self.eqwidget = Text(self.frame, width = 17, height = 0.1)
            self.eqwidget.insert('end', u'q = q')
            self.eqwidget.insert('end', 'max', 'sub')
            self.eqwidget.insert('end', 'b*C/(1+b*C)')
            self.eqwidget.tag_config('sub', offset = -2, font = 'Arial 8')
            self.eqwidget.tag_config('right', justify = 'right')
            self.eqwidget.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

            self.coeflabel  = Label(self.frame, text = 'Langmuir isotherm coefficient:')
            self.qmaxlabel = Text(self.frame, width = 7, height = 0.1)
            self.qmaxlabel.insert('end', '  ', 'sub')
            self.qmaxlabel.insert('end', u'q')
            self.qmaxlabel.insert('end', 'max', 'sub')
            self.qmaxlabel.insert('end', u' =')
            self.qmaxlabel.tag_config('sub', offset = -3, font = 'Arial 8')
            self.qmaxlabel.tag_config('right', justify = 'right')
            self.qmaxlabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

            self.qmaxwidget = Entry(self.frame, textvariable = self.qmax, justify = 'center', width = 10)
            self.qmaxunits  = Label(self.frame, text = self.concunit[:-1] +  'kg')
            
            self.blabel     = Label(self.frame, text = 'b =')
            self.bwidget    = Entry(self.frame, textvariable = self.b, justify = 'center', width = 10)
            self.bunits     = Label(self.frame, text = 'L/' + self.concunit[:-2])
            
            self.equalabel.grid(    row  = 2, column = 5,  padx = 2, pady = 1, sticky = 'WE')
            self.coeflabel.grid(    row  = 2, column = 6,  padx = 2, pady = 1, sticky = 'WE', columnspan = 6)
            self.eqwidget.grid(     row  = 3, column = 5,  padx = 1, pady = 5, sticky = 'S')
            self.qmaxlabel.grid(    row  = 3, column = 6,  padx = 0, pady = 5, sticky = 'SE')
            self.qmaxwidget.grid(   row  = 3, column = 7,  padx = 0, pady = 1)
            self.qmaxunits.grid(    row  = 3, column = 8,  padx = 0, pady = 1, sticky = 'W')
            self.blabel.grid(       row  = 3, column = 9,  padx = 0, pady = 1, sticky = 'E')
            self.bwidget.grid(      row  = 3, column = 10, padx = 0, pady = 1)
            self.bunits.grid(       row  = 3, column = 11, padx = 0, pady = 1, sticky = 'W')

        self.click_kinetic()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def Cancel(self):
        
        try:
            self.isotherm.set(self.sorption.isotherm)
            self.kinetic.set(self.sorption.kinetic)
            self.K.set(self.sorption.K)
            self.Koc.set(self.sorption.Koc)
            self.Kf.set(self.sorption.Kf)
            self.N.set(self.sorption.N)
            self.qmax.set(self.sorption.qmax)
            self.b.set(self.sorption.b)
            self.ksorp.set(self.sorption.ksorp)

        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()


        
class K_Estimator:

    def __init__(self, master, system, isotherm, coef):
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

        self.concunit   = system.concunit
        self.timeunit   = system.timeunit

        self.cinit      = DoubleVar(value = coef[0])
        self.qinit      = DoubleVar(value = coef[1])
        self.thalf      = DoubleVar(value = coef[2])
        self.ksorp      = DoubleVar(value = coef[3])

        self.coef       = coef

        self.isotherms      = ['Linear--Kd specified', 'Linear--Kocfoc', 'Freundlich', 'Langmuir']
        self.isotherm       = isotherm

        if self.isotherm == self.isotherms[0]:
            self.Kd = coef[4]
        if self.isotherm == self.isotherms[1]:
            self.Kd = 10 ** coef[4]*coef[5]
        if self.isotherm == self.isotherms[2]:
            self.Kf = coef[4]
            self.N  = coef[5]
        if self.isotherm == self.isotherms[3]:
            self.qmax = coef[4]
            self.b    = coef[5]

        self.epsilon = coef[6]
        self.rho     = coef[7]

    def make_widgets(self):

        self.instructions = Label(self.frame, text = ' Please input the following information to estimate the rate coefficients               ')

        self.leftcolumn   = Label(self.frame, text = ' ', width = 2)
        self.paracolumn   = Label(self.frame, text = ' ', width = 20)
        self.entrycolumn  = Label(self.frame, text = ' ', width = 12)
        self.unitcolumn   = Label(self.frame, text = ' ', width = 12)

        self.thalflabel   = Label(self.frame, text = ' Characteristic Half-life Time', width = 24)
        self.thalfentry   = Entry(self.frame, textvariable = self.thalf, width = 12, justify = 'center')
        self.thalfunit    = Label(self.frame, text = self.timeunit, width = 5)

        self.klabel       = Label(self.frame, text = 'Sorption rate coefficient ')
        self.kentry       = Label(self.frame, textvariable = self.ksorp, width = 12)

        self.ksorpunits   = Label(self.frame, text = self.timeunit +u'\u207B\u00b9')

        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')
        self.blank3       = Label(self.frame, text = ' ', width = 20)
        self.blank4       = Label(self.frame, text = ' ', width = 20)

        self.updatebutton = Button(self.frame, text = 'Calculate', width = 20, command = self.calculate)
        self.okbutton     = Button(self.frame, text = 'Save', width = 20, command = self.OK)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)

        self.instructions.grid(row = 0, column = 0, columnspan = 6)
        self.blank1.grid(      row = 1, column = 0, columnspan = 6)

        self.leftcolumn.grid(  row = 2, column = 0)
        self.paracolumn.grid(  row = 2, column = 1)
        self.entrycolumn.grid( row = 2, column = 2)
        self.unitcolumn.grid(  row = 2, column = 3)

        self.thalflabel.grid(      row = 3, column = 1, sticky = 'E')
        self.thalfentry.grid(      row = 3, column = 2)
        self.thalfunit.grid(       row = 3, column = 3, sticky = 'W')

        self.blank3.grid(              row = 4, column = 0, columnspan = 4)

        self.klabel.grid(               row = 5, column = 1, sticky = 'E')
        self.kentry.grid(               row = 5, column = 2)
        self.ksorpunits.grid(           row = 5, column = 3, sticky = 'W')

        self.blank1.grid(        row = 6)
        self.updatebutton.grid(  row = 7, columnspan = 4)
        self.okbutton.grid(      row = 8, columnspan = 4)
        self.cancelbutton.grid(  row = 9, columnspan = 4)
        self.blank2.grid(        row = 10)

        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        self.master.geometry()

        self.cancelflag = 0

    def calculate(self):

        if self.thalf.get() > 0:
            if self.isotherm == self.isotherms[0] or self.isotherm == self.isotherms[1]:
                self.ksorp.set(round((0.693/self.thalf.get()/(1+self.epsilon/self.rho/self.Kd)),4))
            elif self.isotherm == self.isotherms[2]:
                self.ksorp.set(round((0.693/self.thalf.get()/(1+self.epsilon/self.rho/(self.Kf))),4))
            elif self.isotherm == self.isotherms[3]:
                self.ksorp.set(round((0.693/self.thalf.get()/(1+self.epsilon/self.rho/(self.qmax*self.b/(1+self.b*self.cinit.get())))),4))
        else:
            tkmb.showerror(title = self.version, message = 'Please input a non-zero characteristic time and concentration.')
            self.focusbutton = self.okbutton
            self.master.tk.lift()

        self.updateksorption()

    def updateksorption(self):

        try: self.kentry.grid_forget()
        except: pass

        row = 4

        self.kentry.grid(               row = 5, column = 2, sticky = 'WE')

    def OK(self, event = None):

        self.master.tk.quit()

    def Cancel(self):

        try:
            self.cinit.set(self.coef[0])
            self.qinit.set(self.coef[1])
            self.thalf.set(self.coef[2])
            self.ksorp.set(self.coef[3])

        except: self.cancelflag = 1

        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
