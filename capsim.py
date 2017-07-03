#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
#CapSim is software to be used for modeling contaminant transport in a
#cap of contaminated sediment.
#
#This file is used to pull together all of the input/output GUIs and the
#mathematical solvers used in the simulation.
#
########################################################################
#                                                                      #
#          ######    ##    ######  ######  #######  #       #          #
#          #        #  #   #    #  #          #     ##     ##          #
#          #       #    #  #    #  #          #     # #   # #          #
#          #       ######  ######  ######     #     #  # #  #          #
#          #       #    #  #            #     #     #   #   #          #
#          #       #    #  #            #     #     #       #          #
#          ######  #    #  #       ######  #######  #       #          #
#                                                                      #
#Version 3.5                                                           #
#                                                                      #
#Developed by Xiaolong Shen, David Lampert and Danny Reible            #
#Department of Civil, Architectural and Environmental Engineering      #
#The University of Texas at Austin                                     #
#                                                                      #
#Last Updated: 6/20/2017 by XS                                         #
#                                                                      #
########################################################################

import cPickle as pickle, sys, os, warnings
import _winreg as wreg
import tkFileDialog as tkfd

from Tkinter import Tk

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
    warnings.filterwarnings('ignore')
else: path = sys.path[0]

#Load the information of registry,
CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)

# Check the existence of the key 'CapSim' in Registry
try:
    CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
    Filepath = wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
    CapSimKey.Close()
except:
    rootinit = Tk()
    w = rootinit.winfo_screenwidth()
    h = rootinit.winfo_screenheight()
    rootsize = tuple(int(_) for _ in rootinit.geometry().split('+')[0].split('x'))
    x = w/2 - rootsize[0]/2
    y = h/2 - rootsize[1]/2
    rootinit.geometry("%dx%d+%d+%d" % (rootsize + (x, y)))

    # Create a window for users to input file directory and then create a key in Registry containing the directory information
    UserPath = os.environ['USERPROFILE']
    Filepath = tkfd.askdirectory(initialdir=UserPath+r'\Documents', parent = rootinit, title='To initialize CapSim, please select the directory for input and output files')
    if Filepath is not '':
        CapSimKey = wreg.CreateKey(CapSimReg, r'Software\CapSim')                                                                            
        wreg.SetValueEx(CapSimKey,r'FilePath',0,wreg.REG_SZ,Filepath)                                               

    # Create the folders under the input, output and database directory
        try:    os.chdir(Filepath)
        except: os.mkdir(Filepath)
        
        try:    os.chdir(Filepath+r'/database')
        except: os.mkdir(Filepath+r'/database')
        
        try:    os.chdir(Filepath+r'/input_cpsm_files')
        except: os.mkdir(Filepath+r'/input_cpsm_files')
        
        try:    os.chdir(Filepath+r'/output')
        except: os.mkdir(Filepath+r'/output')
        
        try:    os.chdir(Filepath+r'/batch_files')
        except: os.mkdir(Filepath+r'/batch_files')
            
    rootinit.destroy()

sys.path.append(path)
sys.path.append(path + r'/input_windows')
sys.path.append(path + r'/database')
sys.path.append(path + r'/solvers')
sys.path.append(path + r'/postprocess')

# Load the functions for GUI and solver
from capsim_object_types  import System
from mainmenu             import show_mainmenu
from updatedfile          import get_updatedfile, get_updateddatabase
from help                 import show_help

from systemunits          import get_systemunits
from chemicalproperties   import get_chemicalproperties
from matrixproperties     import get_matrixproperties
from systemproperties     import get_systemproperties
from layerproperties      import get_layerproperties
from sorptionproperties   import get_sorptionproperties
from reactionproperties   import get_reactionproperties
from reactioncoefficients import get_reactioncoefficients
from layerconditions      import get_layerconditions
from solidlayerconditions import get_solidlayerconditions
from solveroptions        import get_solveroptions
from inputoptions         import get_inputoptions
from summary              import get_summary

from batch                import make_batch
from database             import edit_database, make_database
from soliddatabase        import edit_soliddatabase, make_soliddatabase
from solver               import solve_system, solve_batch
from postprocess          import postprocess_data, postprocess_batch
from graphprocess         import graphprocess_data

# The current version  and the previous versions
version          = '3.5'
previous_version = ['CapSim 3.0', 'CapSim 3.1', 'CapSim 3.2', 'CapSim 3.2a', 'CapSim 3.2b', 'CapSim 3.3', '3.3', '3.4', '3.5', '3.6']
fonttype    = 'Arial 10'
formulatype = 'Calibri 11'

while(1):
    # Start the CapSim loop and create the 'system' instance
    system   = System(version, fonttype, formulatype)

    # Load the chemical and solid material database, create a new database file if no database file is available, update the database file if it is from the older version
    try:
        data = open(Filepath + r'/database/capsim3_chemicaldatabase', 'r')
        database = pickle.load(data)
        data.close()
    except:
        try:
            data = open(Filepath + r'/database/capsim_chemicaldatabase', 'r')
            database = pickle.load(data)
            data.close()
            database = get_updateddatabase(database)
            pickle.dump(database, open(Filepath + r'/database/capsim3_chemicaldatabase', 'w'))
        except:
            data = make_database(Filepath)
            database = pickle.load(data)
            data.close()

    try:    materialdata = open(Filepath + r'/database/capsim_soliddatabase', 'r')
    except: materialdata = make_soliddatabase(Filepath)

    materials = pickle.load(materialdata)
    materialdata.close()
    option, filename = show_mainmenu(system)

    # Create a new input file using the input window classes
    if option == 0:
        step = 1
        while system is not None:
            if step == 1 : system, step = get_systemunits(system, step)
            if step == 2 : system, step = get_chemicalproperties(system, database, step)
            if step == 3 : system, step = get_matrixproperties(system, materials, step)
            if step == 4 : system, step = get_sorptionproperties(system, step)
            if step == 5 : system, step = get_layerproperties(system, step)
            if step == 6 : system, step = get_reactionproperties(system, step)
            if step == 7 : system, step = get_reactioncoefficients(system, step)
            if step == 8 : system, step = get_systemproperties(system, step)
            if step == 9 : system, step = get_layerconditions(system, step)
            if step == 10: system, step = get_solidlayerconditions(system, step)
            if step == 11: system, step = get_solveroptions(system, step)
            if step == 12: system, step = get_inputoptions(system, step)
            if step == 13:
                while(1):
                    #show the summary window
                    system = get_summary(system, database, materials)
                    #run the simulation
                    if system is not None:
                        output, main = solve_system(system)
                        #postprocess
                        if output is not None:
                            main = postprocess_data(system, output)
                        if main == 1: break
                    else: break

    #Loads an existing cpsm file
    if option == 1: 
        cpsmfile = open(filename, 'r')
        system   = pickle.load(cpsmfile)
        cpsmfile.close()

        #Update the loaded input file if it is from a previous version
        if system.version != version and previous_version.count(system.version) == 0:
            system = get_updatedfile(system, version, fonttype)
        system.version = version
        # updates from version 3.3
        try: a = system.outputsteps
        except:  system.outputsteps = 100
        try:    a = system.timeoption
        except: system.timeoption = 'Crank-Nicolson'

        # updates from version 3.4
        try: a = system.matrices[0].components[0].mfraction
        except:
            for matrix in system.matrices:
                for component in matrix.components:
                    component.mfraction = round(component.rho*component.fraction/matrix.rho, 6)
                    print(component.mfraction)

        # updates from version 3.5
        try: a = system.BCs[system.chemicals[0].name].tau
        except:
            system.taucoefs           = {}
            system.taucoefs['Q']      = 1.
            system.taucoefs['V']      = 100.
            system.taucoefs['h']      = 1.
            system.taucoefs['DOC']    = 0.
            system.taucoefs['Qevap']  = 0.
            system.taucoefs['Decay']  = 'None'
            system.taucoefs['Evap']   = 'None'
            for chemical in system.chemicals:
                system.BCs[chemical.name].tau       = 0
                system.BCs[chemical.name].kdecay    = 0
                system.BCs[chemical.name].kevap     = 0

        if system.adv       == 'Tidal oscillation': system.adv = 'Period oscillation'
        if system.topBCtype == 'CSTR water body':   system.topBCtype = 'Finite mixed water column'
        if system.bio       == 'Bioturbation':      system.bio = 'Uniform'

        try: a = system.biomix
        except:
            system.biomix           = 0
            system.depsteps         = 0
            system.averageoption    = 'Instaneous'

        try: a = system.depgrid
        except:
            system.depoption    = 'Time step size'
            system.depgrid      = system.Vdep * system.delt

        try:    a = system.sigma
        except:
            system.sigma    = 10

        while(1):

            #show the summary window
            system = get_summary(system, database, materials)

            #run the simulation

            if system is not None:

                output, main = solve_system(system)

                #postprocess

                if output is not None:

                    main = postprocess_data(system, output)

                if main == 1: break

            else: break

    if option == 2: 
        #run a batch  file

        systems, type, main = make_batch(system)

        if main != 1:

            outputs, main = solve_batch(systems, type)

            if outputs is not None:

                main = postprocess_batch(type, systems, outputs)

            if main == 1: break

    if option == 3:
        #Load an existing output file

        while(1):

            step = 1

            if system is not None:
                system, step = get_systemunits(system, step)


                if step == 2:

                    main = graphprocess_data(system)

                else:
                    main = 1

                if main == 1: break

            else: break

    if option == 4:
        #Edit the chemical database
        
        while(1):
            data = open(Filepath + r'/database/capsim3_chemicaldatabase', 'r')
            database = pickle.load(data)
            data.close()

            database, main = edit_database(database, system)

            pickle.dump(database, open(Filepath + r'/database/capsim3_chemicaldatabase', 'w'))
            if main == 1: break
            
    if option == 5:
        #Edit the solid material database
        
        while(1):
            data = open(Filepath + r'/database/capsim_soliddatabase', 'r')
            database = pickle.load(data)
            data.close()

            database, main = edit_soliddatabase(database, system)

            pickle.dump(database, open(Filepath + r'/database/capsim_soliddatabase', 'w'))
            if main == 1: break

    #if option == 6:
        #show the help

    #    main = 0
    #    while main == 0: main = show_help(system)

sys.exit()
