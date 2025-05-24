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
from PyQt5.QtWidgets import (QMainWindow, QPushButton, QLabel, QComboBox, QTableWidget,
                             QRadioButton, QVBoxLayout, QFileDialog, QTableWidgetItem)

# Matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib import pyplot as plt
from matplotlib import figure

# Local imports
import parameters as p
from my_widgets import (FittingLines, SpectrumCursor)
from utilities import (gauss, full_extent)


class ScaleWindow(QMainWindow):

    # SIGNALS
    signal_load_lamp = pyqtSignal(str,int,int)
    signal_load_lamp_cal = pyqtSignal(str)
    signal_calculate_fit = pyqtSignal(str,list,list,tuple)
    signal_new_scale = pyqtSignal(dict)
    signal_msg = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        # Load UI files
        uic.loadUi(p.PATH_UI_WINDOW_SCALE, self)

        # Start parameters
        self.enable_user_events = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.params = None
        self.inversed_params = None
        self.rms = 0
        self.lamps_dir = ''
        self.lamps_cal_dir = ''
        self.proyection = 1
        self.width = 3
        self.plot_lamp_focus = 'ax1'
        self.grade_params = p.GRADES_PARAMS['1']

        # WIDGETS
        # Buttons
        self.btn_load_lamp = self.findChild(QPushButton,'btn_load_lamp')
        self.btn_load_lamp_cal = self.findChild(QPushButton,'btn_load_lamp_cal')
        self.btn_fit = self.findChild(QPushButton,'btn_fit')
        self.btn_save_scale = self.findChild(QPushButton,'btn_save_scale')
        self.btn_cancel = self.findChild(QPushButton,'btn_cancel')
        # Labels (just interactive ones)
        self.lbl_fit = self.findChild(QLabel,'lbl_fit')
        self.lbl_ax1_state = self.findChild(QLabel,'lbl_ax1_state')
        self.lbl_ax2_state = self.findChild(QLabel,'lbl_ax2_state')
        self.lbl_points = self.findChild(QLabel,'lbl_points')
        self.lbl_rms = self.findChild(QLabel,'lbl_rms')
        # Combo boxes
        self.cbox_grade = self.findChild(QComboBox,'cbox_grade')
        # Radio buttons
        self.rbtn_zoom_both = self.findChild(QRadioButton,'rbtn_zoom_both')
        self.rbtn_zoom_zaxis = self.findChild(QRadioButton,'rbtn_zoom_zaxis')
        self.rbtn_zoom_xaxis = self.findChild(QRadioButton,'rbtn_zoom_xaxis')
        self.rbtn_zoom_both_cal = self.findChild(QRadioButton,'rbtn_zoom_both_cal')
        self.rbtn_zoom_zaxis_cal = self.findChild(QRadioButton,'rbtn_zoom_zaxis_cal')
        self.rbtn_zoom_xaxis_cal = self.findChild(QRadioButton,'rbtn_zoom_xaxis_cal')
        # Layouts (for plotting)
        self.vbox_lamp = self.findChild(QVBoxLayout,'vbox_lamp')
        self.vbox_lamp_cal = self.findChild(QVBoxLayout,'vbox_lamp_cal')
        self.vbox_plot = self.findChild(QVBoxLayout,'vbox_plot')
        # Table
        self.points_table = self.findChild(QTableWidget, 'table_points')

        # Create figure and canvas to plot
        self.figure_lamp = plt.figure()
        self.canvas_lamp = FigureCanvas(self.figure_lamp)
        self.vbox_lamp.addWidget(self.canvas_lamp)

        self.figure_lamp_cal = plt.figure()
        self.canvas_lamp_cal = FigureCanvas(self.figure_lamp_cal)
        self.vbox_lamp_cal.addWidget(self.canvas_lamp_cal)

        self.figure_plot = plt.figure()
        self.canvas_plot = FigureCanvas(self.figure_plot)
        self.vbox_plot.addWidget(self.canvas_plot)
        
        # Add combo boxes options
        grade_list = [str(i) for i in range(1,5)]
        self.cbox_grade.addItems(grade_list)
        self.lbl_fit.setText(self.grade_params['fit'])
        minpoints = self.grade_params['minpoints']
        self.lbl_points.setText(f'Points (at least {minpoints})')

        # Connect widgets with mwthods
        self.btn_load_lamp.clicked.connect(self.search_lamp_file)
        self.btn_load_lamp_cal.clicked.connect(self.search_lamp_cal_file)
        self.btn_fit.clicked.connect(self.calculate_fit)
        self.btn_save_scale.clicked.connect(self.save_scale)
        self.btn_cancel.clicked.connect(self.cancel)
        self.cbox_grade.currentTextChanged.connect(self.grade_changed)

        # Connect mouse events with canvas
        self.canvas_lamp.mpl_connect('button_press_event', self.on_click)
        self.canvas_lamp.mpl_connect('scroll_event', self.on_scroll)
        self.canvas_lamp_cal.mpl_connect('button_press_event', self.on_click)
        self.canvas_lamp_cal.mpl_connect('scroll_event', self.on_scroll)

        # Create widgets, axes, or anything that needs to be initialized when the program starts
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.ax4 = None
        self.lamp_spectrum = None
        self.lamp_cal_spectrum = None
        self.ax1max = []
        self.ax2max = []
        self.fitting_lines = FittingLines(remove_threshold=5)
        self.cursor_ax1 = None
        self.cursor_ax2 = None
        
    # METHODS
    # Window
    def start(self, proyection, width):
        self.reset()
        self.proyection = proyection
        self.width = width
        self.plot_scale(lamps_active=False)
        self.showMaximized()

    def reset(self):
        self.fitting_lines.reset()
        self.cursor_ax1 = None
        self.cursor_ax2 = None
        self.figure_lamp.clf()
        self.figure_lamp_cal.clf()
        self.figure_plot.clf()
        self.enable_user_events = False
        self.setFocusPolicy(Qt.StrongFocus)
        self.params = None
        self.rms = 0
        self.lamps_dir = ''
        self.lamps_cal_dir = ''
        self.plot_lamp_focus = 'ax1'
        self.grade_params = p.GRADES_PARAMS['1']
        self.set_plot_focus_status_label(ax1_status=False, ax2_status=False)
        self.points_table.clear()
        self.points_table.setRowCount(0)
        self.cbox_grade.setCurrentIndex(0)
        self.enable_widgets(False)
        self.btn_save_scale.setEnabled(False)
        self.ax1 = None
        self.ax2 = None
        self.ax3 = None
        self.lamp_spectrum = None
        self.lamp_cal_spectrum = None
        self.ax1max = []
        self.ax2max = []
        self.canvas_lamp.draw()
        self.canvas_lamp_cal.draw()

    def save_scale(self):
        if self.params is not None:
            self.signal_new_scale.emit({'params':self.params,
                                        'inversed_params':self.inversed_params,
                                        'rms_px_to_nm_fit':self.rms})
            self.close()

    def cancel(self):
        self.close()

    def enable_widgets(self, enable):
        self.enable_user_events = enable
        self.cbox_grade.setEnabled(enable)
        self.rbtn_zoom_both.setEnabled(enable)
        self.rbtn_zoom_zaxis.setEnabled(enable)
        self.rbtn_zoom_xaxis.setEnabled(enable)
        self.rbtn_zoom_both_cal.setEnabled(enable)
        self.rbtn_zoom_zaxis_cal.setEnabled(enable)
        self.rbtn_zoom_xaxis_cal.setEnabled(enable)

    def focusOutEvent(self,event):
        self.setFocus(True)

    # File handling
    def search_lamp_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Lamp', self.lamps_dir,
                                                    'FIT files (*.FIT);;All Files (*)')
        if path:
            self.signal_load_lamp.emit(path, self.proyection, self.width)

    def search_lamp_cal_file(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Calibration Lamp', self.lamps_cal_dir,
                                             'Text files (*.txt);;FIT files (*.FIT);;All Files (*)')
        if path:
            self.signal_load_lamp_cal.emit(path)

    # Lamp
    def plot_lamp_spectrum(self, data, title, lamps_dir):
        self.lamps_dir = lamps_dir
        self.figure_lamp.clf()
        xlimits = [0,len(data)]
        yrange = abs(np.max(data)-np.min(data))
        ylimits = [int(np.min(data)-0.1*yrange),int(np.max(data)+0.1*yrange)]
        self.ax1max = [[xlimits[0],xlimits[1]],[ylimits[0],ylimits[1]]]
        xticks = [x for x in range(xlimits[0],xlimits[1]+1,int((xlimits[1]-xlimits[0])/10))]
        yticks = [y for y in range(ylimits[0],ylimits[1]+1,int((ylimits[1]-ylimits[0])/5))]
        self.ax1 = self.figure_lamp.add_subplot(111)
        self.lamp_spectrum, = self.ax1.plot(data,lw=p.SCALE_LW,color='black')
        self.ax1.minorticks_on()
        self.ax1.tick_params(labelsize=p.SCALE_FS,axis='both',which='major',direction='in',
                             length=16,width=1,color='black',right=True,top=True)
        self.ax1.tick_params(labelsize=p.SCALE_FS,axis='both',which='minor',direction='in',
                             length=6,width=1,color='black',right=True,top=True)
        self.ax1.set_xticks(xticks,xticks,fontname=p.SCALE_FN)
        self.ax1.set_yticks(yticks,yticks,fontname=p.SCALE_FN)
        self.ax1.set_xlim(xlimits[0],xlimits[1])
        self.ax1.set_ylim(ylimits[0],ylimits[1])
        self.ax1.set_xlabel('Pixels', fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax1.set_ylabel('Counts', fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        new_title = f'{title} spectrum (Proyection = {self.proyection}, Width = {self.width})'
        self.ax1.set_title(new_title,fontsize=1.2*p.SCALE_FS,fontname=p.SCALE_FN, pad=10)
        self.canvas_lamp.draw()
        if self.ax1 is not None and self.ax2 is not None:
            self.enable_widgets(True)
            self.initialize_cursor_ax1()
            self.initialize_cursor_ax2()
            self.set_plot_focus_status('ax1')
            self.plot_scale()
    
    def initialize_cursor_ax1(self):
        self.cursor_ax1 = SpectrumCursor(
                line=self.lamp_spectrum,
                numberformat="{:.0f}",
                show_axis='both', offset=[[5, 5],[5, 5]],
                textprops=[{'color':'blue','fontsize':p.SCALE_FS,'fontweight':'bold',
                            'fontfamily':p.SCALE_FN},
                           {'color':'black','fontsize':0.8*p.SCALE_FS,'fontweight':'bold',
                            'fontfamily':p.SCALE_FN}],
                admit_scale=False,
                ax=self.ax1,
                useblit=True,
                color='blue',
                linewidth=p.SCALE_LINES_LW, horizOn=False)
        self.canvas_lamp.draw()

    # Calibration lamp
    def plot_lamp_cal_spectrum(self, xlimits, ylimits, xdata, ydata, title, lamps_cal_dir):
        self.lamps_cal_dir = lamps_cal_dir
        self.figure_lamp_cal.clf()
        yrange = abs(np.max(ydata)-np.min(ydata))
        ylimits = [int(ylimits[0]-0.1*yrange),int(ylimits[1]+0.1*yrange)]
        xticks = [x for x in range(xlimits[0],xlimits[1]+1,int((xlimits[1]-xlimits[0])/10))]
        yticks = [y for y in range(ylimits[0],ylimits[1]+1,int((ylimits[1]-ylimits[0])/5))]
        self.ax2max = [[xlimits[0],xlimits[1]],[ylimits[0],ylimits[1]]]
        self.ax2 = self.figure_lamp_cal.add_subplot(111)
        self.lamp_cal_spectrum, = self.ax2.plot(xdata,ydata,lw=p.SCALE_LW,color='black')
        self.ax2.minorticks_on()
        self.ax2.tick_params(labelsize=p.SCALE_FS,axis='both',which='major',direction='in',
                             length=16,width=1,color='black',right=True,top=True)
        self.ax2.tick_params(labelsize=p.SCALE_FS,axis='both',which='minor',direction='in',
                             length=6,width=1,color='black',right=True,top=True)
        self.ax2.set_xticks(xticks,xticks,fontname=p.SCALE_FN)
        self.ax2.set_yticks(yticks,yticks,fontname=p.SCALE_FN)
        self.ax2.set_xlim(xlimits[0],xlimits[1])
        self.ax2.set_ylim(ylimits[0],ylimits[1])
        self.ax2.set_xlabel('Nanometers', fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax2.set_ylabel('Counts', fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax2.set_title(f'{title} spectrum', fontsize=1.2*p.SCALE_FS,fontname=p.SCALE_FN, pad=10)
        self.canvas_lamp_cal.draw()
        if self.ax1 is not None and self.ax2 is not None:
            self.enable_widgets(True)
            self.initialize_cursor_ax1()
            self.initialize_cursor_ax2()
            self.set_plot_focus_status('ax1')
            self.plot_scale()
    
    def initialize_cursor_ax2(self):
        self.cursor_ax2 = SpectrumCursor(
                line=self.lamp_cal_spectrum,
                numberformat="{:.2f}",
                show_axis='both', offset=[[5, 5],[5, 5]],
                textprops=[{'color':'blue','fontsize':p.SCALE_FS,'fontweight':'bold',
                            'fontfamily':p.SCALE_FN},
                           {'color':'black','fontsize':0.8*p.SCALE_FS,'fontweight':'bold',
                            'fontfamily':p.SCALE_FN}],
                admit_scale=False,
                ax=self.ax2,
                useblit=True,
                color='blue',
                linewidth=p.SCALE_LINES_LW, horizOn=False)
        self.canvas_lamp_cal.draw()

    # Lamps control
    def set_plot_focus_status(self, axname):
        if axname == 'ax1':
            self.rbtn_zoom_both.setEnabled(True)
            self.rbtn_zoom_zaxis.setEnabled(True)
            self.rbtn_zoom_xaxis.setEnabled(True)
            self.rbtn_zoom_both_cal.setEnabled(False)
            self.rbtn_zoom_zaxis_cal.setEnabled(False)
            self.rbtn_zoom_xaxis_cal.setEnabled(False)
            self.set_plot_focus_status_label(ax1_status=True, ax2_status=False)
        elif axname == 'ax2':
            self.rbtn_zoom_both_cal.setEnabled(True)
            self.rbtn_zoom_zaxis_cal.setEnabled(True)
            self.rbtn_zoom_xaxis_cal.setEnabled(True)
            self.rbtn_zoom_both.setEnabled(False)
            self.rbtn_zoom_zaxis.setEnabled(False)
            self.rbtn_zoom_xaxis.setEnabled(False)
            self.set_plot_focus_status_label(ax1_status=False, ax2_status=True)

    def set_plot_focus_status_label(self, ax1_status=False, ax2_status=False):
        if ax1_status:
            self.lbl_ax1_state.setText('Active')
            self.lbl_ax1_state.setStyleSheet(f"color: white;background-color: limegreen;")
        elif not ax1_status:
            self.lbl_ax1_state.setText('Inactive')
            self.lbl_ax1_state.setStyleSheet(f"color: white;background-color: red;")
        if ax2_status:
            self.lbl_ax2_state.setText('Active')
            self.lbl_ax2_state.setStyleSheet(f"color: white;background-color: limegreen;")
        elif not ax2_status:
            self.lbl_ax2_state.setText('Inactive')
            self.lbl_ax2_state.setStyleSheet(f"color: white;background-color: red;")

    def check_plot_focus(self):
        if self.plot_lamp_focus == 'ax1':
            canvas = self.canvas_lamp; ax = self.ax1; axmax = self.ax1max
        elif self.plot_lamp_focus == 'ax2':
            canvas = self.canvas_lamp_cal; ax = self.ax2; axmax = self.ax2max
        return canvas, ax, axmax

    def update_spectra_limits(self, canvas, ax, axis, bot_val, top_val):
        bot_val = int(bot_val)
        top_val = int(top_val)
        if axis == 'z':
            yticks = [y for y in range(bot_val,top_val+1,int((top_val-bot_val)/5))]
            yticks_labels = ['{:.0f}'.format(y) for y in yticks]
            ax.set_yticks(yticks,yticks_labels)
            ax.set_ylim(bot_val,top_val)
        elif axis == 'x':
            xticks = [x for x in range(bot_val,top_val+1,int((top_val-bot_val)/10))]
            xticks_labels = ['{:.0f}'.format(x) for x in xticks]
            ax.set_xticks(xticks,xticks_labels)
            ax.set_xlim(bot_val,top_val)
        canvas.draw()

    def translate_up(self):
        canvas,ax,axmax = self.check_plot_focus()
        limits = ax.get_ylim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] + p.SCALE_TRANSLATION_FACTOR*range_limits
        top_val = limits[1] + p.SCALE_TRANSLATION_FACTOR*range_limits
        if bot_val >= axmax[1][0] and top_val <= axmax[1][1]:
            self.update_spectra_limits(canvas, ax, 'z', bot_val, top_val)

    def translate_down(self):
        canvas,ax,axmax = self.check_plot_focus()
        limits = ax.get_ylim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] - p.SCALE_TRANSLATION_FACTOR*range_limits
        top_val = limits[1] - p.SCALE_TRANSLATION_FACTOR*range_limits
        if bot_val >= axmax[1][0] and top_val <= axmax[1][1]:
            self.update_spectra_limits(canvas, ax, 'z', bot_val, top_val)

    def translate_right(self):
        canvas,ax,axmax = self.check_plot_focus()
        limits = ax.get_xlim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] + p.SCALE_TRANSLATION_FACTOR*range_limits
        top_val = limits[1] + p.SCALE_TRANSLATION_FACTOR*range_limits
        if bot_val >= axmax[0][0] and top_val <= axmax[0][1]:
            self.update_spectra_limits(canvas, ax, 'x', bot_val, top_val)

    def translate_left(self):
        canvas,ax,axmax = self.check_plot_focus()
        limits = ax.get_xlim()
        range_limits = abs(limits[1] - limits[0])
        bot_val = limits[0] - p.SCALE_TRANSLATION_FACTOR*range_limits
        top_val = limits[1] - p.SCALE_TRANSLATION_FACTOR*range_limits
        if bot_val >= axmax[0][0] and top_val <= axmax[0][1]:
            self.update_spectra_limits(canvas, ax, 'x', bot_val, top_val)

    # Calibration (polynomial fit)
    def add_table_item(self, row, col, text):
        item = QTableWidgetItem(text)
        self.points_table.setItem(row, col, item)

    def update_points_table(self):
        pxrows = len(self.fitting_lines.pxlines)
        nmrows = len(self.fitting_lines.nmlines)
        nrows = np.max([pxrows,nmrows])
        self.points_table.setRowCount(np.max(nrows))
        for i in range(pxrows):
            self.add_table_item(i, 0, str(self.fitting_lines.pxdata[i]))
        for i in range(nmrows):
            self.add_table_item(i, 1, str(self.fitting_lines.nmdata[i]))
        self.update_grade()

    def grade_changed(self, grade):
        self.grade_params = p.GRADES_PARAMS[grade]
        self.update_fit_lbl()
        minpoints = self.grade_params['minpoints']
        self.lbl_points.setText(f'Points (at least {minpoints})')
        self.update_grade()
    
    def update_grade(self):
        pxrows = len(self.fitting_lines.pxlines)
        nmrows = len(self.fitting_lines.nmlines)
        nrows = np.max([pxrows,nmrows])
        if (pxrows != nmrows) or (nrows < self.grade_params['minpoints']):
            self.btn_fit.setEnabled(False)
        elif (pxrows == nmrows) and (nrows >= self.grade_params['minpoints']):
            self.btn_fit.setEnabled(True)

    def calculate_fit(self):
        grade = self.cbox_grade.currentText()
        x = self.fitting_lines.pxdata
        y = self.fitting_lines.nmdata
        xlimits = self.ax3.get_xlim()
        self.signal_calculate_fit.emit(grade, x, y, xlimits)

    def plot_fit(self,dict_fit):
        self.params = list(dict_fit['px_to_nm']['params'])
        self.inversed_params = list(dict_fit['nm_to_px']['params'])
        self.plot_scale(fit=dict_fit['px_to_nm'])

    def plot_scale(self, lamps_active=True, fit=None):
        self.figure_plot.clf()
        
        self.ax3 = self.figure_plot.add_subplot(111)
        
        if not lamps_active:
            xlimits = [0,10]
            ylimits = [0,10]
            xticks = [x for x in range(0,11,2)]
            yticks = [y for y in range(0,11,2)]
            xticks_labels = []
            yticks_labels = []

        if lamps_active:
            xlimits = self.ax1max[0]
            ylimits = self.ax2max[0]
            x_step = int((xlimits[1]-xlimits[0])/5)
            y_step = int((ylimits[1]-ylimits[0])/5)
            xticks = [x for x in range(int(xlimits[0]),int(xlimits[1])+1,x_step)]
            yticks = [y for y in range(int(ylimits[0]),int(ylimits[1])+1,y_step)]
            xticks_labels = ['{:.1f}'.format(x) for x in xticks]
            yticks_labels = ['{:.1f}'.format(y) for y in yticks]

        if fit is not None:
            self.ax3.plot(fit['xfit'], fit['yfit'], color='red', lw=1.5*p.SCALE_LW)
            for xdot,ydot in zip(fit['xdots'],fit['ydots']):
                self.ax3.scatter(xdot,ydot,s=p.SCALE_DOT_S,c='black')
            self.ax3.set_title(f'Polynomial regression grade {self.cbox_grade.currentText()}',
                                fontsize=1.2*p.SCALE_FS, fontname=p.SCALE_FN)
            self.update_fit_lbl()
            self.rms = fit['rms']
            self.lbl_rms.setText('{:.2e}'.format(fit['rms']))
            self.btn_save_scale.setEnabled(True)

        self.ax3.minorticks_on()
        self.ax3.tick_params(labelsize=p.SCALE_FS,axis='both',which='major',direction='in',
                             length=16,width=1,color='black',right=True,top=True)
        self.ax3.tick_params(labelsize=p.SCALE_FS,axis='both',which='minor',direction='in',
                             length=6,width=1,color='black',right=True,top=True)
        self.ax3.set_xticks(xticks,xticks_labels,fontname=p.SCALE_FN)
        self.ax3.set_yticks(yticks,yticks_labels,fontname=p.SCALE_FN)
        self.ax3.set_xlim(xlimits[0],xlimits[1])
        self.ax3.set_ylim(ylimits[0],ylimits[1])
        self.ax3.set_xlabel('Pixels (px)',fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax3.set_ylabel('Nanometers (nm)',fontsize=p.SCALE_FS, fontname=p.SCALE_FN)
        self.ax3.grid(True, ls=':', lw=0.5*p.SCALE_LW, dashes=(1, 2))
        self.canvas_plot.draw()

    def update_fit_lbl(self):
        grade = int(self.cbox_grade.currentText())
        if (self.params is None) or (len(self.params)-1 != grade):
            self.lbl_fit.setText(self.grade_params['fit'])
        elif (self.params is not None) and (len(self.params)-1 == grade):
            params = ['{:.1e}'.format(p) for p in self.params]
            fit_expression = 'y = '
            for i,param in zip([n-1 for n in range(len(params),0,-1)],params):
                if i == 0:
                    fit_expression += f'{param}'
                elif i == 1:
                    fit_expression += f'{param}x + '
                else:
                    fit_expression += f'{param}x^{i} + '
            self.lbl_fit.setText(fit_expression)

    # Events
    def click_line(self,canvas,ax,fitting_lines,cursor,button,lamp_list):
        canvas.setFocusPolicy(Qt.ClickFocus)
        canvas.setFocus()
        if button == 1:
            if fitting_lines.picking:
                fitting_lines.picking = False
                fitting_lines.adjusting = True
                line_x = float(cursor.text_x.get_text())
                line_y = float(cursor.text_y.get_text())
                guess = ax.axvline(line_x, color='blue', lw=p.SCALE_LINES_LW)
                guess_width_1 = ax.axvline(line_x-2,color='blue',lw=p.SCALE_LINES_LW,ls=':')
                guess_width_2 = ax.axvline(line_x+2,color='blue',lw=p.SCALE_LINES_LW,ls=':')
                fitting_lines.guess(line_guess=guess,line_guess_width=[guess_width_1,guess_width_2])
                canvas.draw()
        elif button == 3:
            line_x = float(cursor.text_x.get_text())
            fitting_lines.remove_line(line_x,lamp_list)
            if fitting_lines.adjusting:
                fitting_lines.line_guess.remove()
                fitting_lines.line_guess_width[0].remove()
                fitting_lines.line_guess_width[1].remove()
                fitting_lines.line_guess = None
                fitting_lines.line_guess_width = None
                fitting_lines.adjusting = False
                fitting_lines.picking = True
            self.canvas_lamp.draw()
            self.canvas_lamp_cal.draw()
            self.update_points_table()

    def on_click(self, event):
        if self.enable_user_events:
            if self.ax1.in_axes(event) and self.plot_lamp_focus == 'ax1':
                self.click_line(self.canvas_lamp,self.ax1,self.fitting_lines,self.cursor_ax1,
                                event.button,'px')
            elif self.ax2.in_axes(event) and self.plot_lamp_focus == 'ax2':
                self.click_line(self.canvas_lamp_cal,self.ax2,self.fitting_lines,
                                self.cursor_ax2,event.button,'nm')

    def scroll_zoom(self, canvas, ax, axmax, xdata, ydata, step, rbtns=[None,None,None]):
        zoom = abs(step) + p.SCALE_ZOOM_FACTOR
        rbtn_zoom_both = rbtns[0]
        rbtn_zoom_zaxis = rbtns[1]
        rbtn_zoom_xaxis = rbtns[2]

        # Z axis
        z_limits = ax.get_ylim()
        z_min_value = axmax[1][0]
        z_max_value = axmax[1][1]
        z_range_i = z_limits[1] - z_limits[0]
        z_center = ydata

        # X axis
        x_limits = ax.get_xlim()
        x_min_value = axmax[0][0]
        x_max_value = axmax[0][1]
        x_range_i = x_limits[1] - x_limits[0]
        x_center = xdata

        # Zoom in
        if step > 0:
            # Z axis
            if rbtn_zoom_both.isChecked() or rbtn_zoom_zaxis.isChecked():
                z_range_f = z_range_i/zoom
                z_bot_val = z_center - z_range_f/2
                z_top_val = z_center + z_range_f/2

                if z_bot_val < z_min_value:
                    z_bot_val = z_min_value
                if z_top_val > z_max_value:
                    z_top_val = z_max_value

                if abs(z_top_val - z_bot_val) >= p.SCALE_ZOOM_IN_MAX:
                    self.update_spectra_limits(canvas, ax, 'z', z_bot_val, z_top_val)

            # X axis
            if rbtn_zoom_both.isChecked() or rbtn_zoom_xaxis.isChecked():
                x_range_f = x_range_i/zoom
                x_bot_val = x_center - x_range_f/2
                x_top_val = x_center + x_range_f/2

                if x_bot_val < x_min_value:
                    x_bot_val = x_min_value
                if x_top_val > x_max_value:
                    x_top_val = x_max_value

                if abs(x_top_val - x_bot_val) >= p.SCALE_ZOOM_IN_MAX:
                    self.update_spectra_limits(canvas, ax, 'x', x_bot_val, x_top_val)

        # Zoom out
        if step < 0:
            # Z axis
            if rbtn_zoom_both.isChecked() or rbtn_zoom_zaxis.isChecked():
                z_range_f = z_range_i*zoom
                if not (abs(z_limits[1] - z_limits[0]) == abs(z_max_value - z_min_value)):
                    z_bot_val = z_limits[0] - (z_range_f-z_range_i)/2
                    z_top_val = z_limits[1] + (z_range_f-z_range_i)/2

                    if z_bot_val < z_min_value:
                        z_bot_val = z_min_value
                    if z_top_val > z_max_value:
                        z_top_val = z_max_value

                    self.update_spectra_limits(canvas, ax, 'z', z_bot_val, z_top_val)
            
            # X axis
            if rbtn_zoom_both.isChecked() or rbtn_zoom_xaxis.isChecked():
                x_range_f = x_range_i*zoom
                if not (abs(x_limits[1] - x_limits[0]) == abs(x_max_value - x_min_value)):
                    x_bot_val = x_limits[0] - (x_range_f-x_range_i)/2
                    x_top_val = x_limits[1] + (x_range_f-x_range_i)/2

                    if x_bot_val < x_min_value:
                        x_bot_val = x_min_value
                    if x_top_val > x_max_value:
                        x_top_val = x_max_value

                    self.update_spectra_limits(canvas, ax, 'x', x_bot_val, x_top_val)

    def on_scroll(self, event):
        if self.enable_user_events:
            if self.ax1.in_axes(event) and self.plot_lamp_focus == 'ax1':
                self.scroll_zoom(self.canvas_lamp, self.ax1, self.ax1max,
                              event.xdata, event.ydata, event.step,
                              rbtns=[self.rbtn_zoom_both,self.rbtn_zoom_zaxis,self.rbtn_zoom_xaxis])
            if self.ax2.in_axes(event) and self.plot_lamp_focus == 'ax2':
                self.scroll_zoom(self.canvas_lamp_cal, self.ax2, self.ax2max,
                  event.xdata, event.ydata, event.step,
                  rbtns=[self.rbtn_zoom_both_cal,self.rbtn_zoom_zaxis_cal,self.rbtn_zoom_xaxis_cal])

    def lines_keyevent(self, key_pressed, ax, axmax, canvas, spectrum, fitting_lines, lamp_list):
        if fitting_lines.adjusting:
            last_w1 = fitting_lines.line_guess_width[0].get_xdata()[0]
            last_w2 = fitting_lines.line_guess_width[1].get_xdata()[0]
            if key_pressed == Qt.Key_M:
                fitting_lines.line_guess_width[0].set_xdata([last_w1-1,last_w1-1])
                fitting_lines.line_guess_width[1].set_xdata([last_w2+1,last_w2+1])
                canvas.draw()
            elif key_pressed == Qt.Key_N:
                if abs(last_w2-last_w1) > 4:
                    fitting_lines.line_guess_width[0].set_xdata([last_w1+1,last_w1+1])
                    fitting_lines.line_guess_width[1].set_xdata([last_w2-1,last_w2-1])
                    canvas.draw()
            elif key_pressed == Qt.Key_G:
                fitting_lines.adjusting = False
                fitting_lines.fitting = True
                left_lim = int(fitting_lines.line_guess_width[0].get_xdata()[0])
                right_lim = int(fitting_lines.line_guess_width[1].get_xdata()[0])
                xdata = [x for x in spectrum.get_xdata() if (x >= left_lim) and (x <= right_lim)]
                ydata = [y for y,x in zip(spectrum.get_ydata(),spectrum.get_xdata()) \
                                                                if (x>=left_lim) and (x<=right_lim)]
                fitting_lines.line_guess.remove()
                fitting_lines.line_guess_width[0].remove()
                fitting_lines.line_guess_width[1].remove()
                fitting_lines.line_guess = None
                fitting_lines.line_guess_width = None
                try:
                    params, _ = curve_fit(gauss,xdata,ydata,
                                      p0=[np.max(ydata),np.min(ydata),np.mean(xdata),np.std(xdata)])
                    x_fit = np.linspace(left_lim, right_lim, 100)
                    y_fit = gauss(x_fit, *params)
                    if params[0] > 0:
                        fit_max = [x_fit[np.argmax(y_fit)],np.max(y_fit)]
                    elif params[0] < 0:
                        fit_max = [x_fit[np.argmin(y_fit)],np.min(y_fit)]
                    gaussian, = ax.plot(x_fit,y_fit,color='blue',lw=p.SPECTRA_LINES_LW,zorder=3)
                    gauss_max = ax.axvline(fit_max[0],color='red',lw=p.SPECTRA_LINES_LW,ls=':',
                                           zorder=3)
                    fitting_lines.gaussian_fit(gaussian=gaussian,gauss_max=gauss_max,fit_max=fit_max)
                    canvas.draw()
                except Exception as e:
                    fitting_lines.discard_fit()
                    canvas.draw()
                    self.update_points_table()
                    msg = 'The gaussian fit for the line selected did not work.\nTry again!'
                    self.signal_msg.emit(msg)
                    print(datetime.datetime.now(),e)
        if fitting_lines.fitting:
            if key_pressed == Qt.Key_H:
                if fitting_lines.fit_max is not None:
                    line = ax.axvline(fitting_lines.fit_max[0], color='red', lw=p.SCALE_LINES_LW)
                    fitting_lines.add_line(line, fitting_lines.fit_max[0], lamp_list)
                    canvas.draw()
                self.update_points_table()
            if key_pressed == Qt.Key_J:
                fitting_lines.discard_fit()
                canvas.draw()
                self.update_points_table()

    def keyPressEvent(self, event):
        if isinstance(event, QKeyEvent):
            key_pressed = event.key()
            if self.enable_user_events:
                if key_pressed == Qt.Key_L:
                    if self.plot_lamp_focus == 'ax1':
                        self.plot_lamp_focus = 'ax2'
                        self.set_plot_focus_status('ax2')
                    elif self.plot_lamp_focus == 'ax2':
                        self.plot_lamp_focus = 'ax1'
                        self.set_plot_focus_status('ax1')
                if key_pressed == Qt.Key_Comma:
                    if self.plot_lamp_focus == 'ax1':
                        if self.rbtn_zoom_both.isChecked():
                            self.rbtn_zoom_zaxis.setChecked(True)
                        elif self.rbtn_zoom_zaxis.isChecked():
                            self.rbtn_zoom_xaxis.setChecked(True)
                        elif self.rbtn_zoom_xaxis.isChecked():
                            self.rbtn_zoom_both.setChecked(True)
                    elif self.plot_lamp_focus == 'ax2':
                        if self.rbtn_zoom_both_cal.isChecked():
                            self.rbtn_zoom_zaxis_cal.setChecked(True)
                        elif self.rbtn_zoom_zaxis_cal.isChecked():
                            self.rbtn_zoom_xaxis_cal.setChecked(True)
                        elif self.rbtn_zoom_xaxis_cal.isChecked():
                            self.rbtn_zoom_both_cal.setChecked(True)
                if key_pressed == Qt.Key_Up:
                    self.translate_up()
                if key_pressed == Qt.Key_Down:
                    self.translate_down()
                if key_pressed == Qt.Key_Right:
                    self.translate_right()
                if key_pressed == Qt.Key_Left:
                    self.translate_left()

                if self.plot_lamp_focus == 'ax1':
                    self.lines_keyevent(key_pressed,self.ax1,self.ax1max,self.canvas_lamp,
                                        self.lamp_spectrum,self.fitting_lines,'px')
                if self.plot_lamp_focus == 'ax2':
                    self.lines_keyevent(key_pressed,self.ax2,self.ax2max,self.canvas_lamp_cal,
                                        self.lamp_cal_spectrum,self.fitting_lines,'nm')

                


    
