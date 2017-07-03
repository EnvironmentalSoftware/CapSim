#!/usr/bin/env python
#
#This file contains the "CapSimWindow", "Chemical," "System" and "Layer" classes
#that are used to build the sediment capping system that is fed to the capsim 
#solver.  

import tkMessageBox as tkmb, cPickle as pickle, sys, os, warnings
import _winreg as wreg

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
    warnings.filterwarnings('ignore')
else: path = sys.path[0]

CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)
CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
Filepath =wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
CapSimKey.Close()

from capsim_functions import freundlich, langmuir, millquirk, boudreau, notort, round_to_n
from Tkinter          import Tk, Toplevel, Canvas, Frame, Label, Entry, Text, \
                             Button, Scrollbar, OptionMenu, StringVar, \
                             DoubleVar, IntVar, FLAT, RAISED, Checkbutton
import tkFont

class AutoScrollbar(Scrollbar):
    """A scrollbar that hides itself if it's not needed (borrowed from
    Fredrik Lundh)."""

    def set(self, lo, hi):
        if float(lo) <= 0 and float(hi) >= 1:
            self.grid_remove()
            self.exist = 0
        else:
            self.grid()
            self.exist = 1
        Scrollbar.set(self, lo, hi)

class CapSimWindow:
    """Makes a CapSim window that looks good and has all the properties it 
    needs."""

    def __init__(self, master = None, buttons = None, left_frame = None):
        """Constructor method.  Makes a Tk root window with horizontal and 
        vertical scrollbars that appear if desired and sets whether it is root
        or a toplevel window.  The "buttons" keyword can be used to make the 
        "OK," "Mainmenu," and "Exit" buttons."""

        self.master  = master
        self.buttons = buttons
        self.left_frame = left_frame

        if master is None: self.tk = Tk()
        else:              self.tk = Toplevel(master.tk)

        self.main       = IntVar(value = 0)
        self.step       = IntVar(value = 0)
        self.vscrollbar = AutoScrollbar(self.tk)
        self.hscrollbar = AutoScrollbar(self.tk, orient = 'horizontal')
        self.canvas     = Canvas(self.tk, highlightthickness = 0)
        self.canvas.config(xscrollcommand = self.hscrollbar.set, yscrollcommand = self.vscrollbar.set)

        self.tframe     = Frame(self.tk)
        self.frame      = Frame(self.canvas)
        self.bframe     = Frame(self.tk)
        self.lframe     = Frame(self.tk)

        self.vscrollbar.config(command = self.canvas.yview)
        self.hscrollbar.config(command = self.canvas.xview)
        self.tk.grid_rowconfigure(   1,  weight = 1)
        self.tk.grid_columnconfigure(0,  weight = 1)

        self.frame.rowconfigure(1, weight=1)
        self.frame.columnconfigure(1, weight=1)

        if left_frame == None:
            self.tframe.grid(row     = 0, column = 0, sticky = 'NWE', columnspan = 2)
            self.bframe.grid(row     = 3, column = 0, sticky = 'N',   columnspan = 2)
            self.canvas.grid(row     = 1, column = 0, sticky = 'NSWE')
            self.vscrollbar.grid(row = 1, column = 1, sticky = 'NS')
            self.hscrollbar.grid(row = 2, column = 0, sticky = 'WE')
        else:
            self.tframe.grid(row     = 0, column = 0, sticky = 'NWE', columnspan = 3)
            self.bframe.grid(row     = 3, column = 0, sticky = 'N',   columnspan = 3)
            self.lframe.grid(row     = 1, column = 0, sticky = 'W')
            self.canvas.grid(row     = 1, column = 1, sticky = 'NSWE')
            self.vscrollbar.grid(row = 1, column = 2, sticky = 'NS')
            self.hscrollbar.grid(row = 2, column = 1, sticky = 'WE')

    def make_window(self, window):
        """Creates a frame to put the widgets from "window" into later, adds 
        the appropriate method to the "x" in the window, puts the correct title
        and icon, places the widgets from "window" into the frame, centers the
        window, and places the focus on the window and the "OK" button."""

        self.window = window
        self.tk.option_add('*font', self.window.fonttype)
        self.tk.title('CapSim ' + self.window.version)
        try: self.tk.iconbitmap(path + r'/capsimicon.ico')
        except: pass

        self.frame.grid(sticky = 'NSWE', row = 0, column = 0)
        self.window.tframe.grid(sticky = 'N', row = 0, column = 0)
        self.window.frame.grid( sticky = 'NSWE', row = 0, column = 0)
        self.window.bframe.grid(sticky = 'N', row = 0, column = 0)

        try: self.window.lframe.grid(sticky = 'E', row = 0, column = 0)
        except: pass

        if self.master is None: self.tk.protocol('WM_DELETE_WINDOW', self.exit)
        else: self.tk.protocol('WM_DELETE_WINDOW', self.closetop)

        if self.buttons is not None: self.make_buttonframe()
        self.window.make_widgets()

        self.tk.update()

        if self.tframe.bbox('all')[2] > (self.frame.bbox('all')[2] + 16 * self.vscrollbar.exist):
            self.canvas.create_window((self.tframe.bbox('all')[2]-self.frame.bbox('all')[2] - 16 * self.vscrollbar.exist)/2, 0, anchor = 'nw', window = self.frame)
        elif self.bframe.bbox('all')[2] > (self.frame.bbox('all')[2] + 16 * self.vscrollbar.exist):
            self.canvas.create_window((self.bframe.bbox('all')[2]-self.frame.bbox('all')[2] - 16 * self.vscrollbar.exist)/2, 0, anchor = 'nw', window = self.frame)
        else:
            self.canvas.create_window(0, 0, anchor = 'nw', window = self.frame)

        self.geometry()
        self.center()

    def geometry(self):
        """Makes the window the right size for the frame."""

        self.tk.update()
        if self.left_frame == None:
            self.tk.geometry('%dx%d' % (max(self.tframe.bbox('all')[2], self.frame.bbox('all')[2], self.bframe.bbox('all')[2]),
                                        min(self.tframe.bbox('all')[3] + self.frame.bbox('all')[3] + self.bframe.bbox('all')[3], self.tk.winfo_screenheight()*3/4) ))
        else:
            self.tk.geometry('%dx%d' % (max(self.tframe.bbox('all')[2], self.frame.bbox('all')[2], self.bframe.bbox('all')[2])+self.lframe.bbox('all')[2],
                                        min(self.tframe.bbox('all')[3] + self.frame.bbox('all')[3] + self.bframe.bbox('all')[3], self.tk.winfo_screenheight()*3/4) ))
        self.tk.update()
        self.focus()

    def center(self):
        """Moves the window into the center of the screen."""

        ws = self.tk.winfo_screenwidth()
        hs = self.tk.winfo_screenheight()
        w  = self.tk.winfo_width()
        h  = self.tk.winfo_height()

        if ws > w:
            if hs > h:  self.tk.geometry('%dx%d+%d+%d' % (w, h, ws / 2. - w / 2., hs / 2. - h / 2))
            else:       self.tk.geometry('%dx%d+%d+%d' % (w, h, ws / 2. - w / 2., hs))
        elif hs > h:    self.tk.geometry('%dx%d+%d+%d' % (w, h, ws, hs / 2. - h / 2.))
        else:           self.tk.geometry('%dx%d+%d+%d' % (w, h, ws, hs))
                
        self.tk.update_idletasks()
        self.tk.focus_force()
        self.canvas.config(scrollregion = (self.frame.bbox('all')[0],self.frame.bbox('all')[1],self.frame.bbox('all')[2]-17, self.frame.bbox('all')[3]-17))

        self.focus()

    def make_buttonframe(self):
        """Creates a frame to put the mainmenu, ok, and exit buttons on."""

        self.buttonframe = Frame(self.bframe)
        self.okbutton    = Button(self.buttonframe, text = 'OK',                    width = 20, command = self.OK)
        self.nextbutton  = Button(self.buttonframe, text = 'Next',                  width = 20, command = self.Next)
        self.backbutton  = Button(self.buttonframe, text = 'Back',                  width = 20, command = self.Back)
        self.mainbutton  = Button(self.buttonframe, text = 'Return to Main Menu',   width = 20, command = self.mainmenu)
        self.exitbutton  = Button(self.buttonframe, text = 'Exit CapSim',           width = 20, command = self.exit)
        self.blank       = Label(self.buttonframe,  text = '')

        if self.master is None and self.buttons == 1:  # The window with
            self.nextbutton.grid(row = 0, pady = 1)
            self.backbutton.grid(row = 1)
            self.mainbutton.grid(row = 2, pady = 1)
            self.exitbutton.grid(row = 3)
            self.blank.grid(     row = 4)
        elif self.master is None and self.buttons == 2:
            self.mainbutton.grid(row = 0, pady = 1, sticky = 'N')
            self.exitbutton.grid(row = 1, sticky = 'N')
            self.blank.grid(     row = 2, sticky = 'N')
        elif self.master is None and self.buttons == 3:
            self.okbutton.grid(  row = 0)
            self.mainbutton.grid(row = 1, pady = 1, sticky = 'N')
            self.exitbutton.grid(row = 2, sticky = 'N')
            self.blank.grid(row = 3, sticky = 'N')
        elif self.buttons == 2:
            self.blank.grid(row = 1)
        else:
            self.okbutton.grid(row = 0)
            self.blank.grid(row = 1)

        #bind the Return key to the buttons
        self.nextbutton.bind('<Return>', self.Next)
        self.backbutton.bind('<Return>', self.Back)
        self.okbutton.bind('<Return>',   self.OK)
        self.mainbutton.bind('<Return>', self.mainmenu)
        self.exitbutton.bind('<Return>', self.exit)

        self.buttonframe.grid(row = 1, sticky = 'NS')

    def mainloop(self): 
        """Points to the correct mainloop method."""
        
        self.tk.mainloop()

    def destroy(self):  
        """Points to the correct destroy method."""

        self.tk.destroy()

    def mainmenu(self, event = None):
        """Return to the main menu."""
        
        if self.window.top is not None: self.open_toplevel()
        else:
            self.main.set(1)
            self.tk.quit()

    def OK(self, event = None):
        """Finish and move on."""
        try:    error = self.window.error_check()
        except: error = 0

        if self.window.top is not None: self.open_toplevel()
        elif error == 1:                self.window.warning()
        else:                           self.tk.quit()

    def Next(self, event = None):
        """Finish and move on."""

        try:    error = self.window.error_check()
        except: error = 0

        if self.window.top is not None: self.open_toplevel()
        elif error == 1: self.window.warning()
        else:
            self.step.set(1)
            self.tk.quit()

    def Back(self, event = None):
        """Finish and move on."""

        if self.window.top is not None: self.open_toplevel()
        else:
            self.step.set(-1)
            self.tk.quit()


    def exit(self, event = None):
        """Exit CapSim."""

        if tkmb.askyesno(self.window.version, 'Do you really want to exit CapSim?') == 1: sys.exit()
        if self.window.top is not None: self.window.top.okbutton.focus()

    def open_toplevel(self):
        """Forces the user to close any existing toplevel widgets before doing
        anything else."""

        tkmb.showerror(title = self.window.system.version, message = 'Please ' +
                       'close the existing parameter input window first.')
        self.window.top.tk.focus()

    def closetop(self):
        """Sets the toplevel widget to None if it is destoyed."""

        self.tk.quit()
        self.tk.destroy()
        self.master.window.top = None

    def focus(self, event = None):
        """Puts the focus on the "OK" button after clicking the OptionMenu."""

        if self.window.focusbutton is None:
            if self.master is None:
                if self.buttons != 3:   self.nextbutton.focus_force()
                else:                   self.okbutton.focus_force()
            else:                   self.okbutton.focus_force()
        else: self.window.focusbutton.focus_force()

class Chemical:
    
    """Stores basic properties of a chemical."""
    def __init__(self, number, soluable):
        """Constructor method.  Uses the "layertype" and the number in the
        capping system and the system's chemical properties to set default
        values for the parameters."""
        
        self.number         = number
        self.soluable       = soluable

    def copy(self):
        """Copy method. Copies everything needed to a new Chemical instance."""

        chemical = Chemical(self.number, self.soluable)

        chemical.number     = self.number
        chemical.soluable   = self.soluable
        chemical.name       = self.name
        chemical.formula    = self.formula
        chemical.MW         = self.MW
        chemical.Ref        = self.Ref
        chemical.temp       = self.temp
        chemical.Dw         = self.Dw 
        chemical.Koc        = self.Koc 
        chemical.Kdoc       = self.Kdoc
        chemical.Kf         = self.Kf
        chemical.N          = self.N

        try:
            chemical.component_name = self.component_name
            chemical.chemical_name  = self.chemical_name
        except: pass

        return chemical
    
    def chemicalwidgets(self, frame, row, master):
        """Makes Tkinter widgets for a layer for an instance of the
        "systemproperties" class."""

        self.master         = master
        self.row            = row

        self.editwidget     = Button(frame, width = 5,  justify = 'center', text = 'Edit',   command = self.editchemical, relief = FLAT, overrelief = RAISED)
        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.delchemical,  relief = FLAT, overrelief = RAISED)
        self.numberlabel    = Label(frame,  width = 2,  justify = 'center', text = self.number)
        self.namelabel      = Label(frame,  width = 16, justify = 'center', text = self.name)
        self.MWlabel        = Label(frame,  width = 8,  justify = 'center', text = self.MW)

        self.templabel      = Label(frame,  width = 8,  justify = 'center', text = self.temp)
        self.Dwlabel        = Label(frame,  width = 10, justify = 'center', text = self.Dw)
        self.Koclabel       = Label(frame,  width = 10, justify = 'center', text = self.Koc)
        self.Kdoclabel      = Label(frame,  width = 10, justify = 'center', text = self.Kdoc)
        self.Reflabel       = Label(frame,              justify = 'center', text = self.Ref)

        self.editwidget.grid( row  = row, column = 1,  padx = 2)
        self.delwidget.grid(  row  = row, column = 2,  padx = 2)
        self.numberlabel.grid(row  = row, column = 3,  padx = 2, sticky = 'WE')
        self.namelabel.grid(  row  = row, column = 4,  padx = 2, sticky = 'WE')
        self.MWlabel.grid(    row  = row, column = 5,  padx = 2, sticky = 'WE')

        self.templabel.grid(  row  = row, column = 6,  padx = 2, sticky = 'WE')
        self.Dwlabel.grid  (  row  = row, column = 7,  padx = 2)
        self.Koclabel.grid (  row  = row, column = 8,  padx = 2)
        self.Kdoclabel.grid(  row  = row, column = 9,  padx = 2)
        self.Reflabel.grid(   row  = row, column = 10, padx = 1)

    def editchemical(self):
        
        self.master.window.editchemical(self.number)

    def delchemical(self):
        
        self.master.window.deletechemical(self.number)
        
    def sorptionwidgets(self, master, row):

        """Makes Tkinter widgets for a layer for an instance of the 
        "LayerModels" class."""
        
        self.sorptionwidget  = Label(master, text ='%s' %(self.name))
        self.sorptionwidget.grid (row =row, column = 2, padx = 4, pady = 2, sticky = 'WE')
        
    def ICwidgets(self, frame, column):

        self.ICwidget = Label(frame, text =self.name, justify = 'center')
        self.ICwidget.grid(row = 2, column = column, padx = 4, pady = 1, sticky ='WE')

    def get_chemical(self, chemicaleditor):
        
        self.name    = chemicaleditor.name.get()
        self.MW      = chemicaleditor.MW.get()
        self.formula = chemicaleditor.formula.get()
        self.Ref     = chemicaleditor.Ref.get()
        self.temp    = chemicaleditor.temp.get()
        self.Dw      = chemicaleditor.Dw.get()
        self.Koc     = chemicaleditor.Koc.get()
        self.Kdoc    = chemicaleditor.Kdoc.get()
        self.Kf      = chemicaleditor.Kf.get()
        self.N       = chemicaleditor.N.get()

    def remove_chemicalwidgets(self):

        self.numberlabel.grid_forget()
        self.namelabel.grid_forget()
        self.MWlabel.grid_forget()
        self.templabel.grid_forget()
        self.Dwlabel.grid_forget()
        self.Koclabel.grid_forget()
        self.Kdoclabel.grid_forget()
        self.Reflabel.grid_forget()
        self.editwidget.grid_forget()
        self.delwidget.grid_forget()

        self.row          = 0
        self.master       = 0
        self.numberlabel  = 0              
        self.namelabel    = 0
        self.MWlabel      = 0
        self.templabel    = 0
        self.Dwlabel      = 0
        self.Koclabel     = 0
        self.Kdoclabel    = 0
        self.Reflabel     = 0
        self.editwidget   = 0
        self.delwidget    = 0
        self.soluablelabel= 0
                
    def remove_sorptionwidgets(self):
        """Removes all the Tkinter property widgets from the layer.  
        Necessary to pickle the System instance."""
        
        self.sorptionwidget.grid_forget()
        self.sorptionwidget    = 0

    def remove_ICwidgets(self):
        """Removes all the Tkinter property widgets from the layer.  
        Necessary to pickle the System instance."""

        self.ICwidget.grid_forget()
        self.ICwidget    = 0

    def get_solid_chemical(self, component_name, chemical_name, MW):

        self.name           = component_name + '_' + chemical_name
        self.component_name = component_name
        self.chemical_name  = chemical_name
        self.MW             = MW
        self.formula        = 0
        self.temp           = 0
        self.Dw             = 0
        self.Koc            = 0
        self.Kdoc           = 0
        self.Kf             = 0
        self.Ref            = ''
        self.N              = 0

class MatrixComponent:
    
    def __init__(self, number):
        
        self.number     = number

    def copy(self):
        
        component           = MatrixComponent(self.number)

        component.name      = self.name
        component.mfraction = self.mfraction
        component.fraction  = self.fraction
        component.e         = self.e
        component.rho       = self.rho 
        component.foc       = self.foc

        component.tort      = self.tort
        component.sorp      = self.sorp

        return component
        
    def propertieswidgets(self, frame, row, master, database, matrices):

        self.master = master

        self.database = database

        self.material_list = database.keys()
        self.material_list.sort()

        try:    self.mfraction     = DoubleVar(value = self.mfraction)
        except: self.mfraction     = DoubleVar(value = 0.5)

        try:
            self.name          = StringVar(value = self.name)
            self.e             = DoubleVar(value = self.e)
            self.rho           = DoubleVar(value = self.rho)
            self.foc           = DoubleVar(value = self.foc)

        except:
            e   = self.database[self.material_list[0]].e
            rho = self.database[self.material_list[0]].rho
            foc = self.database[self.material_list[0]].foc

            for matrix in matrices[:-1]:
                for component in matrix.components:
                    if component.name == self.material_list[0]:
                        e   = component.e
                        rho = component.rho
                        foc = component.foc

            self.name          = StringVar(value = self.material_list[0])
            self.e             = DoubleVar(value = e)
            self.rho           = DoubleVar(value = rho)
            self.foc           = DoubleVar(value = foc)


        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_component, relief = FLAT, overrelief = RAISED)
        if self.material_list.count(self.name.get()) > 0:
            self.namewidget     = OptionMenu(frame, self.name, *self.material_list, command = self.click_name)
            self.namewidget.grid(    row  = row, column = 2, padx = 2, pady = 1, sticky = 'WE')
        else:
            self.namewidget     = Entry( frame, width = 18,  justify = 'center', textvariable = self.name)
            self.namewidget.grid(    row  = row, column = 2, padx = 2, pady = 1)
        self.fractionwidget     = Entry( frame, width = 10, justify = 'center', textvariable = self.mfraction)
        self.elabel             = Entry( frame, width = 10, justify = 'center', textvariable = self.e)
        self.rhowlabel          = Entry( frame, width = 10, justify = 'center', textvariable = self.rho)
        self.foclabel           = Entry( frame, width = 10, justify = 'center', textvariable = self.foc)

        self.delwidget.grid(     row  = row, column = 1, padx = 2 ,pady = 1)
        self.fractionwidget.grid(row  = row, column = 3, padx = 2 ,pady = 1)
        self.elabel.grid(        row  = row, column = 4, padx = 2, pady = 1)
        self.rhowlabel.grid(     row  = row, column = 5, padx = 2 ,pady = 1)
        self.foclabel.grid (     row  = row, column = 6, padx = 2 ,pady = 1)

    def click_name(self, event = None):
        """Pulls up the contaminant properties from the database after selecting
        a compound."""

        self.e.set  (self.database[self.name.get()].e)
        self.rho.set(self.database[self.name.get()].rho)
        self.foc.set(self.database[self.name.get()].foc)
                
    def del_component(self):
        
        self.master.window.del_component(self.number)

    def get_component(self):

        self.mfraction  = self.mfraction.get()
        self.name       = self.name.get()
        self.e          = self.e.get()
        self.rho        = self.rho.get()
        self.foc        = self.foc.get()

        try:
            self.tort       = self.database[self.name].tort
            self.sorp       = self.database[self.name].sorp
        except:
            self.tort       = 'Millington & Quirk'
            self.sorp       = 'Linear--Kd specified'
        
    def remove_propertieswidgets(self):

        self.delwidget.grid_forget()
        self.fractionwidget.grid_forget()
        self.namewidget.grid_forget()
        self.elabel.grid_forget()
        self.rhowlabel.grid_forget()
        self.foclabel.grid_forget()

        self.master         = 0
        
        self.delwidget      = 0
        self.namewidget     = 0
        self.fractionwidget = 0
        self.elabel         = 0
        self.rhowlabel      = 0
        self.foclabel       = 0
        
    def sorptionwidgets(self, master, row):
        """Makes Tkinter widgets for a layer for an instance of the 
        "LayerModels" class."""

        # Title widgets
        self.sorptionwidget   = Label(master, text ='%s' %(self.name))
        
        self.sorptionwidget.grid  (row = row,   column = 1,      padx  = 4,  sticky = 'WE')
        
    def remove_sorptionwidgets(self):
        
        self.sorptionwidget.grid_forget()
        self.sorptionwidget = 0

    def SolidICswidgets(self, frame, row):

        self.SolidICswidget = Label(frame, text ='%s' %(self.name), justify = 'center' )
        self.SolidICswidget.grid  (row = row, column = 2, padx  = 4, pady  = 2, sticky = 'WE')

    def remove_SolidICswidgets(self):

        try:
            self.SolidICswidget.grid_forget()
            self.SolidICswidget = 0
        except: pass

class Matrix:
    """Stores solid properties for CapSim."""

    def __init__(self, number):

        self.number     = number
        
    def copy(self):
        """Copy method. Copies everything needed to a new Chemical instance."""

        matrix              = Matrix(self.number)

        matrix.number       = self.number
        matrix.name         = self.name
        matrix.components   = [component.copy() for component in self.components]
        matrix.model        = self.model
        matrix.e            = self.e
        matrix.rho          = self.rho 
        matrix.foc          = self.foc 
        
        return matrix

    def propertieswidgets(self, frame, row, master):
    
        self.master         = master
        self.row            = row
        materialtext        = ''
        
        self.editwidget     = Button(frame, width = 5,  justify = 'center', text = 'Edit',   command = self.editmatrix , relief = FLAT, overrelief = RAISED)
        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.delmatrix , relief = FLAT, overrelief = RAISED)
        self.namelabel      = Label( frame, width = 16, justify = 'center', text = self.name)
        self.elabel         = Label( frame, width = 8,  justify = 'center', text = self.e)
        self.rhowlabel      = Label( frame, width = 10, justify = 'center', text = self.rho)
        self.foclabel       = Label( frame, width = 10, justify = 'center', text = self.foc)

        self.editwidget.grid(   row  = row, column = 1, padx = 2 ,pady = 1)
        self.delwidget.grid(    row  = row, column = 2, padx = 2 ,pady = 1)
        self.namelabel.grid(    row  = row, column = 3, padx = 2, pady = 1, sticky = 'WE')
        self.elabel.grid(       row  = row, column = 4, padx = 2, pady = 1, sticky = 'WE')
        self.rhowlabel.grid(    row  = row, column = 5, padx = 2 ,pady = 1)
        self.foclabel.grid (    row  = row, column = 6, padx = 2 ,pady = 1)

    def editmatrix(self):
        
        self.master.window.editmatrix(self.number)

    def delmatrix(self):
        
        self.master.window.deletematrix(self.number)
        
    def get_matrix(self, matrixeditor):

        self.name       = matrixeditor.name.get()
        self.e          = matrixeditor.e.get()
        self.rho        = matrixeditor.rho.get()
        self.foc        = matrixeditor.foc.get()
        self.model      = matrixeditor.model.get()
        
        self.components = matrixeditor.components
                
    def remove_propertieswidgets(self):

        self.editwidget.grid_forget()
        self.delwidget.grid_forget()
        self.namelabel.grid_forget()
        self.elabel.grid_forget()
        self.rhowlabel.grid_forget()
        self.foclabel.grid_forget()
        
        self.row          = 0
        self.master       = 0
        self.editwidget   = 0
        self.delwidget    = 0
        self.numberlabel  = 0              
        self.namelabel    = 0
        self.elabel       = 0
        self.rhowlabel    = 0
        self.foclabel     = 0

        
class Sorption:
    """Stores basic properties of a sorption for [layernumber]layer and [chemicalnumber] chemical"""
    
    def __init__(self, matrix, chemical, unit = u'\u03BCg/L'):
        """Constructor method.  Uses the "sorptiontype" and the number in the
        capping system  to set default values for the parameters."""

        self.chemical       = chemical
        self.matrix         = matrix
        self.isotherms      = ['Linear--Kd specified', 'Linear--Kocfoc', 'Freundlich', 'Langmuir']
        self.kinetics       = ['Equilibrium', 'Transient']

        self.isotherm       = matrix.sorp
        self.kinetic        = self.kinetics[0]
        self.foc            = matrix.foc
        self.Koc            = chemical.Koc
        self.Kf             = chemical.Kf
        self.N              = chemical.N

        if unit == 'mg/L':              self.Kf = round_to_n(chemical.Kf * 1000 ** (self.N-1), 3)
        if unit == 'g/L':               self.Kf = round_to_n(chemical.Kf * 1000000 ** (self.N-1), 3)
        if unit == u'\u03BCmol/L':      self.Kf = round_to_n(chemical.Kf * (1./chemical.MW) ** (self.N-1), 3)
        if unit == 'mmol/L':            self.Kf = round_to_n(chemical.Kf * (1000./chemical.MW) ** (self.N-1), 3)
        if unit == 'mol/L':             self.Kf = round_to_n(chemical.Kf * (1000000./chemical.MW) ** (self.N-1), 3)

        self.K              = 0.
        self.qmax           = 0.
        self.b              = 0.
        self.thalf          = 0.
        self.ksorp          = 0.
        self.kdesorp        = 0.
        self.thalf          = 0.
        self.cinit          = 0.
        self.qinit          = 0.

        try:
            self.qmax           = chemical.qmax
            self.b              = chemical.b
        except: pass
            
        if chemical.soluable == 0:
            self.isotherm = self.isotherms[0]

    def copy(self):
        
        sorption = Sorption(self.matrix, self.chemical)

        sorption.isotherms  = self.isotherms
        sorption.isotherm   = self.isotherm

        sorption.kinetics       = self.kinetics
        sorption.kinetic        = self.kinetic
        sorption.foc            = self.foc
        
        sorption.K              = self.K
        sorption.Koc            = self.Koc
        sorption.Kf             = self.Kf
        sorption.N              = self.N
        sorption.qmax           = self.qmax
        sorption.b              = self.b
        sorption.thalf          = self.thalf
        sorption.cinit          = self.cinit
        sorption.qinit          = self.qinit

        sorption.ksorp          = self.ksorp
        sorption.kdesorp        = self.kdesorp

        return sorption
     
    def propertieswidgets(self, frame, row, master, timeunit, concunit):
    
        self.master         = master
        self.row            = row

        bgcolor             = frame.cget('bg')
        self.editwidget     = Button(frame, width = 4,  justify = 'center', text = 'Edit',   command = self.editsorption, relief = FLAT, overrelief = RAISED)
        self.isothermlabel  = Label( frame, width = 16, justify = 'center', text = self.isotherm)
        self.kinetcilabel   = Label( frame, width = 16, justify = 'center', text = self.kinetic)

        if self.isotherm == self.isotherms[0]:

            self.coef1label   = Text(frame, width = 5, height = 1)
            self.coef1label.insert('end', u'K')
            self.coef1label.insert('end', 'd', 'sub')
            self.coef1label.insert('end', ' =')
            self.coef1value   = Label(frame, text = str(self.K))
            self.coef1unit    = Label(frame, text = 'L/kg')

            self.coef2label   = Label(frame, text = ' ')
            self.coef2value   = Label(frame, text = ' ')
            self.coef2unit    = Label(frame, text = ' ')

        if self.isotherm == self.isotherms[1]:

            self.coef1label   = Text(frame, width = 5, height = 1)
            self.coef1label.insert('end', u'K')
            self.coef1label.insert('end', 'oc', 'sub')
            self.coef1label.insert('end', ' =')
            self.coef1value   = Label(frame, text = str(self.Koc))
            self.coef1unit    = Label(frame, text =  'log(L/kg)')

            self.coef2label   = Text(frame, width = 4, height = 1)
            self.coef2label.insert('end', u'f')
            self.coef2label.insert('end', 'oc', 'sub')
            self.coef2label.insert('end', ' =')
            self.coef2value   = Label(frame, text = str(self.matrix.foc))
            self.coef2unit    = Label(frame, text = ' ')

            self.coef2label.tag_config('sub', offset = -2, font = 'Arial 8')
            self.coef2label.tag_config('right', justify = 'right')
            self.coef2label.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

        if self.isotherm == self.isotherms[2]:

            self.coef1label   = Text(frame, width = 5, height = 1)
            self.coef1label.insert('end', u'K')
            self.coef1label.insert('end', 'F', 'sub')
            self.coef1label.insert('end', ' =')

            self.coef1value   = Label(frame, text = str(self.Kf))
            self.coef1unit    = Label(frame, text = concunit[:-1]+'kg/('+ concunit +')'+ u'\u1d3a')

            self.coef2label   = Label(frame, text = 'N =')
            self.coef2value   = Label(frame, text = str(self.N))
            self.coef2unit    = Label(frame, text = ' ')

        if self.isotherm == self.isotherms[3]:

            self.coef1label   = Text(frame, width = 5, height = 1)
            self.coef1label.insert('end', u'q')
            self.coef1label.insert('end', 'max', 'sub')
            self.coef1label.insert('end', ' =')

            self.coef1value   = Label(frame, text = str(self.qmax))
            self.coef1unit    = Label(frame, text = concunit[:-1] + 'kg')

            self.coef2label   = Label(frame, text = 'b =')
            self.coef2value   = Label(frame, text = str(self.b))
            self.coef2unit    = Label(frame, text = 'L/'+ concunit[:-2])

        self.coef1label.tag_config('sub', offset = -2, font = 'Arial 8')
        self.coef1label.tag_config('right', justify = 'right')
        self.coef1label.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

        if self.kinetic == self.kinetics[0]:
            self.coef3label = Label(frame, width = 10, justify = 'center', text = 'Equilibrium')

        if self.kinetic == self.kinetics[1]:

            self.coef3label   = Text(frame, width = 6, height = 1)
            self.coef3label.insert('end', u'k')
            self.coef3label.insert('end', 'sorp', 'sub')
            self.coef3label.insert('end', ' =')

            self.coef3value   = Label(frame, text = str(self.ksorp))

            if self.isotherm == self.isotherms[0] or self.isotherm == self.isotherms[1]:
                self.coef3unit   = Label(frame, text = timeunit + u'\u207B\u00b9')
            if self.isotherm == self.isotherms[2]:
                self.coef3unit   = Label(frame, text = timeunit + u'\u207B\u00b9')
            if self.isotherm == self.isotherms[3]:
                self.coef3unit   = Label(frame, text = '(' + concunit[:-1] +'kg)'+u'\u207B\u00b9 ' +timeunit + u'\u207B\u00b9')

            self.coef3label.tag_config('sub', offset = -2, font = 'Arial 8')
            self.coef3label.tag_config('right', justify = 'right')
            self.coef3label.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)


        self.editwidget.grid(    row  = row, column = 3, padx = 0 ,pady = 1)
        self.isothermlabel.grid( row  = row, column = 4, padx = 0, pady = 3, sticky = 'WE')

        self.coef1label.grid (    row = row, column = 5,  pady = 3, sticky = 'SE')
        self.coef1value.grid (    row = row, column = 6,  pady = 3, sticky = 'SWE')
        self.coef1unit.grid (     row = row, column = 7,  pady = 1, sticky = 'W')
        self.coef2label.grid (    row = row, column = 8,  pady = 1, sticky = 'E')
        self.coef2value.grid (    row = row, column = 9,  pady = 1, sticky = 'WE')
        self.coef2unit.grid (     row = row, column = 10, pady = 1, sticky = 'W')

        if self.kinetic == self.kinetics[0]:
            self.coef3label.grid(    row  = row, column = 11,  padx = 0 ,pady = 1, columnspan = 3, sticky = 'WE')
        else:
            self.coef3label.grid (    row = row, column = 11,  pady = 3, sticky = 'SE')
            self.coef3value.grid (    row = row, column = 12,  pady = 3, sticky = 'WE')
            self.coef3unit.grid (     row = row, column = 13,  pady = 1, sticky = 'W')

    def editsorption(self):
        
        self.master.window.editsorption(self.matrix.name, self.chemical.name)

    def get_sorption(self, sorptioneditor):
        
        self.isotherm   = sorptioneditor.isotherm.get()
        self.kinetic    = sorptioneditor.kinetic.get()
        self.K          = sorptioneditor.K.get()
        self.Koc        = sorptioneditor.Koc.get()
        self.Kf         = sorptioneditor.Kf.get()
        self.N          = sorptioneditor.N.get()   
        self.qmax       = sorptioneditor.qmax.get()
        self.b          = sorptioneditor.b.get()
        self.ksorp      = sorptioneditor.ksorp.get()
        self.thalf      = sorptioneditor.thalf
        self.cinit      = sorptioneditor.cinit
        self.qinit      = sorptioneditor.qinit

        if self.kinetic == self.kinetics[1]:
            if self.isotherm == self.isotherms[0]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/self.K
            if self.isotherm == self.isotherms[1]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/(10**self.Koc)/self.matrix.foc
            if self.isotherm == self.isotherms[2]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/(self.Kf**(1/self.N))
            if self.isotherm == self.isotherms[3]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/self.b

    def update_material(self):

        if self.kinetic == self.kinetics[1]:
            if self.isotherm == self.isotherms[0]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/self.K
            if self.isotherm == self.isotherms[1]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/(10**self.Koc)/self.matrix.foc
            if self.isotherm == self.isotherms[2]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/(self.Kf**(1/self.N))
            if self.isotherm == self.isotherms[3]:  self.kdesorp = self.matrix.e*self.ksorp/self.matrix.rho/self.b

    def remove_propertieswidgets(self):

        self.editwidget.grid_forget()
        self.isothermlabel.grid_forget()
        self.kinetcilabel.grid_forget()
        self.coef1label.grid_forget()
        self.coef1value.grid_forget()
        self.coef1unit.grid_forget()
        self.coef2label.grid_forget()
        self.coef2value.grid_forget()
        self.coef2unit.grid_forget()
        try:
            self.coef3label.grid_forget()
            self.coef3value.grid_forget()
            self.coef3unit.grid_forget()
        except: pass

        self.master          = 0
        self.row             = 0

        self.editwidget      = 0
        self.isothermlabel   = 0
        self.kinetcilabel    = 0
        self.coef1label      = 0
        self.coef1value      = 0
        self.coef1unit       = 0
        self.coef2label      = 0
        self.coef2value      = 0
        self.coef2unit       = 0
        self.coef3label      = 0
        self.coef3value      = 0
        self.coef3unit       = 0

        
    def get_K(self, component, C, Cmax):
        """Takes the concentration "C" for the chemical "chemical" at 
         temperature "temp" and returns the partition coefficient at a point."""

        if self.kinetic == self.kinetics[0]:
            if self.isotherm == self.isotherms[0]:
                K = self.K
            if self.isotherm == self.isotherms[1]:
                K = component.foc * 10**self.Koc
            if self.isotherm == self.isotherms[2]:
                Fmin = 0.0001
                if Cmax < 0.0001: Cmax = 0.0001
                if C <= Fmin * Cmax:                  K = freundlich(Fmin * Cmax, self.Kf, self.N)[0]
                else:                                 K = freundlich(C, self.Kf, self.N)[0]
            if self.isotherm == self.isotherms[3]:
                K = langmuir(C, self.qmax, self.b)[0]
        else:
            K = 0
        return K

    def get_NR(self, C, Cmax):
        """Takes the concentration "C" for the chemical "chemical" at
         temperature "temp" and returns the partition coefficient at a point."""

        if self.isotherm == self.isotherms[2]:
            Fmin = 0.0001
            if Cmax < 0.0001: Cmax = 0.0001
            if C <=Fmin * Cmax:                   K_diff = freundlich(Fmin * Cmax, self.Kf, self.N)[1]
            else:                                 K_diff = freundlich(C, self.Kf, self.N)[1]
        if self.isotherm == self.isotherms[3]:
            K_diff = langmuir(C, self.qmax, self.b)[1]

        return K_diff

    def get_q(self, C):
        """Takes the pore water concentrations "C" for the "Chemical" instance 
        at "temp" and returns the solid-phase concentrations "q." """

        if self.kinetic == self.kinetics[0]:
            if self.isotherm == self.isotherms[0]:
                q = self.K * C
            if self.isotherm == self.isotherms[1]:
                q = self.foc * 10**self.Koc * C
            if self.isotherm == self.isotherms[2]:
                if C <= 0:
                    q = 0
                else:
                    q = freundlich(C, self.Kf, self.N)[0] * C
            if self.isotherm == self.isotherms[3]:
                q = langmuir(C, self.qmax, self.b)[0] * C
        else:
            q = 0

        return q



class Layer:
    """Stores basic properties of a layer."""
    
    def __init__(self, number):
        """Constructor method.  Uses the "layertype" and the number in the
        capping system and the system's chemical properties to set default
        values for the parameters."""

        self.number    = number
        self.torts     = ['Millington & Quirk', 'Boudreau', 'None']
        self.ICtypes   = ['Uniform', 'Linear']
        self.ICtype    = self.ICtypes[0]
        if number == 0: self.name      = 'Deposition'
        else:           self.name      = 'Layer ' + str(number)

        self.delz      = 0
        self.delt      = 0

    def copy(self):
        """Copy method. Copies everything needed to a new Layer instance."""

        layer = Layer(self.number)
        
        layer.name      = self.name
        layer.number    = self.number
        layer.type      = self.type
        layer.type_index= self.type_index
        layer.tort      = self.tort
        layer.torts     = self.torts
        layer.h         = self.h
        layer.alpha     = self.alpha
        layer.doc       = self.doc

        layer.ICtype    = self.ICtype
        layer.ICtypes   = self.ICtypes

        return layer

    def propertywidgets(self, frame, row, master):
        """Makes Tkinter widgets for a layer for an instance of the
        "Layerproperties" class."""
        self.row      = row
        self.master   = master

        self.editwidget = Button(frame, width = 5, justify = 'center', text = 'Edit',   command = self.editlayer, relief = FLAT, overrelief = RAISED)
        self.delwidget  = Button(frame, width = 5, justify = 'center', text = 'Delete', command = self.dellayer, relief = FLAT, overrelief = RAISED)
        self.namelabel  = Label(frame, text = self.name)
        if self.number == 0: self.hlabel     = Label(frame, width = 8, justify = 'center',text = str(self.h)+'/yr')
        else:                self.hlabel     = Label( frame, width = 8, justify = 'center',text = self.h)
        self.typelabel  = Label( frame, width = 8, justify = 'center',text = self.type)
        self.tortlabel  = Label( frame, width = 8, justify = 'center',text = self.tort)
        self.alphalabel = Label( frame, width = 8, justify = 'center',text = self.alpha)
        self.doclabel   = Label( frame, width = 8, justify = 'center',text = self.doc)
        
        self.editwidget.grid(  row = row, column = 1, padx = 2 ,pady = 1)
        self.delwidget.grid(   row = row, column = 2, padx = 2 ,pady = 1)
        self.namelabel.grid(   row = row, column = 3, padx  = 4,  sticky = 'WE')
        self.typelabel.grid(   row = row, column = 4,             sticky = 'WE')
        self.tortlabel.grid(   row = row, column = 5,             sticky = 'WE')
        self.hlabel.grid(      row = row, column = 6, ipady = 2)
        self.alphalabel.grid(  row = row, column = 7, ipady = 2)
        self.doclabel.grid(    row = row, column = 8, ipady = 2)
        
    def editlayer(self):
        
        self.master.window.editlayer(self.number)

    def dellayer(self):
        
        self.master.window.deletelayer(self.number)
        
    def remove_propertywidgets(self):
        
        self.editwidget.grid_forget()
        self.delwidget.grid_forget()
        self.namelabel.grid_forget()
        self.typelabel.grid_forget()
        self.tortlabel.grid_forget()
        self.hlabel.grid_forget()
        self.alphalabel.grid_forget()
        self.doclabel.grid_forget()

        self.row        = 0
        self.master     = 0
        self.editwidget = 0
        self.delwidget  = 0
        self.namelabel  = 0
        self.typelabel  = 0
        self.tortlabel  = 0
        self.hlabel     = 0
        self.alphalabel = 0
        self.doclabel   = 0
        
    def get_layer(self, layereditor):

        if layereditor.editflag == 0:
            if layereditor.names[0] == 'Deposition': self.number = layereditor.names.index(layereditor.name.get())
            else:                                    self.number = layereditor.names.index(layereditor.name.get()) + 1

        self.name       = layereditor.name.get()
        self.type       = layereditor.type.get()
        self.type_index = layereditor.types.index(self.type)
        self.tort       = layereditor.tort.get()
        self.h          = layereditor.h.get()
        self.alpha      = layereditor.alpha.get()
        self.doc        = layereditor.doc.get()
        
    def sorptionwidgets(self, master, row):
        """Makes Tkinter widgets for a layer for an instance of the 
        "LayerModels" class."""

        # Title widgets
        self.sorptionwidget   = Label(master, text = '%s (Layer %d):' % ((self.type, self.number)))
        self.blank1           = Label(master, width = 15, text = ' '*15)
        
        # Widgets grid information        
        self.sorptionwidget.grid  (row = row,   column = 0,      padx  = 4,  sticky = 'WE')                
        self.blank1.grid          (row = row +1, column = 0)
        
    def remove_sorptionwidgets(self):
        """Removes all the Tkinter property widgets from the layer.  
        Necessary to pickle the System instance."""
        self.sorptionwidget.grid_forget()
        self.blank1.grid_forget()
        
        self.sorptionwidget    = 0
        self.blank1            = 0

    def ICwidgets(self, frame, row, master, concunit, default = 0):

        self.layerlabel = Label(frame, text = self.name)
        self.blankrow1  = Label(frame, text = ' ')
        self.blankrow2  = Label(frame, text = ' ')

        self.blankrow1.grid(row = row,     column = 0, padx  = 4,  sticky = 'WE', pady = 2)
        self.blankrow2.grid(row = row + 1, column = 0, padx  = 4,  sticky = 'WE', pady = 2)

        self.layerlabel.grid( row = row, column = 1, padx  = 4,  sticky = 'WE', rowspan = 2)

        if type(self.ICtype) == type('str'): self.ICtype = StringVar(value = self.ICtype)


        if self.name == 'Deposition':

            self.typewidget = Label(frame, textvariable = self.ICtype)
            self.typewidget.grid( row = row, column = 2, padx  = 4,  sticky = 'WE', rowspan = 2)
            if default == 0:
                self.conclabel = Label(frame, text = 'Initial concentration')
                self.unitlabel = Label(frame, text = concunit)
                self.conclabel.grid( row = row, column = 3, padx  = 4,  sticky = 'WE', pady = 4, rowspan = 2)
                self.unitlabel.grid( row = row, column = 4, padx  = 4,  sticky = 'WE', pady = 4, rowspan = 2)
            else:
                self.conclabel = Label(frame, text = 'Initial solid phase concentration')
                self.unitlabel = Label(frame, text = concunit[:-1]+ 'kg')
                self.conclabel.grid( row = row, column = 2, padx  = 4,   sticky = 'WE', rowspan = 2)
                self.unitlabel.grid( row = row, column = 3, padx  = 4,   sticky = 'WE', pady = 4, rowspan = 2)

        else:
            if default == 0:
                self.typewidget = OptionMenu(frame, self.ICtype, *self.ICtypes, command = master.window.updateconditions)
                self.typewidget.grid( row = row, column = 2, padx  = 4,  sticky = 'WE', rowspan = 2)
            else:
                self.typewidget = Label(frame, textvariable = self.ICtype)

            if self.ICtype.get() == self.ICtypes[0]:
                if default == 0:
                    self.conclabel = Label(frame, text = 'Initial concentration')
                    self.unitlabel = Label(frame, text = concunit)
                    self.conclabel.grid( row = row, column = 3, padx  = 4,  sticky = 'WE', pady = 4, rowspan = 2)
                    self.unitlabel.grid( row = row, column = 4, padx  = 4,  sticky = 'WE', pady = 4, rowspan = 2)
                else:
                    self.conclabel = Label(frame, text = 'Initial solid phase concentration')
                    self.unitlabel = Label(frame, text = concunit[:-1]+ 'kg')
                    self.conclabel.grid( row = row, column = 2, padx  = 4,   sticky = 'WE', rowspan = 2)
                    self.unitlabel.grid( row = row, column = 3, padx  = 4,  sticky = 'WE', pady = 4, rowspan = 2)

            if self.ICtype.get() == self.ICtypes[1]:
                if default == 0:
                    self.toplabel     = Label(frame, text = 'Top concentration')
                    self.topunitlabel = Label(frame, text = concunit)
                    self.botlabel = Label(frame, text = 'Bottom concentration')
                    self.botunitlabel = Label(frame, text = concunit)

                    self.toplabel.grid( row = row,      column = 3, padx  = 4,  sticky = 'WE', pady = 2)
                    self.topunitlabel.grid( row = row,  column = 4, padx  = 4,  sticky = 'WE', pady = 2)
                    self.botlabel.grid( row = row + 1,  column = 3, padx  = 4,  sticky = 'WE', pady = 2)
                    self.botunitlabel.grid( row = row+1,column = 4, padx  = 4,  sticky = 'WE', pady = 2)
                else:
                    self.toplabel = Label(frame, text = 'Top solid phase concentration')
                    self.topunitlabel = Label(frame, text = concunit[:-1]+ 'kg')
                    self.botlabel = Label(frame, text = 'Bottom solid phase concentration')
                    self.botunitlabel = Label(frame, text = concunit[:-1]+ 'kg')

                    self.toplabel.grid(     row = row,      column = 2, padx  = 4,  sticky = 'WE', pady = 2)
                    self.topunitlabel.grid( row = row,      column = 3, padx  = 4,  sticky = 'WE', pady = 2)
                    self.botlabel.grid(     row = row + 1,  column = 2, padx  = 4,  sticky = 'WE', pady = 2)
                    self.botunitlabel.grid( row = row + 1,  column = 3, padx  = 4,  sticky = 'WE', pady = 2)


    def remove_ICwidgets(self):
        
        self.layerlabel.grid_forget()
        self.typewidget.grid_forget()
        self.blankrow1.grid_forget()
        self.blankrow2.grid_forget()

        try:
            self.conclabel.grid_forget()
            self.unitlabel.grid_forget()
        except :pass
        
        try:
            self.toplabel.grid_forget()
            self.topunitlabel.grid_forget()
            self.botlabel.grid_forget()
            self.botunitlabel.grid_forget()
        except :pass
        
        self.layerlabel = 0
        self.typewidget = 0
        self.blankrow1  = 0
        self.blankrow2  = 0
        self.conclabel  = 0
        self.toplabel   = 0
        self.botlabel   = 0
        self.unitlabel  = 0
        self.topunitlabel= 0
        self.botunitlabel= 0

    def get_layerconditions(self):
        
        self.ICtype = self.ICtype.get()

        
    def SolidICwidgets(self, frame, row_layer, row, columnspan):

        self.solidlayerlabel = Label(frame, text = self.name, justify = 'center')
        self.blank2          = Label(frame, width = 10, text = '-' * 1000)

        self.solidlayerlabel.grid( row = row_layer, column = 1, padx  = 4,  sticky = 'WE', rowspan = row - row_layer)
        self.blank2.grid(          row = row + 1,   column = 1, sticky = 'WE', columnspan = columnspan)

    def remove_SolidICwidgets(self):

        try:
            self.solidlayerlabel.grid_forget()
            self.blank2.grid_forget()
        except: pass

        self.solidlayerlabel = 0
        self.blank2 = 0

    def reactionwidgets(self, master, row, row_layer):
        
        rowspan = row - row_layer + 1

        # Title widgets
        self.reactionwidget   = Label(master, text = self.name)
        self.blank2           = Label(master, width = 10, text = '-' * 1000)
        
        # Widgets grid information        
        self.reactionwidget.grid(row = row_layer, column = 1,   padx  = 4,  sticky = 'WE', rowspan = rowspan, pady = 4)                
        self.blank2.grid(        row = row +1,    column = 1,   columnspan = 7, sticky = 'WE')

    def remove_reactionwidgets(self):

        self.reactionwidget.grid_forget()
        self.blank2.grid_forget()
        
        self.reactionwidget = 0
        self.blank2         = 0

    def solverwidgets(self, master, row):

        self.tstep = DoubleVar(value = self.tstep)

        self.layerlabel = Label(master, text = 'Layer %d:' % (self.name))
        self.layerlabel.grid(row = row, column = 1,   padx  = 4,  sticky = 'WE', pady = 4)

    def get_solver(self, layersolverparameter):

        self.delz = layersolverparameter.delz.get()

    def remove_solverwidgets(self):

        self.layerlabel.grid_forget()

        self.layerlabel = 0

    def get_D(self, Dw, Vdar, e):
        """Calculates the value of the effective diffusion coefficient "D" at a
        point.  "chemical" is an object containing properties of the chemical,
        "temp" is the temperature, and "Vdar" is the Darcy velocity.  The 
        effective diffusion coefficient is the sum of the tortuosity-corrected 
        molecular diffusion coefficient, the dispersion coefficient (Darcy 
        velocity times dispersivity), the pore water biodiffusion coefficient, 
        and the particle biodiffusion coefficient times the bulk density times 
        the partition coefficient."""

        if   self.tort == self.torts[0]: tort = millquirk
        elif self.tort == self.torts[1]: tort = boudreau
        elif self.tort == self.torts[2]: tort = notort

        return (Dw * tort(e) + self.alpha * abs(Vdar))

class Reaction:
    """Stores basic properties of kinetic process for [layernumber]layer and [chemicalnumber] chemical"""
    
    def __init__(self, number):
        """Constructor method.  Uses number to define the reaction in """
        
        self.number                 = number


    def copy(self):
        
        reaction = Reaction(self.number)

        reaction.name      = self.name
        reaction.model     = self.model
        reaction.equation  = self.equation
        reaction.reactants = [reactant.copy() for reactant in self.reactants]
        reaction.products  = [product.copy()  for product  in self.products]

        try: reaction.component = self.component
        except: pass

        return reaction

        
    def propertieswidgets(self, frame, row, master, font, superfont, subfont, bgcolor):

        self.master = master
        
        self.editwidget = Button(frame, width = 5, justify = 'center', text = 'Edit',   command = self.editreaction, relief = FLAT, overrelief = RAISED)
        self.delwidget  = Button(frame, width = 5, justify = 'center', text = 'Delete', command = self.delreaction, relief = FLAT, overrelief = RAISED)
        self.numblabel  = Label( frame, text = self.number,   justify = 'center')
        self.namelabel  = Label( frame, text = self.name,     justify = 'center')
        self.equalabel  = Label( frame, text = self.equation, justify = 'center', font = 'Calibri 11')

        if self.model == 'User-defined' or self.model == 'Fundamental':

            tkfont      = tkFont.Font(font = font)
            tksubfont   = tkFont.Font(font = subfont)
            tksuperfont = tkFont.Font(font = superfont)

            rate_len  = tkfont.measure(u'r = \u03BB')
            rate_len  = rate_len + tksubfont.measure(str(self.number))
            for reactant in self.reactants:
                if reactant.index <> 0:
                    rate_len = rate_len + tkfont.measure('C')
                    rate_len = rate_len + tksubfont.measure(reactant.formula)
                    if reactant.index == int(reactant.index): index = int(reactant.index)
                    else:                                     index = reactant.index
                    if index <> 1.: rate_len = rate_len + tksuperfont.measure(str(index) + ' ')

            self.ratewidget  = Text(frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font = font)
            self.ratewidget.insert('end', u'r = \u03BB')
            self.ratewidget.insert('end', str(self.number), 'sub')
            for reactant in self.reactants:
                if reactant.index <> 0:
                    self.ratewidget.insert('end', 'C')
                    self.ratewidget.insert('end', reactant.formula, 'sub')
                    if reactant.index == int(reactant.index): index = int(reactant.index)
                    else:                                     index = reactant.index
                    if index <> 1.: self.ratewidget.insert('end', str(index) + ' ', 'super')
            self.ratewidget.tag_config('sub', offset = -4, font = subfont)
            self.ratewidget.tag_config('super', offset = 5, font = superfont)
            self.ratewidget.tag_config('right', justify = 'right')
            self.ratewidget.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
        
        self.editwidget.grid( row = row, column = 1, padx = 2 ,pady = 1)
        self.delwidget.grid(  row = row, column = 2, padx = 2 ,pady = 1)
        self.numblabel.grid(  row = row, column = 3, padx = 2, sticky = 'WE')
        self.namelabel.grid(  row = row, column = 4, padx = 2, sticky = 'WE')
        self.equalabel.grid(  row = row, column = 5, padx = 5, sticky = 'WE')
        self.ratewidget.grid( row = row, column = 6, padx = 5, sticky = 'W')

    def editreaction(self):
        
        self.master.window.editreaction(self.number)

    def delreaction(self):
        
        self.master.window.delreaction(self.number)
    
    def get_reaction(self, reactioneditor):
        
        self.reactants = reactioneditor.reactants
        self.products  = reactioneditor.products
        self.name      = reactioneditor.name.get()
        self.model     = reactioneditor.model.get()

        self.equation  = ''

        if len(self.reactants) <> 0 or len(self.products) <> 0:
            
            for reactant in self.reactants:
                if reactant.coef == 1.0:                  coef = ''
                elif int(reactant.coef) == reactant.coef: coef = int(reactant.coef)
                else:                                     coef = reactant.coef
                self.equation = self.equation + ' ' + str(coef) + reactant.formula + ' '+ '+'
            self.equation = self.equation[:-1]

            if len(self.reactants) <> 0 and len(self.products) <> 0: self.equation = self.equation + ' ==> '

            for product in self.products:
                if product.coef == 1.0:                 coef = ''
                elif int(product.coef) == product.coef: coef = int(product.coef)
                else:                                   coef = product.coef
                self.equation = self.equation + ' ' + str(coef) + product.formula + ' '+ '+'
            self.equation = self.equation[:-1]

            if len(self.reactants) == 0: self.equation =  self.equation + ' Generation'
            if len(self.products) == 0:  self.equation =  self.equation + ' Decay'


    def remove_propertieswidgets(self):

        self.editwidget.grid_forget()
        self.delwidget.grid_forget()
        self.numblabel.grid_forget()
        self.namelabel.grid_forget()
        self.equalabel.grid_forget()
        self.ratewidget.grid_forget()

        self.master       = 0
        self.editwidget   = 0              
        self.delwidget    = 0
        self.numblabel    = 0
        self.namelabel    = 0
        self.equalabel    = 0
        self.ratewidget   = 0

    def get_dynamic_sorption(self, name, component, reactant, product, model):

        self.name      = name
        self.component = component
        self.equation  = ''
        self.model     = model
        self.reactants = [reactant]
        self.products  = [product]

class Coefficient:
    """Stores reaction coefficient of a reaction in a layer."""
    
    def __init__(self, layer, reaction):

        self.layer          = layer
        self.reaction       = reaction

        self.lam            = 0


    def copy(self):
        """Copy method. Copies everything needed to a new Layer instance."""

        coefficient = Coefficient(self.layer, self.reaction)

        coefficient.lam            = self.lam

        return coefficient
        
    def propertieswidgets(self, frame, row, master, font, superfont, subfont, timeunit, concunit):

        self.master = master
        
        bgcolor             = frame.cget('bg')
        
        self.editwidget = Button(frame, text = 'Edit',        justify = 'center', width = 5, command = self.editcoefficient, relief = FLAT, overrelief = RAISED)
        self.delwidget  = Button(frame, text = 'Delete',      justify = 'center', width = 5, command = self.delcoefficient, relief = FLAT, overrelief = RAISED)
        self.namelabel  = Label( frame, text = self.reaction.name,     justify = 'center')
        self.equalabel  = Label( frame, text = self.reaction.equation, justify = 'center', font = 'Calibri 11')
        
        unitindex       = 0

        tkfont      = tkFont.Font(font = font)
        tksubfont   = tkFont.Font(font = subfont)
        tksuperfont = tkFont.Font(font = superfont)

        # Measure the width of rate and lambda expression
        rate_len  = tkfont.measure(u'r = \u03BB')
        rate_len  = rate_len + tksubfont.measure(str(self.reaction.number)+ ',')
        if self.layer.number == 0: rate_len  = rate_len + tksubfont.measure('D')
        else:                      rate_len  = rate_len + tksubfont.measure(str(self.layer.number))
        for reactant in self.reaction.reactants:
            if reactant.index <> 0:
                rate_len = rate_len + tkfont.measure('C')
                rate_len = rate_len + tksubfont.measure(reactant.formula)
                if reactant.index == int(reactant.index): index = int(reactant.index)
                else:                                     index = reactant.index

                if index <> 1.: rate_len = rate_len + tksuperfont.measure(str(index) + ' ')
                unitindex = unitindex + reactant.index

        lam_len   = tkfont.measure(u'\u03BB')
        lam_len   = lam_len + tksubfont.measure(str(self.reaction.number)+ ',')
        if self.layer.number == 0: lam_len  = lam_len + tksubfont.measure('D')
        else:                      lam_len  = lam_len + tksubfont.measure(str(self.layer.number))
        lam_len  = lam_len + tkfont.measure(' = '+str(self.lam) + ' ')

        if unitindex == int(unitindex): unitindex = int(unitindex)
        if (unitindex - 1) != 0:
            if (unitindex - 1) != -1:
                lam_len  = lam_len + tkfont.measure('('+concunit+')')
                lam_len  = lam_len + tksuperfont.measure(str(-(unitindex - 1)))

            else:
                lam_len  = lam_len + tkfont.measure(concunit + ' ')
        lam_len  = lam_len + tkfont.measure(timeunit)
        lam_len  = lam_len + tksuperfont.measure('-1')

        # Construct the text widget for the rate and lambda expressions
        self.ratelabel  = Text(frame, width = int(rate_len*1.1424219345/8)+1, height = 1, font =font)
        self.ratelabel.insert('end', u'r = \u03BB')
        self.ratelabel.insert('end', str(self.reaction.number) + ',', 'sub')
        if self.layer.number == 0: self.ratelabel.insert('end', 'D', 'sub')
        else:                      self.ratelabel.insert('end', str(self.layer.number), 'sub')
        for reactant in self.reaction.reactants:
            if reactant.index <> 0:
                self.ratelabel.insert('end', 'C')
                self.ratelabel.insert('end', reactant.formula, 'sub')
                if reactant.index == int(reactant.index): index = int(reactant.index)
                else:                                     index = reactant.index
                if index <> 1.: self.ratelabel.insert('end', str(index) + ' ', 'super')
        self.ratelabel.tag_config('sub', offset = -4, font = subfont)
        self.ratelabel.tag_config('super', offset = 5, font = superfont)
        self.ratelabel.tag_config('right', justify = 'right')
        self.ratelabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)

        self.lamlabel  = Text(frame, width = int(lam_len*1.1424219345/8)+1, height = 1, font =font)
        self.lamlabel.insert('end',  u'\u03BB')
        self.lamlabel.insert('end', str(self.reaction.number) + ',', 'sub')
        if self.layer.number == 0: self.lamlabel.insert('end', 'D', 'sub')
        else:                      self.lamlabel.insert('end', str(self.layer.number), 'sub')
        self.lamlabel.insert('end',  ' = '+str(self.lam) + ' ')
        if (unitindex - 1) != 0:
            if (unitindex - 1) != -1:
                self.lamlabel.insert('end', '('+concunit+')')
                self.lamlabel.insert('end', str(-(unitindex - 1)), 'super')
            else:
                self.lamlabel.insert('end', concunit + ' ')
        self.lamlabel.insert('end', timeunit)
        self.lamlabel.insert('end', '-1', 'super')
        self.lamlabel.tag_config('sub', offset = -4, font = subfont)
        self.lamlabel.tag_config('super', offset = 5, font = superfont)
        self.lamlabel.tag_config('right', justify = 'right')
        self.lamlabel.config(state = 'disabled', background = bgcolor, borderwidth = 0, spacing3 = 3)
        
        self.editwidget.grid( row = row, column = 2, padx = 2 , pady = 2)
        self.delwidget.grid(  row = row, column = 3, padx = 2 , pady = 2)
        self.namelabel.grid(  row = row, column = 4, padx = 2,  sticky = 'WE')
        self.equalabel.grid(  row = row, column = 5, padx = 5, sticky = 'WE')
        self.ratelabel.grid(  row = row, column = 6, padx = 5, sticky = 'W')
        self.lamlabel.grid(   row = row, column = 7, padx = 5, sticky = 'W')
        
    def editcoefficient(self):
        
        self.master.window.editcoefficient(self.layer.name, self.reaction.name)

    def delcoefficient(self):
        
        self.master.window.delcoefficient(self.layer.name, self.reaction.name)
        
    def remove_propertieswidgets(self):
        
        try:
            self.editwidget.grid_forget()
            self.delwidget.grid_forget()
            self.namelabel.grid_forget()
            self.equalabel.grid_forget()
            self.ratelabel.grid_forget()
            self.lamlabel.grid_forget()
        except: pass
        
        self.row        = 0
        self.master     = 0
        self.editwidget = 0
        self.delwidget  = 0
        self.namelabel  = 0
        self.equalabel  = 0
        self.ratelabel  = 0
        self.lamlabel   = 0
        
    def get_coefficients(self, coefficienteditor):

        self.lam = coefficienteditor.lam.get()

    def get_dynamic_sorption(self, sorption_k):

        self.lam = sorption_k

class BC:
    """Stores the top and bottom boundary conditions of each chemical"""

    def __init__(self, chemical_name, soluableflag):

        self.chemical_name  = chemical_name
        try:    self.soluableflag   = soluableflag
        except: self.soluableflag   = 1
        self.topBCtypes     = ['Fixed Concentration', 'Mass transfer', 'Finite mixed water column']
        self.botBCtypes     = ['Fixed Concentration', 'Flux-matching', 'Zero Gradient']

        self.topBCtype      = self.topBCtypes[0]
        self.botBCtype      = self.botBCtypes[0]

        if self.soluableflag == 1:
            self.Co             = 0.
            self.k              = 0.1
            self.Cw             = 0.
            self.Cb             = 1.
            self.tau            = 0.
            self.kdecay         = 0.
            self.kevap          = 0.
        else:
            self.Co             = 0.
            self.k              = 0.
            self.Cw             = 0.
            self.Cb             = 0.
            self.tau            = 0.
            self.kdecay         = 0.
            self.kevap          = 0.

        
    def copy(self):
        
        bc = BC(self.chemical_name, self.soluableflag)
        
        bc.Co               = self.Co        
        bc.k                = self.k
        bc.Cw               = self.Cw
        bc.Cb               = self.Cb
        bc.tau              = self.tau
        bc.kdecay           = self.kdecay
        bc.kevap            = self.kevap

        bc.topBCtype        = self.topBCtype
        bc.botBCtype        = self.botBCtype
        
        return bc
    
    def topboundarywidget(self, frame, row, column):

        if self.soluableflag == 1:
            if self.topBCtype == 'Fixed Concentration':
                try:       self.Co.get()
                except:    self.Co = DoubleVar(value = self.Co)
                self.Coentry    = Entry(frame, width = 8, textvariable = self.Co, justify = 'center')
                self.Coentry.grid( row = row    , column = column,  padx = 2, pady = 1, rowspan = 2)

            if self.topBCtype == 'Mass transfer':
                try:    self.k.get()
                except: self.k  = DoubleVar(value = self.k)

                try:    self.Cw.get()
                except: self.Cw = DoubleVar(value = self.Cw)
                self.kentry  = Entry(frame, width = 8, textvariable = self.k, justify = 'center')
                self.Cwentry = Entry(frame, width = 8, textvariable = self.Cw, justify = 'center')
                self.kentry.grid(  row = row    , column = column,  padx = 2, pady = 1)
                self.Cwentry.grid( row = row + 1, column = column,  padx = 2, pady = 1)

            if self.topBCtype == 'Finite mixed water column':

                try:    self.k.get()
                except: self.k  = DoubleVar(value = self.k)

                try:    self.tau.get()
                except: self.tau = DoubleVar(value = self.tau)
                self.kentry   = Entry(frame, width = 8, textvariable = self.k,   justify = 'center')
                self.tauentry = Label(frame, width = 8, textvariable = self.tau, justify = 'center')
                self.kentry.grid(   row = row    , column = column,  padx = 2, pady = 1)
                self.tauentry.grid( row = row + 1, column = column,  padx = 2, pady = 1)

    def botboundarywidget(self, frame, row, column):
                
        if self.soluableflag == 1:
            if self.botBCtype == self.botBCtypes[0] or self.botBCtype == self.botBCtypes[1]:
                try:       self.Cb.get()
                except:    self.Cb = DoubleVar(value = self.Cb)
                self.Cbentry    = Entry(frame, width = 8, textvariable = self.Cb, justify = 'center')
                self.Cbentry.grid( row = row    , column = column,  padx = 2, pady = 1)

    def remove_widgets(self):
        
        try:
            self.Coentry.grid_forget()              
        except: pass

        try:
            self.kentry.grid_forget()
        except:pass

        try:
            self.tauentry.grid_forget()
        except:pass

        try:
            self.Cwentry.grid_forget()
        except:pass

        try:
            self.Cbentry.grid_forget()
        except:pass

        self.Coentry    = 0
        self.kentry     = 0
        self.tauentry   = 0
        self.Cwentry    = 0
        self.Cbentry    = 0
            

    def get_BC(self):

        try:
            self.Co = self.Co.get()
        except: pass
                
        try:
            self.k  = self.k.get()
        except: pass

        try:
            self.Cw = self.Cw.get()
        except: pass

        try:
            self.tau    = self.tau.get()
        except: pass

        try:
            self.Cb  = self.Cb.get()
        except: pass

class IC:
    """Stores the initial concentrations of each chemical in all layers."""

    def __init__(self, layer_name, chemical_name):
        
        self.layer_name     = layer_name        
        self.chemical_name  = chemical_name
        self.ICtypes        = ['Uniform', 'Linear']
        self.ICtype         = self.ICtypes[0]
        self.top            = 0.
        self.bot            = 0.
        self.uniform        = 0.

    def copy(self):
        
        ic = IC(self.layer_name, self.chemical_name)
        
        ic.layer_name     = self.layer_name        
        ic.chemical_name  = self.chemical_name
        ic.ICtypes        = self.ICtypes
        ic.ICtype         = self.ICtype
        ic.top            = self.top
        ic.bot            = self.bot
        ic.uniform        = self.uniform

        return ic
        
    def propertieswidgets(self, frame, row, column, ICtype, layername):
        
        self.ICtype = ICtype

        if layername == 'Deposition':
            try:    self.uniform.get()
            except: self.uniform    = DoubleVar(value = self.uniform)
            self.ICentry = Label(frame, width = 8, textvariable = self.uniform, justify = 'center')
            self.ICentry.grid( row = row, column = column,  padx = 2, pady = 1, rowspan = 2)
        else:
            if self.ICtype == self.ICtypes[0]:
                try:    self.uniform.get()
                except: self.uniform    = DoubleVar(value = self.uniform)
                self.ICentry    = Entry(frame, width = 8, textvariable = self.uniform, justify = 'center')
                self.ICentry.grid( row = row, column = column,  padx = 2, pady = 1, rowspan = 2)

            if self.ICtype == self.ICtypes[1]:

                try:    self.top.get()
                except: self.top    = DoubleVar(value = self.top)
                try:    self.bot.get()
                except: self.bot    = DoubleVar(value = self.bot)

                self.ICtopentry = Entry(frame, width = 8, textvariable = self.top, justify = 'center')
                self.ICbotentry = Entry(frame, width = 8, textvariable = self.bot, justify = 'center')
                self.ICtopentry.grid( row = row,     column = column,  padx = 2, pady = 1)
                self.ICbotentry.grid( row = row + 1, column = column,  padx = 2, pady = 1)
            
    def remove_widgets(self):

        try: self.ICentry.grid_forget()
        except :
            self.ICtopentry.grid_forget()
            self.ICbotentry.grid_forget()

        self.ICentry    = 0
        self.ICtopentry = 0
        self.ICbotentry = 0

        
    def get_IC(self):

        try:
            self.uniform    = self.uniform.get()
        except: pass

        try:
            self.top        = self.top.get()
            self.bot        = self.bot.get()
        except: pass

class SolidIC:
    """Stores the initial concentrations of each chemical in all layers."""

    def __init__(self, layer_name, component_name, chemical_name):

        self.layer_name     = layer_name
        self.component_name = component_name
        self.chemical_name  = chemical_name
        self.top            = 0.
        self.bot            = 0.
        self.uniform        = 0.

    def copy(self):

        ic = IC(self.layer_name, self.chemical_name)

        ic.layer_name     = self.layer_name
        ic.chemical_name  = self.chemical_name
        ic.uniform        = self.uniform
        ic.top            = self.top
        ic.bot            = self.bot

        return ic

    def propertieswidgets(self, frame, row, column):

        try:    self.uniform.get()
        except:
            self.uniform    = DoubleVar(value = self.uniform)

        self.ICentry    = Entry(frame, width = 8, textvariable = self.uniform, justify = 'center')
        self.ICentry.grid( row = row, column = column,  padx = 4, pady = 1, rowspan = 1)


    def remove_widgets(self):

        try:
            self.ICentry.grid_forget()
            self.ICentry            = 0
        except: pass

        try:
            self.blank.grid_forget()
            self.blank    = 0
        except: pass

    def blankwidgets(self, frame, row, column):

        self.blank    = Label(frame, width = 8, text = 'Equilibrium', justify = 'center')
        self.blank.grid( row = row, column = column,  padx = 4, pady = 2, rowspan = 1)

    def get_IC(self):

        try:
            self.uniform    = self.uniform.get()
        except: pass

        try:
            self.top        = self.top.get()
            self.bot        = self.bot.get()
        except: pass

        
class System:
    """Stores the properties of a sediment environment for cap modeling."""

    def __init__(self, version, fonttype, formulatype):

        self.version      = version   #CapSim version
        self.fonttype     = fonttype  #font for widgets
        self.formulatype  = formulatype
        self.chemicals    = None
        self.matrices     = None
        self.layers       = None
        self.sorptions    = None
        self.reactions    = None
        self.coefficients = None
        self.ICs          = None
        self.BCs          = None
        self.SolidICs     = None
        self.tfinal       = 100
        self.outputsteps  = 100

    def copy(self):

        system = System(self.version, self.fonttype, self.formulatype)

        return system

    def get_systemunits(self, systemunits):

        self.lengthunit  = systemunits.lengthunit.get()
        self.concunit    = systemunits.concunit.get()
        self.timeunit    = systemunits.timeunit.get()
        self.diffunit    = systemunits.diffunit.get()

        self.lengthunits = systemunits.lengthunits
        self.concunits   = systemunits.concunits
        self.timeunits   = systemunits.timeunits
        self.diffunits   = systemunits.diffunits

    def get_chemicalproperties(self, chemicalproperties):

        self.chemicals  = chemicalproperties.chemicals
        self.nchemicals = chemicalproperties.nchemicals

    def get_matricesproperties(self, matrixproperties):

        self.matrices   = matrixproperties.matrices
        self.nmatrices  = matrixproperties.nmatrices
        
        self.component_list      = []
        self.components          = []
        for matrix in self.matrices:
            for component in matrix.components:
                try:self.component_list.index(component.name)
                except:
                    self.components.append(component)
                    self.component_list.append(component.name)

    def get_sorptionproperties(self, sorptionproperties):
        """Gets models for specific properties of the layers from the 
        "LayerProperties" class and sets default parameters from database."""

        self.sorptions      = sorptionproperties.sorptions
        

    def get_layerproperties(self, layerproperties):
        """Gets basic properties of the layers from the "LayerProperties" 
        class."""

        self.layers  = layerproperties.layers
        self.nlayers = layerproperties.nlayers
        if self.nlayers > 0:
            if self.layers[0].number == 0:
                self.dep  = 'Deposition'
                self.Vdep = self.layers[0].h
            else:
                self.dep  = 0
                self.Vdep = 0

    def get_reactionproperties(self, reactionproperties):

        self.reactions = reactionproperties.reactions

    def get_reactioncoefficients(self, reactioncoefficients):

        self.coefficients = reactioncoefficients.coefficients

    def get_systemproperties(self, systemproperties):
        """Gets information from the "SystemProperties" class."""

        self.adv    = systemproperties.adv.get()
        self.bio    = systemproperties.bio.get()
        self.con    = systemproperties.con.get()

        self.Vdar   = systemproperties.Vdar.get()
        self.Vtidal = systemproperties.Vtidal.get()
        self.ptidal = systemproperties.ptidal.get()
        self.sigma  = systemproperties.sigma.get()
        self.hbio   = systemproperties.hbio.get()
        self.Dbiop  = systemproperties.Dbiop.get()
        self.Dbiopw = systemproperties.Dbiopw.get()
        self.hcon   = systemproperties.hcon.get()
        self.t90    = systemproperties.t90.get()

        if self.bio <> 'None' and (self.layers[0].name == 'Deposition' or self.layers[0].h < self.hbio or self.bio == 'Depth-dependent') and self.Dbiop> 0:     self.biomix = 1
        else:                                                                                                                                                   self.biomix = 0

    def get_layerconditions(self, layerconditions):
        """Gets chemical properties from the layers in the 
        "ChemicalProperties" object type."""

        self.bltype     = layerconditions.bltype
        self.blcoefs    = layerconditions.blcoefs
        self.taucoefs   = layerconditions.taucoefs

        self.BCs        = layerconditions.BCs
        self.ICs        = layerconditions.ICs
        self.topBCtype  = layerconditions.topBCtype.get()
        self.botBCtype  = layerconditions.botBCtype.get()

        for chemical in self.chemicals:
            self.BCs[chemical.name].get_BC()
            for layer in self.layers:
                self.ICs[layer.name][chemical.name].get_IC()
                if layer.name == 'Deposition':
                    if self.topBCtype == 'Mass transfer':               self.ICs[layer.name][chemical.name].uniform = self.BCs[chemical.name].Cw
                    if self.topBCtype == 'Fixed Concentration':         self.ICs[layer.name][chemical.name].uniform = self.BCs[chemical.name].Co
                    if self.topBCtype == 'Finite mixed water column':   self.ICs[layer.name][chemical.name].uniform = 0

    def get_solidlayerconditions(self, solidlayerconditions):

        self.SolidICs = solidlayerconditions.SolidICs

        for layer in self.layers:
            for component in self.matrices[layer.type_index].components:
                for chemical in self.chemicals:
                     self.SolidICs[layer.name][component.name][chemical.name].get_IC()

    def get_solveroptions(self, solveroptions):
        """Gets the output options from the "SolvernOutput" object type."""

        #self.cpsmfilename = solveroptions.inputname.get()
        self.tfinal       = solveroptions.duration.get()
        self.outputsteps  = solveroptions.outputsteps.get()
        self.discrete     = solveroptions.discrete.get()
        self.ptotal       = solveroptions.ptotal.get()
        self.delt         = solveroptions.delt.get()
        self.timeoption   = solveroptions.timeoption.get()
        self.ptype        = solveroptions.ptype
        self.tvariable    = solveroptions.tvariable
        self.delz         = solveroptions.delz
        self.players      = solveroptions.players
        self.tidalsteps   = solveroptions.tidalsteps.get()
        self.nonlinear    = solveroptions.nonlinear.get()
        self.nlerror      = solveroptions.nlerror.get()/100
        self.averageoption= solveroptions.averageoption.get()
        self.depgrid      = solveroptions.depgrid.get()
        self.depoption    = solveroptions.depoption

    def get_inputoptions(self, solveroptions):
        """Gets the output options from the "SolvernOutput" object type."""

        self.cpsmfilename  = solveroptions.inputname.get()
        self.csvfileoption = solveroptions.csvfileoption.get()
        self.csvfilename   = solveroptions.csvfilename.get()

class PlotData:

    def __init__(self, name):
        """Constructor Method.  Provide all the fundamental properties of a chemical."""

        self.name    = name   #chemical name
        self.times   = []
        self.depths  = []

    def propertieswidgets(self, frame, row, master, type):

        self.master         = master
        self.frame          = frame
        self.row            = row

        timestring  = ''
        depthstring = ''

        for time in self.times[:-1]:
            timestring = timestring + str(time) + ', '
        timestring = timestring + str(self.times[-1])

        for depth in self.depths[:-1]:
            depthstring = depthstring + str(depth) + ', '
        depthstring = depthstring + str(self.depths[-1])

        self.editwidget     = Button(frame, width = 5,  justify = 'center', text = 'Edit',   command = self.editchemicaldata, relief = FLAT, overrelief = RAISED)
        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.delchemicaldata,  relief = FLAT, overrelief = RAISED)
        self.namelabel      = Label( frame,  justify = 'center', text = self.name , font = 'Calibri 11')
        self.timelabel      = Label( frame,  justify = 'center', text = timestring )
        self.depthlabel     = Label( frame,  justify = 'center', text = depthstring)

        self.editwidget.grid(row  = row, column = 1, padx = 1 ,pady = 1)
        self.delwidget.grid( row  = row, column = 2, padx = 1 ,pady = 1)
        self.namelabel.grid( row  = row, column = 3, padx = 1, pady = 1, sticky = 'WE')
        self.timelabel.grid( row  = row, column = 4, padx = 1, pady = 1, sticky = 'WE')
        self.depthlabel.grid( row  = row, column = 5, padx = 2, pady = 1, sticky = 'WE')

        self.click_temp()

    def editchemicaldata(self):

        self.master.window.editplotdata(self.name)

    def delchemicaldata(self):

        self.master.window.deleteplotdata(self.name)

class ChemicalData:
        
    def __init__(self, name):
        """Constructor Method.  Provide all the fundamental properties of a chemical."""

        self.name    = name   #chemical name
        self.check   = 0

    def copy(self):

        chemicadata = ChemicalData(self.name)

        chemicadata.MW         = self.MW
        chemicadata.formula    = self.formula        
        chemicadata.temps      = [temp for temp in self.temps]
        
        chemicadata.density    = self.density.copy()
        chemicadata.Ref        = self.Ref.copy()
        chemicadata.Dw         = self.Dw.copy()
        chemicadata.Koc        = self.Koc.copy()
        chemicadata.Kow        = self.Kow.copy()
        chemicadata.Kdoc       = self.Kdoc.copy()
        chemicadata.Kf         = self.Kf.copy()
        chemicadata.N          = self.N.copy()

        return chemicadata

    def read_database(self, database):
        
        self.MW         = database.MW
        try:       self.temps      = [temp for temp in database.temps]
        except:    self.temps      = [temp for temp in database.temp]

        self.density    = database.density.copy()
        self.Dw         = database.Dw.copy()
        self.Koc        = database.Koc.copy()
        self.Kow        = database.Kow.copy()
        self.Kdoc       = database.Kdoc.copy()
        self.Kf         = database.Kf.copy()
        self.N          = database.N.copy()

        try:   self.Ref        = database.Ref.copy()
        except:
            self.Ref        = {}
            for temp in self.temps: self.Ref[temp] = ''

        try:    self.formula = database.formula
        except: self.formula = self.name

    def read_temperature(self, database, temp):

        self.temps.append(temp)

        self.density[temp]    = database.density[temp]
        self.Dw[temp]         = database.Dw[temp]
        self.Koc[temp]        = database.Koc[temp]
        self.Kow[temp]        = database.Kow[temp]
        self.Kdoc[temp]       = database.Kdoc[temp]
        self.Kf[temp]         = database.Kf[temp]
        self.N[temp]          = database.N[temp]

        self.Ref[temp]        = database.Ref[temp]


    def chemicalwidgets(self, frame, row, master):
        
        self.master         = master
        self.frame          = frame
        self.row            = row

        self.temp           = DoubleVar(value = self.temps[0])
        
        self.editwidget     = Button(frame, width = 5,  justify = 'center', text = 'Edit',   command = self.editchemicaldata, relief = FLAT, overrelief = RAISED)
        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.delchemicaldata,  relief = FLAT, overrelief = RAISED)
        self.namelabel      = Label(frame,  justify = 'center', text = self.name)
        self.formlabel      = Label(frame,  justify = 'center', text = self.formula , font = 'Calibri 11')
        self.templabel      = OptionMenu(frame, self.temp, *self.temps, command = self.click_temp)
                                                     
        self.editwidget.grid(row  = row, column = 1, padx = 1 ,pady = 1)
        self.delwidget.grid( row  = row, column = 2, padx = 1 ,pady = 1)
        self.namelabel.grid( row  = row, column = 3, padx = 1, pady = 1, sticky = 'WE')
        self.formlabel.grid( row  = row, column = 4, padx = 1, pady = 1, sticky = 'WE')
        self.templabel.grid( row  = row, column = 5, padx = 2, pady = 1, sticky = 'WE')
            
        self.click_temp()
        
    def editchemicaldata(self):
        
        self.master.window.editchemicaldata(self.name)

    def delchemicaldata(self):
        
        self.master.window.deletechemicaldata(self.name)
        
    def click_temp(self, event = None):

        try: 
            self.Dwlabel.grid_forget()
            self.Koclabel.grid_forget()
            self.Kdoclabel.grid_forget()
            self.Reflabel.grid_forget()
        except: pass

        self.Dwlabel        = Label(self.frame,  width = 10, justify = 'center', text = self.Dw[self.temp.get()])
        self.Koclabel       = Label(self.frame,  width = 10, justify = 'center', text = self.Koc[self.temp.get()])
        self.Kdoclabel      = Label(self.frame,  width = 10, justify = 'center', text = self.Kdoc[self.temp.get()])
        self.Reflabel       = Label(self.frame,              justify = 'center', text = self.Ref[self.temp.get()])

        self.Dwlabel.grid  (  row  = self.row, column = 6, padx = 1 ,pady = 1)
        self.Koclabel.grid (  row  = self.row, column = 7, padx = 1 ,pady = 1)
        self.Kdoclabel.grid(  row  = self.row, column = 8, padx = 1 ,pady = 1)
        self.Reflabel.grid(   row  = self.row, column = 9, padx = 1 ,pady = 1)

    def get_chemicaldata(self, databaseeditor):

        self.name    = databaseeditor.name.get()
        self.MW      = databaseeditor.MW.get()
        self.formula = databaseeditor.formula.get()
        
        self.temps   = [temp for temp in databaseeditor.temps]

        self.density = databaseeditor.densitys.copy()
        self.Ref     = databaseeditor.Refs.copy()
        self.Kow     = databaseeditor.Kows.copy()
        self.Dw      = databaseeditor.Dws.copy()
        self.Koc     = databaseeditor.Kocs.copy()
        self.Kdoc    = databaseeditor.Kdocs.copy()
        self.Kf      = databaseeditor.Kfs.copy()
        self.N       = databaseeditor.Ns.copy()

    def remove_chemicalwidgets(self):
        
        try:
            self.editwidget.grid_forget()
            self.delwidget.grid_forget()
            self.namelabel.grid_forget()
            self.formlabel.grid_forget()
            self.templabel.grid_forget()
            self.Dwlabel.grid_forget()
            self.Koclabel.grid_forget()
            self.Kdoclabel.grid_forget()
            self.Reflabel.grid_forget()
        except: pass

        self.master         = 0
        self.temp           = 0
        self.frame          = 0
        
        self.editwidget     = 0
        self.delwidget      = 0
        self.numberlabel    = 0
        self.namelabel      = 0
        self.templabel      = 0
        self.Dwlabel        = 0
        self.Koclabel       = 0
        self.Kdoclabel      = 0
        self.Reflabel      = 0

    def importedchemicalwidgets(self, frame, row, namewidth = 16):

        self.check          = IntVar(value = self.check)
        self.name_new       = StringVar(value = self.name)

        self.checkbutton    = Checkbutton(frame, variable = self.check)
        self.namelabel      = Label(frame,  width = namewidth, text = self.name)
        self.namewidget     = Entry(frame,  width = namewidth, justify = 'center', textvariable = self.name_new)

        self.checkbutton.grid(  row = row, column = 1,                 rowspan = 1, pady = 1)
        self.namelabel.grid(    row = row, column = 2,                 pady = 1)
        self.namewidget.grid(   row = row, column = 3, columnspan = 2, rowspan = 1, pady = 1)

    def remove_importedchemicalwidgets(self):

        try:
            self.checkbutton.grid_forget()
            self.namelabel.grid_forget()
            self.namewidget.grid_forget()
        except: pass

        self.master         = 0
        self.check          =  self.check.get()

    def get_importedchemical(self):

        self.check    =  self.check.get()
        self.name_new =  self.name_new.get()

        self.checkbutton = 0
        self.namelabel = 0
        self.namewidget = 0


    def selectchemicalwidgets(self, frame, row, master, namewidth = 16, refwidth = 16):

        self.master         = master

        self.check          = IntVar(value = self.check)

        self.temp           = DoubleVar(value = self.temps[0])
        self.ref_selected   = StringVar(value = self.Ref[self.temp.get()])

        self.checkbutton    = Checkbutton(frame, variable = self.check, command = self.select_checkbutton)
        self.namelabel      = Label(frame,  width = namewidth, text = self.name)
        self.tempwidget     = OptionMenu(frame, self.temp, *self.temps, command = self.select_click_temp)
        self.Reflabel       = Label(frame,  width = refwidth, textvariable = self.ref_selected)

        self.checkbutton.grid(  row = row, column = 1, pady = 1)
        self.namelabel.grid(    row = row, column = 2, pady = 1)
        self.tempwidget.grid(   row = row, column = 3, pady = 1, sticky = 'WE')
        self.Reflabel.grid(     row = row, column = 4, columnspan = 2, pady = 1, sticky = 'WE')

    def select_checkbutton(self):

        self.master.window.selectchemicaldata(self.name)

    def remove_selectchemicalwidgets(self):

        try:
            self.checkbutton.grid_forget()
            self.namelabel.grid_forget()
            self.tempwidget.grid_forget()
            self.Reflabel.grid_forget()
        except: pass

        self.master         = 0
        self.check          =  self.check.get()
        self.temp           =  self.temp.get()
        self.ref_selected   =  self.ref_selected.get()

    def get_selectchemical(self):

        self.check    =  self.check.get()
        self.name_new =  self.name_new.get()

        self.checkbutton = 0
        self.namelabel = 0
        self.namewidget = 0

    def select_click_temp(self, event = None):
        """Pulls up the contaminant properties after selecting a temperature."""

        self.ref_selected.set(self.Ref[self.temp.get()])



class ChemicalDatabase:
    """Stores chemical properties for CapSim."""

    def __init__(self, name, formula, number, MW):
        """Constructor Method.  Provide all the fundamental properties of a
        chemical."""

        self.name    = name   #chemical name
        self.formula = formula
        self.number  = number #database number
        self.MW      = MW     #molecular weight
        self.temps   = []     #temperatures for properties
        self.Kow     = {}     #log octanol-water partition coeff.
        self.density = {}     #density
        self.Ref     = {}
        self.Dw      = {}     #molecular diffusivity in water
        self.Koc     = {}     #log organic carbon partition coeff.
        self.Kdoc    = {}     #log colloidal OC partition coeff.
        self.Kf      = {}     #log organic carbon partition coeff.
        self.N       = {}     #log colloidal OC partition coeff.

    def add_properties(self, temp, Kow, density, Ref, Dw, Koc, Kdoc, Kf, N):
        """Add properties at a new temperature."""

        self.temps.append(temp)
        self.Kow[temp]     = Kow
        self.density[temp] = density
        self.Ref[temp]     = Ref
        self.Dw[temp]      = Dw
        self.Koc[temp]     = Koc
        self.Kdoc[temp]    = Kdoc
        self.Kf[temp]      = Kf
        self.N[temp]       = N

    def remove_properties(self, temp):
        """Remove properties at a temperature."""

        self.temps.remove(temp)
        del(self.Kow[temp])
        del(self.density[temp])
        del(self.Ref[temp])
        del(self.Dw[temp])
        del(self.Koc[temp])
        del(self.Kdoc[temp])
        del(self.Kf[temp])
        del(self.N[temp])

class SolidDatabase:
    
    def __init__(self, name, number, e, rho, foc, tort, sorp, Ref):
        """Constructor Method.  Provide all the fundamental properties of a
        chemical."""
        
        self.number  = number   #database number
        self.name    = name     #solid name
        self.e       = e        #solid porosity
        self.rho     = rho      #solid bulk density
        self.foc     = foc      #solid organic carbon fraction
        self.tort    = tort     #solid tortuosity correction
        self.sorp    = sorp     #solid sorption isotherm
        self.Ref     = Ref     #solid sorption isotherm

class Solid:
    """Stores solid properties for CapSim."""

    def __init__(self, number):

        self.number   = number
        self.check    = 0

    def read_database(self, database):
        
        self.name      = database.name
        self.e         = database.e
        self.rho       = database.rho
        self.foc       = database.foc
        self.tort      = database.tort
        self.sorp      = database.sorp

        try:    self.Ref        = database.Ref
        except: self.Ref        = ''

    def copy(self):
        """Copy method. Copies everything needed to a new Chemical instance."""

        solid = Solid(self.number)

        solid.number    = self.number
        solid.name      = self.name
        solid.e         = self.e
        solid.rho       = self.rho 
        solid.foc       = self.foc 
        solid.tort      = self.tort
        solid.sorp      = self.sorp
        solid.Ref       = self.Ref

        return solid

    def import_coefficients(self, solid):

        self.name      = solid.name_new
        self.e         = solid.e
        self.rho       = solid.rho
        self.foc       = solid.foc
        self.tort      = solid.tort
        self.sorp      = solid.sorp
        self.Ref       = solid.Ref

    def propertieswidget(self, frame, row, master):
    
        self.master       = master
        self.row          = row

        self.editwidget  = Button(frame, width = 5,  justify = 'center', text = 'Edit',   command = self.editsolid, relief = FLAT, overrelief = RAISED)
        self.delwidget   = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.delsolid, relief = FLAT, overrelief = RAISED)
        self.numberlabel = Label( frame, width = 2,  justify = 'center', text = self.number)
        self.namelabel   = Label( frame,             justify = 'center', text = self.name)
        self.elabel      = Label( frame, width = 8,  justify = 'center', text = self.e)
        self.rhowlabel   = Label( frame, width = 10, justify = 'center', text = self.rho)
        self.foclabel    = Label( frame, width = 10, justify = 'center', text = self.foc)
        self.tortlabel   = Label( frame, width = 18, justify = 'center', text = self.tort)
        self.sorplabel   = Label( frame, width = 18, justify = 'center', text = self.sorp)
        self.reflabel    = Label( frame,             justify = 'center', text = self.Ref)

        self.editwidget.grid( row  = row, column = 1, padx = 1 ,pady = 1)
        self.delwidget.grid(  row  = row, column = 2, padx = 1 ,pady = 1)
        self.numberlabel.grid(row  = row, column = 3, padx = 1, pady = 1, sticky = 'WE')
        self.namelabel.grid(  row  = row, column = 4, padx = 1, pady = 1, sticky = 'WE')
        self.elabel.grid(     row  = row, column = 5, padx = 1, pady = 1, sticky = 'WE')
        self.rhowlabel.grid(  row  = row, column = 6, padx = 1 ,pady = 1)
        self.foclabel.grid (  row  = row, column = 7, padx = 1 ,pady = 1)
        self.tortlabel.grid(  row  = row, column = 8, padx = 1 ,pady = 1)
        self.sorplabel.grid(  row  = row, column = 9, padx = 1 ,pady = 1)
        self.reflabel.grid(   row  = row, column = 10, padx = 1 ,pady = 1)

    def editsolid(self):
        
        self.master.window.editsolid(self.number)

    def delsolid(self):
        
        self.master.window.deletesolid(self.number)
        
    def get_solid(self, solideditor):
        
        self.name = solideditor.name.get()
        self.e    = solideditor.e.get()
        self.rho  = solideditor.rho.get()
        self.foc  = solideditor.foc.get()
        self.tort = solideditor.tort.get()
        self.sorp = solideditor.sorp.get()
        self.Ref  = solideditor.Ref.get()

    def remove_propertieswidget(self):

        self.editwidget.grid_forget()
        self.delwidget.grid_forget()
        self.numberlabel.grid_forget()
        self.namelabel.grid_forget()
        self.elabel.grid_forget()
        self.rhowlabel.grid_forget()
        self.foclabel.grid_forget()
        self.tortlabel.grid_forget()
        self.sorplabel.grid_forget()
        self.reflabel.grid_forget()

        self.row          = 0
        self.master       = 0
        self.editwidget   = 0
        self.delwidget    = 0
        self.numberlabel  = 0              
        self.namelabel    = 0
        self.elabel       = 0
        self.rhowlabel    = 0
        self.foclabel     = 0
        self.tortlabel    = 0
        self.sorplabel    = 0
        self.reflabel    = 0

        
    def importedsolidwidgets(self, frame, row, namewidth = 16):

        self.check          = IntVar(value = self.check)
        self.name_new       = StringVar(value = self.name)

        self.checkbutton    = Checkbutton(frame, variable = self.check)
        self.namelabel      = Label(frame,  width = namewidth, text = self.name)
        self.namewidget     = Entry(frame,  width = namewidth, justify = 'center', textvariable = self.name_new)

        self.checkbutton.grid(  row = row, column = 1, pady = 1)
        self.namelabel.grid(    row = row, column = 2, pady = 1)
        self.namewidget.grid(   row = row, column = 3, columnspan = 2, pady = 1)

    def remove_importedsolidwidgets(self):

        try:
            self.checkbutton.grid_forget()
            self.namelabel.grid_forget()
            self.namewidget.grid_forget()
        except: pass

        self.master         = 0
        self.check          =  self.check.get()

    def get_importedsolid(self):

        self.check    =  self.check.get()
        self.name_new =  self.name_new.get()

        self.checkbutton = 0
        self.namelabel = 0
        self.namewidget = 0
