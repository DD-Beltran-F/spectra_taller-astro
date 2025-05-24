# IMPORTS
import sys
import json
import os
import datetime

# Maths
import numpy as np
from scipy.optimize import curve_fit

# PyQt
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QLabel, QComboBox, QLineEdit, QSlider,
                             QRadioButton, QVBoxLayout, QFileDialog)

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt
from matplotlib import figure
from matplotlib import colormaps

# Local imports
import parameters as p
from my_widgets import (SpectrumLines, ImageCursor, SpectrumCursor, LineList)
from utilities import (gauss, full_extent)


class MainWindow(QMainWindow):

    # SIGNALS
    signal_load_image = pyqtSignal(int,str)
    signal_open_stretch_w = pyqtSignal(str)
    signal_open_scale_w = pyqtSignal(int,int)
    signal_update_spectrum = pyqtSignal(int, int, list)
    signal_line_list = pyqtSignal(list, str)
    signal_open_addline_w = pyqtSignal(float, float, list)
    signal_open_save_w = pyqtSignal(dict)
    signal_open_load_w = pyqtSignal()
    signal_create_profiles_dir = pyqtSignal()
    signal_msg = pyqtSignal(str)
    signal_open_lines_w = pyqtSignal(list)
    signal_load_fitfile = pyqtSignal(str)
    signal_load_hdulist = pyqtSignal(str)


    def __init__(self):
        super().__init__()

        # Load UI files
        uic.loadUi(p.PATH_UI_WINDOW_MAIN, self)

        # Start parameters
        self.dir_spectra = ''
        self.enable_user_events = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.params = None
        self.inversed_params = None
        self.fit_grade = None
        self.rms_px_to_nm_fit = None

        # WIDGETS
        # Buttons
        self.btn_load_profile = self.findChild(QPushButton,'btn_load_profile')
        self.btn_save_profile = self.findChild(QPushButton,'btn_save_profile')
        self.btn_load_image = self.findChild(QPushButton,'btn_load_image')
        self.btn_stretch = self.findChild(QPushButton,'btn_stretch')
        self.btn_create_scale = self.findChild(QPushButton,'btn_create_scale')
        self.btn_right = self.findChild(QPushButton,'btn_right')
        self.btn_left = self.findChild(QPushButton,'btn_left')
        self.btn_up = self.findChild(QPushButton,'btn_up')
        self.btn_down = self.findChild(QPushButton,'btn_down')
        self.btn_center = self.findChild(QPushButton,'btn_center')
        self.btn_clear_spectral_lines = self.findChild(QPushButton,'btn_clear_spectral_lines')
        self.btn_slctline = self.findChild(QPushButton,'btn_slctline')
        # Labels (just interactive ones)
        self.lbl_proyection_val = self.findChild(QLabel,'lbl_proyection_val')
        self.lbl_width_val = self.findChild(QLabel,'lbl_width_val')
        # Combo boxes
        self.cbox_cmap = self.findChild(QComboBox,'cbox_cmap')
        self.cbox_spectral_lines = self.findChild(QComboBox,'cbox_spectral_lines')
        # Sliders
        self.hslider_proyection = self.findChild(QSlider,'hslider_proyection')
        self.hslider_width = self.findChild(QSlider,'hslider_width')
        # Radio buttons
        self.rbtn_zoom_both = self.findChild(QRadioButton,'rbtn_zoom_both')
        self.rbtn_zoom_zaxis = self.findChild(QRadioButton,'rbtn_zoom_zaxis')
        self.rbtn_zoom_xaxis = self.findChild(QRadioButton,'rbtn_zoom_xaxis')
        self.rbtn_px = self.findChild(QRadioButton,'rbtn_px')
        self.rbtn_nm = self.findChild(QRadioButton,'rbtn_nm')
        # Layouts (for plotting)
        self.vbox_image = self.findChild(QVBoxLayout,'vbox_image')
        self.vbox_spectrum = self.findChild(QVBoxLayout,'vbox_spectrum')

        # Create figure and canvas to plot the image
        self.figure_image = plt.figure()
        self.canvas_image = FigureCanvas(self.figure_image)
        self.vbox_image.addWidget(self.canvas_image)

        # Create figure and canavs to plot the spectrum
        self.figure_spectrum = plt.figure()
        self.canvas_spectrum = FigureCanvas(self.figure_spectrum)
        self.vbox_spectrum.addWidget(self.canvas_spectrum)
        
        # Add combo boxes options
        cmaps = ['magma','plasma','inferno','viridis','cividis','gray','hsv']
        for cmap in colormaps:
            if cmap not in cmaps: cmaps.append(cmap)
        self.cbox_cmap.addItems(cmaps)
        line_list = ['','Galaxy','HI','H2','CO','ISM','Strong','EUV','AGN','Balmer','Paschen','Brackett']
        self.cbox_spectral_lines.addItems(line_list)

        # Connect widgets with methods
        self.btn_slctline.clicked.connect(self.slct_line)
        self.btn_load_image.clicked.connect(self.search_file)
        self.btn_load_profile.clicked.connect(self.open_load_w)
        self.btn_save_profile.clicked.connect(self.open_save_w)
        self.btn_stretch.clicked.connect(self.open_stretch_w)
        self.btn_create_scale.clicked.connect(self.open_scale_w)
        self.hslider_proyection.valueChanged.connect(self.proyection_changed)
        self.hslider_width.valueChanged.connect(self.width_changed)
        self.cbox_cmap.currentTextChanged.connect(self.cmap_changed)
        self.cbox_spectral_lines.currentTextChanged.connect(self.line_list_change)
        self.btn_clear_spectral_lines.clicked.connect(self.clear_spectral_lines)
        self.btn_up.clicked.connect(self.translate_up)
        self.btn_down.clicked.connect(self.translate_down)
        self.btn_right.clicked.connect(self.translate_right)
        self.btn_left.clicked.connect(self.translate_left)
        self.btn_center.clicked.connect(self.center_spectrum)
        self.rbtn_px.toggled.connect(lambda: self.scale_changed(self.rbtn_px.text()))
        self.rbtn_nm.toggled.connect(lambda: self.scale_changed(self.rbtn_nm.text()))

        # Connect mouse events with canvas
        self.canvas_image.mpl_connect('button_press_event', self.on_click)
        self.canvas_image.mpl_connect('scroll_event', self.on_scroll)
        self.canvas_spectrum.mpl_connect('button_press_event', self.on_click)
        self.canvas_spectrum.mpl_connect('scroll_event', self.on_scroll)

        # Create widgets, axes, or anything that needs to be initialized when the program starts
        self.ax1 = None
        self.ax2 = None
        self.data = None
        self.img = None
        self.proyection = None
        self.width = None
        self.spectrum = None
        self.spectrum_lines = SpectrumLines(remove_threshold=5)
        self.line_list_class = None
        self.cursor_ax1 = None
        self.cursor_ax2 = None
        self.image_path = None
        self.hdu_n = None
        
    # METHODS
    # Window
    def start(self):
        self.signal_create_profiles_dir.emit()
        self.plot_image([[10 for i in range(10)] for j in range(10)],'Load an image', '')
        self.enable_widgets(False)
        self.btn_load_image.setEnabled(True)
        self.btn_load_profile.setEnabled(True)

    def enable_widgets(self, enable):
        self.enable_user_events = enable
        self.btn_load_profile.setEnabled(enable)
        self.btn_save_profile.setEnabled(enable)
        self.btn_load_image.setEnabled(enable)
        self.cbox_cmap.setEnabled(enable)
        self.btn_stretch.setEnabled(enable)
        self.hslider_proyection.setEnabled(enable)
        self.hslider_width.setEnabled(enable)
        self.rbtn_zoom_both.setEnabled(enable)
        self.rbtn_zoom_zaxis.setEnabled(enable)
        self.rbtn_zoom_xaxis.setEnabled(enable)
        self.btn_up.setEnabled(enable)
        self.btn_down.setEnabled(enable)
        self.btn_left.setEnabled(enable)
        self.btn_right.setEnabled(enable)
        self.btn_center.setEnabled(enable)
        self.rbtn_px.setEnabled(enable)
        if self.params:
            self.rbtn_nm.setEnabled(enable)
            self.cbox_spectral_lines.setEnabled(enable)
            self.btn_slctline.setEnabled(enable)
            self.btn_clear_spectral_lines.setEnabled(enable)
        if not enable:
            self.rbtn_nm.setEnabled(enable)
            self.cbox_spectral_lines.setEnabled(enable)
            self.btn_slctline.setEnabled(enable)
            self.btn_clear_spectral_lines.setEnabled(enable)
        self.btn_create_scale.setEnabled(enable)

    def focusOutEvent(self,event):
        self.setFocus(True)

    def reset_profile(self):
        self.params = None
        self.inversed_params = None
        self.fit_grade = None
        self.rms_px_to_nm_fit = None
        self.enable_widgets(False)

    # File handling
    def open_load_w(self):
        self.signal_open_load_w.emit()
    
    def load_profile(self, profile_data):
        self.signal_load_image.emit(int(profile_data['hdu_n']), profile_data['image_path'])
        if not self.btn_save_profile.isEnabled():
            self.enable_widgets(True)
        self.image_path = profile_data['image_path']
        self.hdu_n = int(profile_data['hdu_n'])
        self.params = profile_data['scale_params']
        self.inversed_params = profile_data['inversed_scale_params']
        self.rms_px_to_nm_fit = profile_data['rms_px_to_nm_fit']
        self.cbox_cmap.setCurrentIndex(profile_data['cmap'])
        self.btn_stretch.setText(profile_data['stretch'])
        self.hslider_proyection.setValue(int(profile_data['proyection']))
        self.hslider_width.setValue(int(profile_data['width']))
        xlimits = profile_data['xlimits']
        zlimits = profile_data['zlimts']
        self.update_spectra_limits('x', xlimits[0], xlimits[1])
        self.update_spectra_limits('z', zlimits[0], zlimits[1])
        scale_selected = profile_data['scale_selected']
        if self.params:
            self.rbtn_nm.setEnabled(True)
            self.cbox_spectral_lines.setEnabled(True)
            self.btn_slctline.setEnabled(True)
            self.btn_clear_spectral_lines.setEnabled(True)
            if scale_selected == 'Nanometers':
                self.rbtn_nm.setChecked(True)
        if scale_selected == 'Pixels':
            self.rbtn_px.setChecked(True)
        for line_pos,line_text,line_color,line_type,line_align in zip(profile_data['lines_pos'],\
                                                            profile_data['lines_names'],\
                                                            profile_data['lines_color'],\
                                                            profile_data['lines_types'],\
                                                            profile_data['lines_names_align']):
            line = self.ax2.axvline(line_pos[0],color=line_color,lw=p.SPECTRA_LINES_LW,ls=line_type)
            if line_align['valign'] == 'bottom':
                zlblpos = zlimits[0]+0.035*(zlimits[1]-zlimits[0])
            elif line_align['valign'] == 'top':
                zlblpos = zlimits[1]-0.035*(zlimits[1]-zlimits[0])
            label = self.ax2.text(line_pos[0],zlblpos,line_text,
                                      fontsize=0.7*p.SPECTRA_FS,color=line_color,
                                      ha=line_align['halign'],va=line_align['valign'],
                                      fontname=p.SPECTRA_FN)
            self.spectrum_lines.add_line(line, label, line_pos[0], line_pos[1])
        self.ax2.set_title(profile_data['title'],fontsize=1.2*p.SPECTRA_FS,fontname=p.SPECTRA_FN,
                           pad=10)
        if self.cursor_ax2:
            self.cursor_ax2.params = self.params
        self.canvas_image.draw()
        self.canvas_spectrum.draw()

    def open_save_w(self):
        image_file = self.ax1.get_title()
        image_size = [int(self.ax1.get_xlim()[1]),int(self.ax1.get_ylim()[1])]
        proyection = self.lbl_proyection_val.text()
        width = self.lbl_width_val.text()
        if self.params:
            scale_params = 'Yes'
        elif self.params is None:
            scale_params = 'No'
        spectrum = {
                    'data': self.spectrum.get_ydata(),
                    'xticks': self.ax2.get_xticks(),
                    'yticks': self.ax2.get_yticks(),
                    'xticks_labels': self.ax2.get_xticklabels(),
                    'yticks_labels': self.ax2.get_yticklabels(),
                    'xlim': self.ax2.get_xlim(),
                    'ylim': self.ax2.get_ylim(),
                    'xlabel': self.ax2.get_xlabel(),
                    'ylabel': self.ax2.get_ylabel(),
                    'title': self.ax2.get_title(),
                    'lines_pos':[(x,y) for x,y in zip(self.spectrum_lines.xdata,\
                                                          self.spectrum_lines.ydata)],
                    'lines_color':[label.get_color() for label in self.spectrum_lines.labels],
                    'lines_types':[line.get_ls() for line in self.spectrum_lines.lines],
                    'lines_names':[label.get_text() for label in self.spectrum_lines.labels],
                    'lines_names_align': [{'valign':label.get_va(),'halign':label.get_ha()} for\
                                           label in self.spectrum_lines.labels]
                    }
        self.signal_open_save_w.emit({
                                      'image_file':image_file,
                                      'image_size':image_size,
                                      'proyection':proyection,
                                      'width':width,
                                      'scale_params':scale_params,
                                      'spectrum':spectrum
                                    })
        self.enable_widgets(False)

    def save_profile(self, file_name, title):
        self.enable_widgets(True)
        last_spectral_line_list = self.cbox_spectral_lines.currentIndex()
        self.clear_spectral_lines()
        profile_data = {
                        'image_path':self.image_path,
                        'hdu_n':self.hdu_n,
                        'image_file':self.ax1.get_title(),
                        'image_size':[int(self.ax1.get_xlim()[1]),int(self.ax1.get_ylim()[1])],
                        'cmap':self.cbox_cmap.currentIndex(),
                        'stretch':self.btn_stretch.text(),
                        'proyection':self.lbl_proyection_val.text(),
                        'width':self.lbl_width_val.text(),
                        'xlimits':self.ax2.get_xlim(),
                        'zlimts':self.ax2.get_ylim(),
                        'scale_selected':self.ax2.get_xlabel(),
                        'scale_params':self.params,
                        'inversed_scale_params':self.inversed_params,
                        'rms_px_to_nm_fit':self.rms_px_to_nm_fit,
                        'lines_pos':[(x,y) for x,y in zip(self.spectrum_lines.xdata,\
                                                          self.spectrum_lines.ydata)],
                        'lines_color':[label.get_color() for label in self.spectrum_lines.labels],
                        'lines_types':[line.get_ls() for line in self.spectrum_lines.lines],
                        'lines_names':[label.get_text() for label in self.spectrum_lines.labels],
                        'lines_names_align': [{'valign':label.get_va(),'halign':label.get_ha()} for\
                                               label in self.spectrum_lines.labels],
                        'title':title
                       }

        profile_path = os.path.join('profiles', file_name + '.txt')
        profile_image_path = os.path.join('profiles', file_name + '.png')
        with open(profile_path, 'w') as file:
            json.dump(profile_data, file)
        extent = full_extent(self.ax2,p.PNG_FIGURE_MARGIN).transformed(self.figure_spectrum.\
                                                                         dpi_scale_trans.inverted())
        object_name = file_name.split('_')[0]
        self.ax2.set_title(title,fontsize=1.2*p.SPECTRA_FS,fontname=p.SPECTRA_FN, pad=10)
        self.figure_spectrum.savefig(profile_image_path, bbox_inches=extent)
        self.signal_msg.emit(f'The profile "{file_name}" has been successfully saved!')
        self.cbox_spectral_lines.setCurrentIndex(last_spectral_line_list)

    def search_file(self):
        self.enable_widgets(False)
        path, _ = QFileDialog.getOpenFileName(self, 'Open File', self.dir_spectra,
                                             'FITS files (*.FIT *.fits);;All Files (*)')
        self.dir_spectra = os.path.dirname(path)
        if path:
            self.image_path = path
            self.signal_load_fitfile.emit(path)     
        else:
            self.btn_load_image.setEnabled(True)
            self.btn_load_profile.setEnabled(True)
            if self.image_path:
                self.enable_widgets(True)

    def search_file_canceled(self):
        self.btn_load_image.setEnabled(True)
        self.btn_load_profile.setEnabled(True)
        if self.image_path:
                self.enable_widgets(True)

    def reading_fit_error(self):
        self.btn_load_image.setEnabled(True)
        self.btn_load_profile.setEnabled(True)

    # FIT Image
    def plot_image(self, data, title, dir_spectra):
        #self.reset_profile()
        self.enable_widgets(True)
        self.spectrum_lines.reset()
        self.clear_spectral_lines()
        self.data = data
        self.figure_image.clf()
        stretch = float(self.btn_stretch.text())
        xdatalen = len(self.data[0])
        ydatalen = len(self.data)
        if title != 'Load an image':
            self.hslider_proyection.setRange(0,ydatalen)
            self.hslider_proyection.setValue(int(ydatalen/2))
            self.lbl_proyection_val.setText(str(int(ydatalen/2)))
            self.hslider_width.setValue(3)
            self.lbl_width_val.setText('3')
        proyection_value = self.hslider_proyection.value()
        xticks = [x for x in range(0,xdatalen+1,int(xdatalen/5))]
        yticks = [y for y in range(0,ydatalen+1,int(ydatalen/5))]
        self.ax1 = self.figure_image.add_subplot(111)
        self.img = self.ax1.imshow(self.data, vmin = np.nanpercentile(self.data, 100-stretch),
                        vmax = np.nanpercentile(self.data, stretch), cmap='magma', origin='lower')
        self.proyection, = self.ax1.plot([0,xdatalen],[proyection_value,proyection_value],
                                   lw=p.IMAGE_LINES_LW,color='lime')
        self.width, = self.ax1.plot([0,xdatalen],[proyection_value,proyection_value],
                              lw=3,color='lime',alpha=0.25)
        self.ax1.minorticks_on()
        self.ax1.tick_params(labelsize=p.IMAGE_FS,axis='both',which='major',direction='in',
                             length=16,width=1,color='black',right=True,top=True)
        self.ax1.tick_params(labelsize=p.IMAGE_FS,axis='both',which='minor',direction='in',
                             length=6,width=1,color='black',right=True,top=True)
        self.ax1.set_xticks(xticks,xticks,fontname=p.IMAGE_FN)
        self.ax1.set_yticks(yticks,yticks,fontname=p.IMAGE_FN)
        self.ax1.set_xlim(0,xdatalen)
        self.ax1.set_ylim(0,ydatalen)
        self.ax1.set_xlabel('X (px)',fontsize=p.IMAGE_FS, fontname=p.IMAGE_FN)
        self.ax1.set_ylabel('Y (px)',fontsize=p.IMAGE_FS, fontname=p.IMAGE_FN)
        self.ax1.set_title(title,fontsize=1.2*p.IMAGE_FS,fontname=p.IMAGE_FN, pad=10)
        self.plot_spectrum(self.data[proyection_value])
        self.canvas_image.draw()
        if title != 'Load an image':
            self.initialize_cursor_ax1()

    def data_update(self):
        proyection = int(self.lbl_proyection_val.text())
        width = int(self.lbl_width_val.text())
        stretch = float(self.btn_stretch.text())
        self.proyection.set_ydata([proyection,proyection])
        self.width.set_ydata([proyection,proyection])
        self.width.set_linewidth(2*width)
        self.img.set_clim(np.nanpercentile(self.data, 100-stretch),
                          np.nanpercentile(self.data, stretch))
        self.signal_update_spectrum.emit(proyection, width, list(self.data))
        self.canvas_image.draw()

    def cmap_changed(self, cmap):
        self.img.set_cmap(cmap)
        self.canvas_image.draw()

    def open_stretch_w(self):
        self.signal_open_stretch_w.emit(self.btn_stretch.text())
        self.enable_widgets(False)

    def stretch_changed(self, stretch):
        self.enable_widgets(True)
        self.btn_stretch.setText(str(stretch))
        self.data_update()
    
    def proyection_changed(self, value):
        self.lbl_proyection_val.setText(str(value))
        self.data_update()
    
    def width_changed(self, value):
        self.lbl_width_val.setText(str(value))
        self.data_update()

    def initialize_cursor_ax1(self):
        self.cursor_ax1 = ImageCursor(
                        numberformat="{:.0f}",
                        offset=(5, 5),
                        textprops={'color':'lime','fontsize':0.6*p.IMAGE_FS,'fontweight':'bold',
                                   'fontfamily':p.IMAGE_FN},
                        ax=self.ax1,
                        useblit=True,
                        color='lime',
                        linewidth=p.IMAGE_LINES_LW, vertOn=False)
        self.canvas_image.draw()

    # Spectrum
    def plot_spectrum(self, data):
        self.figure_spectrum.clf()
        self.cbox_spectral_lines.setCurrentIndex(0)
        xdatalen = len(data)
        zdatamax = np.max(self.data)
        xticks = [x for x in range(0,int(xdatalen+1),int(xdatalen/10))]
        yticks = [y for y in range(0,int(zdatamax+1),int(zdatamax/5))]
        self.ax2 = self.figure_spectrum.add_subplot(111)
        self.spectrum, = self.ax2.plot(data,lw=p.SPECTRA_LW,color='black')
        self.ax2.minorticks_on()
        self.ax2.tick_params(labelsize=p.SPECTRA_FS,axis='both',which='major',direction='in',
                             length=16,width=1,color='black',right=True,top=True)
        self.ax2.tick_params(labelsize=p.SPECTRA_FS,axis='both',which='minor',direction='in',
                             length=6,width=1,color='black',right=True,top=True)
        self.ax2.set_xticks(xticks,xticks,fontname=p.SPECTRA_FN)
        self.ax2.set_yticks(yticks,yticks,fontname=p.SPECTRA_FN)
        self.ax2.set_xlim(0,xdatalen)
        self.ax2.set_ylim(0,zdatamax)
        self.ax2.set_xlabel('Pixels', fontsize=p.SPECTRA_FS, fontname=p.SPECTRA_FN)
        self.ax2.set_ylabel('Counts', fontsize=p.SPECTRA_FS, fontname=p.SPECTRA_FN)
        self.ax2.set_title('Spectrum',fontsize=1.2*p.SPECTRA_FS,fontname=p.SPECTRA_FN, pad=10)
        self.canvas_spectrum.draw()
        if self.ax1.get_title() != 'Load an image':
            self.initialize_cursor_ax2()

    def spectrum_update(self, data):
        self.spectrum.set_xdata([x for x in range(len(data))])
        self.spectrum.set_ydata(data)
        self.canvas_spectrum.draw()

    def update_spectra_limits(self, axis, bot_val, top_val):
        bot_val = int(bot_val)
        top_val = int(top_val)
        if axis == 'z':
            yticks = [y for y in range(bot_val,top_val+1,int((top_val-bot_val)/5))]
            self.ax2.set_yticks(yticks,yticks)
            self.ax2.set_ylim(bot_val,top_val)
            if self.line_list_class:
                self.line_list_class.check_text_pos(z_min=bot_val,z_max=top_val)
            self.spectrum_lines.check_text_pos(z_min=bot_val,z_max=top_val)
        elif axis == 'x':
            xticks = [x for x in range(bot_val,top_val+1,int((top_val-bot_val)/10))]
            if self.rbtn_px.isChecked():
                xticks_labels = ['{:.0f}'.format(x) for x in xticks]
            if self.rbtn_nm.isChecked():
                xticks_labels = ['{:.0f}'.format(self.scale_px_to_nm(x)) for x in xticks]
            self.ax2.set_xticks(xticks,xticks_labels)
            self.ax2.set_xlim(bot_val,top_val)
            if self.line_list_class:
                self.line_list_class.check_text_pos(limits=[bot_val,top_val])
            self.spectrum_lines.check_text_pos(limits=[bot_val,top_val])
        self.canvas_spectrum.draw()

    def center_spectrum(self):
        self.update_spectra_limits('x', 0, len(self.data[0]))
        self.update_spectra_limits('z', 0, np.max(self.data))
    
    def translate_up(self):
        limits = self.ax2.get_ylim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] + p.TRANSLATION_FACTOR*range_limits
        top_val = limits[1] + p.TRANSLATION_FACTOR*range_limits
        if bot_val >= 0 and top_val <= (np.max(self.data) + 5):
            self.update_spectra_limits('z', bot_val, top_val)

    def translate_down(self):
        limits = self.ax2.get_ylim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] - p.TRANSLATION_FACTOR*range_limits
        top_val = limits[1] - p.TRANSLATION_FACTOR*range_limits
        if bot_val >= 0 and top_val <= (np.max(self.data) + 5):
            self.update_spectra_limits('z', bot_val, top_val)

    def translate_right(self):
        limits = self.ax2.get_xlim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] + p.TRANSLATION_FACTOR*range_limits
        top_val = limits[1] + p.TRANSLATION_FACTOR*range_limits
        if bot_val >= 0 and top_val <= (len(self.data[0]) - 1):
            self.update_spectra_limits('x', bot_val, top_val)

    def translate_left(self):
        limits = self.ax2.get_xlim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] - p.TRANSLATION_FACTOR*range_limits
        top_val = limits[1] - p.TRANSLATION_FACTOR*range_limits
        if bot_val >= 0 and top_val <= (len(self.data[0]) - 1):
            self.update_spectra_limits('x', bot_val, top_val)

    def slct_line(self):
        bot_wv = self.scale_px_to_nm(0)
        top_wv = self.scale_px_to_nm(len(self.data[0]))
        wavelenght_range = sorted([bot_wv*10,top_wv*10])
        self.signal_open_lines_w.emit(wavelenght_range)

    def plot_slct_line(self, name, wrest):
        z_min,z_max = self.ax2.get_ylim()
        if self.line_list_class is None:
            self.line_list_class = LineList()
        wv_in_px = self.scale_nm_to_px(float(wrest))
        line = self.ax2.axvline(wv_in_px, color='green', lw=p.SPECTRA_LINES_LW, ls='--')
        name_1 = name
        name_2 = ''
        if ' ' in name:
            name_1 = name.split(' ')[0]
            name_2 = str('{:.1f}'.format(float(name.replace('  ',' ').split(' ')[1])/10))
        full_name = name_1+'$_{'+name_2+'}$'
        label = self.ax2.text(wv_in_px,z_min+0.035*(z_max-z_min),full_name,
                              fontsize=0.7*p.SPECTRA_FS,color='green', ha='left', va='bottom',
                              fontname=p.SPECTRA_FN)
        self.line_list_class.add_line(line, label)
        self.canvas_spectrum.draw()

    def line_list_change(self, preset_list):
        if self.line_list_class:
            self.line_list_class.clear_lines()
        bot_wv = self.scale_px_to_nm(0)
        top_wv = self.scale_px_to_nm(len(self.data[0]))
        wavelenght_range = sorted([bot_wv*10,top_wv*10])
        self.signal_line_list.emit(wavelenght_range, preset_list)

    def plot_line_list(self, line_list):
        wrest = line_list['wrest']
        names = line_list['name']
        z_min,z_max = self.ax2.get_ylim()
        if self.line_list_class is None:
            self.line_list_class = LineList()
        for w,name in zip(wrest,names):
            wv_in_px = self.scale_nm_to_px(float(w)/10)
            line = self.ax2.axvline(wv_in_px, color='green', lw=p.SPECTRA_LINES_LW, ls='--')
            name_1 = name
            name_2 = ''
            if ' ' in name:
                name_1 = name.split(' ')[0]
                name_2 = str(float(name.replace('  ',' ').split(' ')[1])/10)
            label = self.ax2.text(wv_in_px,z_min+0.035*(z_max-z_min),'$_{'+name_2+'}$\n'+name_1,
                                  fontsize=0.7*p.SPECTRA_FS,color='green', ha='left', va='bottom',
                                  fontname=p.SPECTRA_FN)
            self.line_list_class.add_line(line, label)
        
        self.canvas_spectrum.draw()

    def clear_spectral_lines(self):
        self.cbox_spectral_lines.setCurrentIndex(0)
        if self.line_list_class:
            self.line_list_class.clear_lines()
            self.canvas_spectrum.draw()

    def add_fit_line(self, fit_line_data):
        z_min,z_max = self.ax2.get_ylim()
        name = fit_line_data['name']
        color = fit_line_data['color']
        valign = fit_line_data['valign']
        halign = fit_line_data['halign']
        layer = int(fit_line_data['layer'])
        ltype = fit_line_data['type']
        line = self.ax2.axvline(self.spectrum_lines.fit_max[0], color=color, lw=p.SPECTRA_LINES_LW,
                                ls=ltype)
        name_1 = name
        name_2 = ''
        if ' ' in name:
            name_1 = name.split(' ')[0]
            name_2 = name.replace('  ',' ').split(' ')[1]
            try:
                name_2 = '{:.1f}'.format(float(name_2))
            except:
                pass
        full_name = name_1+'$_{'+name_2+'}$'
        if valign == 'bottom':
            zlblpos = z_min+0.035*(abs(z_max-z_min))
            full_name = full_name + '\n'*(layer-1)
        elif valign == 'top':
            zlblpos = z_max-0.035*(abs(z_max-z_min))
            full_name = '\n'*(layer-1) + full_name
        if halign == 'right':
            real_ha = 'left'
        elif halign == 'left':
            real_ha = 'right'
        label = self.ax2.text(self.spectrum_lines.fit_max[0],zlblpos,full_name,
                                  fontsize=0.7*p.SPECTRA_FS,color=color, ha=real_ha, va=valign,
                                  fontname=p.SPECTRA_FN)
        self.spectrum_lines.add_line(line, label, self.spectrum_lines.fit_max[0], self.spectrum_lines.fit_max[1])
        self.canvas_spectrum.draw()

    def discard_fit_line(self):
        self.spectrum_lines.discard_fit()
        self.canvas_spectrum.draw()

    def initialize_cursor_ax2(self):
        self.cursor_ax2 = SpectrumCursor(
                line=self.spectrum,
                numberformat="{:.0f}",
                show_axis='both', offset=[[5, 5],[5, 5]], params=self.params,
                textprops=[{'color':'black','fontsize':0.6*p.SPECTRA_FS,'fontweight':'bold',
                            'fontfamily':p.SPECTRA_FN},
                           {'color':'blue','fontsize':0.8*p.SPECTRA_FS,'fontweight':'bold',
                            'fontfamily':p.SPECTRA_FN}],
                ax=self.ax2,
                useblit=True,
                color='blue',
                linewidth=p.SPECTRA_LINES_LW, horizOn=False)
        self.canvas_spectrum.draw()

    # Scale
    def open_scale_w(self):
        self.signal_open_scale_w.emit(int(self.lbl_proyection_val.text()),
                                      int(self.lbl_width_val.text()))

    def fit_1(self, x, a, b):
        return a*x + b

    def fit_2(self, x, a, b, c):
        return a*(x**2) + b*x + c

    def fit_3(self, x, a, b, c, d):
        return a *(x**3) + b*(x**2) + c*x + d

    def fit_4(self, x, a, b, c, d, e):
        return a*(x**4) + b *(x**3) + c*(x**2) + d*x + e

    def new_scale(self, params):
        self.params = params['params']
        self.inversed_params = params['inversed_params']
        self.rms_px_to_nm_fit = params['rms_px_to_nm_fit']
        self.cursor_ax2.params = self.params
        self.enable_widgets(True)

    def scale_px_to_nm(self, px):
        if self.params:
            if len(self.params) == 2:
                return self.fit_1(px, *self.params)
            if len(self.params) == 3:
                return self.fit_2(px, *self.params)
            if len(self.params) == 4:
                return self.fit_3(px, *self.params)
            if len(self.params) == 5:
                return self.fit_4(px, *self.params)

    def scale_nm_to_px(self, nm):
        if self.inversed_params:
            if len(self.inversed_params) == 2:
                return self.fit_1(nm, *self.inversed_params)
            if len(self.inversed_params) == 3:
                return self.fit_2(nm, *self.inversed_params)
            if len(self.inversed_params) == 4:
                return self.fit_3(nm, *self.inversed_params)
            if len(self.inversed_params) == 5:
                return self.fit_4(nm, *self.inversed_params)

    def scale_changed(self,rbtn_selected):
        xticks = self.ax2.get_xticks()
        if rbtn_selected == 'Pixels':
            xticks_labels = ['{:.0f}'.format(x) for x in xticks]
        elif rbtn_selected == 'Nanometers':
            xticks_labels = ['{:.0f}'.format(self.scale_px_to_nm(x)) for x in xticks]
        self.ax2.set_xticks(xticks,xticks_labels,fontname=p.SPECTRA_FN)
        self.ax2.set_xlabel(rbtn_selected, fontsize=p.SPECTRA_FS, fontname=p.SPECTRA_FN)
        self.canvas_spectrum.draw()

    # Events
    def on_click(self, event):
        if self.enable_user_events:
            if self.ax1.in_axes(event):
                if event.button == 1:
                    self.hslider_proyection.setValue(int(event.ydata))
            elif self.ax2.in_axes(event):
                self.canvas_spectrum.setFocusPolicy(Qt.ClickFocus)
                self.canvas_spectrum.setFocus()
                if event.button == 1:
                    if self.spectrum_lines.picking:
                        self.spectrum_lines.picking = False
                        self.spectrum_lines.adjusting = True
                        line_x = float(self.cursor_ax2.text_x.get_text())
                        if self.rbtn_nm.isChecked():
                            line_x = self.scale_nm_to_px(line_x)
                        line_y = float(self.cursor_ax2.text_y.get_text())
                        guess = self.ax2.axvline(line_x,color='blue',lw=p.SPECTRA_LINES_LW)
                        guess_width_1 = self.ax2.axvline(line_x-2,color='blue',
                                                         lw=p.SPECTRA_LINES_LW,ls=':')
                        guess_width_2 = self.ax2.axvline(line_x+2,color='blue',
                                                         lw=p.SPECTRA_LINES_LW,ls=':')
                        self.spectrum_lines.guess(line_guess=guess,
                                                  line_guess_width=[guess_width_1,guess_width_2])
                        self.canvas_spectrum.draw()
                elif event.button == 3:
                    line_x = float(self.cursor_ax2.text_x.get_text())
                    if self.rbtn_nm.isChecked():
                        line_x = self.scale_nm_to_px(line_x)
                    self.spectrum_lines.remove_line(line_x)
                    if self.spectrum_lines.adjusting:
                        self.spectrum_lines.line_guess.remove()
                        self.spectrum_lines.line_guess_width[0].remove()
                        self.spectrum_lines.line_guess_width[1].remove()
                        self.spectrum_lines.line_guess = None
                        self.spectrum_lines.line_guess_width = None
                        self.spectrum_lines.adjusting = False
                        self.spectrum_lines.picking = True
                    self.canvas_spectrum.draw()

    def on_scroll(self, event):
        if self.enable_user_events:
            if self.ax1.in_axes(event):
                width = self.hslider_width.value()
                new_width = int(width+event.step)
                if event.step < 0:
                    if new_width < self.hslider_width.minimum():
                        self.hslider_width.setValue(self.hslider_width.minimum())
                    else:
                        self.hslider_width.setValue(new_width)
                elif event.step > 0:
                    if new_width > self.hslider_width.maximum():
                        self.hslider_width.setValue(self.hslider_width.maximum())
                    else:
                        self.hslider_width.setValue(new_width)
            if self.ax2.in_axes(event):
                zoom = abs(event.step) + p.ZOOM_FACTOR
                
                # Z axis
                z_limits = self.ax2.get_ylim()
                z_min_value = 0
                z_max_value = np.max(self.data) + 5
                z_range_i = z_limits[1] - z_limits[0]
                z_center = event.ydata

                # X axis
                x_limits = self.ax2.get_xlim()
                x_min_value = 0
                x_max_value = len(self.data[0]) - 1
                x_range_i = x_limits[1] - x_limits[0]
                x_center = event.xdata

                # Zoom in
                if event.step > 0:
                    # Z axis
                    if self.rbtn_zoom_both.isChecked() or self.rbtn_zoom_zaxis.isChecked():
                        z_range_f = z_range_i/zoom
                        z_bot_val = z_center - z_range_f/2
                        z_top_val = z_center + z_range_f/2

                        if z_bot_val < z_min_value:
                            z_bot_val = z_min_value
                        if z_top_val > z_max_value:
                            z_top_val = z_max_value

                        if abs(z_top_val - z_bot_val) >= p.ZOOM_IN_MAX:
                            self.update_spectra_limits('z', z_bot_val, z_top_val)

                    # X axis
                    if self.rbtn_zoom_both.isChecked() or self.rbtn_zoom_xaxis.isChecked():
                        x_range_f = x_range_i/zoom
                        x_bot_val = x_center - x_range_f/2
                        x_top_val = x_center + x_range_f/2

                        if x_bot_val < x_min_value:
                            x_bot_val = x_min_value
                        if x_top_val > x_max_value:
                            x_top_val = x_max_value

                        if abs(x_top_val - x_bot_val) >= p.ZOOM_IN_MAX:
                            self.update_spectra_limits('x', x_bot_val, x_top_val)

                # Zoom out
                if event.step < 0:
                    # Z axis
                    if self.rbtn_zoom_both.isChecked() or self.rbtn_zoom_zaxis.isChecked():
                        z_range_f = z_range_i*zoom
                        if not (abs(z_limits[1] - z_limits[0]) == abs(z_max_value - z_min_value)):
                            z_bot_val = z_limits[0] - (z_range_f-z_range_i)/2
                            z_top_val = z_limits[1] + (z_range_f-z_range_i)/2

                            if z_bot_val < z_min_value:
                                z_bot_val = z_min_value
                            if z_top_val > z_max_value:
                                z_top_val = z_max_value

                            self.update_spectra_limits('z', z_bot_val, z_top_val)
                    
                    # X axis
                    if self.rbtn_zoom_both.isChecked() or self.rbtn_zoom_xaxis.isChecked():
                        x_range_f = x_range_i*zoom
                        if not (abs(x_limits[1] - x_limits[0]) == abs(x_max_value - x_min_value)):
                            x_bot_val = x_limits[0] - (x_range_f-x_range_i)/2
                            x_top_val = x_limits[1] + (x_range_f-x_range_i)/2

                            if x_bot_val < x_min_value:
                                x_bot_val = x_min_value
                            if x_top_val > x_max_value:
                                x_top_val = x_max_value

                            self.update_spectra_limits('x', x_bot_val, x_top_val)

    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_pressed = event.key()
            if self.enable_user_events:
                if key_pressed == Qt.Key_Comma:
                    if self.rbtn_zoom_both.isChecked():
                        self.rbtn_zoom_zaxis.setChecked(True)
                    elif self.rbtn_zoom_zaxis.isChecked():
                        self.rbtn_zoom_xaxis.setChecked(True)
                    elif self.rbtn_zoom_xaxis.isChecked():
                        self.rbtn_zoom_both.setChecked(True)
                if key_pressed == Qt.Key_Period:
                    if self.rbtn_px.isChecked():
                        if self.params:
                            self.rbtn_nm.setChecked(True)
                    elif self.rbtn_nm.isChecked():
                        self.rbtn_px.setChecked(True)
                if key_pressed == Qt.Key_Up:
                    self.translate_up()
                if key_pressed == Qt.Key_Down:
                    self.translate_down()
                if key_pressed == Qt.Key_Right:
                    self.translate_right()
                if key_pressed == Qt.Key_Left:
                    self.translate_left()
                if self.spectrum_lines.adjusting:
                    last_w1 = self.spectrum_lines.line_guess_width[0].get_xdata()[0]
                    last_w2 = self.spectrum_lines.line_guess_width[1].get_xdata()[0]
                    if key_pressed == Qt.Key_M:
                        self.spectrum_lines.line_guess_width[0].set_xdata([last_w1-1,last_w1-1])
                        self.spectrum_lines.line_guess_width[1].set_xdata([last_w2+1,last_w2+1])
                        self.canvas_spectrum.draw()
                    elif key_pressed == Qt.Key_N:
                        if abs(last_w2-last_w1) > 4:
                            self.spectrum_lines.line_guess_width[0].set_xdata([last_w1+1,last_w1+1])
                            self.spectrum_lines.line_guess_width[1].set_xdata([last_w2-1,last_w2-1])
                            self.canvas_spectrum.draw()
                    elif key_pressed == Qt.Key_G:
                        left_lim = int(self.spectrum_lines.line_guess_width[0].get_xdata()[0])
                        right_lim = int(self.spectrum_lines.line_guess_width[1].get_xdata()[0])
                        xdata = list(self.spectrum.get_xdata()[left_lim:right_lim+1])
                        ydata = list(self.spectrum.get_ydata()[left_lim:right_lim+1])
                        self.spectrum_lines.line_guess.remove()
                        self.spectrum_lines.line_guess_width[0].remove()
                        self.spectrum_lines.line_guess_width[1].remove()
                        self.spectrum_lines.line_guess = None
                        self.spectrum_lines.line_guess_width = None
                        try:
                            self.spectrum_lines.adjusting = False
                            self.spectrum_lines.fitting = True
                            params, _ = curve_fit(gauss,xdata,ydata,
                                      p0=[np.max(ydata),np.min(ydata),np.mean(xdata),np.std(xdata)])
                            x_fit = np.linspace(left_lim, right_lim, 100)
                            y_fit = gauss(x_fit, *params)
                            if params[0] > 0:
                                fit_max = [x_fit[np.argmax(y_fit)],np.max(y_fit)]
                            elif params[0] < 0:
                                fit_max = [x_fit[np.argmin(y_fit)],np.min(y_fit)]
                            gaussian, = self.ax2.plot(x_fit, y_fit,color='blue',
                                                      lw=p.SPECTRA_LINES_LW,zorder=3)
                            gauss_max = self.ax2.axvline(fit_max[0],color='red',
                                                      lw=p.SPECTRA_LINES_LW,ls=':',zorder=3)
                            self.spectrum_lines.gaussian_fit(gaussian=gaussian,gauss_max=gauss_max,
                                                             fit_max=fit_max)
                            self.canvas_spectrum.draw()
                        except Exception as e:
                            self.discard_fit_line()
                            msg = 'The gaussian fit for the line selected did not work.\nTry again!'
                            self.signal_msg.emit(msg)
                            print(datetime.datetime.now(),e)
                        
                if self.spectrum_lines.fitting:
                    if key_pressed == Qt.Key_H:
                        self.signal_open_addline_w.emit(self.spectrum_lines.fit_max[0],
                                         self.spectrum_lines.fit_max[1],
                                         [label.get_text() for label in self.spectrum_lines.labels])
                    if key_pressed == Qt.Key_J:
                        self.discard_fit_line()