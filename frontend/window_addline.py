# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QLabel, QLineEdit, QPushButton, QComboBox, QVBoxLayout)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Matplotlib
import matplotlib.colors as mcolors
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt

# Local imports
import parameters as p

class AddlineWindow(QMainWindow):

    # SIGNALS
    signal_submit_line = pyqtSignal(str,list)
    signal_discard_line = pyqtSignal()
    signal_add_line = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_ADDLINE, self)

        # WIDGETS
        # Labels
        self.labl_y = self.findChild(QLabel,'labl_y')
        # Line edit
        self.ledit_name = self.findChild(QLineEdit,'ledit_name')
        # Buttons
        self.btn_add = self.findChild(QPushButton,'btn_add')
        self.btn_discard = self.findChild(QPushButton,'btn_discard')
        # Combo box
        self.cbox_greek_letters = self.findChild(QComboBox,'cbox_greek_letters')
        self.cbox_color = self.findChild(QComboBox,'cbox_color')
        self.cbox_valign = self.findChild(QComboBox,'cbox_valign')
        self.cbox_halign = self.findChild(QComboBox,'cbox_halign')
        self.cbox_layer = self.findChild(QComboBox,'cbox_layer')
        self.cbox_type = self.findChild(QComboBox,'cbox_type')
        # Layouts (for plotting)
        self.vbox_line = self.findChild(QVBoxLayout,'vbox_line')

        # Create figure and canvas to plot the spectrum
        self.figure_line = plt.figure()
        self.canvas_line = FigureCanvas(self.figure_line)
        self.vbox_line.addWidget(self.canvas_line)

        # Add combo box options
        greek_letters = ['Add greek letter', 
                         'α', 'β', 'γ', 'δ', 'ε', 'ζ', 'η', 'θ', 'ι', 'κ', 'λ', 'μ', 
                         'ν', 'ξ', 'ο', 'π', 'ρ', 'σ', 'τ', 'υ', 'φ', 'χ', 'ψ', 'ω',]
        self.cbox_greek_letters.addItems(greek_letters)

        colors = ['red','blue','green','magenta','black']
        css4_colors = mcolors.CSS4_COLORS
        for color in css4_colors:
            if color not in colors: colors.append(color)
        self.cbox_color.addItems(colors)

        valign = ['bottom','top']
        self.cbox_valign.addItems(valign)
        halign = ['right','left']
        self.cbox_halign.addItems(halign)
        layers = [str(i) for i in range(1,6)]
        self.cbox_layer.addItems(layers)
        types = ['──────',
                 '─  ─  ─  ─',
                 '······················',
                 '· ─ · ─ · ─ ·']
        self.types_mpl = {'──────':'solid',
                          '─  ─  ─  ─':'dashed',
                          '······················':'dotted',
                          '· ─ · ─ · ─ ·':'dashdot'
                         }
        self.cbox_type.addItems(types)

        # Conections
        self.btn_add.clicked.connect(self.submit_line)
        self.btn_discard.clicked.connect(self.discard_line)
        self.ledit_name.returnPressed.connect(self.submit_line)
        self.cbox_greek_letters.currentIndexChanged.connect(lambda: self.add_greek_letter())
        self.cbox_color.currentIndexChanged.connect(lambda: self.color_changed())
        self.cbox_type.currentIndexChanged.connect(lambda: self.type_changed())
        self.cbox_layer.currentIndexChanged.connect(lambda: self.layer_changed())
        self.cbox_valign.currentIndexChanged.connect(lambda: self.valign_changed())
        self.cbox_halign.currentIndexChanged.connect(lambda: self.halign_changed())
        self.ledit_name.textChanged.connect(self.name_changed)

        self.ax = None
        self.line = None
        self.label = None
        self.layers_ln = None
        self.layers_lbl = None
        self.existing_lines = []

    # METHODS
    def add_greek_letter(self):
        if self.cbox_greek_letters.currentText() != 'Add greek letter':
            last_name = self.ledit_name.text()
            self.ledit_name.setText(last_name + self.cbox_greek_letters.currentText())
            self.cbox_greek_letters.setCurrentIndex(0)

    def submit_line(self):
        self.signal_submit_line.emit(self.ledit_name.text(), self.existing_lines)

    def discard_line(self):
        self.close()

    def ln_validation(self, valid, error):
        if valid:
            self.signal_add_line.emit({'name':self.ledit_name.text(),
                                       'color':self.cbox_color.currentText(),
                                       'valign':self.cbox_valign.currentText(),
                                       'halign':self.cbox_halign.currentText(),
                                       'layer':self.cbox_layer.currentText(),
                                       'type':self.types_mpl[self.cbox_type.currentText()]
                                      })
            self.close()
        elif not valid:
            self.ledit_name.setPlaceholderText(error)
            self.ledit_name.setText('')

    def name_changed(self, name):
        if self.label:
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
            self.label.set_text(full_name)
            self.canvas_line.draw()

    def color_changed(self):
        if self.line and self.label:
            color = self.cbox_color.currentText()
            self.line.set_c(color)
            self.label.set_c(color)
            self.canvas_line.draw()

    def type_changed(self):
        if self.line:
            ltype = self.types_mpl[self.cbox_type.currentText()]
            self.line.set_ls(ltype)
            self.canvas_line.draw()

    def layer_changed(self):
        if self.label:
            valign = self.cbox_valign.currentText()
            layer = self.cbox_layer.currentText()
            if valign == 'bottom':
                ylblpos = int(layer)
            elif valign == 'top':
                ylblpos = 12 - int(layer)
            self.label.set_y(ylblpos)
            self.canvas_line.draw()

    def valign_changed(self):
        if self.label:
            valign = self.cbox_valign.currentText()
            self.label.set_va(valign)
            for i in range(1,6):
                if valign == 'bottom':
                    self.layers_ln[i-1].set_ydata(i)
                    self.layers_lbl[i-1].set_y(i)
                elif valign == 'top':
                    self.layers_ln[i-1].set_ydata(12-i)
                    self.layers_lbl[i-1].set_y(12-i)
                self.layers_lbl[i-1].set_va(valign)
            self.layer_changed()

    def halign_changed(self):
        if self.label:
            halign = self.cbox_halign.currentText()
            if halign == 'left':
                label_halign = 'right'
                for lbl in self.layers_lbl:
                    lbl.set_x(10.8)
                    lbl.set_ha(label_halign)
            if halign == 'right':
                label_halign = 'left'
                for lbl in self.layers_lbl:
                    lbl.set_x(1.2)
                    lbl.set_ha(label_halign)
            self.label.set_ha(label_halign)
            self.canvas_line.draw()

    def plot_line(self, x):
        self.figure_line.clf()
        self.ax = self.figure_line.add_subplot(111)

        line_pos = x
        line_color = self.cbox_color.currentText()
        line_type = self.types_mpl[self.cbox_type.currentText()]
        label_name = self.ledit_name.text()
        label_valign = self.cbox_valign.currentText()
       
        if self.cbox_halign.currentText() == 'left':
             label_halign = 'right'
        if self.cbox_halign.currentText() == 'right':
             label_halign = 'left'

        label_layer = self.cbox_layer.currentText()

        self.line = self.ax.axvline(6,color=line_color,ls=line_type,lw=p.SPECTRA_LINES_LW,zorder=3)

        if label_valign == 'bottom':
            ylblpos = int(label_layer)
        elif label_valign == 'top':
            ylblpos = 12 - int(label_layer)
        self.label = self.ax.text(6,ylblpos,label_name,fontsize=0.7*p.SPECTRA_FS,
                                  color=line_color,ha=label_halign,va=label_valign,
                                  fontname=p.SPECTRA_FN,zorder=3)


        self.layers_ln = []
        self.layers_lbl = []
        for i in range(1,6):
            line = self.ax.axhline(i,color='darkgrey',ls=':',lw=0.5*p.SPECTRA_LINES_LW,zorder=1)
            label = self.ax.text(1.2,i,f'Layer {i}',fontsize=0.5*p.SPECTRA_FS,zorder=1,
                                 color='darkgrey',ha='left',va='bottom',
                                 fontname=p.SPECTRA_FN)
            self.layers_ln.append(line)
            self.layers_lbl.append(label)


        self.ax.minorticks_on()
        self.ax.tick_params(labelsize=p.PREVIEW*p.SPECTRA_FS,axis='both',which='major',
                             direction='in',length=16,width=1,color='black',right=True,
                             top=True)
        self.ax.tick_params(labelsize=p.PREVIEW*p.SPECTRA_FS,axis='both',which='minor',
                             direction='in',length=6,width=1,color='black',right=True,
                             top=True)
        xtickslbl = ['' for i in range(0,13,2)]
        xtickslbl[3] = '{:.1f}'.format(x)
        self.ax.set_xticks([i for i in range(0,13,2)],xtickslbl,fontname=p.SPECTRA_FN)
        self.ax.set_yticks([i for i in range(0,13,2)],[],fontname=p.SPECTRA_FN)
        self.ax.set_xlim(0,12)
        self.ax.set_ylim(0,12)
        self.ax.set_xlabel('Pixels',fontsize=p.PREVIEW*p.SPECTRA_FS,fontname=p.SPECTRA_FN)
        self.ax.set_ylabel('')
        self.ax.set_title('Preview',fontsize=p.PREVIEW*1.2*p.SPECTRA_FS,fontname=p.SPECTRA_FN,
                          pad=10)

        self.canvas_line.draw()

    def start(self, x, y, existing_lines):
        self.lbl_y.setText(str(int(y)))
        self.ledit_name.setPlaceholderText('Insert line name')
        self.ledit_name.setText('')
        self.cbox_greek_letters.setCurrentIndex(0)
        self.cbox_color.setCurrentIndex(0)
        self.cbox_valign.setCurrentIndex(0)
        self.cbox_halign.setCurrentIndex(0)
        self.cbox_layer.setCurrentIndex(0)
        self.cbox_type.setCurrentIndex(0)
        self.existing_lines = existing_lines
        self.plot_line(x)
        self.show()
    
    def closeEvent(self, event):
        self.signal_discard_line.emit()
        event.accept()