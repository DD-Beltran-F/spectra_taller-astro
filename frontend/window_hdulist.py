# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QLabel, QMainWindow, QTableWidget, QTableWidgetItem, QPushButton,
                             QScrollArea, QWidget, QVBoxLayout)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Astropy
from astropy.io import fits
from astropy.table import Table

# Local imports
import parameters as p

class HDUListWindow(QMainWindow):

    # SIGNALS
    signal_plot_line = pyqtSignal(str,str)
    signal_cancel = pyqtSignal()
    signal_read_hdu = pyqtSignal(int,str)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_HDULIST, self)

        # WIDGETS
        # Labels
        self.lbl_header = self.findChild(QLabel,'lbl_header')
        # Button
        self.btn_read = self.findChild(QPushButton,'btn_read')
        self.btn_cancel = self.findChild(QPushButton,'btn_cancel')
        # Table
        self.table_hdu = self.findChild(QTableWidget, 'table_hdu')
        # Scroll Area
        self.scrollarea_header = self.findChild(QScrollArea, 'scrollarea_header')
        # Boxes and widgets
        self.widget_hdu = QWidget()            
        self.vbox_hdu = QVBoxLayout()

        

        # Conections
        #self.btn_plot.clicked.connect(self.selected_line)
        self.btn_read.clicked.connect(self.selected_hdu)
        self.btn_cancel.clicked.connect(self.cancel)
        self.table_hdu.itemClicked.connect(self.item_clicked)

        self.vbox_hdu.addWidget(self.lbl_header)
        self.widget_hdu.setLayout(self.vbox_hdu)
        self.scrollarea_header.setWidgetResizable(True)
        self.scrollarea_header.setWidget(self.widget_hdu)
        self.path = ''
        self.hdulist = []

    # METHODS
    def selected_hdu(self):
        selected_row = self.table_hdu.currentRow()

        if selected_row != -1:
            self.signal_read_hdu.emit(selected_row,self.path)
            self.cancel()
        else:
            pass

    def item_clicked(self, item):
        self.lbl_header.setText(self.header_format(self.hdulist[item.text()].header))
        self.lbl_header.adjustSize()

    def add_table_item(self, row, col, text):
        item = QTableWidgetItem(text)
        self.table_hdu.setItem(row, col, item)

    def initiaze_table(self):
        self.table_hdu.setRowCount(len(self.hdulist))
        for i,name in enumerate(self.hdulist):
            self.add_table_item(i, 0, name)

    def header_format(self, header):
        card_names = [str(card) for card in header]
        card_values = [str(header[card]) for card in header]
        card_comments = [str(header.comments[card]) for card in header]
        max_nlen = len(max(card_names, key=len))
        max_vlen = len(max(card_values, key=len))
        max_colen = len(max(card_comments, key=len))

        header_text = f'{"KEYWORD":<{max_nlen}} │ {"VALUE":<{max_vlen}} │ {"COMMENT":<{max_colen}}\n'
        header_text += f'{"":─^{max_nlen}}─┴─{"":─^{max_vlen}}─┴─{"":─^{max_colen}}\n'
        for i in range(len(card_names)):
            if card_comments[i] != '':
                header_text += f'{card_names[i]:<{max_nlen}} = {card_values[i]:.<{max_vlen}}..{card_comments[i]:<{max_colen}}\n'
            else:
                header_text += f'{card_names[i]:<{max_nlen}} = {card_values[i]:<{max_vlen}}\n'
        return header_text

    def cancel(self):
        self.signal_cancel.emit()
        self.close()

    def start(self, hdu_list, path):
        self.path = path
        tuple_hdu_list = [(str(hdu.name),hdu) for hdu in hdu_list]
        self.hdulist = {name: hdu for name,hdu in tuple_hdu_list}
        header0 = tuple_hdu_list[0][1].header
        self.lbl_header.setText(self.header_format(header0))
        self.lbl_header.adjustSize()
        self.table_hdu.setCurrentCell(0,0)
        self.initiaze_table()
        self.show()
        