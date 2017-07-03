#! /usr/bin/env python
#
#This file is used to make the GUI to get chemical properties of each layer.

import sys, os, cPickle as pickle

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar, FLAT, RAISED
from capsim_object_types import CapSimWindow, BC, IC, SolidIC
from capsim_functions    import kblriver, kbllake, tauwater, get_superfont, round_to_n
from benthicboundary     import KblEstimator, TauEstimator
import tkMessageBox as tkmb

class LayerConditions:
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
        self.bgcolor        = self.frame.cget('bg')
        self.top            = None

        self.chemicals      = system.chemicals
        self.layers         = system.layers
        self.sorptions      = system.sorptions
        self.matrices       = system.matrices
        self.dep            = system.dep

        self.CSTR_flag      = 0
        if system.dep == 'Deposition':
            matrix = system.matrices[system.layers[0].type_index]
            for chemical in self.chemicals:
                for component in matrix.components:
                    if system.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or system.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                        self.CSTR_flag      = 1
                    elif system.sorptions[component.name][chemical.name].kinetic == 'Transient':
                        self.CSTR_flag      = 1

        self.topBCtypes     = ['Fixed Concentration', 'Mass transfer', 'Finite mixed water column']
        self.botBCtypes     = ['Fixed Concentration', 'Flux-matching', 'Zero Gradient'  ]

        if system.adv == 'Steady flow' or system.adv == 'Tidal oscillation':
            self.U = system.Vdar
        else:
            self.U = 0

        self.concunit               = system.concunit
        self.lengthunit             = system.lengthunit
        self.timeunit               = system.timeunit

        try:
            self.bltype             = system.bltype
            self.blcoefs            = system.blcoefs
        except:
            self.bltype             = 'River'
            self.blcoefs            = {}
            self.blcoefs['vx']      = 1.
            self.blcoefs['n']       = 0.02
            self.blcoefs['hriver']  = 5.
            self.blcoefs['rh']      = 5.
            self.blcoefs['nu']      = 1e-6

            self.blcoefs['rhoair']  = 1.
            self.blcoefs['rhowater']= 1000.
            self.blcoefs['vwind']   = 5.
            self.blcoefs['hlake']   = 10.
            self.blcoefs['llake']   = 1000.

        try:
            self.taucoefs           = system.taucoefs
        except:
            self.taucoefs           = {}
            self.taucoefs['Q']      = 1.
            self.taucoefs['V']      = 100.
            self.taucoefs['h']      = 1.
            self.taucoefs['DOC']    = 0.
            self.taucoefs['Qevap']  = 0.
            self.taucoefs['Decay']  = 'None'
            self.taucoefs['Evap']   = 'None'

        if system.ICs == None:
            self.ICs = {}
            for layer in system.layers:
                self.ICs[layer.name] = {}
                for chemical in self.chemicals:
                    self.ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
        else:
            self.ICs        = system.ICs                

        if system.BCs == None:
            self.BCs = {}
            self.topBCtype      = StringVar(value = self.topBCtypes[0])
            self.botBCtype      = StringVar(value = self.topBCtypes[0])
            for chemical in self.chemicals:
                self.BCs[chemical.name] = BC(chemical.name, chemical.soluable)
        else:
            self.BCs        = system.BCs
            self.topBCtype  = StringVar(value = system.topBCtype) 
            self.botBCtype  = StringVar(value = system.botBCtype) 

        self.lengthunits    = system.lengthunits
        self.concunits      = system.concunits
        self.timeunits      = system.timeunits
        self.diffunits      = system.diffunits

        self.lengthunit     = system.lengthunit
        self.concunit       = system.concunit
        self.timeunit       = system.timeunit
        self.diffunit       = system.diffunit

        self.diff_factor = 1.
        self.k_factor    = 1.
        self.flux_factor = 0.001

        if self.lengthunit == self.lengthunits[0]:
            self.diff_factor = self.diff_factor * (10000**2)
            self.k_factor    = self.k_factor * 10000
            self.flux_factor = self.flux_factor / (10000**2)
        elif self.lengthunit == self.lengthunits[2]:
            self.diff_factor = self.diff_factor / (100**2)
            self.k_factor    = self.k_factor / 100
            self.flux_factor = self.flux_factor * (100**2)

        if self.diffunit == system.diffunits[0]:
            if self.timeunit == self.timeunits[1]:
                self.diff_factor = self.diff_factor * 60
            elif self.timeunit == self.timeunits[2]:
                self.diff_factor = self.diff_factor * 60 * 60
            elif self.timeunit == self.timeunits[3]:
                self.diff_factor = self.diff_factor * 60 * 60 * 24
            elif self.timeunit == self.timeunits[4]:
                self.diff_factor = self.diff_factor * 60 * 60 * 24 * 365.25
        else:
            if self.timeunit == self.timeunits[0]:
                self.diff_factor = self.diff_factor /365.25/24/60/60
            elif self.timeunit == self.timeunits[1]:
                self.diff_factor = self.diff_factor /365.25/24/60
            elif self.timeunit == self.timeunits[2]:
                self.diff_factor = self.diff_factor /365.25/24
            elif self.timeunit == self.timeunits[3]:
                self.diff_factor = self.diff_factor /365.25

    def make_widgets(self):
        """Makes the widgets for the GUI."""

        self.instructions   = Label(self.frame,  text  = 'Please input the boundary conditions and initial concentration profiles:        ')
        self.blank1         = Label(self.frame,  text  = '')
        self.blank2         = Label(self.frame,  text  = '')

        self.blankcolumn    = Label(self.frame, width = 2,  text = ' ' )
        self.layercolumn    = Label(self.frame, width = 10, text = ' ' )
        self.typecolumn     = Label(self.frame, width = 24, text = ' ' )
        self.paracolumn     = Label(self.frame, width = 20, text = ' ' )
        self.unitcolumn     = Label(self.frame, width = 8,  text = ' ' )
        self.endcolumn      = Label(self.frame, width = 4,  text = ' ' )
        
        self.layerlabel     = Label(self.frame, width = 6,  text = ' ' )
        self.typelabel      = Label(self.frame, width = 6,  text = 'Type' )
        self.paralabel      = Label(self.frame, width = 6,  text = 'Parameter' )
        self.unitlabel      = Label(self.frame, width = 6,  text = 'Unit' )
                
        self.blank1         = Label (self.frame, text = ' ')
        self.blank2         = Label (self.frame, text = ' ')
        self.blank3         = Label (self.frame, text = ' ')
        self.blank4         = Label (self.frame, text = ' ')
        
        #show the widgets on the grid

        self.instructions.grid( row = 0, column = 0, padx = 8, columnspan = 6, sticky = 'W')

        self.blankcolumn.grid(      row = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.layercolumn.grid(      row = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.typecolumn.grid(       row = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.paracolumn.grid(       row = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.unitcolumn.grid(       row = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)

        self.layerlabel.grid(       row = 2, column = 1, padx = 4, sticky = 'WE')
        self.typelabel.grid(        row = 2, column = 2, padx = 4, sticky = 'WE')
        self.paralabel.grid(        row = 2, column = 3, padx = 4, sticky = 'WE')
        self.unitlabel.grid(        row = 2, column = 4, padx = 4, sticky = 'WE')

        column = 5
        for chemical in self.chemicals:
            if chemical.soluable == 1:
                chemical.ICwidgets(self.frame, column)
                column = column + 1

        self.endcolumn.grid(        row = 2, column = column, sticky = 'WE', padx = 1, pady = 1)

        self.updateconditions(event = 1)    
        self.focusbutton = None

    def updateBCs(self, event = None):

        self.updateconditions()
        
    def updateconditions(self, event = None, *args):

        try:    
            self.topBClabel.grid_forget()
            self.topBCtwidget.grid_forget()
            self.botBClabel.grid_forget()
            self.botBCtwidget.grid_forget()
            self.blank3.grid_forget()
            self.blank4.grid_forget()
        except: pass

        try:
            self.Colabel.grid_forget()
            self.Counitlabel.grid_forget()
        except: pass

        try:
            self.klabel.grid_forget()
            self.kunitlabel.grid_forget()
        except: pass

        try:
            self.Cwlabel.grid_forget()
            self.Cwunitlabel.grid_forget()
        except: pass

        try:
            self.taulabel.grid_forget()
            self.tauunitlabel.grid_forget()
        except: pass

        try:
            self.Cblabel.grid_forget()
            self.Cbunitlabel.grid_forget()
        except: pass
        
        for chemical in self.chemicals:
            try:    self.BCs[chemical.name].remove_widgets()
            except: pass

        for chemical in self.chemicals:
            self.BCs[chemical.name].topBCtype = self.topBCtype.get()
            self.BCs[chemical.name].botBCtype = self.botBCtype.get()
        
        row = 4

        self.topblankrow_1  =Label(self.frame, width = 1,  text = '' )
        self.topblankrow_2  =Label(self.frame, width = 1,  text = '' )

        self.topblankrow_1.grid(row = 4,     column = 0, padx  = 4,  sticky = 'WE', pady = 4,     columnspan = 1)
        self.topblankrow_2.grid(row = 5,     column = 0, padx  = 4,  sticky = 'WE', pady = 4,     columnspan = 1)

        self.topBClabel     = Label(self.frame, width = 10,  text = 'Benthic' )
        self.topBCtwidget   = OptionMenu(self.frame, self.topBCtype, *self.topBCtypes, command = self.updateBCs)
        self.topBClabel.grid(           row = row, column = 1, sticky = 'WE', padx = 1, pady = 1, rowspan = 2)
        self.topBCtwidget.grid(         row = row, column = 2, sticky = 'WE', padx = 1, pady = 1, rowspan = 2)

        if self.topBCtype.get() == self.topBCtypes[0]:
            self.Colabel = Label(self.frame, width = 15,  text = 'Surface concentration')
            self.Counitlabel = Label(self.frame, width = 5,  text = self.concunit)
            self.Colabel.grid(       row = row, column = 3, sticky = 'WE', padx = 1, pady = 1, rowspan = 2)
            self.Counitlabel.grid(   row = row, column = 4, sticky = 'WE', padx = 1, pady = 1, rowspan = 2)

            column = 5
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    self.BCs[chemical.name].topboundarywidget(self.frame, row, column)
                    self.BCs[chemical.name].Co.trace('w', self.updateICs)
                    column = column + 1
            row = row + 2

        if self.topBCtype.get() == self.topBCtypes[1]:
            
            self.klabel      = Button(self.frame, width = 15,  text = 'Mass transfer coefficient', command = self.click_kbl)
            self.kunitlabel  = Label(self.frame,  width = 5,   text = 'cm/hr')#self.lengthunit + '/'+ self.timeunit)
            self.Cwlabel     = Label(self.frame,  width = 15,  text = 'Water concentration')
            self.Cwunitlabel = Label(self.frame,  width = 5,   text = self.concunit)
            self.klabel.grid(           row = row,     column = 3, sticky = 'WE', padx = 1, pady = 1)
            self.kunitlabel.grid(       row = row,     column = 4, sticky = 'WE', padx = 1, pady = 1)
            self.Cwlabel.grid(          row = row + 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
            self.Cwunitlabel.grid(      row = row + 1, column = 4, sticky = 'WE', padx = 1, pady = 1)

            column = 5
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    self.BCs[chemical.name].topboundarywidget(self.frame, row, column)
                    self.BCs[chemical.name].Cw.trace('w', self.updateICs)
                    column = column + 1
            row = row + 2

        if self.topBCtype.get() == self.topBCtypes[2]:

            if self.CSTR_flag == 0:
                self.klabel       = Button(self.frame,  width = 15,  text = 'Mass transfer coefficient', command = self.click_kbl)
                self.kunitlabel   = Label( self.frame,  width = 5,   text = 'cm/hr')
                self.taulabel     = Button(self.frame,  width = 15,  text = 'Water body retention time', command = self.click_tau)
                self.tauunitlabel = Label( self.frame,  width = 5,   text = self.timeunit)
                self.klabel.grid(           row = row,     column = 3, sticky = 'WE', padx = 1, pady = 0)
                self.kunitlabel.grid(       row = row,     column = 4, sticky = 'WE', padx = 1, pady = 1)
                self.taulabel.grid(         row = row + 1, column = 3, sticky = 'WE', padx = 1, pady = 0)
                self.tauunitlabel.grid(     row = row + 1, column = 4, sticky = 'WE', padx = 1, pady = 1)

                column = 5
                for chemical in self.chemicals:
                    if chemical.soluable == 1:
                        self.BCs[chemical.name].topboundarywidget(self.frame, row, column)
                        column = column + 1
                row = row + 2

            else:
                tkmb.showerror(title = 'Model Error', message = 'The water body CSTR model is not applicable for systems with deposition layer governing by non-linear equilibrium isotherm or transient sorption kinetics')
                self.topBCtype.set(self.topBCtypes[1])
                self.klabel      = Button(self.frame, width = 15,  text = 'Mass transfer coefficient', command = self.click_kbl)
                self.kunitlabel  = Label(self.frame,  width = 5,   text = 'cm/hr')
                self.Cwlabel     = Label(self.frame,  width = 15,  text = 'Water concentration')
                self.Cwunitlabel = Label(self.frame,  width = 5,   text = self.concunit)
                self.klabel.grid(           row = row,     column = 3, sticky = 'WE', padx = 1, pady = 1)
                self.kunitlabel.grid(       row = row,     column = 4, sticky = 'WE', padx = 1, pady = 1)
                self.Cwlabel.grid(          row = row + 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
                self.Cwunitlabel.grid(      row = row + 1, column = 4, sticky = 'WE', padx = 1, pady = 1)

                column = 5
                for chemical in self.chemicals:
                    if chemical.soluable == 1:
                        self.BCs[chemical.name].topboundarywidget(self.frame, row, column)
                        column = column + 1
                row = row + 2

        if self.layers[0].name != 'Deposition':
            self.blank3.grid( row = row)
            row = row + 1

        for layer in self.layers:
            row = row + 2

        self.updateICs()

        self.blank4.grid( row = row)
        row = row + 1

        self.botBClabel     = Label(self.frame, width = 10,  text = 'Underlying' )
        self.botBCtwidget   = OptionMenu(self.frame, self.botBCtype, *self.botBCtypes, command = self.updateBCs)
        self.botBClabel.grid(           row = row, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.botBCtwidget.grid(         row = row, column = 2, sticky = 'WE', padx = 1, pady = 1)

        #print(self.botBCtype.get())
            
        if self.botBCtype.get() == self.botBCtypes[0] or self.botBCtype.get() == self.botBCtypes[1]:
            
            self.Cblabel = Label(self.frame, width = 15,  text = 'Concentration')
            self.Cbunitlabel = Label(self.frame, width = 5,  text = self.concunit)
            self.Cblabel.grid(          row = row, column = 3, sticky = 'WE', padx = 1, pady = 1)
            self.Cbunitlabel.grid(      row = row, column = 4, sticky = 'WE', padx = 1, pady = 1)

            column = 5
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    self.BCs[chemical.name].botboundarywidget(self.frame, row, column)
                    column = column + 1
            row = row + 1
        else:
            row = row + 1

        self.blank1.grid(  row = row)
        self.focusbutton = None
        self.frame.update()
        self.master.geometry()
        self.master.center()

    def updateICs(self, event = None, *args):

        for layer in self.layers:
            try:    layer.remove_ICwidgets()
            except: pass
            for chemical in self.chemicals:
                try: self.ICs[layer.name][chemical.name].remove_widgets()
                except: pass

        if self.layers[0].name != 'Deposition':
            row = 7
        else:
            row = 6

        for layer in self.layers:
            layer.ICwidgets(self.frame, row, self.master, self.concunit)
            column = 5
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    self.ICs[layer.name][chemical.name].propertieswidgets(self.frame, row, column, layer.ICtype.get(), layer.name)
                    column = column + 1
            row = row + 2

        if self.layers[0].name == 'Deposition':
            for chemical in self.chemicals:
                if chemical.soluable == 1:
                    if self.topBCtype.get() == self.topBCtypes[0]:
                        self.ICs[self.layers[0].name][chemical.name].uniform.set(self.BCs[chemical.name].Co.get())
                    elif self.topBCtype.get() == self.topBCtypes[1]:
                        self.ICs[self.layers[0].name][chemical.name].uniform.set(self.BCs[chemical.name].Cw.get())
                    elif self.topBCtype.get() == self.topBCtypes[2]:
                        self.ICs[self.layers[0].name][chemical.name].uniform.set('Cw')

    def click_kbl(self, event = None):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(KblEstimator(self.top, self.version, self.fonttype, self.bltype, self.blcoefs))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:

                self.bltype = self.top.window.bltype.get()

                if self.top.window.bltype.get() == 'River':

                    self.blcoefs['vx']      = self.top.window.vx.get()
                    self.blcoefs['n']       = self.top.window.n.get()
                    self.blcoefs['hriver']  = self.top.window.hriver.get()
                    self.blcoefs['rh']      = self.top.window.rh.get()
                    self.blcoefs['nu']      = self.top.window.nu.get()

                    for chemical in self.chemicals:
                        if chemical.soluable == 1:
                            try:    self.BCs[chemical.name].k.set(round_to_n(kblriver(self.blcoefs['vx'], self.blcoefs['n'], self.blcoefs['hriver'], self.blcoefs['rh'], self.blcoefs['nu'], chemical.Dw/86400/365*self.diff_factor), 3))
                            except: tkmb.showerror(title = 'Math Error', message = 'The parameters you have entered produce a math error.  Please change the parameters and recalculate.')
                else:
                    self.blcoefs['rhoair']   = self.top.window.rhoair.get()
                    self.blcoefs['rhowater'] = self.top.window.rhowater.get()
                    self.blcoefs['vwind']    = self.top.window.vwind.get()
                    self.blcoefs['hlake']    = self.top.window.hlake.get()
                    self.blcoefs['llake']    = self.top.window.llake.get()

                    for chemical in self.chemicals:
                        if chemical.soluable == 1:
                            try:    self.BCs[chemical.name].k.set(round_to_n(kbllake(self.blcoefs['rhoair'],self.blcoefs['rhowater'],self.blcoefs['vwind'], self.blcoefs['hlake'], chemical.MW, self.blcoefs['llake']), 3))
                            except: tkmb.showerror(title = 'Math Error', message = 'The parameters you have entered produce a math error.  Please change the parameters and recalculate.')

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updateconditions()


    def click_tau(self, event = None):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(TauEstimator(self.top, self.version, self.fonttype, self.timeunit, self.lengthunit, self.chemicals, self.taucoefs,  self.BCs))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:

                self.taucoefs['Q']      = self.top.window.Q.get()
                self.taucoefs['V']      = self.top.window.V.get()
                self.taucoefs['h']      = self.top.window.h.get()
                self.taucoefs['Qevap']  = self.top.window.Qevap.get()
                self.taucoefs['DOC']    = self.top.window.doc.get()
                self.taucoefs['Decay']  = self.top.window.Decay.get()
                self.taucoefs['Evap']   = self.top.window.Evap.get()

                Q = self.taucoefs['Q'] - self.taucoefs['Qevap'] + self.taucoefs['V']/self.taucoefs['h']*self.U

                if self.dep == 'Deposition':
                    if self.lengthunit == 'cm':         kdep  = self.layers[0].h/100
                    elif self.lengthunit == u'\u03BCm': kdep  = self.layers[0].h/100/1000
                    else:                               kdep  = self.layers[0].h
                    matrix  = self.matrices[self.layers[0].type_index]
                    epsilon = self.matrices[self.layers[0].type_index].e
                    dep_rho = matrix.rho
                    dep_fraction = []
                    for component in matrix.components:
                        dep_fraction.append(component.mfraction)
                else:
                    kdep = 0
                    epsilon = 0
                    dep_rho = 0
                    dep_fraction = []

                for n in range(len(self.chemicals)):
                    chemical = self.chemicals[n]
                    self.BCs[chemical.name].kdecay = self.top.window.kdecays[n]
                    self.BCs[chemical.name].kevap  = self.top.window.kevaps[n]

                    if self.taucoefs['Evap'] == 'None':  kevap = 0
                    else:                                kevap = self.top.window.kevaps[n]
                    if self.taucoefs['Decay'] == 'None': kdecay = 0
                    else:                                kdecay = self.top.window.kdecays[n]

                    K = []
                    if self.dep == 'Deposition':
                        matrix  = self.matrices[self.layers[0].type_index]
                        for component in matrix.components:
                            if self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kd specified': K.append(self.sorptions[component.name][chemical.name].K)
                            elif self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kocfoc': K.append(10**self.sorptions[component.name][chemical.name].Koc)

                    try:    self.BCs[chemical.name].tau.set(round_to_n(tauwater(Q, self.taucoefs['DOC'], chemical.Kdoc, kdep, epsilon, dep_rho, dep_fraction, K, self.taucoefs['V'], self.taucoefs['h'], kevap, kdecay),3))
                    except: tkmb.showerror(title = 'Math Error', message = 'The parameters you have entered produce a math error.  Please change the parameters and recalculate.')

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updateconditions()


    def error_check(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error = 0

        if self.topBCtype.get() == 'Finite mixed water column':
            for chemical in self.chemicals:
                if self.BCs[chemical.name].tau.get() <= 0:
                    error = 1

        return error

    def warning(self):

        tkmb.showerror(title = self.version, message = 'The retention time must be positive values')
        self.focusbutton = None
        self.master.tk.lift()

def get_layerconditions(system, step):
    """Get specific parameters for the layers."""

    root = CapSimWindow(buttons = 1)
    root.make_window(LayerConditions(root, system))
    root.okbutton.focus_set()
    root.mainloop()

    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_layerconditions(root.window)
            for layer in system.layers:
                layer.get_layerconditions()
                layer.remove_ICwidgets()
                for chemical in system.chemicals:
                    if chemical.soluable == 1:
                        system.ICs[layer.name][chemical.name].remove_widgets()

            for chemical in system.chemicals:
                if chemical.soluable == 1:
                    chemical.remove_ICwidgets()
                    system.BCs[chemical.name].remove_widgets()
        else:
            system.ICs = None
            system.BCs = None
            for layer in system.layers:
                layer.ICtype = 'Uniform'
                layer.remove_ICwidgets()

    root.destroy()

    return system, step + root.step.get()


