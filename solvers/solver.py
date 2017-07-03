#! /usr/bin/env python
#
#This file contains the GUI used to interface with the solvers.

import tkMessageBox as tkmb, time as timer

from Tkinter             import Frame, Label, Button, StringVar, IntVar
from solver_routines     import Parameters, Output
from capsim_object_types import CapSimWindow

class Solver:
    """Displays the progress of CapSim for the simulation."""

    def __init__(self, master, system):
        """Constructor method."""

        self.sizeflag   = 0
        self.master     = master
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.version    = system.version
        self.fonttype   = system.fonttype
        self.top        = None
        self.output     = None
        self.progress   = StringVar(value = '') #percent complete
        self.remaintime = StringVar(value = '') #percent complete
        self.abort      = IntVar()              #abort flag
        self.parameters = Parameters(system)    #input system

    def make_widgets(self):
        """Makes widgets for the progress window while CapSim evaluates the 
        system."""

        self.instructions1  = Label(self.frame, text = 'Please choose from the following options:')
        self.instructions2  = Label(self.frame, text = 'Please wait while CapSim simulates transport through the system...')
        self.blank1         = Label(self.frame, text = ' ' * 51)
        self.blank2         = Label(self.frame, text = ' ' * 51)
        self.blank3         = Label(self.frame, text = ' ')
        self.blank4         = Label(self.frame, text = ' ')
        self.blank5         = Label(self.frame, text = ' ')
        self.blank6         = Label(self.frame, text = ' ')
        self.progresswidget = Label(self.frame, textvariable = self.progress)
        self.timewidget     = Label(self.frame, textvariable = self.remaintime)

        self.postwidget     = Label(self.frame, text = 'Postprocessing...')

        self.startbutton    = Button(self.frame, text = 'Begin Simulation',command = self.solve_system, width = 20)
        self.abortbutton    = Button(self.frame, text = 'Abort Run', command = self.abortrun, width = 20)

        #show the widgets on the grid

        self.instructions1.grid(row = 0, columnspan = 2)
        self.blank1.grid(row = 1, column = 0)
        self.blank2.grid(row = 1, column = 1)
        self.blank3.grid(row = 2)
        self.blank4.grid(row = 3)
        self.startbutton.grid(row = 4, columnspan = 2, pady = 1)

        #bind the buttons to the appropriate commands

        self.startbutton.bind('<Return>', self.solve_system)
        self.abortbutton.bind('<Return>', self.abortrun)

        self.focusbutton = self.startbutton
    
    def solve_system(self, C_old = None, event = 0 ):
        """Makes the finite difference matrices to step forward in time, pre-
        allocates memory for the output information, clears the "run" screen, 
        directs the system to the appropriate solver, and grids the "run
        progress" information and "abort" button."""

        #clear the screen and start the progress bar

        self.instructions1.grid_forget()
        self.startbutton.grid_forget()
        
        self.instructions2.grid(row = 0,  columnspan = 2)
        self.progresswidget.grid(row = 2, columnspan = 2)
        self.blank3.grid(row = 3)
        self.timewidget.grid(     row = 4, columnspan = 2)
        self.blank4.grid(row = 5)
        self.abortbutton.grid(row = 6, columnspan = 2)
        self.blank5.grid(row = 7, columnspan = 2)
        self.blank6.grid(row = 8, columnspan = 2)

        self.master.canvas.update()
        self.master.buttonframe.grid_forget()

        sorp    = self.parameters.sorp
        cons    = self.parameters.con
        dep     = self.parameters.dep
        tidal   = self.parameters.tidal
        reac    = self.parameters.reac
        bio     = self.parameters.bio
        biomix  = self.parameters.biomix

        variable_list = ['Cn', 'Fi', 'F', 'q', 'qm', 'W','Cw']

        Temp       = {}
        for variable in variable_list:
            Temp[variable] = []

        #determine the grid, time step size, and set up the equations for the 
        #finite differencing
        self.parameters.make_uniform_grid()
        if bio == 1:
            self.parameters.update_bioturbation()
            self.parameters.make_grid_Dbiops()

        Fis, FisL, FisM = self.parameters.get_initial_component_fractions()
        Cn              = self.parameters.get_initial_concentrations()
        Fis_plus_1  = {}
        FisL_plus_1 = {}
        FisM_plus_1 = {}
        for component in self.parameters.components:
            Fis_plus_1[component.name]  = [Fi for Fi in Fis[component.name]]
            FisL_plus_1[component.name] = [Fi for Fi in FisL[component.name]]
            FisM_plus_1[component.name] = [Fi for Fi in FisM[component.name]]
        self.parameters.make_matrix_parameter_vectors(Cn, Fis, FisL)
        self.parameters.make_transport_parameter_vectors()
        self.parameters.make_reaction_parameter_vectors(Cn, Fis)
        self.parameters.update_time_dependents()
        self.parameters.make_matrices()

        #preallocate an instance of the "Output" class to store the desired
        #output data

        self.output = Output(self.parameters)
        if self.output.sizeflag == 1: self.show_size_error()

        #direct to the appropriate solver options

        t = 0
        n = 0

        #step through time and fill out the concentrations in the grid

        start = timer.time()

        #use the correct R for the first time step if nonlinear sorption
        if sorp == 1 or reac == 1: self.parameters.update_nonlinear(Cn, Fis, FisL)

        results = self.output.converter(self.parameters, Cn, FisL)
        for variable in variable_list:
            Temp[variable].append(results[variable_list.index(variable)])

        t_start      = 0
        t_end        = 0

        while t < (self.parameters.tfinal_ori + self.parameters.delt * (2 + self.parameters.steps)): #loop through time to the simulation end

            if dep  == 1:   Cn, Fis_plus_1, FisL_plus_1, FisM_plus_1 = self.parameters.update_deposition(Cn, Fis, FisL, FisM, t+self.parameters.delt)
            self.parameters.update_time_dependents()
            if cons == 1:
                self.parameters.update_consolidation(t+self.parameters.delt, self.parameters.Vdar)
                if tidal == 1: self.parameters.update_tidal(t+self.parameters.delt, self.parameters.U_plus_1)
            else:
                if tidal == 1: self.parameters.update_tidal(t+self.parameters.delt, self.parameters.Vdar)

            if biomix ==1:
                self.parameters.make_components_matrices()
                Fis_plus_1, FisL_plus_1, FisM_plus_1 = self.parameters.get_Fis_plus_1(Fis_plus_1, FisL_plus_1, FisM_plus_1)
                self.parameters.make_matrix_parameter_vectors(Cn, Fis_plus_1, FisL_plus_1)
                self.parameters.make_reaction_parameter_vectors(Cn, Fis_plus_1)

            if (cons + tidal + biomix) > 0:
                self.parameters.make_transport_parameter_vectors()

            if (cons + tidal + dep + biomix + sorp + reac) > 0:
                self.parameters.make_matrices()

            if sorp == 1 or reac == 1:
                Cn_plus_1 = self.parameters.non_linear_solver(Cn, Fis_plus_1, FisL_plus_1)
            else:
                Cn_plus_1 = self.parameters.get_Cn_plus_1(Cn)

            #collect the pertinent data from the time step
            if self.parameters.averageoption == 'Instaneous' and dep != 1:
                if self.output.n < len(self.output.times):
                    self.output.store_no_dep(Cn, Cn_plus_1, t, t+self.parameters.delt, self.parameters, FisL, FisL_plus_1)
            else:
                new_results = self.output.converter(self.parameters, Cn_plus_1, FisL_plus_1)
                for variable in variable_list:
                    Temp[variable].append(new_results[variable_list.index(variable)])

                if len(Temp['Cn']) >= self.parameters.steps:
                    results_plus_1 = []
                    for variable in variable_list:
                        results_plus_1.append(Temp[variable][0])
                        for temp in Temp[variable][1:]:
                            results_plus_1[-1] = results_plus_1[-1] + temp
                        results_plus_1[-1] = results_plus_1[-1]/len(Temp['Cn'])

                    t_middle = (t+self.parameters.delt - t_end)/2 + t_end
                    self.output.store(t_start, t_middle, self.parameters, results, results_plus_1)

                    Temp    = {}
                    for variable in variable_list:
                        Temp[variable] = []
                    results = results_plus_1
                    t_start = t_middle
                    t_end   = t+self.parameters.delt

            t  = t + self.parameters.delt
            Cn = [C for C in Cn_plus_1]
            if biomix ==1 or dep == 1:
                Fis  = {}
                FisL = {}
                FisM = {}
                for component in self.parameters.components:
                    Fis[component.name]  = [Fi for Fi in Fis_plus_1[component.name]]
                    FisL[component.name] = [Fi for Fi in FisL_plus_1[component.name]]
                    FisM[component.name] = [Fi for Fi in FisM_plus_1[component.name]]

            self.progress.set('Simulation Progress: ' + str(int(t)) + ' / ' + str(int(self.parameters.tfinal_ori)) + ' ' + self.parameters.timeunit )
            self.remaintime.set('Approximate Remaining Time: %d Seconds' %((timer.time()-start)*(self.parameters.tfinal-t)/t))
            self.frame.update()
            if self.abort.get() == 1: break

        self.Cn = Cn

        if self.abort.get() == 0: #checks if the abort button was invoked

            #postprocess and store the data in an "Output" object

            self.progresswidget.grid_forget()
            self.postwidget.grid(row = 2, column = 0, columnspan = 3)
            self.frame.update()

        self.frame.quit()

    def abortrun(self, event = 0): 
        """Used to abort run."""

        if tkmb.askyesno(self.version, 'Do you really want to abort?') == 1: 
            self.abort.set(1)
            self.output = None
            self.frame.quit()
    
    def show_size_error(self):
        """Shows ann error if the user specifies an overly complicated system
        that requires too much memory allocation."""

        tkmb.showerror(title = 'Memory Error', message = 'The parameters ' +
                       'you have specified require too much memory to be ' +
                       'computed.  Please decrease the simulation time ' +
                       'and/or the transport rates to rectify this issue.')
        self.frame.quit()

class BatchSolver:
    """Displays the progress of CapSim for the simulation."""

    def __init__(self, master, systems, type):
        """Constructor method."""

        self.sizeflag   = 0
        self.master     = master
        self.tframe     = Frame(master.tframe)
        self.frame      = Frame(master.frame)
        self.bframe     = Frame(master.bframe)
        self.version    = systems[0].version
        self.fonttype   = systems[0].fonttype
        self.top        = None
        self.output     = None
        self.progress   = StringVar(value = '') #percent complete
        self.remaintime = StringVar(value = '') #percent complete
        self.abort      = IntVar()              #abort flag
        self.type       = type
        self.parameters = []
        self.outputs    = []
        for system in systems:
            self.parameters.append(Parameters(system))     #input system

    def make_widgets(self):
        """Makes widgets for the progress window while CapSim evaluates the
        system."""

        self.instructions1  = Label(self.frame, text = 'Please choose from the following options:')
        self.instructions2  = Label(self.frame, text = 'Please wait while CapSim simulates transport through the system...')
        self.blank1         = Label(self.frame, text = ' ' * 51)
        self.blank2         = Label(self.frame, text = ' ' * 51)
        self.blank3         = Label(self.frame, text = '')
        self.blank4         = Label(self.frame, text = '')
        self.blank5         = Label(self.frame, text = '')
        self.blank6         = Label(self.frame, text = '')
        self.progresswidget = Label(self.frame, textvariable = self.progress)
        self.timewidget     = Label(self.frame, textvariable = self.remaintime)
        self.postwidget     = Label(self.frame, text = 'Postprocessing...')

        self.startbutton    = Button(self.frame, text = 'Begin Simulation',command = self.solve_system, width = 20)
        self.abortbutton    = Button(self.frame, text = 'Abort Run', command = self.abortrun, width = 20)

        #show the widgets on the grid

        self.instructions1.grid(row = 0, columnspan = 2)
        self.blank1.grid(row = 1, column = 0)
        self.blank2.grid(row = 1, column = 1)
        self.blank3.grid(row = 2)
        self.blank4.grid(row = 3)
        self.startbutton.grid(row = 4, columnspan = 2, pady = 1)

        #bind the buttons to the appropriate commands

        self.startbutton.bind('<Return>', self.solve_system)
        self.abortbutton.bind('<Return>', self.abortrun)

        self.focusbutton = self.startbutton

    def solve_system(self, event = 0 ):
        """Makes the finite difference matrices to step forward in time, pre-
        allocates memory for the output information, clears the "run" screen,
        directs the system to the appropriate solver, and grids the "run
        progress" information and "abort" button."""

        #clear the screen and start the progress bar

        self.instructions1.grid_forget()
        self.startbutton.grid_forget()

        self.instructions2.grid(row = 0,  columnspan = 2)
        self.progresswidget.grid(row = 2, columnspan = 2)
        self.blank3.grid(row = 3)
        self.timewidget.grid(     row = 4, columnspan = 2)
        self.blank4.grid(row = 5)
        self.abortbutton.grid(row = 6, columnspan = 2)
        self.blank5.grid(row = 7, columnspan = 2)
        self.blank6.grid(row = 8, columnspan = 2)

        self.master.canvas.update()
        self.master.buttonframe.grid_forget()

        self.output = []

        start = timer.time()        #real time at t = 0

        for parameters in self.parameters:

            if self.abort.get() <> 1:

                if self.type == 'Separate': start = timer.time()

                sorp   = parameters.sorp
                cons   = parameters.con
                dep    = parameters.dep
                tidal  = parameters.tidal
                reac   = parameters.reac
                bio    = parameters.bio
                biomix = parameters.biomix

                variable_list = ['Cn', 'Fi', 'F', 'q', 'qm', 'W','Cw']

                Temp       = {}
                for variable in variable_list:
                    Temp[variable] = []

                #determine the grid, time step size, and set up the equations for the
                #finite differencing

                parameters.make_uniform_grid()
                if bio == 1:
                    parameters.update_bioturbation()
                    parameters.make_grid_Dbiops()

                Fis, FisL, FisM = parameters.get_initial_component_fractions()
                Cn              = parameters.get_initial_concentrations()
                Fis_plus_1  = {}
                FisL_plus_1 = {}
                FisM_plus_1 = {}
                for component in parameters.components:
                    Fis_plus_1[component.name]  = [Fi for Fi in Fis[component.name]]
                    FisL_plus_1[component.name] = [Fi for Fi in FisL[component.name]]
                    FisM_plus_1[component.name] = [Fi for Fi in FisM[component.name]]
                parameters.make_matrix_parameter_vectors(Cn, Fis, FisL)
                parameters.make_transport_parameter_vectors()
                parameters.make_reaction_parameter_vectors(Cn, Fis)
                parameters.update_time_dependents()
                parameters.make_matrices()

                output = Output(parameters)
                if output.sizeflag == 1: self.show_size_error()

                t = parameters.tstart
                n = 0

                if sorp == 1 or reac == 1: parameters.update_nonlinear(Cn, Fis, FisL)

                results = output.converter(parameters, Cn, FisL)
                for variable in variable_list:
                    Temp[variable].append(results[variable_list.index(variable)])

                t_start      = 0
                t_end        = 0

                while t < (parameters.tfinal_ori + parameters.delt * (2 + parameters.steps)): #loop through time to the simulation end

                    if dep  == 1: Cn, Fis_plus_1, FisL_plus_1, FisM_plus_1 = parameters.update_deposition(Cn, Fis, FisL, FisM, t+parameters.delt)
                    parameters.update_time_dependents()
                    if cons == 1: parameters.update_consolidation(t+parameters.delt, parameters.Vdar)
                    if tidal== 1: parameters.update_tidal(t+parameters.delt, parameters.U_plus_1)

                    if biomix ==1:
                        parameters.make_components_matrices()
                        Fis_plus_1, FisL_plus_1, FisM_plus_1 = parameters.get_Fis_plus_1(Fis_plus_1, FisL_plus_1, FisM_plus_1)
                        parameters.make_matrix_parameter_vectors(Cn, Fis_plus_1, FisL_plus_1)
                        parameters.make_reaction_parameter_vectors(Cn, Fis_plus_1)

                    if (cons + tidal + biomix) > 0:
                        parameters.make_transport_parameter_vectors()

                    if (cons + tidal + dep + biomix + reac + sorp) > 0:
                        parameters.make_matrices()

                    if sorp == 1 or reac == 1:
                        Cn_plus_1 = parameters.non_linear_solver(Cn, Fis_plus_1, FisL_plus_1)
                    else:
                        Cn_plus_1 = parameters.get_Cn_plus_1(Cn)

                    #collect the pertinent data from the time step
                    if parameters.averageoption == 'Instaneous':
                        if output.n < len(output.times) and round(output.times[output.n], 8) < round(t+parameters.delt, 8):
                            output.store_no_dep(Cn, Cn_plus_1, t, t+parameters.delt, parameters, FisL, FisL_plus_1)
                    else:
                        new_results = output.converter(parameters, Cn_plus_1, FisL_plus_1)
                        for variable in variable_list:
                            Temp[variable].append(new_results[variable_list.index(variable)])

                        if len(Temp['Cn']) >= parameters.steps:
                            results_plus_1 = []
                            for variable in variable_list:
                                results_plus_1.append(Temp[variable][0])
                                for temp in Temp[variable][1:]:
                                    results_plus_1[-1] = results_plus_1[-1] + temp
                                results_plus_1[-1] = results_plus_1[-1]/len(Temp['Cn'])

                            t_middle = (t+parameters.delt - t_end)/2 + t_end

                            output.store(t_start, t_middle, parameters, results, results_plus_1)

                            Temp    = {}
                            for variable in variable_list:
                                Temp[variable] = []
                            results = results_plus_1
                            t_start = t_middle
                            t_end   = t+parameters.delt

                    t  = t + parameters.delt
                    Cn = [C for C in Cn_plus_1]
                    if biomix ==1:
                        Fis  = {}
                        FisL = {}
                        FisM = {}
                        for component in parameters.components:
                            Fis[component.name]  = [Fi for Fi in Fis_plus_1[component.name]]
                            FisL[component.name] = [Fi for Fi in FisL_plus_1[component.name]]
                            FisM[component.name] = [Fi for Fi in FisM_plus_1[component.name]]

                    if self.type == 'Continuous':
                        self.progress.set('Simulation Progress: ' + str(int(t)) + ' / ' + str(int(self.parameters[-1].tfinal_ori)) + ' ' + self.parameters[-1].timeunit )
                        self.remaintime.set('Approximate Remaining Time: %d Seconds' %((timer.time()-start)*(self.parameters[-1].tfinal-t)/(t-self.parameters[0].tstart)))
                    else:
                        self.progress.set('Simulation Progress: ' + str(self.parameters.index(parameters)) + ' / ' + str(len(self.parameters)) )
                        self.remaintime.set('Approximate Remaining Time: %d Seconds' %((timer.time()-start)*(parameters.tfinal-t)/(t)))

                    self.frame.update()
                    if self.abort.get() == 1: break

                if self.abort.get() <> 1: self.outputs.append(output)

        if self.abort.get() == 0: #checks if the abort button was invoked

            self.progresswidget.grid_forget()
            self.postwidget.grid(row = 2, column = 0, columnspan = 3)
            self.frame.update()

        self.frame.quit()

    def abortrun(self, event = 0):
        """Used to abort run."""

        if tkmb.askyesno(self.version, 'Do you really want to abort?') == 1:
            self.abort.set(1)
            self.output = None
            self.outputs = None
            self.frame.quit()

    def show_size_error(self):
        """Shows ann error if the user specifies an overly complicated system
        that requires too much memory allocation."""

        tkmb.showerror(title = 'Memory Error', message = 'The parameters ' +
                       'you have specified require too much memory to be ' +
                       'computed.  Please decrease the simulation time ' +
                       'and/or the transport rates to rectify this issue.')
        self.frame.quit()


def solve_system(system):
    """Makes the GUI that shows the status of the simulation and runs the
    simulation."""

    root = CapSimWindow(buttons = 2)
    root.make_window(Solver(root, system))
    root.mainloop()

    output = root.window.output
    main   = root.main.get()

    root.destroy()

    return output, main

def solve_batch(systems, type):

    root = CapSimWindow(buttons = 2)
    root.make_window(BatchSolver(root, systems, type))
    root.window.solve_system()

    outputs = root.window.outputs
    main   = root.main.get()

    root.destroy()

    return outputs, main
