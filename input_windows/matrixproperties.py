#! /usr/bin/env python
#
#This file is used to get the flow and system parameters for the simulation.

import tkMessageBox as tkmb

from Tkinter             import Frame, Label, Entry, OptionMenu, Button, Text, DoubleVar, StringVar, IntVar
from capsim_object_types import CapSimWindow, Matrix
from capsim_functions    import get_superfont
from matrixeditor        import MatrixEditor, MatrixDeleter, MixtureEditor

class MatrixProperties:
    """Gets the contaminant properties."""

    def __init__(self, master, system, materials):

        """Constructor method. Defines the parameters to be obtained in this window."""

        self.master    = master
        self.fonttype  = system.fonttype
        self.version   = system.version
        self.superfont = get_superfont(self.fonttype) #superscript font
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None                   #flag for existence of toplevel#

        self.system    = system
        self.materials = materials

        if system.matrices is None:
            self.matrices  = []
            self.nmatrices = 0
        else:
            self.matrices  = system.matrices
            self.nmatrices = system.nmatrices


    def make_widgets(self):
        """Make the widgets for the window."""

        self.bgcolor      = self.frame.cget('bg')

        # Construct all label widgets used in the problem
        self.instructions = Label(self.tframe, text = ' Please select the potential layer materials and provide the following properties:                    ')

        self.blankcolumn    = Label(self.tframe,  text ='',  width = 1)
        self.editcolumn     = Label(self.tframe,  text =' ', width = 6)
        self.delcolumn      = Label(self.tframe,  text =' ', width = 6)
        self.namecolumn     = Label(self.tframe,  text =' ', width = 20)
        self.ecolumn        = Label(self.tframe,  text =' ', width = 15)
        self.rhocolumn      = Label(self.tframe,  text =' ', width = 15)
        self.foccolumn      = Label(self.tframe,  text =' ', width = 20)
        self.endcolumn      = Label(self.tframe,  text =' ', width = 2)

        self.namelabel      = Label(self.tframe,  text = 'Matrix')
        self.elabel         = Label(self.tframe,  text = 'Porosity')
        self.rholabel       = Label(self.tframe,  text = 'Bulk density' )
        self.foclabel       = Label(self.tframe,  text = 'Organic carbon fraction')

        self.rhounit        = Label(self.tframe,  text = u'g/cm\u00B3')

        self.botblankcolumn    = Label(self.frame,  text ='', width = 1)
        self.boteditcolumn     = Label(self.frame,  text =' ', width = 6)
        self.botdelcolumn      = Label(self.frame,  text =' ', width = 6)
        self.botnamecolumn     = Label(self.frame,  text =' ', width = 20)
        self.botecolumn        = Label(self.frame,  text =' ', width = 15)
        self.botrhocolumn      = Label(self.frame,  text =' ', width = 15)
        self.botfoccolumn      = Label(self.frame,  text =' ', width = 20)
        self.botendcolumn      = Label(self.frame,  text =' ', width = 2)

        self.blank1 = Label(self.bframe, text = ' ')
        self.blank2 = Label(self.bframe, text = ' ')
        self.blank3 = Label(self.bframe, text = ' ')

        self.addwidget  = Button(self.bframe, text = 'Add materials', command = self.addmatrix,  width = 20)
        self.loadwidget = Button(self.bframe, text = 'Load materials', command = self.loadmatrix,  width = 20)
        self.mixwidget  = Button(self.bframe, text = 'Create mixtures',  command = self.addmixture,  width = 20)

        #show the widgets on the grid
        self.instructions.grid(  row    = 0, column = 0, sticky = 'W',  padx = 8, columnspan = 6,)

        self.blankcolumn.grid(   row    = 1, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.editcolumn.grid(    row    = 1, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.delcolumn.grid(     row    = 1, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.namecolumn.grid(    row    = 1, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.ecolumn.grid(       row    = 1, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.rhocolumn.grid(     row    = 1, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.foccolumn.grid(     row    = 1, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.namelabel.grid(     row    = 2, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.elabel.grid  (      row    = 2, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.rholabel.grid (     row    = 2, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.foclabel.grid (     row    = 2, column = 6, sticky = 'WE', padx = 1, pady = 1)

        self.rhounit.grid (      row    = 3, column = 5, sticky = 'WE', padx = 1, pady = 1)

        self.updatematrices()


    def updatematrices(self):

        self.addwidget.grid_forget()
        self.loadwidget.grid_forget()
        self.blank1.grid_forget()

        self.botblankcolumn.grid_forget()
        self.boteditcolumn.grid_forget()
        self.botdelcolumn.grid_forget()
        self.botnamecolumn.grid_forget()
        self.botecolumn.grid_forget()
        self.botrhocolumn.grid_forget()
        self.botfoccolumn.grid_forget()

        material_list = self.materials.keys()
        for matrix in self.matrices:
            if len(matrix.components) == 1 :
                try: material_list.remove(matrix.name)
                except: pass

        row = 4

        for matrix in self.matrices:
            try: matrix.remove_propertieswidgets()
            except:pass
            matrix.number = self.matrices.index(matrix) + 1
            matrix.propertieswidgets(self.frame, row, self.master)
            row = row + 1

        self.botblankcolumn.grid(   row    = row, column = 0, sticky = 'WE', padx = 1, pady = 1)
        self.boteditcolumn.grid(    row    = row, column = 1, sticky = 'WE', padx = 1, pady = 1)
        self.botdelcolumn.grid(     row    = row, column = 2, sticky = 'WE', padx = 1, pady = 1)
        self.botnamecolumn.grid(    row    = row, column = 3, sticky = 'WE', padx = 1, pady = 1)
        self.botecolumn.grid(       row    = row, column = 4, sticky = 'WE', padx = 1, pady = 1)
        self.botrhocolumn.grid(     row    = row, column = 5, sticky = 'WE', padx = 1, pady = 1)
        self.botfoccolumn.grid(     row    = row, column = 6, sticky = 'WE', padx = 1, pady = 1)

        row = 0
        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1
        if len(material_list) > 0:
            self.loadwidget.grid(row = row, columnspan = 11)
            row = row + 1
        self.mixwidget.grid(row = row, columnspan = 11)
        row = row + 1

        self.addwidget.bind('<Return>', self.addmatrix)
        self.mixwidget.bind('<Return>', self.addmixture)
        if self.nmatrices == 0:     self.focusbutton = self.addwidget
        else:                       self.focusbutton = None
        self.master.geometry()
        self.master.center()

    def addmixture(self, default = None):

        self.nmatrices = self.nmatrices + 1
        self.matrices.append(Matrix(self.nmatrices))

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(MixtureEditor(self.top, self.system, self.matrices[-1], self.matrices, self.materials, editflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.matrices[-1].get_matrix(self.top.window)
            else:
                self.matrices.remove(self.matrices[-1])
                self.nmatrices = self.nmatrices - 1

            for component in self.matrices[-1].components:
                for matrix in self.matrices[:-1]:
                    for sub_component in matrix.components:
                        if sub_component.name == component.name:
                            sub_component.e   = component.e
                            sub_component.rho = component.rho
                            sub_component.foc = component.foc

                    if len(matrix.components) > 1:
                        e         = 0
                        rho       = 0
                        moc       = 0
                        foc       = 0
                        fractions = 0

                        for component in matrix.components:

                            fractions = fractions + component.fraction
                            e         = e         + component.fraction * component.e
                            rho       = rho       + component.fraction * component.rho
                            moc       = moc       + component.fraction * component.rho * component.foc

                        foc = moc/rho

                        matrix.e = (round(e,2))
                        matrix.rho = (round(rho,3))
                        matrix.foc = (round(foc,3))

                    else:
                        matrix.e          = matrix.components[-1].e
                        matrix.rho        = matrix.components[-1].rho
                        matrix.foc        = matrix.components[-1].foc

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updatematrices()

    def addmatrix(self, default = None):

        self.nmatrices = self.nmatrices + 1
        self.matrices.append(Matrix(self.nmatrices))

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(MatrixEditor(self.top, self.system, self.matrices[-1], self.matrices, self.materials, editflag = 0, newflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.matrices[-1].get_matrix(self.top.window)
            else:
                self.matrices.remove(self.matrices[-1])
                self.nmatrices = self.nmatrices - 1

            if len(self.matrices) > 0:
                for component in self.matrices[-1].components:
                    for matrix in self.matrices[:-1]:
                        for sub_component in matrix.components:
                            if sub_component.name == component.name:
                                sub_component.e   = component.e
                                sub_component.rho = component.rho
                                sub_component.foc = component.foc

                        if len(matrix.components) > 1:
                            e         = 0
                            rho       = 0
                            moc       = 0
                            foc       = 0
                            fractions = 0

                            for component in matrix.components:

                                fractions = fractions + component.fraction
                                e         = e         + component.fraction * component.e
                                rho       = rho       + component.fraction * component.rho
                                moc       = moc       + component.fraction * component.rho * component.foc

                            foc = moc/rho

                            matrix.e = (round(e,2))
                            matrix.rho = (round(rho,3))
                            matrix.foc = (round(foc,3))

                        else:
                            matrix.e          = matrix.components[-1].e
                            matrix.rho        = matrix.components[-1].rho
                            matrix.foc        = matrix.components[-1].foc

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updatematrices()

    def loadmatrix(self, default = None):

        self.nmatrices = self.nmatrices + 1
        self.matrices.append(Matrix(self.nmatrices))

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(MatrixEditor(self.top, self.system, self.matrices[-1], self.matrices, self.materials, editflag = 0, newflag = 0))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.matrices[-1].get_matrix(self.top.window)
            else:
                self.matrices.remove(self.matrices[-1])
                self.nmatrices = self.nmatrices - 1

            if len(self.matrices) > 0:
                for component in self.matrices[-1].components:
                    for matrix in self.matrices[:-1]:
                        for sub_component in matrix.components:
                            if sub_component.name == component.name:
                                sub_component.e   = component.e
                                sub_component.rho = component.rho
                                sub_component.foc = component.foc

                        if len(matrix.components) > 1:
                            e         = 0
                            rho       = 0
                            moc       = 0
                            foc       = 0
                            fractions = 0

                            for component in matrix.components:

                                fractions = fractions + component.fraction
                                e         = e         + component.fraction * component.e
                                rho       = rho       + component.fraction * component.rho
                                moc       = moc       + component.fraction * component.rho * component.foc

                            foc = moc/rho

                            matrix.e = (round(e,2))
                            matrix.rho = (round(rho,3))
                            matrix.foc = (round(foc,3))

                        else:
                            matrix.e          = matrix.components[-1].e
                            matrix.rho        = matrix.components[-1].rho
                            matrix.foc        = matrix.components[-1].foc

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updatematrices()

    def editmatrix(self, number):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            if len(self.matrices[number - 1].components) < 2: self.top.make_window(MatrixEditor(self.top, self.system, self.matrices[number-1], self.matrices, self.materials, editflag = 1, newflag = 0))
            else:                                             self.top.make_window(MixtureEditor(self.top, self.system,self.matrices[number-1], self.matrices, self.materials, editflag = 1))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.matrices[number-1].get_matrix(self.top.window)

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updatematrices()

    def deletematrix(self, number):

        if self.top is None:

            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(MatrixDeleter(self.top, self.system, self.matrices[number-1]))
            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.matrices[number-1].remove_propertieswidgets()
                self.matrices.remove(self.matrices[number-1])
                self.nmatrices = self.nmatrices - 1

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

        self.updatematrices()


    def error_check(self):

        error = 0

        if self.nmatrices == 0: error = 1

        return error

    def warning(self):

        tkmb.showerror(title = self.version, message = 'No matrices has been selected, please add matrices by pressing the button "Add materials" or the button "Add mixture"')
        self.focusbutton = None
        self.master.tk.lift()

def get_matrixproperties(system, materials, step):
    """Get some basic parameters for each layer."""

    root = CapSimWindow(master = None, buttons = 1)
    root.make_window(MatrixProperties(root, system, materials))
    root.mainloop()
    
    if root.main.get() == 1: system = None
    else:
        if root.step.get() == 1:
            system.get_matricesproperties(root.window)
            for matrix in system.matrices: matrix.remove_propertieswidgets()
        else:
            system.matrices   = None
            system.nmatrices  = 0
            system.component_list      = []
            system.components          = []

    root.destroy()

    return system, step + root.step.get()

        
        
