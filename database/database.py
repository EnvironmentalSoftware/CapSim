#!/usr/bin/env python
#
#This file is used to make the GUI for inputing a new chemical into the database
#of compounds for CapSim.

import tkMessageBox as tkmb, cPickle as pickle, sys, os
import tkFileDialog as tkfd

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, StringVar, DoubleVar, IntVar, Tk
from capsim_object_types import CapSimWindow, ChemicalDatabase, ChemicalData
from capsim_functions    import get_superfont
from databaseeditor      import DatabaseEditor, DatabaseDeleter, DatabaseImporter

class Database:
    """Opens a window for inputing the properties of a compound."""

    def __init__(self, master, system, database):
        """The constructor method."""
        
        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.tframe        = Frame(master.tframe)
        self.frame         = Frame(master.frame)
        self.bframe        = Frame(master.bframe)
        self.top           = None

        self.system        = system
        self.database      = database    #the chemical database
        
        self.chemicals_list = self.database.keys()
        self.chemicals_list.sort()
        
        self.chemicaldatas = {}
        
        for name in self.chemicals_list:
            self.chemicaldatas[name] = ChemicalData(name)
            self.chemicaldatas[name].read_database(self.database[name])
            
    def make_widgets(self):

        self.insruction   = Label(self.tframe, text ='Please provide the following fundamental properties for the chemicals:\n')

        self.blankcolumn  = Label(self.tframe,  text =' ', width = 1)
        self.editcolumn   = Label(self.tframe,  text =' ', width = 6)
        self.delcolumn    = Label(self.tframe,  text =' ', width = 6)
        self.namecolumn   = Label(self.tframe,  text =' ', width = 18)
        self.formcolumn   = Label(self.tframe,  text =' ', width = 10)
        self.tempcolumn   = Label(self.tframe,  text =' ', width = 10)
        self.Dwcolumn     = Label(self.tframe,  text =' ', width = 18)
        self.Koccolumn    = Label(self.tframe,  text =' ', width = 18)
        self.Kdoccolumn   = Label(self.tframe,  text =' ', width = 18)
        self.Refcolumn    = Label(self.tframe,  text =' ', width = 18)
        self.endcolumn    = Label(self.tframe,  text =' ', width = 2)

        self.namelabel    = Label(self.tframe,  text = 'Chemical name')
        self.formlabel    = Label(self.tframe,  text = 'Formula')
        self.templabel    = Label(self.tframe,  text = 'Temperature')
        self.Dwlabel      = Label(self.tframe,  text = 'Molecular diffusivity\n in water')
        self.Koclabel     = Label(self.tframe,  text = 'Organic carbon\n partition coefficient')
        self.Kdoclabel    = Label(self.tframe,  text = 'Dissolved organic carbon\n partition coefficient')
        self.Reflabel     = Label(self.tframe,  text = 'Reference')

        self.tempunits    = Label(self.tframe,  text = unichr(176) + 'C')
        self.Dwunits      = Label(self.tframe,  text = u'cm\u00B2/s')
        self.Kocunits     = Label(self.tframe,  text = 'log(L/kg)')
        self.Kdocunits    = Label(self.tframe,  text = 'log(L/kg)')
        
        self.addwidget    = Button(self.bframe, text = 'Add new chemicals',      command = self.addchemicaldata,   width = 20)
        self.tempwidget   = Button(self.bframe, text = 'Add new temperatures',   command = self.addtempdata,       width = 20)
        self.importwidget = Button(self.bframe, text = 'Import database file',   command = self.importchemicaldata,width = 20)
        self.savebutton   = Button(self.bframe, text = 'Save',                   command = self.OK,                width = 20)
        self.cancelbutton = Button(self.bframe, text = 'Cancel',                 command = self.cancel,            width = 20)

        self.botblankcolumn  = Label(self.frame,  text =' ', width = 1)
        self.boteditcolumn   = Label(self.frame,  text =' ', width = 6)
        self.botdelcolumn    = Label(self.frame,  text =' ', width = 6)
        self.botnamecolumn   = Label(self.frame,  text =' ', width = 18)
        self.botformcolumn   = Label(self.frame,  text =' ', width = 10)
        self.bottempcolumn   = Label(self.frame,  text =' ', width = 10)
        self.botDwcolumn     = Label(self.frame,  text =' ', width = 18)
        self.botKoccolumn    = Label(self.frame,  text =' ', width = 18)
        self.botKdoccolumn   = Label(self.frame,  text =' ', width = 18)
        self.botRefcolumn    = Label(self.frame,  text =' ', width = 18)
        self.botendcolumn    = Label(self.frame,  text =' ', width = 2)

        self.blank1       = Label(self.bframe, text = ' ')
        self.blank2       = Label(self.bframe, text = ' ')
        self.blank3       = Label(self.bframe, text = ' ')

        self.insruction.grid(   row    = 0, column = 0, sticky = 'W', padx = 1, pady = 1, columnspan = 11)
       
        self.blankcolumn.grid(  row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.editcolumn.grid(   row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(    row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(   row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.formcolumn.grid(   row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.tempcolumn.grid(   row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Dwcolumn.grid(     row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Koccolumn.grid(    row    = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoccolumn.grid(   row    = 1, column = 8, sticky = 'WE', padx = 1, pady = 1)
        self.Refcolumn.grid(    row    = 1, column = 9, sticky = 'WE', padx = 1, pady = 1)
        self.endcolumn.grid(    row    = 1, column = 10, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.formlabel.grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.templabel.grid(    row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Dwlabel  .grid(    row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Koclabel .grid(    row    = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoclabel.grid(    row    = 2, column = 8, sticky = 'WE', padx = 1, pady = 1)
        self.Reflabel.grid(     row    = 2, column = 9, sticky = 'WE', padx = 1, pady = 1)

        self.tempunits.grid(    row    = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Dwunits.grid  (    row    = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Kocunits.grid (    row    = 3, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.Kdocunits.grid(    row    = 3, column = 8, sticky = 'WE', padx = 1, pady = 1)


        #Bind the "return key" to the buttons

        self.updatechemicals()
        
    def updatechemicals(self, event = None):
            
        self.addwidget.grid_forget()
        self.tempwidget.grid_forget()
        self.savebutton.grid_forget()
        self.cancelbutton.grid_forget()
        self.blank1.grid_forget()
        self.blank2.grid_forget()

        self.chemicals_list = self.chemicaldatas.keys()
        self.chemicals_list.sort()
        row = 4

        namelabellength = 18
        formlabellength = 10
        Reflabellength  = 18

        for name in self.chemicals_list:
            try: self.chemicaldatas[name].remove_chemicalwidgets()
            except:pass
            self.chemicaldatas[name].chemicalwidgets(self.frame, row, self.master)
            row = row + 1

            if namelabellength < self.chemicaldatas[name].namelabel.winfo_reqwidth()/8:  namelabellength = int(self.chemicaldatas[name].namelabel.winfo_reqwidth()/8) + 1
            if formlabellength < self.chemicaldatas[name].formlabel.winfo_reqwidth()/8:  formlabellength = int(self.chemicaldatas[name].formlabel.winfo_reqwidth()/8) + 1
            if Reflabellength  < self.chemicaldatas[name].Reflabel.winfo_reqwidth()/8:   Reflabellength  = int(self.chemicaldatas[name].Reflabel.winfo_reqwidth()/8) + 1

        self.namecolumn.config(width = namelabellength)
        self.formcolumn.config(width = formlabellength)
        self.Refcolumn.config( width = Reflabellength)

        self.botnamecolumn.config(width = namelabellength)
        self.botformcolumn.config(width = formlabellength)
        self.botRefcolumn.config( width = Reflabellength)

        self.botblankcolumn.grid(  row    = row, column = 0,  sticky = 'WE', padx = 1, pady = 1)
        self.boteditcolumn.grid(   row    = row, column = 1,  sticky = 'WE', padx = 1, pady = 1)
        self.botdelcolumn.grid(    row    = row, column = 2,  sticky = 'WE', padx = 1, pady = 1)
        self.botnamecolumn.grid(   row    = row, column = 3,  sticky = 'WE', padx = 1, pady = 1)
        self.botformcolumn.grid(   row    = row, column = 4,  sticky = 'WE', padx = 1, pady = 1)
        self.bottempcolumn.grid(   row    = row, column = 5,  sticky = 'WE', padx = 1, pady = 1)
        self.botDwcolumn.grid(     row    = row, column = 6,  sticky = 'WE', padx = 1, pady = 1)
        self.botKoccolumn.grid(    row    = row, column = 7,  sticky = 'WE', padx = 1, pady = 1)
        self.botKdoccolumn.grid(   row    = row, column = 8,  sticky = 'WE', padx = 1, pady = 1)
        self.botRefcolumn.grid(    row    = row, column = 9,  sticky = 'WE', padx = 1, pady = 1)
        self.botendcolumn.grid(    row    = row, column = 10, sticky = 'WE', padx = 1, pady = 1)

        self.blank2.grid(row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.tempwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.importwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.savebutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.blank3.grid(row = row)
        row = row + 1

        self.savebutton.bind(   '<Return>',   self.OK)
        self.cancelbutton.bind( '<Return>',   self.cancel)

        self.focusbutton = self.cancelbutton
        self.master.geometry()
        self.master.center()

    def addchemicaldata(self, event = None):

        new_name = 'chemical' + str(len(self.chemicals_list))
        
        self.chemicaldatas[new_name] = ChemicalData(new_name)

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(DatabaseEditor(self.top, self.system, self.chemicaldatas[new_name], self.chemicaldatas, editflag = 0, tempflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.chemicaldatas[new_name].get_chemicaldata(self.top.window)
                self.chemicaldatas[self.chemicaldatas[new_name].name] = self.chemicaldatas[new_name].copy()
                
            del self.chemicaldatas[new_name]
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatechemicals()

    def importchemicaldata(self):

        UserPath = os.environ['USERPROFILE']
        Filepath = tkfd.askopenfilename(initialdir = UserPath)

        if Filepath != '':
            data = open(Filepath, 'r')
            database_imported = pickle.load(data)
            data.close()
            if self.top is None:
                self.top = CapSimWindow(master = self.master, buttons = 2)
                self.top.make_window(DatabaseImporter(self.top, self.system, database_imported))
                self.top.tk.mainloop()

                duplicate_name = []
                duplicate_temp = []

                if self.top.window.cancelflag == 0:
                    error_check = 0
                    for name in self.top.window.chemicals_list:
                        if self.top.window.importedchemicals[name].check == 1:
                            if self.chemicals_list.count(self.top.window.importedchemicals[name].name_new) == 0:
                                self.chemicals_list.append(self.top.window.importedchemicals[name].name_new)
                                self.chemicaldatas[self.top.window.importedchemicals[name].name_new] = ChemicalData(self.top.window.importedchemicals[name].name_new)
                                self.chemicaldatas[self.top.window.importedchemicals[name].name_new].read_database(self.top.window.importedchemicals[name])
                            else:
                                for temp in self.top.window.importedchemicals[name].temps:
                                    if self.chemicaldatas[self.top.window.importedchemicals[name].name_new].temps.count(temp) == 0:
                                        self.chemicaldatas[self.top.window.importedchemicals[name].name_new].read_temperature(self.top.window.importedchemicals[name], temp)
                                    else:
                                        duplicate_name.append(self.top.window.importedchemicals[name].name_new)
                                        duplicate_temp.append(temp)
                                        error_check = 1
                    error_message = 'The following compound information are duplicated:\n\n'
                    for na in range(len(duplicate_name)):
                        error_message = error_message + '              ' + str(duplicate_name[na]) + ' @ ' + str(duplicate_temp[na]) + 'C \n'

                    if error_check == 1: tkmb.showerror(title = self.system.version, message = error_message)

                if self.top is not None:
                    self.top.destroy()
                    self.top = None

            elif self.top is not None:
                tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
                self.top.tk.focus()

        self.updatechemicals()


    def addtempdata(self, event = None):

        name = self.chemicals_list[0]
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(DatabaseEditor(self.top, self.system, self.chemicaldatas[name], self.chemicaldatas, editflag = 0, tempflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.chemicaldatas[self.top.window.name.get()].get_chemicaldata(self.top.window)

            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatechemicals()

    def editchemicaldata(self, name):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(DatabaseEditor(self.top, self.system, self.chemicaldatas[name], self.chemicaldatas, editflag = 1, tempflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.chemicaldatas[name].get_chemicaldata(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
            
        self.updatechemicals()
        
    def deletechemicaldata(self, name):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(DatabaseDeleter(self.top, self.system, self.chemicaldatas[name]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.chemicaldatas[name].get_chemicaldata(self.top.window)
            if self.top.window.cancelflag == 2:
                self.chemicaldatas[name].remove_chemicalwidgets()
                del self.chemicaldatas[name]
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        self.updatechemicals()

    def cancel(self, event = None): 

        self.exitflag = 1
        self.frame.quit()

    def OK(self, event = None):
        """Finish and move on."""

        self.database = {}
        for name in self.chemicals_list:
            chemicaldata = self.chemicaldatas[name]
            index        = self.chemicals_list.index(name)
            self.database[name] = ChemicalDatabase(chemicaldata.name, chemicaldata.formula, index + 1, chemicaldata.MW)
            for temp in chemicaldata.temps:
                Dw      = chemicaldata.Dw[temp]
                Kow     = chemicaldata.Kow[temp]
                density = chemicaldata.density[temp]
                Ref     = chemicaldata.Ref[temp]
                Koc     = chemicaldata.Koc[temp]
                Kdoc    = chemicaldata.Kdoc[temp]
                Kf      = chemicaldata.Kf[temp]
                N       = chemicaldata.N[temp]

                self.database[name].add_properties(temp, Kow, density, Ref, Dw, Koc, Kdoc, Kf, N)

        self.exitflag = 1
        self.frame.quit()

def edit_database(chemicaldatabase, system):
    """Makes the GUI that is used to edit the chemical database."""

    root = CapSimWindow(master = None, buttons = None)
    root.make_window(Database(root, system, chemicaldatabase))
    root.mainloop()
        
    chemicaldatabase = root.window.database
    flag = root.window.exitflag
    root.destroy()
    
    return chemicaldatabase, flag

def make_database(path):
    chemicaldatabase = {}
    chemicaldatabase['phenanthrene']=ChemicalDatabase('phenanthrene', u'C\u2081\u2084H\u2089NO\u2082', 1, 178.)
    chemicaldatabase['phenanthrene'].add_properties(0., 4.57, 1.06, 'CapSim',3.33e-6, 4.22, 3.48, 0., 1.)

    pickle.dump(chemicaldatabase, open(path + r'/database/capsim3_chemicaldatabase', 'w'))
    
    return open(path + r'/database/capsim3_chemicaldatabase', 'r')
