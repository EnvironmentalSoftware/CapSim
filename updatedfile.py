from capsim_object_types  import System, Chemical, Matrix, MatrixComponent, Layer, Sorption, Reaction, Coefficient, IC, BC, ChemicalDatabase
from reactioneditor       import Reactant

def get_updatedfile(system, version, fonttype):

    try:    tidal_test = system.tidal
    except: system.tidal = 0
    
    try:    ptype_test = system.ptype
    except: system.ptype = 'Uniform size'

    new_system = System(version, fonttype, 'Calibri 11')

    new_system.lengthunits = [u'\u03BCm', 'cm', 'm']
    new_system.concunits   = [u'\u03BCg/L', 'mg/L', 'g/L', u'\u03BCmol/L', 'mmol/L', 'mol/L']
    new_system.timeunits   = ['s', 'min', 'hr', 'day', 'yr']
    new_system.diffunits   = [u'cm\u00B2/s', u'cm\u00B2/yr']

    new_system.lengthunit               = 'cm'
    new_system.diffunit                 =  u'cm\u00B2/s'
    new_system.timeunit                 = 'yr'
    new_system.concunit                 = u'\u03BCg/L'

    new_system.nchemicals               = 1
    new_system.chemicals                = [Chemical(1, soluable = 1)]
    new_system.chemicals[0].soluable    = 1
    new_system.chemicals[0].name        = system.chemical.name
    new_system.chemicals[0].MW          = system.chemical.MW
    new_system.chemicals[0].formula     = ' '
    new_system.chemicals[0].Ref         = ' '
    new_system.chemicals[0].temp        = system.temp
    new_system.chemicals[0].Dw          = system.Dw
    new_system.chemicals[0].Koc         = system.Koc
    new_system.chemicals[0].Kdoc        = system.Kdoc
    new_system.chemicals[0].Kf          = 0
    new_system.chemicals[0].N           = 0

    if system.deposition == 0: system.deplayer = []
    else:                      system.deplayer = [system.deplayer]

    new_system.layers = []
    for layer in (system.deplayer + system.layers):
        new_system.layers.append(Layer(layer.number))
        new_system.layers[-1].type  = layer.type
        new_system.layers[-1].tort  = layer.tort
        new_system.layers[-1].h     = layer.h
        new_system.layers[-1].alpha = layer.alpha
        new_system.layers[-1].doc   = system.doc

    if new_system.layers[0].number == 0:  new_system.layers[0].name == 'Deposition'
        
#======================================================================================================================
    new_system.components               = [MatrixComponent(1)]
    new_system.components[0].name       = system.layers[0].type
    new_system.components[0].fraction   = 1.    
    new_system.components[0].e          = system.layers[0].e
    new_system.components[0].rho        = system.layers[0].rho
    new_system.components[0].foc        = system.layers[0].foc
    new_system.components[0].tort       = system.layers[0].tort
    new_system.components[0].sorp       = system.layers[0].sorption
    
    component_list                      = [system.layers[0].type]
    name_list                           = [system.layers[0].type]
    sorp_list                           = []
    sorp_list.append([])
    
    if system.layers[0].sorption == 'Linear--Kd specified':
        sorp_list[0].append(system.layers[0].K)
    if system.layers[0].sorption == 'Freundlich':
        sorp_list[0].append(system.layers[0].Kf)
        sorp_list[0].append(system.layers[0].N)
    if system.layers[0].sorption == 'Langmuir':
        sorp_list[0].append(system.layers[0].qmax)
        sorp_list[0].append(system.layers[0].b)
        
    
    new_system.sorptions = {}
    new_system.sorptions[new_system.components[0].name]={}
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name]=Sorption(new_system.components[0], new_system.chemicals[0])
    if system.layers[0].sorption == 'Linear--Kd specified':
        new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].K    = system.layers[0].K
    if system.layers[0].sorption == 'Freundlich':
        new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].Kf   = system.layers[0].Kf
        new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].N    = system.layers[0].N
    if system.layers[0].sorption == 'Langmuir':
        new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].qmax = system.layers[0].qmax
        new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].b    = system.layers[0].b

    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].kinetic  = 'Equilibrium'
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].kdesorp  = 0
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].ksorp    = 0
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].thalf    = 0
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].cinit    = 0
    new_system.sorptions[new_system.components[0].name][new_system.chemicals[0].name].qinit    = 0

    for layer in (system.deplayer + system.layers):
        check = 2
        for component in new_system.components:
            if layer.type == component.name:
                check = 0
                if layer.e        != component.e:    check = 1
                if layer.rho      != component.rho:  check = 1
                if layer.foc      != component.foc:  check = 1
                if layer.sorption != component.sorp:
                    check = 1
                else:
                    if layer.sorption == 'Linear--Kd specified':
                        if sorp_list[new_system.components.index(component)][0] != layer.K:    check = 1
                    if layer.sorption == 'Freundlich':
                        if sorp_list[new_system.components.index(component)][0] != layer.Kf:   check = 1
                        if sorp_list[new_system.components.index(component)][1] != layer.N:    check = 1
                    if layer.sorption == 'Langmuir':
                        if sorp_list[new_system.components.index(component)][0] != layer.qmax: check = 1
                        if sorp_list[new_system.components.index(component)][1] != layer.b:    check = 1

        if check == 1:
            component_list.append(layer.type)
            new_system.components.append(MatrixComponent(len(new_system.components)+1))
            new_system.components[-1].name      = layer.type + ' ' + str(component_list.count(layer.type))
            new_system.components[-1].fraction  = 1.
            new_system.components[-1].mfraction = 1.
            new_system.components[-1].e         = layer.e
            new_system.components[-1].rho       = layer.rho
            new_system.components[-1].foc       = layer.foc
            new_system.components[-1].tort      = layer.tort
            new_system.components[-1].sorp      = layer.sorption

            new_system.layers[(system.deplayer + system.layers).index(layer)].type = new_system.components[-1].name
            new_system.sorptions[new_system.components[-1].name]={}
            new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name] = Sorption(new_system.components[-1], new_system.chemicals[0])
            sorp_list.append([])
            if layer.sorption == 'Linear--Kd specified':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].K    = layer.K
                sorp_list[-1].append(layer.K)
            if layer.sorption == 'Freundlich':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].Kf   = layer.Kf
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].N    = layer.N
                sorp_list[-1].append(layer.Kf)
                sorp_list[-1].append(layer.N)
            if layer.sorption == 'Langmuir':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].qmax = layer.qmax
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].b    = layer.b
                sorp_list[-1].append(layer.qmax)
                sorp_list[-1].append(layer.b)

        elif check == 2:
            name_list.append(layer.type)
            component_list.append(layer.type)
            new_system.components.append(MatrixComponent(len(new_system.components)+1))
            new_system.components[-1].name      = layer.type
            new_system.components[-1].fraction  = 1.
            new_system.components[-1].mfraction = 1.
            new_system.components[-1].e         = layer.e
            new_system.components[-1].rho       = layer.rho
            new_system.components[-1].foc       = layer.foc
            new_system.components[-1].tort      = layer.tort
            new_system.components[-1].sorp      = layer.sorption
            
            new_system.sorptions[new_system.components[-1].name]={}
            new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name] = Sorption(new_system.components[-1], new_system.chemicals[0])
            sorp_list.append([])
            if layer.sorption == 'Linear--Kd specified':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].K    = layer.K
                sorp_list[-1].append(layer.K)              
            if layer.sorption == 'Freundlich':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].Kf   = layer.Kf
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].N    = layer.N
                sorp_list[-1].append(layer.Kf)
                sorp_list[-1].append(layer.N)
            if layer.sorption == 'Langmuir':
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].qmax = layer.qmax
                new_system.sorptions[new_system.components[-1].name][new_system.chemicals[0].name].b    = layer.b
                sorp_list[-1].append(layer.qmax)
                sorp_list[-1].append(layer.b)

    for component_name in name_list:
        if component_list.count(component_name) > 1:
            new_system.sorptions[component_name + ' ' + str(1)]={}
            new_system.sorptions[component_name + ' ' + str(1)][new_system.chemicals[0].name] = new_system.sorptions[component_name][new_system.chemicals[0].name].copy()
            del new_system.sorptions[component_name][new_system.chemicals[0].name]
            for layer in new_system.layers:
                if layer.type == component_name: layer.type = component_name + ' ' + str(1)
            new_system.components[component_list.index(component_name)].name = component_name + ' ' + str(1)
            
    new_system.component_list = [component.name for component in new_system.components]
    for layer in new_system.layers:
        layer.type_index = new_system.component_list.index(layer.type)
            
    new_system.matrices = [Matrix(i+1) for i in range(len(new_system.components))]
    new_system.nmatrices = len(new_system.matrices)

    for i in range (new_system.nmatrices):
        new_system.matrices[i].name = new_system.components[i].name
        new_system.matrices[i].e    = new_system.components[i].e
        new_system.matrices[i].rho  = new_system.components[i].rho
        new_system.matrices[i].foc  = new_system.components[i].foc
        new_system.matrices[i].model= 'Linear'
        new_system.matrices[i].components=[new_system.components[i]]
        
#======================================================================================================================
    new_system.nlayers = len(new_system.layers)
    
    if new_system.layers[0].number == 0:
        new_system.dep  = 'Deposition'
        new_system.Vdep = system.Vdep
    else:
        new_system.dep  = 0
        new_system.Vdep = 0

    if system.bioturbation == 1:    new_system.bio = 'Bioturbation'
    else:                           new_system.bio = 'None'
    
    if system.tidal == 1:           new_system.adv = 'Tidal oscillation'
    elif system.Vdar > 0:           new_system.adv = 'Steady flow'
    else:                           new_system.adv = 'None'

    if system.consolidation == 1:   new_system.con = 'Consolidation'
    else:                           new_system.con = 'None'

    new_system.Vdar   = system.Vdar
    if new_system.adv == 'Tidal oscillation':
        new_system.Vtidal = system.Vtidal
        new_system.ptidal = system.ptidal
    else:
        new_system.Vtidal = 0
        new_system.ptidal = 0
        
    new_system.hbio   = system.hbio
    new_system.Dbiop  = system.Dbiop
    new_system.Dbiopw = system.Dbiopw
    new_system.hcon   = system.hcon
    new_system.t90    = system.t90

    new_system.bltype             = 'River'
    new_system.blcoefs            = {}
    new_system.blcoefs['vx']      = 1.
    new_system.blcoefs['n']       = 0.02
    new_system.blcoefs['hriver']  = 5.
    new_system.blcoefs['rh']      = 5.
    new_system.blcoefs['nu']      = 1e-6

    new_system.blcoefs['rhoair']  = 1.
    new_system.blcoefs['rhowater']= 1000.
    new_system.blcoefs['vwind']   = 5.
    new_system.blcoefs['hlake']   = 10.
    new_system.blcoefs['llake']   = 1000.

#======================================================================================================================
    reaction_check = 0
    for layer in (system.deplayer + system.layers):
        if layer.decay == layer.decays[1]: reaction_check = 1

    if reaction_check == 1:
        new_system.reactions = [Reaction(1)]
        new_system.reactions[0].name = 'Reaction 1'
        new_system.reactions[0].model = 'Fundamental'
        new_system.reactions[0].equation = str(new_system.chemicals[0].name) + ' decay'
        new_system.reactions[0].reactants = [Reactant(1)]
        new_system.reactions[0].products  = []

        new_system.reactions[0].reactants[0].name    = new_system.chemicals[0].name
        new_system.reactions[0].reactants[0].coef    = 1
        new_system.reactions[0].reactants[0].soluable= 1
        new_system.reactions[0].reactants[0].formula = new_system.chemicals[0].name
        new_system.reactions[0].reactants[0].index   = 1
        new_system.reactions[0].reactants[0].MW      = 1

        new_system.coefficients = {}
        for layer in new_system.layers:
            new_system.coefficients[layer.name] = {}
            new_system.coefficients[layer.name][new_system.reactions[0].name] = Coefficient(layer, new_system.reactions[0])
        if new_system.layers[0].name == 'Deposition':
            for layer in new_system.layers[1:]:
                new_system.coefficients[layer.name][new_system.reactions[0].name].lam = system.layers[new_system.layers.index(layer)-1].lam
        else:
            for layer in new_system.layers:
                new_system.coefficients[layer.name][new_system.reactions[0].name].lam = system.layers[new_system.layers.index(layer)].lam
    else:
        new_system.reactions    = []
        new_system.coefficients = {}
        for layer in new_system.layers:
            new_system.coefficients[layer.name] = {}
#======================================================================================================================    
        
    new_system.topBCtype = 'Mass transfer'
    if system.bottombc == 'constant concentration':  new_system.botBCtype = 'Fixed Concentration'
    else:                                            new_system.botBCtype = 'Flux-matching'
    
    new_system.ICs       = {}
    for layer in new_system.layers:
        new_system.ICs[layer.name] = {}
        new_system.ICs[layer.name][new_system.chemicals[0].name] = IC(layer.name, new_system.chemicals[0].name)
    if new_system.layers[0].name == 'Deposition':
        for layer in new_system.layers[1:]:
            new_system.ICs[layer.name][new_system.chemicals[0].name].uniform = system.layers[new_system.layers.index(layer)-1].C0
    else:
        for layer in new_system.layers:
           new_system.ICs[layer.name][new_system.chemicals[0].name].uniform = system.layers[new_system.layers.index(layer)].C0



    new_system.BCs      = {}
    new_system.BCs[new_system.chemicals[0].name]              = BC(new_system.chemicals[0].name, 1)
    new_system.BCs[new_system.chemicals[0].name].k            = system.kbl
    new_system.BCs[new_system.chemicals[0].name].Cw           = system.Cw
    new_system.BCs[new_system.chemicals[0].name].Cb           = system.Cb
    new_system.BCs[new_system.chemicals[0].name].topBCtype    = new_system.topBCtype
    new_system.BCs[new_system.chemicals[0].name].botBCtype    = new_system.botBCtype
    
#======================================================================================================================    
   
    new_system.cpsmfilename  = system.cpsmfilename
    new_system.csvfileoption = 'None'
    new_system.cpsmfilename  = system.cpsmfilename
    new_system.tfinal       = system.tfinal
    new_system.outputsteps  = 1000
    new_system.discrete     = 'Use defaults'
    new_system.delt         = system.tfinal/1000
    new_system.ptype        = system.ptype
    new_system.timeoption   = 'Implicit'
    new_system.tvariable    = 'User-defined'
    new_system.nonlinear    = 'Newton method'
    new_system.nlerror      = 0.01
    try:
        if system.ptype == 'Uniform size':
            if new_system.layers[0].name == 'Deposition':
                htot = sum([layer.h for layer in new_system.layers[1:]])
                new_system.players = [int(layer.h/(htot/system.ptotal))+1 for layer in new_system.layers[1:]]
                new_system.delz    = [new_system.layers[i].h/new_system.players[i] for i in range(1, new_system.nlayers)]
                new_system.ptotal  = sum(new_system.players)
                new_system.delz.insert(0,new_system.delz[0])
                new_system.players.insert(0, new_system.layers[0].h/new_system.delz[0])
            else:
                htot = sum([layer.h for layer in new_system.layers])
                new_system.players = [int(layer.h/(htot/system.ptotal))+1 for layer in new_system.layers]
                new_system.delz    = [new_system.layers[i].h/new_system.players[i] for i in range(new_system.nlayers)]
                new_system.ptotal  = sum(new_system.players)
        else:
            if new_system.layers[0].name == 'Deposition':
                new_system.ptotal  = system.ptotal
                new_system.players = [int(new_system.ptotal/(new_system.nlayers-1))+1 for layer in new_system.layers[1:]]
                new_system.delz    = [new_system.layers[i].h/new_system.players[i] for i in range(1, new_system.nlayers)]
                new_system.ptotal  = sum(new_system.players)
                new_system.delz.insert(0,    new_system.delz[0])
                new_system.players.insert(0, new_system.layers[0].h/new_system.delz[0])
            else:
                htot = sum([layer.h for layer in new_system.layers])
                new_system.ptotal  = system.ptotal
                new_system.players = [int(new_system.ptotal/(new_system.nlayers-1))+1 for layer in new_system.layers]
                new_system.delz    = [new_system.layers[i].h/new_system.players[i] for i in range(new_system.nlayers)]
                new_system.ptotal  = sum(new_system.players)
    except:
        new_system.players = [10   for layer in new_system.layers]
        new_system.delz    = [0.01 for layer in new_system.layers]
        new_system.ptotal  = sum(new_system.players)

    if system.tidal == 1:   new_system.tidalsteps   = int(new_system.tfinal/new_system.delt)
    else:                   new_system.tidalsteps   = 10

    print(new_system.delz)
    print(new_system.players)
    return new_system

def get_updateddatabase(database):

    new_database = {}

    chemicals_list = database.keys()

    for chemical_name in chemicals_list:
        new_database[chemical_name] = ChemicalDatabase(chemical_name, '', chemicals_list.index(chemical_name)+1, database[chemical_name].MW)
        for temp in database[chemical_name].temp:
            new_database[chemical_name].add_properties(temp, database[chemical_name].Kow[temp], database[chemical_name].density[temp],' ',database[chemical_name].Dw[temp]
                                                       , database[chemical_name].Koc[temp], database[chemical_name].Kdoc[temp], database[chemical_name].Kf[temp], database[chemical_name].N[temp])


    return new_database
