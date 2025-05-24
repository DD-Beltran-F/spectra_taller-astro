# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QLabel, QLineEdit)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Local imports
import parameters as p

class StretchWindow(QMainWindow):

    # SIGNALS
    signal_submit_stretch = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_STRETCH, self)

        # WIDGETS
        # Line edit
        self.ledit_stretch = self.findChild(QLineEdit,'ledit_stretch')

        # Conections
        self.ledit_stretch.returnPressed.connect(self.submit_stretch)

    # METHODS
    def submit_stretch(self):
        self.signal_submit_stretch.emit(self.ledit_stretch.text())
        self.close()

    def start(self, last_stretch):
        self.ledit_stretch.setText(last_stretch)
        self.show()
        