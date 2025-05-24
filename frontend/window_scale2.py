import sys
import numpy as np
from PyQt5.QtWidgets import (QMainWindow, QLabel, QLineEdit, QPushButton, QVBoxLayout)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt
from utilities import scale_px_to_nm
import parameters as p


class ScaleWindow(QMainWindow):

    signal_verify_params = pyqtSignal(str, str)
    signal_submit_params = pyqtSignal(float, float)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_SCALE2, self)

        # Line edit
        self.ledit_m_param = self.findChild(QLineEdit,'ledit_m_param')
        self.ledit_b_param = self.findChild(QLineEdit,'ledit_b_param')
        # Layouts (for plotting)
        self.vbox_plot = self.findChild(QVBoxLayout,'vbox_plot')
        # Buttons
        self.btn_default = self.findChild(QPushButton,'btn_default')
        self.btn_submit_scale = self.findChild(QPushButton,'btn_submit_scale')

        # Create figure and canvas to plot
        self.figure_plot = plt.figure()
        self.canvas_plot = FigureCanvas(self.figure_plot)
        self.vbox_plot.addWidget(self.canvas_plot)

        self.btn_default.clicked.connect(self.set_scale_to_default)
        self.btn_submit_scale.clicked.connect(self.verify_params)


    def plot_scale(self, m, b):
        x_values = np.linspace(0, 1000, 1000)
        y_values = [scale_px_to_nm(x,m,b) for x in x_values]

        self.figure_plot.clf()
        xticks = [x for x in range(0,1001,250)]
        yticks = [y for y in range(int(np.min(y_values)),int(np.max(y_values)+1),int((np.max(y_values)-np.min(y_values))/5))]
        self.ax = self.figure_plot.add_subplot(111)
        self.ax.plot(x_values, y_values, color='red', lw=p.SCALE_LW)
        self.ax.minorticks_on()
        self.ax.tick_params(labelsize=p.SCALE_FS,axis='both',which='major',direction='in',length=16,width=1,
                       color='black',right=True,top=True)
        self.ax.tick_params(labelsize=p.SCALE_FS,axis='both',which='minor',direction='in',length=6,width=1,
                       color='black',right=True,top=True)
        self.ax.set_xticks(xticks,xticks,fontname=p.IMAGE_FN)
        self.ax.set_yticks(yticks,yticks,fontname=p.IMAGE_FN)
        self.ax.set_xlim(0,1000)
        self.ax.set_ylim(np.min(y_values),np.max(y_values))
        self.ax.set_xlabel('Pixels (px)',fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax.set_ylabel('Nanometers (nm)',fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax.grid(True, ls=':', lw=0.5*p.SCALE_LW, dashes=(1, 2))
        self.canvas_plot.draw()

    def set_scale_to_default(self):
        self.ledit_m_param.setText(str(p.M_PARAM))
        self.ledit_b_param.setText(str(p.B_PARAM))

    def verify_params(self):
        self.signal_verify_params.emit(self.ledit_m_param.text(),self.ledit_b_param.text())

    def submit_params(self, m, b, m_is_float, b_is_float):
        if not m_is_float:
            self.ledit_m_param.clear()
        if not b_is_float:
            self.ledit_b_param.clear()
        if m_is_float and b_is_float:
            self.signal_submit_params.emit(float(m),float(b))
            self.close()

    def start(self, last_m, last_b):
        self.ledit_m_param.setText(last_m)
        self.ledit_b_param.setText(last_b)
        self.plot_scale(float(last_m), float(last_b))
        self.show()
