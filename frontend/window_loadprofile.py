# IMPORTS
import sys
import json
import datetime

# PyQt
from PyQt5.QtWidgets import (QMainWindow, QLabel, QPushButton, QFileDialog)
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

# Local imports
import parameters as p

class LoadProfileWindow(QMainWindow):

    # SIGNALS
    signal_load_profile = pyqtSignal(dict)
    signal_msg = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()

        uic.loadUi(p.PATH_UI_WINDOW_LOADPROFILE, self)

        # WIDGETS
        # Labels
        self.lbl_profilename = self.findChild(QLabel,'lbl_profilename')
        self.lbl_image = self.findChild(QLabel,'lbl_image')
        self.lbl_imagefile = self.findChild(QLabel,'lbl_imagefile')
        self.lbl_imagesize = self.findChild(QLabel,'lbl_imagesize')
        self.lbl_spectrum_proyection = self.findChild(QLabel,'lbl_spectrum_proyection')
        self.lbl_spectrum_width = self.findChild(QLabel,'lbl_spectrum_width')
        self.lbl_spectrum_lines = self.findChild(QLabel,'lbl_spectrum_lines')
        self.lbl_spectrum_scale = self.findChild(QLabel,'lbl_spectrum_scale')
        # Buttons
        self.btn_open = self.findChild(QPushButton,'btn_open')
        self.btn_load = self.findChild(QPushButton,'btn_load')
        self.btn_cancel = self.findChild(QPushButton,'btn_cancel')

        # Conections
        self.btn_open.clicked.connect(self.open_profile)
        self.btn_load.clicked.connect(self.load_profile)
        self.btn_cancel.clicked.connect(self.cancel)

        self.profile_data = None


    def open_profile(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Open Profile', 'profiles',
                                                    'Text files (*.txt)')
        if path:
            image_path = path[:-4] + '.png'
            profile_file = path.split('/')[-1]
            profile_name = path.split('/')[-1][:-4]
            try:
                with open(path, 'r') as file:
                    self.profile_data = json.load(file)
                    self.show_profile_data(profile_name, image_path)
            except Exception as e:
                msg = f'Invalid format.\nMaybe "{profile_file}" is not a spectrum profile!'
                self.signal_msg.emit(msg)
                print(datetime.datetime.now(),e)

    def load_profile(self):
        if self.profile_data is not None:
            self.signal_load_profile.emit(self.profile_data)
            self.close()

    def cancel(self):
        self.close()

    def show_profile_data(self, profile_name, image_path):
        self.btn_load.setEnabled(True)
        self.lbl_image.setText('')
        image_pixmap = QPixmap(image_path)
        scaled_image_pixmap = image_pixmap.scaled(self.lbl_image.size(), Qt.KeepAspectRatio)
        self.lbl_image.setPixmap(scaled_image_pixmap)
        self.lbl_image.setObjectName(profile_name)

        self.lbl_profilename.setText(profile_name)
        self.lbl_imagefile.setText(self.profile_data['image_file'])
        image_size = self.profile_data['image_size']
        self.lbl_imagesize.setText(f'{image_size[0]} x {image_size[1]} (px)')
        self.lbl_spectrum_proyection.setText(self.profile_data['proyection'])
        self.lbl_spectrum_width.setText(self.profile_data['width'])
        lines_cant = str(len(self.profile_data['lines_pos']))
        self.lbl_spectrum_lines.setText(lines_cant)
        params = self.profile_data['scale_params']
        if params is not None:
            self.lbl_spectrum_scale.setText('Yes')
        elif params is None:
            self.lbl_spectrum_scale.setText('No')

    def start(self):
        self.lbl_image.setText('Open a profile')
        self.btn_load.setEnabled(False)
        self.lbl_profilename.setText('')
        self.lbl_imagefile.setText('')
        self.lbl_imagesize.setText('')
        self.lbl_spectrum_proyection.setText('')
        self.lbl_spectrum_width.setText('')
        self.lbl_spectrum_lines.setText('')
        self.lbl_spectrum_scale.setText('')
        self.show()
        