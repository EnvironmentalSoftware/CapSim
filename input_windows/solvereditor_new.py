#!/usr/bin/env python
#
#This script is used to make the window for the output options from CapSim.

from Tkinter             import Frame, Label, Entry, Checkbutton, OptionMenu, StringVar, IntVar, DoubleVar, Button
from capsim_object_types import CapSimWindow
from capsim_functions    import consolidation, tidal
from math                import ceil

import os, tkMessageBox as tkmb

class SolverEditor:
    """Makes a window for the user to specify output options."""

    def __init__(self, master, system, ptype, ptotal, tvariable, delt, delz, players):
        """Constructor method."""

        self.master      = master
        self.tframe      = Frame(master.tframe)
        self.frame       = Frame(master.frame)
        self.bframe      = Frame(master.bframe)
        self.fonttype    = system.fonttype
        self.version     = system.version
        self.top         = None

        self.adv         = system.adv
        self.bio         = system.bio
        self.Dbiop       = system.Dbiop * self.diff_factor/86400/365
        self.Dbiopw      = system.Dbiopw * self.diff_factor/86400/365

        self.diffunit    = system.diffunit
        self.timeunit    = system.timeunit
        self.lengthunit  = system.lengthunit

        self.components  = [component.copy() for component in system.components]
        self.chemicals   = [chemical.copy() for chemical in system.chemicals]
        self.matrices    = [matrix.copy()   for matrix   in system.matrices]
        self.layers      = [layer.copy()    for layer    in system.layers]

        self.nlayers     = system.nlayers
        self.nchemicals  = system.nchemicals

        self.sorptions   = {}
        for component in self.components:
            self.sorptions[component.name] = {}
            for chemical in self.chemicals:
                self.sorptions[component.name][chemical.name] = system.sorptions[component.name][chemical.name].copy()

        self.BCs         = {}
        self.ICs         = {}
        for chemical in self.chemicals:
            self.BCs[chemical.name] = system.BCs[chemical.name].copy()

        for layer in self.layers:
            self.ICs[layer.name] = {}
            for chemical in self.chemicals:
                self.ICs[layer.name][chemical.name] = system.ICs[layer.name][chemical.name].copy()

        if system.con == 'Consolidation':
            self.kcon   = 2.3026 / system.t90
            self.Vcon0  = self.kcon * system.hcon
            self.U = system.Vdar + consolidation(0, self.Vcon0, self.kcon)
        else:
            self.U = system.Vdar

        if system.adv == 'Tidal oscillation': self.U = self.U + system.Vtidal

        self.non_linear_check = 0
        
        for component in system.component_list:
            for chemical in system.chemicals:
                self.non_linear_check = self.non_linear_check + (system.sorptions[component][chemical.name].isotherm == 'Freundlich')
                self.non_linear_check = self.non_linear_check + (system.sorptions[component][chemical.name].isotherm == 'Langmuir')

        if system.reactions is not None:
            for reaction in system.reactions:
                if sum([reactant.index for reactant in reaction.reactants]) > 1:
                    self.non_linear_check = self.non_linear_check + 1
            
        self.length_unit_converter = 1.
        self.time_unit_converter = 1.
        self.diff_unit_converter = 1.

        if   self.lengthunit == 'm' :        self.length_unit_converter = self.length_unit_converter / (0.01)**2
        elif self.lengthunit == u'\u03BCm':  self.length_unit_converter = self.length_unit_converter / (10000)**2

        elif self.timeunit == 's':           self.time_unit_converter = self.time_unit_converter *365.25*24*3600
        if   self.timeunit == 'min':         self.time_unit_converter = self.time_unit_converter *365.25*24*60
        elif self.timeunit == 'hr':          self.time_unit_converter = self.time_unit_converter *365.25*24
        elif self.timeunit == 'day':         self.time_unit_converter = self.time_unit_converter *365.25

        if self.diffunit == u'cm\u00B2/s':  self.diff_unit_converter = self.diff_unit_converter * 86400 * 365.25

        self.ptypes      = ['Uniform size',  'Uniform Number', 'User-defined']
        self.tvariables  = ['slowest layer', 'geometric mean', 'User-defined']

        self.ptype       = StringVar(value = ptype)
        self.tvariable   = StringVar(value = tvariable)
        self.ptotal      = IntVar(value = ptotal)                                #minimum grid points
        self.delt        = DoubleVar(value = delt)                               #minimumu time steps

        self.htot        = sum([layer.h for layer in self.layers])
        self.D           = []
        self.R           = []

        self.players     = [player for player in players]
        self.delz        = [dz for dz in delz]

        self.Cmax = {}
        for chemical in self.chemicals:
            self.Cmax[chemical.name] = max(max([self.ICs[ilayer.name][chemical.name].uniform for ilayer in self.layers]),
                                           max([self.ICs[ilayer.name][chemical.name].top     for ilayer in self.layers]),
                                           max([self.ICs[ilayer.name][chemical.name].bot     for ilayer in self.layers]),
                                           self.BCs[chemical.name].Co,
                                           self.BCs[chemical.name].Cw,
                                           self.BCs[chemical.name].Cb)

        for i in range(system.nlayers):
            self.D.append([])
            matrix = self.matrices[self.layers[i].type_index]
            for n in range(system.nchemicals):
                self.D[i].append(self.layers[i].get_D(self.chemicals[n].Dw * self.diff_unit_converter, self.U, matrix.e) )
                if self.layers[i].number < 2 and system.bio == 1:
                    self.D[i][n] = self.D[i][n] + system.Dbiopw
                    for component in matrix.components:
                        self.D[i][n] = self.D[i][n] + system.Dbiop * component.fraction * component.rho * self.sorptions[component.name][chemical.name].get_K(component, self.Cmax[chemical.name], self.Cmax[chemical.name])

        for i in range(system.nlayers):
            self.R.append([])
            matrix = self.matrices[self.layers[i].type_index]
            for n in range(self.nchemicals):
                chemical = self.chemicals[n]
                Kd_rho   = 0
                for component in matrix.components:
                    Kd_rho = Kd_rho + component.fraction * component.rho * self.sorptions[component.name][chemical.name].get_K(component, self.Cmax[chemical.name], self.Cmax[chemical.name])
                self.R[i].append((matrix.e *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc) ) + Kd_rho )/( 1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))

        self.cancelflag = 0


        if self.layers[0].number == 0:
            self.deplayersolveroptions = [LayerSolverOption(self.layers[0], self.players[0], self.D[0], self.U*self.length_unit_converter*self.time_unit_converter, self.R[0], self.length_unit_converter, self.timeunit)]
            self.dep = 1
        else:
            self.dep = 0
            self.deplayersolveroptions = []

        self.layersolveroptions = []

        for i in range(self.dep, self.nlayers):
            layer = self.layers[i]
            self.layersolveroptions.append(LayerSolverOption(layer, self.players[i], self.D[i], self.U*self.length_unit_converter*self.time_unit_converter, self.R[i], self.length_unit_converter))

    def make_widgets(self):
        """Make the widgets."""

        self.instructions     = Label(self.tframe, text = 'Please specify the grid and time step options for the system:  ')
        self.blank1           = Label(self.tframe, text = ' ')
        self.blank2           = Label(self.bframe, text = ' ')
        self.blank3           = Label(self.bframe, text = ' ')
        self.blank4           = Label(self.bframe, text = ' ')
        self.blank5           = Label(self.bframe, text = ' ')
        self.blank6           = Label(self.bframe, text = ' ')
        self.blank7           = Label(self.bframe, text = ' ')

        self.leftcolumn       = Label(self.tframe, text = '', font = 'courier 10', width = 5)
        self.layercolumn      = Label(self.tframe, text = '', font = 'courier 10', width = 10)
        self.thickcolumn      = Label(self.tframe, text = '', font = 'courier 10', width = 10)
        self.gridnumbercolumn = Label(self.tframe, text = '', font = 'courier 10', width = 12)
        self.gridsizecolumn   = Label(self.tframe, text = '', font = 'courier 10', width = 10)
        self.penumbercolumn   = Label(self.tframe, text = '', font = 'courier 10', width = 15)
        self.timestepcolumn   = Label(self.tframe, text = '', font = 'courier 10', width = 15)
        self.endcolumn        = Label(self.tframe, text = '', font = 'courier 10', width = 2)

        self.ptypelabel       = Label(self.tframe, text = 'Grid option:', width = 15)
        self.ptypewidget      = OptionMenu(self.tframe, self.ptype, *self.ptypes, command = self.updatesolvereditor)
        self.ptypewidget.config(width =15)
        self.ptotallabel      = Label(self.tframe, text = 'Total number of grids:', width = 15)
        self.ptotalwidget     = Label(self.tframe, textvariable = self.ptotal ,    width = 10, justify = 'center')
        self.ptotalentry      = Entry(self.tframe, textvariable = self.ptotal ,    width = 10, justify = 'center')

        self.tvariablelabel   = Label(self.tframe, text = 'Time step option:', width = 15)
        self.tvariablewidget  = OptionMenu(self.tframe, self.tvariable, *self.tvariables, command = self.updatesolvereditor)
        self.tvariablewidget.config(width =15)
        self.tsteplabel       = Label(self.tframe, text = 'Time step size (' + self.timeunit +'):',       width = 15)
        self.tstepwidget      = Label(self.tframe, textvariable = self.delt,       width = 10, justify = 'center')
        self.tstepentry       = Entry(self.tframe, textvariable = self.delt,       width = 10, justify = 'center')


        self.layerlabel       = Label(self.tframe, text = 'Layer')
        self.thicklabel       = Label(self.tframe, text = 'Thickness')
        self.gridnumberlabel  = Label(self.tframe, text = 'Number of grids')
        self.gridsizelabel    = Label(self.tframe, text = 'Grid size')
        self.gridPelabel      = Label(self.tframe, text = 'Max Peclet number')
        self.timesteplabel    = Label(self.tframe, text = 'CFL Time Step')

        self.thickunit        = Label(self.tframe, text = self.lengthunit)
        self.gridsizeunit     = Label(self.tframe, text = self.lengthunit)
        self.timestepunit     = Label(self.tframe, text = self.timeunit)

        self.botleftcolumn       = Label(self.frame, text = '', font = 'courier 10', width = 5)
        self.botlayercolumn      = Label(self.frame, text = '', font = 'courier 10', width = 10)
        self.botthickcolumn      = Label(self.frame, text = '', font = 'courier 10', width = 10)
        self.botgridnumbercolumn = Label(self.frame, text = '', font = 'courier 10', width = 12)
        self.botgridsizecolumn   = Label(self.frame, text = '', font = 'courier 10', width = 10)
        self.botpenumbercolumn   = Label(self.frame, text = '', font = 'courier 10', width = 15)
        self.bottimestepcolumn   = Label(self.frame, text = '', font = 'courier 10', width = 15)
        self.botendcolumn        = Label(self.frame, text = '', font = 'courier 10', width = 2)

        self.updatebutton     = Button(self.bframe, text  = 'Update',       width = 20, command = self.updatesolvereditor)
        self.okbutton         = Button(self.bframe, text  = 'OK',           width = 20, command = self.OK)
        self.cancelbutton     = Button(self.bframe, text  = 'Cancel',       width = 20, command = self.Cancel)

        #show the widgets that don't change on the grid

        row = 0

        self.instructions.grid(     row = row,  column = 0, sticky = 'W' , padx = 8, columnspan = 7)

        row = 1
        self.leftcolumn.grid(       row =  row, column = 0, sticky = 'WE', padx = 2)
        self.layercolumn.grid(      row =  row, column = 1, sticky = 'WE', padx = 2)
        self.thickcolumn.grid(      row =  row, column = 2, sticky = 'WE', padx = 2)
        self.gridnumbercolumn.grid( row =  row, column = 3, sticky = 'WE', padx = 2)
        self.gridsizecolumn.grid(   row =  row, column = 4, sticky = 'WE', padx = 2)
        self.penumbercolumn.grid(   row =  row, column = 5, sticky = 'WE', padx = 2)
        self.timestepcolumn.grid(   row =  row, column = 6, sticky = 'WE', padx = 2)
        self.endcolumn.grid(        row =  row, column = 7, sticky = 'WE', padx = 2)

        row = 2
        self.ptypelabel.grid(       row =  row, column = 0, sticky = 'E',  padx = 2, columnspan = 2)
        self.ptypewidget.grid(      row =  row, column = 2, sticky = 'W',  padx = 2, columnspan = 2)
        self.ptotallabel.grid(      row =  row, column = 4, sticky = 'E', padx = 2, columnspan = 2)

        row = 3
        self.tvariablelabel.grid(   row =  row, column = 0, sticky = 'E',  padx = 2, columnspan = 2)
        self.tvariablewidget.grid(  row =  row, column = 2, sticky = 'W',  padx = 2, columnspan = 2)
        self.tsteplabel.grid(       row =  row, column = 4, sticky = 'E', padx = 2, columnspan = 2)

        row = 4
        self.blank1.grid(           row =  row, column = 0, sticky = 'WE', padx = 2, columnspan = 7)

        row = 5
        self.layerlabel.grid(       row =  row, column = 1, sticky = 'WE', padx = 2)
        self.thicklabel.grid(       row =  row, column = 2, sticky = 'WE', padx = 2)
        self.gridnumberlabel.grid(  row =  row, column = 3, sticky = 'WE', padx = 2)
        self.gridsizelabel.grid(    row =  row, column = 4, sticky = 'WE', padx = 2)
        self.gridPelabel.grid(      row =  row, column = 5, sticky = 'WE', padx = 2)
        self.timesteplabel.grid(    row =  row, column = 6, sticky = 'WE', padx = 2)

        row = 6
        self.thickunit.grid(        row =  row, column = 2, sticky = 'WE', padx = 2)
        self.gridsizeunit.grid(     row =  row, column = 4, sticky = 'WE', padx = 2)
        self.timestepunit.grid(     row =  row, column = 6, sticky = 'WE', padx = 2)


        try:
            self.ptotalwidget.grid_forget()
            self.ptotalentry.grid_forget()
            self.tstepwidget.grid_forget()
            self.tstepentry.grid_forget()
        except: pass

        if self.ptype.get() == self.ptypes[2]:          self.ptotalwidget.grid( row =  2, column = 6, sticky = 'E', padx = 2)
        else:                                           self.ptotalentry.grid(  row =  2, column = 6, sticky = 'E', padx = 2)

        if self.tvariable.get() == self.tvariables[2]:  self.tstepentry.grid(   row =  3, column = 6, sticky = 'E', padx = 2)
        else:                                           self.tstepwidget.grid(  row =  3, column = 6, sticky = 'E', padx = 2)

        row = 7

        if self.dep == 1:
            layersolveroption =  self.deplayersolveroptions[0]
            layersolveroption.propertieswidgets(self.frame, row, self.ptype.get())
            row = row + 1

        for i in range (self.dep, self.nlayers):
            layersolveroption =  self.layersolveroptions[i-self.dep]
            layersolveroption.propertieswidgets(self.frame, row, self.ptype.get())
            row = row + 1

        self.botleftcolumn.grid(       row =  row, column = 0, sticky = 'WE', padx = 2)
        self.botlayercolumn.grid(      row =  row, column = 1, sticky = 'WE', padx = 2)
        self.botthickcolumn.grid(      row =  row, column = 2, sticky = 'WE', padx = 2)
        self.botgridnumbercolumn.grid( row =  row, column = 3, sticky = 'WE', padx = 2)
        self.botgridsizecolumn.grid(   row =  row, column = 4, sticky = 'WE', padx = 2)
        self.botpenumbercolumn.grid(   row =  row, column = 5, sticky = 'WE', padx = 2)
        self.bottimestepcolumn.grid(   row =  row, column = 6, sticky = 'WE', padx = 2)
        self.botendcolumn.grid(        row =  row, column = 7, sticky = 'WE', padx = 2)


        row = row + 1
        self.blank4.grid(        row = row)
        row = row + 1
        self.updatebutton.grid(  row = row, columnspan = 11)
        row = row + 1
        self.okbutton.grid(      row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(  row = row, columnspan = 11)
        row = row + 1
        self.blank5.grid(        row = row)

        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        self.master.geometry()
        self.master.center()

    def updatesolverparameters(self):

        if self.ptype.get() == self.ptypes[0]:
            delz      = self.htot / self.ptotal.get()
            for i in range(self.dep, self.nlayers):
                if self.layersolveroptions[i-self.dep].h / 5 < delz:
                    delz = self.layersolveroptions[i-self.dep].h / 5
                for n in range(self.nchemicals):
                    if self.U != 0:    delzcfl = 2. * self.D[i][n] / abs(self.U)
                    else:              delzcfl = 0
                    if delzcfl != 0 and delzcfl < delz: delz = delzcfl
            ptotal    = 0
            for i in range(self.dep, self.nlayers):
                if int(self.layers[i].h/delz) <> self.layers[i-self.dep].h/delz: self.layersolveroptions[i-self.dep].player.set(int(self.layers[i].h/delz)+1)
                else:                                                            self.layersolveroptions[i-self.dep].player.set(int(self.layers[i].h/delz))

                delz_temp = self.layers[i].h/ self.layersolveroptions[i-self.dep].player.get()
                if delz_temp > 1:  self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*1000)/1000)
                else:
                    j = 2
                    while delz_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*10**j)/10**j)
                try: self.layersolveroptions[i-self.dep].Pe = round(self.U*self.layersolveroptions[i-self.dep].delz/min(self.D[i]),2)
                except: self.layersolveroptions[i-self.dep].Pe = 0

                delt_temp = min([self.R[i][n] * self.layersolveroptions[i-self.dep].delz**2 / 2. / self.D[i][n] for n in range(self.nchemicals)])
                if delt_temp > 1:  self.layersolveroptions[i-self.dep].delt = (round(delt_temp, 3))
                else:
                    j = 2
                    while delt_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delt = (round(delt_temp, j))

                ptotal= ptotal + self.layersolveroptions[i-self.dep].player.get()

            self.ptotal.set(ptotal)

            if self.dep == 1:
                delz = min(layersolveroption.delz for layersolveroption in self.layersolveroptions)
                for n in range(self.nchemicals):
                    if self.U != 0:    delzcfl = 2. * self.D[0][n] / abs(self.U)
                    else:              delzcfl = 0
                    if delzcfl != 0 and delzcfl < delz: delz = delzcfl

                if delz > 1:  self.deplayersolveroptions[0].delz = (ceil(delz*1000)/1000)
                else:
                    j = 2
                    while delz/100 < 0.1**j:
                        j = j + 1
                    self.deplayersolveroptions[0].delz = (ceil(delz*10**j)/10**j)
                self.deplayersolveroptions[0].player.set(round(self.deplayersolveroptions[0].h/delz, 2))

        elif self.ptype.get() == self.ptypes[1]:
            players   = []
            for i in range(self.dep, self.nlayers):
                delz     = self.layersolveroptions[i-self.dep].h / float(self.ptotal.get()/(self.nlayers-self.dep))
                for n in range(self.nchemicals):
                    if self.U != 0:    delzcfl = 2. * self.D[i][n] / abs(self.U)
                    else:              delzcfl = 0
                    if delzcfl != 0 and delzcfl < delz: delz = delzcfl
                players.append(int(self.layersolveroptions[i-self.dep].h/delz))
            if max(players) > self.ptotal.get()/self.nlayers: self.ptotal.set(max(players) * (self.nlayers-self.dep))
            for i in range(self.dep, self.nlayers):
                self.layersolveroptions[i-self.dep].player.set(self.ptotal.get()/(self.nlayers-self.dep))

                delz_temp = self.layers[i].h/ self.layersolveroptions[i-self.dep].player.get()
                if delz_temp > 1:  self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*1000)/1000)
                else:
                    j = 2
                    while delz_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*10**j)/10**j)

                self.layersolveroptions[i-self.dep].Pe = round(self.U*self.layersolveroptions[i-self.dep].delz/min(self.D[i]),2)

                try:    delt_temp = min([self.R[i][n] * self.layersolveroptions[i-self.dep].delz**2 / 2. / self.D[i][n] for n in range(self.nchemicals)])
                except: delt_temp = 0
                if delt_temp > 1:  self.layersolveroptions[i-self.dep].delt = (round(delt_temp, 3))
                else:
                    j = 2
                    while delt_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delt = (round(delt_temp, j))

            if self.dep == 1:
                delz = min(layersolveroption.delz for layersolveroption in self.layersolveroptions)
                for n in range(self.nchemicals):
                    if self.U != 0:    delzcfl = 2. * self.D[0][n] / abs(self.U)
                    else:              delzcfl = 0
                    if delzcfl != 0 and delzcfl < delz: delz = delzcfl
                if delz > 1:  self.deplayersolveroptions[0].delz = (ceil(delz*1000)/1000)
                else:
                    j = 2
                    while delz/100 < 0.1**j:
                        j = j + 1
                    self.deplayersolveroptions[0].delz = (ceil(delz*10**j)/10**j)
                self.deplayersolveroptions[0].player.set(round(self.deplayersolveroptions[0].h/delz, 2))

        else:
            for i in range(self.dep, self.nlayers):

                if self.layersolveroptions[i-self.dep].player.get() < 5: self.layersolveroptions[i-self.dep].player.set(5)

                delz_temp = self.layers[i].h/ self.layersolveroptions[i-self.dep].player.get()
                if delz_temp > 1:  self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*1000)/1000)
                else:
                    j = 2
                    while delz_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delz = (ceil(delz_temp*10**j)/10**j)

                self.layersolveroptions[i-self.dep].Pe = round(self.U*self.layersolveroptions[i-self.dep].delz/min(self.D[i]),2)

                try:    delt_temp = min([self.R[i][n] * self.layersolveroptions[i-self.dep].delz**2 / 2. / self.D[i][n] for n in range(self.nchemicals)])
                except: delt_temp = 0
                if delt_temp > 1:  self.layersolveroptions[i-self.dep].delt = (round(delt_temp, 3))
                else:
                    j = 2
                    while delt_temp/100 < 0.1**j:
                        j = j + 1
                    self.layersolveroptions[i-self.dep].delt = (round(delt_temp, j))
            self.ptotal.set(sum([layersolveroption.player.get() for layersolveroption in self.layersolveroptions]))

            if self.dep == 1:
                delz_temp = self.layers[0].h/ self.deplayersolveroptions[0].player.get()
                if delz_temp > 1:  self.deplayersolveroptions[0].delz = (ceil(delz_temp*1000)/1000)
                else:
                    j = 2
                    while delz_temp/100 < 0.1**j:
                        j = j + 1
                    self.deplayersolveroptions[0].delz = (ceil(delz_temp*10**j)/10**j)

        if self.tvariable.get() == self.tvariables[0]:
            self.delt.set(min([self.layersolveroptions[i-self.dep].delt for i in range(self.dep, self.nlayers)]))
        elif self.tvariable.get() == self.tvariables[1]:
            delt_temp = (min([self.layersolveroptions[i-self.dep].delt for i in range(self.dep, self.nlayers)])*max([self.layersolveroptions[i-self.dep].delt for i in range(self.dep, self.nlayers)]))**0.5
            if delt_temp > 1:  self.delt.set(round(delt_temp, 3))
            else:
                j = 2
                while delt_temp/100 < 0.1**j:
                    j = j + 1
                self.delt.set(round(delt_temp, j))

        for i in range(self.dep, self.nlayers):
            self.delz[i]    = self.layersolveroptions[i-self.dep].delz
            self.players[i] = self.layersolveroptions[i-self.dep].player.get()

        if self.dep == 1:
            self.delz[0] = self.deplayersolveroptions[0].delz
            self.players[0] = self.deplayersolveroptions[0].player.get()

    def updatesolvereditor(self, event = None):

        self.updatesolverparameters()

        try:
            self.ptotalwidget.grid_forget()
            self.ptotalentry.grid_forget()
            self.tstepwidget.grid_forget()
            self.tstepentry.grid_forget()
        except: pass

        if self.ptype.get() == self.ptypes[2]:          self.ptotalwidget.grid( row =  2, column = 6, sticky = 'E', padx = 2)
        else:                                           self.ptotalentry.grid(  row =  2, column = 6, sticky = 'E', padx = 2)

        if self.tvariable.get() == self.tvariables[2]:  self.tstepentry.grid(   row =  3, column = 6, sticky = 'E', padx = 2)
        else:                                           self.tstepwidget.grid(  row =  3, column = 6, sticky = 'E', padx = 2)

        row = 7

        if self.dep == 1:
            layersolveroption =  self.deplayersolveroptions[0]
            layersolveroption.propertieswidgets(self.frame, row, self.ptype.get())
            row = row + 1

        for i in range (self.dep, self.nlayers):
            layersolveroption =  self.layersolveroptions[i-self.dep]
            layersolveroption.propertieswidgets(self.frame, row, self.ptype.get())
            row = row + 1

        self.botleftcolumn.grid(       row =  row, column = 0, sticky = 'WE', padx = 2)
        self.botlayercolumn.grid(      row =  row, column = 1, sticky = 'WE', padx = 2)
        self.botthickcolumn.grid(      row =  row, column = 2, sticky = 'WE', padx = 2)
        self.botgridnumbercolumn.grid( row =  row, column = 3, sticky = 'WE', padx = 2)
        self.botgridsizecolumn.grid(   row =  row, column = 4, sticky = 'WE', padx = 2)
        self.botpenumbercolumn.grid(   row =  row, column = 5, sticky = 'WE', padx = 2)
        self.bottimestepcolumn.grid(   row =  row, column = 6, sticky = 'WE', padx = 2)
        self.botendcolumn.grid(        row =  row, column = 7, sticky = 'WE', padx = 2)


        row = row + 1
        self.blank4.grid(        row = row)
        row = row + 1
        self.updatebutton.grid(  row = row, columnspan = 11)
        row = row + 1
        self.okbutton.grid(      row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(  row = row, columnspan = 11)
        row = row + 1
        self.blank5.grid(        row = row)

        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        self.master.geometry()
        self.master.center()


    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        #self.updatesolverparameters()

        self.master.tk.quit()


    def Cancel(self):

        self.cancelflag = 1

        if self.master.window.top is not None:
            self.master.open_toplevel()
        else:
            self.master.tk.quit()

class LayerSolverOption:

    def __init__(self, layer, player, D, U, R, lengthunitconverter, timeunit = 'yr'):

        self.name    = layer.name
        self.h       = layer.h
        delz_temp    = self.h/player

        if delz_temp > 1:  self.delz = (round(delz_temp, 3))
        else:
            j = 2
            while delz_temp/100 < 0.1**j:
                j = j + 1
            self.delz = (round(delz_temp, j))

        self.Pe      = round(U * self.delz / min(D) * lengthunitconverter, 2)
        delt_temp    = min([R[n] * self.delz**2 / 2. / D[n] * lengthunitconverter**2 for n in range(len(D))])

        if delt_temp > 1:  self.delt = (round(delt_temp, 3))
        else:
            j = 2
            while delt_temp/100 < 0.1**j:
                j = j + 1
            self.delt = (round(delt_temp, j))

        if layer.number == 0:
            self.dep = 1
            self.player  = DoubleVar(value = player)
            self.delt = 'NA'
        else:
            self.dep  = 0
            self.player  = IntVar(value = player)

        self.timeunit = timeunit

    def propertieswidgets(self, frame, row, ptype):

        try:
            self.layerlabel.grid_forget()
            self.thicknesslabel.grid_forget()
            self.playerlabel.grid_forget()
            self.playerentry.grid_forget()
            self.delzlabel.grid_forget()
            self.Pelabel.grid_forget()
            self.deltlabel.grid_forget()
        except:pass

        self.layerlabel     = Label(frame, width = 10,  justify = 'center', text = self.name)
        self.thicknesslabel = Label(frame, width = 10,  justify = 'center', text = str(self.h) + self.dep * ('(/'+self.timeunit+')'))

        self.playerlabel    = Label(frame, width = 10,  justify = 'center', textvariable = self.player)
        self.playerentry    = Entry(frame, width = 10,  justify = 'center', textvariable = self.player)

        self.delzlabel      = Label(frame, width = 10,  justify = 'center', text = str(self.delz))
        self.Pelabel        = Label(frame, width = 10,  justify = 'center', text = str(self.Pe))
        self.deltlabel      = Label(frame, width = 10,  justify = 'center', text = str(self.delt))

        self.layerlabel.grid(       row  = row, column = 1, padx = 2 ,pady = 1)
        self.thicknesslabel.grid(   row  = row, column = 2, padx = 2 ,pady = 1)

        if ptype == 'User-defined':   self.playerentry.grid(     row  = row, column = 3, padx = 2 ,pady = 1)
        else:                         self.playerlabel.grid(     row  = row, column = 3, padx = 2 ,pady = 1)

        self.delzlabel.grid(        row  = row, column = 4, padx = 2 ,pady = 1)
        self.Pelabel.grid(          row  = row, column = 5, padx = 2 ,pady = 1)
        self.deltlabel.grid(        row  = row, column = 6, padx = 2 ,pady = 1)
