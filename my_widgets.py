# IMPORTS
# Maths
import numpy as np

# Matplotlib
from matplotlib import pyplot as plt
from matplotlib.widgets import Cursor
from matplotlib.transforms import Bbox

# Local imports
import parameters as p


'''
WIDGETS

SpectrumLines: Manages the spectral lines added by the user in the Spectrum figure.

FittingLines: Manages the spectral lines of the Scale window for calibration (polynomial fit).

LineList: Manage the spectral lines from the Linetools database to display them in the Spectrum
          figure.

ImageCursor: Cursor widget for the Image figure in Main window. Inherit from matplotlib cursor.

SpectrumCursor: Cursor widget for the Image figure in Main window. Inherit from matplotlib cursor.
                Also used for the calibration spectrum figures in the Scale window.
'''

class SpectrumLines():
    def __init__(self, remove_threshold=5):
        self.lines = []
        self.labels = []
        self.xdata = []
        self.ydata = []
        self.remove_threshold = remove_threshold
        self.picking = True
        self.adjusting = False
        self.fitting = False
        self.line_guess = None
        self.line_guess_width = None
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None

    def guess(self, line_guess=None, line_guess_width=None):
        self.line_guess = line_guess
        self.line_guess_width = line_guess_width

    def gaussian_fit(self, gaussian=None, gauss_max=None, fit_max=None):
        self.gaussian = gaussian
        self.gauss_max = gauss_max
        self.fit_max = fit_max

    def add_line(self, line, label, x, y):
        self.lines.append(line)
        self.labels.append(label)
        self.xdata.append(x)
        self.ydata.append(y)
        if self.gaussian:
            self.gaussian.remove()
        if self.gauss_max:
            self.gauss_max.remove()
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None
        self.fitting = False
        self.picking = True

    def remove_line(self, x):
        remove_index = 0
        remove = False
        for i in range(len(self.lines)):
            if abs(self.xdata[i] - x) <= self.remove_threshold:
                remove_index = i
                remove = True
        if remove:
            self.lines[remove_index].remove()
            self.labels[remove_index].remove()
            self.lines.pop(remove_index)
            self.labels.pop(remove_index)
            self.xdata.pop(remove_index)
            self.ydata.pop(remove_index)
 
    def discard_fit(self):
        if self.gaussian:
            self.gaussian.remove()
        if self.gauss_max:
            self.gauss_max.remove()
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None
        self.fitting = False
        self.picking = True

    def check_text_pos(self, limits=[], z_min=0, z_max=1):
        if self.labels != []:
            for label in self.labels:
                x,y = label.get_position()
                if limits == []:
                    valign = label.get_va()
                    if valign == 'bottom':
                        zlblpos = z_min+0.035*(abs(z_max-z_min))
                    elif valign == 'top':
                        zlblpos = z_max-0.035*(abs(z_max-z_min))
                    label.set_position((x, zlblpos))
                if limits != []:
                    if x >= limits[0] and x <= limits[1]:
                        label.set_visible(True)
                    elif x < limits[0] or x > limits[1]:
                        label.set_visible(False)

    def reset(self):
        if self.lines != [] and self.labels != []:
            for line, label in zip(self.lines,self.labels):
                line.remove()
                label.remove()
        if self.line_guess:
            self.line_guess.remove()
            self.line_guess = None
        if self.line_guess_width:
            self.line_guess_width[0].remove()
            self.line_guess_width[1].remove()
            self.line_guess_width = None
        if self.gaussian:
            self.gaussian.remove()
            self.gaussian = None
        if self.gauss_max:
            self.gauss_max.remove()
            self.gauss_max = None
        self.lines = []
        self.labels = []
        self.xdata = []
        self.ydata = []
        self.picking = True
        self.adjusting = False
        self.fitting = False

class FittingLines():
    def __init__(self, remove_threshold=5):
        self.pxlines = []
        self.nmlines = []
        self.pxdata = []
        self.nmdata = []
        self.remove_threshold = remove_threshold
        self.picking = True
        self.adjusting = False
        self.fitting = False
        self.line_guess = None
        self.line_guess_width = None
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None

    def guess(self, line_guess=None, line_guess_width=None):
        self.line_guess = line_guess
        self.line_guess_width = line_guess_width

    def gaussian_fit(self, gaussian=None, gauss_max=None, fit_max=None):
        self.gaussian = gaussian
        self.gauss_max = gauss_max
        self.fit_max = fit_max


    def add_line(self, line, data, lamp_list):
        if lamp_list == 'px':
            self.pxlines.append(line)
            self.pxdata.append(data)
        elif lamp_list == 'nm':
            self.nmlines.append(line)
            self.nmdata.append(data)
        if self.gaussian:
            self.gaussian.remove()
        if self.gauss_max:
            self.gauss_max.remove()
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None
        self.fitting = False
        self.picking = True

    def remove_line(self, x, lamp_list):
        remove_index = 0
        remove = False
        if lamp_list == 'px':
            for i in range(len(self.pxlines)):
                if abs(self.pxdata[i] - x) <= self.remove_threshold:
                    remove_index = i
                    remove = True
        elif lamp_list == 'nm':
            for i in range(len(self.nmlines)):
                if abs(self.nmdata[i] - x) <= self.remove_threshold:
                    remove_index = i
                    remove = True
        if remove:
            try:
                self.pxlines[remove_index].remove()
                self.pxlines.pop(remove_index)
                self.pxdata.pop(remove_index)
            except:
                pass
            try:
                self.nmlines[remove_index].remove()
                self.nmlines.pop(remove_index)
                self.nmdata.pop(remove_index)
            except:
                pass
 
    def discard_fit(self):
        if self.gaussian:
            self.gaussian.remove()
        if self.gauss_max:
            self.gauss_max.remove()
        self.gaussian = None
        self.gauss_max = None
        self.fit_max = None
        self.fitting = False
        self.picking = True

    def reset(self):
        if self.pxlines != [] and self.nmlines != []:
            for pxline, nmline in zip(self.pxlines,self.nmlines):
                pxline.remove()
                nmline.remove()
        if self.line_guess:
            self.line_guess.remove()
            self.line_guess = None
        if self.line_guess_width:
            self.line_guess_width[0].remove()
            self.line_guess_width[1].remove()
            self.line_guess_width = None
        if self.gaussian:
            self.gaussian.remove()
            self.gaussian = None
        if self.gauss_max:
            self.gauss_max.remove()
            self.gauss_max = None
        self.pxlines = []
        self.nmlines = []
        self.pxdata = []
        self.nmdata = []
        self.picking = True
        self.adjusting = False
        self.fitting = False

class LineList():
    def __init__(self):
        self.lines = []
        self.labels = []

    def add_line(self, line, label):
        self.lines.append(line)
        self.labels.append(label)

    def clear_lines(self):
        if len(self.lines) != 0:
            for line,label in zip(self.lines,self.labels):
                line.remove()
                label.remove()
        self.lines = []
        self.labels = []

    def check_text_pos(self, limits=[], z_min=0, z_max=1):
        for label in self.labels:
            x,y = label.get_position()
            if limits == []:
                label.set_position((x, z_min + 0.035*(z_max-z_min)))
            if limits != []:
                if x >= limits[0] and x <= limits[1]:
                    label.set_visible(True)
                elif x < limits[0] or x > limits[1]:
                    label.set_visible(False)

class ImageCursor(Cursor):
    def __init__(self, numberformat="{:.2f}", offset=(5, 5), textprops=None, **cursorargs):
        if textprops is None:
            textprops = {}
        self.numberformat = numberformat
        self.offset = np.array(offset)
        super().__init__(**cursorargs)

        self.set_position(0, 0)
        self.text = self.ax.text(
            self.ax.get_xbound()[0],
            self.ax.get_ybound()[0],
            "0, 0",
            animated=bool(self.useblit),
            visible=False, **textprops)
        self.lastdrawnplotpoint = None

    # Detect when mouse move on the figure
    def onmove(self, event):
        # Copy cursor conditions (matplotlib cursor object)
        if self.ignore(event):
            self.lastdrawnplotpoint = None
            return
        if not self.canvas.widgetlock.available(self):
            self.lastdrawnplotpoint = None
            return
        # Hide and reset the text label if the mouse moves out of the axes
        if event.inaxes != self.ax:
            self.lastdrawnplotpoint = None
            self.text.set_visible(False)
            super().onmove(event)
            return

        # Create a new point in the cursor position
        plotpoint = None
        if event.xdata and event.ydata:
            plotpoint = self.set_position(event.xdata, event.ydata)
            if plotpoint:
                event.xdata = plotpoint[0]
                event.ydata = plotpoint[1]

        if plotpoint and plotpoint == self.lastdrawnplotpoint:
            return
        
        super().onmove(event)

        if not self.get_active() or not self.visible:
            return

        if plotpoint:
            temp = [0, event.ydata]
            temp = self.ax.transData.transform(temp)
            temp = temp + self.offset[0]
            temp = self.ax.transData.inverted().transform(temp)
            self.text.set_position(temp)
            self.text.set_text(self.numberformat.format(plotpoint[1]))
            self.text.set_visible(self.visible)
            self.needclear = True
            self.lastdrawnplotpoint = plotpoint
        else:
            self.text.set_visible(False)
        if self.useblit:
            self.ax.draw_artist(self.text)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()

    # Return the position for the text label (plotpoint)
    def set_position(self, xpos, ypos):
        lim = self.ax.get_ylim()
        xdata = [0 for i in range(0,int(lim[-1]))]
        ydata = [i for i in range(0,int(lim[-1]))]
        if ypos and lim[0] <= ypos <= lim[-1]:
            index = np.searchsorted(ydata, ypos)
            if index < 0 or index >= len(ydata):
                return None
            return (xdata[index], ydata[index])
        return None

    # Clear the widget
    def clear(self, event):
        super().clear(event)
        if self.ignore(event):
            return
        self.text.set_visible(False)

    # Update the widget
    def _update(self):
        if self.useblit:
            super()._update()

class SpectrumCursor(Cursor):
    def __init__(self, line, numberformat="{:.2f}", offset=[(5, 5),(5, 5)], params=[1,0],
                 show_axis='both', textprops=None, admit_scale=True, **cursorargs):
        if textprops is None:
            textprops = {}
        self.line = line
        self.numberformat = numberformat
        self.offset = np.array((offset[0],offset[1]))
        self.show_axis = show_axis
        self.admit_scale = admit_scale
        self.params = params
        super().__init__(**cursorargs)

        self.set_position(self.line.get_xdata()[0], self.line.get_ydata()[0])
        if self.show_axis == 'x' or self.show_axis == 'both':
            self.text_x = self.ax.text(
                self.ax.get_xbound()[0],
                self.ax.get_ybound()[0],
                "0, 0",
                animated=bool(self.useblit),
                visible=False, **textprops[0])
        if self.show_axis == 'y' or self.show_axis == 'both':
            self.text_y = self.ax.text(
                self.ax.get_xbound()[0],
                self.ax.get_ybound()[0],
                "0, 0",
                animated=bool(self.useblit),
                visible=False, **textprops[1])
        self.lastdrawnplotpoint = None

    
    # Scale from px to nm or nm to px
    def fit_1(self, x, a, b):
        return a*x + b

    def fit_2(self, x, a, b, c):
        return a*(x**2) + b*x + c

    def fit_3(self, x, a, b, c, d):
        return a *(x**3) + b*(x**2) + c*x + d

    def fit_4(self, x, a, b, c, d, e):
        return a*(x**4) + b *(x**3) + c*(x**2) + d*x + e

    def scale_px_to_nm(self, px):
        if self.params:
            if len(self.params) == 2:
                return self.fit_1(px, *self.params)
            if len(self.params) == 3:
                return self.fit_2(px, *self.params)
            if len(self.params) == 4:
                return self.fit_3(px, *self.params)
            if len(self.params) == 5:
                return self.fit_4(px, *self.params)

    # Detect when mouse move on the figure
    def onmove(self, event):
        # Copy cursor conditions (matplotlib cursor object)
        if self.ignore(event):
            self.lastdrawnplotpoint = None
            return
        if not self.canvas.widgetlock.available(self):
            self.lastdrawnplotpoint = None
            return
        # Hide and reset the text label if the mouse moves out of the axes
        if event.inaxes != self.ax:
            self.lastdrawnplotpoint = None
            if self.show_axis == 'x' or self.show_axis == 'both':
                self.text_x.set_visible(False)
            if self.show_axis == 'y' or self.show_axis == 'both':
                self.text_y.set_visible(False)
            super().onmove(event)
            return

        # Create a new point in the cursor position
        plotpoint = None
        if event.xdata and event.ydata:
            plotpoint = self.set_position(event.xdata, event.ydata)
            if plotpoint:
                event.xdata = plotpoint[0]
                event.ydata = plotpoint[1]

        if plotpoint and plotpoint == self.lastdrawnplotpoint:
            return

        super().onmove(event)

        if not self.get_active() or not self.visible:
            return

        if plotpoint:
            zmin,zmax = self.ax.get_ylim()
            temp_x = [event.xdata, zmin]
            temp_x = self.ax.transData.transform(temp_x)
            temp_x = temp_x + self.offset[0]
            temp_x = self.ax.transData.inverted().transform(temp_x)
            temp_y = [event.xdata, event.ydata]
            temp_y = self.ax.transData.transform(temp_y)
            temp_y = temp_y + self.offset[1]
            temp_y = self.ax.transData.inverted().transform(temp_y)
            self.text_x.set_position(temp_x)
            xtext_val = plotpoint[0]
            if self.admit_scale and 'Nanometers' in self.ax.get_xlabel():
                xtext_val = self.scale_px_to_nm(xtext_val)
            self.text_x.set_text(self.numberformat.format(xtext_val))
            self.text_x.set_visible(self.visible)
            self.text_y.set_position(temp_y)
            self.text_y.set_text(self.numberformat.format(plotpoint[1]))
            self.text_y.set_visible(self.visible)
            self.needclear = True
            self.lastdrawnplotpoint = plotpoint
        else:
            self.text_x.set_visible(False)
            self.text_y.set_visible(False)
        if self.useblit:
            self.ax.draw_artist(self.text_x)
            self.ax.draw_artist(self.text_y)
            self.canvas.blit(self.ax.bbox)
        else:
            self.canvas.draw_idle()

    # Return the position for the text label (plotpoint)
    def set_position(self, xpos, ypos):
        # Spectrum data (line)
        xdata = self.line.get_xdata()
        ydata = self.line.get_ydata()
        lim = self.ax.get_xlim()
        # Check the point doesnt get out the figure limits
        if xpos and lim[0] <= xpos <= lim[-1]:
            index = np.searchsorted(xdata, xpos)
            if index < 0 or index >= len(xdata):
                return None
            # Return the points found on the spectrum
            return (xdata[index], ydata[index])
        return None

    # Clear the widget
    def clear(self, event):
        super().clear(event)
        if self.ignore(event):
            return
        self.text_x.set_visible(False)
        self.text_y.set_visible(False)

    # Update the widget
    def _update(self):
        if self.useblit:
            super()._update()