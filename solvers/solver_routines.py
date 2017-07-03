#! /usr/bin/env python
#
#This file contains a variety of functions that are used collectively to
#simulate transport through a sediment cap system.  In essence the "System"
#object type that is built using the GUI or batch file is used to create an 
#instance of the "Parameters" class that lumps together the data for 
#discretization.  Based on the appropriate solver for the system, the 
#simulation is performed to ensure an accurate and stable solution.  The 
#details of each function are presented below.

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

import math, cPickle as pickle

from numpy               import matrix, array, linalg, zeros, transpose, interp, ceil, exp
from capsim_object_types import System, Layer, Chemical, BC, Reaction, Coefficient, SolidIC
from reactioneditor      import Reactant, Product
from capsim_functions    import consolidation, tidal, tauwater

class Parameters:
    """This object type creates the variables used for the finite 
    differencing to solve the transport equations for simulating a sediment
    cap.  The discretized matrix form of the differential equations used to
    solve for the unknown concentrations at the succeeding time step "Cn+1" 
    using the known concentration "Cn" is: 
        
    A * Cn+1 + a = B * Cn + b.

    Parameter instances can obtain the following attributes:

    z    -- the array of the grid points
    A    -- the matrix defined above representing the coefficients for the
            unknown values at the next time step
    B    -- the matrix defined above that is multiplied by the 
            concentrations at the previous time step
    a    -- the vector defined above containing boundary values and forcing
            functions, it also contains the non-linear terms at the next time step
    b    -- the vector defined above containing boundary values and forcing 
            functions, it also contains the non-linear terms at the next time step

    p    -- a list of the boundary points of each of the layers
    U    -- the Darcy velocity at the time step (scalar)
    D    -- an array of the diffusion coefficients at each grid point
    R    -- an array of the retardation factors at each grid point
    elam -- an array of the product of porosity and decay rate at each 
            grid point
    delz -- an array of the grid spacing in each layer
    delt -- the time step size
    """
    
    def __init__(self, system):
        """Constructor method.  Gets parameters from a "System" instance that
        is either built by the GUI or the user (for batch processing) and uses
        them to build a finite difference approximation for cap simulation.
        Variable definitions can be found in the "capsim_object_types" file."""
        
        self.bio            = 0
        self.con            = 0
        self.sorp           = 0
        self.tidal          = 0
        self.reac           = 0
        self.nsolidchemicals= 0
        self.varit          = 0

        self.Vdar           = system.Vdar
        
        self.nlayers        = system.nlayers
        self.nchemicals     = system.nchemicals
        self.component_list = system.component_list
        self.topBCtype      = system.topBCtype
        self.botBCtype      = system.botBCtype

        try:    self.tstart     = system.tstart
        except: self.tstart     = 0

        try:    self.timeoption = system.timeoption
        except: self.timeoption = 'Crank-Nicolson'

        self.outputsteps    = system.outputsteps
        self.discrete       = system.discrete
        self.ptotal         = system.ptotal
        self.delt           = system.delt
        self.delto          = system.delt
        self.ptype          = system.ptype
        self.tvariable      = system.tvariable
        self.delz           = system.delz
        self.players        = system.players
        self.tidalsteps     = system.tidalsteps
        self.nloption       = system.nonlinear
        self.nlerror        = system.nlerror
        self.averageoption  = system.averageoption
        self.depsteps       = system.depgrid
        self.depgrid        = 1

        if system.dep == 'Deposition':  self.steps      = self.depsteps
        else:                           self.steps      = 0

        if self.averageoption == 'Average' and self.depsteps <= self.tidalsteps:
            self.steps      = self.tidalsteps

        self.tfinal         = system.tfinal + self.delt * (1 + self.steps)
        self.tfinal_ori     = system.tfinal

        self.lengthunits    = system.lengthunits
        self.concunits      = system.concunits
        self.timeunits      = system.timeunits
        self.diffunits      = system.diffunits

        self.lengthunit     = system.lengthunit
        self.concunit       = system.concunit
        self.timeunit       = system.timeunit
        self.diffunit       = system.diffunit

        self.taucoefs       = system.taucoefs

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

        if self.timeunit == self.timeunits[0]:
            self.k_factor = self.k_factor / 60 / 60
        elif self.timeunit == self.timeunits[1]:
            self.k_factor = self.k_factor / 60
        elif self.timeunit == self.timeunits[3]:
            self.k_factor = self.k_factor * 24
        elif self.timeunit == self.timeunits[4]:
            self.k_factor = self.k_factor * 24 * 365.25

        if system.layers[0].name == 'Deposition':
            self.dep            = 1
            self.layers         = [layer.copy() for layer   in system.layers[1:]]
            self.delzdep        = self.delz[0]
            self.delz           = self.delz[1:]
            self.depplayer      = self.players[0]
            self.players        = self.players[1:]
            self.deplayer       = [system.layers[0].copy()]
            self.Vdep           = system.Vdep
            self.deplayer[0].h  = self.Vdep * self.tfinal
        else:
            self.dep            = 0
            self.layers         = [layer.copy() for layer   in system.layers]
            self.deplayer       = []
            self.Vdep           = 0
            self.depplayer      = 0

        self.depcheck     = 'None'
        self.toppoints    = 1
        if self.dep == 1:
            self.depsize = self.delzdep

        self.nlayers = len(self.layers)

        for i in range(len(self.players)):
            self.players[i] = int(self.players[i])

        self.layertot           = self.layers

        self.chemicals      = [chemical.copy() for chemical  in system.chemicals]
        self.solidchemicals = []
        self.matrices       = [matrix.copy()   for matrix    in system.matrices]
        self.components     = [component.copy()for component in system.components]
        self.reactions      = [reaction.copy() for reaction  in system.reactions]

        self.ncomponents    = len(self.components)

        if self.concunits[:3].count(self.concunit) == 0:
            for chemical in self.chemicals: chemical.MW = 1

        for chemical in self.chemicals:
            chemical.Dw = chemical.Dw * self.diff_factor

        self.layerchemicals     = []
        self.deplayerchemicals  = []


        self.sorptions      = {}
        self.coefficients   = {}
        self.BCs            = {}
        self.ICs            = {}

        # Convert the transient sorption to kinetic reactions
        for component in self.components:
            self.sorptions[component.name] = {}
            for chemical in self.chemicals:
                self.sorptions[component.name][chemical.name] = system.sorptions[component.name][chemical.name].copy()
                if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                    for layer in self.layers:
                        for layer_component in self.matrices[layer.type_index].components:
                            if layer_component.name == component.name:   self.sorp = 1

                if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                    if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich':
                        self.sorptions[component.name][chemical.name].ksorp   = self.sorptions[component.name][chemical.name].ksorp
                        self.sorptions[component.name][chemical.name].kdesorp = self.sorptions[component.name][chemical.name].kdesorp/(chemical.MW**(1.-1./self.sorptions[component.name][chemical.name].N))

                    elif self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                        self.sorptions[component.name][chemical.name].ksorp = self.sorptions[component.name][chemical.name].ksorp/chemical.MW

                    self.solidchemicals.append(Chemical(self.nchemicals+self.nsolidchemicals, soluable = 0))
                    self.solidchemicals[-1].get_solid_chemical(component.name, chemical.name, chemical.MW)
                    self.nsolidchemicals = self.nsolidchemicals + 1

                    self.reactions.append(Reaction(len(self.reactions)))
                    reactants = Reactant(1)
                    products =  Product(1)

                    if self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kd specified' or self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kocfoc':
                        reactants.get_dynamic_sorption(chemical, 1)
                        products.get_dynamic_sorption(self.solidchemicals[-1])
                        self.reactions[-1].get_dynamic_sorption(component.name +  '_' + chemical.name + '_sorption', component.name, reactants, products, 'Fundamental')

                    elif self.sorptions[component.name][chemical.name].isotherm == 'Freundlich':
                        reactants.get_dynamic_sorption(chemical, 1)
                        products.get_dynamic_sorption(self.solidchemicals[-1])
                        self.reactions[-1].get_dynamic_sorption(component.name +  '_' + chemical.name + '_sorption', component.name, reactants, products, 'Fundamental')

                    elif self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                        reactants.get_dynamic_sorption(chemical, self.sorptions[component.name][chemical.name].qmax/chemical.MW)
                        products.get_dynamic_sorption(self.solidchemicals[-1])
                        self.reactions[-1].get_dynamic_sorption(component.name +  '_' + chemical.name + '_sorption', component.name, reactants, products, 'Langmuir')

                    self.reactions.append(Reaction(len(self.reactions)))
                    reactants = Reactant(1)
                    products =  Product(1)
                    if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich':
                        reactants.get_dynamic_desorption(self.solidchemicals[-1], 1./self.sorptions[component.name][chemical.name].N)
                        products.get_dynamic_desorption(chemical)
                        self.reactions[-1].get_dynamic_sorption(component.name +  '_' + chemical.name + '_desorption', component.name, reactants, products, 'User-defined')
                    else:
                        reactants.get_dynamic_desorption(self.solidchemicals[-1], 1)
                        products.get_dynamic_desorption(chemical)
                        self.reactions[-1].get_dynamic_sorption(component.name +  '_' + chemical.name + '_desorption', component.name, reactants, products, 'Fundamental')

        for reaction in self.reactions:
            for reactant in reaction.reactants:
                reactant.coef = - reactant.coef

        if system.adv == 'Period oscillation':
            self.tidal      = 1
            self.U          = self.Vdar
            self.Vtidal     = system.Vtidal
            self.ptidal     = system.ptidal
        elif system.adv == 'Steady flow':
            self.U = self.Vdar
            self.tidalsteps = 0
        else:
            self.U = 0
            self.tidalsteps = 0

        self.biomix                 = system.biomix
        self.biolayerinit           = 0
        self.mixcomponents          = []
        self.mixcomponentslist      = []
        self.nmixcomponents         = 0
        self.mixsolidchemicalslist  = []
        self.mixsolidchemicals      = []
        self.solidcomponents        = []

        if system.bio == 'Uniform' or system.bio == 'Depth-dependent':

            self.bio     = 1
            self.biotype = system.bio
            self.sigma   = system.sigma
            if system.bio == 'Depth-dependent':
                if self.dep == 1:
                    self.hbio    = sum([layer.h for layer in self.layers]) + self.tfinal*self.deplayer[0].h
                else:
                    self.hbio    = sum([layer.h for layer in self.layers])
            else:
                self.hbio    = system.hbio

            self.Dbiop   = system.Dbiop * self.diff_factor/86400/365
            self.Dbiopw  = system.Dbiopw * self.diff_factor/86400/365

            if self.biomix == 1:
                H = 0
                for j in range(len(self.layers)):
                    layer = self.layers[j]
                    if self.hbio > H:
                        for component in self.matrices[layer.type_index].components:
                            if self.mixcomponentslist.count(component.name) == 0:
                                self.mixcomponentslist.append(component.name)
                                self.mixcomponents.append(component.copy())
                                for solidchemical in self.solidchemicals:
                                    if component.name == solidchemical.component_name:
                                        if self.mixsolidchemicalslist.count(solidchemical.name) == 0:
                                            self.mixsolidchemicals.append(solidchemical.copy())
                                            self.mixsolidchemicalslist.append(solidchemical.name)
                    if self.hbio > H + layer.h:
                        if j < len(self.layers) - 1:
                            self.biolayerinit = self.biolayerinit + 1
                    H = H + layer.h

                if self.dep == 1:
                    for component in self.matrices[self.deplayer[0].type_index].components:
                        if self.mixcomponentslist.count(component.name) == 0:
                            self.mixcomponentslist.append(component.name)
                            self.mixcomponents.append(component.copy())
                            for solidchemical in self.solidchemicals:
                                if component.name == solidchemical.component_name:
                                    if self.mixsolidchemicalslist.count(solidchemical.name) == 0:
                                        self.mixsolidchemicals.append(solidchemical.copy())
                                        self.mixsolidchemicalslist.append(solidchemical.name)

        if system.con == 'Consolidation':
            self.con    = 1
            self.kcon   = 2.3026 / system.t90
            self.Vcon0  = system.hcon * self.kcon
            self.U      = self.Vdar + self.Vcon0

        self.U_plus_1 = self.U

        self.chemical_list = [chemical.name for chemical in (self.chemicals + self.solidchemicals)]
        self.solidchemical_list = [chemical.name for chemical in (self.solidchemicals)]

        # Load the parameters of chemical informations in layers

        layer_num = 0
        if self.biolayerinit > 0:
            for i in range(self.biolayerinit+1):
                layer = self.layers[i]
                layer.nchemicals            = self.nchemicals
                layer.nsolidchemicals       = 0
                layer.nsolidcomponents      = 0
                layer.chemicals             = [chemical.copy() for chemical in self.chemicals]
                layer.solidchemicals        = []
                layer.solidcomponents       = []
                layer.components            = [component.copy() for component in self.mixcomponents]
                layer.component_list        = [component.name   for component in self.mixcomponents]
                layer.init_components       = [component.copy() for component in self.matrices[layer.type_index].components]
                layer.init_component_list   = [component.name   for component in self.matrices[layer.type_index].components]
                layer.lreactions            = []
                layer.nlreactions           = []

                for solidchemical in self.mixsolidchemicals:
                    layer.solidchemicals.append(solidchemical.copy())
                    layer.solidchemicals[-1].component_name = solidchemical.component_name
                    layer.solidchemicals[-1].chemical_name  = solidchemical.chemical_name
                    layer.solidchemicals[-1].component_index = self.mixcomponentslist.index(layer.solidchemicals[-1].component_name)
                    layer.chemicals.append(solidchemical.copy())
                    layer.nsolidchemicals = layer.nsolidchemicals + 1
                    layer.nchemicals      = layer.nchemicals + 1

                layer_num = layer_num + 1

        for i in range(layer_num, self.nlayers):
            layer = self.layers[i]
            layer.nchemicals            = self.nchemicals
            layer.nsolidchemicals       = 0
            layer.chemicals             = [chemical.copy() for chemical in self.chemicals]
            layer.solidchemicals        = []
            layer.components            = [component.copy() for component in self.matrices[layer.type_index].components]
            layer.component_list        = [component.name for component in layer.components]
            layer.init_components       = [component.copy() for component in self.matrices[layer.type_index].components]
            layer.init_component_list   = [component.name for component in layer.components]
            layer.lreactions            = []
            layer.nlreactions           = []

            for solidchemical in self.solidchemicals:
                for component in layer.components:
                     if component.name == solidchemical.component_name:
                        layer.solidchemicals.append(solidchemical.copy())
                        layer.solidchemicals[-1].component_name = solidchemical.component_name
                        layer.solidchemicals[-1].chemical_name  = solidchemical.chemical_name
                        layer.solidchemicals[-1].component_index = layer.components.index(component)
                        layer.chemicals.append(solidchemical.copy())
                        layer.nsolidchemicals = layer.nsolidchemicals + 1
                        layer.nchemicals      = layer.nchemicals + 1

        if self.dep == 1:
            if self.biomix == 1:
                self.deplayer[0].nchemicals             = self.nchemicals
                self.deplayer[0].nsolidchemicals        = 0
                self.deplayer[0].chemicals              = [chemical.copy() for chemical in self.chemicals]
                self.deplayer[0].solidchemicals         = []
                self.deplayer[0].components             = [component.copy() for component in self.mixcomponents]
                self.deplayer[0].component_list         = [component.name   for component in self.mixcomponents]
                self.deplayer[0].init_components        = [component.copy() for component in self.matrices[self.deplayer[0].type_index].components]
                self.deplayer[0].init_component_list    = [component.name   for component in self.matrices[self.deplayer[0].type_index].components]
                self.deplayer[0].lreactions             = []
                self.deplayer[0].nlreactions            = []

                for solidchemical in self.mixsolidchemicals:
                    self.deplayer[0].solidchemicals.append(solidchemical.copy())
                    self.deplayer[0].solidchemicals[-1].component_name = solidchemical.component_name
                    self.deplayer[0].solidchemicals[-1].chemical_name  = solidchemical.chemical_name
                    self.deplayer[0].solidchemicals[-1].component_index = self.mixcomponentslist.index(self.deplayer[0].solidchemicals[-1].component_name)
                    self.deplayer[0].chemicals.append(solidchemical.copy())
                    self.deplayer[0].nsolidchemicals = self.deplayer[0].nsolidchemicals + 1
                    self.deplayer[0].nchemicals      = self.deplayer[0].nchemicals + 1

                self.deplayer[0].chemical_list      = [chemical.name for chemical in self.deplayer[0].chemicals]
                self.deplayer[0].solidchemical_list = [chemical.name for chemical in self.deplayer[0].solidchemicals]

            else:
                self.deplayer[0].nchemicals             = self.nchemicals
                self.deplayer[0].nsolidchemicals        = 0
                self.deplayer[0].chemicals              = [chemical.copy() for chemical in self.chemicals]
                self.deplayer[0].solidchemicals         = []
                self.deplayer[0].components             = [component.copy() for component in self.matrices[self.deplayer[0].type_index].components]
                self.deplayer[0].component_list         = [component.name   for component in self.deplayer[0].components]
                self.deplayer[0].init_components        = [component.copy() for component in self.matrices[self.deplayer[0].type_index].components]
                self.deplayer[0].init_component_list    = [component.name   for component in self.deplayer[0].components]
                self.deplayer[0].lreactions             = []
                self.deplayer[0].nlreactions            = []

                for solidchemical in self.solidchemicals:
                    for component in self.deplayer[0].components:
                        if component.name == solidchemical.component_name:
                            self.deplayer[0].solidchemicals.append(solidchemical.copy())
                            self.deplayer[0].solidchemicals[-1].component_name = solidchemical.component_name
                            self.deplayer[0].solidchemicals[-1].chemical_name  = solidchemical.chemical_name
                            self.deplayer[0].solidchemicals[-1].component_index = self.deplayer[0].components.index(component)
                            self.deplayer[0].nsolidchemicals = self.deplayer[0].nsolidchemicals + 1
                            self.deplayer[0].nchemicals      = self.deplayer[0].nchemicals + 1
                            self.deplayer[0].chemicals.append(solidchemical.copy())

                self.deplayer[0].chemical_list      = [chemical.name for chemical in self.deplayer[0].chemicals]
                self.deplayer[0].solidchemical_list = [chemical.name for chemical in self.deplayer[0].solidchemicals]



        for layer in self.deplayer + self.layers:
            self.coefficients[layer.name] = {}
            for reaction in self.reactions:
                if reaction.name.count('_sorption') == 1:
                    self.coefficients[layer.name][reaction.name] = Coefficient(layer, reaction)
                    for component in layer.components:
                        if component.name == reaction.component:
                            self.coefficients[layer.name][reaction.name].get_dynamic_sorption(self.sorptions[component.name][reaction.reactants[0].name].ksorp)
                elif reaction.name.count('_desorption') == 1:
                    self.coefficients[layer.name][reaction.name] = Coefficient(layer, reaction)
                    for component in layer.components:
                        if component.name == reaction.component:
                            self.coefficients[layer.name][reaction.name].get_dynamic_sorption(self.sorptions[component.name][reaction.products[0].name].kdesorp)
                else:
                    self.coefficients[layer.name][reaction.name] = system.coefficients[layer.name][reaction.name].copy()

        for layer in self.layers:
            layer.chemical_list         = [chemical.name for chemical in layer.chemicals]
            layer.solidchemical_list    = [chemical.name for chemical in layer.solidchemicals]

            for reaction in self.reactions:
                if self.coefficients[layer.name][reaction.name].lam > 0:
                    indeces    = [reactant.index for reactant in reaction.reactants]
                    if sum(indeces) == 1 and indeces.count(1.) == 1 and reaction.model != 'Langmuir':
                        layer.lreactions.append(reaction.copy())
                        for chemical in (layer.lreactions[-1].reactants + layer.lreactions[-1].products):
                            chemical.count = layer.chemical_list.index(chemical.name)
                        for chemical in (layer.lreactions[-1].reactants):
                            if chemical.index == 1: layer.lreactions[-1].key = chemical
                    else:
                        layer.nlreactions.append(reaction.copy())
                        for chemical in (layer.nlreactions[-1].reactants + layer.nlreactions[-1].products):
                            chemical.count = layer.chemical_list.index(chemical.name)
                        self.reac = 1

        if self.dep == 1:
            for reaction in self.reactions:
                if self.coefficients[self.deplayer[0].name][reaction.name].lam > 0:
                    indeces    = [reactant.index for reactant in reaction.reactants]
                    if sum(indeces) == 1 and indeces.count(1.) == 1 and reaction.model != 'Langmuir':
                        self.deplayer[0].lreactions.append(reaction.copy())
                        for chemical in (self.deplayer[0].lreactions[-1].reactants + self.deplayer[0].lreactions[-1].products):
                            chemical.count = self.deplayer[0].chemical_list.index(chemical.name)
                        for chemical in (self.deplayer[0].lreactions[-1].reactants):
                            if chemical.index == 1: self.deplayer[0].lreactions[-1].key = chemical
                    else:
                        self.deplayer[0].nlreactions.append(reaction.copy())
                        for chemical in (self.deplayer[0].nlreactions[-1].reactants + self.deplayer[0].nlreactions[-1].products):
                            chemical.count = self.deplayer[0].chemical_list.index(chemical.name)
                        self.reac = 1


        for chemical in self.chemicals:
            self.BCs[chemical.name] = system.BCs[chemical.name].copy()
            self.BCs[chemical.name].k  = self.BCs[chemical.name].k * self.k_factor
            self.BCs[chemical.name].Co = self.BCs[chemical.name].Co/chemical.MW
            self.BCs[chemical.name].Cb = self.BCs[chemical.name].Cb/chemical.MW
            self.BCs[chemical.name].Cw = self.BCs[chemical.name].Cw/chemical.MW

        for chemical in self.solidchemicals:
            self.BCs[chemical.name] = BC(chemical.name, 0)

        for layer in self.deplayer + self.layers:
            self.ICs[layer.name] = {}
            for chemical in self.chemicals:
                self.ICs[layer.name][chemical.name] = system.ICs[layer.name][chemical.name].copy()
                self.ICs[layer.name][chemical.name].uniform = self.ICs[layer.name][chemical.name].uniform / chemical.MW
                self.ICs[layer.name][chemical.name].top = self.ICs[layer.name][chemical.name].top / chemical.MW
                self.ICs[layer.name][chemical.name].bot = self.ICs[layer.name][chemical.name].bot / chemical.MW

            for chemical in self.solidchemicals:
                if [component.name for component in system.matrices[layer.type_index].components].count(chemical.component_name) >= 1:
                    self.ICs[layer.name][chemical.name] = system.SolidICs[layer.name][chemical.component_name][chemical.chemical_name].copy()
                    self.ICs[layer.name][chemical.name].uniform = self.ICs[layer.name][chemical.name].uniform / chemical.MW
                else:
                    self.ICs[layer.name][chemical.name] = SolidIC(layer.name, chemical.component_name, chemical.chemical_name)
                    self.ICs[layer.name][chemical.name].uniform = 0 / chemical.MW


        self.Cmax = {}
        for chemical in (self.chemicals + self.solidchemicals):
            self.Cmax[chemical.name] = max(self.BCs[chemical.name].Co, self.BCs[chemical.name].Cw, self.BCs[chemical.name].Cb)

        for layer in (self.deplayer + self.layers):
            for chemical in layer.chemicals:
                try:
                    if self.Cmax[chemical.name] < max(self.ICs[layer.name][chemical.name].uniform, self.ICs[layer.name][chemical.name].top, self.ICs[layer.name][chemical.name].bot):
                        self.Cmax[chemical.name] = max(self.ICs[layer.name][chemical.name].uniform, self.ICs[layer.name][chemical.name].top, self.ICs[layer.name][chemical.name].bot)
                except: pass

    def make_uniform_grid(self):

        """Creates a uniform grid for assessing contaminant transport in a cap
        using the depth in each layer with a spacing of approximately delzmax.
        The actual spacing is set up such that the boundary of each layer falls
        exactly on a grid point.  Creates a list with the depth of each grid
        point "z," the actual grid spacing in each layer "delz," the list number
        of the boundary points "p."
        """

        self.z      = []
        self.p      = []
        self.ptot   = []
        self.cp     = []
        self.cptot  = []
        self.cpL    = []
        self.cptotL = []

        self.z.append(0)
        self.p.append(0)
        self.ptot.append(0)
        self.cp.append(0)
        self.cptot.append(0)

        for i in range(len(self.layers)):
            layer = self.layers[i]
            self.p.append(self.p[-1] + self.players[i])
            self.ptot.append(self.ptot[-1] + self.players[i])
            self.cp.append(self.cp[-1] + self.players[i]* layer.nchemicals)
            self.cptot.append(self.cptot[-1] + self.players[i]* layer.nchemicals)
            for j in range (self.p[-2], self.p[-1]):
                self.z.append(self.z[-1]+self.delz[i])

        if self.dep == 1:
            points       = int(round(self.depplayer*self.tfinal,10))-1
            self.zdep    = [-self.delzdep]
            for i in range(0, points):
                self.zdep.append(self.zdep[-1] - self.delzdep)
            self.zdep.reverse()
            self.pdep = [len(self.zdep)]
            self.bdep = [len(self.zdep) * self.deplayer[0].nchemicals]

        else:
            self.zdep = []
            self.pdep = [0]
            self.bdep = [0]

        if self.bio == 1:            self.update_bioturbation()

    def get_initial_concentrations(self):
        """Uses the list of "Layer" objects and their concentrations to fill in
        the values of concentration at each grid point "C0" """

        C0 = []
        for j in range(len(self.p) - 1):
            layer = self.layers[j]
            if layer.ICtype == 'Uniform':
                for i in range(self.p[j], self.p[j + 1]):
                    for chemical in (self.chemicals):
                        C0.append(self.ICs[layer.name][chemical.name].uniform)
                    for solidchemical in layer.solidchemicals:
                        try: C0.append(self.ICs[layer.name][solidchemical.name].uniform)
                        except: C0.append(0)

            elif layer.ICtype == 'Linear':
                for i in range (self.p[j],self.p[j + 1]):
                    for chemical in (self.chemicals):
                        top = self.ICs[layer.name][chemical.name].top
                        bot = self.ICs[layer.name][chemical.name].bot
                        C0.append(top + (bot-top)/(self.z[self.p[j + 1]] - self.z[self.p[j]])*(self.z[i]-self.z[self.p[j]]))
                    for solidchemical in layer.solidchemicals:
                        try: C0.append(self.ICs[layer.name][solidchemical.name].uniform)
                        except: C0.append(0)

        if self.layers[-1].ICtype == 'Uniform':
            for chemical in (self.chemicals):
                C0.append(self.ICs[self.layers[-1].name][chemical.name].uniform)
            for solidchemical in self.layers[-1].solidchemicals:
                try:    C0.append(self.ICs[self.layers[-1].name][solidchemical.name].uniform)
                except: C0.append(0)

        elif self.layers[-1].ICtype == 'Linear':
            for chemical in (self.chemicals):
                C0.append(self.ICs[self.layers[-1].name][chemical.name].bot)
            for solidchemical in self.layers[-1].solidchemicals:
                try:    C0.append(self.ICs[self.layers[-1].name][solidchemical.name].uniform)
                except: C0.append(0)

        return C0

    def get_initial_component_fractions(self):
        """Uses the list of "Layer" objects and their concentrations to fill in
        the values of concentration at each grid point "C0" """

        Fis0 = {}
        for component in (self.components):
            Fis0[component.name] = []
            if self.layers[0].init_component_list.count(component.name) == 0: Fis0[component.name].append(0)
            else:                                                             Fis0[component.name].append(self.layers[0].init_components[self.layers[0].init_component_list.index(component.name)].fraction)
            for j in range(len(self.p) - 1):
                layer = self.layers[j]
                for i in range(self.p[j]+1, self.p[j + 1]+1):
                    if layer.init_component_list.count(component.name) == 0:  Fis0[component.name].append(0)
                    else:                                                     Fis0[component.name].append(layer.init_components[layer.init_component_list.index(component.name)].fraction)

        Fis0L = {}
        for component in (self.components):
            Fis0L[component.name] = [Fi for Fi in Fis0[component.name]]
            for j in range(len(self.p) - 1):
                layer = self.layers[j]
                if layer.init_component_list.count(component.name) == 0:     Fis0L[component.name][self.p[j]] = 0
                else:                                                        Fis0L[component.name][self.p[j]] = layer.init_components[layer.init_component_list.index(component.name)].fraction

        Fis0M = {}
        for component in (self.components):
            Fis0M[component.name] = [Fi for Fi in Fis0[component.name]]
            for j in range(len(self.p) - 1):
                layer = self.layers[j]
                if layer.init_component_list.count(component.name) == 0:     Fis0M[component.name][self.p[j]] = 0
                else:                                                        Fis0M[component.name][self.p[j]] = layer.init_components[layer.init_component_list.index(component.name)].fraction

        return Fis0, Fis0L, Fis0M

    def make_grid_es_rhos(self, Fis, FisL):

        """Makes the list of values of "R" for the finite difference equations
        for the grid "z" with boundary points "p" and concentrations "Cn." """

        self.es_plus_1      = []
        self.rhos_plus_1    = []

        self.es_plus_1.append(0)
        self.rhos_plus_1.append(0)
        for component in self.components:
            self.es_plus_1[-1]      = self.es_plus_1[-1]    + Fis[component.name][0] * component.e
            self.rhos_plus_1[-1]    = self.rhos_plus_1[-1]  + Fis[component.name][0] * component.rho

        for j in range(len(self.ptot) - 1):
            for i in range(self.ptot[j]+1, self.ptot[j + 1] + 1):
                self.es_plus_1.append(0)
                self.rhos_plus_1.append(0)
                for component in self.components:
                    self.es_plus_1[-1]   = self.es_plus_1[-1]   + Fis[component.name][i] * component.e
                    self.rhos_plus_1[-1] = self.rhos_plus_1[-1] + Fis[component.name][i] * component.rho

        self.esL_plus_1     = [e for e in self.es_plus_1]
        self.rhosL_plus_1   = [rho for rho in self.rhos_plus_1]

        for j in range(len(self.ptot) - 1):
            self.esL_plus_1[self.ptot[j]]   = 0
            self.rhosL_plus_1[self.ptot[j]] = 0
            for component in self.components:
                self.esL_plus_1[self.ptot[j]]   = self.esL_plus_1[self.ptot[j]]   + FisL[component.name][self.ptot[j]] * component.e
                self.rhosL_plus_1[self.ptot[j]] = self.rhosL_plus_1[self.ptot[j]] + FisL[component.name][self.ptot[j]] * component.rho

        if self.bio == 1:
            self.esL_plus_1[self.pbio]   = 0
            self.rhosL_plus_1[self.pbio] = 0
            for component in self.components:
                self.esL_plus_1[self.pbio]   = self.esL_plus_1[self.pbio]   + FisL[component.name][self.pbio] * component.e
                self.rhosL_plus_1[self.pbio] = self.rhosL_plus_1[self.pbio] + FisL[component.name][self.pbio] * component.rho

    def make_grid_Rs(self, Cn, Fis_plus_1, FisL_plus_1):

        """Makes the list of values of "R" for the finite difference equations
        for the grid "z" with boundary points "p" and concentrations "Cn." """

        self.Rs_plus_1  = []
        self.Ss_plus_1  = []
        self.Ks_plus_1  = []

        num     = self.nchemicals

        layer  = self.layertot[0]
        for n in range(num):
            chemical = (self.chemicals)[n]
            Kd_rho   = 0
            for component in layer.components:
                Kd_rho = Kd_rho + Fis_plus_1[component.name][0] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
            self.Rs_plus_1.append(self.es_plus_1[0] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
            self.Ss_plus_1.append(self.es_plus_1[0] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
            self.Ks_plus_1.append(Kd_rho)
        for solidchemical in layer.solidchemicals:
            self.Rs_plus_1.append(Fis_plus_1[layer.components[solidchemical.component_index].name][0] * layer.components[solidchemical.component_index].rho)
            self.Ss_plus_1.append(0)
            self.Ks_plus_1.append(Fis_plus_1[layer.components[solidchemical.component_index].name][0] * layer.components[solidchemical.component_index].rho)

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for ii in range(self.ptot[j + 1] - 1 - self.ptot[j]):
                i = ii + 1
                for n in range(num):
                    chemical = self.chemicals[n]
                    Kd_rho   = 0
                    for component in layer.components:
                        Kd_rho = Kd_rho + Fis_plus_1[component.name][self.ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[self.cptot[j]+i*layer.nchemicals+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
                    self.Rs_plus_1.append(self.es_plus_1[self.ptot[j]+i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
                    self.Ss_plus_1.append(self.es_plus_1[self.ptot[j]+i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                    self.Ks_plus_1.append(Kd_rho)
                for solidchemical in layer.solidchemicals:
                    self.Rs_plus_1.append(Fis_plus_1[layer.components[solidchemical.component_index].name][self.ptot[j]+i] * layer.components[solidchemical.component_index].rho)
                    self.Ss_plus_1.append(0)
                    self.Ks_plus_1.append(Fis_plus_1[layer.components[solidchemical.component_index].name][self.ptot[j]+i] * layer.components[solidchemical.component_index].rho)

            if j < len(self.ptot) - 2:
                i = self.ptot[j+1]
                layer = self.layertot[j]
                for n in range(num):
                    chemical = self.chemicals[n]
                    Kd_rho   = 0
                    for component in layer.components:
                        Kd_rho = Kd_rho + Fis_plus_1[component.name][i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[self.cptot[j + 1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
                    self.Rs_plus_1.append(self.es_plus_1[i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
                    self.Ss_plus_1.append(self.es_plus_1[i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                    self.Ks_plus_1.append(Kd_rho)
                for solidchemical in self.layertot[j+1].solidchemicals:
                    self.Rs_plus_1.append(Fis_plus_1[solidchemical.component_name][i] * self.components[self.component_list.index(solidchemical.component_name)].rho)
                    self.Ss_plus_1.append(0)
                    self.Ks_plus_1.append(Fis_plus_1[solidchemical.component_name][i] * self.components[self.component_list.index(solidchemical.component_name)].rho)

        layer  = self.layertot[-1]
        for n in range(num):
            chemical = self.chemicals[n]
            Kd_rho   = 0
            for component in layer.components:
                Kd_rho = Kd_rho + Fis_plus_1[component.name][-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[self.cptot[-1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
            self.Rs_plus_1.append(self.es_plus_1[-1] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
            self.Ss_plus_1.append(self.es_plus_1[-1] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
            self.Ks_plus_1.append(Kd_rho)
        for solidchemical in layer.solidchemicals:
            self.Rs_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][-1] * layer.components[solidchemical.component_index].rho)
            self.Ss_plus_1.append(0)
            self.Ks_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][-1] * layer.components[solidchemical.component_index].rho)


        self.RsL_plus_1  = []
        self.SsL_plus_1  = []
        self.KsL_plus_1  = []

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j + 1] - self.ptot[j]):
                for n in range(num):
                    chemical = self.chemicals[n]
                    Kd_rho   = 0
                    for component in layer.components:
                        Kd_rho = Kd_rho + FisL_plus_1[component.name][self.ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[self.cptot[j]+i*layer.nchemicals+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
                    self.RsL_plus_1.append(self.esL_plus_1[self.ptot[j]+i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
                    self.SsL_plus_1.append(self.esL_plus_1[self.ptot[j]+i] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                    self.KsL_plus_1.append(Kd_rho)
                for solidchemical in layer.solidchemicals:
                    self.RsL_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][self.ptot[j]+i] * layer.components[solidchemical.component_index].rho)
                    self.SsL_plus_1.append(0)
                    self.KsL_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][self.ptot[j]+i] * layer.components[solidchemical.component_index].rho)

        layer  = self.layertot[-1]
        for n in range(num):
            chemical = self.chemicals[n]
            Kd_rho   = 0
            for component in layer.components:
                Kd_rho = Kd_rho + FisL_plus_1[component.name][-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[self.cptot[-1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)
            self.RsL_plus_1.append(self.esL_plus_1[-1] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)) + Kd_rho )
            self.SsL_plus_1.append(self.esL_plus_1[-1] *(1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
            self.KsL_plus_1.append(Kd_rho)
        for solidchemical in layer.solidchemicals:
            self.RsL_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][-1] * layer.components[solidchemical.component_index].rho)
            self.SsL_plus_1.append(0)
            self.KsL_plus_1.append(FisL_plus_1[layer.components[solidchemical.component_index].name][-1] * layer.components[solidchemical.component_index].rho)


    def make_grid_Us(self):
        """Makes the list of values of "D" for the finite difference equations
        for the grid "z" with boundary points "p." """

        self.Us_plus_1  = []

        layer  = self.layertot[0]
        for chemical in (self.chemicals):
            self.Us_plus_1.append(   self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
        for n in range(self.layertot[0].nsolidchemicals):
            self.Us_plus_1.append(0)

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j]+1, self.ptot[j + 1]):
                for chemical in (self.chemicals):
                    self.Us_plus_1.append(self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                for n in range(self.layertot[j].nsolidchemicals):
                    self.Us_plus_1.append(0)
            if j < len(self.ptot) - 2:
                for chemical in (self.chemicals):
                    self.Us_plus_1.append(self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                for n in range(self.layertot[j+1].nsolidchemicals):
                    self.Us_plus_1.append(0)

        for chemical in (self.chemicals):
            self.Us_plus_1.append(self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
        for n in range(self.layertot[-1].nsolidchemicals):
            self.Us_plus_1.append(0)

        self.UsL_plus_1 = []
        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j], self.ptot[j + 1]):
                for chemical in (self.chemicals):
                    self.UsL_plus_1.append(self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
                for n in range(self.layertot[j].nsolidchemicals):
                    self.UsL_plus_1.append(0)

        layer  = self.layertot[-1]
        for chemical in (self.chemicals):
            self.UsL_plus_1.append(self.U_plus_1 * (1 + layer.doc/(10**6) * 10**(chemical.Kdoc)))
        for n in range(self.layertot[-1].nsolidchemicals):
            self.UsL_plus_1.append(0)


    def make_grid_Dbiops(self):
        """Makes the list of values of "D" for the finite difference equations
        for the grid "z" with boundary points "p." """

        self.Dbiops_plus_1  = []
        self.Dbiops_plus_1.append(0)

        for j in range(len(self.ptot) - 1):
            for i in range(self.ptot[j]+1, self.ptot[j + 1]+1):
                self.Dbiops_plus_1.append(0)

        if self.biotype == 'Depth-dependent':
            for n in range (self.pbio + 1):
                self.Dbiops_plus_1[n] = self.Dbiops_plus_1[n] + self.Dbiop * exp(-(self.z[n]-self.z[0])**2/2/self.sigma**2)
        else:
            for n in range (self.pbio + 1):
                self.Dbiops_plus_1[n] = self.Dbiops_plus_1[n] + self.Dbiop

        self.DbiopsL_plus_1  = [Dbiop for Dbiop in self.Dbiops_plus_1]
        self.DbiopsL_plus_1[self.pbio] = 0


    def make_grid_Ds(self):
        """Makes the list of values of "D" for the finite difference equations
        for the grid "z" with boundary points "p." """

        self.Ds_plus_1   = []

        Dn = 0

        layer  = self.layertot[0]
        for chemical in (self.chemicals):
            self.Ds_plus_1.append(layer.get_D(chemical.Dw, self.Us_plus_1[Dn], self.es_plus_1[0]))
            Dn = Dn + 1
        for n in range(self.layertot[0].nsolidchemicals):
            self.Ds_plus_1.append(layer.get_D(0, 0, self.es_plus_1[0]))
            Dn = Dn + 1

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j] + 1, self.ptot[j + 1]):
                for chemical in (self.chemicals):
                    self.Ds_plus_1.append(layer.get_D(chemical.Dw, self.Us_plus_1[Dn], self.es_plus_1[i]))
                    Dn = Dn + 1
                for n in range(self.layertot[j].nsolidchemicals):
                    self.Ds_plus_1.append(layer.get_D(0, 0, self.es_plus_1[i]))
                    Dn = Dn + 1
            if j < len(self.ptot)-2:
                for chemical in (self.chemicals):
                    self.Ds_plus_1.append(layer.get_D(chemical.Dw, self.Us_plus_1[Dn], self.es_plus_1[i]))
                    Dn = Dn + 1
                for n in range(self.layertot[j+1].nsolidchemicals):
                    self.Ds_plus_1.append(layer.get_D(0, 0, self.es_plus_1[i]))
                    Dn = Dn + 1

        layer  = self.layertot[-1]
        for chemical in (self.chemicals):
            self.Ds_plus_1.append(layer.get_D(chemical.Dw, self.UsL_plus_1[Dn], self.esL_plus_1[-1]))
            Dn = Dn + 1
        for n in range(self.layertot[-1].nsolidchemicals):
            self.Ds_plus_1.append(layer.get_D(0, 0, self.esL_plus_1[-1]))
            Dn = Dn + 1

        self.Dws_plus_1 = [D for D in self.Ds_plus_1]

        if self.bio == 1:
            if self.biotype == 'Uniform':
                for n in range (self.cpbio + self.layertot[self.layerbio].nchemicals):
                    self.Ds_plus_1[n] = self.Ds_plus_1[n] + self.Dbiopw * self.Ss_plus_1[n]
            else:
                for j in range(len(self.ptot) - 1):
                    for i in range(self.ptot[j + 1] - self.ptot[j]):
                        for n in range(len(self.layertot[j].chemicals)):
                            if i <= self.pbio and i < self.ptot[-1]:
                                self.Ds_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n] = self.Ds_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n] + self.Dbiopw * self.Ss_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n]* exp(-(self.z[self.ptot[j]+i]-self.z[0])**2/2/self.sigma**2)

                if self.ptot[-1] <= self.pbio:
                    for n in range(len(self.layertot[-1].chemicals)):
                        self.Ds_plus_1[self.cptot[-1]+n] = self.Ds_plus_1[self.cptot[-1]+n] + self.Dbiopw * self.Ss_plus_1[self.cptot[-1]+n]* exp(-(self.z[self.ptot[-1]]-self.z[0])**2/2/self.sigma**2)

        self.DsL_plus_1   = []

        Dn = 0

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j], self.ptot[j + 1]):
                for chemical in (self.chemicals):
                    self.DsL_plus_1.append(layer.get_D(chemical.Dw, self.UsL_plus_1[Dn], self.esL_plus_1[i]))
                    Dn = Dn + 1
                for n in range(self.layertot[j].nsolidchemicals):
                    self.DsL_plus_1.append(layer.get_D(0, 0, self.esL_plus_1[i]))
                    Dn = Dn + 1

        layer  = self.layertot[-1]
        for chemical in (self.chemicals):
            self.DsL_plus_1.append(layer.get_D(chemical.Dw, self.UsL_plus_1[Dn], self.esL_plus_1[-1]))
            Dn = Dn + 1
        for n in range(self.layertot[-1].nsolidchemicals):
            self.DsL_plus_1.append(layer.get_D(0, 0, self.esL_plus_1[-1]))
            Dn = Dn + 1

        self.DwsL_plus_1 = [D for D in self.DsL_plus_1]

        if self.bio == 1:
            if self.biotype == 'Uniform':
                for n in range (self.cpbio):
                    self.DsL_plus_1[n] = self.DsL_plus_1[n] + self.Dbiopw * self.SsL_plus_1[n] #+ self.Dbiop * self.KsL_plus_1[n]
            else:
                for j in range(len(self.ptot) - 1):
                    for i in range(self.ptot[j + 1] - self.ptot[j]):
                        for n in range(len(self.layertot[j].chemicals)):
                            if i < self.pbio and i < self.ptot[-1]:
                                self.DsL_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n] = self.DsL_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n] + self.Dbiopw * self.SsL_plus_1[self.cptot[j]+i*self.layertot[j].nchemicals+n]* exp(-(self.z[self.ptot[j]+i]-self.z[0])**2/2/self.sigma**2)


    def make_grid_elams(self, Fis):
        """Makes the list of values of "elam" for the finite difference 
        equations for the grid "z" with boundary points "p." """

        self.elams_plus_1 = zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals])

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j + 1] - self.ptot[j]):
                #i = ii + 1
                for reaction in layer.lreactions:
                    n = reaction.key.count
                    if reaction.name.count('_sorption') == 1:
                        component_name = reaction.component
                        e = self.components[self.component_list.index(component_name)].e * Fis[component_name][self.ptot[j]+i]
                        for chemical in (reaction.reactants + reaction.products):
                            nn = chemical.count
                            self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n] = (self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n]
                                                                                                                          +chemical.coef * self.coefficients[layer.name][reaction.name].lam * e)
                    elif reaction.name.count('_desorption') == 1:
                        component_name = reaction.component
                        rho = self.components[self.component_list.index(component_name)].rho * Fis[component_name][self.ptot[j]+i]
                        for chemical in (reaction.reactants + reaction.products):
                            nn = chemical.count
                            self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n] = (self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n]
                                                                                                                          + chemical.coef * self.coefficients[layer.name][reaction.name].lam * rho)
                    else:
                        for chemical in (reaction.reactants + reaction.products):
                            nn = chemical.count
                            self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n] = self.elams_plus_1[self.cptot[j]+i*layer.nchemicals+nn, self.cptot[j]+i*layer.nchemicals+n] \
                                                                                                                                            + chemical.coef * self.coefficients[layer.name][reaction.name].lam * self.es_plus_1[self.ptot[j]+i]


    def make_grid_rates(self, Cn, Fis):

        """Makes the list of values of "rates" for the finite difference
        equations for the grid "z" with boundary points "p." """

        self.rates      = zeros(self.cptot[-1] + self.layertot[-1].nchemicals)

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j + 1] - self.ptot[j]):
                #i = ii + 1
                for reaction in layer.nlreactions:
                    if reaction.model == 'Langmuir':
                        component_name = reaction.component
                        e   = self.components[self.component_list.index(component_name)].e * Fis[component_name][self.ptot[j]+i]
                        rate = (self.coefficients[layer.name][reaction.name].lam * Cn[self.cptot[j]+i*layer.nchemicals+reaction.reactants[0].count] * e
                                *(reaction.reactants[0].index - Cn[self.cptot[j]+i*layer.nchemicals+reaction.products[0].count]))
                    else:
                        if reaction.name.count('_desorption') == 1:
                            component_name = reaction.component
                            rho = self.components[self.component_list.index(component_name)].rho * Fis[component_name][self.ptot[j]+i]
                            rate = self.coefficients[layer.name][reaction.name].lam * rho
                            for reactant in reaction.reactants:
                                if     Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] <= 0:    rate = 0
                                else:                                                               rate = rate * Cn[self.cptot[j]+i*layer.nchemicals+reactant.count]**reactant.index
                        else:
                            rate = self.coefficients[layer.name][reaction.name].lam * self.es_plus_1[self.ptot[j]+i]
                            for reactant in reaction.reactants:
                                if     Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] <= 0:    rate = 0
                                else:                                                               rate = rate * Cn[self.cptot[j]+i*layer.nchemicals+reactant.count]**reactant.index

                    for chemical in (reaction.reactants + reaction.products):
                        self.rates[self.cptot[j]+i*layer.nchemicals+chemical.count]      = self.rates[self.cptot[j]+i*layer.nchemicals+chemical.count] + rate * chemical.coef

    def make_grid_rates_plus_1(self, Cn , Fis):

        """Makes the list of values of "rates" for the finite difference
        equations for the grid "z" with boundary points "p." """

        self.rates_plus_1      = zeros(self.cptot[-1] + self.layertot[-1].nchemicals)

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j + 1] - self.ptot[j]):
                #i = ii + 1
                for reaction in layer.nlreactions:
                    if reaction.model == 'Langmuir':
                        component_name = reaction.component
                        e   = self.components[self.component_list.index(component_name)].e * Fis[component_name][self.ptot[j]+i]
                        rate = (self.coefficients[layer.name][reaction.name].lam * Cn[self.cptot[j]+i*layer.nchemicals+reaction.reactants[0].count] * e
                                *(reaction.reactants[0].index - Cn[self.cptot[j]+i*layer.nchemicals+reaction.products[0].count]))
                    else:
                        if reaction.name.count('_desorption') == 1:
                            component_name = reaction.component
                            rho = self.components[self.component_list.index(component_name)].rho * Fis[component_name][self.ptot[j]+i]
                            rate = self.coefficients[layer.name][reaction.name].lam * rho
                            for reactant in reaction.reactants:
                                if     Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] <= 0:    rate = 0
                                else:                                                               rate = rate * Cn[self.cptot[j]+i*layer.nchemicals+reactant.count]**reactant.index
                        else:
                            rate = self.coefficients[layer.name][reaction.name].lam * self.es_plus_1[self.ptot[j]+i]
                            for reactant in reaction.reactants:
                                if     Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] <= 0:    rate = 0
                                else:                                                               rate = rate * Cn[self.cptot[j]+i*layer.nchemicals+reactant.count]**reactant.index

                    for chemical in (reaction.reactants + reaction.products):
                        self.rates_plus_1[self.cptot[j]+i*layer.nchemicals+chemical.count]      = self.rates_plus_1[self.cptot[j]+i*layer.nchemicals+chemical.count] + rate * chemical.coef


    def make_grid_rates_diff(self, Cn, Fis):

        """Makes the list of values of "rates differentiation" for the newton's medthod finite difference
        equations for the grid "z" with boundary points "p." """


        self.rates_diff  = zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals])

        for j in range(len(self.ptot) - 1):
            layer  = self.layertot[j]
            for i in range(self.ptot[j + 1] - self.ptot[j]):
                #i = ii + 1
                for reaction in layer.nlreactions:
                    diff = zeros(layer.nchemicals)
                    if reaction.model == 'Langmuir':
                        component_name = reaction.component
                        e   = self.components[self.component_list.index(component_name)].e * Fis[component_name][self.ptot[j]+i]
                        diff[reaction.reactants[0].count] = diff[reaction.reactants[0].count] + self.coefficients[layer.name][reaction.name].lam * e * (reaction.reactants[0].index - Cn[self.cptot[j]+i*layer.nchemicals+reaction.products[0].count])

                        diff[reaction.products[0].count]  = diff[reaction.products[0].count] - self.coefficients[layer.name][reaction.name].lam * e * Cn[self.cptot[j]+i*layer.nchemicals+reaction.reactants[0].count]
                    else:
                        if reaction.name.count('_desorption') == 1:
                            component_name = reaction.component
                            rho = self.components[self.component_list.index(component_name)].rho * Fis[component_name][self.ptot[j]+i]
                            rate = self.coefficients[layer.name][reaction.name].lam * rho
                        else:
                            rate = self.coefficients[layer.name][reaction.name].lam * self.es_plus_1[self.ptot[j]+i]

                        for reactant in reaction.reactants:
                            if     Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] <= 0:    rate = 0
                            else:                                                               rate = rate * Cn[self.cptot[j]+i*layer.nchemicals+reactant.count]**reactant.index
                        for reactant in reaction.reactants:
                            if  Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] >0:
                                diff[reactant.count] = rate / Cn[self.cptot[j]+i*layer.nchemicals+reactant.count] * reactant.index

                    for chemical in (reaction.reactants + reaction.products):
                        for chemical_a in (reaction.reactants + reaction.products):
                            self.rates_diff[self.cptot[j]+i*layer.nchemicals+chemical.count, self.cptot[j]+i*layer.nchemicals+chemical_a.count]      \
                                = self.rates_diff[self.cptot[j]+i*layer.nchemicals+chemical.count, self.cptot[j]+i*layer.nchemicals+chemical_a.count] + diff[chemical_a.count] * chemical_a.coef

    def make_boundary_equations(self):
        """Makes the finite difference equations for the boundary conditions."""

        ptot    = []
        cptot   = []
        layers  = []

        for i in self.ptot: ptot.append(i)
        for i in self.cptot: cptot.append(i)

        for layer in self.layertot:
            layers.append(layer)

        i    = 0
        if self.bio == 1 and ptot.count(self.pbio) == 0:
            ptot.insert(self.layerbio + 1, self.pbio)
            cptot.insert(self.layerbio + 1, self.cpbio)
            layers.insert(self.layerbio + 1, self.layertot[self.layerbio])

        #top boundary
        num = layers[0].nchemicals
        for n in range(num):
            chemical = layers[0].chemicals[n]
            if chemical.soluable == 1:
                if self.topBCtype == 'Mass transfer':
                    if self.bio == 1:
                        KDbiops_plus_1  = [self.Dbiops_plus_1[0]  *self.KsL_plus_1[i+n],
                                           self.Dbiops_plus_1[0]  *self.Ks_plus_1[i+num+n],
                                           self.Dbiops_plus_1[0]  *self.Ks_plus_1[i+2*num+n]]
                    else:
                        KDbiops_plus_1 = 0
                    [self.A[n,n], self.A[n,num+n], self.A[n,2*num+n]], self.b[n] = top_mass_transfer_boundary(self.Ds_plus_1[n],  KDbiops_plus_1,  self.BCs[chemical.name].k, self.BCs[chemical.name].Cw, self.z[0:3])
                elif self.topBCtype == 'Fixed Concentration':
                    self.A[n,n], self.b[n] = 1, self.BCs[chemical.name].Co
                elif self.topBCtype == 'Finite mixed water column':
                    [self.A[n,n], self.A[n,num+n], self.A[n,2*num+n]], self.b[n] = top_CSTR_boundary(self.Ds_plus_1[n], self.Us_plus_1[n], self.BCs[chemical.name].k, self.BCs[chemical.name].tau, self.taucoefs['h'], self.z[0:3])
            else:
                self.A[n,n], self.A[n,n+num]  = -1 , 1

        #flux boundary conditions at interfaces
        for j in range(len(layers) - 1):
            numa =layers[j].nchemicals
            numb =layers[j+1].nchemicals
            i = cptot[j+1]
            p = ptot[j+1]
            for n in range(self.nchemicals):
                if self.bio == 1 and p <> self.pbio:
                    KDbiops_plus_1  = [self.Dbiops_plus_1[p]  *self.KsL_plus_1[i-2*numa+n],
                                       self.Dbiops_plus_1[p]  *self.Ks_plus_1[i-numa+n],
                                       self.Dbiops_plus_1[p]  *self.Ks_plus_1[i+n]]
                    KDbiopsL_plus_1 = [self.DbiopsL_plus_1[p] *self.KsL_plus_1[i+n],
                                       self.DbiopsL_plus_1[p] *self.Ks_plus_1[i+numb+n],
                                       self.DbiopsL_plus_1[p] *self.Ks_plus_1[i+2*numb+n]]
                else:
                    KDbiops_plus_1  =  0
                    KDbiopsL_plus_1 =  0

                [self.A[i+n,i-numa*2+n], self.A[i+n,i-numa+n], self.A[i+n,i+n], self.A[i+n,i+numb+n], self.A[i+n,i+2*numb+n]] = interface_boundary(self.Ds_plus_1[i+n],  self.Us_plus_1[i+n],  KDbiops_plus_1,
                                                                                                                                                   self.DsL_plus_1[i+n], self.UsL_plus_1[i+n], KDbiopsL_plus_1, self.z[p-2:p+3])
            for n in range(layers[j+1].nsolidchemicals):
                if layers[j].solidchemical_list.count(layers[j+1].solidchemicals[n].name) > 0  and self.bio == 1 and self.DbiopsL[p] > 0 :
                    na = layers[j].solidchemical_list.index(layers[j+1].solidchemicals[n].name)
                    nb = n
                    if self.biomix == 1 and self.Ks_plus_1[i-numa+self.nchemicals+n] > 0:
                        KDbiops_plus_1  = [self.Dbiops[p]  *self.KsL_plus_1[i-2*numa+self.nchemicals+na],
                                           self.Dbiops[p]  *self.Ks_plus_1[i-numa+self.nchemicals+na],
                                           self.Dbiops[p]  *self.Ks_plus_1[i+self.nchemicals+n]]
                        KDbiopsL_plus_1 = [self.DbiopsL[p] *self.KsL_plus_1[i+self.nchemicals+n],
                                           self.DbiopsL[p] *self.Ks_plus_1[i+numb+self.nchemicals+nb],
                                           self.DbiopsL[p] *self.Ks_plus_1[i+2*numb+self.nchemicals+nb]]
                        [self.A[i+self.nchemicals+n,i-numa*2+self.nchemicals+na], self.A[i+self.nchemicals+n,i-numa+self.nchemicals+na], self.A[i+self.nchemicals+n,i+self.nchemicals+n],
                         self.A[i+self.nchemicals+n,i+numb+self.nchemicals+n], self.A[i+self.nchemicals+n,i+2*numb+self.nchemicals+n]] = interface_boundary(0, 0, KDbiops_plus_1, 0, 0, KDbiopsL_plus_1, self.z[p-2:p+3])
                    else:
                        self.A[i + n + self.nchemicals, i + n+ self.nchemicals], self.A[i + n+ self.nchemicals, i + numb + n+ self.nchemicals] = 1, -1

                else:
                    self.A[i + n + self.nchemicals, i + n+ self.nchemicals], self.A[i + n+ self.nchemicals, i + numb + n+ self.nchemicals] = 1, -1

        #bottom boundary
        numb = layers[-1].nchemicals
        i   = cptot[-1]
        for n in range(self.nchemicals):
            chemical = self.chemicals[n]
            if self.botBCtype == 'Fixed Concentration':
                self.A[i+n,i+n], self.b[i+n] = 1, self.BCs[chemical.name].Cb

            elif self.botBCtype == 'Flux-matching':
                [self.A[i+n,i-numb*2+n], self.A[i+n,i-numb+n], self.A[i+n,i+n]], self.b[i+n] = flux_bottom_boundary(self.Us_plus_1[i+n], self.Ds_plus_1[i+n], [0,0,0], self.BCs[chemical.name].Cb, self.z[-3:])

            elif self.botBCtype == 'Zero Gradient':
                self.A[i+n,i-numb+n], self.A[i+n,i+n] = -1, 1

        for n in range(layers[-1].nsolidchemicals):
            self.A[i + n + self.nchemicals, i - numb  + n + self.nchemicals], self.A[i + n + self.nchemicals, i + n + self.nchemicals] = -1, 1

    def make_components_equations(self):

        ptot    = []
        cptot   = []
        layers  = []

        for i in self.ptot: ptot.append(i)
        for i in self.cptot: cptot.append(i)

        for layer in self.layertot:
            layers.append(layer)

        i    = 0
        if self.bio == 1 and ptot.count(self.pbio) == 0:
            ptot.insert(self.layerbio + 1, self.pbio)
            cptot.insert(self.layerbio + 1, self.cpbio)
            layers.insert(self.layerbio + 1, self.layertot[self.layerbio])

        for j in range(len(ptot) - 1):
            for ii in range((ptot[j+1] - 1 - (ptot[j] + 1))):
                i = ii + 1
                p = ptot[j] + i

                Ds_plus_1      = [ self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i] - self.DbiopsL_plus_1[ptot[j]+(i+1)]/4,
                                   self.DbiopsL_plus_1[ptot[j]+i],
                                  -self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i] + self.DbiopsL_plus_1[ptot[j]+(i+1)]/4]
                Ds             = [ self.DbiopsL[ptot[j]+(i-1)]/4+self.DbiopsL[ptot[j]+i] - self.DbiopsL[ptot[j]+(i+1)]/4,
                                   self.DbiopsL[ptot[j]+i],
                                  -self.DbiopsL[ptot[j]+(i-1)]/4+self.DbiopsL[ptot[j]+i] + self.DbiopsL[ptot[j]+(i+1)]/4]
                KDbiops_plus_1 = [0, 0, 0]
                KDbiops        = [0, 0, 0]

                [self.Acomp[ptot[j]+i,ptot[j]+(i-1)], self.Acomp[ptot[j]+i,ptot[j]+i], self.Acomp[ptot[j]+i,ptot[j]+(i+1)], self.Acomp[ptot[j]+i,ptot[j]+(i+2)]] , \
                [self.Bcomp[ptot[j]+i,ptot[j]+(i-1)], self.Bcomp[ptot[j]+i,ptot[j]+i], self.Bcomp[ptot[j]+i,ptot[j]+(i+1)], self.Bcomp[ptot[j]+i,ptot[j]+(i+2)]] = \
                get_4pt_adr_fde_CN(1, 1, 0, 0, Ds_plus_1, Ds, KDbiops_plus_1, KDbiops, self.delt, self.z[p-1:p+3])

            p        = ptot[j+1]
            if p == self.pbio:
                Ds_plus_1      = [(self.DbiopsL_plus_1[p-2]+self.DbiopsL_plus_1[p-1])/2,
                                  (self.DbiopsL_plus_1[p-2]+self.DbiopsL_plus_1[p-1])/4,
                                  0]
                Ds             = [(self.DbiopsL[p-2]+self.DbiopsL[p-1])/2,
                                  (self.DbiopsL[p-2]+self.DbiopsL[p-1])/4,
                                  0]

            else:
                Ds_plus_1      = [ self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4,
                                   self.DbiopsL_plus_1[p-1],
                                  -self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4]
                Ds             = [ self.DbiopsL[p-2]/4+self.DbiopsL[p-1] - self.DbiopsL[p]/4,
                                   self.DbiopsL[p-1],
                                  -self.DbiopsL[p-2]/4+self.DbiopsL[p-1] + self.DbiopsL[p]/4]
            KDbiops        = [0, 0, 0]
            KDbiops_plus_1 = [0, 0, 0]

            [self.Acomp[ptot[j+1]-1,ptot[j+1]-2], self.Acomp[ptot[j+1]-1,ptot[j+1]-1], self.Acomp[ptot[j+1]-1,ptot[j+1]]], \
            [self.Bcomp[ptot[j+1]-1,ptot[j+1]-2], self.Bcomp[ptot[j+1]-1,ptot[j+1]-1], self.Bcomp[ptot[j+1]-1,ptot[j+1]]] = \
            get_3pt_adr_fde_CN(1, 1, 0, 0, Ds_plus_1, Ds, KDbiops_plus_1, KDbiops, self.delt, self.z[ptot[j+1]-2:ptot[j+1]+1])

        [self.Acomp[0,0], self.Acomp[0,1],  self.Acomp[0,2]], self.bcomp[0]= top_mass_transfer_boundary(self.Dbiops[0], 0, 0, 0, self.z[0:3])

        for j in range(len(layers) - 1):
            p = ptot[j+1]
            if p < self.pbio:
                [self.Acomp[p,p-2], self.Acomp[p,p-1], self.Acomp[p,p], self.Acomp[p,p+1], self.Acomp[p,p+2]] = comp_interface_boundary(self.Dbiops_plus_1[p], 0, [0,0,0], self.DbiopsL_plus_1[p], 0, [0,0,0], self.z[p-2:p+3])
            else:
                self.Acomp[p, p], self.Bcomp[p, p] = 1, 1

        self.Acomp[self.ptot[-1],self.ptot[-1]], self.Bcomp[self.ptot[-1], self.ptot[-1]]  = 1, 1

    def make_governing_equations(self):
        """Makes finite difference equations for the governing PDEs."""

        ptot    = []
        cptot   = []
        layers  = []
        for i in self.ptot: ptot.append(i)
        for i in self.cptot: cptot.append(i)

        for layer in self.layertot:
            layers.append(layer)


        i    = 0
        if self.bio == 1 and ptot.count(self.pbio) == 0:
            ptot.insert(self.layerbio + 1, self.pbio)
            cptot.insert(self.layerbio + 1, self.cpbio)
            layers.insert(self.layerbio + 1, self.layertot[self.layerbio])

        if self.timeoption == 'Crank-Nicolson':

            for j in range(len(ptot) - 1):
                num = layers[j].nchemicals
                for n in range(self.nchemicals):
                    for ii in range((ptot[j+1] - 1 - (ptot[j] + 1))):
                        i = ii + 1
                        p = ptot[j] + i
                        if self.biomix == 1:
                            Ds_plus_1      = [ self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]-self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds_plus_1[cptot[j]+i*num+n],
                                              -self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]+self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4]
                            Ds             = [ self.DsL[cptot[j]+(i-1)*num+n]/4+self.Ds[cptot[j]+i*num+n]-self.Ds[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds[cptot[j]+i*num+n],
                                              -self.DsL[cptot[j]+(i-1)*num+n]/4+self.Ds[cptot[j]+i*num+n]+self.Ds[cptot[j]+(i+1)*num+n]/4]
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                            KDbiops        = [( self.DbiopsL[p-1]/4+self.DbiopsL[p] - self.DbiopsL[p+1]/4)                      *self.KsL[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL[p])                                                                *self.Ks[cptot[j]+i*num+n],
                                              (-self.DbiopsL[p-1]/4+self.DbiopsL[p] + self.DbiopsL[p+1]/4)                      *self.Ks[cptot[j]+(i+1)*num+n]]

                        elif self.bio == 1:
                            Ds_plus_1      = [ self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]-self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds_plus_1[cptot[j]+i*num+n],
                                              -self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]+self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4]
                            Ds             = [ self.DsL[cptot[j]+(i-1)*num+n]/4+self.Ds[cptot[j]+i*num+n]-self.Ds[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds[cptot[j]+i*num+n],
                                              -self.DsL[cptot[j]+(i-1)*num+n]/4+self.Ds[cptot[j]+i*num+n]+self.Ds[cptot[j]+(i+1)*num+n]/4]

                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                            KDbiops        = [( self.DbiopsL[p-1]/4+self.DbiopsL[p] - self.DbiopsL[p+1]/4)                      *self.KsL[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL[p])                                                                *self.Ks[cptot[j]+i*num+n],
                                              (-self.DbiopsL[p-1]/4+self.DbiopsL[p] + self.DbiopsL[p+1]/4)                      *self.Ks[cptot[j]+(i+1)*num+n]]
                        else:
                            Ds_plus_1      = [self.DsL_plus_1[cptot[j]+i*num+n], self.Ds_plus_1[cptot[j]+i*num+n], self.Ds_plus_1[cptot[j]+i*num+n]]
                            Ds             = [self.DsL[cptot[j]+i*num+n], self.Ds[cptot[j]+i*num+n], self.Ds[cptot[j]+i*num+n]]
                            KDbiops_plus_1 = [0,0,0]
                            KDbiops        = [0,0,0]

                        [self.A[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+i*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] , \
                        [self.B[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+i*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] = \
                        get_4pt_adr_fde_CN(self.Rs[cptot[j]+i*num+n], self.Rs_plus_1[cptot[j]+i*num+n], self.Us[cptot[j]+i*num+n], self.Us_plus_1[cptot[j]+i*num+n], Ds, Ds_plus_1,  KDbiops, KDbiops_plus_1, self.delt, self.z[p-1:p+3])
                        for np in range(num):
                            self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] - self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]/2
                            self.B[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.B[cptot[j]+i*num+n,cptot[j]+i*num+np] + self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]/2

                        self.a[cptot[j]+i*num+n] = -self.rates_plus_1[cptot[j]+i*num+n]/2
                        self.b[cptot[j]+i*num+n] = self.rates[cptot[j]+i*num+n]/2


                    p        = ptot[j+1]
                    if self.biomix == 1:
                        Ds_plus_1      = [ self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]-self.Ds_plus_1[cptot[j+1]+n]/4,
                                           self.Ds_plus_1[cptot[j+1]-num+n],
                                          -self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]+self.Ds_plus_1[cptot[j+1]+n]/4]
                        Ds             = [ self.DsL[cptot[j+1]-2*num+n]/4+self.Ds[cptot[j+1]-num+n]-self.Ds[cptot[j+1]+n]/4,
                                           self.Ds[cptot[j+1]-num+n],
                                          -self.DsL[cptot[j+1]-2*num+n]/4+self.Ds[cptot[j+1]-num+n]+self.Ds[cptot[j+1]+n]/4]

                        if p == self.pbio:
                            KDbiops_plus_1 = [(self.DbiopsL_plus_1[p-2]+self.DbiopsL_plus_1[p-1])/2*self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              (self.Dbiops_plus_1[p-2] +self.DbiopsL_plus_1[p-1])/4*self.Ks_plus_1[cptot[j+1]-num+n],
                                              0]
                            KDbiops        = [(self.DbiopsL[p-2]+self.DbiopsL[p-1])/2*self.KsL[cptot[j+1]-2*num+n],
                                              (self.Dbiops[p-2]+ self.DbiopsL[p-1])/4*self.Ks[cptot[j+1]-num+n],
                                              0]
                        else:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                              (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                            KDbiops        = [( self.DbiopsL[p-2]/4+self.DbiopsL[p-1] - self.DbiopsL[p]/4)                      *self.KsL[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL[p-1])                                                              *self.Ks[cptot[j+1]-num+n],
                                              (-self.DbiopsL[p-2]/4+self.DbiopsL[p-1] + self.DbiopsL[p]/4)                      *self.Ks[cptot[j+1]+n]]

                    elif self.bio == 1:
                        Ds_plus_1      = [ self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]-self.Ds_plus_1[cptot[j+1]+n]/4,
                                           self.Ds_plus_1[cptot[j+1]-num+n],
                                          -self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]+self.Ds_plus_1[cptot[j+1]+n]/4]
                        Ds             = [ self.DsL[cptot[j+1]-2*num+n]/4+self.Ds[cptot[j+1]-num+n]-self.Ds[cptot[j+1]+n]/4,
                                           self.Ds[cptot[j+1]-num+n],
                                          -self.DsL[cptot[j+1]-2*num+n]/4+self.Ds[cptot[j+1]-num+n]+self.Ds[cptot[j+1]+n]/4]

                        KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                          ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                          (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                        KDbiops        = [( self.DbiopsL[p-2]/4+self.DbiopsL[p-1] - self.DbiopsL[p]/4)                      *self.KsL[cptot[j+1]-2*num+n],
                                          ( self.DbiopsL[p-1])                                                              *self.Ks[cptot[j+1]-num+n],
                                          (-self.DbiopsL[p-2]/4+self.DbiopsL[p-1] + self.DbiopsL[p]/4)                      *self.Ks[cptot[j+1]+n]]
                    else:
                        Ds_plus_1      = [self.DsL_plus_1[cptot[j+1]-num+n], self.Ds_plus_1[cptot[j+1]-num+n], self.Ds_plus_1[cptot[j+1]-num+n]]
                        KDbiops_plus_1 = [0,0,0]
                        Ds             = [self.DsL[cptot[j+1]-num+n], self.Ds[cptot[j+1]-num+n], self.Ds[cptot[j+1]-num+n]]
                        KDbiops        = [0,0,0]

                    [self.A[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.A[cptot[j+1]-num+n,cptot[j+1]-num+n], self.A[cptot[j+1]-num+n,cptot[j+1]+n]], \
                    [self.B[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.B[cptot[j+1]-num+n,cptot[j+1]-num+n], self.B[cptot[j+1]-num+n,cptot[j+1]+n]] = \
                    get_3pt_adr_fde_CN(self.Rs[cptot[j+1]-num+n], self.Rs_plus_1[cptot[j+1]-num+n], self.Us[cptot[j+1]-num+n], self.Us_plus_1[cptot[j+1]-num+n],Ds, Ds_plus_1, KDbiops, KDbiops_plus_1, self.delt, self.z[ptot[j+1]-2:ptot[j+1]+1])
                    for np in range(num):
                        self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] - self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]/2
                        self.B[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.B[cptot[j+1]-num+n,cptot[j+1]-num+np] + self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]/2

                    self.a[cptot[j+1]-num+n] = -self.rates_plus_1[cptot[j+1]-num+n]/2
                    self.b[cptot[j+1]-num+n] = self.rates[cptot[j+1]-num+n]/2


                for nn in range(layers[j].nsolidchemicals):
                    solidchemical = layers[j].solidchemicals[nn]
                    n = nn + self.nchemicals
                    for ii in range((ptot[j+1] - 1 - (ptot[j] + 1))):
                        i = ii + 1
                        p = ptot[j] + i
                        if self.biomix == 1:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                            KDbiops        = [( self.DbiopsL[p-1]/4+self.DbiopsL[p] - self.DbiopsL[p+1]/4)                      *self.KsL[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL[p])                                                                *self.Ks[cptot[j]+i*num+n],
                                              (-self.DbiopsL[p-1]/4+self.DbiopsL[p] + self.DbiopsL[p+1]/4)                      *self.Ks[cptot[j]+(i+1)*num+n]]
                        elif self.bio == 1:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                            KDbiops        = [( self.DbiopsL[p-1]/4+self.DbiopsL[p] - self.DbiopsL[p+1]/4)                      *self.KsL[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL[p])                                                                *self.Ks[cptot[j]+i*num+n],
                                              (-self.DbiopsL[p-1]/4+self.DbiopsL[p] + self.DbiopsL[p+1]/4)                      *self.Ks[cptot[j]+(i+1)*num+n]]
                        else:
                            KDbiops_plus_1 = [0,0,0]
                            KDbiops        = [0,0,0]

                        if self.Rs_plus_1[cptot[j]+i*num+n]/self.components[solidchemical.component_index].rho < 0.0000000001:
                            self.A[cptot[j]+i*num+n,cptot[j]+i*num+n] = 1
                        else:
                            [self.A[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+i*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] , \
                            [self.B[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+i*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] = \
                            get_4pt_adr_fde_CN(self.Rs[cptot[j]+i*num+n], self.Rs_plus_1[cptot[j]+i*num+n], self.Us[cptot[j]+i*num+n], self.Us_plus_1[cptot[j]+i*num+n], [0,0,0], [0,0,0], KDbiops, KDbiops_plus_1, self.delt, self.z[p-1:p+3])
                            for np in range(num):
                                self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] - self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]/2
                                self.B[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.B[cptot[j]+i*num+n,cptot[j]+i*num+np] + self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]/2

                            self.a[cptot[j]+i*num+n] = -self.rates_plus_1[cptot[j]+i*num+n]/2
                            self.b[cptot[j]+i*num+n] = self.rates[cptot[j]+i*num+n]/2

                    p        = ptot[j+1]
                    if self.biomix == 1:
                        if p == self.pbio:
                            KDbiops_plus_1 = [(self.DbiopsL_plus_1[p-2]+self.DbiopsL_plus_1[p-1])/2*self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              (self.Dbiops_plus_1[p-2] +self.DbiopsL_plus_1[p-1])/4*self.Ks_plus_1[cptot[j+1]-num+n],
                                              0]
                            KDbiops        = [(self.DbiopsL[p-2]+self.DbiopsL[p-1])/2*self.KsL[cptot[j+1]-2*num+n],
                                              (self.Dbiops[p-2]+ self.DbiopsL[p-1])/4*self.Ks[cptot[j+1]-num+n],
                                              0]
                        else:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                              (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                            KDbiops        = [( self.DbiopsL[p-2]/4+self.DbiopsL[p-1] - self.DbiopsL[p]/4)                      *self.KsL[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL[p-1])                                                              *self.Ks[cptot[j+1]-num+n],
                                              (-self.DbiopsL[p-2]/4+self.DbiopsL[p-1] + self.DbiopsL[p]/4)                      *self.Ks[cptot[j+1]+n]]

                    elif self.bio == 1:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                              (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                            KDbiops        = [( self.DbiopsL[p-2]/4+self.DbiopsL[p-1] - self.DbiopsL[p]/4)                      *self.KsL[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL[p-1])                                                              *self.Ks[cptot[j+1]-num+n],
                                              (-self.DbiopsL[p-2]/4+self.DbiopsL[p-1] + self.DbiopsL[p]/4)                      *self.Ks[cptot[j+1]+n]]

                    else:
                        KDbiops_plus_1 = [0,0,0]
                        KDbiops        = [0,0,0]

                    if self.Rs_plus_1[cptot[j+1]-num+n]/self.components[solidchemical.component_index].rho < 0.0000000001:
                        self.A[cptot[j+1]-num+n,cptot[j+1]-num+n] = 1
                    else:
                        [self.A[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.A[cptot[j+1]-num+n,cptot[j+1]-num+n], self.A[cptot[j+1]-num+n,cptot[j+1]+n]], \
                        [self.B[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.B[cptot[j+1]-num+n,cptot[j+1]-num+n], self.B[cptot[j+1]-num+n,cptot[j+1]+n]] = \
                        get_3pt_adr_fde_CN(self.Rs[cptot[j+1]-num+n], self.Rs_plus_1[cptot[j+1]-num+n], self.Us[cptot[j+1]-num+n], self.Us_plus_1[cptot[j+1]-num+n],[0,0,0], [0,0,0], KDbiops, KDbiops_plus_1, self.delt, self.z[ptot[j+1]-2:ptot[j+1]+1])
                        for np in range(num):
                            self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] - self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]/2
                            self.B[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.B[cptot[j+1]-num+n,cptot[j+1]-num+np] + self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]/2

                        self.a[cptot[j+1]-num+n] = -self.rates_plus_1[cptot[j+1]-num+n]/2
                        self.b[cptot[j+1]-num+n] = self.rates[cptot[j+1]-num+n]/2


        elif self.timeoption == 'Implicit':
            for j in range(len(ptot) - 1):
                num = layers[j].nchemicals
                for n in range(self.nchemicals):
                    chemical = layers[j].chemicals[n]
                    for ii in range((ptot[j+1] - 1 - (ptot[j] + 1))):
                        i = ii + 1
                        p = ptot[j] + i
                        if self.biomix == 1:
                            Ds_plus_1      = [ self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]-self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds_plus_1[cptot[j]+i*num+n],
                                              -self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]+self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4]
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                        elif self.bio == 1:
                            Ds_plus_1      = [ self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]-self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4,
                                               self.Ds_plus_1[cptot[j]+i*num+n],
                                              -self.DsL_plus_1[cptot[j]+(i-1)*num+n]/4+self.Ds_plus_1[cptot[j]+i*num+n]+self.Ds_plus_1[cptot[j]+(i+1)*num+n]/4]
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                        else:
                            Ds_plus_1      = [self.DsL_plus_1[cptot[j]+i*num+n], self.Ds_plus_1[cptot[j]+i*num+n], self.Ds_plus_1[cptot[j]+i*num+n]]
                            KDbiops_plus_1 = [0,0,0]

                        [self.A[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+i*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] , \
                        [self.B[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+i*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] = \
                        get_4pt_adr_fde_imp(self.Rs[cptot[j]+i*num+n], self.Rs_plus_1[cptot[j]+i*num+n], self.Us_plus_1[cptot[j]+i*num+n], Ds_plus_1, KDbiops_plus_1, self.delt, self.z[p-1:p+3])
                        for np in range(num):
                            self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] - self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]
                            self.B[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.B[cptot[j]+i*num+n,cptot[j]+i*num+np]

                        self.a[cptot[j]+i*num+n] = -self.rates[cptot[j]+i*num+n]
                        self.b[cptot[j]+i*num+n] = 0

                        if self.Rs_plus_1[cptot[j]+i*num+n] == 0: self.A[cptot[j]+i*num+n,cptot[j]+i*num+n] = 1

                    p        = ptot[j+1]
                    if self.biomix == 1:
                        Ds_plus_1      = [ self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]-self.Ds_plus_1[cptot[j+1]+n]/4,
                                           self.Ds_plus_1[cptot[j+1]-num+n],
                                          -self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]+self.Ds_plus_1[cptot[j+1]+n]/4]
                        if p == self.pbio:
                            KDbiops_plus_1        = [(self.DbiopsL[p-2]+self.DbiopsL[p-1])/2*self.KsL[cptot[j+1]-2*num+n],
                                                     (self.Dbiops[p-2]+ self.DbiopsL[p-1])/4*self.Ks[cptot[j+1]-num+n],
                                                     0]
                        else:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.Dbiops_plus_1[p-1] - self.Dbiops_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              ( self.Dbiops_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                              (-self.DbiopsL_plus_1[p-2]/4+self.Dbiops_plus_1[p-1] + self.Dbiops_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                    elif self.bio == 1:
                        Ds_plus_1      = [ self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]-self.Ds_plus_1[cptot[j+1]+n]/4,
                                           self.Ds_plus_1[cptot[j+1]-num+n],
                                          -self.DsL_plus_1[cptot[j+1]-2*num+n]/4+self.Ds_plus_1[cptot[j+1]-num+n]+self.Ds_plus_1[cptot[j+1]+n]/4]
                        KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.Dbiops_plus_1[p-1] - self.Dbiops_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                          ( self.Dbiops_plus_1[p-1])                                                      *self.Ks_plus_1[cptot[j+1]-num+n],
                                          (-self.DbiopsL_plus_1[p-2]/4+self.Dbiops_plus_1[p-1] + self.Dbiops_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                    else:
                        Ds_plus_1      = [self.DsL_plus_1[cptot[j+1]-num+n], self.Ds_plus_1[cptot[j+1]-num+n], self.Ds_plus_1[cptot[j+1]-num+n]]
                        KDbiops_plus_1 = [0,0,0]

                    [self.A[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.A[cptot[j+1]-num+n,cptot[j+1]-num+n], self.A[cptot[j+1]-num+n,cptot[j+1]+n]], \
                    [self.B[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.B[cptot[j+1]-num+n,cptot[j+1]-num+n], self.B[cptot[j+1]-num+n,cptot[j+1]+n]] = \
                    get_3pt_adr_fde_imp(self.Rs[cptot[j+1]-num+n], self.Rs_plus_1[cptot[j+1]-num+n],  self.Us_plus_1[cptot[j+1]-num+n], Ds_plus_1, KDbiops_plus_1, self.delt, self.z[ptot[j+1]-2:ptot[j+1]+1])
                    for np in range(num):
                        self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] - self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]
                        self.B[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.B[cptot[j+1]-num+n,cptot[j+1]-num+np]

                    self.a[cptot[j+1]-num+n] = -self.rates[cptot[j+1]-num+n]
                    self.b[cptot[j+1]-num+n] = 0

                    if self.Rs_plus_1[cptot[j+1]-num+n] == 0: self.A[cptot[j+1]-num+n,cptot[j+1]-num+n] = 1

                for nn in range(layers[j].nsolidchemicals):
                    solidchemical = layers[j].solidchemicals[nn]
                    n = nn + self.nchemicals
                    for ii in range((ptot[j+1] - 1 - (ptot[j] + 1))):
                        i = ii + 1
                        p = ptot[j] + i
                        if self.biomix == 1:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]

                        elif self.bio == 1:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] - self.DbiopsL_plus_1[p+1]/4) *self.KsL_plus_1[cptot[j]+(i-1)*num+n],
                                              ( self.DbiopsL_plus_1[p])                                                         *self.Ks_plus_1[cptot[j]+i*num+n],
                                              (-self.DbiopsL_plus_1[p-1]/4+self.DbiopsL_plus_1[p] + self.DbiopsL_plus_1[p+1]/4) *self.Ks_plus_1[cptot[j]+(i+1)*num+n]]
                        else:
                            KDbiops_plus_1 = [0,0,0]

                        if self.Rs_plus_1[cptot[j]+i*num+n]/self.components[solidchemical.component_index].rho < 0.0000000001:
                            self.A[cptot[j]+i*num+n,cptot[j]+i*num+n] = 1
                        else:
                            [self.A[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+i*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.A[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] , \
                            [self.B[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+i*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n], self.B[cptot[j]+i*num+n,cptot[j]+(i+2)*num+n]] = \
                            get_4pt_adr_fde_imp(self.Rs[cptot[j]+i*num+n], self.Rs_plus_1[cptot[j]+i*num+n], self.Us_plus_1[cptot[j]+i*num+n],  [0,0,0], KDbiops_plus_1, self.delt, self.z[p-1:p+3])
                            for np in range(num):
                                self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] = self.A[cptot[j]+i*num+n,cptot[j]+i*num+np] - self.elams[cptot[j]+i*num+n,cptot[j]+i*num+np]#/2

                            self.a[cptot[j]+i*num+n] = -self.rates_plus_1[cptot[j]+i*num+n]
                            self.b[cptot[j]+i*num+n] = 0

                    p        = ptot[j+1]
                    if self.biomix == 1:
                        if p == self.pbio:
                            KDbiops_plus_1 = [(self.DbiopsL_plus_1[p-2]+self.DbiopsL_plus_1[p-1])/2*self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              (self.Dbiops_plus_1[p-2] +self.DbiopsL_plus_1[p-1])/4*self.Ks_plus_1[cptot[j+1]-num+n],
                                              0]
                        else:
                            KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                              ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                              (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                    elif self.bio == 1:
                        KDbiops_plus_1 = [( self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] - self.DbiopsL_plus_1[p]/4) *self.KsL_plus_1[cptot[j+1]-2*num+n],
                                          ( self.DbiopsL_plus_1[p-1])                                                       *self.Ks_plus_1[cptot[j+1]-num+n],
                                          (-self.DbiopsL_plus_1[p-2]/4+self.DbiopsL_plus_1[p-1] + self.DbiopsL_plus_1[p]/4) *self.Ks_plus_1[cptot[j+1]+n]]
                    else:
                        KDbiops_plus_1 = [0,0,0]

                    if self.Rs_plus_1[cptot[j+1]-num+n]/self.components[solidchemical.component_index].rho < 0.0000000001:
                        self.A[cptot[j+1]-num+n,cptot[j+1]-num+n] = 1
                    else:
                        [self.A[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.A[cptot[j+1]-num+n,cptot[j+1]-num+n], self.A[cptot[j+1]-num+n,cptot[j+1]+n]], \
                        [self.B[cptot[j+1]-num+n,cptot[j+1]-2*num+n], self.B[cptot[j+1]-num+n,cptot[j+1]-num+n], self.B[cptot[j+1]-num+n,cptot[j+1]+n]] = \
                        get_3pt_adr_fde_imp(self.Rs[cptot[j+1]-num+n], self.Rs_plus_1[cptot[j+1]-num+n], self.Us_plus_1[cptot[j+1]-num+n],[0,0,0], KDbiops_plus_1, self.delt, self.z[ptot[j+1]-2:ptot[j+1]+1])
                        for np in range(num):
                            self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] = self.A[cptot[j+1]-num+n,cptot[j+1]-num+np] - self.elams[cptot[j+1]-num+n,cptot[j+1]-num+np]#/2

                        self.a[cptot[j+1]-num+n] = -self.rates_plus_1[cptot[j+1]-num+n]
                        self.b[cptot[j+1]-num+n] = 0

    def make_Newton_Raphson_equations(self, Cn, Fis, FisL):

        self.NR     = self.A.copy()

        ptot    = []
        cptot   = []
        layers  = []
        for i in self.ptot: ptot.append(i)
        for i in self.cptot: cptot.append(i)

        for layer in self.layertot:
            layers.append(layer)

        i    = 0
        if self.bio == 1:
            ptot.insert(self.layerbio + 1, self.pbio)
            cptot.insert(self.layerbio + 1, self.cpbio)
            layers.insert(self.layerbio + 1, self.layertot[self.layerbio])

        if self.timeoption == 'Crank-Nicolson':
            # Correct the non-linear sorption terms in Newton Raphson Matrix
            for j in range(len(ptot) - 1):
                layer = layers[j]
                num = layers[j].nchemicals
                if self.sorp == 1:
                    for n in range(self.nchemicals):
                        chemical = self.chemicals[n]
                        for component in layer.components:
                            if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                    for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                                        i = ii + 1
                                        self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n] = (self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n]
                                                                    -Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt
                                                                    +Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt)
                                    p = ptot[j+1] - (ptot[j] + 1)
                                    self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                -Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt
                                                                +Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt)

                # Correct the non-linear reaction terms in Newton Raphson Matrix
                if self.reac == 1:
                    for n in range(num):
                        chemical = layers[j].chemicals[n]
                        for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                            i = ii + 1
                            for nn in range(num):
                                self.NR[cptot[j]+i*num+n, cptot[j]+i*num+nn] = self.NR[cptot[j]+i*num+n, cptot[j]+i*num+nn] - self.rates_diff[cptot[j]+i*num+n, cptot[j]+i*num+nn]/2
                        for nn in range(num):
                            self.NR[cptot[j+1]-num+n, cptot[j+1]-num+nn] = self.NR[cptot[j+1]-num+n, cptot[j+1]-num+nn] - self.rates_diff[cptot[j+1]-num+n, cptot[j+1]-num+nn]/2

            if self.bio == 1 and self.Dbiop > 0 and self.sorp == 1:
                for j in range(self.layerbio+1):
                    layer = layers[j]
                    num = layers[j].nchemicals
                    for n in range(self.nchemicals):
                        chemical = self.chemicals[n]
                        for component in layer.components:
                            if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                    for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                                        i = ii + 1
                                        self.NR[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n]  = (self.NR[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n]
                                                                                            +(self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]-self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * FisL[component.name][ptot[j]+(i-1)] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+(i-1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2
                                                                                            -(self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]-self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * FisL[component.name][ptot[j]+(i-1)] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+(i-1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2)

                                        self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n]      = (self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n]
                                                                                            -(self.DbiopsL_plus_1[ptot[j]+i]) * Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                                            +(self.DbiopsL_plus_1[ptot[j]+i]) * Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                        self.NR[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n]  = (self.NR[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n]
                                                                                            +(-self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]+self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * Fis[component.name][ptot[j]+(i+1)] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+(i+1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2
                                                                                            -(-self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]+self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * Fis[component.name][ptot[j]+(i+1)] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+(i+1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2)

                                    p = ptot[j+1]

                                    if ptot[j+1] == self.pbio:
                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n]
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/2 * Fis[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/2 * Fis[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/4 * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/4 * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                    else:
                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n]
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]-self.Dbiops_plus_1[ptot[j+1]]/4) * Fis[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]-self.Dbiops_plus_1[ptot[j+1]]/4) * Fis[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-1]) * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-1]) * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]+n]
                                                                    +(-self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]+self.Dbiops_plus_1[ptot[j+1]]/4) * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2
                                                                    -(-self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]+self.Dbiops_plus_1[ptot[j+1]]/4) * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2/2)

                    if j < len(ptot) - 1:
                        numa =layers[j].nchemicals
                        numb =layers[j+1].nchemicals
                        i = cptot[j+1]
                        p = ptot[j+1]
                        if p != self.ptot[-1] and p != self.pbio:
                            for n in range(self.nchemicals):
                                chemical = self.chemicals[n]
                                for component in layers[j].components:
                                    if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                        if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                            self.NR[cptot[j+1]+n,cptot[j+1]-2*numa+n] = (self.NR[cptot[j+1]+n,cptot[j+1]-2*numa+n]
                                                                                         -self.Dbiops_plus_1[p] * FisL[component.name][ptot[j]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*numa+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])/2
                                                                                         +self.Dbiops_plus_1[p] * FisL[component.name][ptot[j]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])/2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]-numa+n] = (self.NR[cptot[j+1]+n,cptot[j+1]-numa+n]
                                                                                        +self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-numa+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*2
                                                                                        -self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+n]
                                                                                    -self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*3/2
                                                                                    +self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*3/2)
                                for component in layers[j+1].components:
                                    if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                        if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                            self.NR[cptot[j+1]+n,cptot[j+1]+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+n]
                                                                                    +self.DbiopsL_plus_1[p] * FisL[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*3/2
                                                                                    -self.DbiopsL_plus_1[p] * FisL[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*3/2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+numb+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+numb+n]
                                                                                        -self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*2
                                                                                        +self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+2*numb+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+2*numb+n]
                                                                                            +self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+2*numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])/2
                                                                                            -self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+2*numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])/2)


        if self.timeoption == 'Implicit':
            # Correct the non-linear sorption terms in Newton Raphson Matrix
            for j in range(len(ptot) - 1):
                layer = layers[j]
                num = layers[j].nchemicals
                if self.sorp == 1:
                    for n in range(self.nchemicals):
                        chemical = self.chemicals[n]
                        for component in layer.components:
                            if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                    for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                                        i = ii + 1
                                        self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n] = (self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n]
                                                                    -Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt
                                                                    +Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt)

                                    self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                -Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt
                                                                +Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/self.delt)

                # Correct the non-linear reaction terms in Newton Raphson Matrix
                if self.reac == 1:
                    for n in range(num):
                        chemical = layers[j].chemicals[n]
                        for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                            i = ii + 1
                            for nn in range(num):
                                self.NR[cptot[j]+i*num+n, cptot[j]+i*num+nn] = self.NR[cptot[j]+i*num+n, cptot[j]+i*num+nn] - self.rates_diff[cptot[j]+i*num+n, cptot[j]+i*num+nn]
                        for nn in range(num):
                            self.NR[cptot[j+1]-num+n, cptot[j+1]-num+nn] = self.NR[cptot[j+1]-num+n, cptot[j+1]-num+nn] - self.rates_diff[cptot[j+1]-num+n, cptot[j+1]-num+nn]

            if self.bio == 1 and self.Dbiop > 0 and self.sorp == 1:
                for j in range(self.layerbio+1):
                    layer = layers[j]
                    num = layers[j].nchemicals
                    for n in range(self.nchemicals):
                        chemical = self.chemicals[n]
                        for component in layer.components:
                            if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                    for ii in range((ptot[j+1] - 1-(ptot[j] + 1))):
                                        i = ii + 1
                                        self.NR[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n] = (self.NR[cptot[j]+i*num+n,cptot[j]+(i-1)*num+n]
                                                                                            +(self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]-self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * FisL[component.name][ptot[j]+(i-1)] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+(i-1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                                            -(self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]-self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * FisL[component.name][ptot[j]+(i-1)] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+(i-1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                        self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n] = (self.NR[cptot[j]+i*num+n,cptot[j]+i*num+n]
                                                                    -(self.DbiopsL_plus_1[ptot[j]+i]) * Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2
                                                                    +(self.DbiopsL_plus_1[ptot[j]+i]) * Fis[component.name][ptot[j]+i] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+i*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2)

                                        self.NR[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n] = (self.NR[cptot[j]+i*num+n,cptot[j]+(i+1)*num+n]
                                                                    +(-self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]+self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * Fis[component.name][ptot[j]+(i+1)] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j]+(i+1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    -(-self.DbiopsL_plus_1[ptot[j]+(i-1)]/4+self.DbiopsL_plus_1[ptot[j]+i]+self.DbiopsL_plus_1[ptot[j]+(i+1)]/4) * Fis[component.name][ptot[j]+(i+1)] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j]+(i+1)*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                    if ptot[j+1] == self.pbio:

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n]
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/2 * FisL[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/2 * FisL[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/4 * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]+self.Dbiops_plus_1[ptot[j+1]-1])/4 * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2)

                                    else:
                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-2*num+n]
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]-self.Dbiops_plus_1[ptot[j+1]]/4) * FisL[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]-self.Dbiops_plus_1[ptot[j+1]]/4) * FisL[component.name][ptot[j+1]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]-num+n]
                                                                    -(self.Dbiops_plus_1[ptot[j+1]-1]) * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2
                                                                    +(self.Dbiops_plus_1[ptot[j+1]-1]) * Fis[component.name][ptot[j+1]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2*2)

                                        self.NR[cptot[j+1]-num+n,cptot[j+1]+n] = (self.NR[cptot[j+1]-num+n,cptot[j+1]+n]
                                                                    +(-self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]+self.Dbiops_plus_1[ptot[j+1]]/4) * Fis[component.name][ptot[j+1]] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2
                                                                    -(-self.Dbiops_plus_1[ptot[j+1]-2]/4+self.Dbiops_plus_1[ptot[j+1]-1]+self.Dbiops_plus_1[ptot[j+1]]/4) * Fis[component.name][ptot[j+1]] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])**2)


                    if j < len(ptot)-1:
                        numa =layers[j].nchemicals
                        numb =layers[j+1].nchemicals
                        i = cptot[j+1]
                        p = ptot[j+1]
                        if p != self.ptot[-1] and p != self.pbio:
                            for n in range(self.nchemicals):
                                chemical = self.chemicals[n]
                                for component in layers[j].components:
                                    if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                        if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                            self.NR[cptot[j+1]+n,cptot[j+1]-2*numa+n] = (self.NR[cptot[j+1]+n,cptot[j+1]-2*numa+n]
                                                                        -self.Dbiops_plus_1[p] * FisL[component.name][ptot[j]-2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-2*numa+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])/2
                                                                        +self.Dbiops_plus_1[p] * FisL[component.name][ptot[j]-2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-2*num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])/2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]-numa+n] = (self.NR[cptot[j+1]+n,cptot[j+1]-numa+n]
                                                                        +self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]-1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]-numa+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*2
                                                                        -self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]-1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]-num+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+n]
                                                                        -self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*3/2
                                                                        +self.Dbiops_plus_1[p] * Fis[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j]+1]-self.z[ptot[j]])*3/2)
                                for component in layers[j+1].components:
                                    if self.sorptions[component.name][chemical.name].kinetic == 'Equilibrium':
                                        if self.sorptions[component.name][chemical.name].isotherm == 'Freundlich' or self.sorptions[component.name][chemical.name].isotherm == 'Langmuir':
                                            self.NR[cptot[j+1]+n,cptot[j+1]+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+n]
                                                                        +self.DbiopsL_plus_1[p] * FisL[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*3/2
                                                                        -self.DbiopsL_plus_1[p] * FisL[component.name][ptot[j]] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*3/2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+numb+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+numb+n]
                                                                        -self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+1] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*2
                                                                        +self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+1] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])*2)

                                            self.NR[cptot[j+1]+n,cptot[j+1]+2*numb+n] = (self.NR[cptot[j+1]+n,cptot[j+1]+2*numb+n]
                                                                        +self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+2] * component.rho * self.sorptions[component.name][chemical.name].get_K(component, Cn[cptot[j+1]+2*numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])/2
                                                                        -self.DbiopsL_plus_1[p] * Fis[component.name][ptot[j]+2] * component.rho * self.sorptions[component.name][chemical.name].get_NR(Cn[cptot[j+1]+2*numb+n]*chemical.MW, self.Cmax[chemical.name]*chemical.MW)/(self.z[ptot[j+1]+1]-self.z[ptot[j+1]])/2)


    def make_matrix_parameter_vectors(self, Cn, Fis, FisL):

        self.make_grid_es_rhos(Fis, FisL)
        self.make_grid_Rs(Cn, Fis, FisL)

    def make_transport_parameter_vectors(self):

        self.make_grid_Us()
        self.make_grid_Ds()

    def make_reaction_parameter_vectors(self, Cn, Fis):

        self.make_grid_elams(Fis)
        self.make_grid_rates(Cn, Fis)
        self.make_grid_rates_plus_1(Cn, Fis)

    def make_matrices(self):
        """Generates the discretized variables necessary to perform a finite
        difference analysis of the underlying governing differential equations
        and auxiliary conditions for a linear system.  The "A," "B," and "b"
        matrices are used to determine the concentrations at the succeeding
        time step from:

        A * Cn+1 = B * Cn + b

        Cn -- the concentrations in the grid at time n
        """

        self.A = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals]))
        self.B = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals]))
        self.a = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, 1]))
        self.b = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, 1]))

        self.make_boundary_equations()
        self.make_governing_equations()

    def make_components_matrices(self):

        self.Acomp = matrix(zeros([self.ptot[-1] + 1, self.ptot[-1] + 1]))
        self.Bcomp = matrix(zeros([self.ptot[-1] + 1, self.ptot[-1] + 1]))
        self.acomp = matrix(zeros([self.ptot[-1] + 1, 1]))
        self.bcomp = matrix(zeros([self.ptot[-1] + 1, 1]))

        self.make_components_equations()

    def update_time_dependents(self):

        self.U      = self.U_plus_1

        if self.bio == 1:
            self.Dbiops = [Dbiop for Dbiop in self.Dbiops_plus_1]
            self.DbiopsL= [Dbiop for Dbiop in self.DbiopsL_plus_1]

        self.es     = [e for e in self.es_plus_1]
        self.rhos   = [rho for rho in self.rhos_plus_1]
        self.Dws    = [tort for tort in self.Dws_plus_1]
        self.Ks     = [R for R in self.Ks_plus_1]
        self.Rs     = [R for R in self.Rs_plus_1]
        self.Ss     = [S for S in self.Ss_plus_1]
        self.Us     = [U for U in self.Us_plus_1]
        self.Ds     = [D for D in self.Ds_plus_1]

        self.esL     = [e for e in self.esL_plus_1]
        self.rhosL   = [rho for rho in self.rhosL_plus_1]
        self.DwsL    = [tort for tort in self.DwsL_plus_1]
        self.KsL     = [R for R in self.KsL_plus_1]
        self.SsL     = [S for S in self.SsL_plus_1]
        self.RsL     = [R for R in self.RsL_plus_1]
        self.UsL     = [U for U in self.UsL_plus_1]
        self.DsL     = [D for D in self.DsL_plus_1]

        self.elams  = self.elams_plus_1.copy()
        self.rates  = self.rates_plus_1.copy()

    def update_bioturbation(self):

        i                = 0
        self.pbio        = 0
        flag             = 0
        while flag == 0:

            if i <= len(self.ptot) - 1:

                if (self.z[self.ptot[i]]-self.z[0]) < self.hbio:
                    i = i + 1
                else:
                    self.pbio = self.ptot[i-1] + int(round((self.hbio - (self.z[self.ptot[i-1]]-self.z[0])) / (self.z[self.ptot[i-1]+1] -self.z[self.ptot[i-1]] ), 8))
                    self.cpbio = self.cptot[i-1] + (self.pbio - self.ptot[i-1]) * self.layertot[i-1].nchemicals
                    self.layerbio = i - 1
                    flag = 1
            else:
                self.pbio = self.ptot[i-1]
                self.cpbio = self.cptot[i-1]
                self.layerbio = i - 2
                flag = 2

        if flag == 1:
            if self.ptot[self.layerbio + 1] - self.pbio   <= 1:
                self.pbio = self.ptot[self.layerbio + 1]
                self.cpbio = self.cptot[self.layerbio + 1]
            elif self.pbio - self.ptot[self.layerbio]     <= 1:
                if self.layerbio == 0:
                    self.pbio = self.ptot[self.layerbio] + 2
                    self.cpbio = self.cptot[self.layerbio] + 2
                else:
                    self.pbio = self.ptot[self.layerbio]
                    self.cpbio = self.cptot[self.layerbio]
                    self.layerbio = self.layerbio - 1


    def update_deposition(self, Cn, Fis_load, FisL_load, FisM_load, t):
        """Updates the grid for deposition."""

        updatecheck = 0

        Fis  = {}
        FisL = {}
        FisM = {}
        for component in self.components:
            Fis[component.name]  = [Fi for Fi in Fis_load[component.name]]
            FisL[component.name] = [Fi for Fi in FisL_load[component.name]]
            FisM[component.name] = [Fi for Fi in FisM_load[component.name]]

        if self.depsize >= self.delzdep:                                                                                                                self.depcheck = -1
        else:
            if self.z[0] == 0:
                if self.Vdep * t >= self.depsize * 2:                                                                                                   self.depcheck = 2
                else:                                                                                                                                   self.depcheck = 0
            elif round(self.Vdep*t-abs(self.z[0]), 8) >= round(self.depsize, 8):                                                                        self.depcheck = 1
            else:                                                                                                                                       self.depcheck = 0

        if self.depcheck < 0:
            if self.z[0] == 0:
                if self.Vdep*t >= 2 * self.delzdep:
                    points = int(round((self.Vdep * t)/self.delzdep, 8))
                    self.ptot  = [0] + [p +  points for p  in self.p]
                    self.cptot = [0] + [cp + points * self.deplayer[0].nchemicals for cp in self.cp]
                    self.layertot = self.deplayer + self.layers
                    for component in self.components:
                        Fis[component.name][0] = 0
                        FisM[component.name][0] = FisM[component.name][0]/2
                    for component in self.deplayer[0].init_components:
                        Fis[component.name][0] = component.fraction
                        FisM[component.name][0] = FisM[component.name][0] + component.fraction/2
                else:
                    points = 0
            else:
                points = int(round((self.Vdep*t -abs(self.z[0]))/self.delzdep, 8))
                self.ptot     = [ptot + points for ptot in self.ptot]
                self.cptot    = [cptot + points * self.deplayer[0].nchemicals for cptot in self.cptot]
                self.ptot[0]  = 0
                self.cptot[0] = 0

            if points > 0:
                try: Cn = list(Cn.copy())
                except: pass
                Cn_solid = []
                for solidchemical in self.deplayer[0].solidchemicals:
                    Cn_solid.append(self.ICs[self.deplayer[0].name][solidchemical.name].uniform)
                for i in range(points):
                    Cn = [self.BCs[chemical.name].Cw for chemical in (self.chemicals)] + Cn_solid + Cn
                    for component in self.components:
                        Fis[component.name].insert(0, 0)
                        FisL[component.name].insert(0, 0)
                        FisM[component.name].insert(0, 0)
                    for component in self.deplayer[0].init_components:
                        Fis[component.name][0] = component.fraction
                        FisL[component.name][0] = component.fraction
                        FisM[component.name][0] = component.fraction
                    self.z.insert(0, round(self.z[0]-self.delzdep, 8))
                updatecheck = 1

        elif self.depcheck == 2:

            self.toppoints = 2
            self.ptot  = [0] + [p +  self.toppoints for p  in self.p]
            self.cptot = [0] + [cp + self.toppoints * self.deplayer[0].nchemicals for cp in self.cp]
            try: Cn = list(Cn.copy())
            except: pass
            for component in self.components:
                Fis[component.name][0] = 0
                FisM[component.name][0] = FisM[component.name][0]/2
            for component in self.deplayer[0].init_components:
                Fis[component.name][0] = component.fraction
                FisM[component.name][0] = FisM[component.name][0] + component.fraction/2
            Cn_solid = []
            for solidchemical in self.deplayer[0].solidchemicals:
                Cn_solid.append(self.ICs[self.deplayer[0].name][solidchemical.name].uniform)
            for j in range(self.toppoints):
                Cn = [self.BCs[chemical.name].Cw for chemical in (self.chemicals)] + Cn_solid + Cn
                for component in self.components:
                    Fis[component.name].insert(0, 0)
                    FisL[component.name].insert(0, 0)
                    FisM[component.name].insert(0, 0)
                for component in self.deplayer[0].init_components:
                    Fis[component.name][0]  = component.fraction
                    FisL[component.name][0] = component.fraction
                    FisM[component.name][0] = component.fraction
                self.z.insert(0, - round(self.depsize * (j+1), 8))
            self.layertot = self.deplayer + self.layers

            updatecheck = 1

        elif self.depcheck == 1:

            updatecheck = 1

            points = int(round((self.Vdep*t-abs(self.z[0]))/self.depsize, 8))

            self.toppoints = self.toppoints + points
            self.ptot     = [ptot +  points for ptot in self.ptot]
            self.cptot    = [cptot + self.deplayer[0].nchemicals * points for cptot in self.cptot]
            self.ptot[0]  = 0
            self.cptot[0] = 0

            try: Cn = list(Cn.copy())
            except: pass
            Cn_solid = []
            for solidchemical in self.deplayer[0].solidchemicals:
                Cn_solid.append(self.ICs[self.deplayer[0].name][solidchemical.name].uniform)
            for i in range(points):
                Cn = [self.BCs[chemical.name].Cw for chemical in (self.chemicals)] + Cn_solid + Cn
                for component in self.components:
                    Fis[component.name].insert(0, 0)
                    FisL[component.name].insert(0, 0)
                    FisM[component.name].insert(0, 0)
                for component in self.deplayer[0].init_components:
                    Fis[component.name][0]  = component.fraction
                    FisL[component.name][0] = component.fraction
                    FisM[component.name][0] = component.fraction
                self.z.insert(0, round(self.z[0] - self.depsize, 8))

        if self.depcheck >= 0 and round(self.Vdep*t-abs(self.z[self.toppoints]), 8) > round(self.delzdep*1.5, 8) and round(self.Vdep*t, 8) > round(self.delzdep*2.5, 8):

            updatecheck = 1

            points = int(round(self.toppoints/self.depgrid, 8))
            toppoints_new = self.toppoints - points * self.depgrid

            if self.z[self.toppoints] == 0:
                self.ptot  = [0] + [p +  points * (1-self.depgrid) for p  in self.ptot]
                self.cptot = [0] + [cp + points * (1-self.depgrid) * self.deplayer[0].nchemicals for cp in self.cptot]
                self.ptot[1]  = toppoints_new
                self.cptot[1] = toppoints_new* self.deplayer[0].nchemicals
            else:
                self.ptot     = [ptot +  points * (1-self.depgrid) for ptot in self.ptot]
                self.cptot    = [cptot + points * (1-self.depgrid) * self.deplayer[0].nchemicals for cptot in self.cptot]
                self.ptot[0]  = 0
                self.cptot[0] = 0
                self.ptot[1]  = toppoints_new
                self.cptot[1] = toppoints_new* self.deplayer[0].nchemicals

            try: Cn = list(Cn.copy())
            except: pass

            z_top   = []
            Cn_top  = []
            Fis_top = {}

            z_mid   = []
            Cn_mid  = []
            Fis_mid = {}

            for toppoint in range(toppoints_new):
                for i in range(self.deplayer[0].nchemicals):
                    Cn_top.append(Cn[self.deplayer[0].nchemicals*toppoint+i])
                z_top.append(self.z[toppoint])
            for component in self.components:
                Fis_top[component.name] = []
                for toppoint in range(toppoints_new):
                    Fis_top[component.name].append(Fis[component.name][toppoint])

            for point in range(points):
                midpoint = toppoints_new + point * self.depgrid
                for i in range(self.deplayer[0].nchemicals):
                    Cn_mid.append(Cn[self.deplayer[0].nchemicals*midpoint+i])
            for component in self.components:
                Fis_mid[component.name] = []
                for point in range(points):
                    midpoint = toppoints_new + point * self.depgrid
                    Fis_mid[component.name].append(Fis[component.name][midpoint])

            for j in range (self.toppoints):
                self.z.remove(self.z[0])
            for point in range(points):
                self.z.insert(0, round(self.z[0]-self.delzdep, 8))
            for point in range(toppoints_new):
                self.z.insert(0, round(self.z[0]-self.depsize, 8))
            self.layertot = self.deplayer + self.deplayer + self.layers

            Cn = Cn[self.toppoints* self.deplayer[0].nchemicals:]
            for component in self.components:
                Fis[component.name]  = Fis[component.name][self.toppoints:]
                FisL[component.name] = FisL[component.name][self.toppoints:]
                FisM[component.name] = FisM[component.name][self.toppoints:]

            Cn  = Cn_top  + Cn_mid + Cn
            for component in self.components:
                Fis[component.name]  = Fis_top[component.name] + Fis_mid[component.name] + Fis[component.name]
                FisL[component.name] = Fis_top[component.name] + Fis_mid[component.name] + FisL[component.name]
                FisM[component.name] = Fis_top[component.name] + Fis_mid[component.name] + FisM[component.name]

            self.toppoints = toppoints_new

        if updatecheck == 1:

            if self.bio == 1:
                self.update_bioturbation()
                self.make_grid_Dbiops()

            self.make_matrix_parameter_vectors(Cn, Fis, FisL)
            self.make_transport_parameter_vectors()
            self.make_reaction_parameter_vectors(Cn, Fis)

        return Cn, Fis, FisL, FisM


    def update_consolidation(self, time, U):
        """Updates the Darcy velocity and then the equations if there is
        consolidation in the underlying sediment."""

        self.U_plus_1 = U + consolidation(time, self.Vcon0, self.kcon)

        self.make_grid_Us()
        self.make_grid_Ds()

    def update_tidal(self, time, U):
        """Updates the Darcy velocity and then the equations if there is
        consolidation in the underlying sediment."""

        self.U_plus_1 = U + tidal(time, self.Vtidal, self.ptidal)

        if self.topBCtype == 'Finite mixed water column':

            Q = self.taucoefs['Q'] - self.taucoefs['Qevap'] + self.taucoefs['V']/self.taucoefs['h']*self.U

            if self.dep == 1:
                if self.lengthunit == 'cm':         kdep  = self.Vdep/100
                elif self.lengthunit == u'\u03BCm': kdep  = self.Vdep/100/1000
                else:                               kdep  = self.Vdep
                epsilon = self.matrices[self.deplayer[0].type_index].e
                matrixa  = self.matrices[self.deplayer[0].type_index]
                dep_rho = matrixa.rho
                dep_fraction = []
                for component in matrixa.components:
                    dep_fraction.append(component.mfraction)
            else:
                kdep = 0
                epsilon = 0
                dep_rho = 0
                dep_fraction = []

            for n in range(len(self.chemicals)):
                chemical = self.chemicals[n]
                if self.taucoefs['Evap'] == 'None':  kevap = 0
                else:                                kevap = self.BCs[chemical.name].kevap
                if self.taucoefs['Decay'] == 'None': kdecay = 0
                else:                                kdecay = self.BCs[chemical.name].kdecay

                K = []
                if self.dep == 1:
                    matrixa  = self.matrices[self.deplayer[0].type_index]
                    for component in matrixa.components:
                        if self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kd specified': K.append(self.sorptions[component.name][chemical.name].K)
                        elif self.sorptions[component.name][chemical.name].isotherm == 'Linear--Kocfoc': K.append(10**self.sorptions[component.name][chemical.name].Koc)

                self.BCs[chemical.name].tau = tauwater(Q, self.taucoefs['DOC'], chemical.Kdoc, kdep, epsilon, dep_rho, dep_fraction, K, self.taucoefs['V'], self.taucoefs['h'], kevap, kdecay)

        self.make_grid_Us()
        self.make_grid_Ds()

    def update_nonlinear(self, Cn, Fis, FisL):
        """Updates the retardation factors, delt, and governing equations for
        nonlinear sorption."""

        Cn = transpose(array([i for i in Cn]))

        if self.sorp == 1:
            self.make_grid_Rs(Cn, Fis, FisL)
            self.make_grid_Ds()

        if self.reac == 1:
            self.make_grid_rates_plus_1(Cn, Fis)
            self.make_grid_rates_diff(Cn, Fis)

        self.A = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals]))
        self.B = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, self.cptot[-1] + self.layertot[-1].nchemicals]))
        self.a = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, 1]))
        self.b = matrix(zeros([self.cptot[-1] + self.layertot[-1].nchemicals, 1]))

        self.make_boundary_equations()
        self.make_governing_equations()
        self.make_Newton_Raphson_equations(Cn, Fis, FisL)

        #return Cn_new

    def non_linear_solver(self, Cn, Fis, FisL):

        convergence_check = 0
        A_old = self.A.copy()
        B_old = self.B.copy()
        b_old = self.b.copy()

        self.update_nonlinear(Cn, Fis, FisL)

        Cn_old = self.get_Cn_plus_1(Cn)

        while convergence_check == 0:
            self.update_nonlinear(Cn_old, Fis, FisL)
            Cn_new = Cn_old - array(transpose(linalg.solve(self.NR, self.A * transpose(matrix(Cn_old)) + self.a - B_old * transpose(matrix(Cn)) - b_old)))[0]

            SE   = zeros((self.nchemicals))
            AVG  = zeros((self.nchemicals))
            RMSE = zeros((self.nchemicals))

            for j in range(len(self.layertot)):
                num = (self.layertot)[j].nchemicals
                for i in range(self.ptot[j+1]-self.ptot[j]):
                    for n in range(self.nchemicals):
                        SE[n]  = SE[n]  + (Cn_new[self.cptot[j]+i*num + n]-Cn_old[self.cptot[j]+i*num + n])**2/(len(self.z)-1)
                        AVG[n] = AVG[n] + abs(Cn_new[self.cptot[j]+i*num + n])/(len(self.z)-1)

            RMSE[n] = SE[n]/AVG[n]

            if sum([(RMSE[n] > self.nlerror) for n in range((self.nchemicals))]) == 0:
                convergence_check = 1
            else:
                Cn_old = Cn_new

        self.update_nonlinear(Cn_new, Fis, FisL)

        return Cn_new

    def get_Fis_plus_1(self, Fis, FisL, FisM):
        """Uses the matrices to solve the system.  Returns the concentrations
        at the next time step in a one-dimensional row array."""
        Fis_plus_1  = {}
        FisL_plus_1 = {}
        FisM_plus_1 = {}

        for component in self.components:
            FisM_plus_1[component.name]  = list(array((transpose(linalg.solve(self.Acomp, self.Bcomp * transpose(matrix(FisL[component.name]))))))[0])
            if self.pbio < self.ptot[-1]:
                Fis_plus_1[component.name]   = FisM_plus_1[component.name][:self.pbio] + Fis[component.name][self.pbio:]
                FisL_plus_1[component.name]  = FisM_plus_1[component.name][:self.pbio] + FisL[component.name][self.pbio:]
            else:
                Fis_plus_1[component.name]   = FisM_plus_1[component.name][:]
                FisL_plus_1[component.name]  = FisM_plus_1[component.name][:]

        return Fis_plus_1, FisL_plus_1, FisM_plus_1

    def get_Cn_plus_1(self, Cn):
        """Uses the matrices to solve the system.  Returns the concentrations
        at the next time step in a one-dimensional row array."""

        return array((transpose(linalg.solve(self.A, self.B * transpose(matrix(Cn)) + self.b - self.a))))[0]


    def get_Cws(self, C, O = None, flag = None):

        Cws = zeros(self.nchemicals)

        for n in range (self.nchemicals):

            Cws[n] = ((self.U*(1 + self.taucoefs['DOC']/10**6*10**self.chemicals[n].Kdoc)+self.BCs[self.chemicals[n].name].k)/self.taucoefs['h']
                      /(self.BCs[self.chemicals[n].name].tau+self.BCs[self.chemicals[n].name].k/self.taucoefs['h'])*C[0,n])

        return Cws


    def get_fluxes(self, C, O = None, flag = None, Cn_top = None, O_top = None):
        """Calculates the fluxes in the domain "z" using the concentration at
        each grid point "C," the Darcy velocity "U," and the diffusion
        coefficient at each grid point "D." Converts units to ug/m2/yr."""

        U       = self.U_plus_1
        Ds      = self.Ds_plus_1

        ptot    = []
        cptot   = []
        layers  = []
        for i in self.ptot: ptot.append(i)
        for i in self.cptot: cptot.append(i)

        for layer in self.layertot:
            layers.append(layer)

        i    = 0
        if self.bio == 1:

            if ptot.count(self.pbio) == 0:
                ptot.insert(self.layerbio + 1, self.pbio)
                cptot.insert(self.layerbio + 1, self.cpbio)
                layers.insert(self.layerbio + 1, self.layertot[self.layerbio])

            if self.dep == 1 and self.toppoints > 1:
                F = zeros(((len(self.z)-self.toppoints + 1), self.nchemicals))

                for n in range (self.nchemicals):
                    chemical = self.chemicals[n]
                    for jj in range(len(ptot) - 2):
                        j = jj + 1
                        for i in range(ptot[j] + 1, ptot[j+1]):
                            ii = i - ptot[j]
                            iii = i - self.toppoints + 1
                            if i == self.pbio - 1 :
                                KDbiops_plus_1  = [self.Dbiops_plus_1[i]*self.KsL_plus_1[cptot[j]+(ii-1)*layers[j].nchemicals+n],
                                                   self.Dbiops_plus_1[i]*self.Ks_plus_1[cptot[j]+ii*layers[j].nchemicals+n]]
                                top_flux = self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n]*(C[iii,n]-C[iii-1,n])/(self.z[i]-self.z[i-1])+ U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc)*C[iii,n]+(KDbiops_plus_1[1]*C[iii,n]-KDbiops_plus_1[0]*C[iii-1,n])/(self.z[i]-self.z[i-1])
                                bot_flux = self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n]*(C[iii,n]-C[iii-1,n])/(self.z[i]-self.z[i-1])+ U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc)*C[iii,n]
                                F[iii,n] = (top_flux + bot_flux) / 2 * self.flux_factor
                            else:
                                KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+(ii-1)*layers[j].nchemicals+n],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+ii*layers[j].nchemicals+n],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+(ii+1)*layers[j].nchemicals+n]]
                                F[iii,n] =  get_point_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[iii-1:iii+2,n], self.z[i-1:i+2]) * self.flux_factor

                        i = ptot[j]
                        iii = i - self.toppoints + 1
                        KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+layers[j].nchemicals+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+2*layers[j].nchemicals+n]]
                        F[iii,n] = get_top_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[cptot[j]+n], KDbiops_plus_1, C[iii:iii+3,n], self.z[i:i+3]) * self.flux_factor


                    if self.topBCtype =='Mass transfer':
                        F[0,n] = get_surface_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.BCs[chemical.name].k, Cn_top[0,n], self.BCs[chemical.name].Cw ) * self.flux_factor
                    else:
                        KDbiops_plus_1  = [self.Dbiops_plus_1[0]*self.KsL_plus_1[n],
                                           self.Dbiops_plus_1[0]*self.Ks_plus_1[layers[0].nchemicals+n],
                                           self.Dbiops_plus_1[0]*self.Ks_plus_1[2*layers[0].nchemicals+n]]
                        F[0,n] = get_top_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[n], KDbiops_plus_1, Cn_top[0:3, n], self.z[0:3]) * self.flux_factor

                    if self.pbio <> ptot[-1]:
                        i   = ptot[-1]
                        iii = i - self.toppoints + 1
                        KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[-1]-2*layers[-1].nchemicals+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[-1]-layers[-1].nchemicals+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[-1]+n]]
                        F[-1,n] = get_boundary_flux(U* (1+layers[-1].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[-1]+n] , KDbiops_plus_1, C[-3:,n], self.z[-3:]) * self.flux_factor

                if self.nsolidchemicals > 0:
                    for jj in range(len(ptot) - 2):
                        j = jj + 1
                        num = layers[j].nchemicals
                        layer = layers[j]
                        for solidchemical in layers[j].solidchemicals:
                            n  = self.solidchemical_list.index(solidchemical.name)
                            nn = self.chemical_list.index(solidchemical.chemical_name)
                            na = layer.solidchemical_list.index(solidchemical.name)
                            for i in range(ptot[j] + 1, ptot[j+1]):
                                ii = i - ptot[j]
                                iii = i - self.toppoints + 1
                                if i <= self.pbio:
                                    KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+(ii-1)*num+self.nchemicals+n],
                                                       self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+ii*num+self.nchemicals+n],
                                                       self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+(ii+1)*num+self.nchemicals+n]]
                                    F[iii,nn] =  F[iii,nn] + get_point_flux(0, 0, KDbiops_plus_1, O[iii-1:iii+2,n], self.z[i-1:i+2]) * self.flux_factor

                            i = ptot[j]
                            iii = i - self.toppoints + 1
                            if i <= self.pbio and j < len(ptot) - 2:
                                nb = layers[j].solidchemical_list.index(solidchemical.name)
                                KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+self.nchemicals+nb],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+layers[j].nchemicals+self.nchemicals+nb],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+2*layers[j].nchemicals+self.nchemicals+nb]]
                                F[iii,nn] =  F[iii,nn] + get_top_flux(0, 0, KDbiops_plus_1, O[iii:iii+3,n], self.z[i:i+3]) * self.flux_factor
            else:
                F = zeros((len(self.z), self.nchemicals))

                for n in range (self.nchemicals):
                    chemical = self.chemicals[n]
                    for j in range(len(ptot) - 1):
                        for i in range(ptot[j] + 1, ptot[j+1]):
                            ii = i - ptot[j]
                            if i == self.pbio - 1 :
                                KDbiops_plus_1  = [self.DbiopsL[i]*self.KsL_plus_1[cptot[j]+(ii-1)*layers[j].nchemicals+n],
                                                   self.Dbiops[i] *self.Ks_plus_1[cptot[j]+ii*layers[j].nchemicals+n]]
                                top_flux = self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n]*(C[i,n]-C[i-1,n])/(self.z[i]-self.z[i-1])+ U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc)*C[i,n]+(KDbiops_plus_1[1]*C[i,n]-KDbiops_plus_1[0]*C[i-1,n])/(self.z[i]-self.z[i-1])
                                bot_flux = self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n]*(C[i+1,n]-C[i,n])/(self.z[i]-self.z[i-1])+ U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc)*C[i,n]
                                F[i,n] = (top_flux + bot_flux) / 2 * self.flux_factor
                            else:
                                KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+(ii-1)*layers[j].nchemicals+n],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+ii*layers[j].nchemicals+n],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+(ii+1)*layers[j].nchemicals+n]]
                                F[i,n] =  get_point_flux(U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[i-1:i+2,n], self.z[i-1:i+2]) * self.flux_factor
                        i = ptot[j+1]
                        if i == self.pbio:
                            F[i,n] = (self.Ds_plus_1[cptot[j+1]+n]*(C[i,n]-C[i-1,n])/(self.z[i-1]-self.z[i-2])+ U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc)*C[i,n]) * self.flux_factor
                        else:
                            KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j+1]-2*layers[j].nchemicals+n],
                                               self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j+1]-layers[j].nchemicals+n],
                                               self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j+1]+n]]
                            F[i,n] = get_boundary_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[j+1]+n], KDbiops_plus_1, C[i-2:i+1,n], self.z[i-2:i+1]) * self.flux_factor

                    if self.topBCtype =='Mass transfer':
                        F[0,n] = get_surface_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.BCs[chemical.name].k, C[0,n], self.BCs[chemical.name].Cw ) * self.flux_factor
                    else:
                        KDbiops_plus_1  = [self.DbiopsL_plus_1[0]*self.KsL_plus_1[n],
                                           self.DbiopsL_plus_1[0]*self.Ks_plus_1[layers[0].nchemicals+n],
                                           self.DbiopsL_plus_1[0]*self.Ks_plus_1[2*layers[0].nchemicals+n]]
                        F[0,n] = get_top_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[n], KDbiops_plus_1, C[0:3,n], self.z[0:3]) * self.flux_factor

                    if self.pbio <> ptot[-1]:
                        i = ptot[-1]
                        KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[-1]-2*layers[j].nchemicals+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[-1]-layers[j].nchemicals+n],
                                           self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[-1]+n]]
                        F[i,n] = get_boundary_flux(U* (1+layers[-1].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[-1]+n] ,KDbiops_plus_1,  C[-3:,n], self.z[-3:]) * self.flux_factor

                if self.nsolidchemicals > 0:
                    for j in range(len(ptot) - 1):
                        layer = layers[j]
                        for solidchemical in layer.solidchemicals:
                            n  = self.solidchemical_list.index(solidchemical.name)
                            nn = self.chemical_list.index(solidchemical.chemical_name)
                            na = layer.solidchemical_list.index(solidchemical.name)
                            nb = layer.solidchemical_list.index(solidchemical.name)
                            num = layer.nchemicals
                            for i in range(ptot[j] + 1, ptot[j+1]):
                                if i <= self.pbio:
                                    ii = i - ptot[j]
                                    KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+(ii-1)*num+self.nchemicals+na],
                                                       self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+ii*num+self.nchemicals+na],
                                                       self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+(ii+1)*num+self.nchemicals+na]]
                                    F[i,nn] =  F[i,nn] + get_point_flux(0, 0, KDbiops_plus_1, O[i-1:i+2,n], self.z[i-1:i+2]) * self.flux_factor

                            i = ptot[j]
                            if i <= self.pbio and j < len(ptot) - 1:

                                KDbiops_plus_1  = [self.DbiopsL_plus_1[i]*self.KsL_plus_1[cptot[j]+self.nchemicals+na],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+num+self.nchemicals+na],
                                                   self.DbiopsL_plus_1[i]*self.Ks_plus_1[cptot[j]+2*num+self.nchemicals+na]]
                                F[i,nn] =  F[i,nn] + get_top_flux(0, 0, KDbiops_plus_1, O[i:i+3,n], self.z[i:i+3]) * self.flux_factor
        else:
            if self.dep == 1 and self.toppoints > 1:
                F = zeros(((len(self.z)-self.toppoints + 1), self.nchemicals))

                for n in range (self.nchemicals):
                    chemical = self.chemicals[n]
                    for jj in range(len(ptot) - 2):
                        j = jj + 1
                        for i in range(ptot[j] + 1, ptot[j+1]):
                            ii = i - ptot[j]
                            iii = i - self.toppoints + 1
                            if ii == 0:
                                KDbiops_plus_1 =  [0,0,0]
                                F[iii,n] =  get_point_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[iii-1:iii+2,n], self.z[i-1:i+2]) * self.flux_factor
                            else:
                                KDbiops_plus_1 =  [0,0,0]
                                F[iii,n] =  get_point_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[iii-1:iii+2,n], self.z[i-1:i+2]) * self.flux_factor

                        i = ptot[j]
                        iii = i - self.toppoints + 1
                        KDbiops_plus_1 =  [0,0,0]
                        F[iii,n] = get_top_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[cptot[j]+n], KDbiops_plus_1, C[iii:iii+3,n], self.z[i:i+3]) * self.flux_factor

                    if self.topBCtype =='Mass transfer':
                        F[0,n] = get_surface_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.BCs[chemical.name].k, Cn_top[0,n], self.BCs[chemical.name].Cw ) * self.flux_factor
                    else:
                        KDbiops_plus_1 =  [0,0,0]
                        F[0,n] = get_top_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[n], KDbiops_plus_1, Cn_top[0:3, n], self.z[0:3]) * self.flux_factor

                    if self.bio == 1 and self.pbio <> ptot[-1]:
                        i   = ptot[-1]
                        KDbiops_plus_1 =  [0,0,0]
                        F[-1,n] = get_boundary_flux(U* (1+layers[-1].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[-1]+n] , KDbiops_plus_1, C[-3:,n], self.z[-3:]) * self.flux_factor

            else:
                F = zeros((len(self.z), self.nchemicals))

                for n in range (self.nchemicals):
                    #top boundary
                    chemical = self.chemicals[n]

                    for j in range(len(ptot) - 1):
                        #loop through the interior points of the layers
                        for i in range(ptot[j] + 1, ptot[j+1]):
                            ii = i - ptot[j]
                            if ii == 0:
                                KDbiops_plus_1 =  [0,0,0]
                                F[i,n] =  get_point_flux(U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[i-1:i+2,n], self.z[i-1:i+2]) * self.flux_factor
                            else:
                                KDbiops_plus_1 =  [0,0,0]
                                F[i,n] =  get_point_flux(U*(1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[j]+ii*layers[j].nchemicals+n], KDbiops_plus_1, C[i-1:i+2,n], self.z[i-1:i+2]) * self.flux_factor

                        i = ptot[j+1]
                        KDbiops_plus_1 =  [0,0,0]
                        F[i,n] = get_boundary_flux(U* (1+layers[j].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[j+1]+n], KDbiops_plus_1, C[i-2:i+1,n], self.z[i-2:i+1]) * self.flux_factor

                    if self.topBCtype =='Mass transfer':
                        F[0,n] = get_surface_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.BCs[chemical.name].k, C[0,n], self.BCs[chemical.name].Cw ) * self.flux_factor
                    else:
                        KDbiops_plus_1 =  [0,0,0]
                        F[0,n] = get_top_flux(U* (1+layers[0].doc/(10**6)*10**chemical.Kdoc), self.DsL_plus_1[n], KDbiops_plus_1, C[0:3,n], self.z[0:3]) * self.flux_factor

                    if self.bio == 1 and self.pbio <> ptot[-1]:
                        i = ptot[-1]
                        KDbiops_plus_1 =  [0,0,0]
                        F[-1,n] = get_boundary_flux(U* (1+layers[-1].doc/(10**6)*10**chemical.Kdoc), self.Ds_plus_1[cptot[-1]+n] ,KDbiops_plus_1,  C[-3:,n], self.z[-3:]) * self.flux_factor

        return F

    def get_qs(self, C, Fis, O = None):
        """Calculates the solid-phase concentration "q" in the domain "z"
        using the pore water concentration at each grid point "C." """

        if self.dep == 1 and self.toppoints > 1:
            q = zeros(((len(self.z)-self.toppoints + 1), self.nchemicals))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for jj in range(len(self.ptot) - 2):
                    j = jj + 1
                    for i in range(self.ptot[j], self.ptot[j+1]):
                        iii = i - self.toppoints + 1
                        q[iii, n] = 0
                        matrix_rho = 0
                        for component in self.components:
                            q[iii,n] = q[iii,n] + self.sorptions[component.name][chemical.name].get_q(C[iii,n]) * Fis[component.name][i] * component.rho
                            matrix_rho = matrix_rho + Fis[component.name][i] * component.rho
                            if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                                for solidchemical in self.solidchemicals:
                                    if solidchemical.chemical_name == chemical.name and solidchemical.component_name == component.name:
                                        q[iii,n] = q[iii,n] + O[iii,self.solidchemicals.index(solidchemical)]* Fis[component.name][i] * component.rho
                        q[iii,n] = q[iii,n]/matrix_rho


        else:
            q = zeros((len(self.z), self.nchemicals))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for j in range(len(self.ptot) - 1):
                    for i in range(self.ptot[j], self.ptot[j+1]+1):
                        q[i, n] = 0
                        matrix_rho = 0
                        for component in self.components:
                            q[i,n] = q[i,n] + self.sorptions[component.name][chemical.name].get_q(C[i,n]) * Fis[component.name][i] * component.rho
                            matrix_rho = matrix_rho + Fis[component.name][i] * component.rho
                            if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                                for solidchemical in self.solidchemicals:
                                    if solidchemical.chemical_name == chemical.name and solidchemical.component_name == component.name:
                                        q[i,n] = q[i,n] + O[i,self.solidchemicals.index(solidchemical)]* Fis[component.name][i] * component.rho
                        q[i,n] = q[i,n]/matrix_rho
        return q

    def get_qms(self, C, Fis, O = None):
        """Calculates the solid-phase concentration "q" in the domain "z"
        using the pore water concentration at each grid point "C." """

        if self.dep == 1 and self.toppoints > 1:
            qm = zeros(((len(self.z)-self.toppoints + 1), self.nchemicals, len(self.components)))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for jj in range(len(self.ptot) - 2):
                    j = jj +1
                    for i in range(self.ptot[j], self.ptot[j+1]+1):
                        iii = i - self.toppoints + 1
                        for component in self.components:
                            m = self.component_list.index(component.name)
                            if Fis[component.name][i] > 0.0001:
                                qm[iii,n,m] = self.sorptions[component.name][chemical.name].get_q(C[iii,n])
                                if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                                    for solidchemical in self.solidchemicals:
                                        if solidchemical.chemical_name == chemical.name and solidchemical.component_name == component.name:
                                            qm[iii,n,m] = qm[iii,n,m] + O[iii,self.solidchemicals.index(solidchemical)]

        else:
            qm = zeros((len(self.z), self.nchemicals, len(self.components)))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for j in range(len(self.ptot) - 1):
                    for i in range(self.ptot[j], self.ptot[j+1]+1):
                        for component in self.components:
                            m = self.component_list.index(component.name)
                            if Fis[component.name][i] > 0.0001:
                                qm[i,n,m] = self.sorptions[component.name][chemical.name].get_q(C[i,n])
                                if self.sorptions[component.name][chemical.name].kinetic == 'Transient':
                                    for solidchemical in self.solidchemicals:
                                        if solidchemical.chemical_name == chemical.name and solidchemical.component_name == component.name:
                                            qm[i,n,m] = qm[i,n,m] + O[i,self.solidchemicals.index(solidchemical)]

        return qm


    def get_Ws(self,C, O = None):
        """Calculates the total (aqueous + solid-phase) concentration "W" in
        the domain "z" using the pore water concentration at each grid point
        "C." """

        if self.dep == 1 and self.toppoints > 1:
            W = zeros(((len(self.z)-self.toppoints + 1), self.nchemicals))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for jj in range(len(self.ptot) - 2):
                    j = jj + 1
                    layer  = self.layertot[j]
                    for i in range(self.ptot[j], self.ptot[j+1]+1):
                        iii = i - self.toppoints + 1
                        W[iii, n] = C[iii, n] *(1+layer.doc/(10**6)*10**chemical.Kdoc)

        else:
            W = zeros((len(self.z), self.nchemicals))
            for n in range (self.nchemicals):
                chemical = self.chemicals[n]
                for j in range(len(self.ptot) - 1):
                    layer  = self.layertot[j]
                    for i in range(self.ptot[j], self.ptot[j+1]+1):
                        W[i, n] = C[i, n] *(1+layer.doc/(10**6)*10**chemical.Kdoc)

        return W

class Output:
    """Stores the output information from a simulation."""

    def __init__(self, parameters):
        """Constructor method.  Essentially this just lumps the output data
        together for portability.  Variable definitions:

        C     -- Porewater concentrations at 250 times and all grid points
        F     -- Fluxes at 250 times and all grid points
        q     -- Solid concentrations at 250 times and all grid points
        W     -- Total concentrations at 250 times and all grid points
        z     -- The grid
        t     -- Times for the profiles for the other variables
        tCFqw -- A list of tuples containing the flux, pore water concentration,
                 solid and total concentration at a given time
                 at the depth of interest
        tplot -- A list of the times to get for plotting
        Cplot -- The porewater concentrations at the times in tplot
        Fplot -- The fluxes at the times in tplot
        qplot -- The solid concentrations at the times in tplot
        Wplot -- The total concentrations at the times in tplot
        """
        self.p                  = parameters.p
        self.z                  = parameters.zdep + parameters.z
        self.deplayer           = parameters.deplayer
        self.layers             = parameters.layers
        self.chemicals          = parameters.chemicals
        self.nchemicals         = parameters.nchemicals
        self.outputsteps        = parameters.outputsteps

        self.solidchemicals     = parameters.solidchemicals
        self.nsolidchemicals    = parameters.nsolidchemicals
        self.solidchemical_list = parameters.solidchemical_list

        self.times      = [parameters.tstart + round(i * (parameters.tfinal_ori-parameters.tstart)/self.outputsteps, 10) for i in range(self.outputsteps+1)]
        self.sizeflag = 0

        try:
            self.O  = zeros((len(self.times), len(self.z), parameters.nsolidchemicals))
            self.C  = zeros((len(self.times), len(self.z), parameters.nchemicals))
            self.F  = zeros((len(self.times), len(self.z), parameters.nchemicals))
            self.q  = zeros((len(self.times), len(self.z), parameters.nchemicals))
            self.W  = zeros((len(self.times), len(self.z), parameters.nchemicals))
            self.qm = zeros((len(self.times), len(self.z), parameters.nchemicals, len(parameters.components)))
            self.Cw = zeros((len(self.times), parameters.nchemicals))
            self.Fi = zeros((len(self.times), len(self.z), parameters.ncomponents))

        except :    self.sizeflag = 1
        self.n     = 0     #index of next time to collect data

        self.parameters = parameters

    def copy(self):

        output = Output(self.parameters)
        output.z = self.z

        return output


    def converter (self, parameters, Cn, Fis):

        """Stores the concentrations and fluxes from a given time."""
        self.ptot       = parameters.ptot
        self.cptot      = parameters.cptot
        self.layertot   = parameters.layertot

        z_t             = parameters.z

        if parameters.dep == 1 and parameters.toppoints > 1:

            toppoints           = parameters.toppoints
            pdep                = len(self.z) - (len(parameters.z) - toppoints + 1)

            Cn_2D               = zeros((len(self.z), parameters.nchemicals))
            Solid_Cn_2D         = zeros((len(self.z), self.nsolidchemicals))
            Fis_2D              = zeros((len(self.z), parameters.ncomponents))

            F_2D                = zeros((len(self.z), parameters.nchemicals))
            q_2D                = zeros((len(self.z), parameters.nchemicals))
            qm_2D               = zeros((len(self.z), parameters.nchemicals, len(parameters.components)))
            W_2D                = zeros((len(self.z), parameters.nchemicals))
            Cw                  = zeros(parameters.nchemicals)

            Cn_top_2D           = zeros((toppoints + 1, parameters.nchemicals))
            Solid_Cn_top_2D     = zeros((toppoints + 1, self.nsolidchemicals))
            Fis_top_2D          = zeros((toppoints + 1, parameters.ncomponents))

            for jj in range(len(self.layertot) - 1):
                j = jj + 1
                num = self.layertot[j].nchemicals
                for i in range((self.ptot[j+1]-self.ptot[j])):
                    for n in range(self.nchemicals):
                        Cn_2D[pdep + self.ptot[j] - toppoints + 1 + i,n] = Cn[self.cptot[j] + i*num + n] * self.chemicals[n].MW
                for n in range(self.nchemicals):
                    Cn_2D[pdep + self.ptot[-1] - toppoints + 1,n]        = Cn[self.cptot[-1] + n] * self.chemicals[n].MW
                    Cn_2D[pdep,n]                                        = Cn[n] * self.chemicals[n].MW
            for n in range(self.nchemicals):
                for i in range(toppoints + 1):
                    Cn_top_2D[i,n]        = Cn[self.layertot[0].nchemicals*i+n] * self.chemicals[n].MW

            if self.nsolidchemicals > 0:
                for jj in range(len(self.layertot) - 1):
                    j = jj + 1
                    num = self.layertot[j].nsolidchemicals
                    for i in range((self.ptot[j+1]-self.ptot[j])):
                        for n in range(num):
                            nn = parameters.solidchemical_list.index(self.layertot[j].solidchemicals[n].name)
                            Solid_Cn_2D[pdep + self.ptot[j] - toppoints + 1 + i,nn]        = Cn[self.cptot[j] + i*(self.nchemicals + num) + self.nchemicals + n] * self.solidchemicals[nn].MW
                for n in range(self.layertot[-1].nsolidchemicals):
                    nn = parameters.solidchemical_list.index(self.layertot[-1].solidchemicals[n].name)
                    Solid_Cn_2D[pdep + self.ptot[-1] - toppoints + 1, nn]                  = Cn[self.cptot[-1] + self.nchemicals + n] * self.solidchemicals[nn].MW
                    Solid_Cn_2D[pdep,nn]                                                   = Cn[self.nchemicals + n] * self.solidchemicals[nn].MW

                for n in range(self.nsolidchemicals):
                    for i in range(toppoints + 1):
                        Solid_Cn_top_2D[i,n]           = Cn[self.layertot[0].nchemicals*i+self.nchemicals+n] * self.chemicals[n].MW

            for jj in range(len(self.layertot) - 1):
                j = jj + 1
                for i in range((self.ptot[j+1]-self.ptot[j])):
                    for m in range(parameters.ncomponents):
                        Fis_2D[pdep + self.ptot[j] - toppoints + 1 + i,m] = Fis[parameters.components[m].name][self.ptot[j] + i]
                for m in range(parameters.ncomponents):
                    Fis_2D[pdep + self.ptot[-1]- toppoints + 1,m]         = Fis[parameters.components[m].name][self.ptot[-1]]
                    Fis_2D[pdep,m]                                        = Fis[parameters.components[m].name][0]

                for m in range(parameters.ncomponents):
                    for i in range(parameters.toppoints + 1):
                        Fis_top_2D[i,m]                                   = Fis[parameters.components[m].name][i]


            if self.nsolidchemicals > 0:
                F_2D[pdep:, :]      = parameters.get_fluxes(Cn_2D[pdep:, :], O = Solid_Cn_2D[pdep:, :], Cn_top = Cn_top_2D, O_top = Solid_Cn_top_2D )
                q_2D[pdep:, :]      = parameters.get_qs(Cn_2D[pdep:, :], Fis, Solid_Cn_2D[pdep:, :])
                W_2D[pdep:, :]      = parameters.get_Ws(Cn_2D[pdep:, :], Solid_Cn_2D[pdep:, :])
                qm_2D[pdep:, :, :]  = parameters.get_qms(Cn_2D[pdep:, :], Fis, Solid_Cn_2D[pdep:, :])
            else:
                F_2D[pdep:, :]      = parameters.get_fluxes(Cn_2D[pdep:, :], Cn_top = Cn_top_2D)
                q_2D[pdep:, :]      = parameters.get_qs(Cn_2D[pdep:, :], Fis)
                W_2D[pdep:, :]      = parameters.get_Ws(Cn_2D[pdep:, :])
                qm_2D[pdep:, :, :]  = parameters.get_qms(Cn_2D[pdep:, :], Fis)

            if parameters.topBCtype == 'Finite mixed water column':
                Cw = parameters.get_Cws(Cn_2D[pdep:, :], flag = 1)
            else:
                Cw = zeros(parameters.nchemicals)

        else:
            pdep            = len(self.z) - len(parameters.z)

            Cn_2D           = zeros((len(self.z), parameters.nchemicals))
            Solid_Cn_2D     = zeros((len(self.z), self.nsolidchemicals))
            F_2D            = zeros((len(self.z), parameters.nchemicals))
            q_2D            = zeros((len(self.z), parameters.nchemicals))
            qm_2D           = zeros((len(self.z), parameters.nchemicals, len(parameters.components)))
            W_2D            = zeros((len(self.z), parameters.nchemicals))
            Cw              = zeros(parameters.nchemicals)

            for j in range(len(self.layertot)):
                num = self.layertot[j].nchemicals
                for i in range((self.ptot[j+1]-self.ptot[j])):
                    for n in range(self.nchemicals):
                        Cn_2D[pdep + self.ptot[j] + i,n] = Cn[self.cptot[j] + i*num + n] * self.chemicals[n].MW
                for n in range(self.nchemicals):
                    Cn_2D[pdep + self.ptot[-1],n]        = Cn[self.cptot[-1] + n] * self.chemicals[n].MW

            if self.nsolidchemicals > 0:
                for j in range(len(self.layertot)):
                    num = self.layertot[j].nsolidchemicals
                    for i in range((self.ptot[j+1]-self.ptot[j])):
                        for n in range(num):
                            nn = parameters.solidchemical_list.index(self.layertot[j].solidchemicals[n].name)
                            Solid_Cn_2D[pdep + self.ptot[j] + i,nn]        = Cn[self.cptot[j] + i*(self.nchemicals + num) + self.nchemicals + n] * self.solidchemicals[nn].MW
                for n in range(self.layertot[-1].nsolidchemicals):
                    nn = parameters.solidchemical_list.index(self.layertot[-1].solidchemicals[n].name)
                    Solid_Cn_2D[pdep + self.ptot[-1],nn]        = Cn[self.cptot[-1] + self.nchemicals + n] * self.solidchemicals[nn].MW


            Fis_2D           = zeros((len(self.z), parameters.ncomponents))
            for j in range(len(self.layertot)):
                for i in range((self.ptot[j+1]-self.ptot[j])):
                    for m in range(parameters.ncomponents):
                        Fis_2D[pdep + self.ptot[j] + i,m]        = Fis[parameters.components[m].name][self.ptot[j] + i]
                for m in range(parameters.ncomponents):
                    Fis_2D[pdep + self.ptot[-1],m]               = Fis[parameters.components[m].name][self.ptot[-1]]

            if self.nsolidchemicals > 0:
                F_2D[pdep:, :]      = parameters.get_fluxes(Cn_2D[pdep:, :], O = Solid_Cn_2D[pdep:, :])
                q_2D[pdep:, :]      = parameters.get_qs(Cn_2D[pdep:, :], Fis, Solid_Cn_2D[pdep:, :])
                W_2D[pdep:, :]      = parameters.get_Ws(Cn_2D[pdep:, :], Solid_Cn_2D[pdep:, :])
                qm_2D[pdep:, :, :]  = parameters.get_qms(Cn_2D[pdep:, :], Fis, Solid_Cn_2D[pdep:, :])
            else:
                F_2D[pdep:, :]      = parameters.get_fluxes(Cn_2D[pdep:, :])
                q_2D[pdep:, :]      = parameters.get_qs(Cn_2D[pdep:, :], Fis)
                W_2D[pdep:, :]      = parameters.get_Ws(Cn_2D[pdep:, :])
                qm_2D[pdep:, :, :]  = parameters.get_qms(Cn_2D[pdep:, :], Fis)

            if parameters.topBCtype == 'Finite mixed water column':
                Cw = parameters.get_Cws(Cn_2D[pdep:, :], flag = 1)
            else:
                Cw = zeros(parameters.nchemicals)

        return [Cn_2D, Fis_2D, F_2D, q_2D, qm_2D, W_2D, Cw]

    def store(self, t, t_plus_1, parameters, variables, variables_plus_1):

        delt                  = t_plus_1 - t

        Cn_2D                 = variables[0]
        Fis_2D                = variables[1]
        F_2D                  = variables[2]
        q_2D                  = variables[3]
        qm_2D                 = variables[4]
        W_2D                  = variables[5]
        Cw_2D                 = variables[6]

        Cn_plus_1_2D          = variables_plus_1[0]
        Fis_plus_1_2D         = variables_plus_1[1]
        F_plus_1_2D           = variables_plus_1[2]
        q_plus_1_2D           = variables_plus_1[3]
        qm_plus_1_2D          = variables_plus_1[4]
        W_plus_1_2D           = variables_plus_1[5]
        Cw_plus_1_2D          = variables_plus_1[6]

        while self.n < len(self.times) and round(self.times[self.n], 8) <= round(t_plus_1, 8):

            time = self.times[self.n]
            self.C[self.n, :, :]         = time_interpolate(time, t, delt, Cn_2D, Cn_plus_1_2D)
            self.Fi[self.n, :, :]        = time_interpolate(time, t, delt, Fis_2D, Fis_plus_1_2D)
            self.F[self.n, :, :]         = time_interpolate(time, t, delt, F_2D,  F_plus_1_2D)
            self.q[self.n, :, :]         = time_interpolate(time, t, delt, q_2D,  q_plus_1_2D)
            self.qm[self.n, :, :, :]     = time_interpolate(time, t, delt, qm_2D, qm_plus_1_2D)
            self.W[self.n, :, :]         = time_interpolate(time, t, delt, W_2D,  W_plus_1_2D)
            if parameters.topBCtype == 'Finite mixed water column':
                for n in range(parameters.nchemicals):
                    self.Cw[self.n, :] = time_interpolate(self.times[self.n], t, delt, Cw_2D, Cw_plus_1_2D)

            self.n = self.n + 1

    def store_no_dep(self, Cn, Cn_plus_1, t, t_plus_1, parameters, Fis, Fis_plus_1):
        """Stores the concentrations and fluxes from a given time."""

        self.ptot       = parameters.ptot
        self.cptot      = parameters.cptot
        self.layertot   = parameters.layertot

        delt            = t_plus_1 - t
        pdep            = len(self.z) - len(parameters.z)

        z_t             = len(parameters.z)
        Cn_2D           = zeros((z_t, parameters.nchemicals))
        Cn_plus_1_2D    = zeros((z_t, parameters.nchemicals))

        for j in range(len(self.layertot)):
            num = self.layertot[j].nchemicals
            for i in range((self.ptot[j+1]-self.ptot[j])):
                for n in range(self.nchemicals):
                    Cn_2D[self.ptot[j] + i,n]        = Cn[self.cptot[j] + i*num + n] * self.chemicals[n].MW
                    Cn_plus_1_2D[self.ptot[j] + i,n] = Cn_plus_1[self.cptot[j] + i*num + n] * self.chemicals[n].MW
            for n in range(self.nchemicals):
                Cn_2D[self.ptot[-1],n]        = Cn[self.cptot[-1] + n] * self.chemicals[n].MW
                Cn_plus_1_2D[self.ptot[-1],n] = Cn_plus_1[self.cptot[-1] + n] * self.chemicals[n].MW

        if self.nsolidchemicals > 0:
            Solid_Cn_2D        = zeros((z_t, self.nsolidchemicals))
            Solid_Cn_plus_1_2D = zeros((z_t, self.nsolidchemicals))

            for j in range(len(self.layertot)):
                num = self.layertot[j].nsolidchemicals
                for i in range((self.ptot[j+1]-self.ptot[j])):
                    for n in range(num):
                        nn = parameters.solidchemical_list.index(self.layertot[j].solidchemicals[n].name)
                        Solid_Cn_2D[self.ptot[j] + i,nn]        = Cn[self.cptot[j] + i*(self.nchemicals + num) + self.nchemicals + n] * self.solidchemicals[nn].MW
                        Solid_Cn_plus_1_2D[self.ptot[j] + i,nn] = Cn_plus_1[self.cptot[j] + i*(self.nchemicals + num) + self.nchemicals + n] * self.solidchemicals[nn].MW

            for n in range(self.layertot[-1].nsolidchemicals):
                nn = parameters.solidchemical_list.index(self.layertot[-1].solidchemicals[n].name)
                Solid_Cn_2D[self.ptot[-1],nn]        = Cn[self.cptot[-1] + self.nchemicals + n] * self.solidchemicals[nn].MW
                Solid_Cn_plus_1_2D[self.ptot[-1],nn] = Cn_plus_1[self.cptot[-1]  + self.nchemicals + n] * self.solidchemicals[nn].MW

        Fis_2D           = zeros((z_t, parameters.ncomponents))
        Fis_plus_1_2D    = zeros((z_t, parameters.ncomponents))
        for j in range(len(self.layertot)):
            for i in range((self.ptot[j+1]-self.ptot[j])):
                for m in range(parameters.ncomponents):
                    Fis_2D[self.ptot[j] + i,m]        = Fis[parameters.components[m].name][self.ptot[j] + i]
                    Fis_plus_1_2D[self.ptot[j] + i,m] = Fis_plus_1[parameters.components[m].name][self.ptot[j] + i]
            for m in range(parameters.ncomponents):
                Fis_2D[self.ptot[-1],m]               = Fis[parameters.components[m].name][self.ptot[-1]]
                Fis_plus_1_2D[self.ptot[-1],m]        = Fis_plus_1[parameters.components[m].name][self.ptot[-1]]

        while self.n < len(self.times) and round(self.times[self.n], 8) <= round(t_plus_1, 8):
            self.C[self.n, pdep:, :]         = time_interpolate(self.times[self.n], t, delt, Cn_2D, Cn_plus_1_2D)
            self.Fi[self.n, pdep:, :]        = time_interpolate(self.times[self.n], t, delt, Fis_2D, Fis_plus_1_2D)
            if self.nsolidchemicals > 0:
                self.O[self.n, pdep:, :]     = time_interpolate(self.times[self.n], t, delt, Solid_Cn_2D, Solid_Cn_plus_1_2D)
                if self.n != 0:
                    self.F[self.n, pdep:, :] = time_interpolate(self.times[self.n], t, delt, parameters.get_fluxes(Cn_2D, O = Solid_Cn_2D, flag = 1), parameters.get_fluxes(Cn_plus_1_2D, O = Solid_Cn_plus_1_2D))
                self.q[self.n, pdep:, :]     = time_interpolate(self.times[self.n], t, delt, parameters.get_qs(Cn_2D, Fis, Solid_Cn_2D), parameters.get_qs(Cn_plus_1_2D, Fis_plus_1, Solid_Cn_plus_1_2D))
                self.W[self.n, pdep:, :]     = parameters.get_Ws(self.C[self.n, pdep:], self.O[self.n, pdep:])
                self.qm[self.n, pdep:, :, :] = parameters.get_qms(self.C[self.n, pdep:], Fis_plus_1, self.O[self.n, pdep:])
            else:
                if self.n != 0:
                    self.F[self.n, pdep:, :] = time_interpolate(self.times[self.n], t, delt, parameters.get_fluxes(Cn_2D, flag = 1), parameters.get_fluxes(Cn_plus_1_2D))
                self.q[self.n, pdep:, :]     = time_interpolate(self.times[self.n], t, delt, parameters.get_qs(Cn_2D, Fis), parameters.get_qs(Cn_plus_1_2D, Fis_plus_1))
                self.qm[self.n, pdep:, :, :] = parameters.get_qms(self.C[self.n, pdep:], Fis_plus_1)
                self.W[self.n, pdep:, :]     = parameters.get_Ws(self.C[self.n, pdep:])

            if parameters.topBCtype == 'Finite mixed water column':
                for n in range(parameters.nchemicals):
                    self.Cw[self.n, :] = time_interpolate(self.times[self.n], t, delt, parameters.get_Cws(Cn_2D, flag = 1), parameters.get_Cws(Cn_plus_1_2D))

            self.n = self.n + 1

def first_deriv_2pt_fwd(x):
    """Returns the finite difference coefficients for the first derivative for
    a two-point forward finite difference equation with uneven grid spacing.
    The variable "x" is an array with the values of the independent variable
    at points xi and xi+1."""

    return array([-1. / (x[1] - x[0]), 1. / (x[1] - x[0])])


def first_deriv_3pt_fwd(x):
    """Returns the finite difference coefficients for the first derivative for
    a three-point forward finite difference equation with uneven grid spacing.
    The variable "x" is an array with the values of the independent variable
    at points xi, xi+1, xi+2."""

    y = []
    y.append((2. * x[0] - x[1] - x[2]) / (x[1] - x[0]) / (x[2] - x[0]))
    y.append((x[2] - x[0]) / float(x[1] - x[0]) / (x[2] - x[1]))
    y.append((x[1] - x[0]) / float(x[2] - x[0]) / (x[1] - x[2]))
    return array(y)

def first_deriv_3pt_bwd(x):
    """Returns the finite difference coefficients for the first derivative for
    a three-point backward finite difference equation with uneven grid spacing.
    The variable "x" is an array with the values of the independent variable
    at points xi-2, xi-1, and xi."""

    y = []
    y.append((x[2] - x[1]) / float(x[2] - x[0]) / (x[1] - x[0]))
    y.append((x[0] - x[2]) / float(x[2] - x[1]) / (x[1] - x[0]))
    y.append((2 * x[2] - x[1] - x[0]) / float(x[2] - x[1]) / (x[2] - x[0]))
    return array(y)

def first_deriv_3pt_cen(x):
    """Returns the finite difference coefficients for the first derivative for
    a three-point forward finite difference equation with uneven grid spacing.
    The variable "x" is an array with the values of the independent variable
    at points xi-1, xi, and xi+1."""

    y = []
    y.append((x[1] - x[2]) / float(x[1] - x[0]) / (x[2] - x[0]))
    y.append((x[0] + x[2] - 2. * x[1]) / float(x[1] - x[0]) / (x[2] - x[1]))
    y.append((x[1] - x[0]) / float(x[2] - x[0]) / (x[2] - x[1]))
    return array(y)

def first_deriv_4pt_upw(x):
    """Returns the finite difference coefficients for the first derivative for
    a four-point finite difference equation with uneven grid spacing.  The
    algorithm uses a linear com+bination of the 3-point centered scheme and the
    3-point forward scheme (2/3 to 1/3 ratio, respectively).  The scheme
    provides good stability for hyperbolic problems with better accuracy than
    a simple forward difference."""

    y      = zeros(4)
    z      = zeros(4)
    y[0:3] = first_deriv_3pt_cen(x[0:3])
    z[1:4] = first_deriv_3pt_fwd(x[1:4])
    return 2. / 3 * y + 1. / 3 * z

def second_deriv_3pt_cen(x):
    """Returns the finite difference coefficients for the second derivative for
    a three-point finite difference equation with uneven grid spacing. The
    variable "x" is an array with the values of the independent variable at
    points xi-1, xi, and xi+1."""

    y = []
    y.append(2.  / (x[2] - x[0]) / (x[1] - x[0]))
    y.append(-2. / (x[1] - x[0]) / (x[2] - x[1]))
    y.append(2.  / (x[2] - x[0]) / (x[2] - x[1]))
    return array(y)

def get_delzmax(U, D, elam):
    """Calculates the maximum grid spacing for each layer to prevent
    oscillations in the discretized solution (mesh Peclet number = 2).
    The function uses the effective diffusion for a layer "D" and the
    Darcy velocity "U." """

    if U != 0:    delzmax = 2. * D / abs(U)
    else:         delzmax = 0

    if elam != 0: delzmax_e = 2 * (D / elam)**0.5
    else:         delzmax_e = 0

    if U != 0 and elam != 0: delzmax = min(delzmax,delzmax_e)
    else:                    delzmax = max(delzmax,delzmax_e)

    return delzmax

def get_max_time_step(delz, D, R):
    """Calculates the maximum time step size from the Courant-Friedrichs-Lewy
    condition (R * delz**2 / 2D).  "R" is the retardation factor, "delz" is
    the grid spacing, and "D" the effective diffusion coefficient."""

    return R * delz**2 / 2. / D

def top_mass_transfer_boundary(D, KDbiop, kbl, Cw, z):
    """Returns the finite difference equation for the top mass transfer 
    boundary condition using the benthic boundary layer mass transfer 
    coefficient "kbl," the diffusion coefficient in the top layer "D," the 
    overlying water concentration "Cw," and the top three grid points 
    (in array "z")."""
    
    kbl = kbl #convert the unit of k from cm/hr to cm/yr
    
    LHS = -D   * first_deriv_3pt_fwd(z) + array([kbl, 0 , 0]) - array(KDbiop) * first_deriv_3pt_fwd(z[0:3])
    RHS = kbl * Cw

    return LHS, RHS

def top_CSTR_boundary(D, U, kbl, tau, h, z):
    """Returns the finite difference equation for the top mass transfer
    boundary condition using the benthic boundary layer mass transfer
    coefficient "kbl," the diffusion coefficient in the top layer "D," the
    overlying water concentration "Cw," and the top three grid points
    (in array "z")."""

    kbl = kbl #convert the unit of k from cm/hr to cm/yr
    k_Cw  = (U+kbl)/h/(1/tau+kbl/h)

    LHS = -D   * first_deriv_3pt_fwd(z) + array([kbl*(1-k_Cw), 0 , 0])
    RHS = 0
    return LHS, RHS

def interface_boundary(D1, U1, KDbiop1, D2, U2, KDbiop2, z):
    """Returns the finite difference equation for the interface between two
    layers.  The diffusion coefficient in the first layer is "D1," the diffusion
    coefficient in the second layer is "D2", and "z" is an array containing the
    grid points two above the interface, at the interface, and two below the
    interface (total length five)."""

    equation      = zeros(5)
    equation[0:3] = -D1 * first_deriv_3pt_bwd(z[0:3]) - array([0, 0, U1]) - array(KDbiop1) * first_deriv_3pt_bwd(z[0:3])
    equation[2:5] = equation[2:5] + D2 * first_deriv_3pt_fwd(z[2:5]) + array([U2, 0, 0]) + array(KDbiop2) * first_deriv_3pt_fwd(z[2:5])

    return equation

def comp_interface_boundary(D1, U1, KDbiop1, D2, U2, KDbiop2, z):
    """Returns the finite difference equation for the interface between two
    layers.  The diffusion coefficient in the first layer is "D1," the diffusion
    coefficient in the second layer is "D2", and "z" is an array containing the
    grid points two above the interface, at the interface, and two below the
    interface (total length five)."""

    equation      = zeros(5)
    equation[0:3] = -D1 * first_deriv_3pt_bwd(z[0:3]) - array([0, 0, U1]) - array(KDbiop1) * first_deriv_3pt_bwd(z[0:3])
    equation[2:5] = equation[2:5] + D2 * first_deriv_3pt_fwd(z[2:5]) + array([U2, 0, 0]) + array(KDbiop2) * first_deriv_3pt_fwd(z[2:5])

    #equation      = zeros(5)
    #equation[1:3] = -D1 * first_deriv_2pt_fwd(z[1:3]) - array([0, U1]) - array(KDbiop1) * first_deriv_2pt_fwd(z[1:3])
    #equation[2:4] = equation[2:4] + D2 * first_deriv_2pt_fwd(z[2:4]) + array([U2, 0]) + array(KDbiop2) * first_deriv_2pt_fwd(z[2:4])

    return equation

def flux_bottom_boundary(U, D, Dbiops, C0, x):
    """Returns the finite difference equation for a flux-matching bottom
    boundary condition using the Darcy velocity "U," the diffusion coefficient
    in the bottom layer "D," the underlying sediment concentration "C0," and
    the bottom three grid points "x." """

    y    = D * first_deriv_3pt_bwd(x) + array(Dbiops) * first_deriv_3pt_bwd(x)
    y[2] = y[2] + U
    return array(y), U * C0

def get_4pt_adr_fde_imp(R, R_plus_1, U_plus_1, D_plus_1, K_plus_1, delt, z):
    """Returns the LHS of the finite difference equation at a point for the
    advection-diffusion-reaction equation with sorption using one point
    downwind and two points upwind.  "U" is the Darcy velocity, "D" is the
    diffusion coefficient, "e" is the porosity, "lam" is the first-order
    decay rate constant, "delt" is the time step size, and "z" is an array
    of the four points used in the discretization."""

    a      = zeros(4)
    a[0:3] = second_deriv_3pt_cen(z)
    b      = first_deriv_4pt_upw(z)
    c      = array([0, 1, 0, 0])

    return - array(D_plus_1 + [0]) * a - array(K_plus_1 + [0]) * a - U_plus_1 * b + (R_plus_1/delt)*c, (R/delt)*c

def get_3pt_adr_fde_imp(R, R_plus_1, U_plus_1, D_plus_1, K_plus_1, delt, z):
    """Returns the LHS of the finite difference equation at a point for the
    advection-diffusion-reaction equation with sorption using one point
    downwind and one point upwind.  "U" is the Darcy velocity, "D" is the
    diffusion coefficient, "e" is the porosity, "lam" is the first-order
    decay rate constant, "delt" is the time step size, and "z" is an array
    of the four points used in the discretization."""

    a      = second_deriv_3pt_cen(z)
    b      = zeros(3)
    b[1:3] = first_deriv_2pt_fwd(z)
    c      = array([0, 1, 0])

    return -array(D_plus_1) * a - array(K_plus_1) * a  - U_plus_1*b + (R_plus_1/delt)*c, (R/delt)*c


def get_4pt_adr_fde_CN(R, R_plus_1, U, U_plus_1, D, D_plus_1, K, K_plus_1, delt, z):
    """Returns the LHS of the finite difference equation at a point for the 
    advection-diffusion-reaction equation with sorption using one point 
    downwind and two points upwind.  "U" is the Darcy velocity, "D" is the 
    diffusion coefficient, "e" is the porosity, "lam" is the first-order 
    decay rate constant, "delt" is the time step size, and "z" is an array 
    of the four points used in the discretization."""

    a               = zeros(4)
    a[0:3]          = second_deriv_3pt_cen(z)
    b               = first_deriv_4pt_upw(z)
    c               = array([0, 1, 0, 0])

    return (-array(D_plus_1 + [0])*a - array(K_plus_1 + [0])*a - U_plus_1 * b + (2*R_plus_1/delt)*c)/2, (array(D + [0])*a + array(K + [0])*a + U*b + (2*R/delt)*c)/2

def get_3pt_adr_fde_CN(R, R_plus_1, U, U_plus_1, D, D_plus_1, K, K_plus_1, delt, z):
    """Returns the LHS of the finite difference equation at a point for the 
    advection-diffusion-reaction equation with sorption using one point 
    downwind and one point upwind.  "U" is the Darcy velocity, "D" is the 
    diffusion coefficient, "e" is the porosity, "lam" is the first-order 
    decay rate constant, "delt" is the time step size, and "z" is an array 
    of the four points used in the discretization."""

    a      = second_deriv_3pt_cen(z)
    b      = zeros(3)  
    b[1:3] = first_deriv_2pt_fwd(z)
    c      = array([0, 1, 0])

    return (-array(D_plus_1) * a - array(K_plus_1) * a- U_plus_1*b + (2*R_plus_1/delt)*c)/2, (array(D)*a + array(K)*a + U*b + (2*R/delt)*c)/2

def time_interpolate(tint, t, delt, Cn, Cn_plus_1):
    """Returns the interpolated concentrations at time "tint" using the
    concentrations "Cn" at time "t" and concentrations "Cn_plus_1" at time 
    "t + delt." """

    return (Cn + (tint - t) / delt * (Cn_plus_1 - Cn))

def get_surface_flux(U, kbl, C, Cw):
    """Returns the surface flux using the benthic boundary layer mass transfer 
    coefficient "kbl," the concentration at the cap-water interface "C," and
    the overlying water concentration "Cw." """


    return (kbl * (C - Cw) + U * C)

def get_top_flux(U, D, KD, C, z):

    return U * C[0] + D * sum(first_deriv_3pt_fwd(z) *  C) + sum(array(KD) * first_deriv_3pt_fwd(z) * C)

def get_top_flux_dep(U, D, C, z):

    #return U * C[0] + D * sum(first_deriv_3pt_fwd(z) *  C)
    y = []
    y.append(-1./(z[1]-z[0]))
    y.append(1./(z[1]-z[0]))

    return U * C[0] + D * sum(array(y) *  C)

def get_boundary_flux(U, D, KD, C, z):
    """Returns the flux at a boundary between two layers using the properties
    of the overlying layer.  Uses the three-point backwards difference, the
    overlying effective diffusion coefficient, the concentrations at the three
    points above in array "C," and the grid depths in array "z." """

    return U * C[2] + D * sum(first_deriv_3pt_bwd(z) * C) + sum(array(KD) * first_deriv_3pt_bwd(z) * C)

def get_point_flux(U, D, KD, C, z):
    """Returns the flux at a grid point that is not a boundary.  Uses the three-
    point centered difference, the diffusion coefficient at the point "D," the
    concentrations at the points before, at and after "C," and the grid points
    "z." """

    return U * C[1] + D * sum(first_deriv_3pt_cen(z) *  C) + sum(array(KD) * first_deriv_3pt_cen(z) * C)

def get_2_point_upwind_flux(U, D, C, z):
    """Returns the flux at a grid point that is not a boundary.  Uses the three-
    point centered difference, the diffusion coefficient at the point "D," the
    concentrations at the points before, at and after "C," and the grid points
    "z." """

    return U * C[0] + D * sum(first_deriv_2pt_fwd(z) *  C)

def get_2_point_downwind_flux(U, D, C, z):
    """Returns the flux at a grid point that is not a boundary.  Uses the three-
    point centered difference, the diffusion coefficient at the point "D," the
    concentrations at the points before, at and after "C," and the grid points
    "z." """

    return U * C[1] + D * sum(first_deriv_2pt_fwd(z) *  C)

def get_nonpoint_flux(U, D, C1, C2, z1, z2):
    """Returns the flux at a point that is not part of the grid.  Uses the two-
    point centered difference between points "z1" and "z2" and the 
    concentrations "C1" and "C2" at those points and the diffusion coefficient
    at the point "D." """
    
    return U * (C1 + C2) / 2 + D * (C2 - C1) / (z2 - z1)
