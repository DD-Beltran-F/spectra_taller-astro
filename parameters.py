# IMPORTS
import os

# PATHS
PATH_UI_WINDOW_MAIN = os.path.join('frontend', 'window_main_qt.ui')
PATH_UI_WINDOW_STRETCH = os.path.join('frontend', 'window_stretch_qt.ui')
PATH_UI_WINDOW_SCALE = os.path.join('frontend', 'window_scale_qt.ui')
PATH_UI_WINDOW_SCALE2 = os.path.join('frontend', 'window_scale2_qt.ui')
PATH_UI_WINDOW_ADDLINE = os.path.join('frontend', 'window_addline_qt.ui')
PATH_UI_WINDOW_SAVEPROFILE = os.path.join('frontend', 'window_saveprofile_qt.ui')
PATH_UI_WINDOW_MSGPOPUP = os.path.join('frontend', 'window_msgpopup_qt.ui')
PATH_UI_WINDOW_OVERWRITE = os.path.join('frontend', 'window_overwrite_qt.ui')
PATH_UI_WINDOW_LOADPROFILE = os.path.join('frontend', 'window_loadprofile_qt.ui')
PATH_UI_WINDOW_LINES = os.path.join('frontend', 'window_lines_qt.ui')
PATH_UI_WINDOW_HDULIST = os.path.join('frontend', 'window_hdulist_qt.ui')
PATH_SPECTRA_TEST = os.path.join('spectra', 'Alrescha_40s.FIT')
PATH_LINE_LIST = os.path.join('backend', 'line_list_linetools', 'llist_v1.3.ascii')
PATH_LINE_LIST_FULL = os.path.join('backend', 'line_list_linetools', 'linelist.ascii')

# IMAGE PARAMETERS
IMAGE_LINES_LW = 1                       # Linewidth for cursor lines
IMAGE_FS = 20                            # Fontsize
IMAGE_FN = 'Times New Roman'             # Fontname

# SPECTRA PARAMETERS
ZOOM_FACTOR = 0.1                        # Fraction of the image cropped/added when zooming (0 TO 1)
ZOOM_IN_MAX = 20                         # Limit for zoom in (in terms of axis units)
TRANSLATION_FACTOR = 0.05                # Faction of the image translated (0 TO 1)
SPECTRA_LW = 1                           # Linewidth for scale figures
SPECTRA_LINES_LW = 1                     # Linewidth for spectral lines
SPECTRA_FS = 20                          # Fontsize
SPECTRA_FN = 'Times New Roman'           # Fontname

# SPECTRAL LINES
BALMER_LIST = ['Halpha','Hbeta','Hgamma','Hdelta','Hepsilon']           # Balmer serie
PASCHEN_LIST = ['Paalpha','Pabeta','Pagamma','Padelta','Paepsilon']     # Paschen serie
BRACKETT_LIST = ['Bralpha','Brbeta','Brgamma','Brdelta']                # Brackket serie
GREEK_CHAR_UTF8 = ['α','β','γ','δ','ε']                                 # Greek letters (UTF-8)
GREEK_CHAR_ASCII= ['alpha','beta','gamma','delta','epsilon']            # Greek letters (when ASCII)

LIST_KEYS = {                  # List of keys for spectral lines clasification
              'Galaxy':'fgE',  # Lines typically identified in galaxy spectra
              'HI':'fHI',      # HI Lyman series
              'H2':'fH2',      # H2 (Lyman-Werner)
              'CO':'fCO',      # CO UV band-heads
              'ISM':'fISM',    # “All” Interstellar Medium lines (can be overwhelming!)
              'Strong':'fSI',  # Strong ISM lines (most common absorption line transitions observed)
              'EUV':'fEUV',    # Extreme UV lines
              'AGN':'fAGN'     # Lines tipically identified in Active Galactic Nucleus spectra
             }


# SCALE PARAMETERS
PREVIEW = 0.5                            # Spectra preview factor for some scale figures 
SCALE_ZOOM_FACTOR = 0.1                  # Fraction of the image cropped/added when zooming (0 TO 1)
SCALE_ZOOM_IN_MAX = 20                   # Limit for zoom in (in terms of axis units)
SCALE_TRANSLATION_FACTOR = 0.05          # Faction of the image translated (0 TO 1)
SCALE_LW = 1                             # Linewidth for scale figures
SCALE_LINES_LW = 1                       # Linewidth for spectral lines
SCALE_FS = 12                            # Fontsize
SCALE_FN = 'Times New Roman'             # Fontname
SCALE_DOT_S = 20                         # Size for dots in scale figures (scatter)

# EXTRA
GRADES_PARAMS = {                                                                        # Poly. fit
                 '1':{'minpoints':2,'fit':'y = ax + b','nparams':2},                     # n = 1
                 '2':{'minpoints':3,'fit':'y = ax^2 + bx + c','nparams':3},              # n = 2
                 '3':{'minpoints':4,'fit':'y = ax^3 + bx^2 + cx + d','nparams':4},       # n = 3
                 '4':{'minpoints':5,'fit':'y = ax^4 + bx^3 + cx^2 + dx + e','nparams':5} # n = 4
                }
ALLOWED_CHAR_LINENAME = r'^[a-zA-Z0-9\s.Α-Ωα-ω\[\]*]*$'   # Allowed characters for line names
ALLOWED_CHAR_FILENAME = r'^[a-zA-Z0-9\s_]+$'              # Allowed characters for profile file name
PNG_FIGURE_MARGIN = 0.025                                 # Margin when extend an image bbox