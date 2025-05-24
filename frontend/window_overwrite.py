# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QPushButton)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Local imports
import parameters as p

class OverwriteWindow(QMainWindow):

    # SIGNALS
    signal_overwrite = pyqtSignal(bool)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_OVERWRITE, self)

        # WIDGETS
        # Buttons
        self.btn_no = self.findChild(QPushButton,'btn_no')
        self.btn_yes = self.findChild(QPushButton,'btn_yes')

        # Conections
        self.btn_no.clicked.connect(self.not_overwrite)
        self.btn_yes.clicked.connect(self.overwrite)

    # METHODS
    def not_overwrite(self):
        self.signal_overwrite.emit(False)
        self.close()

    def overwrite(self):
        self.signal_overwrite.emit(True)
        self.close()

    def popup(self):
        self.show()
        