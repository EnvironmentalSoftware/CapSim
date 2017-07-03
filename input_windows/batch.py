#! /usr/bin/env python
#
#This file is used to read data from a batch script to build a "System" object
#for CapSim to execute.

import tkFileDialog as tkfd, tkMessageBox as tkmb, cPickle as pickle, sys, os, csv
import _winreg as wreg

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)
CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
Filepath =wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
CapSimKey.Close()

sys.path.append(path + r'/solvers')

from Tkinter             import Frame, Label, Button
from capsim_object_types import CapSimWindow, System, Chemical, Matrix, MatrixComponent, Sorption, Reaction, Layer, Coefficient, BC, IC, SolidIC
from reactioneditor      import Reactant, Product
from capsim_functions    import formula_converter

class BatchFile:
    """A class that creates a window to execute batch CapSim files."""

    def __init__(self, master, system):

        self.master   = master
        self.system   = system
        self.fonttype = system.fonttype
        self.version  = system.version
        self.tframe   = Frame(master.tframe)
        self.frame    = Frame(master.frame)
        self.bframe   = Frame(master.bframe)
        self.top      = None

    def make_widgets(self):

        self.label      = Label(self.frame, text = 'Please select the batch ' +
                                'file for CapSim to use to build the system:')
        self.loadbutton = Button(self.frame, text = 'Load File', width = 20,
                                 command = self.get_filename)
        self.runbutton  = Button(self.frame, text = 'Run Batch', width = 20,
                                 command = self.run)
        self.blank      = Label(self.frame, text = '')

        self.label.grid(row = 0, padx = 10)
        self.blank.grid(row = 1)
        self.loadbutton.grid(row = 2)

        self.loadbutton.bind('<Return>', self.get_filename)
        self.runbutton.bind('<Return>', self.run)
        self.focusbutton = self.loadbutton
        
    def get_filename(self, event = None):

        self.filename = tkfd.askopenfilename(initialdir = Filepath +r'\batch_files',  filetypes = [('CapSim batch files','*.csv')])
        if self.filename != '':

            content       = []
            systems       = []
            file          = open(self.filename, 'r')
            file_content  = csv.reader(file)
            for row in file_content:    content.append(row)
            rows     = len(content)

            row_file            = []
            row_units           = []
            row_chemicals       = []
            row_matrices        = []
            row_components      = []
            row_sorptions       = []
            row_layers          = []
            row_reactions       = []
            row_coefficients    = []
            row_system          = []
            row_conditions      = []
            row_solver          = []
            row_ow              = []

            # Determine the rows of each section
            old_batch_file = 0
            row = 0
            try:     self.type = content[1][1]
            except :
                self.type = 'Separate'
                old_batch_file = 1

            version = content[0][1]

            while row < rows:
                if len(content[row]) > 0:
                    if content[row][0] == 'File':                               row_file.append(        row)
                    if content[row][0] == 'System Units':                       row_units.append(       row)
                    if content[row][0] == 'Chemicals':                          row_chemicals.append(   row)
                    if content[row][0] == 'Matrices':                           row_matrices.append(    row)
                    if content[row][0] == 'Matrix Components':                  row_components.append(  row)
                    if content[row][0] == 'Sorptions':                          row_sorptions.append(   row)
                    if content[row][0] == 'Layers':                             row_layers.append(      row)
                    if content[row][0] == 'Reactions':                          row_reactions.append(   row)
                    if content[row][0] == 'Reaction Coefficients':              row_coefficients.append(row)
                    if content[row][0] == 'System Properties':                  row_system.append(      row)
                    if content[row][0] == 'Auxiliary Conditions':               row_conditions.append(  row)
                    if content[row][0] == 'Solver Options':                     row_solver.append(      row)
                    if content[row][0] == 'Overlying Water Column Properties':  row_ow.append(          row)
                row = row + 1

            if self.type == 'Separate':
                for num in range(len(row_file)):
                    systems.append(self.system.copy())

                    # Read information in each section
                    systems[-1].filename       = content[row_file[num] + 1][2]

                    lengthunits = ['um', 'cm', 'm']
                    concunits   = ['ug/L', 'mg/L', 'g/L', 'umol/L', 'mmol/L', 'mol/L']
                    timeunits   = ['s', 'min', 'hr', 'day', 'yr']
                    diffunits   = ['cm^2/s', 'cm^2/yr']

                    systems[-1].lengthunits = [u'\u03BCm', 'cm', 'm']
                    systems[-1].concunits   = [u'\u03BCg/L', 'mg/L', 'g/L', u'\u03BCmol/L', 'mmol/L', 'mol/L']
                    systems[-1].timeunits   = ['s', 'min', 'hr', 'day', 'yr']
                    systems[-1].diffunits   = [u'cm\u00B2/s', u'cm\u00B2/yr']

                    systems[-1].lengthunit     = systems[-1].lengthunits[lengthunits.index(str(content[row_units[num] + 1][2]))]
                    systems[-1].concunit       = systems[-1].concunits[concunits.index(str(content[row_units[num] + 2][2]))]
                    systems[-1].timeunit       = systems[-1].timeunits[timeunits.index(str(content[row_units[num] + 3][2]))]
                    systems[-1].diffunit       = systems[-1].diffunits[diffunits.index(str(content[row_units[num] + 4][2]))]

                    systems[-1].nchemicals = int(content[row_chemicals[num]][1])
                    systems[-1].chemicals  = []
                    for i in range(systems[-1].nchemicals):
                        systems[-1].chemicals.append(Chemical(i+1, 1))
                        systems[-1].chemicals[-1].name    = content[row_chemicals[num] + 2 + i][1]
                        systems[-1].chemicals[-1].formula = formula_converter(content[row_chemicals[num] + 2 + i][2])
                        systems[-1].chemicals[-1].MW      = float(content[row_chemicals[num] + 2 + i][3])
                        systems[-1].chemicals[-1].temp    = float(content[row_chemicals[num] + 2 + i][4])
                        systems[-1].chemicals[-1].Dw      = float(content[row_chemicals[num] + 2 + i][5])
                        systems[-1].chemicals[-1].Koc     = float(content[row_chemicals[num] + 2 + i][6])
                        systems[-1].chemicals[-1].Kdoc    = float(content[row_chemicals[num] + 2 + i][7])
                        systems[-1].chemicals[-1].Ref     = (content[row_chemicals[num] + 2 + i][8])
                        systems[-1].chemicals[-1].Kf      = 0
                        systems[-1].chemicals[-1].N       = 0

                    systems[-1].nmatrices  = int(content[row_matrices[num]][1])
                    systems[-1].matrices   = []
                    current_row_components         = row_components[num] + 2
                    for i in range(systems[-1].nmatrices):
                        systems[-1].matrices.append(Matrix(i+1))
                        systems[-1].matrices[-1].name    = content[row_matrices[num] + 2 + i][1]
                        systems[-1].matrices[-1].e       = float(content[row_matrices[num] + 2 + i][3])
                        systems[-1].matrices[-1].rho     = float(content[row_matrices[num] + 2 + i][4])
                        systems[-1].matrices[-1].foc     = float(content[row_matrices[num] + 2 + i][5])
                        systems[-1].matrices[-1].model   = content[row_matrices[num] + 2 + i][6]
                        systems[-1].matrices[-1].components = []
                        for j in range (int(content[row_matrices[num] + 2 + i][2])):
                            systems[-1].matrices[-1].components.append(MatrixComponent(j))
                            systems[-1].matrices[-1].components[-1].name     =       content[current_row_components+ j][2]
                            systems[-1].matrices[-1].components[-1].e        = float(content[current_row_components+ j][4])
                            systems[-1].matrices[-1].components[-1].rho      = float(content[current_row_components+ j][5])
                            systems[-1].matrices[-1].components[-1].foc      = float(content[current_row_components+ j][6])
                            systems[-1].matrices[-1].components[-1].sorp     = 'Linear--Kd specified'
                            systems[-1].matrices[-1].components[-1].tort     = 'None'
                            if content[row_components[num]+1][3] == 'Weight fraction':
                                systems[-1].matrices[-1].components[-1].mfraction = float(content[current_row_components+ j][3])
                                systems[-1].matrices[-1].components[-1].fraction = systems[-1].matrices[-1].components[-1].mfraction/systems[-1].matrices[-1].components[-1].rho * systems[-1].matrices[-1].rho
                            else:
                                systems[-1].matrices[-1].components[-1].fraction  = float(content[current_row_components+ j][3])
                                systems[-1].matrices[-1].components[-1].mfraction = systems[-1].matrices[-1].components[-1].fraction * systems[-1].matrices[-1].components[-1].rho / systems[-1].matrices[-1].rho

                        current_row_components = current_row_components + int(content[row_matrices[num] + 2 + i][2])

                    systems[-1].component_list      = []
                    systems[-1].components          = []
                    for matrix in systems[-1].matrices:
                        for component in matrix.components:
                            try: systems[-1].component_list.index(component.name)
                            except:
                                 systems[-1].components.append(component)
                                 systems[-1].component_list.append(component.name)

                    systems[-1].sorptions  = {}
                    for i in range(len(systems[-1].components)):
                        systems[-1].sorptions[systems[-1].components[i].name]={}
                        for j in range(systems[-1].nchemicals):
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name] = Sorption(systems[-1].components[i], systems[-1].chemicals[j])
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm = content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][3]
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kinetic  = content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][4]
                            if systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Linear--Kd specified':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].K  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                            elif systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Linear--Kocfoc':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].Koc  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                            elif systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Freundlich':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].Kf  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].N   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][6])
                            else:
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].qmax  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].b     = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][6])
                            if systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kinetic == 'Transient':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].ksorp   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][7])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kdesorp = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][8])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].thalf   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][9])

                    matrix_list = [matrix.name for matrix in systems[-1].matrices]
                    systems[-1].nlayers  = int(content[row_layers[num]][1])
                    systems[-1].layers   = []
                    for i in range(systems[-1].nlayers):
                        if content[row_layers[num] + 2][1] == 'Deposition':  systems[-1].layers.append(Layer(i))
                        else:                                           systems[-1].layers.append(Layer(i + 1))
                        systems[-1].layers[i].name   = content[row_layers[num] + 2 + i][1]
                        systems[-1].layers[i].type   = content[row_layers[num] + 2 + i][2]
                        systems[-1].layers[i].h      = float(content[row_layers[num] + 2 + i][3])
                        systems[-1].layers[i].tort   = content[row_layers[num] + 2 + i][4]
                        systems[-1].layers[i].alpha  = float(content[row_layers[num] + 2 + i][5])
                        systems[-1].layers[i].doc    = float(content[row_layers[num] + 2 + i][6])
                        systems[-1].layers[i].type_index = matrix_list.index(systems[-1].layers[i].type)

                    systems[-1].nreactions  = int(content[row_reactions[num]][1])
                    systems[-1].reactions   = []
                    for i in range(systems[-1].nreactions):
                        systems[-1].reactions.append(Reaction(i+1))
                        systems[-1].reactions[i].name     = content[row_reactions[num] + 1 + i * 7][2]
                        systems[-1].reactions[i].model    = content[row_reactions[num] + 1 + i * 7][3]
                        systems[-1].reactions[i].equation = formula_converter(content[row_reactions[num] + 1 + i * 7][4])
                        systems[-1].reactions[i].reactants = []
                        systems[-1].reactions[i].products  = []
                        column = 2
                        for j in range(int(content[row_reactions[num] + 2 + i * 7][3])):
                            systems[-1].reactions[i].reactants.append(Reactant(j+1))
                            systems[-1].reactions[i].reactants[j].name   = content[row_reactions[num] + 3 + i * 7][column]
                            systems[-1].reactions[i].reactants[j].formula = formula_converter(content[row_reactions[num] + 4 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].MW = float(content[row_reactions[num] + 5 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].coef = float(content[row_reactions[num] + 6 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].index = float(content[row_reactions[num] + 7 + i * 7][column])
                            column = column + 1
                        column = column + 1

                        for j in range(int(content[row_reactions[num] + 2 + i * 7][column+1])):
                            systems[-1].reactions[i].products.append(Product(j+1))
                            systems[-1].reactions[i].products[j].name   = content[row_reactions[num] + 3 + i * 7][column]
                            systems[-1].reactions[i].products[j].formula = formula_converter(content[row_reactions[num] + 4 + i * 7][column])
                            systems[-1].reactions[i].products[j].MW = float(content[row_reactions[num] + 5 + i * 7][column])
                            systems[-1].reactions[i].products[j].coef = float(content[row_reactions[num] + 6 + i * 7][column])
                            column = column + 1

                    systems[-1].coefficients   = {}
                    for i in range(systems[-1].nlayers):
                        systems[-1].coefficients[systems[-1].layers[i].name]={}
                        for j in range(systems[-1].nreactions):
                            systems[-1].coefficients[systems[-1].layers[i].name][systems[-1].reactions[j].name]=Coefficient(systems[-1].layers[i], systems[-1].reactions[j])
                            systems[-1].coefficients[systems[-1].layers[i].name][systems[-1].reactions[j].name].lam = float(content[row_coefficients[num] + 2 + i * systems[-1].nreactions + j][3])

                    systems[-1].adv    = content[row_system[num] + 1][2]
                    systems[-1].Vdar   = float(content[row_system[num] + 2][2])
                    systems[-1].Vtidal = float(content[row_system[num] + 3][2])
                    systems[-1].ptidal = float(content[row_system[num] + 4][2])
                    systems[-1].bio    = content[row_system[num] + 5][2]
                    systems[-1].hbio   = float(content[row_system[num] + 6][2])
                    systems[-1].sigma  = float(content[row_system[num] + 7][2])
                    systems[-1].Dbiop  = float(content[row_system[num] + 8][2])
                    systems[-1].Dbiopw = float(content[row_system[num] + 9][2])
                    systems[-1].con    = content[row_system[num] + 10][2]
                    systems[-1].hcon   = float(content[row_system[num] + 11][2])
                    systems[-1].t90    = float(content[row_system[num] + 12][2])

                    systems[-1].biomix = 0
                    if systems[-1].bio <> 'None':
                        if systems[-1].layers[0].name == 'Deposition':
                            systems[-1].biomix = 1
                        elif systems[-1].hbio >  systems[-1].layers[0].h:
                            systems[-1].biomix = 1

                    systems[-1].BCs = {}
                    row = row_conditions[num] + 2
                    systems[-1].topBCtype   = content[row][2]
                    column = 4
                    for chemical in systems[-1].chemicals:
                        systems[-1].BCs[chemical.name] = BC(chemical.name, 1)
                        if systems[-1].topBCtype == 'Fixed Concentration':
                            systems[-1].BCs[chemical.name].Co = float(content[row][column])
                        elif systems[-1].topBCtype == 'Mass transfer':
                            systems[-1].BCs[chemical.name].k   = float(content[row  ][column])
                            systems[-1].BCs[chemical.name].Cw  = float(content[row+1][column])
                        else:
                            systems[-1].BCs[chemical.name].k   = float(content[row  ][column])
                            systems[-1].BCs[chemical.name].tau = float(content[row+1][column])
                        column = column + 1

                    systems[-1].ICs      = {}
                    systems[-1].SolidICs = {}

                    if systems[-1].topBCtype == 'Fixed Concentration': row = row_conditions[num] + 4
                    else:                                         row = row_conditions[num] + 5
                    for layer in systems[-1].layers:
                        layer.ICtype = content[row][2]
                        systems[-1].ICs[layer.name] = {}
                        systems[-1].SolidICs[layer.name] = {}
                        column = 4
                        if layer.ICtype == 'Uniform':
                            for chemical in systems[-1].chemicals:
                                systems[-1].ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
                                systems[-1].ICs[layer.name][chemical.name].uniform = float(content[row][column])
                                column = column + 1

                            for component in systems[-1].matrices[layer.type_index].components:
                                systems[-1].SolidICs[layer.name][component.name] = {}
                                for chemical in systems[-1].chemicals:
                                    systems[-1].SolidICs[layer.name][component.name][chemical.name] = SolidIC(component.name,layer.name,chemical.name)
                                    if systems[-1].sorptions[component.name][chemical.name].kinetic == 'Transient':
                                        systems[-1].SolidICs[layer.name][component.name][chemical.name].uniform = float(content[row][column])
                                        column = column + 1

                            row = row + 1

                        else:
                            for chemical in systems[-1].chemicals:
                                systems[-1].ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
                                systems[-1].ICs[layer.name][chemical.name].top = float(content[row][column])
                                systems[-1].ICs[layer.name][chemical.name].bot = float(content[row+1][column])
                                column = column + 1
                                for component in systems[-1].matrices[layer.type_index].components:
                                    systems[-1].SolidICs[layer.name][component.name] = {}
                                    for chemical in systems[-1].chemicals:
                                        systems[-1].SolidICs[layer.name][component.name][chemical.name] = SolidIC(component.name,layer.name,chemical.name)
                                        if systems[-1].sorptions[component.name][chemical.name].kinetic == 'Transient':
                                            systems[-1].SolidICs[layer.name][component.name][chemical.name].top = float(content[row][column])
                                            systems[-1].SolidICs[layer.name][component.name][chemical.name].bot = float(content[row + 1][column])
                                            column = column + 1

                            row = row + 2

                    row     = row + 1
                    column  = 4
                    systems[-1].botBCtype   = content[row][2]
                    for chemical in systems[-1].chemicals:
                        if systems[-1].botBCtype == 'Fixed Concentration' or systems[-1].botBCtype == 'Flux-matching':
                            systems[-1].BCs[chemical.name].Cb = float(content[row][column])
                        column = column + 1

                    systems[-1].tstart       = float(content[row_solver[num] + 1][2])
                    systems[-1].tfinal       = float(content[row_solver[num] + 2][2])
                    systems[-1].outputsteps  = int(content[row_solver[num] + 3][2])
                    systems[-1].timeoption   = content[row_solver[num] + 4][2]
                    systems[-1].discrete     = content[row_solver[num] + 5][2]
                    systems[-1].ptotal       = content[row_solver[num] + 6][2]
                    systems[-1].delt         = float(content[row_solver[num] + 7][2])
                    systems[-1].ptype        = content[row_solver[num] + 8][2]
                    systems[-1].tvariable    = content[row_solver[num] + 9][2]
                    systems[-1].delz         = []
                    systems[-1].players      = []
                    column = 2
                    for layer in systems[-1].layers:
                        systems[-1].delz.append(float(content[row_solver[num] + 11][column]))
                        systems[-1].players.append(float(content[row_solver[num] + 12][column]))
                        column = column + 1
                    systems[-1].tidalsteps    = float(content[row_solver[num] + 13][2])
                    systems[-1].nonlinear     = content[row_solver[num] + 14][2]
                    systems[-1].nlerror       = float(content[row_solver[num] + 15][2])
                    systems[-1].depoption    = content[row_solver[num] + 16][2]
                    systems[-1].depgrid      = int(content[row_solver[num] + 17][2])
                    systems[-1].averageoption= content[row_solver[num] + 18][2]

                    systems[-1].taucoefs           = {}
                    systems[-1].taucoefs['Q']      = float(content[row_ow[num] + 1][2])
                    systems[-1].taucoefs['V']      = float(content[row_ow[num] + 2][2])
                    systems[-1].taucoefs['h']      = float(content[row_ow[num] + 3][2])
                    systems[-1].taucoefs['DOC']    = float(content[row_ow[num] + 4][2])
                    systems[-1].taucoefs['Qevap']  = float(content[row_ow[num] + 5][2])
                    systems[-1].taucoefs['Decay']  = 'First order'
                    systems[-1].taucoefs['Evap']   = 'First order'
                    for n in range(systems[-1].nchemicals):
                        systems[-1].BCs[systems[-1].chemicals[n].name].kdecay = float(content[row_ow[num] + 7][2 + n])
                        systems[-1].BCs[systems[-1].chemicals[n].name].kevap  = float(content[row_ow[num] + 8][2 + n])

                    # Fill the rest of the systems[-1] properties using default properties
                    systems[-1].bltype             = 'River'
                    systems[-1].blcoefs            = {}
                    systems[-1].blcoefs['vx']      = 1.
                    systems[-1].blcoefs['n']       = 0.02
                    systems[-1].blcoefs['hriver']  = 5.
                    systems[-1].blcoefs['rh']      = 5.
                    systems[-1].blcoefs['nu']      = 1e-6

                    systems[-1].blcoefs['rhoair']  = 1.
                    systems[-1].blcoefs['rhowater']= 1000.
                    systems[-1].blcoefs['vwind']   = 5.
                    systems[-1].blcoefs['hlake']   = 10.
                    systems[-1].blcoefs['llake']   = 1000.

                    if systems[-1].nlayers > 0:
                        if systems[-1].layers[0].name == 'Deposition':
                            systems[-1].dep  = 'Deposition'
                            systems[-1].Vdep = systems[-1].layers[0].h
                        else:
                            systems[-1].dep  = 0
                            systems[-1].Vdep = 0

            elif self.type == 'Continuous':

                tstart  = []
                tfinal  = []
                sysnum  = []
                timenum = []


                for i in range(len(row_file)):
                    tnum = int(content[row_solver[i]][1])
                    for j in range(tnum):
                        tstart.append(float(content[row_solver[i] + 1][2 + j]))
                        tfinal.append(float(content[row_solver[i] + 2][2 + j]))
                        sysnum.append(i)
                        timenum.append(j)


                nums     = []
                timenums = []
                time     = 0
                for i in range(len(sysnum)):
                    nums.append(sysnum[tstart.index(time)])
                    timenums.append(timenum[tstart.index(time)])
                    time = tfinal[tstart.index(time)]

                for n_num in range(len(nums)):
                    num = nums[n_num]
                    timenum = timenums[n_num]
                    systems.append(self.system.copy())

                    # Read information in each section

                    systems[-1].filename       = content[row_file[num] + 1][2]

                    lengthunits = ['um', 'cm', 'm']
                    concunits   = ['ug/L', 'mg/L', 'g/L', 'umol/L', 'mmol/L', 'mol/L']
                    timeunits   = ['s', 'min', 'hr', 'day', 'yr']
                    diffunits   = ['cm^2/s', 'cm^2/yr']

                    systems[-1].lengthunits = [u'\u03BCm', 'cm', 'm']
                    systems[-1].concunits   = [u'\u03BCg/L', 'mg/L', 'g/L', u'\u03BCmol/L', 'mmol/L', 'mol/L']
                    systems[-1].timeunits   = ['s', 'min', 'hr', 'day', 'yr']
                    systems[-1].diffunits   = [u'cm\u00B2/s', u'cm\u00B2/yr']

                    systems[-1].lengthunit     = systems[-1].lengthunits[lengthunits.index(str(content[row_units[num] + 1][2]))]
                    systems[-1].concunit       = systems[-1].concunits[concunits.index(str(content[row_units[num] + 2][2]))]
                    systems[-1].timeunit       = systems[-1].timeunits[timeunits.index(str(content[row_units[num] + 3][2]))]
                    systems[-1].diffunit       = systems[-1].diffunits[diffunits.index(str(content[row_units[num] + 4][2]))]

                    systems[-1].nchemicals = int(content[row_chemicals[num]][1])
                    systems[-1].chemicals  = []
                    for i in range(systems[-1].nchemicals):
                        systems[-1].chemicals.append(Chemical(i+1, 1))
                        systems[-1].chemicals[-1].name    = content[row_chemicals[num] + 2 + i][1]
                        systems[-1].chemicals[-1].formula = formula_converter(content[row_chemicals[num] + 2 + i][2])
                        systems[-1].chemicals[-1].MW      = float(content[row_chemicals[num] + 2 + i][3])
                        systems[-1].chemicals[-1].temp    = float(content[row_chemicals[num] + 2 + i][4])
                        systems[-1].chemicals[-1].Dw      = float(content[row_chemicals[num] + 2 + i][5])
                        systems[-1].chemicals[-1].Koc     = float(content[row_chemicals[num] + 2 + i][6])
                        systems[-1].chemicals[-1].Kdoc    = float(content[row_chemicals[num] + 2 + i][7])
                        systems[-1].chemicals[-1].Ref     = (content[row_chemicals[num] + 2 + i][8])
                        systems[-1].chemicals[-1].Kf      = 0
                        systems[-1].chemicals[-1].N       = 0



                    systems[-1].nmatrices  = int(content[row_matrices[num]][1])
                    systems[-1].matrices   = []
                    current_row_components         = row_components[num] + 2
                    for i in range(systems[-1].nmatrices):
                        systems[-1].matrices.append(Matrix(i+1))
                        systems[-1].matrices[-1].name    = content[row_matrices[num] + 2 + i][1]
                        systems[-1].matrices[-1].e       = float(content[row_matrices[num] + 2 + i][3])
                        systems[-1].matrices[-1].rho     = float(content[row_matrices[num] + 2 + i][4])
                        systems[-1].matrices[-1].foc     = float(content[row_matrices[num] + 2 + i][5])
                        systems[-1].matrices[-1].model   = content[row_matrices[num] + 2 + i][6]
                        systems[-1].matrices[-1].components = []
                        for j in range (int(content[row_matrices[num] + 2 + i][2])):
                            systems[-1].matrices[-1].components.append(MatrixComponent(j))
                            systems[-1].matrices[-1].components[-1].name     =       content[current_row_components+ j][2]
                            systems[-1].matrices[-1].components[-1].e        = float(content[current_row_components+ j][4])
                            systems[-1].matrices[-1].components[-1].rho      = float(content[current_row_components+ j][5])
                            systems[-1].matrices[-1].components[-1].foc      = float(content[current_row_components+ j][6])
                            systems[-1].matrices[-1].components[-1].sorp     = 'Linear--Kd specified'
                            systems[-1].matrices[-1].components[-1].tort     = 'None'
                            if row_components[num][3] == 'Weight fraction':
                                systems[-1].matrices[-1].components[-1].mfraction = float(content[current_row_components+ j][3])
                                systems[-1].matrices[-1].components[-1].fraction = systems[-1].matrices[-1].components[-1].mfraction/systems[-1].matrices[-1].components[-1].rho * systems[-1].matrices[-1].rho
                            else:
                                systems[-1].matrices[-1].components[-1].fraction  = float(content[current_row_components+ j][3])
                                systems[-1].matrices[-1].components[-1].mfraction = systems[-1].matrices[-1].components[-1].fraction * systems[-1].matrices[-1].components[-1].rho / systems[-1].matrices[-1].rho

                        current_row_components = current_row_components + int(content[row_matrices[num] + 2 + i][2])

                    systems[-1].component_list      = []
                    systems[-1].components          = []
                    for matrix in systems[-1].matrices:
                        for component in matrix.components:
                            try: systems[-1].component_list.index(component.name)
                            except:
                                 systems[-1].components.append(component)
                                 systems[-1].component_list.append(component.name)

                    systems[-1].sorptions  = {}
                    for i in range(len(systems[-1].components)):
                        systems[-1].sorptions[systems[-1].components[i].name]={}
                        for j in range(systems[-1].nchemicals):
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name] = Sorption(systems[-1].components[i], systems[-1].chemicals[j])
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm = content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][3]
                            systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kinetic  = content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][4]
                            if systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Linear--Kd specified':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].K  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                            elif systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Linear--Kocfoc':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].Koc  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                            elif systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].isotherm == 'Freundlich':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].Kf  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].N   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][6])
                            else:
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].qmax  = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][5])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].b     = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][6])
                            if systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kinetic == 'Transient':
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].ksorp   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][7])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].kdesorp = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][8])
                                systems[-1].sorptions[systems[-1].components[i].name][systems[-1].chemicals[j].name].thalf   = float(content[row_sorptions[num] + 2 + i * systems[-1].nchemicals+ j][9])

                    matrix_list = [matrix.name for matrix in systems[-1].matrices]
                    systems[-1].nlayers  = int(content[row_layers[num]][1])
                    systems[-1].layers   = []
                    for i in range(systems[-1].nlayers):
                        if content[row_layers[num] + 2][1] == 'Deposition':  systems[-1].layers.append(Layer(i))
                        else:                                           systems[-1].layers.append(Layer(i + 1))
                        systems[-1].layers[i].name   = content[row_layers[num] + 2 + i][1]
                        systems[-1].layers[i].type   = content[row_layers[num] + 2 + i][2]
                        systems[-1].layers[i].h      = float(content[row_layers[num] + 2 + i][3])
                        systems[-1].layers[i].tort   = content[row_layers[num] + 2 + i][4]
                        systems[-1].layers[i].alpha  = float(content[row_layers[num] + 2 + i][5])
                        systems[-1].layers[i].doc    = float(content[row_layers[num] + 2 + i][6])
                        systems[-1].layers[i].type_index = matrix_list.index(systems[-1].layers[i].type)

                    systems[-1].nreactions  = int(content[row_reactions[num]][1])
                    systems[-1].reactions   = []
                    for i in range(systems[-1].nreactions):
                        systems[-1].reactions.append(Reaction(i+1))
                        systems[-1].reactions[i].name     = content[row_reactions[num] + 1 + i * 7][2]
                        systems[-1].reactions[i].model    = content[row_reactions[num] + 1 + i * 7][3]
                        systems[-1].reactions[i].equation = formula_converter(content[row_reactions[num] + 1 + i * 7][4])
                        systems[-1].reactions[i].reactants = []
                        systems[-1].reactions[i].products  = []
                        column = 2
                        for j in range(int(content[row_reactions[num] + 2 + i * 7][3])):
                            systems[-1].reactions[i].reactants.append(Reactant(j+1))
                            systems[-1].reactions[i].reactants[j].name   = content[row_reactions[num] + 3 + i * 7][column]
                            systems[-1].reactions[i].reactants[j].formula = formula_converter(content[row_reactions[num] + 4 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].MW = float(content[row_reactions[num] + 5 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].coef = float(content[row_reactions[num] + 6 + i * 7][column])
                            systems[-1].reactions[i].reactants[j].index = float(content[row_reactions[num] + 7 + i * 7][column])
                            column = column + 1
                        column = column + 1

                        for j in range(int(content[row_reactions[num] + 2 + i * 7][column+1])):
                            systems[-1].reactions[i].products.append(Product(j+1))
                            systems[-1].reactions[i].products[j].name   = content[row_reactions[num] + 3 + i * 7][column]
                            systems[-1].reactions[i].products[j].formula = formula_converter(content[row_reactions[num] + 4 + i * 7][column])
                            systems[-1].reactions[i].products[j].MW = float(content[row_reactions[num] + 5 + i * 7][column])
                            systems[-1].reactions[i].products[j].coef = float(content[row_reactions[num] + 6 + i * 7][column])
                            column = column + 1

                    systems[-1].coefficients   = {}
                    for i in range(systems[-1].nlayers):
                        systems[-1].coefficients[systems[-1].layers[i].name]={}
                        for j in range(systems[-1].nreactions):
                            systems[-1].coefficients[systems[-1].layers[i].name][systems[-1].reactions[j].name]=Coefficient(systems[-1].layers[i], systems[-1].reactions[j])
                            systems[-1].coefficients[systems[-1].layers[i].name][systems[-1].reactions[j].name].lam = float(content[row_coefficients[num] + 2 + i * systems[-1].nreactions + j][3])

                    systems[-1].adv    = content[row_system[num] + 1][2]
                    systems[-1].Vdar   = float(content[row_system[num] + 2][2])
                    systems[-1].Vtidal = float(content[row_system[num] + 3][2])
                    systems[-1].ptidal = float(content[row_system[num] + 4][2])
                    systems[-1].bio    = content[row_system[num] + 5][2]
                    systems[-1].hbio   = float(content[row_system[num] + 6][2])
                    systems[-1].sigma  = float(content[row_system[num] + 7][2])
                    systems[-1].Dbiop  = float(content[row_system[num] + 8][2])
                    systems[-1].Dbiopw = float(content[row_system[num] + 9][2])
                    systems[-1].con    = content[row_system[num] + 10][2]
                    systems[-1].hcon   = float(content[row_system[num] + 11][2])
                    systems[-1].t90    = float(content[row_system[num] + 12][2])

                    systems[-1].biomix = 0
                    if systems[-1].bio <> 'None':
                        if systems[-1].layers[0].name == 'Deposition':
                            systems[-1].biomix = 1
                        elif systems[-1].hbio >  systems[-1].layers[0].h:
                            systems[-1].biomix = 1

                    systems[-1].BCs = {}
                    row = row_conditions[num] + 2
                    systems[-1].topBCtype   = content[row][2]
                    column = 4
                    for chemical in systems[-1].chemicals:
                        systems[-1].BCs[chemical.name] = BC(chemical.name, 1)
                        if systems[-1].topBCtype == 'Fixed Concentration':
                            systems[-1].BCs[chemical.name].Co = float(content[row][column])
                        elif systems[-1].topBCtype == 'Mass transfer':
                            systems[-1].BCs[chemical.name].k   = float(content[row  ][column])
                            systems[-1].BCs[chemical.name].Cw  = float(content[row+1][column])
                        else:
                            systems[-1].BCs[chemical.name].k   = float(content[row  ][column])
                            systems[-1].BCs[chemical.name].tau = float(content[row+1][column])
                        column = column + 1

                    systems[-1].ICs      = {}
                    systems[-1].SolidICs = {}

                    if systems[-1].topBCtype == 'Fixed Concentration': row = row_conditions[num] + 4
                    else:                                              row = row_conditions[num] + 5
                    for layer in systems[-1].layers:
                        layer.ICtype = content[row][2]
                        systems[-1].ICs[layer.name] = {}
                        systems[-1].SolidICs[layer.name] = {}
                        column = 4
                        if layer.ICtype == 'Uniform':
                            for chemical in systems[-1].chemicals:
                                systems[-1].ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
                                systems[-1].ICs[layer.name][chemical.name].uniform = float(content[row][column])
                                column = column + 1

                            for component in systems[-1].matrices[layer.type_index].components:
                                systems[-1].SolidICs[layer.name][component.name] = {}
                                for chemical in systems[-1].chemicals:
                                    systems[-1].SolidICs[layer.name][component.name][chemical.name] = SolidIC(component.name,layer.name,chemical.name)
                                    if systems[-1].sorptions[component.name][chemical.name].kinetic == 'Transient':
                                        systems[-1].SolidICs[layer.name][component.name][chemical.name].uniform = float(content[row][column])
                                        column = column + 1

                            row = row + 1

                        else:
                            for chemical in systems[-1].chemicals:
                                systems[-1].ICs[layer.name][chemical.name] = IC(layer.name, chemical.name)
                                systems[-1].ICs[layer.name][chemical.name].top = float(content[row][column])
                                systems[-1].ICs[layer.name][chemical.name].bot = float(content[row+1][column])
                                column = column + 1
                                for component in systems[-1].matrices[layer.type_index].components:
                                    systems[-1].SolidICs[layer.name][component.name] = {}
                                    for chemical in systems[-1].chemicals:
                                        systems[-1].SolidICs[layer.name][component.name][chemical.name] = SolidIC(component.name,layer.name,chemical.name)
                                        if systems[-1].sorptions[component.name][chemical.name].kinetic == 'Transient':
                                            systems[-1].SolidICs[layer.name][component.name][chemical.name].top = float(content[row][column])
                                            systems[-1].SolidICs[layer.name][component.name][chemical.name].bot = float(content[row + 1][column])
                                            column = column + 1

                            row = row + 2

                    row     = row + 1
                    column  = 4
                    systems[-1].botBCtype   = content[row][2]
                    for chemical in systems[-1].chemicals:
                        if systems[-1].botBCtype == 'Fixed Concentration' or systems[-1].botBCtype == 'Flux-matching':
                            systems[-1].BCs[chemical.name].Cb = float(content[row][column])
                        column = column + 1

                    systems[-1].tstart       = float(content[row_solver[num] + 1][2 + timenum])
                    systems[-1].tfinal       = float(content[row_solver[num] + 2][2 + timenum])
                    systems[-1].outputsteps  = int(content[row_solver[num] + 3][2])
                    systems[-1].timeoption   = content[row_solver[num] + 4][2]
                    systems[-1].discrete     = content[row_solver[num] + 5][2]
                    systems[-1].ptotal       = content[row_solver[num] + 6][2]
                    systems[-1].delt         = float(content[row_solver[num] + 7][2])
                    systems[-1].ptype        = content[row_solver[num] + 8][2]
                    systems[-1].tvariable    = content[row_solver[num] + 9][2]
                    systems[-1].delz         = []
                    systems[-1].players      = []
                    column = 2
                    for layer in systems[-1].layers:
                        systems[-1].delz.append(float(content[row_solver[num] + 11][column]))
                        systems[-1].players.append(float(content[row_solver[num] + 12][column]))
                        column = column + 1
                    systems[-1].tidalsteps    = float(content[row_solver[num] + 13][2])
                    systems[-1].nonlinear     = content[row_solver[num] + 14][2]
                    systems[-1].nlerror       = float(content[row_solver[num] + 15][2])
                    systems[-1].depoption    = content[row_solver[num] + 14][2]
                    systems[-1].depgrid      = int(content[row_solver[num] + 15][2])
                    systems[-1].averageoption= content[row_solver[num] + 16][2]

                    systems[-1].taucoefs           = {}
                    systems[-1].taucoefs['Q']      = float(content[row_ow[num] + 1][2])
                    systems[-1].taucoefs['V']      = float(content[row_ow[num] + 2][2])
                    systems[-1].taucoefs['h']      = float(content[row_ow[num] + 3][2])
                    systems[-1].taucoefs['DOC']    = float(content[row_ow[num] + 4][2])
                    systems[-1].taucoefs['Qevap']  = float(content[row_ow[num] + 5][2])
                    systems[-1].taucoefs['Decay']  = 'First order'
                    systems[-1].taucoefs['Evap']   = 'First order'
                    for n in range(systems[-1].nchemicals):
                        systems[-1].BCs[systems[-1].chemicals[n].name].kdecay = float(content[row_ow[num] + 7][2 + n])
                        systems[-1].BCs[systems[-1].chemicals[n].name].kevap  = float(content[row_ow[num] + 8][2 + n])

                    # Fill the rest of the systems[-1] properties using default properties

                    systems[-1].bltype             = 'River'
                    systems[-1].blcoefs            = {}
                    systems[-1].blcoefs['vx']      = 1.
                    systems[-1].blcoefs['n']       = 0.02
                    systems[-1].blcoefs['hriver']  = 5.
                    systems[-1].blcoefs['rh']      = 5.
                    systems[-1].blcoefs['nu']      = 1e-6

                    systems[-1].blcoefs['rhoair']  = 1.
                    systems[-1].blcoefs['rhowater']= 1000.
                    systems[-1].blcoefs['vwind']   = 5.
                    systems[-1].blcoefs['hlake']   = 10.
                    systems[-1].blcoefs['llake']   = 1000.

                    if systems[-1].nlayers > 0:
                        if systems[-1].layers[0].name == 'Deposition':
                            systems[-1].dep  = 'Deposition'
                            systems[-1].Vdep = systems[-1].layers[0].h
                        else:
                            systems[-1].dep  = 0
                            systems[-1].Vdep = 0

            self.systems = systems

            self.loadbutton.grid_forget()
            self.runbutton.grid(row = 2)
            self.runbutton.focus_set()

            #except:
            #    self.show_error()

    def run(self, event = None):

        self.master.tk.quit()

    def show_error(self, event = None):

        tkmb.showerror(title = 'Run Error', message = 'Unable to process the file')

        self.runbutton.grid_forget()
        self.loadbutton.grid(row = 2)
        self.loadbutton.focus_set()

        return 2

def make_batch(system):

    root = CapSimWindow(buttons = 2)
    root.make_window(BatchFile(root, system))
    root.mainloop()

    if root.main.get() == 1:
        root.window.systems = None
        root.window.type    = None

    root.destroy()

    return root.window.systems, root.window.type, root.main.get()
