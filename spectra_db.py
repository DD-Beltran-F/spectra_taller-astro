# IMPORTS
# PyQt
from PyQt5.QtWidgets import QApplication

# Frontend imports
from frontend.window_main import MainWindow
from frontend.window_stretch import StretchWindow
from frontend.window_scale import ScaleWindow
from frontend.window_addline import AddlineWindow
from frontend.window_saveprofile import SaveProfileWindow
from frontend.window_msgpopup import MSGPopUpWindow
from frontend.window_overwrite import OverwriteWindow
from frontend.window_loadprofile import LoadProfileWindow
from frontend.window_lines import LinesWindow
from frontend.window_hdulist import HDUListWindow

# Backend imports
from backend.logic_main import MainLogic
from backend.logic_saveprofile import SaveProfileLogic
from backend.logic_scale import ScaleLogic


class SpectraDB(QApplication):

	def __init__(self, argv):
		super().__init__(argv)

		# Frontend instances
		self.window_main = MainWindow()
		self.window_stretch = StretchWindow()
		self.window_scale = ScaleWindow()
		self.window_addline = AddlineWindow()
		self.window_saveprofile = SaveProfileWindow()
		self.window_msgpopup = MSGPopUpWindow()
		self.window_overwrite = OverwriteWindow()
		self.window_loadprofile = LoadProfileWindow()
		self.window_lines = LinesWindow()
		self.window_hdulist = HDUListWindow()

		# Backend instances
		self.logic_main = MainLogic()
		self.logic_saveprofile = SaveProfileLogic()
		self.logic_scale = ScaleLogic()

	    # Run connections
		self.connect_main()
		self.connect_stretch()
		self.connect_addline()
		self.connect_saveprofile()
		self.connect_loadprofile()
		self.connect_scale()

	# Conections
	def connect_main(self):
		self.window_main.signal_create_profiles_dir.connect(self.logic_main.create_profiles_dir)

		#self.window_main.signal_load_hdulist.connect(self.window_hdulist.start)
		self.window_main.signal_load_fitfile.connect(self.logic_main.read_fit)
		self.logic_main.signal_fit_hdulist.connect(self.window_hdulist.start)
		self.window_hdulist.signal_read_hdu.connect(self.logic_main.read_fit_data)
		self.window_hdulist.signal_cancel.connect(self.window_main.search_file_canceled)

		self.window_main.signal_load_image.connect(self.logic_main.read_fit_data)
		self.logic_main.signal_fit_data.connect(self.window_main.plot_image)

		self.window_main.signal_update_spectrum.connect(self.logic_main.calculate_spectrum_data)
		self.logic_main.signal_update_spectrum.connect(self.window_main.spectrum_update)

		self.window_main.signal_line_list.connect(self.logic_main.get_line_list)
		self.logic_main.signal_line_list.connect(self.window_main.plot_line_list)

		self.window_main.signal_open_stretch_w.connect(self.window_stretch.start)

		self.window_main.signal_open_scale_w.connect(self.window_scale.start)

		self.window_main.signal_open_addline_w.connect(self.window_addline.start)

		self.window_main.signal_open_save_w.connect(self.window_saveprofile.start)

		self.window_main.signal_open_load_w.connect(self.window_loadprofile.start)

		self.window_main.signal_open_lines_w.connect(self.window_lines.start)
		self.window_lines.signal_plot_line.connect(self.window_main.plot_slct_line)

		self.logic_main.signal_readig_fit_error.connect(self.window_main.reading_fit_error)

		self.window_main.signal_msg.connect(self.window_msgpopup.popup)
		self.logic_main.signal_msg.connect(self.window_msgpopup.popup)

	def connect_stretch(self):
		self.window_stretch.signal_submit_stretch.connect(self.logic_main.validate_stretch)
		self.logic_main.signal_update_stretch.connect(self.window_main.stretch_changed)

	def connect_addline(self):
		self.window_addline.signal_submit_line.connect(self.logic_main.validate_line_name)
		self.logic_main.signal_ln_verification.connect(self.window_addline.ln_validation)

		self.window_addline.signal_discard_line.connect(self.window_main.discard_fit_line)
		self.window_addline.signal_add_line.connect(self.window_main.add_fit_line)

	def connect_saveprofile(self):
		self.window_saveprofile.signal_submit_file.connect(self.logic_saveprofile.\
			                                                                     validate_file_name)
		self.logic_saveprofile.signal_fn_verification.connect(self.window_saveprofile.fn_validation)

		self.window_saveprofile.signal_check_overwrite.connect(self.logic_saveprofile.\
			                                                                        check_overwrite)
		self.logic_saveprofile.signal_will_overwrite.connect(self.window_saveprofile.\
			                                                                       overwrite_result)

		self.window_saveprofile.signal_show_overwrite_w.connect(self.window_overwrite.popup)
		self.window_overwrite.signal_overwrite.connect(self.window_saveprofile.overwrite)

		self.window_saveprofile.signal_save_file.connect(self.window_main.save_profile)

		self.window_saveprofile.signal_save_file_canceled.connect(self.window_main.enable_widgets)

	def connect_loadprofile(self):
		self.window_loadprofile.signal_load_profile.connect(self.window_main.load_profile)

		self.window_loadprofile.signal_msg.connect(self.window_msgpopup.popup)

	def connect_scale(self):
		self.window_scale.signal_load_lamp.connect(self.logic_scale.read_lamp_fit_data)
		self.logic_scale.signal_lamp_spectrum.connect(self.window_scale.plot_lamp_spectrum)

		self.window_scale.signal_load_lamp_cal.connect(self.logic_scale.read_lamp_txt_data)
		self.logic_scale.signal_lamp_cal_spectrum.connect(self.window_scale.plot_lamp_cal_spectrum)

		self.window_scale.signal_calculate_fit.connect(self.logic_scale.calculate_curve_fit)
		self.logic_scale.signal_curve_fit.connect(self.window_scale.plot_fit)

		self.window_scale.signal_new_scale.connect(self.window_main.new_scale)

		self.window_scale.signal_msg.connect(self.window_msgpopup.popup)
		self.logic_scale.signal_msg.connect(self.window_msgpopup.popup)



	# Start program
	def start(self):
		self.window_main.showMaximized()
		self.window_main.start()
