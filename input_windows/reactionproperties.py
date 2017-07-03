#!/usr/bin/env python
#
#This file is used to make the GUI for the general layer properties of the cap. 

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, \
                                DoubleVar, StringVar, IntVar
from capsim_functions    import get_superfont
from capsim_object_types import CapSimWindow, Reaction
from reactioneditor      import ReactionEditor, ReactionDeleter

import tkMessageBox as tkmb

class ReactionProperties:
    """Gets the model types for each of the layers in the system."""

    def __init__(self, master, system):
        """Constructor method. Used to defines the layers."""
        
        self.master         = master
        self.system         = system
        self.version        = system.version
        self.fonttype       = system.fonttype
        self.formulatype    = system.formulatype
        self.superfont      = get_superfont(self.fonttype)
        self.subfont        = get_superfont(self.formulatype)
        self.tframe         = Frame(master.tframe)
        self.frame          = Frame(master.frame)
        self.bframe         = Frame(master.bframe)
        self.bgcolor        = self.frame.cget('bg')
        self.top            = None

        self.chemicals      = system.chemicals
        
        if master.master is None: self.defaults = 1

        if system.reactions is None: self.reactions      = []
        else:                        self.reactions      = system.reactions
        
    def make_widgets(self):
        """Makes the widgets for the GUI."""

        self.instructions   = Label(self.tframe,  text  = 'Please input the kinetic processes in the system:        ')

        self.blankcolumn    = Label(self.tframe,  text = '', font = 'courier 10',  width = 1 )
        self.editcolumn     = Label(self.tframe,  text = '', font = 'courier 10',  width = 6 )
        self.delcolumn      = Label(self.tframe,  text = '', font = 'courier 10',  width = 6 )
        self.numbercolumn   = Label(self.tframe,  text = '', font = 'courier 10',  width = 5 )
        self.namecolumn     = Label(self.tframe,  text = '', font = 'courier 10',  width = 15)
        self.equationcolumn = Label(self.tframe,  text = '', font = 'courier 10',  width = 20)
        self.ratecolumn     = Label(self.tframe,  text = '', font = 'courier 10',  width = 10)
        self.endcolumn      = Label(self.tframe,  text = '', font = 'courier 10',  width = 2)
        
        self.numberlabel    = Label(self.tframe,  text = 'Number')
        self.namelabel      = Label(self.tframe,  text = 'Name')
        self.equationlabel  = Label(self.tframe,  text = 'Chemical equation')
        self.ratelabel      = Label(self.tframe,  text = 'Rate equation')

        self.botblankcolumn    = Label(self.frame,  text = '', font = 'courier 10',  width = 1 )
        self.boteditcolumn     = Label(self.frame,  text = '', font = 'courier 10',  width = 6 )
        self.botdelcolumn      = Label(self.frame,  text = '', font = 'courier 10',  width = 6 )
        self.botnumbercolumn   = Label(self.frame,  text = '', font = 'courier 10',  width = 5 )
        self.botnamecolumn     = Label(self.frame,  text = '', font = 'courier 10',  width = 15)
        self.botequationcolumn = Label(self.frame,  text = '', font = 'courier 10',  width = 20)
        self.botratecolumn     = Label(self.frame,  text = '', font = 'courier 10',  width = 10)
        self.botendcolumn      = Label(self.frame,  text = '', font = 'courier 10',  width = 2)

        self.addwidget      = Button(self.bframe, text = 'Add reactions', command = self.addreaction, width = 20)
        self.blank1         = Label (self.bframe, text = ' ')
        self.blank2         = Label (self.bframe, text = ' ')
        #show the widgets on the grid

        self.instructions.grid( row = 0, column = 0, padx = 8, columnspan = 6, sticky = 'W')

        self.blankcolumn.grid(      row = 1, column = 0, padx = 1, sticky = 'WE', pady = 1)
        self.editcolumn.grid(       row = 1, column = 1, padx = 1, sticky = 'WE', pady = 1)
        self.delcolumn.grid(        row = 1, column = 2, padx = 1, sticky = 'WE', pady = 1)
        self.numbercolumn.grid(     row = 1, column = 3, padx = 4, sticky = 'WE')
        self.namecolumn.grid(       row = 1, column = 4, padx = 4, sticky = 'WE')
        self.equationcolumn.grid(   row = 1, column = 5, padx = 4, sticky = 'WE')
        self.ratecolumn.grid(       row = 1, column = 6, padx = 4, sticky = 'WE')
        self.endcolumn.grid(        row = 1, column = 7, padx = 4, sticky = 'WE')

        self.numberlabel.grid(      row = 2, column = 3, padx = 1, sticky = 'WE', pady = 4)
        self.namelabel.grid(        row = 2, column = 4, padx = 1, sticky = 'WE', pady = 4)
        self.equationlabel.grid(    row = 2, column = 5, padx = 1, sticky = 'WE', pady = 4)
        self.ratelabel.grid(        row = 2, column = 6, padx = 1, sticky = 'WE', pady = 4)

        self.updatereactions()
        
    def updatereactions(self):
        
        self.addwidget.grid_forget()
        self.blank1.grid_forget()
        self.blank2.grid_forget()

        namelabellength         = 15
        equationlabellength     = 20
        ratelabellength         = 10

        row = 4
        
        for reaction in self.reactions:
            try: reaction.remove_propertieswidgets()
            except:pass
            reaction.number = self.reactions.index(reaction) + 1
            reaction.propertieswidgets(self.frame, row, self.master, self.formulatype, self.superfont, self.subfont, self.bgcolor)
            row = row + 1

            if namelabellength     < reaction.namelabel.winfo_reqwidth()/8:  namelabellength     = int(reaction.namelabel.winfo_reqwidth()/8) + 1
            if equationlabellength < reaction.equalabel.winfo_reqwidth()/8:  equationlabellength = int(reaction.equalabel.winfo_reqwidth()/8) + 1
            if ratelabellength     < reaction.ratewidget.winfo_reqwidth()/8: ratelabellength     = int(reaction.ratewidget.winfo_reqwidth()/8) + 1

        self.botblankcolumn.grid(      row = row, column = 0, padx = 1, sticky = 'WE',pady = 1)
        self.boteditcolumn.grid(       row = row, column = 1, padx = 1, sticky = 'WE',pady = 1)
        self.botdelcolumn.grid(        row = row, column = 2, padx = 1, sticky = 'WE',pady = 1)
        self.botnumbercolumn.grid(     row = row, column = 3, padx = 4, sticky = 'WE')
        self.botnamecolumn.grid(       row = row, column = 4, padx = 4, sticky = 'WE')
        self.botequationcolumn.grid(   row = row, column = 5, padx = 4, sticky = 'WE')
        self.botratecolumn.grid(       row = row, column = 6, padx = 4, sticky = 'WE')
        self.botendcolumn.grid(        row = row, column = 7, padx = 4, sticky = 'WE')

        self.namecolumn.config(width     = namelabellength)
        self.equationcolumn.config(width = equationlabellength)
        self.ratecolumn.config(width     = ratelabellength)

        self.botnamecolumn.config(width     = namelabellength)
        self.botequationcolumn.config(width = equationlabellength)
        self.botratecolumn.config(width     = ratelabellength)


        row = 0

        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1

        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1

        self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def addreaction(self, event = None):

        self.reactions.append(Reaction(len(self.reactions)+1))
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ReactionEditor(self.top, self.system, self.reactions[-1], editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.reactions[-1].get_reaction(self.top.window)
            else:
                self.reactions.remove(self.reactions[-1])
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
                    
        self.updatereactions()
                    
    def editreaction(self, number):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ReactionEditor(self.top, self.system, self.reactions[number-1], editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0: self.reactions[number-1].get_reaction(self.top.window)
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatereactions()
        

    def delreaction(self, number):
        
        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ReactionDeleter(self.top, self.system, self.reactions[number-1]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.reactions[number-1].remove_propertieswidgets()
                self.reactions.remove(self.reactions[number-1])
                
            if self.top is not None:
                self.top.destroy()
                self.top = None
                
        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()
        
        self.updatereactions()



def get_reactionproperties(system, step):
    """Get some basic parameters for each layer."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(ReactionProperties(root, system))
    root.mainloop()

    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_reactionproperties(root.window)
            for reaction in system.reactions: reaction.remove_propertieswidgets()
        else:
            system.reactions = None
        
    root.destroy()

    return system, step + root.step.get()
