#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Chemical, ChemicalData
from capsim_functions    import get_superfont
from database            import Database

import tkFont

class ChemicalEditor:
    """Gets the contaminant properties."""
    
    def __init__(self, master, system, chemical, chemicals, database, editflag):
        
        """Constructor method.  Defines the parameters to be obtained in this window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.frame     = Frame(master.frame)
        self.tframe    = Frame(master.tframe)
        self.bframe    = Frame(master.bframe)
        self.system    = system
        self.database  = database
        self.top       = None                   #flag for existence of toplevel#
        self.tkfont    = tkFont.Font(font = system.fonttype)

        self.soluableflag = chemical.soluable
        self.editflag     = editflag
        self.cancelflag   = 0
        self.chemicals    = chemicals
        self.diffunit     = system.diffunit
        self.diffunits    = system.diffunits
        
        if self.soluableflag == 1:
            self.database  = database
            self.chemical  = chemical

            self.name         = StringVar(value = '')
            self.formula      = StringVar(value = '')
            self.MW           = DoubleVar(value = 0)
            self.temp         = DoubleVar(value = 0)
            self.Dw           = DoubleVar(value = 0)
            self.Ref          = StringVar(value = '')
            self.Koc          = DoubleVar(value = 0)
            self.Kdoc         = DoubleVar(value = 0)
            self.Kf           = DoubleVar(value = 0)
            self.N            = DoubleVar(value = 0)

            if editflag == 1:                       #Detemine whether the chemical is added or edited

                self.name.set(self.chemical.name)
                self.formula.set(self.chemical.formula)
                self.MW.set(self.chemical.MW)
                self.temp.set(self.chemical.temp)
                self.Dw.set(self.chemical.Dw)
                self.Koc.set(self.chemical.Koc)
                self.Kdoc.set(self.chemical.Kdoc)
                self.Ref.set(self.chemical.Ref)
                self.Kf.set(self.chemical.Kf)
                self.N.set(self.chemical.N)
        else:
            self.name         = StringVar(value = ' ')
            self.formula      = StringVar(value = ' ')
            self.MW           = DoubleVar(value = 100)
            self.temp         = DoubleVar(value = 0)
            self.Dw           = DoubleVar(value = 0)
            self.Koc          = DoubleVar(value = 0)
            self.Kdoc         = DoubleVar(value = 0)
            self.Kf           = DoubleVar(value = 0)
            self.N            = DoubleVar(value = 0)

            if editflag == 1:                       #Detemine whether the chemical is added or edited
                self.name.set(chemical.name)

    def make_widgets(self):
        """Make the widgets for the window."""
        
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.tframe, text = ' Please provide the following chemical properties:                    ')
        
        self.blankcolumn  = Label(self.frame,  text =' ', width = 2)
        self.namecolumn   = Label(self.frame,  text =' ', width = 20)
        self.MWcolumn     = Label(self.frame,  text =' ', width = 12)
        self.tempcolumn   = Label(self.frame,  text =' ', width = 10)
        self.Dwcolumn     = Label(self.frame,  text =' ', width = 18)
        self.Koccolumn    = Label(self.frame,  text =' ', width = 18)
        self.Kdoccolumn   = Label(self.frame,  text =' ', width = 18)
        self.Refcolumn    = Label(self.frame,  text =' ', width = 20)
        self.Rightcolumn  = Label(self.frame,  text =' ', width = 2)

        self.namelabel    = Label(self.frame,  text = 'Chemical name')
        self.MWlabel      = Label(self.frame,  text = 'Molecular\n weight')
        self.templabel    = Label(self.frame,  text = 'Temperature')
        self.Dwlabel      = Label(self.frame,  text = 'Molecular diffusivity\n in water')
        self.Koclabel     = Label(self.frame,  text = 'Organic carbon\n partition coefficient')
        self.Kdoclabel    = Label(self.frame,  text = 'Dissolved organic carbon\n partition coefficient')
        self.Reflabel     = Label(self.frame,  text = 'Reference')

        self.tempunits    = Label(self.frame,  text = unichr(176) + 'C')
        self.Dwunits      = Label(self.frame,  text = self.diffunit)
        self.Kocunits     = Label(self.frame,  text = 'log(L/kg)')
        self.Kdocunits    = Label(self.frame,  text = 'log(L/kg)')

        self.importbutton = Button(self.frame, text = 'From Database', width = 20, command = self.importchemical)
        self.okbutton     = Button(self.frame, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')

        #show the widgets on the grid
        self.instructions.grid(row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')
        
        self.blankcolumn.grid(  row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)        
        self.namecolumn.grid(   row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.MWcolumn.grid(     row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.tempcolumn.grid(   row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwcolumn.grid(     row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Koccolumn.grid(    row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoccolumn.grid(   row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Refcolumn.grid(    row    = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)
        self.Rightcolumn.grid(  row    = 1, column = 8, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.MWlabel.grid(      row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.templabel.grid(    row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwlabel  .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Koclabel .grid(    row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoclabel.grid(    row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Reflabel.grid(     row    = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)

        self.tempunits.grid(    row    = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwunits.grid  (    row    = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Kocunits.grid (    row    = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdocunits.grid(    row    = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)

        if self.soluableflag == 1:
            if self.editflag == 0:
                self.namewidget = Entry(self.frame, width = 18, justify = 'center', textvariable = self.name)
                self.tempwidget = Entry(self.frame, width = 10, justify = 'center', textvariable = self.temp)
            else:
                self.namewidget = Label(self.frame, width = 18, justify = 'center', textvariable = self.name)
                self.tempwidget = Label(self.frame, width = 10, justify = 'center', textvariable = self.temp)

            self.Dwwidget   = Entry(self.frame, width = 16, justify = 'center', textvariable = self.Dw)
            self.MWwidget   = Entry(self.frame, width = 10, justify = 'center', textvariable = self.MW)
            self.Kocwidget  = Entry(self.frame, width = 16, justify = 'center', textvariable = self.Koc)
            self.Kdocwidget = Entry(self.frame, width = 16, justify = 'center', textvariable = self.Kdoc)
            self.Refwidget  = Entry(self.frame, width = 18, justify = 'center', textvariable = self.Ref)

            self.namewidget.grid(   row    = 4, column = 1, padx = 2, pady = 1)
            self.MWwidget.grid(     row    = 4, column = 2, padx = 2, pady = 1)
            self.tempwidget.grid(   row    = 4, column = 3, padx = 2, pady = 1)
            self.Dwwidget.grid  (   row    = 4, column = 4, padx = 2 ,pady = 1)
            self.Kocwidget.grid (   row    = 4, column = 5, padx = 2 ,pady = 1)
            self.Kdocwidget.grid(   row    = 4, column = 6, padx = 2 ,pady = 1)
            self.Refwidget.grid(    row    = 4, column = 7, padx = 2 ,pady = 1)

        else:
            self.namewidget = Entry(self.frame, width = 18, justify = 'center', textvariable = self.name)
            self.Dwwidget   = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')
            self.Kocwidget  = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')
            self.Kdocwidget = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')

            self.namewidget.grid(   row    = 4, column = 1, padx = 2, pady = 1)
            self.Dwwidget.grid  (   row    = 4, column = 3, padx = 2 ,pady = 1)
            self.Kocwidget.grid (   row    = 4, column = 4, padx = 2 ,pady = 1)
            self.Kdocwidget.grid(   row    = 4, column = 5, padx = 2 ,pady = 1)

        self.blank1.grid(       row    = 5)
        if self.editflag == 0:  self.importbutton.grid( row    = 6, columnspan = 11)
        self.okbutton.grid(     row    = 7, columnspan = 11)
        self.cancelbutton.grid( row    = 8, columnspan = 11)
        self.blank2.grid(       row    = 9)
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton

        if int((self.tkfont.measure(self.Ref.get()) + 10)*1.1424219345/8)+1 > 18:
            self.Refwidget.config(width = int((self.tkfont.measure(self.Ref.get()) + 10)*1.1424219345/8)+3)
        if int((self.tkfont.measure(self.name.get())+ 10)*1.1424219345/8)+1 > 18:
            self.namewidget.config(width = int((self.tkfont.measure(self.name.get()) + 10)*1.1424219345/8)+3)

        self.master.geometry()
        self.master.center()

    def importchemical(self):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ChemicalImporter(self.top, self.system, self.database))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.updatechemical(self.top.window)

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

    def updatechemical(self, window):

        self.name.set(      window.name.get())
        self.formula.set(   window.formula.get())
        self.MW.set(        window.MW.get())
        self.temp.set(      window.temp.get())
        self.Koc.set(       window.Koc.get())
        self.Kdoc.set(      window.Kdoc.get())
        self.Ref.set(       window.Ref.get())
        self.Kf.set(        window.Kf.get())
        self.N.set(         window.N.get())

        if self.diffunit == self.diffunits[0]:   self.Dw.set(window.Dw.get())
        elif self.diffunit == self.diffunits[1]:
            Dw = window.Dw.get() * 86400 * 365
            if Dw > 1:   self.Dw.set(round(Dw, 2))
            else:
                i = 2
                while Dw/100 < 0.1**i:
                    i = i + 1
                self.Dw.set(round(Dw, i))

        self.frame.update()

        if int((self.tkfont.measure(self.Ref.get()) + 10)*1.1424219345/8)+1 > 20:
            self.Refwidget.config(width = int((self.tkfont.measure(self.Ref.get()) + 10)*1.1424219345/8)+3)
        if int((self.tkfont.measure(self.name.get())+ 10)*1.1424219345/8)+1 > 20:
            self.namewidget.config(width = int((self.tkfont.measure(self.name.get()) + 10)*1.1424219345/8)+3)
        self.master.geometry()
        self.master.center()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the total number of chemicals in database."""

        if self.editflag == 0:
           check =[(chemical.name == self.name.get()) for chemical in self.chemicals[0:-1]]
        else:
            check = [0]

        if self.master.window.top is not None: self.master.open_toplevel()
        elif sum(check) >= 1: self.chemicals_error()
        elif self.name.get() == '' or self.name.get().count(' ') == len(self.name.get()): self.name_error()
        elif self.Dw.get() == 0: self.Dw_error()
        else: self.master.tk.quit()
        
    def chemicals_error(self):

        tkmb.showerror(title = self.version, message = 'This chemical has already been selected!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def name_error(self):

        tkmb.showerror(title = self.version, message = 'Please input the name for the chemical!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()

    def Dw_error(self):

        tkmb.showerror(title = self.version, message = 'The diffusivity of the chemical can not be zero, please correct!')
        self.focusbutton = self.okbutton
        self.master.tk.lift()


    def Cancel(self):
        
        try:
            self.name.set(self.chemical.name)
            self.MW.set(self.chemical.MW.get())
            self.formula.set(self.chemical.formula.get())
            self.temp.set(self.chemical.temp.get())
            self.Dw.set(self.chemical.Dw.get())
            self.Koc.set(self.chemical.Koc.get())
            self.Kdoc.set(self.chemical.Kdoc.get())
            self.Ref.set(self.chemical.Ref.get())
            self.Kf.set(self.chemical.Kf.get())
            self.N.set(self.chemical.N.get())
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
    
class ChemicalImporter:

    def __init__(self, master, system, database):
        """The constructor method."""

        self.version       = system.version
        self.fonttype      = system.fonttype
        self.sfont         = get_superfont(self.fonttype)
        self.master        = master
        self.frame         = Frame(master.frame)
        self.tframe        = Frame(master.tframe)
        self.bframe        = Frame(master.bframe)
        self.tkfont        = tkFont.Font(font = system.fonttype)

        self.chemicals_list = database.keys()
        self.chemicals_list.sort()

        self.name         = StringVar()
        self.formula      = StringVar()
        self.MW           = DoubleVar()
        self.temp         = DoubleVar(value = 0)
        self.Dw           = DoubleVar(value = 0)
        self.Ref          = StringVar(value = 0)
        self.Koc          = DoubleVar(value = 0)
        self.Kdoc         = DoubleVar(value = 0)
        self.Kf           = DoubleVar(value = 0)
        self.N            = DoubleVar(value = 0)


        self.importedchemicals = {}
        for name in self.chemicals_list:
            self.importedchemicals[name] = ChemicalData(name)
            self.importedchemicals[name].read_database(database[name])

        self.name_width    = 10
        self.ref_width     = 10

        for chemical_name in self.chemicals_list:
            if (self.tkfont.measure(chemical_name) + 10) > self.name_width: self.name_width = self.tkfont.measure(chemical_name) + 10
            for temp in self.importedchemicals[chemical_name].temps:
                if (self.tkfont.measure(self.importedchemicals[chemical_name].Ref[temp]) + 10) > self.name_width:
                    self.name_width = self.tkfont.measure(self.importedchemicals[chemical_name].Ref[temp]) + 10

        if self.name_width < 150: self.name_width = 150
        if self.ref_width <  150: self.ref_width = 150


        self.cancelflag      = 0

        self.sname     = StringVar(self.frame, value = '')

    def make_widgets(self):

        self.instructions     = Label( self.tframe,  text = 'Please select the chemical you would like to add       ')

        self.leftcolumn       = Label( self.tframe,  text = ' ', width = 2)
        self.checkcolumn      = Label( self.tframe,  text = ' ', width = 5)
        self.orinamecolumn    = Label( self.tframe,  text = ' ', width = int(self.name_width*1.1424219345/8)+1)
        self.tempcolumn       = Label( self.tframe,  text = ' ', width = 15)
        self.ref1column       = Label( self.tframe,  text = ' ', width = int(self.ref_width*1.1424219345/8/2)+1)
        self.ref2column       = Label( self.tframe,  text = ' ', width = int(self.ref_width*1.1424219345/8/2)+1)
        self.rightcolumn      = Label( self.tframe,  text = ' ', width = 2)

        self.search_label     = Label( self.tframe,  text          = 'Search:')
        self.search_entry     = Entry( self.tframe,  textvariable  = self.sname)

        self.namelabel        = Label( self.tframe,  text = 'Name')
        self.templabel        = Label( self.tframe,  text = 'Temperature')
        self.reflabel         = Label( self.tframe,  text = 'Reference')

        self.botleftcolumn    = Label( self.frame,   text = ' ', width = 2)
        self.botcheckcolumn   = Label( self.frame,   text = ' ', width = 5)
        self.botorinamecolumn = Label( self.frame,   text = ' ', width = int(self.name_width*1.1424219345/8)+1)
        self.bottempcolumn    = Label( self.frame,   text = ' ', width = 15)
        self.botref1column    = Label( self.frame,   text = ' ', width = int(self.ref_width*1.1424219345/8/2)+1)
        self.botref2column    = Label( self.frame,   text = ' ', width = int(self.ref_width*1.1424219345/8/2)+1)
        self.botrightcolumn   = Label( self.frame,   text = ' ', width = 2)

        self.importbutton     = Button(self.bframe,  text = 'Import',         command = self.OK,             width = 20)
        self.cancelbutton     = Button(self.bframe,  text = 'Cancel',         command = self.cancel,         width = 20)

        self.blank1           = Label(self.tframe, text = ' ')
        self.blank2           = Label(self.frame,  text = ' ')
        self.blank3           = Label(self.bframe, text = ' ')
        self.blank4           = Label(self.bframe, text = ' ')

        #show the widgets on the grid (top to bottom and left to right)

        self.instructions.grid(     row = 0, columnspan = 5, sticky = 'W', padx = 8)

        self.leftcolumn.grid(       row = 1, column = 0, sticky = 'WE')
        self.checkcolumn.grid(      row = 1, column = 1, sticky = 'WE')
        self.orinamecolumn.grid(    row = 1, column = 2, sticky = 'WE')
        self.tempcolumn.grid(       row = 1, column = 3, sticky = 'WE')
        self.ref1column.grid(       row = 1, column = 4, sticky = 'WE')
        self.ref2column.grid(       row = 1, column = 5, sticky = 'WE')
        self.rightcolumn.grid(      row = 1, column = 6, sticky = 'WE')

        self.search_label.grid(     row = 2, column = 1, sticky = 'E'                 , padx = 4)
        self.search_entry.grid(     row = 2, column = 2, columnspan = 4, sticky = 'WE', padx = 4)

        self.blank1.grid(row = 3)

        self.namelabel.grid(        row = 4, column = 2,                 sticky = 'WE')
        self.templabel.grid(        row = 4, column = 3,                 sticky = 'WE')
        self.reflabel.grid(         row = 4, column = 4, columnspan = 2, sticky = 'WE')

        self.botleftcolumn.grid(       row = 1, column = 0, sticky = 'WE')
        self.botcheckcolumn.grid(      row = 1, column = 1, sticky = 'WE')
        self.botorinamecolumn.grid(    row = 1, column = 2, sticky = 'WE')
        self.bottempcolumn.grid(       row = 1, column = 3, sticky = 'WE')
        self.botref1column.grid(       row = 1, column = 4, sticky = 'WE')
        self.botref2column.grid(       row = 1, column = 5, sticky = 'WE')
        self.botrightcolumn.grid(      row = 1, column = 6, sticky = 'WE')

        self.searchname()

        self.sname.trace('w', self.searchname)


    def searchname(self, event = None, *args):

        row = 2

        for name in self.chemicals_list:
            try: self.importedchemicals[name].remove_selectchemicalwidgets()
            except: pass

        if self.sname.get() == '':
            for name in self.chemicals_list:
                self.importedchemicals[name].selectchemicalwidgets(self.frame, row = row, master = self.master, namewidth=int(self.name_width*1.1424219345/8)+1, refwidth = int(self.ref_width*1.1424219345/8)+1)
                row = row + 1
        else:
            for name in self.chemicals_list:
                if name.lower()[:len(self.sname.get())].count(self.sname.get().lower())>= 1:
                    self.importedchemicals[name].selectchemicalwidgets(self.frame, row = row, master = self.master, namewidth=int(self.name_width*1.1424219345/8)+1, refwidth = int(self.ref_width*1.1424219345/8)+1)
                    row = row + 1
                else:
                    self.importedchemicals[name].check = IntVar(value = self.importedchemicals[name].check)

        self.blank2.grid(row = row)

        row = 2

        self.blank3.grid(row = row)
        row = row + 1
        self.importbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.cancelbutton.grid(row = row,column = 0, columnspan = 5, pady = 1)
        row = row + 1
        self.blank4.grid(      row = row)

        self.cancelbutton.bind('<Return>', self.cancel)

        self.focusbutton = self.cancelbutton

    def selectchemicaldata(self, name):

        for othername in self.chemicals_list:
            if othername <> name:
                try: self.importedchemicals[othername].check.set(0)
                except: pass

    def cancelname(self, event = None):

        self.sname.set('')
        self.searchname()

    def OK(self, event = None):

        for name in self.chemicals_list:
            if  self.importedchemicals[name].check.get() == 1:

                self.name.set(name)
                self.formula.set(self.importedchemicals[name].formula)
                self.MW.set(self.importedchemicals[name].MW)
                self.temp.set(self.importedchemicals[name].temp.get())
                self.Dw.set(self.importedchemicals[name].Dw[self.temp.get()])
                self.Ref.set(self.importedchemicals[name].Ref[self.temp.get()])
                self.Koc.set(self.importedchemicals[name].Koc[self.temp.get()])
                self.Kdoc.set(self.importedchemicals[name].Kdoc[self.temp.get()])
                self.Kf.set(self.importedchemicals[name].Kf[self.temp.get()])
                self.N.set(self.importedchemicals[name].N[self.temp.get()])

        for name in self.chemicals_list:
            try: self.importedchemicals[name].remove_selectchemicalwidgets()
            except: pass

        self.frame.quit()

    def cancel(self, event = None):

        self.cancelflag = 1
        self.frame.quit()


class ChemicalDeleter:
    
    def __init__(self, master, system, chemical):
        
        """Constructor method. Defines the parameters to be obtained in this window."""
        
        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.frame     = Frame(master.frame)
        self.tframe    = Frame(master.tframe)
        self.bframe    = Frame(master.bframe)
        self.top       = None                   #flag for existence of toplevel#

        self.soluableflag = chemical.soluable
        self.name         = StringVar(value = chemical.name)
        self.MW           = DoubleVar(value = chemical.MW)
        self.formula      = StringVar(value = chemical.formula)
        self.temp         = DoubleVar(value = chemical.temp)        
        self.Dw           = DoubleVar(value = chemical.Dw)
        self.Koc          = DoubleVar(value = chemical.Koc)
        self.Kdoc         = DoubleVar(value = chemical.Kdoc)
        self.Ref          = StringVar(value = chemical.Ref)
        self.Kf           = DoubleVar(value = chemical.Kf)
        self.N            = DoubleVar(value = chemical.N)

        self.chemical     = chemical

        self.cancelflag = 0

    def make_widgets(self):
    
        self.bgcolor      = self.frame.cget('bg')
        self.instructions = Label(self.frame, text = ' Are you sure to delete the following chemical?                   ')
                
        self.namelabel    = Label(self.frame,  text = 'Chemical name')
        self.MWlabel      = Label(self.frame,  text = 'Molecular\n weight')
        self.templabel    = Label(self.frame,  text = 'Temperature')
        self.Dwlabel      = Label(self.frame,  text = 'Molecular diffusivity\n in water')
        self.Koclabel     = Label(self.frame,  text = 'Organic carbon\n partition coefficient')
        self.Kdoclabel    = Label(self.frame,  text = 'Dissolved organic carbon\n partition coefficient')
        self.Reflabel     = Label(self.frame,  text = 'Reference')

        self.tempunits    = Label(self.frame,  text = unichr(176) + 'C')
        self.Dwunits      = Label(self.frame,  text = u'cm\u00B2/s')
        self.Kocunits     = Label(self.frame,  text = 'log(L/kg)')
        self.Kdocunits    = Label(self.frame,  text = 'log(L/kg)')

        self.namewidget = Label(self.frame, width = 20, justify = 'center', textvariable = self.name)
        if self.soluableflag == 1:
            self.tempwidget = Label(self.frame, width = 10, justify = 'center', textvariable = self.temp)
            self.MWwidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.MW)
            self.Dwwidget   = Label(self.frame, width = 16, justify = 'center', textvariable = self.Dw)
            self.Kocwidget  = Label(self.frame, width = 16, justify = 'center', textvariable = self.Koc)
            self.Kdocwidget = Label(self.frame, width = 16, justify = 'center', textvariable = self.Kdoc)
            self.Refwidget  = Label(self.frame, width = 16, justify = 'center', textvariable = self.Ref)
        else:
            self.tempwidget = Label(self.frame, width = 10, justify = 'center', text = ' ')
            self.Dwwidget   = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')
            self.Kocwidget  = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')
            self.Kdocwidget = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')

        self.insoluablestate = Label(self.frame, width = 16, justify = 'center', text = 'Not applicable')
        
        #show the widgets on the grid
        self.blankcolumn  = Label(self.frame,  text =' ', width = 2)
        self.namecolumn   = Label(self.frame,  text =' ', width = 20)
        self.MWcolumn     = Label(self.frame,  text =' ', width = 18)
        self.tempcolumn   = Label(self.frame,  text =' ', width = 10)
        self.Dwcolumn     = Label(self.frame,  text =' ', width = 18)
        self.Koccolumn    = Label(self.frame,  text =' ', width = 18)
        self.Kdoccolumn   = Label(self.frame,  text =' ', width = 18)
        self.Refcolumn    = Label(self.frame,  text =' ', width = 18)

        self.deletebutton = Button(self.frame, text = 'Delete', width = 20, command = self.Delete)
        self.cancelbutton = Button(self.frame, text = 'Cancel', width = 20, command = self.Cancel)
        self.blank1       = Label(self.frame, text = ' ')
        self.blank2       = Label(self.frame, text = ' ')

        self.instructions.grid(row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')
        
        self.blankcolumn.grid(  row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)        
        self.namecolumn.grid(   row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.MWcolumn.grid(     row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.tempcolumn.grid(   row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwcolumn.grid(     row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Koccolumn.grid(    row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoccolumn.grid(   row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Refcolumn.grid(    row    = 1, column = 7, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(    row    = 2, column = 1, sticky = 'WE', padx = 4, pady = 1)
        self.MWlabel.grid(      row    = 2, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.templabel.grid(    row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwlabel  .grid(    row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Koclabel .grid(    row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdoclabel.grid(    row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)
        self.Reflabel.grid(     row    = 2, column = 7, sticky = 'WE', padx = 1, pady = 1)

        self.tempunits.grid(    row    = 3, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.Dwunits.grid  (    row    = 3, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.Kocunits.grid (    row    = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.Kdocunits.grid(    row    = 3, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.namewidget.grid(   row    = 4, column = 1, padx = 2, pady = 1, sticky = 'WE')
        self.MWwidget.grid(     row    = 4, column = 2, padx = 2, pady = 1, sticky = 'WE')
        self.tempwidget.grid(   row    = 4, column = 3, padx = 2, pady = 1, sticky = 'WE')
        self.Dwwidget.grid  (   row    = 4, column = 4, padx = 2 ,pady = 1)
        self.Kocwidget.grid (   row    = 4, column = 5, padx = 2 ,pady = 1)
        self.Kdocwidget.grid(   row    = 4, column = 6, padx = 2 ,pady = 1)
        self.Refwidget.grid(    row    = 4, column = 7, padx = 2 ,pady = 1)

        self.blank1.grid(       row    = 5)
        self.deletebutton.grid(     row    = 6, columnspan = 11)
        self.cancelbutton.grid( row    = 7, columnspan = 11)
        self.blank2.grid(       row    = 8)
        self.deletebutton.bind('<Return>', self.Delete)
        self.focusbutton = self.deletebutton
        
    def Delete(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""
        
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def Cancel(self):
        
        try:
            self.name.set(self.chemical.name)
            self.temp.set(self.chemical.temp)
            self.MW.set(self.chemical.MW)
            self.formula.set(self.chemical.formula)
            self.Dw.set(self.chemical.Dw)
            self.Koc.set(self.chemical.Koc)
            self.Kdoc.set(self.chemical.Kdoc)
            self.Ref.set(self.chemical.Ref)
            self.Kf.set(self.chemical.Kf)
            self.N.set(self.chemical.N)
        except: self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
