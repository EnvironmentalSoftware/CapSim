# -*- coding: utf-8 -*-

#!/usr/bin/env python
#These subroutines are used in post-processing for CapSim.

import matplotlib.pyplot as plt, tkMessageBox as tkmb, math, sys, os, codecs, _winreg as wreg
import tkFileDialog as tkfd
import matplotlib.patches  as patches
import matplotlib.gridspec as gridspec
import matplotlib.tri      as tri

if sys.path[0][-3:] == 'zip': 
    os.chdir(sys.path[0][:-12])
    path = sys.path[0][:-12]
else: path = sys.path[0]

CapSimReg = wreg.ConnectRegistry(None, wreg.HKEY_CURRENT_USER)
CapSimKey = wreg.OpenKey(CapSimReg, r'Software\CapSim')
Filepath =wreg.QueryValueEx(CapSimKey, 'FilePath')[0]
CapSimKey.Close()

from numpy               import zeros, transpose, interp, array, isnan
from capsim_object_types import System, CapSimWindow
from datetime            import datetime
from Tkinter             import Tk, Toplevel, Canvas, Frame, Label, Entry, Text, Button, Scrollbar, OptionMenu, StringVar, DoubleVar, IntVar, FLAT, RAISED, Checkbutton
from PIL                 import Image, ImageTk
from textwrap            import fill

class Postprocess:
    """Makes a window to display the simulation plots."""

    def __init__(self, master, system, output, batch_type = None):
        """Constructor method."""

        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.system    = system
        self.output    = output
        rgb            = self.master.frame.winfo_rgb(self.master.frame.cget('bg'))
        self.color     = '#%02x%02x%02x' %rgb
        self.mplrgb    = (rgb[0] / 65536., rgb[1] / 65536., rgb[2] / 65536.) 
        self.tframe    = Frame(master.tframe, bg = self.color)
        self.frame     = Frame(master.frame,  bg = self.color)
        self.bframe    = Frame(master.bframe, bg = self.color)
        self.top       = None
        self.flag      = 0
        self.filename  = 'plot_output'

        self.lengthunit = system.lengthunit
        self.concunit   = system.concunit
        self.timeunit   = system.timeunit
        self.diffunit   = system.diffunit

        self.types        = ['Spatial profile', 'Time profile']
        self.variables    = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Water concentration', 'Material fraction']

        self.sketch       = {}
        self.sketch['Sketches'] = ['Show sketch', 'Hide sketch']
        self.sketch['Sketch']   = 'Show sketch'
        self.sketch['Label']    = 1
        self.sketch['Time']     = 0
        self.sketch['Depth']    = 0

        self.chemicals  = [chemical.name for chemical in system.chemicals]

        self.layer_h   =[0]
        for layer in system.layers:
            if layer.name !='Deposition':
                self.layer_h.append(self.layer_h[-1]+layer.h)

        self.type        = self.types[0]
        self.variable    = self.variables[0]

        self.spatialplotdatas   = []
        for i in range(6):
            self.spatialplotdatas.append(PlotData(i))
            self.spatialplotdatas[-1].name  = self.chemicals[0]
            self.spatialplotdatas[-1].value = round(self.output.times[-1]/5*i, 1)
            self.spatialplotdatas[-1].type  = self.spatialplotdatas[-1].types[0]
            self.spatialplotdatas[-1].component= 'Total solid'

        self.timeplotdatas              = [PlotData(0)]
        self.timeplotdatas[-1].name     = self.chemicals[0]
        self.timeplotdatas[-1].value    = 0
        self.timeplotdatas[-1].type     = self.timeplotdatas[-1].types[0]
        self.timeplotdatas[-1].component= 'Total solid'

        self.Cplot = zeros((len(self.output.z),  len(self.spatialplotdatas)))
        for n in range(len(self.spatialplotdatas)):
            chemnum = self.chemicals.index(self.spatialplotdatas[n].name)
            i = 0
            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
            self.Cplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.C[i, :, chemnum], self.output.C[i + 1, :, chemnum])

        Cmax = 0
        for i in range(len(self.output.z)):
            for j in range(6):
                if self.Cplot [i,j] > Cmax and isnan(self.Cplot [i,j]) == 0:
                    Cmax = self.Cplot [i,j]

        self.figuresize = [600, 450]

        if master.tk.winfo_screenheight()/master.tk.winfo_screenwidth() > 3/4:
            if master.tk.winfo_screenheight()*3/5 < 450:
                self.figuresize[1] = int(master.tk.winfo_screenheight()*3/5)
                self.figuresize[0] = int(self.figuresize[1]/3*4)

        else:
            if master.tk.winfo_screenwidth()*4/5 < 600:
                self.figuresize[0] = int(master.tk.winfo_screenwidth()*4/5)
                self.figuresize[1] = int(self.figuresize[0]*3/4)

        self.axislimit  = [0, 1.2 * Cmax, min(self.output.z), max(self.output.z)]
        self.legendposition = 0

        self.fontsize = {}
        self.fontsize['Flag']   = 'Default'
        self.fontsize['Title']  = 12
        self.fontsize['Label']  = [10, 10]
        self.fontsize['Axis' ]  = [8, 8]
        self.fontsize['Legend'] = 9

        self.graphpath = Filepath + '\output\\'

        self.gs = gridspec.GridSpec(1, 2, width_ratios=[1, 5])
        self.gs.update(left = 0.01, right = 0.95)
        if batch_type != 'batch':  self.make_graphs()

    def make_widgets(self):
        """Makes the widgets for the window."""

        self.master.frame.config(bg      = self.color)
        self.master.mainbutton.config(bg = self.color)
        self.master.exitbutton.config(bg = self.color)

        self.graph      = Image.open(Filepath + r'/output/%s.png' % self.filename)
        self.image      = ImageTk.PhotoImage(self.graph)
        self.graphlabel = Label(self.frame, image = self.image,       bg = self.color)

        self.blank1     = Label(self.bframe, text = ' ')
        self.blank2     = Label(self.bframe, text = ' ')
        self.blank3     = Label(self.bframe, text = ' ')

        self.editbutton   = Button(self.bframe, text = 'Edit plot',     bg = self.color, command = self.editplot,    width = 20, activebackground = 'white', highlightbackground = 'black')
        self.figurebutton = Button(self.bframe, text = 'Edit figure',   bg = self.color, command = self.editfigure,  width = 20, activebackground = 'white', highlightbackground = 'black')
        self.savebutton   = Button(self.bframe, text = 'Save figure',   bg = self.color, command = self.savegraph,   width = 20, activebackground = 'white', highlightbackground = 'black')
        self.exportbutton = Button(self.bframe, text = 'Export result', bg = self.color, command = self.export_data, width = 20, activebackground = 'white', highlightbackground = 'black')
        self.modifybutton = Button(self.bframe, text = 'Modify System', bg = self.color, command = self.modify,      width = 20, activebackground = 'white', highlightbackground = 'black')

        self.graphlabel.grid(   row = 0, column = 1, padx = 40)

        self.blank1.grid(       row = 1, column = 0, columnspan = 7, padx = 40)
        self.editbutton.grid(   row = 2, column = 0, columnspan = 7, padx = 40)
        self.figurebutton.grid( row = 3, column = 0, columnspan = 7, padx = 40)
        self.exportbutton.grid( row = 4, column = 0, columnspan = 7, padx = 40)
        self.savebutton.grid(   row = 5, column = 0, columnspan = 7)

        if self.master.master is None: self.modifybutton.grid(row = 6, columnspan = 7, column = 0)

        self.modifybutton.bind('<Return>', self.modify)

        self.focusbutton = self.editbutton

        self.master.geometry()
        self.master.center()

    def editplot(self, event = None):

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(GraphEditor(self.top, self.system, self.type, self.variable, self.spatialplotdatas, self.timeplotdatas, self.output.z, self.output.times))

            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.type     = self.top.window.type.get()
                self.variable = self.top.window.variable.get()

                for spatialplotdata in self.top.window.spatialplotdatas:  spatialplotdata.get_plotdata()
                for timeplotdata in self.top.window.timeplotdatas:        timeplotdata.get_plotdata()

                self.spatialplotdatas = [spatialplotdata.copy() for spatialplotdata in self.top.window.spatialplotdatas]
                self.timeplotdatas    = [timeplotdata.copy()    for timeplotdata    in self.top.window.timeplotdatas]


                if self.type == self.types[0]:

                    self.axislimit[2]  = min(self.output.z)
                    self.axislimit[3]  = max(self.output.z)

                    if self.variable == 'Concentration':
                        self.Cplot       = zeros((len(self.output.z),  len(self.spatialplotdatas)))

                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.chemicals.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
                            self.Cplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.C[i, :, chemnum], self.output.C[i + 1, :, chemnum])

                        Cmax = 0
                        for i in range(len(self.output.z)):
                            for j in range(len(self.spatialplotdatas)):
                                if self.Cplot [i,j] > Cmax and isnan(self.Cplot [i,j]) == 0:
                                    Cmax = self.Cplot [i,j]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * Cmax

                    if self.variable == 'Flux':
                        self.Fplot = zeros((len(self.output.z),  len(self.spatialplotdatas)))
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.chemicals.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
                            self.Fplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.F[i, :, chemnum], self.output.F[i + 1, :, chemnum])

                        Fmax = 0
                        for i in range(len(self.output.z)):
                            for j in range(len(self.spatialplotdatas)):
                                if self.Fplot [i,j] > Fmax and isnan(self.Fplot [i,j]) == 0:
                                    Fmax = self.Fplot [i,j]

                        if self.Fplot[:, :].max() < 0:     Fmax = 0.8 * self.Fplot[:, :].max()
                        else:                              Fmax = 1.2 * self.Fplot[:, :].max()

                        if self.Fplot[:, :].min() < 0:     Fmin = 1.2 * self.Fplot[:, :].min()
                        else:                              Fmin = 0.8 * self.Fplot[:, :].min()

                        self.axislimit[0]  = Fmin
                        self.axislimit[1]  = Fmax

                    if self.variable == 'Solid concentration':
                        self.qplot = zeros((len(self.output.z),  len(self.spatialplotdatas)))
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.chemicals.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
                            if self.spatialplotdatas[n].component == 'Total solid':
                                self.qplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.q[i, :, chemnum], self.output.q[i + 1, :, chemnum])
                            else:
                                compnum = self.system.component_list.index(self.spatialplotdatas[n].component)
                                self.qplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.qm[i, :, chemnum, compnum], self.output.qm[i + 1, :, chemnum, compnum])

                        qmax = 0
                        for i in range(len(self.output.z)):
                            for j in range(len(self.spatialplotdatas)):
                                if self.qplot [i,j] > qmax and isnan(self.qplot [i,j]) == 0:
                                    qmax = self.qplot [i,j]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * qmax

                    if self.variable == 'Total concentration':

                        self.Wplot = zeros((len(self.output.z),  len(self.spatialplotdatas)))
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.chemicals.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
                            self.Wplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.W[i, :, chemnum], self.output.W[i + 1, :, chemnum])

                        Wmax = 0
                        for i in range(len(self.output.z)):
                            for j in range(len(self.spatialplotdatas)):
                                if self.Wplot [i,j] > Wmax and isnan(self.Wplot [i,j]) == 0:
                                    Wmax = self.Wplot [i,j]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * Wmax

                    if self.variable == 'Material fraction':

                        self.Fiplot = zeros((len(self.output.z),  len(self.spatialplotdatas)))
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.system.component_list.index(self.spatialplotdatas[n].component)
                            i = 0
                            while self.spatialplotdatas[n].value > self.output.times[i+1]: i = i + 1
                            self.Fiplot[:, n] = time_interpolate(self.spatialplotdatas[n].value, self.output.times[i], self.output.times[i + 1] - self.output.times[i], self.output.Fi[i, :, chemnum], self.output.Fi[i + 1, :, chemnum])

                        Fimax = 0
                        for i in range(len(self.output.z)):
                            for j in range(len(self.spatialplotdatas)):
                                if self.Fiplot [i,j] > Fimax and isnan(self.Fiplot [i,j]) == 0:
                                    Fimax = self.Fiplot [i,j]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * Fimax

                if self.type == self.types[1]:
                    self.axislimit[0]  = 0
                    self.axislimit[1]  = self.output.times[-1]

                    if self.variable == 'Concentration':
                        self.Cinterest  = zeros([len(self.output.times), len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.chemicals.index(self.timeplotdatas[n].name)
                            for i in range (len(self.output.times)):
                                if self.system.dep == 'Deposition' and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    #if self.system.depgrid == 1:
                                    #self.Cinterest[i,n] = interp((self.timeplotdatas[n].value-self.system.Vdep*self.output.times[i]), self.output.z, self.output.C[i,:,chemnum])
                                    #else:
                                    self.Cinterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.C[i,:,chemnum])
                                else:
                                    self.Cinterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.C[i,:,chemnum])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = self.Cinterest.max()*1.2

                    if self.variable == 'Flux':
                        self.Finterest  = zeros([len(self.output.times),len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.chemicals.index(self.timeplotdatas[n].name)
                            for i in range (len(self.output.times)):
                                if self.system.dep == 'Deposition' and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    #if self.system.depgrid == 1:
                                    #self.Finterest[i,n] = interp((self.timeplotdatas[n].value-self.system.Vdep*self.output.times[i]), self.output.z, self.output.F[i,:,chemnum])
                                    #else:
                                    self.Finterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.F[i,:,chemnum])
                                else:
                                    self.Finterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.F[i,:,chemnum])

                        if self.Finterest.max() < 0:     Fmax = 0.8 * self.Finterest.max()
                        else:                            Fmax = 1.2 * self.Finterest.max()

                        if self.Finterest.min() < 0:     Fmin = 1.2 * self.Finterest.min()
                        else:                            Fmin = 0.8 * self.Finterest.min()

                        self.axislimit[2]  = Fmin
                        self.axislimit[3]  = Fmax

                    if self.variable == 'Solid concentration':
                        self.qinterest  = zeros([len(self.output.times), len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.chemicals.index(self.timeplotdatas[n].name)
                            for i in range (len(self.output.times)):
                                if self.system.dep == 'Deposition' and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    if self.timeplotdatas[n].component == 'Total solid':
                                        self.qinterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.q[i,:,chemnum])
                                    else:
                                        compnum = self.system.component_list.index(self.timeplotdatas[n].component)
                                        self.qinterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.qm[i,:,chemnum, compnum])

                                else:
                                    if self.timeplotdatas[n].component == 'Total solid':
                                        self.qinterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.q[i,:,chemnum])
                                    else:
                                        compnum = self.system.component_list.index(self.timeplotdatas[n].component)
                                        self.qinterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.qm[i,:,chemnum, compnum])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = self.qinterest.max()*1.2

                    if self.variable == 'Total concentration':

                        self.Winterest  = zeros([len(self.output.times), len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.chemicals.index(self.timeplotdatas[n].name)
                            for i in range (len(self.output.times)):
                                if self.system.dep == 'Deposition' and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    self.Winterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.W[i,:,chemnum])
                                else:
                                    self.Winterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.W[i,:,chemnum])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = self.Winterest.max()*1.2

                    if self.variable == 'Water concentration':

                        self.Cwinterest  = zeros([len(self.output.times), len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.chemicals.index(self.timeplotdatas[n].name)
                            for i in range (len(self.output.times)):
                                self.Cwinterest[i,n] = self.output.Cw[i,chemnum]

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = self.Cwinterest.max()*1.2

                    if self.variable == 'Material fraction':

                        self.Fiinterest  = zeros([len(self.output.times), len(self.timeplotdatas)])
                        for n in range(len(self.timeplotdatas)):
                            chemnum         = self.system.component_list.index(self.timeplotdatas[n].component)
                            for i in range (len(self.output.times)):
                                if self.system.dep == 'Deposition' and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    self.Fiinterest[i,n] = interp_dep(self.timeplotdatas[n].value, -self.system.Vdep*self.output.times[i], -self.system.delz[0], self.output.z, self.output.Fi[i,:,chemnum])
                                else:
                                    self.Fiinterest[i,n] = interp(self.timeplotdatas[n].value, self.output.z, self.output.Fi[i,:,chemnum])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = self.Fiinterest.max()*1.2

                self.updategraph()

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

    def editfigure(self, event = None):

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(FigureEditor(self.top, self.system, self.type, self.variable, self.sketch, self.axislimit, self.figuresize, self.legendposition, self.fontsize))

            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:

                self.sketch['Sketch']       = self.top.window.sketch.get()
                self.sketch['Label']        = self.top.window.sketchlabel.get()
                self.sketch['Time']         = self.top.window.sketchline.get()
                self.sketch['Depth']        = self.top.window.locationline.get()

                self.legendposition         = self.top.window.legendpositions.index(self.top.window.legendposition.get())
                self.axislimit[0]           = self.top.window.xaxismin.get()
                self.axislimit[1]           = self.top.window.xaxismax.get()
                self.axislimit[2]           = self.top.window.yaxismin.get()
                self.axislimit[3]           = self.top.window.yaxismax.get()

                self.figuresize[0]          = self.top.window.figurewidth.get()
                self.figuresize[1]          = self.top.window.figureheight.get()

                self.fontsize['Flag']       = self.top.window.fontsize.get()
                self.fontsize['Title']      = self.top.window.titlefontsize.get()
                self.fontsize['Axis'][0]    = self.top.window.xaxisfontsize.get()
                self.fontsize['Axis'][1]    = self.top.window.yaxisfontsize.get()
                self.fontsize['Label'][0]   = self.top.window.xlabelfontsize.get()
                self.fontsize['Label'][1]   = self.top.window.ylabelfontsize.get()
                self.fontsize['Legend']     = self.top.window.legendfontsize.get()

                self.updategraph()

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing parameter input window first.')
            self.top.tk.focus()

    def updategraph(self, event = None):

        try: self.graphlabel.grid_forget()
        except: pass

        self.make_graphs()

        self.graph      = Image.open(Filepath + r'/output/%s.png' % self.filename)
        self.image      = ImageTk.PhotoImage(self.graph)
        self.graphlabel = Label(self.frame, image = self.image, bg = self.color)

        self.graphlabel.grid(  row = 0, column = 1, padx = 40, sticky = 'WE')

        self.master.geometry()
        self.master.center()

    def savegraph(self, event = None):

        self.graphname = tkfd.asksaveasfilename(initialdir=self.graphpath,  title='Please define the directory to save the graph', filetypes = [('PNG files', '*.png')])
        self.outputgraphs.savefig(self.graphname)

        #update the default directory
        try:
            i = 1
            while self.graphname[-i] != '/':
                i = i + 1
            self.graphpath = self.graphname[0:-i+1]
        except: pass


    def export_data(self, event = None):

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(ResultExporter(self.top, self.system, self.output))
            self.top.mainloop()

            if self.top.window.cancelflag == 0:
                filename = self.top.window.filepath.get() + self.top.window.name.get()
                if self.top.window.type.get() == self.top.window.types[0]:
                    self.make_csv_file(filename, self.top.window.chemical.get(), self.top.window.MW)

            if self.top is not None:
                self.top.destroy()
                self.top = None

        elif self.top is not None:
            tkmb.showerror(title = self.system.version, message = 'Please close the existing result export window first.')
            self.top.tk.focus()

    def make_graphs(self):

        """Makes graphs for the postprocessing window."""
        self.family         = 'Calibri'

        plt.rcParams['mathtext.default']      = 'regular'
        plt.rcParams['axes.facecolor']        = self.mplrgb
        plt.rcParams['savefig.edgecolor']     = self.mplrgb
        plt.rcParams['savefig.facecolor']     = self.mplrgb
        plt.rcParams['axes.formatter.limits'] = [-4,4]
        plt.rcParams['xtick.labelsize']       = self.fontsize['Axis'][0]
        plt.rcParams['ytick.labelsize']       = self.fontsize['Axis'][1]

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]:
            self.outputgraphs = plt.figure(figsize=(self.figuresize[0]/100, self.figuresize[1]/100))
            self.make_sketch_image()
        else:
            self.outputgraphs = plt.figure(figsize=(self.figuresize[0]/100, self.figuresize[1]/100))

        if self.type == self.types[0]:
            if self.variable == 'Concentration':
                self.make_C_profiles()
            if self.variable == 'Flux':
                self.make_F_profiles()
            if self.variable == 'Total concentration':
                self.make_W_profiles()
            if self.variable == 'Solid concentration':
                self.make_q_profiles()
            if self.variable == 'Material fraction':
                self.make_Fi_profiles()

        elif self.type == self.types[1]:

            if self.variable == 'Concentration':
                self.make_Cinterest()
            if self.variable == 'Flux':
                self.make_Finterest()
            if self.variable == 'Total concentration':
                self.make_Winterest()
            if self.variable == 'Solid concentration':
                self.make_qinterest()
            if self.variable == 'Water concentration':
                self.make_Cwinterest()
            if self.variable == 'Material fraction':
                self.make_Fiinterest()

        if 0.15 * self.figuresize[0] < 90:   leftspace    = 90./self.figuresize[0]
        else:                                leftspace    = 0.15
        if 0.05 * self.figuresize[0] < 30:   rightspace   = 1. - 30./self.figuresize[0]
        else:                                rightspace   = 0.95
        if 0.35 * self.figuresize[0] < 210:  widthspace   = 210./self.figuresize[0]
        else:                                widthspace   = 0.35
        if 0.1  * self.figuresize[1] < 45:   bottomspace  = 45./self.figuresize[1]
        else:                                bottomspace  = 0.1
        if 0.07 * self.figuresize[1] < 31.5: topspace     = 1. - 45./self.figuresize[1]
        else:                                topspace     = 0.93
        if 0.33 * self.figuresize[0] < 121.5:heightspace  = 121.5/self.figuresize[0]
        else:                                heightspace  = 0.33

        plt.subplots_adjust(left = leftspace, right = rightspace, bottom =bottomspace, top = topspace,  wspace = widthspace, hspace = heightspace)
        self.outputgraphs.savefig(Filepath + r'/output/%s.png' % self.filename)

    def make_sketch_image(self):
        """Makes plots of concentration profiles over time."""

        Sketchprofiles  = self.outputgraphs.add_subplot(self.gs[0])

        Htotal = self.output.z[-1] - self.output.z[0]

        sfont = {9:6, 10:7, 11:7.5, 12:8, 13:9}

        H = 0
        color_step = round(0.5/len(self.system.layers),2)
        Blocks = []
        for layer in self.system.layers:
            if layer.number <> 0:
                Blocks.append(patches.Rectangle((0.0, H), 0.99, layer.h, facecolor = str( 0.75 - color_step * layer.number), edgecolor = 'k', linestyle = 'solid', linewidth = '1'))
                Sketchprofiles.add_patch(Blocks[-1])
                if self.sketch['Label'] == 1:
                    rx, ry = Blocks[-1].get_xy()
                    cx = rx + Blocks[-1].get_width()/2.0
                    cy = ry + Blocks[-1].get_height()/2.0
                    if Blocks[-1].get_height()/Htotal*self.figuresize[1] >= 14:
                        Sketchprofiles.annotate(fill(layer.type, 10), (cx, cy), color='w', fontsize = 10, ha='center', va='center')
                    elif Blocks[-1].get_height()/Htotal*self.figuresize[1] >= 9:
                        Sketchprofiles.annotate(fill(layer.type, 10), (cx, cy), color='w', fontsize = sfont[int(Blocks[-1].get_height()/Htotal*self.figuresize[1])], ha='center', va='center')
                H = H + layer.h

        if self.system.dep == 'Deposition':
            Blockdep = patches.Polygon(array([[0.995, self.output.z[0]], [0.0, 0.0], [0.995, 0.0]]), facecolor = '0.75', edgecolor = 'k', linestyle = 'solid', linewidth = '1')
            Sketchprofiles.add_patch(Blockdep)
            if self.sketch['Label'] == 1:
                rx, ry = 0.0, 0.0
                cx = rx + 0.995/2.0
                cy = ry + self.output.z[0]/2.0
                if abs(self.output.z[0])/Htotal*self.figuresize[1] >= 14:
                    Sketchprofiles.annotate(fill(self.system.layers[0].type, 10), (cx, cy), color='k', fontsize = 10, ha='center', va='center')
                elif abs(self.output.z[0])/Htotal*self.figuresize[1] >= 9:
                    Sketchprofiles.annotate(fill(self.system.layers[0].type, 10), (cx, cy), color='k', fontsize = sfont[int(abs(self.output.z[0])/Htotal*self.figuresize[1])], ha='center', va='center')

        if self.system.dep == 'Deposition' and self.sketch['Time'] == 1:
            Sketchprofiles.annotate('0', (0, H),                                                color='k', fontsize = 10, ha='center', va='top')
            Sketchprofiles.annotate(fill(str(self.output.times[-1]) + self.system.timeunit, 6), (1.0, H),color='k', fontsize = 10, ha='center', va='top')

        if self.type == self.types[0]:
            if self.sketch['Time'] == 1:
                if self.system.dep == 'Deposition':
                    for plotdata in self.spatialplotdatas:
                        Sketchprofiles.plot( [plotdata.value/self.output.times[-1], plotdata.value/self.output.times[-1]],[0-plotdata.value*self.system.Vdep, self.output.z[-1]])
                else:
                    for plotdata in self.spatialplotdatas:
                        Sketchprofiles.plot( [plotdata.value/self.output.times[-1], plotdata.value/self.output.times[-1]], [0, self.output.z[-1]])

        if self.type == self.types[1]:
            if self.sketch['Depth'] == 1:
                for plotdata in self.timeplotdatas:
                    if plotdata.type == plotdata.types[0]:
                        Sketchprofiles.plot([0.0, 1.0], [plotdata.value, plotdata.value])
                    else:
                        Sketchprofiles.plot([0.0, 1.0], [plotdata.value, plotdata.value + self.output.z[0]])

        if self.system.bio <> 'None':
            Sketchprofiles.plot([0.0, 1.0], [self.system.hbio, self.system.hbio + self.output.z[0]], linestyle = ':', color = 'k')

        Sketchprofiles.axis('off')
        Sketchprofiles.set_ylim([max(self.output.z), min(self.output.z)])

    def make_C_profiles(self):
        """Makes plots of concentration profiles over time."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cprofiles  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Cprofiles  = self.outputgraphs.add_subplot(111)

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)
        time_list = [plotdata.value for plotdata in self.spatialplotdatas]


        if self.system.dep == 'Deposition': #remove points above deposition layer
            for j in range(len(time_list)):
                time = time_list[j]
                dep = -self.system.Vdep * time
                i = 0
                while round(self.output.z[i] + 0.5 * self.system.delz[0], 8) < round(dep, 8):
                    i = i + 1
                if round(-dep, 8) < 1.5 * self.system.delz[0] and round(-dep, 8) >= 0.5 * self.system.delz[0]:
                    Cs = self.Cplot[i+2:, j]
                    zs = self.output.z[i+2:]
                else:
                    Cs = self.Cplot[i+1:, j]
                    zs = self.output.z[i+1:]
                zs[0] = -self.system.Vdep * time


                Cs_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[j].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[j].name].ICtype == 'Uniform':
                            Cs_plot.append(Cs[i-1])
                            Cs_plot.append(Cs[i])
                        else:
                            Cs_plot.append(Cs[i])
                            Cs_plot.append(Cs[i])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(zs[i])
                        Cs_plot.append(Cs[i])

                Cprofiles.plot(Cs_plot, zs_plot, linewidth = 0.5)

        else:
            Cs = self.Cplot
            zs = self.output.z

            for n in range(len(self.spatialplotdatas)):
                Cs_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[n].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[n].name].ICtype == 'Uniform':
                            Cs_plot.append(Cs[i-1, n])
                            Cs_plot.append(Cs[i, n])
                        else:
                            Cs_plot.append(Cs[i, n])
                            Cs_plot.append(Cs[i, n])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(zs[i])
                        Cs_plot.append(Cs[i, n])

                Cprofiles.plot(Cs_plot, zs_plot, linewidth = 0.5)

        for layer_h in self.layer_h:
            Cprofiles.plot([0, 2. * self.Cplot.max()], [layer_h, layer_h], linewidth = 0.5, linestyle = ':', color = 'k')

        Cprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Cprofiles.set_xlabel('Concentration ('+self.concunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family =self.family)
        Cprofiles.set_title('Pore Water Concentration Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Cleg = Cprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_F_profiles(self):
        """Makes a graph of the Total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Fprofiles  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Fprofiles  = self.outputgraphs.add_subplot(111)

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)
        time_list = [plotdata.value for plotdata in self.spatialplotdatas]

        if self.system.dep == 'Deposition': #remove points above deposition layer
            for j in range(len(time_list)):
                time = time_list[j]
                dep = -self.system.Vdep * time
                i = 0
                while round(self.output.z[i] + 0.5 * self.system.delz[0], 8) < round(dep, 8):
                    i = i + 1
                if round(-dep, 8) < 1.5 * self.system.delz[0] and round(-dep, 8) >= 0.5 * self.system.delz[0]:
                    Fs = self.Fplot[i+2:, j]
                    zs = self.output.z[i+2:]
                else:
                    Fs = self.Fplot[i+1:, j]
                    zs = self.output.z[i+1:]
                zs[0] = -self.system.Vdep * time
                Fprofiles.plot(Fs, zs, linewidth = 0.5)
        else:
            Fprofiles.plot(self.Fplot, self.output.z, linewidth = 0.5)

        for layer_h in self.layer_h:
            Fprofiles.plot([0, 2. * self.Fplot.max()], [layer_h, layer_h], linewidth = 0.5, linestyle = ':', color = 'k')

        Fprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Fprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Fprofiles.set_xlabel('Flux (' + self.concunit[:-1] + self.lengthunit + u'\u00B2' + '/' + self.timeunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Fprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        Fprofiles.set_title('Flux Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Fleg = Fprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Fleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Fleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_q_profiles(self):
        """Makes a graph of the Total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: qprofiles  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   qprofiles  = self.outputgraphs.add_subplot(111)

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' in '  + self.spatialplotdatas[n].component + ' '+  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)
        time_list = [plotdata.value for plotdata in self.spatialplotdatas]

        if self.system.dep == 'Deposition': #remove points above deposition layer
            for j in range(len(time_list)):
                time = time_list[j]
                dep = -self.system.Vdep * time
                i = 0
                while round(self.output.z[i] + 0.5 * self.system.delz[0], 8) < round(dep, 8):
                    i = i + 1
                if round(-dep, 8) < 1.5 * self.system.delz[0] and round(-dep, 8) >= 0.5 * self.system.delz[0]:
                    qs = self.qplot[i+2:, j]
                    zs = self.output.z[i+2:]
                else:
                    qs = self.qplot[i+1:, j]
                    zs = self.output.z[i+1:]
                zs[0] = -self.system.Vdep * time

                qs_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[j].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[j].name].ICtype == 'Uniform':
                            qs_plot.append(qs[i-1])
                            qs_plot.append(qs[i])
                        else:
                            qs_plot.append(qs[i])
                            qs_plot.append(qs[i])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(zs[i])
                        qs_plot.append(qs[i])

                qprofiles.plot(qs_plot, zs_plot, linewidth = 0.5)

        else:
            qs = self.qplot
            zs = self.output.z

            for n in range(len(self.spatialplotdatas)):

                qs_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[n].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[n].name].ICtype == 'Uniform':
                            qs_plot.append(qs[i-1, n])
                            qs_plot.append(qs[i, n])
                        else:
                            qs_plot.append(qs[i, n])
                            qs_plot.append(qs[i, n])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(self.output.z[i])
                        qs_plot.append(qs[i, n])

                qprofiles.plot(qs_plot, zs_plot, linewidth = 0.5)

        for layer_h in self.layer_h:
            qprofiles.plot([0, 2. * self.qplot.max()], [layer_h, layer_h], linewidth = 0.5, linestyle = ':', color = 'k')


        qprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        qprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        qprofiles.set_xlabel('Concentration ('+self.concunit[:-1]+'kg)', fontsize = self.fontsize['Label'][0], family = self.family)
        qprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        qprofiles.set_title('Solid Concentration Profiles', fontsize = self.fontsize['Title'], family = self.family)
        qleg = qprofiles.legend(tlegend, loc = self.legendposition,labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        qleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in qleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_W_profiles(self):
        """Makes a graph of the Total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Wprofiles  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Wprofiles  = self.outputgraphs.add_subplot(111)

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)
        time_list = [plotdata.value for plotdata in self.spatialplotdatas]

        if self.system.dep == 'Deposition': #remove points above deposition layer
            for j in range(len(time_list)):
                time = time_list[j]
                dep = -self.system.Vdep * time
                i = 0
                while round(self.output.z[i] + 0.5 * self.system.delz[0], 8) < round(dep, 8):
                    i = i + 1
                if round(-dep, 8) < 1.5 * self.system.delz[0] and round(-dep, 8) >= 0.5 * self.system.delz[0]:
                    Ws = self.Wplot[i+2:, j]
                    zs = self.output.z[i+2:]
                else:
                    Ws = self.Wplot[i+1:, j]
                    zs = self.output.z[i+1:]
                zs[0] = -self.system.Vdep * time

                Ws_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[j].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[j].name].ICtype == 'Uniform':
                            Ws_plot.append(Ws[i-1])
                            Ws_plot.append(Ws[i])
                        else:
                            Ws_plot.append(Ws[i])
                            Ws_plot.append(Ws[i])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(zs[i])
                        Ws_plot.append(Ws[i])

                Wprofiles.plot(Ws_plot, zs_plot, linewidth = 0.5)

        else:
            Ws = self.Wplot
            zs = self.output.z

            for n in range(len(self.spatialplotdatas)):
                Ws_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[n].value == 0 and self.system.ICs[self.system.layers[j_layer].name][self.spatialplotdatas[n].name].ICtype == 'Uniform':
                            Ws_plot.append(Ws[i-1, n])
                            Ws_plot.append(Ws[i, n])
                        else:
                            Ws_plot.append(Ws[i, n])
                            Ws_plot.append(Ws[i, n])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(self.output.z[i])
                        Ws_plot.append(Ws[i, n])

                Wprofiles.plot(Ws_plot, zs_plot, linewidth = 0.5)

        for layer_h in self.layer_h:
            Wprofiles.plot([0, 2. * self.Wplot.max()], [layer_h, layer_h], linewidth = 0.5, linestyle = ':', color = 'k')

        Wprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Wprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Wprofiles.set_xlabel('Concentration ('+self.concunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Wprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        Wprofiles.set_title('Total Concentration Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Wleg = Wprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Wleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Wleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Fi_profiles(self):
        """Makes a graph of the Total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Fiprofiles  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Fiprofiles  = self.outputgraphs.add_subplot(111)

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].component + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)
        time_list = [plotdata.value for plotdata in self.spatialplotdatas]

        if self.system.dep == 'Deposition': #remove points above deposition layer
            for j in range(len(time_list)):
                time = time_list[j]
                dep = -self.system.Vdep * time
                i = 0
                while round(self.output.z[i] + 0.5 * self.system.delz[0], 8) < round(dep, 8):
                    i = i + 1
                if round(-dep, 8) < 1.5 * self.system.delz[0] and round(-dep, 8) >= 0.5 * self.system.delz[0]:
                    Fis = self.Fiplot[i+2:, j]
                    zs = self.output.z[i+2:]
                else:
                    Fis = self.Fiplot[i+1:, j]
                    zs = self.output.z[i+1:]
                zs[0] = -self.system.Vdep * time

                Fis_plot = []
                zs_plot = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[j].value == 0:
                            Fis_plot.append(Fis[i-1])
                            Fis_plot.append(Fis[i])
                        else:
                            Fis_plot.append(Fis[i])
                            Fis_plot.append(Fis[i])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(zs[i])
                        Fis_plot.append(Fis[i])

                Fiprofiles.plot(Fis_plot, zs_plot, linewidth = 0.5)

        else:
            Fis = self.Fiplot
            zs =  self.output.z

            for n in range(len(self.spatialplotdatas)):
                Fis_plot = []
                zs_plot  = []

                j_layer = 0
                for i in range(len(zs)):
                    if self.layer_h[1:-1].count(round(zs[i], 8)):
                        zs_plot.append(zs[i])
                        zs_plot.append(zs[i])
                        if self.spatialplotdatas[n].value == 0:
                            Fis_plot.append(Fis[i-1, n])
                            Fis_plot.append(Fis[i, n])
                        else:
                            Fis_plot.append(Fis[i, n])
                            Fis_plot.append(Fis[i, n])
                        j_layer = j_layer + 1
                    else:
                        zs_plot.append(self.output.z[i])
                        Fis_plot.append(Fis[i, n])

                Fiprofiles.plot(Fis_plot, zs_plot, linewidth = 0.5)

        for layer_h in self.layer_h:
            Fiprofiles.plot([0, 2. * self.Fiplot.max()], [layer_h, layer_h], linewidth = 0.5, linestyle = ':', color = 'k')

        Fiprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Fiprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Fiprofiles.set_xlabel('Volumetric fraction', fontsize = self.fontsize['Label'][0], family = self.family)
        Fiprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        Fiprofiles.set_title('Material Concentration Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Fileg = Fiprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Fileg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Fileg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Cinterest(self):
        """Makes a graph of the pore water concentration at the depth of
        interest."""

        zlegend = []

        if self.system.dep == 'Deposition':
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
        else:
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Cinterest_graph  = self.outputgraphs.add_subplot(111)

        Cinterest_graph.plot(self.output.times, self.Cinterest, linewidth = 1)
        Cinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cinterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Cinterest_graph.set_title('Pore Water Concentration Time Profiles', fontsize = self.fontsize['Title'])

        Cinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.Cinterest[i,n]) > max_value:
                    max_value = abs(self.Cinterest[i,n])

        if max_value < 10**-3 or max_value >= 10**4:
            Cinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))


        Cinterestleg = Cinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Finterest(self):
        """Makes a graph of the flux at the depth of interest."""

        zlegend = []
        if self.system.dep == 'Deposition':
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
        else:
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Finterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Finterest_graph  = self.outputgraphs.add_subplot(111)

        Finterest_graph.plot(self.output.times, self.Finterest, linewidth = 1)
        Finterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Finterest_graph.set_ylabel('Flux (' + self.concunit[:-1]+ self.lengthunit + u'\u00B2' + '/' + self.timeunit+')',fontsize = self.fontsize['Label'][1], family = self.family)
        Finterest_graph.set_title('Flux Time Profiles',fontsize = self.fontsize['Title'])

        Finterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Finterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.Finterest[i,n]) > max_value:
                    max_value = abs(self.Finterest[i,n])
        if max_value < 10**-3 or max_value >= 10**4:
            Finterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Finterestleg = Finterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Finterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Finterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_qinterest(self):
        """Makes a graph of the flux at the depth of interest."""

        zlegend = []
        if self.system.dep == 'Deposition':
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' in ' + self.timeplotdatas[n].component + ' ' + str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
        else:
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' in ' + self.timeplotdatas[n].component + ' ' + str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: qinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   qinterest_graph  = self.outputgraphs.add_subplot(111)

        qinterest_graph.plot(self.output.times, self.qinterest, linewidth = 1)
        qinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        qinterest_graph.set_ylabel('Concentration (' + self.concunit[:-1] + 'kg)',fontsize = self.fontsize['Label'][1], family = self.family)
        qinterest_graph.set_title('Solid Concentration Time Profiles', fontsize = self.fontsize['Title'])

        qinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        qinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.qinterest[i,n]) > max_value:
                    max_value = abs(self.qinterest[i,n])
        if max_value < 10**-3 or max_value >= 10**4:
            qinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        qinterestleg = qinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        qinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in qinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Winterest(self):
        """Makes a graph of the flux at the depth of interest."""

        zlegend = []

        if self.system.dep == 'Deposition':
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
        else:
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Winterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Winterest_graph  = self.outputgraphs.add_subplot(111)

        Winterest_graph.plot(self.output.times, self.Winterest, linewidth = 1)
        Winterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Winterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Winterest_graph.set_title('Total Concentration Time Profiles', fontsize = self.fontsize['Title'])

        Winterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Winterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.Winterest[i,n]) > max_value:
                    max_value = abs(self.Winterest[i,n])
        if max_value < 10**-3 or max_value >= 10**4:
            Winterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Winterestleg = Winterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Winterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Winterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Cwinterest(self):
        """Makes a graph of the pore water concentration at the depth of
        interest."""

        zlegend = []

        for n in range(len(self.timeplotdatas)):
            zlegend.append(self.timeplotdatas[n].name)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cwinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Cwinterest_graph  = self.outputgraphs.add_subplot(111)

        Cwinterest_graph.plot(self.output.times, self.Cwinterest, linewidth = 1)
        Cwinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cwinterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Cwinterest_graph.set_title('Overlying Water Concentration Time Profiles', fontsize = self.fontsize['Title'])

        Cwinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cwinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.Cwinterest[i,n]) > max_value:
                    max_value = abs(self.Cwinterest[i,n])

        if max_value < 10**-3 or max_value >= 10**4:
            Cwinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))


        Cwinterestleg = Cwinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cwinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cwinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Fiinterest(self):
        """Makes a graph of the flux at the depth of interest."""

        zlegend = []

        if self.system.dep == 'Deposition':
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].component + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
        else:
            for n in range(len(self.timeplotdatas)):
                zlegend.append(self.timeplotdatas[n].component + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Fiinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])
        else:                                                   Fiinterest_graph  = self.outputgraphs.add_subplot(111)

        Fiinterest_graph.plot(self.output.times, self.Fiinterest, linewidth = 1)
        Fiinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Fiinterest_graph.set_ylabel('Volumetric Fraction',fontsize = self.fontsize['Label'][1], family = self.family)
        Fiinterest_graph.set_title('Material Fraction Time Profiles', fontsize = self.fontsize['Title'])

        Fiinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Fiinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.output.times)):
                if abs(self.Fiinterest[i,n]) > max_value:
                    max_value = abs(self.Fiinterest[i,n])
        if max_value < 10**-3 or max_value >= 10**4:
            Fiinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Fiinterestleg = Fiinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Fiinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Fiinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def modify(self, event = None):
        """Takes the user back to the Summary window for the simulation."""

        self.frame.quit()

    def make_csv_file(self, filename, chemical, MW):
        """This subroutine is used to create the output file for CapSim."""

        lengthunits = ['um', 'cm', 'm']
        concunits   = ['ug/L', 'mg/L', 'g/L', 'umol/L', 'mmol/L', 'mol/L']
        timeunits   = ['s', 'min', 'hr', 'day', 'yr']

        lengthunit  = lengthunits[self.system.lengthunits.index(self.lengthunit)]
        concunit    = concunits[self.system.concunits.index(self.concunit)]
        timeunit    = timeunits[self.system.timeunits.index(self.timeunit)]

        fluxunit    = concunit[:-2]+ ',/,'+ lengthunit + '^2' + ',/,' + timeunit


        file = open(filename + '.csv', 'w')

        file.write('CapSim,'+self.system.version + '\n\n')

        if self.chemicals.count(chemical) > 0:

            n = self.chemicals.index(chemical)

            file.write('Chemical,' + chemical + ',' + str(MW)  +'\n')

            file.write('Layers')
            for layer in self.system.layers:
                file.write(',' + layer.type)
            file.write('\n')

            file.write('Thickness')
            for layer in self.system.layers:
                file.write( ',' + str(layer.h))
            file.write('\n')

            file.write('Bioturbation,')
            if self.system.bio <> 'None':
                file.write(str(self.system.hbio))
            else:
                file.write('0')
            file.write('\n')
            file.write('\n')

            file.write('Pore water concentrations,' + concunit + '\n,Times\n Depths,')
            for t in self.output.times: file.write('%.3e,' % t)
            file.write('\n')
            for i in range(len(self.output.z)):
                file.write('%.3e,' % self.output.z[i])

                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.output.C[j, i, n])

                file.write('\n')
            file.write('\n')

            file.write('Fluxes,' + fluxunit + '\n,Times\nDepths,')
            for t in self.output.times: file.write('%.3e,' % t)
            file.write('\n')
            for i in range(len(self.output.z)):
                file.write('%.3e,' % self.output.z[i])

                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.output.F[j, i, n])

                file.write('\n')
            file.write('\n')

            file.write('Total concentrations,' + concunit  + '\n,Times\nDepths,')
            for t in self.output.times: file.write('%.3e,' % t)
            file.write('\n')

            for i in range(len(self.output.z)):
                file.write('%.3e' % self.output.z[i] + ',')

                for j in range(len(self.output.times)):
                    file.write('%.3e' % self.output.W[j, i, n] + ',')

                file.write('\n')
            file.write('\n')

            file.write('Solid concentrations,' + 'Total solid,' + concunit[:-1] + 'kg' + '\n,Times\nDepths,')
            for t in self.output.times: file.write('%.3e,' % t)
            file.write('\n')

            for i in range(len(self.output.z)):
                file.write('%.3e,' % self.output.z[i])

                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.output.q[j, i, n])

                file.write('\n')
            file.write('\n')

            for component in self.system.components:
                file.write('Solid concentrations,' + component.name + ',' + concunit[:-1] + 'kg' + '\n,Times\nDepths,')
                for t in self.output.times: file.write('%.3e,' % t)
                file.write('\n')

                for i in range(len(self.output.z)):
                    file.write('%.3e,' % self.output.z[i])

                    for j in range(len(self.output.times)):
                        file.write('%.3e,' % self.output.qm[j, i, n, self.system.components.index(component)])

                    file.write('\n')
                file.write('\n')

            if self.system.topBCtype == 'Finite mixed water column':
                file.write('Overlying water concentrations,' + concunit + '\n,Times\n Depths,')
                for t in self.output.times: file.write('%.3e,' % t)
                file.write('\n')
                file.write(',')
                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.output.Cw[j, n])
                file.write('\n')

            elif self.system.topBCtype == 'Mass transfer':
                file.write('Overlying water concentrations,' + concunit + '\n,Times\n Depths,')
                for t in self.output.times: file.write('%.3e,' % t)
                file.write('\n')
                file.write(',')
                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.system.BCs[self.system.chemicals[n].name].Cw)
                file.write('\n')

            else:
                file.write('Overlying water concentrations,' + concunit + '\n,Times\n Depths,')
                for t in self.output.times: file.write('%.3e,' % t)
                file.write('\n')
                file.write(',')
                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.system.BCs[self.system.chemicals[n].name].Co)
                file.write('\n')

        else:

            n = self.system.component_list.index(chemical)

            file.write('Material,' + chemical + '\n')

            file.write('Layers')
            for layer in self.system.layers:
                file.write(',' + layer.type)
            file.write('\n')

            file.write('Thickness')
            for layer in self.system.layers:
                file.write( ',' + str(layer.h))
            file.write('\n')

            file.write('Bioturbation,')
            if self.system.bio <> 'None':
                file.write(str(self.system.hbio))
            else:
                file.write('0')
            file.write('\n')
            file.write('\n')

            file.write('Volume fraction,' + '\n,Times\n Depths,')
            for t in self.output.times: file.write('%.3e,' % t)
            file.write('\n')
            for i in range(len(self.output.z)):
                file.write('%.3e,' % self.output.z[i])

                for j in range(len(self.output.times)):
                    file.write('%.3e,' % self.output.Fi[j, i, n])

                file.write('\n')
            file.write('\n')

class GraphEditor:

    def __init__(self, master, system, type, variable, spatialplotdatas, timeplotdatas, outputz, outputt):

        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None
        self.flag      = 0
        self.system    = system

        self.components = ['Total solid']
        for component in system.component_list:
            self.components.append(component)

        rgb            = self.master.frame.winfo_rgb(self.master.frame.cget('bg'))
        self.color     = '#%02x%02x%02x' %rgb
        self.mplrgb    = (rgb[0] / 65536., rgb[1] / 65536., rgb[2] / 65536.)

        self.types          = ['Spatial profile', 'Time profile']
        if system.biomix == 1:
            self.variables =      ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Material fraction']
            self.extravariables = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Water concentration', 'Material fraction']
        else:
            self.variables =      ['Concentration', 'Flux', 'Solid concentration', 'Total concentration']
            self.extravariables = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Water concentration']

        self.type      = StringVar(value = type)
        self.variable  = StringVar(value = variable)

        self.chemical_list  = [chemical.name     for chemical in system.chemicals]

        self.timeunit   = system.timeunit
        self.lengthunit = system.lengthunit

        self.cancelflag =  0

        self.spatialplotdatas   = [plotdata.copy() for plotdata in spatialplotdatas]
        self.timeplotdatas      = [plotdata.copy() for plotdata in timeplotdatas]

        for plotdata in self.spatialplotdatas:
            plotdata.name     = StringVar(value = plotdata.name)
            plotdata.value    = DoubleVar(value = plotdata.value)
            plotdata.type     = StringVar(value = plotdata.type)
            plotdata.component= StringVar(value = plotdata.component)

        for plotdata in self.timeplotdatas:
            plotdata.name       = StringVar(value = plotdata.name)
            plotdata.value      = DoubleVar(value = plotdata.value)
            plotdata.type       = StringVar(value = plotdata.type)
            plotdata.component  = StringVar(value = plotdata.component)

        self.outputz = outputz
        self.outputt = outputt

        self.lastvariable = self.variables[0]

    def make_widgets(self):

        self.instructions   = Label(self.tframe, text = ' Please provides the following output information                    ')

        self.startcolumn    = Label(self.tframe, text = ' ', width = 2)
        self.delcolumn      = Label(self.tframe, text = ' ', width = 8)
        self.namecolumn     = Label(self.tframe, text = ' ', width = 20)
        self.valuecolumn    = Label(self.tframe, text = ' ', width = 12)
        self.matrixcolumn   = Label(self.tframe, text = ' ', width = 20)
        self.depthcolumn    = Label(self.tframe, text = ' ', width = 21)
        self.endcolumn      = Label(self.tframe, text = ' ', width = 2)

        self.typelabel      = Label(self.tframe, bg = self.color, text = 'Type:')
        self.varilabel      = Label(self.tframe, bg = self.color, text = 'Variable:')

        self.typewidget     = OptionMenu(self.tframe, self.type,     *self.types,          command = self.updateplots)
        self.variwidget     = OptionMenu(self.tframe, self.variable, *self.variables,      command = self.updateplots)
        self.extravariwidget= OptionMenu(self.tframe, self.variable, *self.extravariables, command = self.updateplots)

        self.namelabel      = Label(self.tframe, text = 'Chemical Name')
        self.timelabel      = Label(self.tframe, text = 'Plot Time(' + self.timeunit + ')')
        self.depthlabel     = Label(self.tframe, text = 'Plot Depth (' + self.lengthunit + ')')
        self.ztlabel        = Label(self.tframe, bg = self.color, text = 'Depth from:')
        self.matrixlabel    = Label(self.tframe, bg = self.color, text = 'Phase:')

        self.blank3         = Label (self.tframe, text = ' ')

        self.botstartcolumn     = Label(self.frame, text = ' ', width = 2)
        self.botdelcolumn       = Label(self.frame, text = ' ', width = 8)
        self.botnamecolumn      = Label(self.frame, text = ' ', width = 20)
        self.botvaluecolumn     = Label(self.frame, text = ' ', width = 12)
        self.botmatrixcolumn    = Label(self.frame, text = ' ', width = 20)
        self.botdepthcolumn     = Label(self.frame, text = ' ', width = 21)
        self.botendcolumn       = Label(self.frame, text = ' ', width = 2)

        self.blank1         = Label (self.bframe, text = ' ')
        self.blank2         = Label (self.bframe, text = ' ')

        self.addwidget      = Button(self.bframe, text = 'Add plots', command = self.addplotdata, width = 20)
        self.okbutton       = Button(self.bframe, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton   = Button(self.bframe, text = 'Cancel', width = 20, command = self.Cancel)

        self.instructions.grid( row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')

        self.startcolumn.grid(  row = 1, column = 0)
        self.delcolumn.grid(    row = 1, column = 1)
        self.namecolumn.grid(   row = 1, column = 2)
        self.valuecolumn.grid(  row = 1, column = 3)
        self.matrixcolumn.grid( row = 1, column = 4)
        self.endcolumn.grid(    row = 1, column = 6)

        self.typelabel.grid(    row = 2, column = 1, sticky = 'E',  pady = 1)
        self.typewidget.grid(   row = 2, column = 2, sticky = 'WE', pady = 1)
        self.varilabel.grid(    row = 2, column = 3, sticky = 'E',  pady = 1)

        self.blank3.grid(       row = 3, column = 2)
        self.namelabel.grid(    row = 4, column = 2)
        self.matrixlabel.grid(  row = 4, column = 4)

        self.botstartcolumn.grid(  row = 0, column = 0)
        self.botdelcolumn.grid(    row = 0, column = 1)
        self.botnamecolumn.grid(   row = 0, column = 2)
        self.botvaluecolumn.grid(  row = 0, column = 3)
        self.botmatrixcolumn.grid( row = 0, column = 4)
        self.botendcolumn.grid(    row = 0, column = 6)

        self.updateplots()


    def updateplots(self, event = None):

        try:
            self.timelabel.grid_forget()
            self.depthlabel.grid_forget()
            self.ztlabel.grid_forget()
            self.depthcolumn.grid_forget()
            self.botdepthcolumn.grid_forget()
            self.ztlabel.grid_forget()
        except: pass

        for plotdata in self.spatialplotdatas:
            try: plotdata.remove_propertieswidgets()
            except:pass

        for plotdata in self.timeplotdatas:
            try: plotdata.remove_propertieswidgets()
            except:pass

        try:
            self.variwidget.grid_forget()
            self.extravariwidget.grid_forget()
        except: pass

        if self.type.get() == 'Spatial profile':
            if self.variable.get() == 'Water concentration': self.variable.set('Concentration')
            self.variwidget.grid(   row = 2, column = 4, sticky = 'WE', pady = 1)
        else:
            if self.system.topBCtype == 'Finite mixed water column':
                self.extravariwidget.grid(row = 2, column = 4, sticky = 'WE', pady = 1)
            else:
                self.variwidget.grid(     row = 2, column = 4, sticky = 'WE', pady = 1)

        row = 2

        if self.type.get() == 'Spatial profile':
            self.timelabel.grid(  row = 4, column = 3)
            for plotdata in self.spatialplotdatas:
                plotdata.number = self.spatialplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.chemical_list, self.type.get(), self.variable.get(), component_list = self.components)
                row = row + 1

        elif self.system.dep == 'Deposition':
            self.depthcolumn.grid(      row = 1, column = 5)
            self.depthlabel.grid(       row = 4, column = 3)
            self.ztlabel.grid(          row = 4, column = 5)
            self.botdepthcolumn.grid(   row = 0, column = 5)
            for plotdata in self.timeplotdatas:
                plotdata.number = self.timeplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.chemical_list, self.type.get(), self.variable.get(), component_list = self.components, depositionflag = 1)
                row = row + 1
        else:
            self.depthlabel.grid(       row = 4, column = 3)
            for plotdata in self.timeplotdatas:
                plotdata.number = self.timeplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.chemical_list, self.type.get(), self.variable.get(), component_list = self.components)
                row = row + 1

        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        self.addwidget.grid(row = row, columnspan = 11)
        row = row + 1
        self.okbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(row = row, columnspan = 11)
        row = row + 1

        self.focusbutton = self.okbutton
        self.okbutton.bind('<Return>',   self.OK)

        self.master.geometry()
        self.master.center()

    def addplotdata(self):

        if self.type.get() == 'Spatial profile':
            self.spatialplotdatas.append(PlotData(len(self.spatialplotdatas)+ 1))

            self.spatialplotdatas[-1].name      = StringVar(value = self.chemical_list[0])
            self.spatialplotdatas[-1].value     = DoubleVar(value = 0)
            self.spatialplotdatas[-1].type      = StringVar(value = 'Initial benthic surface')
            self.spatialplotdatas[-1].component = StringVar(value = 'Total solid')

        else:
            self.timeplotdatas.append(PlotData(len(self.timeplotdatas)+ 1))

            self.timeplotdatas[-1].name         = StringVar(value = self.chemical_list[0])
            self.timeplotdatas[-1].value        = DoubleVar(value = 0)
            self.timeplotdatas[-1].type         = StringVar(value = 'Initial benthic surface')
            self.timeplotdatas[-1].component    = StringVar(value = 'Total solid')

        self.updateplots()

    def delplotdata(self, number):

        if self.type.get() == 'Spatial profile':
            self.spatialplotdatas[number - 1].remove_propertieswidgets()
            self.spatialplotdatas.remove(self.spatialplotdatas[number - 1])
        else:
            self.timeplotdatas[number - 1].remove_propertieswidgets()
            self.timeplotdatas.remove(self.timeplotdatas[number - 1])

        self.updateplots()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error_flag = 0

        if self.type.get() == 'Spatial profile':
            try:
                for plotdata in self.spatialplotdatas:
                    if plotdata.value.get() < self.outputt[0]:  error_flag = 1
                    if plotdata.value.get() > self.outputt[-1]: error_flag = 1
            except:
                for plotdata in self.spatialplotdatas:
                    if plotdata.value < self.outputt[0]:  error_flag = 1
                    if plotdata.value > self.outputt[-1]: error_flag = 1

        else:
            try:
                for plotdata in self.timeplotdatas:
                    if plotdata.type == 'Initial benthic surface':
                        if plotdata.value.get() < self.outputz[0]:  error_flag = 1
                        if plotdata.value.get() > self.outputz[-1]: error_flag = 1
                    else:
                        if plotdata.value.get() < self.outputz[0] - self.outputz[0]: error_flag = 1
                        if plotdata.value.get() > self.outputz[-1]- self.outputz[0]: error_flag = 1
            except:
                for plotdata in self.timeplotdatas:
                    if plotdata.type == 'Initial benthic surface':
                        if plotdata.value < self.outputz[0]:  error_flag = 1
                        if plotdata.value > self.outputz[-1]: error_flag = 1
                    else:
                        if plotdata.value < self.outputz[0] - self.outputz[0]: error_flag = 1
                        if plotdata.value > self.outputz[-1]- self.outputz[0]: error_flag = 1

        if self.master.window.top is not None: self.master.open_toplevel()
        elif error_flag == 1: self.warning()
        else: self.master.tk.quit()

    def warning(self):

        tkmb.showerror(title = self.version, message = 'The input depth/time is out of range, please correct')
        self.focusbutton = None
        self.master.tk.lift()

    def Cancel(self):

        self.cancelflag = 1

        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

class PlotData:

    def __init__(self, number):

        self.number       = number
        self.types        = ['Initial benthic surface', 'New benthic surface']

    def copy(self):

        plotdata = PlotData(self.number)

        plotdata.name         = self.name
        plotdata.value        = self.value
        plotdata.component    = self.component
        plotdata.type         = self.type

        return plotdata

    def propertieswidgets(self, frame, row, master, chemical_list, type, variable, component_list = None, depositionflag = None):

        self.master = master
        self.frame  = frame

        self.chemical_list  = chemical_list

        self.row        = row

        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_plotdata)

        self.valuewidget    = Entry (frame, width = 8,  justify = 'center', textvariable = self.value)
        self.valuelabel     = Label (frame, width = 8,  justify = 'center', text = 'N/A')

        self.delwidget.grid(      row  = row, column = 1, padx = 2 ,pady = 1)

        if variable == 'Water concentration':
            self.valuelabel.grid(    row  = row, column = 3, padx = 2, pady = 1)
        else:
            self.valuewidget.grid(    row  = row, column = 3, padx = 2, pady = 1)

        if variable == 'Material fraction':
            if self.component.get() == 'Total solid':
                self.component.set(component_list[1])
            self.namewidget     = OptionMenu(frame, self.component, *component_list[1:])
        else:
            self.namewidget      = OptionMenu(frame, self.name, *chemical_list)

        self.namewidget.grid(     row  = row, column = 2, padx = 2 ,pady = 1, sticky = 'WE')

        if variable == 'Solid concentration':
            self.componentwidget = OptionMenu(frame, self.component, *component_list)
        elif variable == 'Concentration':
            self.componentwidget = Label (frame, width = 16,  justify = 'center', text = 'Porewater')
        elif variable == 'Total concentration':
            self.componentwidget = Label (frame, width = 16,  justify = 'center', text = 'Porewater/DOC')
        elif variable == 'Flux':
            self.componentwidget = Label (frame, width = 16,  justify = 'center', text = 'Porewater/DOC/Solid')
        elif variable == 'Water concentration':
            self.componentwidget = Label (frame, width = 16,  justify = 'center', text = 'Overlying water column')
        elif variable == 'Material fraction':
            self.componentwidget = Label (frame, width = 16,  justify = 'center', text = 'N/A')

        self.componentwidget.grid(row  = row, column = 4, padx = 2 ,pady = 1, sticky = 'WE')

        if depositionflag == 1:
            self.typewidget     = OptionMenu(frame, self.type, *self.types)
            self.typewidget.grid(     row  = row, column = 5, padx = 2, pady = 1, sticky = 'WE')

    def remove_propertieswidgets(self):

        self.delwidget.grid_forget()
        self.namewidget.grid_forget()

        try: self.typewidget.grid_forget()
        except:pass
        try: self.componentwidget.grid_forget()
        except:pass
        try: self.valuewidget.grid_forget()
        except:pass

        self.master          = 0
        self.frame           = 0
        self.delwidget       = 0
        self.namewidget      = 0
        self.valuewidget     = 0
        self.typewidget      = 0
        self.componentwidget = 0

    def get_plotdata(self):

        self.name          = self.name.get()
        self.value         = self.value.get()
        self.type          = self.type.get()
        self.component     = self.component.get()

    def del_plotdata(self):

        self.master.window.delplotdata(self.number)


class FigureEditor:

    def __init__(self, master, system, type, variable, sketch, axislimit, figuresize, legendposition, fontsize):

        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None
        self.flag      = 0
        self.system    = system
        self.type      = type
        self.variable  = variable

        rgb            = self.master.frame.winfo_rgb(self.master.frame.cget('bg'))
        self.color     = '#%02x%02x%02x' %rgb
        self.mplrgb    = (rgb[0] / 65536., rgb[1] / 65536., rgb[2] / 65536.)

        self.timeunit   = system.timeunit
        self.lengthunit = system.lengthunit

        self.xaxismin = DoubleVar(value = '%.4g' % axislimit[0])
        self.xaxismax = DoubleVar(value = '%.4g' % axislimit[1])
        self.yaxismin = DoubleVar(value = '%.4g' % axislimit[2])
        self.yaxismax = DoubleVar(value = '%.4g' % axislimit[3])

        self.figurewidth  = IntVar(value = figuresize[0])
        self.figureheight = IntVar(value = figuresize[1])

        self.titlefontsize  = IntVar(value = fontsize['Title'])
        self.xaxisfontsize  = IntVar(value = fontsize['Axis'][0])
        self.yaxisfontsize  = IntVar(value = fontsize['Axis'][1])
        self.xlabelfontsize = IntVar(value = fontsize['Label'][0])
        self.ylabelfontsize = IntVar(value = fontsize['Label'][1])
        self.legendfontsize = IntVar(value = fontsize['Legend'])

        self.legendpositions = ['Default', 'Upper right', 'Upper left', 'Lower left', 'Lower right', 'Right', 'Center left', 'Center right', 'Lower center', 'Upper center', 'Center']
        self.legendposition = StringVar(value = self.legendpositions[legendposition])

        self.sketches       = sketch['Sketches']
        self.plotsizes      = ['Default', 'User-defined']
        self.fontsizes      = ['Default', 'User-defined']

        self.sketch         = StringVar(value = sketch['Sketch'])
        self.sketchlabel    = IntVar(value = sketch['Label'])
        self.sketchline     = IntVar(value = sketch['Time'])
        self.locationline   = IntVar(value = sketch['Depth'])
        self.fontsize       = StringVar(value = fontsize['Flag'])

        self.cancelflag =  0

    def make_widgets(self):

        self.instructions   = Label(self.frame, text = ' Please provides the following output information                    ')

        self.startcolumn    = Label(self.frame, text = ' ', width = 2)
        self.delcolumn      = Label(self.frame, text = ' ', width = 12)
        self.name1column    = Label(self.frame, text = ' ', width = 6)
        self.name2column    = Label(self.frame, text = ' ', width = 2)
        self.name3column    = Label(self.frame, text = ' ', width = 6)
        self.unitcolumn     = Label(self.frame, text = ' ', width = 12)
        self.endcolumn      = Label(self.frame, text = ' ', width = 2)

        self.sizelabel      = Label(self.frame, bg = self.color, text = 'Plot size:')
        self.widthwidget    = Entry(self.frame, textvariable = self.figurewidth ,  width = 8, justify = 'center')
        self.xwidget        = Label(self.frame, bg = self.color, text = 'x', width = 2, justify = 'center')
        self.heightwidget   = Entry(self.frame, textvariable = self.figureheight , width = 8, justify = 'center')
        self.sizeunit       = Label(self.frame, bg = self.color, text = 'Pixels')

        self.xaxiswidget1    = Entry(self.frame, textvariable = self.xaxismin,  width = 8, justify = 'center')
        self.xaxiswidget2    = Label(self.frame, text = 'to'         ,  width = 2, justify = 'center')
        self.xaxiswidget3    = Entry(self.frame, textvariable = self.xaxismax,  width = 8, justify = 'center')

        self.yaxiswidget1    = Entry(self.frame, textvariable = self.yaxismin,  width = 8, justify = 'center')
        self.yaxiswidget2    = Label(self.frame, text = 'to'         ,  width = 2, justify = 'center')
        self.yaxiswidget3    = Entry(self.frame, textvariable = self.yaxismax,  width = 8, justify = 'center')

        if self.type == 'Spatial profile':
            self.yaxislabel = Label(self.frame, bg = self.color, text = 'Depth:')
            self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.lengthunit)
            if self.variable == 'Concentration':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Concentration:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Flux':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Flux:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit[:-1] + self.system.lengthunit + '^2' + '/' + self.system.timeunit)
            if self.variable == 'Solid concentration':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Solid concentration:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit[:-1] + 'kg')
            if self.variable == 'Total concentration':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Total concentration:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Water concentration':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Water column concentration:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Material fraction':
                self.xaxislabel = Label(self.frame, bg = self.color, text = 'Material fraction:')
                self.xaxisunit  = Label(self.frame, bg = self.color, text = '')
        else:
            self.xaxislabel = Label(self.frame, bg = self.color, text = 'Time:')
            self.xaxisunit  = Label(self.frame, bg = self.color, text = self.system.timeunit)
            if self.variable == 'Concentration':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Concentration:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Flux':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Flux:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit[:-1]+ '/'+ self.system.lengthunit + '^2' + '/' + self.system.timeunit)
            if self.variable == 'Solid concentration':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Solid concentration:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit[:-1] + 'kg')
            if self.variable == 'Total concentration':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Total concentration:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Water concentration':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Water column concentration:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = self.system.concunit)
            if self.variable == 'Material fraction':
                self.yaxislabel = Label(self.frame, bg = self.color, text = 'Material fraction:')
                self.yaxisunit  = Label(self.frame, bg = self.color, text = '')

        self.legendlabel    = Label(self.frame, bg = self.color, text = 'Legend:')
        self.legendwidget   = OptionMenu(self.frame, self.legendposition,  *self.legendpositions)

        self.sketchslabel   = Label(self.frame, bg = self.color, text = 'Column sketch:')
        self.sketchwidget   = OptionMenu(self.frame, self.sketch, *self.sketches, command = self.updatewidgets)

        self.typelabel      = Label(self.frame, bg = self.color, text = 'Materials:')
        self.typewidget     = Checkbutton(self.frame, variable = self.sketchlabel)

        if self.type == 'Spatial profile':
            self.linelabel  = Label(self.frame, bg = self.color, text = 'Time:')
            self.linewidget = Checkbutton(self.frame, variable = self.sketchline)
        else:
            self.linelabel  = Label(self.frame, bg = self.color, text = 'Depth:')
            self.linewidget = Checkbutton(self.frame, variable = self.locationline)

        self.fontsizelabel  = Label(self.frame, bg = self.color, text = 'Fontsize:')
        self.fontsizewidget = OptionMenu(self.frame, self.fontsize,  *self.fontsizes, command = self.updatewidgets)

        self.titlefontlabel  = Label(self.frame, bg = self.color, text = 'Title:')
        self.titlefontentry  = Entry(self.frame, textvariable = self.titlefontsize ,  width = 8, justify = 'center')
        self.titlefontunit   = Label(self.frame, bg = self.color, text = 'pt')

        self.xaxisfontlabel  = Label(self.frame, bg = self.color, text = 'X-axis:')
        self.xaxisfontentry  = Entry(self.frame, textvariable = self.xaxisfontsize ,   width = 8, justify = 'center')
        self.xaxisfontunit   = Label(self.frame, bg = self.color, text = 'pt')
        self.yaxisfontlabel  = Label(self.frame, bg = self.color, text = 'Y-axis:')
        self.yaxisfontentry  = Entry(self.frame, textvariable = self.yaxisfontsize ,   width = 8, justify = 'center')
        self.yaxisfontunit   = Label(self.frame, bg = self.color, text = 'pt')

        self.xlabelfontlabel = Label(self.frame, bg = self.color, text = 'X-Label:')
        self.xlabelfontentry = Entry(self.frame, textvariable = self.xlabelfontsize ,  width = 8, justify = 'center')
        self.xlabelfontunit  = Label(self.frame, bg = self.color, text = 'pt')
        self.ylabelfontlabel = Label(self.frame, bg = self.color, text = 'Y-Label:')
        self.ylabelfontentry = Entry(self.frame, textvariable = self.ylabelfontsize ,  width = 8, justify = 'center')
        self.ylabelfontunit  = Label(self.frame, bg = self.color, text = 'pt')

        self.legendfontlabel = Label(self.frame, bg = self.color, text = 'Legend:')
        self.legendfontentry = Entry(self.frame, textvariable = self.legendfontsize , width = 8, justify = 'center')
        self.legendfontunit  = Label(self.frame, bg = self.color, text = 'pt')

        self.blank1         = Label (self.bframe, text = ' ')
        self.blank2         = Label (self.bframe, text = ' ')

        self.okbutton       = Button(self.bframe, text = 'OK', width = 20, command = self.OK)
        self.cancelbutton   = Button(self.bframe, text = 'Cancel', width = 20, command = self.Cancel)

        self.instructions.grid( row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')

        self.startcolumn.grid(  row = 1, column = 0)
        self.delcolumn.grid(    row = 1, column = 1)
        self.name1column.grid(  row = 1, column = 2)
        self.name2column.grid(  row = 1, column = 3)
        self.name3column.grid(  row = 1, column = 4)
        self.endcolumn.grid(    row = 1, column = 5)

        self.sizelabel.grid(    row = 2, column = 1, sticky = 'E', pady = 4)
        self.widthwidget.grid(  row = 2, column = 2, sticky = 'E', pady = 2)
        self.xwidget.grid(      row = 2, column = 3)
        self.heightwidget.grid( row = 2, column = 4, sticky = 'W', pady = 2)
        self.sizeunit.grid(     row = 2, column = 5, sticky = 'W', pady = 2)

        self.xaxislabel.grid(   row = 3, column = 1, sticky = 'E', pady = 4)
        self.xaxiswidget1.grid( row = 3, column = 2, sticky = 'E', pady = 2)
        self.xaxiswidget2.grid( row = 3, column = 3, pady = 2)
        self.xaxiswidget3.grid( row = 3, column = 4, sticky = 'W', pady = 2)
        self.xaxisunit.grid(    row = 3, column = 5, sticky = 'W', pady = 2)

        self.yaxislabel.grid(   row = 4, column = 1, sticky = 'E', pady = 4)
        self.yaxiswidget1.grid( row = 4, column = 2, sticky = 'E', pady = 2)
        self.yaxiswidget2.grid( row = 4, column = 3)
        self.yaxiswidget3.grid( row = 4, column = 4, sticky = 'W', pady = 2)
        self.yaxisunit.grid(    row = 4, column = 5, sticky = 'W', pady = 2)

        self.legendlabel.grid(  row = 5, column = 1, sticky = 'E', pady = 4)
        self.legendwidget.grid( row = 5, column = 2, sticky = 'WE', columnspan = 3, pady = 1)

        self.sketchslabel.grid( row = 6, column = 1, sticky = 'E', pady = 4)
        self.sketchwidget.grid( row = 6, column = 2, sticky = 'WE', columnspan = 3, pady = 1)

        row = 0
        self.blank1.grid(row = row)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        self.okbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(row = row, columnspan = 11)
        row = row + 1

        self.okbutton.bind('<Return>',   self.OK)

        self.updatewidgets()

    def updatewidgets(self, default = None):

        try:
            self.typelabel.grid_forget()
            self.typewidget.grid_forget()
            self.linelabel.grid_forget()
            self.linewidget.grid_forget()
        except: pass

        try:
            self.fontsizelabel.grid_forget()
            self.fontsizewidget.grid_forget()
        except: pass

        try:
            self.xlabelfontlabel.grid_forget()
            self.xlabelfontentry.grid_forget()
            self.xlabelfontunit.grid_forget()
            self.ylabelfontlabel.grid_forget()
            self.ylabelfontentry.grid_forget()
            self.ylabelfontunit.grid_forget()
            self.xaxisfontlabel.grid_forget()
            self.xaxisfontentry.grid_forget()
            self.xaxisfontunit.grid_forget()
            self.yaxisfontlabel.grid_forget()
            self.yaxisfontentry.grid_forget()
            self.yaxisfontunit.grid_forget()
            self.titlefontlabel.grid_forget()
            self.titlefontentry.grid_forget()
            self.titlefontunit.grid_forget()
            self.legendfontlabel.grid_forget()
            self.legendfontentry.grid_forget()
            self.legendfontunit.grid_forget()
        except: pass

        row = 7

        if self.sketch.get() != 'Hide sketch':

            self.typelabel.grid(    row = row, column = 2, columnspan = 2, sticky = 'WE', pady = 1)
            self.typewidget.grid(   row = row, column = 4, columnspan = 1, sticky = 'WE', pady = 1)

            row = row + 1

            self.linelabel.grid(    row = row, column = 2, columnspan = 2, sticky = 'WE', pady = 1)
            self.linewidget.grid(   row = row, column = 4, columnspan = 1, sticky = 'WE', pady = 1)

            row = row + 1

        self.fontsizelabel.grid(    row = row, column = 1, sticky = 'E', pady = 1)
        self.fontsizewidget.grid(   row = row, column = 2, sticky = 'WE', columnspan = 3, pady = 1)

        row = row + 1

        if self.fontsize.get() == self.fontsizes[1]:

            self.titlefontlabel.grid( row = row, column = 2, columnspan = 1,sticky = 'E', pady = 1)
            self.titlefontentry.grid( row = row, column = 4, sticky = 'W', pady = 1)
            self.titlefontunit.grid(  row = row, column = 5, sticky = 'W', pady = 1)
            row = row + 1

            self.legendfontlabel.grid( row = row, column = 2, columnspan = 1,sticky = 'E', pady = 1)
            self.legendfontentry.grid( row = row, column = 4, sticky = 'W', pady = 1)
            self.legendfontunit.grid(  row = row, column = 5, sticky = 'W', pady = 1)
            row = row + 1

            self.xlabelfontlabel.grid( row = row, column = 2, columnspan = 1, sticky = 'E', pady = 1)
            self.xlabelfontentry.grid( row = row, column = 4, sticky = 'W', pady = 1)
            self.xlabelfontunit.grid(  row = row, column = 5, sticky = 'W', pady = 1)

            row = row + 1

            self.ylabelfontlabel.grid( row = row, column = 2, columnspan = 1,sticky = 'E', pady = 1)
            self.ylabelfontentry.grid( row = row, column = 4, sticky = 'W', pady = 1)
            self.ylabelfontunit.grid(  row = row, column = 5, sticky = 'W', pady = 1)

            row = row + 1

            self.xaxisfontlabel.grid(  row = row, column = 2, columnspan = 1, sticky = 'E', pady = 1)
            self.xaxisfontentry.grid(  row = row, column = 4, sticky = 'W', pady = 1)
            self.xaxisfontunit.grid(   row = row, column = 5, sticky = 'W', pady = 1)

            row = row + 1
            self.yaxisfontlabel.grid(  row = row, column = 2, columnspan = 1,sticky = 'E', pady = 1)
            self.yaxisfontentry.grid(  row = row, column = 4, sticky = 'W', pady = 1)
            self.yaxisfontunit.grid(   row = row, column = 5, sticky = 'W', pady = 1)

        else:

            self.titlefontsize  = IntVar(value = 12)
            self.xaxisfontsize  = IntVar(value = 8)
            self.yaxisfontsize  = IntVar(value = 8)
            self.xlabelfontsize = IntVar(value = 10)
            self.ylabelfontsize = IntVar(value = 10)
            self.legendfontsize = IntVar(value = 9)

        self.focusbutton = self.okbutton

        self.master.geometry()
        self.master.center()

    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        error_flag = 0

        if self.xaxismin.get() > self.xaxismax.get():  error_flag = 1
        if self.yaxismin.get() > self.yaxismax.get():  error_flag = 1

        if self.master.window.top is not None: self.master.open_toplevel()
        elif error_flag == 1: self.warning()
        else: self.master.tk.quit()

    def warning(self):

        tkmb.showerror(title = self.version, message = 'The minimum axis must be smaller than the maximum axis value')
        self.focusbutton = None
        self.master.tk.lift()

    def Cancel(self):

        self.cancelflag = 1

        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()


class ResultExporter:

    def __init__(self, master, system, output):
    
        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None
        self.flag      = 0
        
        self.system    = system
        self.output    = output
        self.filename  = self.master.master.window.graphpath

        self.cancelflag =  0

        self.types      = ['CSV file', 'Doc Report']
        self.chemicals  = [chemical.name for chemical in system.chemicals]
        self.MWs        = [chemical.MW   for chemical in system.chemicals]
        self.components = [component.name for component in system.components]

        if system.biomix == 1:  self.list = self.chemicals + self.components
        else:                   self.list = self.chemicals

        self.type      = StringVar(value = self.types[0])
        self.name      = StringVar(value = 'output')
        self.filepath  = StringVar(value = self.master.master.window.graphpath)
        self.chemical  = StringVar(value = self.chemicals[0])
        self.MW        = self.MWs[0]

    def make_widgets(self):

        self.instructions   = Label(self.frame, text = ' Please provides the following output information                    ')

        self.startcolumn    = Label(self.frame, text = ' ', width = 2)
        self.paracolumn     = Label(self.frame, text = ' ', width = 10)
        self.valuecolumn    = Label(self.frame, text = ' ', width = 20)
        self.browsecolumn   = Label(self.frame, text = ' ', width = 10)
        self.endcolumn      = Label(self.frame, text = ' ', width = 2)

        self.typelabel      = Label(self.frame, text = 'File type:')
        self.namelabel      = Label(self.frame, text = 'File name:')
        self.dirlabel       = Label(self.frame, text = 'File directory:')
        self.chemlabel      = Label(self.frame, text = 'Chemical:')
        self.chemblank      = Label(self.frame, text = '  ')
        
        self.typewidget     = Label(self.frame, textvariable = self.type, width = 20, justify = 'center')
        self.namewidget     = Entry(self.frame, textvariable = self.name, width = 20, justify = 'center')
        self.csvext         = Label(self.frame, text = '.csv')
        self.docext         = Label(self.frame, text = '.doc')
        
        self.dirwidget      = Entry(self.frame, textvariable = self.filepath, width = 20)
        self.dirbutton      = Button(self.frame, text = 'Browse', command = self.browse_dir, width = 8)
        self.chemwidget     = OptionMenu(self.frame, self.chemical, *self.list, command = self.click_type)

        self.okbutton      = Button(self.frame, text = 'OK', width = 15, command = self.OK)
        self.cancelbutton  = Button(self.frame, text = 'Cancel', width = 15, command = self.Cancel)
        self.blank1        = Label(self.frame, text = ' ')
        self.blank2        = Label(self.frame, text = ' ')
        
        self.instructions.grid( row = 0, column = 0, columnspan = 6, padx = 8, sticky = 'W')
        
        self.startcolumn.grid(  row = 1, column = 0)
        self.paracolumn.grid(   row = 1, column = 1)
        self.valuecolumn.grid(  row = 1, column = 2)
        self.browsecolumn.grid( row = 1, column = 3)
        self.endcolumn.grid(    row = 1, column = 4)

        self.typelabel.grid(    row = 2, column = 1, sticky = 'E',  padx = 4, pady = 1)
        self.typewidget.grid(   row = 2, column = 2, sticky = 'WE', padx = 4, pady = 1)

        self.namelabel.grid(    row = 3, column = 1, sticky = 'E',  padx = 4, pady = 1)
        self.namewidget.grid(   row = 3, column = 2,                padx = 4, pady = 1)
        
        self.dirlabel.grid(     row = 4, column = 1, sticky = 'E',  padx = 4, pady = 1)
        self.dirwidget.grid(    row = 4, column = 2,                padx = 4, pady = 1)
        self.dirbutton.grid(    row = 4, column = 3, sticky = 'WE', padx = 4, pady = 1)

        self.click_type()
        
    def click_type(self, event = None):

        try:
            self.csvext.grid_forget()
            self.docext.grid_forget()
        except: pass

        
        row = 5
        
        if self.type.get() == self.types[0]:
            
            self.csvext.grid(    row = 3, column = 3, sticky = 'W', padx = 4, pady = 1)
            self.chemlabel.grid( row = row, column = 1, sticky = 'E', padx = 4, pady = 1)
            self.chemwidget.grid(row = row, column = 2, sticky = 'WE', padx = 4, pady = 1)
            row = row + 1
        else:
            self.docext.grid(    row = 3, column = 3, sticky = 'W', padx = 4, pady = 1)
            self.chemblank.grid( row = row, column = 1, sticky = 'WE', padx = 4, pady = 1)
            row = row + 1
            
        self.blank1.grid(row = row)
        row = row + 1
        self.okbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.cancelbutton.grid(row = row, columnspan = 11)
        row = row + 1
        self.blank2.grid(row = row)
        row = row + 1
        
        self.okbutton.bind('<Return>', self.OK)
        self.focusbutton = self.okbutton
        self.master.geometry()

    def browse_dir(self, event = None):

        if self.type.get() == self.types[0]:    filetype = [('CSV files',  '*.csv')]
        else:                                   filetype = [('Word files', '*.doc')]
        
        self.filename = tkfd.asksaveasfilename(initialdir=self.filepath.get(), initialfile = self.name.get(), title='Please define the directory to save the file', filetypes = filetype)

        if self.filename.count('.csv') > 0: self.filename = self.filename[0:-4]
        if self.filename.count('.doc') > 0: self.filename = self.filename[0:-4]

        if len(self.filename) > 0:
            i = 1
            while self.filename[-i] != '/':
                i = i + 1

            self.filepath.set(self.filename[0:-i+1])
            self.name.set(self.filename[-i+1:])

        self.frame.update()
        self.focusbutton = self.okbutton        
        self.master.geometry()
        
    def OK(self, event = None):
        """Finish and move on.  Checks that the number chemicals are less than the
        total number of chemicals in database."""

        if self.chemicals.count(self.chemical.get()) > 0:
            self.MW = self.MWs[self.chemicals.index(self.chemical.get())]
        else:
            self.MW = 0

        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()
        
    def Cancel(self):
        
        self.cancelflag = 1
            
        if self.master.window.top is not None: self.master.open_toplevel()
        else: self.master.tk.quit()

def postprocess_data(system, output):
    """Shows the results of the simulation."""

    root = CapSimWindow(buttons = 2)
    root.make_window(Postprocess(root, system, output))
    root.tk.config(background = root.window.color)
    root.buttonframe.config(background = root.window.color)
    root.blank.config(background = root.window.color)
    root.mainloop()    
    main = root.main.get()
    root.destroy()
    
    return main

def postprocess_batch(type, systems, outputs):
    """Shows the results of the simulation."""

    top = CapSimWindow(buttons = 1)

    if type == 'Separate':
        for system in systems:
            output = outputs[systems.index(system)]
            postprocess = Postprocess(top, system, output, batch_type = 'batch')
            for chemical in system.chemicals:
                filename = postprocess.graphpath + '\\' + system.filename + '_' + chemical.name
                postprocess.make_csv_file(filename, chemical.name, chemical.MW)
    else:
        output_s = outputs[-1].copy()

        output_s.times = [0]

        for output in outputs:
            output_s.times = output_s.times + output.times[1:]

        output_s.C  = zeros((len(output_s.times), len(outputs[-1].z), systems[-1].nchemicals))
        output_s.F  = zeros((len(output_s.times), len(outputs[-1].z), systems[-1].nchemicals))
        output_s.q  = zeros((len(output_s.times), len(outputs[-1].z), systems[-1].nchemicals))
        output_s.W  = zeros((len(output_s.times), len(outputs[-1].z), systems[-1].nchemicals))

        output_s.C[0, (len(outputs[-1].z)-len(outputs[0].z)):, :] = outputs[0].C[0, :, :]
        output_s.F[0, (len(outputs[-1].z)-len(outputs[0].z)):, :] = outputs[0].F[0, :, :]
        output_s.q[0, (len(outputs[-1].z)-len(outputs[0].z)):, :] = outputs[0].q[0, :, :]
        output_s.W[0, (len(outputs[-1].z)-len(outputs[0].z)):, :] = outputs[0].W[0, :, :]

        time_index = 1
        for output in outputs:
            z_index = len(outputs[-1].z)-len(output.z)
            for t in range(len(output.times)-1):
                output_s.C[time_index+t, z_index:, :] = output.C[t+1, :, :]
                output_s.F[time_index+t, z_index:, :] = output.F[t+1, :, :]
                output_s.q[time_index+t, z_index:, :] = output.q[t+1, :, :]
                output_s.W[time_index+t, z_index:, :] = output.W[t+1, :, :]

            time_index = time_index + len(output.times) - 1

        postprocess = Postprocess(top, systems[-1], output_s, batch_type = 'batch')

        for chemical in systems[-1].chemicals:
            filename = postprocess.graphpath + '\\' + systems[-1].filename + '_' + chemical.name
            postprocess.make_csv_file(filename, chemical.name, chemical.MW)

    top.destroy()

def time_interpolate(tint, t, delt, Cn, Cn_plus_1):
    """Returns the interpolated concentrations at time "tint" using the
    concentrations "Cn" at time "t" and concentrations "Cn_plus_1" at time 
    "t + delt." """

    return (Cn + (tint - t) / delt * (Cn_plus_1 - Cn))

def interp_dep(zpoint, dep, delz, z, Cn):
    """Returns the interpolated concentrations at time "tint" using the
    concentrations "Cn" at time "t" and concentrations "Cn_plus_1" at time
    "t + delt." """

    jj = 0

    for j in range(len(z)-1):
        if round(z[j], 8) == 0.0: jo = j

    if round(dep, 8) > round(1.5*delz, 8):
        ans = interp(zpoint+dep, [dep]+z[jo+1:], Cn[jo:])

    else:
        for j in range(len(z)-1):
            if round(dep, 8) >= round(z[j] + 0.5 * delz,8) and round(dep,8) < round(z[j+1] + 0.5 * delz, 8):
                jj = j + 1
        ans = interp(zpoint+dep, [dep]+z[jj+1:], Cn[jj:])

    return ans
