#
# Here is a more complicated example that loads a .csv file and
# then creates a plot from the x,y data in it.
# The data file is the saved curve from partsim.com of the low pass filter.
# It was saved as xls file and then opened in Excel and exported to csv
#
# First import the csv parser, the numeric tools and plotting tools
import csv
import numpy as np   # This gives numpy the shorthand np
import matplotlib.pyplot as plt
#
# Open the file
#
f = open("low_pass_filter.csv")
#
# Pass the file to the csv parser
#
data = csv.reader(f)
headers = data.next()
units = data.next()
#
# Here is a "wicked" way in Python that does quicker what the
# the more verbose code does below. It is "Matlab" like.
# dat = np.array([ [float(z) for z in x] for x in data ]) # put the data in dat as floats.
# x_ar  = dat[:,0]   # select the first column
# y1_ar = dat[:,1]   # select the second column
# y2_ar = dat[:,2]   # select the third column

x_ar = [] # Create a new list (array) called dat to hold the data.
y1_ar = []
y2_ar = []
for (x,y1,y2) in data:  # Unpack the csv data into x,y1,y2 variables.
    x_ar.append( float(x))
    y1_ar.append(float(y1))
    y2_ar.append(float(y2)) # Convert the variable from string to float and add to dat

#
# Now plot the data. plt.plot returns a tuple (plot, )
#
(p1,) = plt.plot(x_ar,y1_ar,color='green',label=headers[1])
(p2,) = plt.plot(x_ar,y2_ar,color='blue',label=headers[2])
plt.legend(handles=[p1,p2])        # make sure the legend is drawn
plt.xscale('log')                  # plot with a log x axis
plt.yscale('log')
plt.grid(True)                     # and a grid.
plt.title('Low pass filter')
plt.xlabel('F[Hz]',position=(0.9,1))
plt.ylabel('Amplitude [Volt]')
plt.show()                         # show the plot.
