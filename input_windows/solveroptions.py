#!/usr/bin/env python
#
#This script is used to make the window for the output options from CapSim.

from Tkinter             import Frame, Label, Entry, Checkbutton, OptionMenu, StringVar, IntVar, DoubleVar
from solvereditor        import SolverEditor
from capsim_object_types import CapSimWindow
from capsim_functions    import round_to_n
from numpy               import ceil, log2
import os, tkMessageBox as tkmb

class SolverOptions:
    """Makes a window for the user to specify output options."""

    def __init__(self, master, system, editflag = 0):
        """Constructor method."""

        self.master         = master
        self.tframe         = Frame(master.tframe)
        self.frame          = Frame(master.frame)
        self.bframe         = Frame(master.bframe)
        self.fonttype       = system.fonttype
        self.version        = system.version
        self.top            = None

        self.system         = system
        self.adv            = system.adv
        self.dep            = system.dep
        self.Vdep           = system.Vdep
        self.timeunit       = system.timeunit
        self.lengthunit     = system.lengthunit

        self.non_linear_check = 0
        
        for component in system.component_list:
            for chemical in system.chemicals:
                self.non_linear_check = self.non_linear_check + (system.sorptions[component][chemical.name].isotherm == 'Freundlich')
                self.non_linear_check = self.non_linear_check + (system.sorptions[component][chemical.name].isotherm == 'Langmuir')

        if system.reactions is not None:
            for reaction in system.reactions:
                if sum([reactant.index for reactant in reaction.reactants]) > 1 or reaction.model == 'Michaelis-Menten':
                    self.non_linear_check = self.non_linear_check + 1
            
        
        self.pvariables     = ['Use defaults', 'Specify manually']
        self.nonlinears     = ['Newton method', 'Fixed Point Iteration']

        self.ptypes         = ['Uniform size',  'Uniform Number', 'User-defined']
        self.tvariables     = ['slowest layer', 'geometric mean', 'User-defined']
        self.depoptions     = ['Time step size','Layer Grid size','User defined']

        self.timeoptions    = ['Crank-Nicolson', 'Implicit']
        self.averageoptions = ['Instaneous', 'Average']                                                     #simulation duration

        self.duration       = DoubleVar(value = 100)                                                        #simulation duration
        self.outputsteps    = IntVar(value = 100)                                                           #simulation duration
        self.averageoption  = StringVar(value = 'Instaneous')                                               #simulation duration
        self.discrete       = StringVar(value = self.pvariables[0])                                         #discretization flag
        self.ptotal         = IntVar(value = 0)                                                             #minimum grid points
        self.delt           = DoubleVar(value =  0)                                                         #minimumu time steps
        self.timeoption     = StringVar(value = self.timeoptions[0])
        self.ptype          = self.ptypes[2]
        self.tvariable      = self.tvariables[2]
        self.depoption      = self.depoptions[2]
        self.delz           = []
        self.players        = []

        self.tidalsteps     = IntVar(value = 0)                                                             #time steps within a tidal circle
        self.depgrid        = IntVar(value = 1)                                                             #time steps within a depsition layer
        self.nonlinear      = StringVar(value = self.nonlinears[0])                                         #iteration flag
        self.nlerror        = DoubleVar(value = 1)                                                          #iteration error tolerance

        for layer in system.layers:
            self.players.append(10)
            self.delz.append(layer.h/10)
            self.ptotal.set(sum(self.players))

        try:
            self.duration.set(system.tfinal)
            self.outputsteps.set(system.outputsteps)
            self.averageoption.set(system.averageoption)
            self.discrete.set(system.discrete)
            self.ptotal.set(system.ptotal)
            self.delt.set(system.delt)
            self.timeoption.set(system.timeoption)
            self.ptype      = system.ptype
            self.tvariable  = system.tvariable
            self.delz       = system.delz
            self.players    = system.players
            self.depoption  = system.depoption
            self.tidalsteps.set(system.tidalsteps)
            self.depgrid.set(system.depgrid)                                                              #time steps within a deposition grid
            self.nonlinear.set(system.nonlinear)
            self.nlerror.set(system.nlerror * 100)

        except: pass

        self.editflag = editflag

        if editflag == 1:
            self.delz        = []
            for layer in system.layers:
                self.delz.append(layer.h/self.players[system.layers.index(layer)])

    def make_widgets(self):
        """Make the widgets."""

        self.instructions     = Label(self.frame, text = 'Please specify the simulation options for the system:  ')
        self.blank1           = Label(self.frame, text = ' ' * 57)
        self.blank2           = Label(self.frame, text = ' ' * 10)
        self.blank3           = Label(self.frame, text = ' ' * 16)
        self.blank4           = Label(self.frame, text = ' ' * 5)

        self.durationlabel    = Label(self.frame, text ='Simulation duration ('+self.timeunit + '):')
        self.durationentry    = Entry(self.frame, textvariable = self.duration, width = 15, justify = 'center')

        self.outputlabel      = Label(self.frame, text ='Steps in output files:')
        self.outputentry      = Entry(self.frame, textvariable = self.outputsteps, width = 15, justify = 'center')

        self.timeoptionlabel  = Label(self.frame, text = 'Time step options:')
        self.timeoptionmenu   = OptionMenu(self.frame, self.timeoption, *self.timeoptions)
        self.timeoptionmenu.config(width = 16)
        self.timeoptionwidget = Label(self.frame, textvariable = self.timeoption, width = 15, justify = 'center')

        self.averageoptionlabel = Label(self.frame, text = 'Oscillation output options:')
        self.averageoptionmenu  = OptionMenu(self.frame, self.averageoption, *self.averageoptions)
        self.averageoptionmenu.config(width = 16)

        self.discretelabel    = Label(self.frame, text = 'Discretization options:')
        self.discretemenu     = OptionMenu(self.frame, self.discrete, *self.pvariables, command = self.discretization)
        self.discretemenu.config(width = 16)

        self.ptotallabel      = Label(self.frame, text = 'Number of grid points:')
        self.ptotalvalue      = Label(self.frame, textvariable = self.ptotal)
        self.ptotalentry      = Entry(self.frame, width = 15, justify= 'center', textvariable = self.ptotal)

        self.deltlabel        = Label(self.frame, text = 'Time step ('+ self.timeunit + '):')
        self.deltvalue        = Label(self.frame, textvariable = self.delt)
        self.deltentry        = Entry(self.frame, width = 15, justify= 'center', textvariable = self.delt)

        self.deplabel         = Label(self.frame, text = 'Steps in deposition grid')
        self.depvalue         = Label(self.frame, textvariable = self.depgrid)

        self.tidallabel       = Label(self.frame, text = 'Time steps per oscillation circle:')
        self.tidalvalue       = Label(self.frame, textvariable = self.tidalsteps)

        self.nlerrorlabel     = Label(self.frame, text = 'Error tolerance(%):')
        self.nlerrorentry     = Entry(self.frame, width = 15, justify= 'center', textvariable = self.nlerror)

        self.blank5           = Label(self.frame, text = '')
        self.blank6           = Label(self.frame, text = '')
        self.blank7           = Label(self.frame, text = '')

        self.focusbutton = None

        #show the widgets that don't change on the grid

        self.instructions.grid(row = 0, padx = 8, columnspan = 4, sticky = 'W')

        self.blank1.grid(row        =  1, column = 0)
        self.blank2.grid(row        =  1, column = 1)
        self.blank3.grid(row        =  1, column = 2)

        row = 3

        self.durationlabel.grid(row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.durationentry.grid(row =  row, column = 1,               padx = 1, pady = 2)
        row = row + 1

        self.outputlabel.grid(  row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.outputentry.grid(  row =  row, column = 1,               padx = 1, pady = 2)
        row = row + 1

        self.timeoptionlabel.grid(row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.timeoptionmenu.grid( row =  row, column = 1, sticky = 'WE')
        row = row + 1

        if self.adv == 'Period oscillation':

            self.averageoptionlabel.grid(row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
            self.averageoptionmenu.grid( row =  row, column = 1, sticky = 'WE')
            row = row + 1

        self.discretelabel.grid(row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.discretemenu.grid( row =  row, column = 1, sticky = 'WE')
        row = row + 1

        self.ptotallabel.grid(  row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.ptotalvalue.grid(  row =  row, column = 1, pady = 2)
        row = row + 1

        self.deltlabel.grid(    row =  row, column = 0, sticky = 'E', padx = 2, pady = 4)
        self.deltvalue.grid(    row  =  row, column = 1, pady = 2)
        row = row + 1

        if self.dep == 'Deposition':
            self.deplabel.grid(row  = row, column = 0, sticky = 'E', padx = 2, pady = 4)
            self.depvalue.grid(row  = row, column = 1, sticky = 'WE', padx = 2, pady = 4)
            row = row + 1

        if self.adv == 'Period oscillation':
            self.tidallabel.grid(row  = row, column = 0, sticky = 'E', padx = 2, pady = 4)
            self.tidalvalue.grid(row  = row, column = 1, sticky = 'WE', padx = 2, pady = 4)
            row = row + 1

        if self.non_linear_check > 0:
            
            self.nlerrorlabel.grid(  row =  row, column = 0, sticky = 'E',  padx = 2, pady = 4)
            self.nlerrorentry.grid(  row =  row, column = 1, padx = 1, pady = 2)
            row = row + 1

        self.blank5.grid(row        =  row + 1)
        self.blank6.grid(row        =  row + 2)

        self.discretization()
        self.master.geometry()
        self.master.center()

    def discretization(self, event = None):
        """Allows user to change discretization options."""

        if self.discrete.get() == self.pvariables[1]:

            if event != None:
                if self.top is None:
                    self.top = CapSimWindow(master = self.master, buttons = 2)
                    self.top.make_window(SolverEditor(self.top, self.system, self.ptype, self.ptotal.get(), self.tvariable, self.delt.get(), self.delz, self.players, self.depoption, self.depgrid.get()))
                    self.top.tk.mainloop()

                    if self.top.window.cancelflag == 0:
                        self.ptotal.set(self.top.window.ptotal.get())
                        self.ptype      = self.top.window.ptype.get()
                        self.tvariable  = self.top.window.tvariable.get()
                        self.delz       = self.top.window.delz
                        self.players    = self.top.window.players
                        self.depoption  = self.top.window.depoption.get()

                        if self.adv == 'Period oscillation':
                            self.tidalsteps.set(int(ceil(round(self.system.ptidal/self.top.window.delt.get(),4))))
                            if self.tidalsteps.get() < 4: self.tidalsteps.set(4)
                            else: self.tidalsteps.set(int(2*(ceil(self.tidalsteps.get()/2))))
                            self.delt.set(self.system.ptidal/self.tidalsteps.get())
                        else:
                            self.delt.set(self.top.window.delt.get())

                        if self.dep == 'Deposition':
                            self.depgrid.set(int(ceil(round(self.delz[0]/self.delt.get()/self.system.Vdep, 4))))
                            self.delz[0] = (self.delt.get()*self.depgrid.get()*self.system.Vdep)
                            self.players[0] = int(ceil(self.system.layers[0].h/self.delz[0]))

                    if self.top is not None:
                        self.top.destroy()
                        self.top = None

                elif self.top is not None:
                    tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
                    self.top.tk.focus()

            else:
                if self.adv == 'Period oscillation':
                    self.tidalsteps.set(int(ceil(self.system.ptidal/self.delt.get())))
                    if self.tidalsteps.get() < 4: self.tidalsteps.set(4)
                    else: self.tidalsteps.set(int(2*(ceil(self.tidalsteps.get()/2))))
                    self.delt.set(self.system.ptidal/self.tidalsteps.get())
                else:
                    self.delt.set(self.delt.get())

        else:
            self.players= []
            self.delz   = []
            for layer in self.system.layers:
                self.players.append(10)
                self.delz.append(layer.h/10)
            self.ptype      = self.ptypes[2]
            self.tvariable  = self.tvariables[2]
            self.ptotal.set(sum(self.players))
            self.depgrid.set(1)

            self.solvereditor = SolverEditor(self.master, self.system, self.ptype, self.ptotal.get(), self.tvariable, self.duration.get()/100, self.delz, self.players, self.depoption, self.depgrid.get())
            self.solvereditor.updatesolverparameters()

            self.delz        = self.solvereditor.delz
            self.players     = self.solvereditor.players

            self.duration.set(self.system.tfinal)                                       #simulation duration
            self.outputsteps.set(self.system.outputsteps)                               #simulation duration
            self.discrete.set(self.pvariables[0])                                       #discretization flag
            self.ptotal.set(self.solvereditor.ptotal.get())                             #minimum grid points
            if self.adv == 'Period oscillation':
                self.tidalsteps.set(int(ceil(round(self.system.ptidal/self.solvereditor.delt.get(),8))))
                if self.tidalsteps.get() < 4: self.tidalsteps.set(4)
                else: self.tidalsteps.set(int(2*(ceil(self.tidalsteps.get()/2))))
                self.delt.set(self.system.ptidal/self.tidalsteps.get())
            else:
                self.delt.set(self.solvereditor.delt.get())
                if self.delt.get() > self.duration.get()/100:
                    self.delt.set(self.duration.get()/100)

            if self.dep == 'Deposition':
                self.depoption = self.depoptions[2]
                self.depgrid.set(int(ceil(round(self.delz[0]/self.delt.get()/self.system.Vdep, 4))))
                self.delz[0] = (self.delt.get()*self.depgrid.get()*self.system.Vdep)
                self.players[0] = int(ceil(round(self.system.layers[0].h/self.delz[0],4)))


        self.master.geometry()
        self.master.center()

def get_solveroptions(system, step):
    """Get the output options."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(SolverOptions(root, system))
    root.mainloop()

    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_solveroptions(root.window)

    root.destroy()

    return system, step + root.step.get()
