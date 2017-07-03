#!/usr/bin/env python
#
#This file is used to make the GUI for inputing a new chemical into the database
#of compounds for CapSim.

import tkMessageBox as tkmb, cPickle as pickle, sys, os
import tkFileDialog as tkfd

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Tk, Text, StringVar, DoubleVar, IntVar
from capsim_object_types import CapSimWindow, SolidDatabase, Solid
from capsim_functions    import get_superfont
from soliddatabaseeditor import SolidDatabaseEditor, SolidDatabaseDeleter, SolidDatabaseImporter

class Database:
    """Opens a window for inputing the properties of a compound."""

    def __init__(self, master, system, database):
        """The constructor method."""

        self.system        = system
        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.tframe        = Frame(master.tframe)
        self.frame         = Frame(master.frame)
        self.bframe        = Frame(master.bframe)
        self.top           = None

        self.database      = database    #the database of values
                
        self.exitflag      = 0
        self.names         = []          #a list of the chemical names

        solids_list = self.database.keys()
        solids_list.sort()

        self.solids_list = solids_list
        
        self.solids = []
        for solidname in solids_list:
            self.solids.append(Solid(solids_list.index(solidname)))
            self.solids[-1].read_database(self.database[solidname])

    def make_widgets(self):

        self.instructions = Label(self.tframe,  text ='Please provide the following fundamental properties for the material:\n')
        
        self.blankcolumn  = Label(self.tframe,  text ='', font = 'courier 10', width = 1)
        self.editcolumn   = Label(self.tframe,  text ='', font = 'courier 10', width = 6)
        self.delcolumn    = Label(self.tframe,  text ='', font = 'courier 10', width = 6)
        self.numbercolumn = Label(self.tframe,  text ='', font = 'courier 10', width = 8)
        self.namecolumn   = Label(self.tframe,  text ='', font = 'courier 10', width = 18)
        self.ecolumn      = Label(self.tframe,  text ='', font = 'courier 10', width = 8)
        self.rhocolumn    = Label(self.tframe,  text ='', font = 'courier 10', width = 12)
        self.foccolumn    = Label(self.tframe,  text ='', font = 'courier 10', width = 20)
        self.tortcolumn   = Label(self.tframe,  text ='', font = 'courier 10', width = 18)
        self.sorpcolumn   = Label(self.tframe,  text ='', font = 'courier 10', width = 18)
        self.refcolumn    = Label(self.tframe,  text ='', font = 'courier 10', width = 15)

        self.numberlabel  = Label(self.tframe,  text = 'Number')
        self.namelabel    = Label(self.tframe,  text = 'Material')
        self.elabel       = Label(self.tframe,  text = 'Porosity')
        self.rholabel     = Label(self.tframe,  text = 'Bulk density')
        self.foclabel     = Label(self.tframe,  text = 'Organic carbon fraction')
        self.tortlabel    = Label(self.tframe,  text = 'Tortuosity correction')
        self.sorplabel    = Label(self.tframe,  text = 'Sorption isotherms')
        self.reflabel     = Label(self.tframe,  text = 'Reference')

        self.rhounitlabel = Label(self.tframe,  text = u'g/cm\u00B3')

        self.botblankcolumn  = Label(self.frame,  text ='', font = 'courier 10', width = 1)
        self.boteditcolumn   = Label(self.frame,  text ='', font = 'courier 10', width = 6)
        self.botdelcolumn    = Label(self.frame,  text ='', font = 'courier 10', width = 6)
        self.botnumbercolumn = Label(self.frame,  text ='', font = 'courier 10', width = 8)
        self.botnamecolumn   = Label(self.frame,  text ='', font = 'courier 10', width = 18)
        self.botecolumn      = Label(self.frame,  text ='', font = 'courier 10', width = 8)
        self.botrhocolumn    = Label(self.frame,  text ='', font = 'courier 10', width = 12)
        self.botfoccolumn    = Label(self.frame,  text ='', font = 'courier 10', width = 20)
        self.bottortcolumn   = Label(self.frame,  text ='', font = 'courier 10', width = 18)
        self.botsorpcolumn   = Label(self.frame,  text ='', font = 'courier 10', width = 18)
        self.botrefcolumn    = Label(self.frame,  text ='', font = 'courier 10', width = 15)

        self.addwidget    = Button(self.bframe, text = 'Add solids', command = self.addsolid, width = 20)
        self.savebutton   = Button(self.bframe, text = 'Save', width = 20, command = self.save)
        self.importwidget = Button(self.bframe, text = 'Import database file',   command = self.importsoliddata,width = 20)
        self.cancelbutton = Button(self.bframe, text = 'Cancel', command = self.cancel, width = 20)

        self.blank1 = Label(self.bframe, text = ' ')
        self.blank2 = Label(self.bframe, text = ' ')
        self.blank3 = Label(self.bframe, text = ' ')
        
        #show the widgets on the grid (top to bottom and left to right)

        self.instructions.grid(row = 0, column = 0, columnspan = 11, padx = 8, sticky = 'W', pady = 10)

        self.blankcolumn.grid(  row = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.editcolumn.grid(   row = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(    row = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.numbercolumn.grid( row = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(   row = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.ecolumn.grid(      row = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.rhocolumn.grid(    row = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.foccolumn.grid(    row = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.tortcolumn.grid(   row = 1, column = 8, sticky = 'WE', padx = 1, pady = 1)
        self.sorpcolumn.grid(   row = 1, column = 9, sticky = 'WE', padx = 1, pady = 1)
        self.refcolumn.grid(    row = 1, column = 10, sticky = 'WE', padx = 1, pady = 1)

        self.numberlabel.grid(  row = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.namelabel.grid(    row = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.elabel.grid(       row = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.rholabel.grid(     row = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel.grid(     row = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.tortlabel.grid(    row = 2, column = 8, sticky = 'WE', padx = 1, pady = 1)
        self.sorplabel.grid(    row = 2, column = 9, sticky = 'WE', padx = 1, pady = 1)
        self.reflabel.grid(     row = 2, column = 10, sticky = 'WE', padx = 1, pady = 1)

        self.rhounitlabel.grid(    row = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)


        self.updatesolids()

        #Bind the "return key" to the buttons


        self.focusbutton = self.cancelbutton

    def updatesolids(self):

        self.addwidget.grid_forget()
        self.blank1.grid_forget()
        self.blank2.grid_forget()

        self.botblankcolumn.grid_forget()
        self.boteditcolumn.grid_forget()
        self.botdelcolumn.grid_forget()
        self.botnumbercolumn.grid_forget()
        self.botnamecolumn.grid_forget()
        self.botecolumn.grid_forget()
        self.botrhocolumn.grid_forget()
        self.botfoccolumn.grid_forget()
        self.bottortcolumn.grid_forget()
        self.botsorpcolumn.grid_forget()
        self.botrefcolumn.grid_forget()

        namelabellength = 18
        reflabellength  = 15


        row = 4
        for solid in self.solids:
            try: solid.remove_propertieswidget()
            except:pass
            solid.number = self.solids.index(solid) + 1
            solid.propertieswidget(self.frame, row, self.master)
            row = row + 1

            if namelabellength < solid.namelabel.winfo_reqwidth()/8:  namelabellength = int(solid.namelabel.winfo_reqwidth()/8) + 1
            if reflabellength < solid.reflabel.winfo_reqwidth()/8:    reflabellength = int(solid.reflabel.winfo_reqwidth()/8) + 1


        self.namecolumn.config(     width = namelabellength)
        self.botnamecolumn.config(  width = namelabellength)
        self.refcolumn.config(      width = reflabellength)
        self.botrefcolumn.config(   width = reflabellength)

        self.botblankcolumn.grid(  row = row, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.boteditcolumn.grid(   row = row, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.botdelcolumn.grid(    row = row, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.botnumbercolumn.grid( row = row, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.botnamecolumn.grid(   row = row, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.botecolumn.grid(      row = row, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.botrhocolumn.grid(    row = row, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.botfoccolumn.grid(    row = row, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.bottortcolumn.grid(   row = row, column = 8, sticky = 'WE', padx = 1, pady = 1)
        self.botsorpcolumn.grid(   row = row, column = 9, sticky = 'WE', padx = 1, pady = 1)
        self.botrefcolumn.grid(    row = row, column = 10, sticky = 'WE', padx = 1, pady = 1)
        row = row + 1

        row = 0
        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.importwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.savebutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.blank3.grid(row = row)

        self.savebutton.bind('<Return>', self.save)
        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.savebutton
        self.master.geometry()
        
    def addsolid(self):

        self.solids.append(Solid(self.solids[-1].number + 1))

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(SolidDatabaseEditor(self.top, self.system, self.solids[-1], self.solids, editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.solids[-1].get_solid(self.top.window)
            else:
                self.solids.remove(self.solids[-1])
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatesolids()
        
    def editsolid(self, number):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(SolidDatabaseEditor(self.top, self.system, self.solids[number-1], self.solids, editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.solids[number-1].get_solid(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatesolids()

    def importsoliddata(self):


        UserPath = os.environ['USERPROFILE']
        Filepath = tkfd.askopenfilename(initialdir = UserPath)

        if Filepath != '':
            data = open(Filepath, 'r')
            database_imported = pickle.load(data)
            data.close()
            if self.top is None:
                self.top = CapSimWindow(master = self.master, buttons = 2)
                self.top.make_window(SolidDatabaseImporter(self.top, self.system, database_imported))
                self.top.tk.mainloop()

                duplicate_name = []

                if self.top.window.cancelflag == 0:
                    error_check = 0
                    for solid in self.top.window.solids:
                        if solid.check == 1:
                            if self.solids_list.count(solid.name_new) == 0:
                                self.solids_list.append(solid.name_new)
                                self.solids.append(Solid(self.solids_list.index(solid.name_new)))
                                self.solids[-1].import_coefficients(solid)
                            else:
                                duplicate_name.append(solid.name_new)
                                error_check = 1

                    error_message = 'The following compound information are duplicated:\n\n'
                    for na in range(len(duplicate_name)):
                        error_message = error_message + '              ' + str(duplicate_name[na]) + ' \n'

                    if error_check == 1: tkmb.showerror(title = self.system.version, message = error_message)

                if self.top is not None:
                    self.top.destroy()
                    self.top = None

            elif self.top is not None:
                tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
                self.top.tk.focus()

        self.updatesolids()

    def deletesolid(self, number):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(SolidDatabaseDeleter(self.top, self.system, self.solids[number-1]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.solids[number-1].remove_propertieswidget()
                self.solids.remove(self.solids[number-1])
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatesolids()

    def save(self, event = None):
        
        self.database = self.write_database()
        
        self.exitflag = 1
        self.frame.quit()

    def cancel(self, event = None): 

        self.exitflag = 1
        self.frame.quit()

    def exit(self, event = None):
        """Exit CapSim."""

        if tkmb.askyesno(self.version, 'Do you really want to exit CapSim?') == 1: sys.exit()

    def write_database(self):

        soliddatabase = {}
        for solid in self.solids:
            soliddatabase[solid.name] = SolidDatabase(solid.name, solid.number, solid.e, solid.rho, solid.foc, solid.tort, solid.sorp, solid.Ref)

        return soliddatabase
            
def edit_soliddatabase(soliddatabase, system):
    """Makes the GUI that is used to edit the chemical database."""

    root = CapSimWindow(master = None, buttons = None)
    root.make_window(Database(root, system, soliddatabase))
    root.mainloop()
        
    database = root.window.database
    flag = root.window.exitflag
    root.destroy()
    return database, flag

def make_soliddatabase(path):
    
    soliddatabase = {}
    soliddatabase['Activated Carbon'] =SolidDatabase('Activated Carbon', 1, 0.6, 0.4, 1.00, 'Millington & Quirk', 'Freundlich'          , 'CapSim')
    soliddatabase['Biochar']          =SolidDatabase('Biochar',          2, 0.4, 0.5, 1.00, 'Millington & Quirk', 'Linear--Kocfoc'      , 'CapSim')
    soliddatabase['Organoclay']       =SolidDatabase('Organoclay',       3, 0.5, 1.0, 0.20, 'Millington & Quirk', 'Linear--Kd specified', 'CapSim')
    soliddatabase['Sand']             =SolidDatabase('Sand',             4, 0.5, 1.25,0.001,'Millington & Quirk', 'Linear--Kd specified', 'CapSim')
    soliddatabase['Sediment']         =SolidDatabase('Sediment',         5, 0.5, 1.25,0.01, 'Boudreau',           'Linear--Kocfoc'      , 'CapSim')

    pickle.dump(soliddatabase, open(path + r'/database/capsim_soliddatabase', 'w'))
    
    return open(path + r'/database/capsim_soliddatabase', 'r')
