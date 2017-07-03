# -*- coding: utf-8 -*-

#!/usr/bin/env python
#These subroutines are used in post-processing for CapSim.

import matplotlib.pyplot as plt, tkMessageBox as tkmb, math, sys, os, codecs, csv, _winreg as wreg
import matplotlib.patches  as patches
import matplotlib.gridspec as gridspec
import tkFileDialog as tkfd

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
from postprocess         import FigureEditor
from datetime            import datetime
from Tkinter             import Tk, Toplevel, Canvas, Frame, Label, Entry, Text, Button, Scrollbar, OptionMenu, StringVar, DoubleVar, IntVar, FLAT, RAISED
from PIL                 import Image, ImageTk
from textwrap            import fill

class Graphprocess:
    """Makes a window to display the simulation plots."""

    def __init__(self, master, system):
        """Constructor method."""

        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.system    = system
        rgb            = self.master.frame.winfo_rgb(self.master.frame.cget('bg'))
        self.color     = '#%02x%02x%02x' %rgb
        self.mplrgb    = (rgb[0] / 65536., rgb[1] / 65536., rgb[2] / 65536.) 
        self.tframe    = Frame(master.tframe, bg = self.color)
        self.frame     = Frame(master.frame,  bg = self.color)
        self.bframe    = Frame(master.bframe, bg = self.color)
        self.top       = None
        self.flag      = 0
        self.filename  = 'plot'

        self.lengthunit = system.lengthunit
        self.concunit   = system.concunit
        self.timeunit   = system.timeunit
        self.diffunit   = system.diffunit

        self.lengthunits = [u'\u03BCm', 'cm', 'm']
        self.concunits   = [u'\u03BCg/L', 'mg/L', 'g/L', u'\u03BCmol/L', 'mmol/L', 'mol/L']
        self.timeunits   = ['s', 'min', 'hr', 'day', 'yr']
        self.diffunits   = [u'cm\u00B2/s', u'cm\u00B2/yr']

        self.types        = ['Spatial profile', 'Time profile']
        self.variables    = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Water concentration', 'Material fraction']

        self.type        = self.types[0]
        self.variable    = self.variables[0]

        self.sketch       = {}
        self.sketch['Sketches'] = ['Hide sketch']
        self.sketch['Sketch']   = 'Hide sketch'
        self.sketch['Label']    = 1
        self.sketch['Time']     = 0
        self.sketch['Depth']    = 0

        self.profiles  =[]

        self.z          = []
        self.times      = []
        self.dep        = []
        self.Vdep       = []
        self.C          = []
        self.F          = []
        self.q          = []
        self.W          = []
        self.qm         = []
        self.Cw         = []
        self.solids     = []
        self.layer_type = []
        self.layer_h    = []
        self.hbio       = []
        self.components = []

        self.timeplotdatas      = []
        self.spatialplotdatas   = []

        self.figuresize = [600, 450]

        if master.tk.winfo_screenheight()/master.tk.winfo_screenwidth() > 3/4:
            if master.tk.winfo_screenheight()*3/5 < 450:
                self.figuresize[1] = int(master.tk.winfo_screenheight()*3/5)
                self.figuresize[0] = int(self.figuresize[1]/3*4)
        else:
            if master.tk.winfo_screenwidth()*4/5 < 600:
                self.figuresize[0] = int(master.tk.winfo_screenwidth()*4/5)
                self.figuresize[1] = int(self.figuresize[0]*3/4)

        self.axislimit  = [0, 1.2, 0, 1]
        self.legendposition = 0

        self.fontsize = {}
        self.fontsize['Flag']   = 'Default'
        self.fontsize['Title']  = 12
        self.fontsize['Label']  = [10, 10]
        self.fontsize['Axis' ]  = [8, 8]
        self.fontsize['Legend'] = 9

        self.graphpath = Filepath + '\output\\'
        self.make_graphs()

        self.gs = gridspec.GridSpec(1, 2, width_ratios=[1, 5])
        self.gs.update(left = 0.01, right = 0.95)


    def make_widgets(self):
        """Makes the widgets for the window."""

        self.master.frame.config(bg      = self.color)
        self.master.mainbutton.config(bg = self.color)
        self.master.exitbutton.config(bg = self.color)

        self.graph          = Image.open(Filepath + r'/output/%s.png' % self.filename)
        self.image          = ImageTk.PhotoImage(self.graph)
        self.graphlabel     = Label(self.frame, image = self.image, bg = self.color)

        self.blank1         = Label(self.bframe, text = ' ')
        self.blank2         = Label(self.bframe, text = ' ')
        self.blank3         = Label(self.bframe, text = ' ')

        self.importbutton = Button(self.bframe, text = 'Import profiles',   bg = self.color, command = self.importdata,  width = 20, activebackground = 'white', highlightbackground = 'black')
        self.editbutton   = Button(self.bframe, text = 'Edit plot',         bg = self.color, command = self.editplot,    width = 20, activebackground = 'white', highlightbackground = 'black')
        self.figurebutton = Button(self.bframe, text = 'Edit figure',       bg = self.color, command = self.editfigure,  width = 20, activebackground = 'white', highlightbackground = 'black')
        self.savebutton   = Button(self.bframe, text = 'Save figure',       bg = self.color, command = self.savegraph,   width = 20, activebackground = 'white', highlightbackground = 'black')

        self.graphlabel.grid(   row = 0, column = 1, padx = 40)

        self.blank1.grid(       row = 1, column = 0, columnspan = 7, padx = 40)
        self.importbutton.grid( row = 2, column = 0, columnspan = 7, padx = 40)

        self.focusbutton = self.importbutton

        self.master.geometry()
        self.master.center()

    def importdata(self, event = None):

        self.dataname = tkfd.askopenfilename(initialdir = Filepath +r'\output',  filetypes = [('Output files','*.csv')])
        if self.dataname != '':

            content       = []
            file          = open(self.dataname, 'r')
            file_content  = csv.reader(file)
            for row in file_content:    content.append(row)
            rows     = len(content)
            row = 0
            row_solids    = []
            self.components.append(['Total solid'])

            while row < rows:
                if len(content[row]) > 0:
                    if content[row][0] == 'Pore water concentrations' or content[row][0] == 'Pore Water Concentrations':  row_conc        = row
                    if content[row][0] == 'Fluxes':                         row_flux        = row
                    if content[row][0] == 'Solid concentrations':
                        if content[row][1] == 'Total solid':                row_solid       = row
                        else:
                            row_solids.append(row)
                            self.components[-1].append(content[row][1])
                    if content[row][0] == 'Total concentrations':           row_whole       = row
                    if content[row][0] == 'Overlying water concentrations': row_water       = row

                row = row + 1

            conc_converter   = 1.
            length_converter = 1.
            time_converter   = 1.

            if len(content[row_conc]) > 1:

                MW = float(content[2][2])

                concunit   = content[row_conc][1]
                lengthunit = content[row_flux][3]
                timeunit   = content[row_flux][5]

            else:
                MW = 1

                concunit   = 'ug/L'
                lengthunit = 'cm^2'
                timeunit   = 'yr'

            lengthunits = ['um^2', 'cm^2', 'm^2']
            concunits   = ['ug/L', 'mg/L', 'g/L', 'umol/L', 'mmol/L', 'mol/L']
            timeunits   = ['s', 'min', 'hr', 'day', 'yr']

            if self.concunit == self.concunits[0]: conc_converter = conc_converter
            if self.concunit == self.concunits[1]: conc_converter = conc_converter/1000
            if self.concunit == self.concunits[2]: conc_converter = conc_converter/1000/1000
            if self.concunit == self.concunits[3]: conc_converter = conc_converter/MW
            if self.concunit == self.concunits[4]: conc_converter = conc_converter/1000/MW
            if self.concunit == self.concunits[5]: conc_converter = conc_converter/1000/1000/MW

            if concunit == concunits[0]:    conc_converter = conc_converter
            if concunit == concunits[1]:    conc_converter = conc_converter * 1000
            if concunit == concunits[2]:    conc_converter = conc_converter * 1000 *1000
            if concunit == concunits[3]:    conc_converter = conc_converter * MW
            if concunit == concunits[4]:    conc_converter = conc_converter * MW* 1000
            if concunit == concunits[5]:    conc_converter = conc_converter * MW* 1000 *1000

            flux_converter  = conc_converter

            if self.lengthunit == self.lengthunits[0]:  flux_converter = flux_converter/10000/10000
            if self.lengthunit == self.lengthunits[1]:  flux_converter = flux_converter
            if self.lengthunit == self.lengthunits[2]:  flux_converter = flux_converter*100*100

            if lengthunit == lengthunits[0]:            flux_converter = flux_converter * 10000 * 10000
            if lengthunit == lengthunits[1]:            flux_converter = flux_converter
            if lengthunit == lengthunits[2]:            flux_converter = flux_converter /100/100

            if self.timeunit == self.timeunits[0]:      flux_converter = flux_converter/365.25/24/3600
            if self.timeunit == self.timeunits[1]:      flux_converter = flux_converter/24/3600
            if self.timeunit == self.timeunits[2]:      flux_converter = flux_converter/3600
            if self.timeunit == self.timeunits[3]:      flux_converter = flux_converter/60
            if self.timeunit == self.timeunits[4]:      flux_converter = flux_converter

            if timeunit == timeunits[0]:                flux_converter = flux_converter*365.25*24*3600
            if timeunit == timeunits[1]:                flux_converter = flux_converter*24*3600
            if timeunit == timeunits[2]:                flux_converter = flux_converter*3600
            if timeunit == timeunits[3]:                flux_converter = flux_converter*60
            if timeunit == timeunits[4]:                flux_converter = flux_converter


            if self.lengthunit == self.lengthunits[0]:  length_converter = length_converter * 10000
            if self.lengthunit == self.lengthunits[1]:  length_converter = length_converter
            if self.lengthunit == self.lengthunits[2]:  length_converter = length_converter / 100

            if lengthunit == lengthunits[0]:            length_converter = length_converter / 10000
            if lengthunit == lengthunits[1]:            length_converter = length_converter
            if lengthunit == lengthunits[2]:            length_converter = length_converter * 100

            if self.timeunit == self.timeunits[0]:      time_converter = time_converter*365.25*24*3600
            if self.timeunit == self.timeunits[1]:      time_converter = time_converter*24*3600
            if self.timeunit == self.timeunits[2]:      time_converter = time_converter*3600
            if self.timeunit == self.timeunits[3]:      time_converter = time_converter*60
            if self.timeunit == self.timeunits[4]:      time_converter = time_converter

            if timeunit == timeunits[0]:                time_converter = time_converter/365.25/24/3600
            if timeunit == timeunits[1]:                time_converter = time_converter/24/3600
            if timeunit == timeunits[2]:                time_converter = time_converter/3600
            if timeunit == timeunits[3]:                time_converter = time_converter/60
            if timeunit == timeunits[4]:                time_converter = time_converter


            self.z.append([])
            self.times.append([])

            row = row_conc + 2

            num_t = len(content[row]) - 2
            for t in range(num_t):
                self.times[-1].append(float(content[row][t+1]) * time_converter)

            num_z = (row_flux-2) - (row_conc+3) + 1
            for z in range(num_z):
                self.z[-1].append(float(content[row+z+1][0]) * length_converter)

            version = content[0][1]

            if float(version) >= 3.3:
                self.layer_type.append([])
                self.layer_h .append([])
                for i in range(len(content[3])-1):
                    self.layer_type[-1].append(content[3][i+1])
                    self.layer_h[-1].append(float(content[4][i+1]))

                self.hbio.append(float(content[5][1]))
            else:
                self.layer_type.append([])
                self.layer_h .append([])
                self.layer_type[-1].append('NA')
                self.layer_h[-1].append(self.z[-1][-1]-self.z[-1][0])

                self.hbio.append(0)

            if self.z[-1][0] < 0:
                self.dep.append(1)
                #self.Vdep.append(-self.z[-1][0]/self.times[-1][-1])
                self.Vdep.append(self.layer_h[-1][0])
            else:
                self.dep.append(0)
                self.Vdep.append(0)

            self.C.append(zeros([num_t, num_z]))
            self.F.append(zeros([num_t, num_z]))
            self.q.append(zeros([num_t, num_z]))
            self.W.append(zeros([num_t, num_z]))
            self.qm.append(zeros([num_t, num_z, len(row_solids)]))
            self.Cw.append(zeros(num_t))

            for z in range(num_z):
                for t in range(num_t):
                    self.C[-1][t,z] = float(content[row_conc + 3 + z][1 + t]) * conc_converter
                    self.F[-1][t,z] = float(content[row_flux + 3 + z][1 + t]) * flux_converter
                    self.q[-1][t,z] = float(content[row_solid + 3 + z][1 + t])* conc_converter
                    self.W[-1][t,z] = float(content[row_whole + 3 + z][1 + t])* conc_converter
                    for n in range(len(row_solids)):
                        self.qm[-1][t,z,n] = float(content[row_solids[n] + 3 + z][1 + t])* conc_converter

            if row_water != 0:
                for t in range(num_t):
                    self.Cw[-1][t]      = float(content[row_water + 3][1 + t]) * conc_converter

            profilename = self.dataname[:-4]
            p = len(profilename) - 1
            while profilename[p] <> '/':
                p = p - 1

            try: self.profiles.remove('None profile')
            except:pass
            self.profiles.append(profilename[p+1:])

            self.update_widgets()
            self.updategraph()


    def show_error(self, event = None):

        tkmb.showerror(title = 'Run Error', message = 'Unable to process the file')


    def update_widgets(self):

        try:
            self.editbutton.grid_forget()
            self.figurebutton.grid_forget()
            self.savebutton.grid_forget()
        except: pass

        if len(self.profiles) > 1:
            self.editbutton.grid(   row = 3, column = 0, columnspan = 7, padx = 40)
            self.figurebutton.grid( row = 4, column = 0, columnspan = 7, padx = 40)
            self.savebutton.grid(   row = 5, column = 0, columnspan = 7)

        elif len(self.profiles) == 1:

            self.editbutton.grid(   row = 3, column = 0, columnspan = 7, padx = 40)
            self.figurebutton.grid( row = 4, column = 0, columnspan = 7, padx = 40)
            self.savebutton.grid(   row = 5, column = 0, columnspan = 7)

            for i in range(6):
                self.spatialplotdatas.append(PlotData(i))
                self.spatialplotdatas[-1].name      = self.profiles[0]
                self.spatialplotdatas[-1].value     = round(self.times[0][-1]/5*i, 1)
                self.spatialplotdatas[-1].type      = self.spatialplotdatas[-1].types[0]
                self.spatialplotdatas[-1].component = 'Total solid'

            self.timeplotdatas               = [PlotData(0)]
            self.timeplotdatas[-1].name      = self.profiles[0]
            self.timeplotdatas[-1].value     = 0
            self.timeplotdatas[-1].type      = self.timeplotdatas[-1].types[0]
            self.timeplotdatas[-1].component = 'Total solid'

            self.Cplot = []
            for n in range(len(self.spatialplotdatas)):
                chemnum = 0
                i = 0
                print(self.spatialplotdatas[n].value)
                while self.spatialplotdatas[n].value > self.times[0][i+1]:
                    i = i + 1
                    print(self.times[0][i+1])
                self.Cplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.C[chemnum][i, :], self.C[chemnum][i + 1, :]))

            self.axislimit  = [0, 1.2 * max([self.Cplot[n].max() for n in range(len(self.spatialplotdatas))]), min(self.z[0]), max(self.z[0])]
            self.legendposition = 0

        self.sketch['Sketches'] = ['Hide sketch']

        for i in self.profiles: self.sketch['Sketches'].append(i)

        self.sketch['Sketch'] = self.sketch['Sketches'][0]

        self.master.geometry()
        self.master.center()


    def editplot(self, event = None):

        if self.top is None:
            self.top = CapSimWindow(master = self.master, buttons = 2)
            self.top.make_window(GraphEditor(self.top, self.system, self.type, self.variable, self.profiles, self.components, self.dep, self.spatialplotdatas, self.timeplotdatas, self.z, self.times))

            self.top.tk.mainloop()

            if self.top.window.cancelflag == 0:
                self.type     = self.top.window.type.get()
                self.variable = self.top.window.variable.get()

                for spatialplotdata in self.top.window.spatialplotdatas:  spatialplotdata.get_plotdata()
                for timeplotdata in self.top.window.timeplotdatas:        timeplotdata.get_plotdata()

                self.spatialplotdatas = [spatialplotdata.copy() for spatialplotdata in self.top.window.spatialplotdatas]
                self.timeplotdatas    = [timeplotdata.copy()    for timeplotdata    in self.top.window.timeplotdatas]

                if self.type == self.types[0]:

                    self.axislimit[3] = max([max(self.z[self.profiles.index(self.spatialplotdatas[n].name)]) for n in range(len(self.spatialplotdatas))])
                    self.axislimit[2] = min([min(self.z[self.profiles.index(self.spatialplotdatas[n].name)]) for n in range(len(self.spatialplotdatas))])

                    if self.variable == self.variables[0]:
                        self.Cplot = []
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.times[chemnum][i+1]: i = i + 1
                            self.Cplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.C[chemnum][i, :], self.C[chemnum][i + 1, :]))

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2  * max([self.Cplot[n].max() for n in range(len(self.spatialplotdatas))])

                    if self.variable == self.variables[1]:
                        self.Fplot = []
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.times[chemnum][i+1]: i = i + 1
                            self.Fplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.F[chemnum][i, :], self.F[chemnum][i + 1, :]))

                        if max([max(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))]) < 0:     Fmax = 0.8 * max([max(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))])
                        else:                                                                                Fmax = 1.2 * max([max(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))])

                        if min([min(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))]) < 0:     Fmin = 1.2 * min([min(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))])
                        else:                                                                                Fmin = 0.8 * min([min(self.Fplot[n][1:]) for n in range(len(self.spatialplotdatas))])

                        self.axislimit[0]  = Fmin
                        self.axislimit[1]  = Fmax

                    if self.variable == self.variables[2]:

                        self.qplot = []
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.times[chemnum][i+1]: i = i + 1
                            if self.spatialplotdatas[n].component == 'Total solid':
                                self.qplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.q[chemnum][i, :], self.q[chemnum][i + 1, :]))
                            else:
                                compnum = self.components[chemnum].index(self.spatialplotdatas[n].component) - 1
                                self.qplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.qm[chemnum][i, :, compnum], self.qm[chemnum][i + 1, :, compnum]))

                        qmax = 0
                        for j in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[j].name)
                            for i in range(len(self.z[chemnum])):
                                if self.qplot [j][i] > qmax and isnan(self.qplot [j][i]) == 0:
                                    qmax = self.qplot [j][i]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * max([self.qplot[n].max() for n in range(len(self.spatialplotdatas))])

                    if self.variable == self.variables[3]:

                        self.Wplot = []
                        for n in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
                            i = 0
                            while self.spatialplotdatas[n].value > self.times[chemnum][i+1]: i = i + 1
                            self.Wplot.append(time_interpolate(self.spatialplotdatas[n].value, self.times[chemnum][i], self.times[chemnum][i + 1] - self.times[chemnum][i], self.W[chemnum][i, :], self.W[chemnum][i + 1, :]))

                        Wmax = 0
                        for j in range(len(self.spatialplotdatas)):
                            chemnum = self.profiles.index(self.spatialplotdatas[j].name)
                            for i in range(len(self.z[chemnum])):
                                if self.Wplot [j][i] > Wmax and isnan(self.Wplot [j][i]) == 0:
                                    Wmax = self.Wplot [j][i]

                        self.axislimit[0]  = 0
                        self.axislimit[1]  = 1.2 * max([self.Wplot[n].max() for n in range(len(self.spatialplotdatas))])

                if self.type == self.types[1]:

                    self.axislimit[0] = 0
                    self.axislimit[1] = max([max(self.times[self.profiles.index(self.timeplotdatas[n].name)]) for n in range(len(self.timeplotdatas))])

                    if self.variable == self.variables[0]:
                        Cmax = 0
                        self.Cinterest  = []
                        for n in range(len(self.timeplotdatas)):
                            self.Cinterest.append([])
                            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                            for i in range (len(self.times[chemnum])):
                                if self.dep[chemnum] == 1 and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    self.Cinterest[-1].append(interp_dep(self.timeplotdatas[n].value, -self.Vdep[chemnum]*self.times[chemnum][i], (self.z[chemnum][0]-self.z[chemnum][1]), self.z[chemnum], self.C[chemnum][i,:]))
                                else:
                                    self.Cinterest[-1].append(interp(self.timeplotdatas[n].value, self.z[chemnum], self.C[chemnum][i,:]))
                            if max(self.Cinterest[-1]) > Cmax: Cmax = max(self.Cinterest[-1])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = Cmax*1.2

                    if self.variable == self.variables[1]:
                        Fmax = 0
                        self.Finterest  = []
                        for n in range(len(self.timeplotdatas)):
                            self.Finterest.append([])
                            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                            for i in range (len(self.times[chemnum])):
                                if self.dep[chemnum] == 1 and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    self.Finterest[-1].append(interp_dep(self.timeplotdatas[n].value, -self.Vdep[chemnum]*self.times[chemnum][i],(self.z[chemnum][0]-self.z[chemnum][1]),  self.z[chemnum], self.F[chemnum][i,:]))
                                else:
                                    self.Finterest[-1].append(interp(self.timeplotdatas[n].value, self.z[chemnum], self.F[chemnum][i,:]))

                        if max([max(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))]) < 0:     Fmax = 0.8 * max([max(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))])
                        else:                                                                                 Fmax = 1.2 * max([max(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))])

                        if min([min(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))]) < 0:     Fmin = 1.2 * min([min(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))])
                        else:                                                                                 Fmin = 0.8 * min([min(self.Finterest[n][1:]) for n in range(len(self.timeplotdatas))])

                        self.axislimit[2]  = Fmin
                        self.axislimit[3]  = Fmax

                    if self.variable == self.variables[2]:
                        qmax            = 0
                        self.qinterest  = []
                        for n in range(len(self.timeplotdatas)):
                            self.qinterest.append([])
                            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                            for i in range (len(self.times[chemnum])):
                                if self.dep[chemnum] == 1 and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    if self.timeplotdatas[n].component == 'Total solid':
                                        self.qinterest[-1].append(interp_dep(self.timeplotdatas[n].value, -self.Vdep[chemnum]*self.times[chemnum][i], (self.z[chemnum][0]-self.z[chemnum][1]), self.z[chemnum], self.q[chemnum][i,:]))
                                    else:
                                        compnum = self.components[chemnum].index(self.timeplotdatas[n].component)
                                        self.qinterest[-1].append(interp_dep(self.timeplotdatas[n].value, -self.Vdep[chemnum]*self.times[chemnum][i], (self.z[chemnum][0]-self.z[chemnum][1]), self.z[chemnum], self.qm[chemnum][i,:, compnum]))

                                else:
                                    if self.timeplotdatas[n].component == 'Total solid':
                                        self.qinterest[-1].append(interp(self.timeplotdatas[n].value, self.z[chemnum], self.q[chemnum][i,:]))
                                    else:
                                        compnum = self.components[chemnum].index(self.timeplotdatas[n].component) - 1
                                        self.qinterest[-1].append(interp(self.timeplotdatas[n].value, self.z[chemnum], self.qm[chemnum][i,:, compnum]))
                            if max(self.qinterest[-1]) > qmax: qmax = max(self.qinterest[-1])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = qmax*1.2

                    if self.variable == self.variables[3]:
                        Wmax = 0
                        self.Winterest  = []
                        for n in range(len(self.timeplotdatas)):
                            self.Winterest.append([])
                            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                            for i in range (len(self.times[chemnum])):
                                if self.dep[chemnum] == 1 and self.timeplotdatas[n].type == self.timeplotdatas[n].types[1]:
                                    self.Winterest[-1].append(interp_dep(self.timeplotdatas[n].value, -self.Vdep[chemnum]*self.times[chemnum][i], (self.z[chemnum][0]-self.z[chemnum][1]), self.z[chemnum], self.W[chemnum][i,:]))
                                else:
                                    self.Winterest[-1].append(interp(self.timeplotdatas[n].value, self.z[chemnum], self.W[chemnum][i,:]))
                            if max(self.Winterest[-1]) > Wmax: Wmax = max(self.Winterest[-1])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = Wmax*1.2

                    if self.variable == 'Water concentration':
                        Cwmax = 0

                        self.Cwinterest  = []
                        for n in range(len(self.timeplotdatas)):
                            self.Cwinterest.append([])
                            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                            for i in range (len(self.times[chemnum])):
                                self.Cwinterest[-1].append(self.Cw[chemnum][i])
                            if max(self.Cwinterest[-1]) > Cwmax: Cwmax = max(self.Cwinterest[-1])

                        self.axislimit[2]  = 0
                        self.axislimit[3]  = Cwmax*1.2

                        if self.axislimit[3] == 0:
                            self.axislimit[2] = -1e-3
                            self.axislimit[3] = 1e-3

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

        try:
            self.graphlabel.grid_forget()
        except: pass

        self.make_graphs()
        
        self.graph      = Image.open(Filepath + r'/output/%s.png' % self.filename)
        self.image      = ImageTk.PhotoImage(self.graph)
        self.graphlabel = Label(self.frame, image = self.image, bg = self.color)

        self.graphlabel.grid( row = 0, column = 0, columnspan = 7, padx = 40)
            
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
        else:
            self.outputgraphs = plt.figure(figsize=(self.figuresize[0]/100, self.figuresize[1]/100))
            self.make_sketch_image()

        if len(self.profiles) >= 1:
            if self.type == self.types[0]:
                if self.variable == 'Concentration':
                    self.make_C_profiles()
                if self.variable == 'Flux':
                    self.make_F_profiles()
                if self.variable == 'Total concentration':
                    self.make_W_profiles()
                if self.variable == 'Solid concentration':
                    self.make_q_profiles()

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

        else:
            self.make_blank_graphs()

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

    def make_blank_graphs(self):
        """Makes plots of concentration profiles over time."""

        blankprofiles  = self.outputgraphs.add_subplot(111)

        blankprofiles.text(0.35,0.5,'Please import profiles',fontsize=15)

        blankprofiles.set_xlabel('Concentration ('+self.concunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        blankprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family =self.family)

    def make_sketch_image(self):
        """Makes plots of concentration profiles over time."""

        Sketchprofiles  = self.outputgraphs.add_subplot(self.gs[0])

        pnum    = self.profiles.index(self.sketch['Sketch'])
        Htotal  = self.z[pnum][-1] - self.z[pnum][0]

        sfont = {9:6, 10:7, 11:7.5, 12:8, 13:9}

        H = 0
        color_step = round(0.5/len(self.layer_h[pnum]),2)
        Blocks = []

        for i in range(len(self.layer_h[pnum])):
            if self.dep[pnum] == 0 or i > 0:
                Blocks.append(patches.Rectangle((0.0, H), 0.99, self.layer_h[pnum][i], facecolor = str( 0.75 - color_step * i), edgecolor = 'k', linestyle = 'solid', linewidth = '1'))
                Sketchprofiles.add_patch(Blocks[-1])
                if self.sketch['Label'] == 1:
                    rx, ry = Blocks[-1].get_xy()
                    cx = rx + Blocks[-1].get_width()/2.0
                    cy = ry + Blocks[-1].get_height()/2.0
                    if Blocks[-1].get_height()/Htotal*self.figuresize[1] >= 14:
                        Sketchprofiles.annotate(fill(self.layer_type[pnum][i], 10), (cx, cy), color='w', fontsize = 10, ha='center', va='center')
                    elif Blocks[-1].get_height()/Htotal*self.figuresize[1] >= 9:
                        Sketchprofiles.annotate(fill(self.layer_type[pnum][i], 10), (cx, cy), color='w', fontsize = sfont[int(Blocks[-1].get_height()/Htotal*self.figuresize[1])], ha='center', va='center')
                H = H + self.layer_h[pnum][i]

        if self.dep[pnum] == 1:
            Blockdep = patches.Polygon(array([[0.995, self.z[pnum][0]], [0.0, 0.0], [0.995, 0.0]]), facecolor = '0.75', edgecolor = 'k', linestyle = 'solid', linewidth = '1')
            Sketchprofiles.add_patch(Blockdep)
            if self.sketch['Label'] == 1:
                rx, ry = 0.0, 0.0
                cx = rx + 0.995/2.0
                cy = ry + self.z[pnum][0]/2.0
                if abs(self.z[pnum][0])/Htotal*self.figuresize[1] >= 14:
                    Sketchprofiles.annotate(fill(self.layer_type[pnum][0], 10), (cx, cy), color='k', fontsize = 10, ha='center', va='center')
                elif abs(self.z[pnum][0])/Htotal*self.figuresize[1] >= 9:
                    Sketchprofiles.annotate(fill(self.layer_type[pnum][0], 10), (cx, cy), color='k', fontsize = sfont[int(abs(self.z[pnum][0])/Htotal*self.figuresize[1])], ha='center', va='center')

        if self.dep[pnum] == 1 or self.sketch['Time'] == 1:
            Sketchprofiles.annotate('0', (0, H),                                         color='k', fontsize = 10, ha='center', va='top')
            Sketchprofiles.annotate(fill(str(self.times[pnum][-1]) + self.timeunit, 6), (1.0, H), color='k', fontsize = 10, ha='center', va='top')

        if self.type == self.types[0]:
            if self.sketch['Time'] == 1:
                if self.dep[pnum] == 1:
                    for plotdata in self.spatialplotdatas:
                        Sketchprofiles.plot( [plotdata.value/self.times[pnum][-1], plotdata.value/self.times[pnum][-1]],[0-plotdata.value*self.Vdep[pnum], self.z[pnum][-1]])
                else:
                    for plotdata in self.spatialplotdatas:
                        Sketchprofiles.plot( [plotdata.value/self.times[pnum][-1], plotdata.value/self.times[pnum][-1]], [0, self.z[pnum][-1]])

        if self.type == self.types[1]:
            if self.sketch['Depth'] == 1:
                for plotdata in self.timeplotdatas:
                    if plotdata.type == plotdata.types[0]:
                        Sketchprofiles.plot([0.0, 1.0], [plotdata.value, plotdata.value])
                    else:
                        Sketchprofiles.plot([0.0, 1.0], [plotdata.value, plotdata.value + self.z[pnum][0]])

        if self.hbio[pnum] <> 0 :
            Sketchprofiles.plot([0.0, 1.0], [self.hbio[pnum], self.hbio[pnum] + self.z[pnum][0]], linestyle = ':', color = 'k')

        Sketchprofiles.axis('off')
        if self.type == self.types[0]:
            Sketchprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])
        else:
            Sketchprofiles.set_ylim([max(self.z[pnum]), min(self.z[pnum])])

    def make_C_profiles(self):
        """Makes plots of concentration profiles over time."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cprofiles  = self.outputgraphs.add_subplot(111)
        else:                                                   Cprofiles  = self.outputgraphs.add_subplot(self.gs[1])

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)

        for n in range(len(self.spatialplotdatas)):
            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
            if self.dep[chemnum] == 1:
                time = self.spatialplotdatas[n].value
                dep = -self.Vdep[chemnum] * time
                i = 0
                while round(self.z[chemnum][i] + 0.5*(self.z[chemnum][1]-self.z[chemnum][0]), 8) < round(dep, 8)  : i = i + 1
                if round(-dep, 8) < 1.5 * (self.z[chemnum][1]-self.z[chemnum][0]) and round(-dep, 8) >= 0.5 * (self.z[chemnum][1]-self.z[chemnum][0]):
                    Cs = self.Cplot[n][i+2:]
                    zs = self.z[chemnum][i+2:]
                else:
                    Cs = self.Cplot[n][i+1:]
                    zs = self.z[chemnum][i+1:]
                zs[0] = -self.Vdep[chemnum] * time
                Cprofiles.plot(Cs, zs, linewidth = 0.5)
            else:
                Cs = self.Cplot[n][:]
                zs = self.z[chemnum][:]
                Cprofiles.plot(Cs, zs, linewidth = 0.5)


        Cprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Cprofiles.set_xlabel('Concentration ('+self.concunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][0], family =self.family)
        Cprofiles.set_title(' Pore Water Concentration Depth Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Cleg = Cprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cleg.get_texts(): 
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_F_profiles(self):
        """Makes a graph of the total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Fprofiles  = self.outputgraphs.add_subplot(111)
        else:                                                   Fprofiles  = self.outputgraphs.add_subplot(self.gs[1])

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' in ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)

        for n in range(len(self.spatialplotdatas)):
            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
            if self.dep[chemnum] == 1:
                time = self.spatialplotdatas[n].value
                dep = -self.Vdep[chemnum] * time
                i = 0
                while round(self.z[chemnum][i] + 0.5*(self.z[chemnum][1]-self.z[chemnum][0]), 8) < round(dep, 8)  : i = i + 1
                if round(-dep, 8) < 1.5 * (self.z[chemnum][1]-self.z[chemnum][0]) and round(-dep, 8) >= 0.5 * (self.z[chemnum][1]-self.z[chemnum][0]):
                    Fs = self.Fplot[n][i+2:]
                    zs = self.z[chemnum][i+2:]
                else:
                    Fs = self.Fplot[n][i+1:]
                    zs = self.z[chemnum][i+1:]
                zs[0] = -self.Vdep[chemnum] * time

                Fprofiles.plot(Fs, zs, linewidth = 0.5)
            else:
                Fs = self.Fplot[n][:]
                zs = self.z[chemnum][:]
                Fprofiles.plot(Fs, zs, linewidth = 0.5)

        Fprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Fprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Fprofiles.set_xlabel('Flux (' + self.concunit[:-1] + self.lengthunit + u'\u00B2' + '/' + self.timeunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Fprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        Fprofiles.set_title('Flux Depth Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Fleg = Fprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Fleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Fleg.get_texts(): 
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_q_profiles(self):
        """Makes a graph of the total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: qprofiles  = self.outputgraphs.add_subplot(111)
        else:                                                   qprofiles  = self.outputgraphs.add_subplot(self.gs[1])

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  self.spatialplotdatas[n].component + ' ' +str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)

        for n in range(len(self.spatialplotdatas)):
            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
            if self.dep[chemnum] == 1:
                time = self.spatialplotdatas[n].value
                dep = -self.Vdep[chemnum] * time
                i = 0
                while round(self.z[chemnum][i] + 0.5*(self.z[chemnum][1]-self.z[chemnum][0]), 8) < round(dep, 8)  : i = i + 1
                if round(-dep, 8) < 1.5 * (self.z[chemnum][1]-self.z[chemnum][0]) and round(-dep, 8) >= 0.5 * (self.z[chemnum][1]-self.z[chemnum][0]):
                    qs = self.qplot[n][i+2:]
                    zs = self.z[chemnum][i+2:]
                else:
                    qs = self.qplot[n][i+1:]
                    zs = self.z[chemnum][i+1:]
                zs[0] = -self.Vdep[chemnum] * time

                qprofiles.plot(qs, zs, linewidth = 0.5)
            else:
                qs = self.qplot[n][:]
                zs = self.z[chemnum][:]
                qprofiles.plot(qs, zs, linewidth = 0.5)

        qprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        qprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        qprofiles.set_xlabel('Concentration ('+self.concunit[:-1]+'kg)', fontsize = self.fontsize['Label'][0], family = self.family)
        qprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        qprofiles.set_title('Solid Concentration Depth Profiles', fontsize = self.fontsize['Title'], family = self.family)
        qleg = qprofiles.legend(tlegend, loc = self.legendposition,labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        qleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in qleg.get_texts(): 
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_W_profiles(self):
        """Makes a graph of the total concentration at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Wprofiles  = self.outputgraphs.add_subplot(111)
        else:                                                   Wprofiles  = self.outputgraphs.add_subplot(self.gs[1])

        tlegend = []
        for n in range(len(self.spatialplotdatas)):
            tlegend.append(self.spatialplotdatas[n].name + ' ' +  str(self.spatialplotdatas[n].value) + ' ' + self.timeunit)

        for n in range(len(self.spatialplotdatas)):
            chemnum = self.profiles.index(self.spatialplotdatas[n].name)
            if self.dep[chemnum] == 1:
                time = self.spatialplotdatas[n].value
                dep = -self.Vdep[chemnum] * time
                i = 0
                while round(self.z[chemnum][i] + 0.5*(self.z[chemnum][1]-self.z[chemnum][0]), 8) < round(dep, 8)  : i = i + 1
                if round(-dep, 8) < 1.5 * (self.z[chemnum][1]-self.z[chemnum][0]) and round(-dep, 8) >= 0.5 * (self.z[chemnum][1]-self.z[chemnum][0]):
                    Ws = self.Wplot[n][i+2:]
                    zs = self.z[chemnum][i+2:]
                else:
                    Ws = self.Wplot[n][i+1:]
                    zs = self.z[chemnum][i+1:]
                zs[0] = -self.Vdep[chemnum] * time

                Wprofiles.plot(Ws, zs, linewidth = 0.5)
            else:
                Ws = self.Wplot[n][:]
                zs = self.z[chemnum][:]
                Wprofiles.plot(Ws, zs, linewidth = 0.5)

        Wprofiles.set_xlim([self.axislimit[0], self.axislimit[1]])
        Wprofiles.set_ylim([self.axislimit[3], self.axislimit[2]])

        Wprofiles.set_xlabel('Concentration ('+self.concunit+')', fontsize = self.fontsize['Label'][0], family = self.family)
        Wprofiles.set_ylabel('Depth ('+self.lengthunit+')', fontsize = self.fontsize['Label'][1], family = self.family)
        Wprofiles.set_title('Pore Space Concentration Depth Profiles', fontsize = self.fontsize['Title'], family = self.family)
        Wleg = Wprofiles.legend(tlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Wleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Wleg.get_texts(): 
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Cinterest(self):
        """Makes a graph of the pore water concentration at the depth of 
        interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cinterest_graph  = self.outputgraphs.add_subplot(111)
        else:                                                   Cinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])

        zlegend         = []

        if self.dep.count(1) >= 1:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit+ ' from ' + self.timeplotdatas[n].type)
                Cinterest_graph.plot(self.times[chemnum], self.Cinterest[n], linewidth = 1)
        else:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)
                Cinterest_graph.plot(self.times[chemnum], self.Cinterest[n], linewidth = 1)

        Cinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cinterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Cinterest_graph.set_title('Pore Water Concentration Time Profiles', fontsize = self.fontsize['Title'])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            chemnum         = self.profiles.index(self.timeplotdatas[n].name)
            for i in range (len(self.times[chemnum])):
                if abs(self.Cinterest[n][i]) > max_value:
                    max_value = abs(self.Cinterest[n][i])
        if max_value < 10**-3 or max_value >= 10**4:
            Cinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Cinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        Cinterestleg = Cinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Finterest(self):
        """Makes a graph of the flux at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Finterest_graph  = self.outputgraphs.add_subplot(111)
        else:                                                   Finterest_graph  = self.outputgraphs.add_subplot(self.gs[1])

        zlegend         = []
        if self.dep.count(1) >= 1:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
                Finterest_graph.plot(self.times[chemnum], self.Finterest[n], linewidth = 1)

        else:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)
                Finterest_graph.plot(self.times[chemnum], self.Finterest[n], linewidth = 1)

        Finterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Finterest_graph.set_ylabel('Flux (' + self.concunit[:-1]+ self.lengthunit + u'\u00B2' + '/' + self.timeunit+')',fontsize = self.fontsize['Label'][1], family = self.family)
        Finterest_graph.set_title('Flux Time Profiles',fontsize =  self.fontsize['Title'])

        Finterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Finterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.times)):
                if abs(self.Finterest[n][i]) > max_value:
                    max_value = abs(self.Finterest[n][i])
        if max_value < 10**-3 or max_value >= 10**4:
            Finterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Finterestleg = Finterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Finterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Finterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_qinterest(self):
        """Makes a graph of the flux at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: qinterest_graph  = self.outputgraphs.add_subplot(111)
        else:                                                   qinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])

        zlegend         = []

        if self.dep.count(1) >= 1:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' in ' +  self.timeplotdatas[n].component + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
                qinterest_graph.plot(self.times[chemnum], self.qinterest[n], linewidth = 1)
        else:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' in ' +  self.spatialplotdatas[n].component + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)
                qinterest_graph.plot(self.times[chemnum], self.qinterest[n], linewidth = 1)

        qinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        qinterest_graph.set_ylabel('Concentration (' + self.concunit[:-1] + 'kg)',fontsize = self.fontsize['Label'][1], family = self.family)
        qinterest_graph.set_title('Solid Concentration Time Profiles', fontsize = self.fontsize['Title'])

        qinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        qinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.times)):
                if abs(self.qinterest[n][i]) > max_value:
                    max_value = abs(self.qinterest[n][i])
        if max_value < 10**-3 or max_value >= 10**4:
            qinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        qinterestleg = qinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        qinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in qinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def make_Winterest(self):
        """Makes a graph of the flux at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Winterest_graph  = self.outputgraphs.add_subplot(111)
        else:                                                   Winterest_graph  = self.outputgraphs.add_subplot(self.gs[1])

        zlegend         = []
        Wmax            = 0

        if self.dep.count(1) >= 1:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
                Winterest_graph.plot(self.times[chemnum], self.Winterest[n], linewidth = 1)
        else:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)
                Winterest_graph.plot(self.times[chemnum], self.Winterest[n], linewidth = 1)

        Winterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Winterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Winterest_graph.set_title('Pore Space Concentration Time Profiles', fontsize = self.fontsize['Title'])

        Winterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Winterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.times)):
                if abs(self.Winterest[n][i]) > max_value:
                    max_value = abs(self.Winterest[n][i])
        if max_value < 10**-3 or max_value >= 10**4:
            Winterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Winterestleg = Winterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Winterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Winterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)


    def make_Cwinterest(self):
        """Makes a graph of the flux at the depth of interest."""

        if self.sketch['Sketch'] == self.sketch['Sketches'][0]: Cwinterest_graph  = self.outputgraphs.add_subplot(111)
        else:                                                   Cwinterest_graph  = self.outputgraphs.add_subplot(self.gs[1])

        zlegend         = []
        Cwmax           = 0

        if self.dep.count(1) >= 1:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit + ' from ' + self.timeplotdatas[n].type)
                Cwinterest_graph.plot(self.times[chemnum], self.Cwinterest[n], linewidth = 1)
        else:
            for n in range(len(self.timeplotdatas)):
                chemnum         = self.profiles.index(self.timeplotdatas[n].name)
                zlegend.append(self.timeplotdatas[n].name + ' ' +  str(self.timeplotdatas[n].value) + ' ' + self.lengthunit)
                Cwinterest_graph.plot(self.times[chemnum], self.Cwinterest[n], linewidth = 1)

        Cwinterest_graph.set_xlabel('Time (' + self.timeunit + ')', fontsize = self.fontsize['Label'][0], family = self.family)
        Cwinterest_graph.set_ylabel('Concentration (' + self.concunit + ')',fontsize = self.fontsize['Label'][1], family = self.family)
        Cwinterest_graph.set_title('Overlying Water Column Concentration Time Profiles', fontsize = self.fontsize['Title'])

        Cwinterest_graph.set_xlim([self.axislimit[0], self.axislimit[1]])
        Cwinterest_graph.set_ylim([self.axislimit[2], self.axislimit[3]])

        max_value = 0
        for n in range(len(self.timeplotdatas)):
            for i in range (len(self.times)):
                if abs(self.Cwinterest[n][i]) > max_value:
                    max_value = abs(self.Cwinterest[n][i])
        if max_value < 10**-3 or max_value >= 10**4:
            Cwinterest_graph.yaxis.set_major_formatter(plt.FormatStrFormatter('%.1e'))

        Cwinterestleg = Cwinterest_graph.legend(zlegend, loc = self.legendposition, labelspacing = 0, borderpad = 0.3, handlelength = 1.5, handletextpad = 0.1, fancybox = 0)
        Cwinterestleg.legendPatch.set_fc(plt.rcParams['axes.facecolor'])
        for caption in Cwinterestleg.get_texts():
            caption.set_fontsize(self.fontsize['Legend'])
            caption.set_fontname(self.family)

    def modify(self, event = None):
        """Takes the user back to the Summary window for the simulation."""

        self.frame.quit()

class GraphEditor:

    def __init__(self, master, system, type, variable, profiles, components, dep, spatialplotdatas, timeplotdatas, outputz, outputt):

        self.master    = master
        self.version   = system.version
        self.fonttype  = system.fonttype
        self.tframe    = Frame(master.tframe)
        self.frame     = Frame(master.frame)
        self.bframe    = Frame(master.bframe)
        self.top       = None
        self.flag      = 0
        self.system    = system


        rgb            = self.master.frame.winfo_rgb(self.master.frame.cget('bg'))
        self.color     = '#%02x%02x%02x' %rgb
        self.mplrgb    = (rgb[0] / 65536., rgb[1] / 65536., rgb[2] / 65536.)

        self.types          = ['Spatial profile', 'Time profile']
        self.variables      = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration']
        self.extravariables = ['Concentration', 'Flux', 'Solid concentration', 'Total concentration', 'Water concentration']

        self.type      = StringVar(value = type)
        self.variable  = StringVar(value = variable)

        self.profiles   = profiles
        self.components = components
        self.dep        = dep

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

    def make_widgets(self):

        self.instructions   = Label(self.tframe, text = ' Please provides the following output information                    ')

        self.startcolumn    = Label(self.tframe, text = ' ', width = 2)
        self.delcolumn      = Label(self.tframe, text = ' ', width = 8)
        self.namecolumn     = Label(self.tframe, text = ' ', width = 20)
        self.valuecolumn    = Label(self.tframe, text = ' ', width = 12)
        self.matrixcolumn   = Label(self.tframe, text = ' ', width = 20)
        self.depthcolumn    = Label(self.tframe, text = ' ', width = 21)
        self.endcolumn      = Label(self.tframe, text = ' ', width = 2)

        self.typelabel      = Label(self.tframe, bg = self.color, text = 'Plot type:')
        self.varilabel      = Label(self.tframe, bg = self.color, text = 'Plot variable:')
        self.sizelabel      = Label(self.tframe, bg = self.color, text = 'Plot size:')
        self.sizeunit       = Label(self.tframe, bg = self.color, text = 'Pixels')

        self.typewidget     = OptionMenu(self.tframe, self.type,     *self.types,     command = self.updateplots)
        self.variwidget     = OptionMenu(self.tframe, self.variable, *self.variables, command = self.updateplots)
        self.extravariwidget= OptionMenu(self.tframe, self.variable, *self.extravariables, command = self.updateplots)

        self.namelabel      = Label(self.tframe, text = 'Chemical Name')
        self.timelabel      = Label(self.tframe, text = 'Plot Time(' + self.timeunit + ')')
        self.depthlabel     = Label(self.tframe, text = 'Plot Depth (' + self.lengthunit + ')')
        self.ztlabel        = Label(self.tframe, bg = self.color, text = 'Depth from:')
        self.matrixlabel    = Label(self.tframe, bg = self.color, text = 'Phase:')

        self.blank3         = Label (self.tframe, text = ' ')

        self.botstartcolumn = Label(self.frame, text = ' ', width = 2)
        self.botdelcolumn   = Label(self.frame, text = ' ', width = 8)
        self.botnamecolumn  = Label(self.frame, text = ' ', width = 20)
        self.botvaluecolumn = Label(self.frame, text = ' ', width = 12)
        self.botmatrixcolumn= Label(self.frame, text = ' ', width = 20)
        self.botdepthcolumn = Label(self.frame, text = ' ', width = 21)
        self.botendcolumn   = Label(self.frame, text = ' ', width = 2)

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
        self.botmatrixcolumn.grid(  row = 0, column = 4)
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
            self.extravariwidget.grid(row = 2, column = 4, sticky = 'WE', pady = 1)

        row = 2

        if self.type.get() == 'Spatial profile':
            self.timelabel.grid(  row = 5, column = 3)
            for plotdata in self.spatialplotdatas:
                plotdata.number = self.spatialplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.profiles, self.type.get(), self.variable.get(), self.components)
                row = row + 1

        elif self.dep.count(1) >= 1:
            self.depthcolumn.grid(      row = 1, column = 5)
            self.depthlabel.grid(       row = 4, column = 3)
            self.ztlabel.grid(          row = 4, column = 5)
            self.botdepthcolumn.grid(   row = 0, column = 5)
            for plotdata in self.timeplotdatas:
                plotdata.number = self.timeplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.profiles, self.type.get(), self.variable.get(), self.components, depositionflag = 1)
                row = row + 1
        else:
            self.depthlabel.grid(       row = 4, column = 3)
            for plotdata in self.timeplotdatas:
                plotdata.number = self.timeplotdatas.index(plotdata) + 1
                plotdata.propertieswidgets(self.frame, row, self.master, self.profiles, self.type.get(), self.variable.get(), self.components)
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

            self.spatialplotdatas[-1].name      = StringVar(value = self.profiles[0])
            self.spatialplotdatas[-1].value     = DoubleVar(value = 0)
            self.spatialplotdatas[-1].component = StringVar(value = 'Total solid')
            self.spatialplotdatas[-1].type      = StringVar(value = 'Initial benthic surface')

        else:
            self.timeplotdatas.append(PlotData(len(self.timeplotdatas)+ 1))

            self.timeplotdatas[-1].name         = StringVar(value = self.profiles[0])
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
            for plotdata in self.spatialplotdatas:
                if plotdata.value.get() < self.outputt[self.profiles.index(plotdata.name.get())][0]:  error_flag = 1
                if plotdata.value.get() > self.outputt[self.profiles.index(plotdata.name.get())][-1]: error_flag = 1
        else:
            for plotdata in self.timeplotdatas:
                if plotdata.type == 'Initial benthic surface':
                    if plotdata.value.get() < self.outputz[self.profiles.index(plotdata.name.get())][0]:  error_flag = 1
                    if plotdata.value.get() > self.outputz[self.profiles.index(plotdata.name.get())][-1]: error_flag = 1
                else:
                    if plotdata.value.get() < self.outputz[self.profiles.index(plotdata.name.get())][0] - self.outputz[self.profiles.index(plotdata.name.get())][0]: error_flag = 1
                    if plotdata.value.get() > self.outputz[self.profiles.index(plotdata.name.get())][-1]- self.outputz[self.profiles.index(plotdata.name.get())][0]: error_flag = 1

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

        self.number   = number
        self.types    = ['Initial benthic surface', 'New benthic surface']


    def copy(self):

        plotdata = PlotData(self.number)

        plotdata.name      = self.name
        plotdata.value     = self.value
        plotdata.type      = self.type
        plotdata.component = self.component

        return plotdata

    def propertieswidgets(self, frame, row, master, chemical_list, type, variable, component_list, depositionflag = None):

        self.master = master

        self.chemical_list  = chemical_list
        self.component_list = component_list
        self.variable       = variable

        self.row        = row
        self.frame      = frame

        self.delwidget      = Button(frame, width = 5,  justify = 'center', text = 'Delete', command = self.del_plotdata)
        self.namewidget     = OptionMenu(frame, self.name, *chemical_list, command = self.click_name)
        self.valuewidget    = Entry (frame, width = 8,  justify = 'center', textvariable = self.value)
        self.valuelabel     = Label (frame, width = 8,  justify = 'center', text = 'N/A')

        self.delwidget.grid(      row  = row, column = 1, padx = 2 ,pady = 1)
        self.namewidget.grid(     row  = row, column = 2, padx = 2 ,pady = 1, sticky = 'WE')

        if variable == 'Water concentration':
            self.valuelabel.grid(    row  = row, column = 3, padx = 2, pady = 1)
        else:
            self.valuewidget.grid(    row  = row, column = 3, padx = 2, pady = 1)

        if variable == 'Solid concentration':
            self.componentwidget = OptionMenu(frame, self.component, *component_list[self.chemical_list.index(self.name.get())])
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


    def click_name(self, default = None):

        try: self.componentwidget.grid_forget()
        except: pass

        if self.variable == 'Solid concentration':
            self.componentwidget = OptionMenu(self.frame, self.component, *self.component_list[self.chemical_list.index(self.name.get())])
        elif self.variable == 'Concentration':
            self.componentwidget = Label (self.frame, width = 16,  justify = 'center', text = 'Porewater')
        elif self.variable == 'Total concentration':
            self.componentwidget = Label (self.frame, width = 16,  justify = 'center', text = 'Porewater/DOC')
        elif self.variable == 'Flux':
            self.componentwidget = Label (self.frame, width = 16,  justify = 'center', text = 'Porewater/DOC/Solid')
        elif self.variable == 'Water concentration':
            self.componentwidget = Label (self.frame, width = 16,  justify = 'center', text = 'Overlying water column')
        elif self.variable == 'Material fraction':
            self.componentwidget = Label (self.frame, width = 16,  justify = 'center', text = 'N/A')

        self.componentwidget.grid(row  = self.row, column = 4, padx = 2 ,pady = 1, sticky = 'WE')

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

        self.name       = self.name.get()
        self.value      = self.value.get()
        self.type       = self.type.get()
        self.component  = self.component.get()

    def del_plotdata(self):

        self.master.window.delplotdata(self.number)


def graphprocess_data(system):
    """Shows the results of the simulation."""

    root = CapSimWindow(buttons = 2)
    root.make_window(Graphprocess(root, system))
    root.tk.config(background = root.window.color)
    root.buttonframe.config(background = root.window.color)
    root.blank.config(background = root.window.color)

    root.mainloop()
    main = root.main.get()
    root.destroy()
    
    return main

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

    if round(dep, 8) > round(0.5*delz, 8):
        ans = interp(zpoint+dep, [dep]+z[jo+1:], Cn[jo:])

    else:
        for j in range(len(z)-1):
            if round(dep, 8) >= round(z[j] + 0.5 * delz,8) and round(dep,8) < round(z[j+1] + 0.5 * delz, 8):
                jj = j + 1
        ans = interp(zpoint+dep, [dep]+z[jj+1:], Cn[jj:])

    return ans
