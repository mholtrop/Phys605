#!/usr/bin/env python3

import pandas;
import matplotlib.pyplot as plt;

#
# We use Pandas to read the Excel output from Partsim.
#
diode_data = pandas.read_excel("Diode_1N4148.xls");
zener_data = pandas.read_excel("Diode_1N5226B_reverse.xls");
# print(diode_data.head())
# Uncomment the line above to discover the names of the
# columns from the header, and inspect the first few lines.
# The first line are the keys, which you need to select the colum.
# Typing them incorrectly will give you a "key error".
# You see the second line is the units, so we will need to skip that.

# Make the plot using pyplot.
fig=plt.figure(figsize=(9,7)) # This does not show anything yet, it create a 10"x8" figure space
axes = fig.add_axes([0.1,0.1,0.85,0.8]) # This creates the axes to plot on, with some margin space.
# The numbers are the amount of white space to leave for the border. [x_low,y_low,x_width,y_width]
# The choice made here [0.1,0.1,0.85,0.8] leaves enough space for good effect.
# Set to [0,0,1,1] for no space at all.
axes.plot(diode_data['m2'][1:],1000*diode_data['i(m1)'][1:],label="1N4148")
# Make the plot on the axes, give it a label for the legend.
# The [1:] means to skip the first row of the column.
# We muliply y by 1000 to get mA.
axes.plot(zener_data['m2'][1:],1000*zener_data['i(m1)'][1:],label="1N5226B")

axes.set_title('I-V curve for diode',fontsize=24) # Give the plot a title, extra large.
axes.set_xlabel('V',fontsize=16)                  # Set a label of the x-axis
axes.set_ylabel('I[mA]',fontsize=16)              # and label for y-axis
axes.legend(fontsize=18)                          # Do a legend, in size 18
axes.set_xlim(-4,4)                             # Plot x from -4 to 4, even if the data does not.
plt.grid()
plt.savefig("diode_iv_plot.pdf")
plt.show()                                        # show the result on screen.
