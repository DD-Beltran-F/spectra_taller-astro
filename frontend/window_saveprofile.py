# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt

# Local imports
import parameters as p

class SaveProfileWindow(QMainWindow):

    # SIGNALS
    signal_submit_file = pyqtSignal(str)
    signal_save_file = pyqtSignal(str,str)
    signal_check_overwrite = pyqtSignal(str)
    signal_show_overwrite_w = pyqtSignal()
    signal_save_file_canceled = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_SAVEPROFILE, self)

        # WIDGETS
        # Labels
        self.lbl_imagefile = self.findChild(QLabel,'lbl_imagefile')
        self.lbl_imagesize = self.findChild(QLabel,'lbl_imagesize')
        self.lbl_spectrum_proyection = self.findChild(QLabel,'lbl_spectrum_proyection')
        self.lbl_spectrum_width = self.findChild(QLabel,'lbl_spectrum_width')
        self.lbl_spectrum_lines = self.findChild(QLabel,'lbl_spectrum_lines')
        self.lbl_spectrum_scale = self.findChild(QLabel,'lbl_spectrum_scale')
        # Buttons
        self.btn_save = self.findChild(QPushButton,'btn_save')
        self.btn_cancel = self.findChild(QPushButton,'btn_cancel')
        # Line edit
        self.ledit_filename = self.findChild(QLineEdit,'ledit_filename')
        self.ledit_title = self.findChild(QLineEdit,'ledit_title')

        # Layouts (for plotting)
        self.vbox_spectrum_preview = self.findChild(QVBoxLayout,'vbox_spectrum_preview')

        # Create figure and canvas to plot the spectrum
        self.figure_spectrum_preview = plt.figure()
        self.canvas_spectrum_preview = FigureCanvas(self.figure_spectrum_preview)
        self.vbox_spectrum_preview.addWidget(self.canvas_spectrum_preview)

        # Conections
        self.btn_save.clicked.connect(self.submit_file)
        self.btn_cancel.clicked.connect(self.cancel)
        self.ledit_title.textChanged.connect(self.title_changed)

        self.ax2 = None
        self.title = 'Spectrum'

    def title_changed(self, title):
        if self.ax2 is not None:
            if title == '':
                title = self.title
            self.ax2.set_title(title,fontsize=p.PREVIEW*1.2*p.SPECTRA_FS,fontname=p.SPECTRA_FN,
                pad=10)
            self.canvas_spectrum_preview.draw()


    def submit_file(self):
        self.signal_submit_file.emit(self.ledit_filename.text())

    def fn_validation(self, valid):
        if valid:
            self.signal_check_overwrite.emit(self.ledit_filename.text())
        elif not valid:
            self.ledit_filename.setPlaceholderText('Must be letters, numbers, space or underscore')
            self.ledit_filename.setText('')

    def overwrite_result(self, will_overwrite):
        if will_overwrite:
            self.signal_show_overwrite_w.emit()
        elif not will_overwrite:
            self.save_file()

    def overwrite(self, overwrite):
        if overwrite:
            self.save_file()
        elif not overwrite:
            self.ledit_filename.setPlaceholderText('Insert file name')
            self.ledit_filename.setText('')

    def save_file(self):
        self.signal_save_file.emit(self.ledit_filename.text(),self.ax2.get_title())
        self.close()
    
    def plot_spectrum(self, figure):
        self.figure_spectrum_preview.clf()
        self.title = figure['title']
        self.ax2 = self.figure_spectrum_preview.add_subplot(111)
        self.ax2.plot(figure['data'],lw=p.PREVIEW*p.SPECTRA_LW,color='black')
        self.ax2.minorticks_on()
        self.ax2.tick_params(labelsize=p.PREVIEW*p.SPECTRA_FS,axis='both',which='major',
                             direction='in',length=p.PREVIEW*16,width=1,color='black',right=True,
                             top=True)
        self.ax2.tick_params(labelsize=p.PREVIEW*p.SPECTRA_FS,axis='both',which='minor',
                             direction='in',length=p.PREVIEW*6,width=1,color='black',right=True,
                             top=True)
        self.ax2.set_xticks(figure['xticks'],figure['xticks_labels'],fontname=p.SPECTRA_FN)
        self.ax2.set_yticks(figure['yticks'],figure['yticks_labels'],fontname=p.SPECTRA_FN)
        self.ax2.set_xlim(figure['xlim'][0],figure['xlim'][1])
        self.ax2.set_ylim(figure['ylim'][0],figure['ylim'][1])
        self.ax2.set_xlabel(figure['xlabel'],fontsize=p.PREVIEW*p.SPECTRA_FS,fontname=p.SPECTRA_FN)
        self.ax2.set_ylabel(figure['ylabel'],fontsize=p.PREVIEW*p.SPECTRA_FS,fontname=p.SPECTRA_FN)
        self.ax2.set_title(figure['title'],fontsize=p.PREVIEW*1.2*p.SPECTRA_FS,
                           fontname=p.SPECTRA_FN,pad=10)

        for line_pos,line_text,line_color,line_type,line_align in zip(figure['lines_pos'],\
                                                                      figure['lines_names'],\
                                                                      figure['lines_color'],\
                                                                      figure['lines_types'],\
                                                                      figure['lines_names_align']):
            self.ax2.axvline(line_pos[0],color=line_color,ls=line_type,
                             lw=p.PREVIEW*p.SPECTRA_LINES_LW)
            if line_align['valign'] == 'bottom':
                ylblpos = figure['ylim'][0]+0.035*(figure['ylim'][1]-figure['ylim'][0])
            elif line_align['valign'] == 'top':
                ylblpos = figure['ylim'][1]-0.035*(figure['ylim'][1]-figure['ylim'][0])
            self.ax2.text(line_pos[0],ylblpos,line_text,fontsize=p.PREVIEW*0.7*p.SPECTRA_FS,
                          color=line_color,ha=line_align['halign'],va=line_align['valign'],
                          fontname=p.SPECTRA_FN)

        self.canvas_spectrum_preview.draw()

    def cancel(self):
        self.signal_save_file_canceled.emit(True)
        self.close()


    def start(self, data):
        image_file = data['image_file']
        image_size = data['image_size']
        proyection = data['proyection']
        width = data['width']
        scale_params = data['scale_params']
        spectrum = data['spectrum']
        self.ledit_filename.setPlaceholderText('Insert file name')
        self.ledit_filename.setText('')
        self.ledit_title.setPlaceholderText('Insert new title')
        self.ledit_title.setText('')
        self.lbl_imagefile.setText(image_file)
        self.lbl_imagesize.setText(f'{image_size[0]} x {image_size[1]} (px)')
        self.lbl_spectrum_proyection.setText(proyection)
        self.lbl_spectrum_width.setText(width)
        self.lbl_spectrum_lines.setText(str(len(spectrum['lines_pos'])))
        self.lbl_spectrum_scale.setText(scale_params)
        self.plot_spectrum(spectrum)
        self.show()
        