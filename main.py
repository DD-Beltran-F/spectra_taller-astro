# IMPORTS
import sys
from spectra_db import SpectraDB

# Start application
if __name__ == '__main__':
	def hook(type_, value, traceback):
		print(type_)
		print(traceback)
	sys.__excepthook__ = hook

	app = SpectraDB(sys.argv)
	app.start()
	sys.exit(app.exec())
	