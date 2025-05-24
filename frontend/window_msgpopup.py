# IMPORTS
import sys

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QLabel)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal

# Local imports
import parameters as p


class MSGPopUpWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_MSGPOPUP, self)

        # WIDGETS
        # Label
        self.lbl_msg = self.findChild(QLabel,'lbl_msg')

    # METHODS
    def popup(self, msg):
        self.lbl_msg.setText(msg)
        self.show()
        