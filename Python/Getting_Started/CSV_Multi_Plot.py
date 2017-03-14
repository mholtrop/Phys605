#!/usr/bin/env python
#
# This example expands on the CSV_Plot.py. It will open all the
# csv files that are given on the command line, and plot the data found
# in the files in a single plot.
#
import sys
import argparse
#
import os.path as path
import csv
import numpy as np   # This gives numpy the shorthand np
import matplotlib.pyplot as plt
#
#

def main(argv=None):
    ''' This is the main program that runs, but it is also callable from the python
    command line if you import this file into python. '''

    # Parse the connand line arguments.
    if argv is None:
        argv = sys.argv[1:]  # First item in sys.argv is progname

    parser = argparse.ArgumentParser(description='A program to plot CSV files from the Analog Discovery.')
    parser.add_argument('-b','--bode',action='store_true',help='Make bode plots, log x')
    parser.add_argument('-s','--signal',action='store_true',help='Make signal plots, lin x')

    parser.add_argument('files',type=str, nargs='+', help='input files')

    args = parser.parse_args(argv)

    if args.bode == False and args.signal == False:
        print "Please supply either --bode or --signal option"
        return

    p_data = []
    for f in args.files:
        dirname,filename = path.split(f)
        basename, ext    = path.splitext(filename)
        if ext.lower() != '.csv':
            print "File {} does not appear to be a CSV file. Skipped.".format(filename)
            continue

        infile = open(f)
        #
        # Pass the file to the csv parser
        #
        data = csv.reader(infile)
        line = data.next()
        while len(line) == 0 or line[0][0]=='#':   # Skip comments and empty lines.
            line = data.next()
        headers = data.next()

        dat = np.array([ [float(z) for z in x] for x in data ]) # put the data in dat as floats.
        p_data.append( (basename,dat))

    #
    # Now plot the data. plt.plot returns a tuple (plot, )
    #
    plots = []
    for name,dat in p_data:
        x_ar = [float(x[0]) for x in dat ]
        if args.bode:
            y_ar = [float(x[2]) for x in dat ]
        if args.signal:
            y_ar = [float(x[1]) for x in dat ]

        lab = name.split('_')[2]
        (p1,) = plt.plot(x_ar,y_ar,label=lab)
        plots.append(p1)

    plt.legend(handles=plots)        # make sure the legend is drawn
                     # plot with a log x axis
    #    plt.yscale('log')
    plt.grid(True)                     # and a grid.
    if args.bode:
        plt.title('Bode Plot of Transistor Amplifier')
        plt.xlabel('F[Hz]',position=(0.9,1))
        plt.ylabel('Magnitude [dB]')
        plt.xscale('log')

    if args.signal:
        plt.title('Output Signal of Transistor Amplifier')
        plt.xlabel('Time[S]',position=(0.9,1))
        plt.ylabel('Signal [V]')

    plt.show()                         # show the plot.

if __name__ == "__main__":  # This makes sure that main() is called when you
                            # run the script from the command line.
    sys.exit(main())
