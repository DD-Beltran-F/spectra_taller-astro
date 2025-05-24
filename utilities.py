# Imports
import numpy as np
from matplotlib import pyplot as plt
from matplotlib.transforms import Bbox

def gauss(x, a, b, mu, sigma):
    return a * np.exp(-((x - mu)**2)/(2 * sigma**2)) + b

def full_extent(ax, pad=0.0):
    ax.figure.canvas.draw()
    items = ax.get_xticklabels() + ax.get_yticklabels() 
    items += [ax, ax.title, ax.xaxis.label, ax.yaxis.label]
    bbox = Bbox.union([item.get_window_extent() for item in items])
    return bbox.expanded(1.0 + pad, 1.0 + pad)