# IMPORTS
import os
import re
import json
import datetime

# Maths
import numpy as np
from scipy.optimize import curve_fit

# PyQt
from PyQt5.QtCore import QObject, pyqtSignal

# Astropy
from astropy.io import fits
from astropy.table import Table

# Local imports
import parameters as p

class ScaleLogic(QObject):

    # SIGNALS
    signal_lamp_spectrum = pyqtSignal(list, str, str)
    signal_lamp_cal_spectrum = pyqtSignal(list,list,list,list,str,str)
    signal_curve_fit = pyqtSignal(dict)
    signal_msg = pyqtSignal(str)

    def __init__(self):

        super().__init__()

    # METHODS
    # Calculations
    def calculate_lamp_spectrum_data(self, proyection, width, data, title, lamps_dir):
        bottom_lim = int(proyection-width)
        top_lim = int(proyection+width+1)
        if bottom_lim < 0:
            bottom_lim = 0
        if top_lim > len(data):
            top_lim = len(data)
        spectrum_data = [sum(col)/len(col) for col in zip(*data[bottom_lim:top_lim])]
        self.signal_lamp_spectrum.emit(spectrum_data, title, lamps_dir)

    def fit_1(self, x, a, b):
        return a*x + b

    def fit_2(self, x, a, b, c):
        return a*(x**2) + b*x + c

    def fit_3(self, x, a, b, c, d):
        return a *(x**3) + b*(x**2) + c*x + d

    def fit_4(self, x, a, b, c, d, e):
        return a*(x**4) + b *(x**3) + c*(x**2) + d*x + e

    def poln(self, x, *args):
        return sum(c * x**i for i,c in enumerate(reversed(args)))

    def poln_fit(self, x,y,n=1):
        params,covs = curve_fit(self.poln,x,y,p0=np.ones(n+1))
        return params,covs

    def calculate_curve_fit(self, grade, x, y, xlimits):
        params = []
        xfit = np.linspace(xlimits[0], xlimits[1], 1000)
        yfit = []
        params,_ = self.poln_fit(x, y, n=int(grade))
        inversed_params,_ = self.poln_fit(y, x, n=int(grade))
        yfit = [self.poln(x, *params) for x in xfit]
        dif_y_n_fit = [ydot - self.poln(xdot, *params) for ydot,xdot in zip(y,x)]
        rms = np.sqrt(sum([dif**2 for dif in dif_y_n_fit])/len(y))
        
        self.signal_curve_fit.emit(
            {'px_to_nm':{'params':params,'xfit':xfit,'yfit':yfit,'xdots':x,'ydots':y,'rms':rms},
             'nm_to_px':{'params':inversed_params}})

    # Actions
    def read_lamp_fit_data(self, path, proyection, width):
        fit_file = path.split('/')[-1]
        try:
            with fits.open(path) as hdu_list:
                shapes = [hdu_list[i].data.shape for i in range(len(hdu_list))]
                img_i = shapes.index([shape for shape in shapes if shape != (0,0)][0])
                data = hdu_list[img_i].data
                data = np.nan_to_num(data)
            title = path.split('/')[-1]
            lamps_dir = path.split('/')[-2]
            self.calculate_lamp_spectrum_data(proyection, width, data, title, lamps_dir)
        except Exception as e:
            msg = f'Cannot open "{fit_file}", maybe is not a valid FITS file.'
            self.signal_msg.emit(msg)
            print(datetime.datetime.now(),e)
    
    def read_lamp_txt_data(self, path):
        with open(path, 'r') as file:
            lamp_cal_data = json.load(file)
        xlimits = lamp_cal_data['xlimits']
        ylimits = lamp_cal_data['ylimits']
        xdata = lamp_cal_data['xdata']
        ydata = lamp_cal_data['ydata']
        title = path.split('/')[-1]
        lamps_cal_dir = path.split('/')[-2]
        self.signal_lamp_cal_spectrum.emit(xlimits,ylimits,xdata,ydata,title,lamps_cal_dir)


    