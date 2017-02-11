# This Python script will take the I-V data from the partsim simulation and
# create the I-V plot from it.
#
import numpy as np
import matplotlib.pyplot as plt
import csv
#
f=open("Forward_biased_diode.csv")
data = csv.reader(f)
headers = data.next()
units = data.next()
dat = np.array([ [float(z) for z in x] for x in data ]) # put the data in dat as floats.
x_ar  = dat[:,0]   # select the first column
y1_ar = 1000*dat[:,1]   # select the second column
y2_ar = dat[:,2]   # select the third column

plt.plot(y2_ar,y1_ar)
ax = plt.gca()
ax.set_xlim(-0.2,1.2)  # Zoom in on the interesting part of the curve.
plt.title("Forward Biased Small Signal Diode: 1N4148")
plt.xlabel("V [Volts]")
plt.ylabel("I [mA]")
plt.show()
