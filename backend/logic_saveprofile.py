# IMPORTS
import os
import re

# PyQt
from PyQt5.QtCore import QObject, pyqtSignal

# Local imports
import parameters as p

class SaveProfileLogic(QObject):

    # SIGNALS
    signal_fn_verification = pyqtSignal(bool)
    signal_will_overwrite = pyqtSignal(bool)

    def __init__(self):

        self.allowed_char = re.compile(p.ALLOWED_CHAR_FILENAME)

        super().__init__()

    # METHODS
    def validate_file_name(self, name):
        coincidence = self.allowed_char.search(name)
        self.signal_fn_verification.emit(bool(coincidence))

    def check_overwrite(self, name):
        files = os.listdir('profiles')
        will_overwrite = False
        for file in files:
            if name+'.txt' in file:
                will_overwrite = True
        self.signal_will_overwrite.emit(will_overwrite)



