# %%
from curses.panel import bottom_panel
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import cm
import matplotlib as mpl
import skimage.color as skc
import skimage.io as skio

# %%
def centre_crop(img:np.ndarray, scale:float = 0.78) -> np.ndarray:
    assert 0.5 < scale and scale <= 1
    h, w = img.shape
    return img[round(h*(1-scale)):round(h*scale), round(w*(1-scale)):round(w*scale)]


# %%
# Wheel_T
path_t = '../data/wheel_T7.png'
fg = plt.figure(figsize=(5,5))
ax = fg.add_axes([0.1,0.1,0.8,0.8], projection='polar')

norm = mpl.colors.Normalize(0.0, 2*np.pi)

# Plot the colorbar onto the polar axis
# note - use orientation horizontal so that the gradient goes around
# the wheel rather than centre out
quant_steps = 2056*3
hsv = cm.get_cmap('twilight', quant_steps)
cmap = mpl.colors.ListedColormap(hsv(np.tile(np.linspace(0,1,quant_steps),1)))
cb = mpl.colorbar.ColorbarBase(ax, cmap=cmap,
                                   norm=norm,
                                   orientation='horizontal')

# aesthetics - get rid of border and axis labels
cb.outline.set_visible(False)                                 
ax.set_axis_off()
plt.savefig(path_t)
# skio.imsave(path_t, skc.rgb2gray(skio.imread(path_t)[...,:-1]))
skio.imsave(path_t, centre_crop(skio.imread(path_t, as_gray=True)))

# %%
# Wheel_R
path_r = '../data/wheel_R7.png'

norm = mpl.colors.Normalize(0.0, 2*np.pi)
quant_steps = 2056*3

fg = plt.figure(figsize=(5,5))
ax1 = fg.add_axes([0.1,0.1,0.8,0.8], projection='polar')

# Plot the colorbar onto the polar axis
# note - use orientation horizontal so that the gradient goes around
# the wheel rather than centre out
cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cm.get_cmap('twilight',quant_steps),
                                   norm=norm,
                                   orientation='horizontal')

# aesthetics - get rid of border and axis labels                                   
cb1.outline.set_visible(False)                                 
ax1.set_axis_off()
ax1.set_theta_offset(np.deg2rad(5))


ax2 = fg.add_axes([0.1,0.1,0.8,0.8], projection='polar')

# Plot the colorbar onto the polar axis
# note - use orientation horizontal so that the gradient goes around
# the wheel rather than centre out
cb2 = mpl.colorbar.ColorbarBase(ax2, cmap=cm.get_cmap('twilight',quant_steps),
                                   norm=norm,
                                   orientation='horizontal')

# aesthetics - get rid of border and axis labels                                   
cb2.outline.set_visible(False)                                 
ax2.set_axis_off()
ax2.set_theta_offset(np.deg2rad(-5))
ax2.set_rlim([-0.7,1])
# plt.savefig('../data/wheels.png')
plt.savefig(path_r)

skio.imsave(path_r, centre_crop(skio.imread(path_r, as_gray=True)))

# %%
