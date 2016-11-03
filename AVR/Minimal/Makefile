#
# Usage:
#
# make
# make disasm 
# make stats 
# make hex
# make writeflash
# make gdbinit
# make clean
#
#
# Specs come from a SPEC file, also used for library.
#
include ../Makefile_specs.mk

DEPDIR = depdir

# Define the program name

PROGNAME=Minimal

# Source files
# List C/C++/Assembly source files:
# (list all files to compile, e.g. 'a.c b.cpp as.S'):
# Use .cc, .cpp or .C suffix for C++ files.
# Use .c              suffix for C   files.
# Use .S  (NOT .s !!!) for assembly source code files.

SOURCES=main.cpp


#
# Include all the common rules for AVR.
#
include ../Makefile_common.mk
