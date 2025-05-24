# IMPORTS
import os
import re
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

class MainLogic(QObject):

    # SIGNALS
    signal_fit_data = pyqtSignal(np.ndarray, str, str)
    signal_update_stretch = pyqtSignal(float)
    signal_update_spectrum = pyqtSignal(list)
    signal_gauss_params = pyqtSignal(list)
    signal_params_verification = pyqtSignal(str, str, bool, bool)
    signal_line_list = pyqtSignal(type(Table()))
    signal_ln_verification = pyqtSignal(bool,str)
    signal_msg = pyqtSignal(str)
    signal_readig_fit_error = pyqtSignal()
    signal_fit_hdulist = pyqtSignal(fits.hdu.hdulist.HDUList, str)

    def __init__(self):
        
        self.line_table = Table.read(p.PATH_LINE_LIST, format='ascii', delimiter='|',header_start=0)
        self.allowed_char = re.compile(p.ALLOWED_CHAR_LINENAME)

        super().__init__()

    # METHODS
    # Validations
    def validate_stretch(self, str_stretch):
        is_float = False
        try:
            float(str_stretch)
            is_float = True
        except ValueError:
            self.signal_update_stretch.emit(99.9)
        if is_float:
            stretch = float(str_stretch)
            if stretch >= 60 and stretch < 100:
                self.signal_update_stretch.emit(stretch)
            elif stretch < 60:
                self.signal_update_stretch.emit(60)
            elif stretch >= 100:
                self.signal_update_stretch.emit(99.9)

    def validate_params(self, str_m, str_b):
        m_is_float = False
        b_is_float = False
        try:
            float(str_m)
            m_is_float = True
            if float(str_m) == 0:
                str_m = '1'
        except ValueError:
            m_is_float = False
        try:
            float(str_b)
            b_is_float = True
        except ValueError:
            b_is_float = False
        self.signal_params_verification.emit(str_m, str_b, m_is_float, b_is_float)

    def validate_line_name(self, name, existing_lines):
        valid = True
        error = ''
        valid_format = bool(self.allowed_char.search(name))
        if not valid_format:
            error = 'Must be letters and/or numbers'
            valid = False
        elif name in existing_lines:
            error = 'This line name alredy exists'
            valid = False
        self.signal_ln_verification.emit(valid,error)

    # Calculations
    def calculate_spectrum_data(self, proyection, width, data):
        bottom_lim = int(proyection-width)
        top_lim = int(proyection+width+1)
        if bottom_lim < 0:
            bottom_lim = 0
        if top_lim > len(data):
            top_lim = len(data)
        spectrum_data = [sum(col)/len(col) for col in zip(*data[bottom_lim:top_lim])]
        self.signal_update_spectrum.emit(spectrum_data)
    
    def get_line_list(self, wavelenght_range, preset_list):
        if preset_list != '':
            if preset_list == 'Balmer':
                mask_list = np.isin(self.line_table['name'], p.BALMER_LIST)
            elif preset_list == 'Paschen':
                mask_list = np.isin(self.line_table['name'], p.PASCHEN_LIST)
            elif preset_list == 'Brackett':
                mask_list = np.isin(self.line_table['name'], p.BRACKETT_LIST)
            else:
                mask_list = (self.line_table[p.LIST_KEYS[preset_list]] == 1)
            mask_bot_wrest = (self.line_table['wrest'] >= wavelenght_range[0])
            mask_top_wrest = (self.line_table['wrest'] <= wavelenght_range[1])
            line_list = self.line_table[mask_list & mask_bot_wrest & mask_top_wrest]
            for i in range(len(line_list)):
                for char_ascii,char_utf8 in zip(p.GREEK_CHAR_ASCII,p.GREEK_CHAR_UTF8):
                    line_list['name'][i] = line_list['name'][i].replace(char_ascii,char_utf8)
            self.signal_line_list.emit(line_list)

    # Actions
    def create_profiles_dir(self):
        if not os.path.exists('profiles'):
            os.makedirs('profiles')

    def read_fit(self, path):
        fit_file = path.split('/')[-1]
        try:
            with fits.open(path) as hdu_list:
                self.signal_fit_hdulist.emit(hdu_list, path)
        except Exception as e:
            self.signal_readig_fit_error.emit()
            msg = f'Cannot open "{fit_file}", maybe is not a valid FITS file.'
            self.signal_msg.emit(msg)
            print(datetime.datetime.now(),e)

    def read_fit_data(self, hdu_n, path):
        fit_file = path.split('/')[-1]
        try:
            with fits.open(path) as hdu_list:
                hdu = hdu_list[hdu_n]
                data = hdu.data
                data = np.nan_to_num(data)
                title = path.split('/')[-1]
                dir_spectra = path.split('/')[-2]
            self.signal_fit_data.emit(data, title, dir_spectra)
        except Exception as e:
            self.signal_readig_fit_error.emit()
            msg = f'Cannot read spectra data from "{fit_file}".'
            self.signal_msg.emit(msg)
            print(datetime.datetime.now(),e)

    
    