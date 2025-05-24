# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QTableWidget, QTableWidgetItem, QPushButton)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Astropy
from astropy.table import Table

# Local imports
import parameters as p

class LinesWindow(QMainWindow):

    # SIGNALS
    signal_plot_line = pyqtSignal(str,str)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_LINES, self)

        # WIDGETS
        # Button
        self.btn_plot = self.findChild(QPushButton,'btn_plot')
        # Table
        self.table_lines = self.findChild(QTableWidget, 'table_lines')

        # Conections
        self.btn_plot.clicked.connect(self.selected_line)

        self.line_table_full = Table.read(p.PATH_LINE_LIST_FULL, format='ascii')
        self.name = []
        self.wrest = []

    # METHODS
    def selected_line(self):
        selected_row = self.table_lines.currentRow()

        if selected_row != -1:
            selected_name = self.table_lines.item(selected_row, 0).text()
            selected_wrest = self.table_lines.item(selected_row, 1).text()
            self.signal_plot_line.emit(selected_name,selected_wrest)
        else:
            pass

    def add_table_item(self, row, col, text):
        item = QTableWidgetItem(text)
        self.table_lines.setItem(row, col, item)

    def initiaze_table(self):
        self.table_lines.setRowCount(len(self.name))
        for i in range(len(self.name)):
            self.add_table_item(i, 0, str(self.name[i]))
            self.add_table_item(i, 1, str('{:.4f}'.format(self.wrest[i])))

    def start(self, wavelenght_range):
        mask_bot_wrest = (self.line_table_full['wrest'] >= wavelenght_range[0])
        mask_top_wrest = (self.line_table_full['wrest'] <= wavelenght_range[1])
        line_table_full = self.line_table_full[mask_bot_wrest & mask_top_wrest]
        self.name = line_table_full['name']
        self.wrest = [wv/10 for wv in line_table_full['wrest']]
        for i in range(len(self.name)):
            for char_ascii,char_utf8 in zip(p.GREEK_CHAR_ASCII,p.GREEK_CHAR_UTF8):
                self.name[i] = self.name[i].replace(char_ascii,char_utf8)
        wrest, name = zip(*sorted(zip(self.wrest, self.name)))
        self.name = list(name)
        self.wrest = list(wrest)
        self.initiaze_table()
        self.show()
        