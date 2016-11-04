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
# Include this file in the Makefile of your project at the BOTTOM of the Makefile.
#
# Specs come from SPEC file (Makefile_spec.mk), which is also used for compiling the libraries.
# You include the SPEC file at the TOP of your Makefile.
#
AVR_HOME ?= ${HOME}/code/AVR

DEPDIR = depdir

# additional includes (e.g. -I/path/to/mydir)
INC= -I${AVR_HOME}/include -I${AVR_HOME}/include/variants/$(BOARD_TYPE) $(EXTRA_INCLUDES)

# libraries to link in (e.g. -lmylib)
LIBS= -Wl,-u,vfprintf -lprintf_flt -lm -lc -L${AVR_HOME}/lib/$(SYSTEM_TYPE) -larduino  -larduinoutil $(EXTRA_LIBS)
#LIBS= -Wl,-u,vfprintf -lprintf_flt -lm -lc 

##### ADDED Flags ####

CFLAGS   += -I. $(INC) 
CXXFLAGS += -I. $(INC)
ASMFLAGS += -I. $(INC)

# HEXFORMAT -- format for .hex file output
HEXFORMAT=ihex

##### automatic target names ####
TARGET=$(PROGNAME).out
DUMPTARGET=$(PROGNAME).s

HEXROMTARGET=$(PROGNAME).hex 
HEXTARGET=$(HEXROMTARGET) $(PROGNAME).ee.hex
GDBINITFILE=gdbinit-$(PROGNAME)

# Define all object files.

# Start by splitting source files by type
#  C++
CPPFILES=$(filter %.cpp, $(SOURCES))
CXXFILES +=$(filter %.cxx, $(SOURCES))
CCFILES=$(filter %.cc, $(SOURCES))
#  C
CFILES=$(filter %.c, $(SOURCES))
#  Assembly
ASMFILES=$(filter %.S, $(SOURCES))


# List all object files we need to create
OBJDEPS=$(CFILES:.c=.o)    \
	$(CXXFILES:.cxx=.o)\
	$(CPPFILES:.cpp=.o)\
	$(CCFILES:.cc=.o)  \
	$(ASMFILES:.S=.o)

# Define all lst files.
LST=$(filter %.lst, $(OBJDEPS:.o=.lst))

# All the possible generated assembly 
# files (.s files)
GENASMFILES=$(filter %.s, $(OBJDEPS:.o=.s)) 

####################################################################################
# Program settings
CC = avr-gcc
CXX = avr-g++
OBJCOPY = avr-objcopy
OBJDUMP = avr-objdump
AR  = avr-ar
SIZE = avr-size
NM = avr-nm
AVRDUDE = avrdude
REMOVE = rm -f
MV = mv -f

#
# Details of the compiler process. 
# Probably no need to change any of this.
#

ifndef OPTLEVEL
OPTLEVEL=s
endif

ifdef DEBUG
OPTIMIZE = -g
else
OPTIMIZE = -O$(OPTLEVEL)
endif

# compiler
CFLAGS +=$(OPTIMIZE) -mmcu=$(MCU) -DF_CPU=$(F_CPU) \
	-fpack-struct -fshort-enums             \
	-funsigned-bitfields -funsigned-char    \
	-Wall -Wstrict-prototypes               \
#	-Wa,-ahlms=$(firstword                  \
#	$(filter %.lst, $(<:.c=.lst)))

# c++ specific flags
CXXFLAGS +=$(OPTIMIZE) -mmcu=$(MCU)  -DF_CPU=$(F_CPU) \
	-fno-exceptions 		           \
	-fpack-struct -fshort-enums     	   \
	-funsigned-bitfields -funsigned-char       \
	-Wall 	                                   \
#	-Wa,-ahlms=$(firstword                     \
#	$(filter %.lst, $(<:.cpp=.lst))\
#	$(filter %.lst, $(<:.cc=.lst)) \
#	$(filter %.lst, $(<:.C=.lst)))

# assembler
ASMFLAGS +=  -mmcu=$(MCU)        \
	-x assembler-with-cpp            \
#	-Wa,-gstabs,-ahlms=$(firstword   \
#		$(<:.S=.lst) $(<.s=.lst))

# linker
LDFLAGS=-Wl,-Map,$(TARGET).map -mmcu=$(MCU) 




.SUFFIXES : .c .cc .cpp .C .o .out .s .S \
	.hex .ee.hex .h .hh .hpp

# Make targets:
# all, disasm, stats, hex, writeflash/install, clean
all: $(DEPDIR) $(TARGET)


disasm: $(DUMPTARGET) stats

stats: $(TARGET)
	$(OBJDUMP) -h $(TARGET)
	$(SIZE) $(TARGET) 

hex: $(HEXTARGET)

burn: hex
	$(AVRDUDE) -c $(AVRDUDE_PROGRAMMERID)   \
	 -p $(PROGRAMMER_MCU) -P $(AVRDUDE_PORT) -e $(AVRDUDE_EXTRA_FLAGS)   \
	 -U flash:w:$(HEXROMTARGET)

$(DUMPTARGET): $(TARGET) 
	$(OBJDUMP) -S  $< > $@


$(TARGET): $(OBJDEPS)
	$(CC) $(LDFLAGS) -o $(TARGET) $(OBJDEPS) $(LIBS)

$(DEPDIR):
	mkdir  -p $(DEPDIR)
	echo "Directory is used for dependency files " > $(DEPDIR)/README

FORCE:

.PHONY:	all lib build elf hex eep lss sym program coff extcoff clean applet_files sizebefore sizeafter writeflash clean stats gdbinit stats

#### Generating assembly ####
# asm from C
%.s: %.c
	$(CC) -S -fverbose-asm $(CFLAGS) $< -o $@

# asm from (hand coded) asm
%.s: %.S
	$(CC) -S -fverbose-asm $(ASMFLAGS) $< > $@


# asm from C++
.cpp.s .cc.s .C.s :
	$(CXX) -S -fverbose-asm $(CXXFLAGS) $< -o $@



#### Generating object files ####
# object from C
.c.o: 
	$(CC) $(CFLAGS) -c $< -o $@


# object from C++ (.cc, .cpp, .C files)
.cc.o .cpp.o .C.o :
	$(CXX) $(CXXFLAGS) -c $< -o $@

# object from asm
.S.o :
	$(CC) $(ASMFLAGS) -c $< -o $@

# Automatic dependencies
#%.d: %.c
#	$(CC) -M $(CFLAGS) $< | sed "s;$(notdir $*).o:;$*.o $*.d:;" > $@
#
#%.d: %.cpp
#	$(CXX) -M $(CXXFLAGS) $< | sed "s;$(notdir $*).o:;$*.o $*.d:;" > $@

CFLAGS +=  -Wp,-MD,$(DEPDIR)/$*.d
CXXFLAGS+=  -Wp,-MD,$(DEPDIR)/$*.d


#### Generating hex files ####
# hex files from elf
#
.out.hex:
	$(OBJCOPY) --only-section .text  \
		--only-section .data    \
		--output-target $(HEXFORMAT) $< $@

.out.ee.hex: 
	$(OBJCOPY) --only-section .eeprom            \
		--change-section-lma .eeprom=0 \
		--output-target $(HEXFORMAT) $< $@


#####  Generating a gdb initialisation file    #####
##### Use by launching simulavr and avr-gdb:   #####
#####   avr-gdb -x gdbinit-myproject           #####
gdbinit: $(GDBINITFILE)

$(GDBINITFILE): $(TARGET)
	@echo "file $(TARGET)" > $(GDBINITFILE)	
	@echo "target remote localhost:1212" \
		                >> $(GDBINITFILE)
	@echo "load"        >> $(GDBINITFILE) 
	@echo "break main"  >> $(GDBINITFILE)
	@echo "continue"    >> $(GDBINITFILE)
	@echo
	@echo "Use 'avr-gdb -x $(GDBINITFILE)'"


help:
	@echo "Make file for AVR programming."
	@echo ""
	@echo "make                 - build the *.out executable."
	@echo "make lib             - make the library in lib."
	@echo "make disasm          - make a *.s disassembled file."
	@echo "make stats           - print the objects stats."
	@echo "make hex             - make a *.hex file, ready for burning."
	@echo "make burn            - burn the code using avrdude. "
	@echo " "
	@echo "make gdb             - initialize gdb debugging"
	@echo " "
	@echo "make clean           - cleanup"
	@echo "make distclean       - really cleanup. "
	@echo " "
	@echo "Using: "
	@echo "AVR_HOME             = $(AVR_HOME) "
	@echo "BOARD_TYPE           = $(BOARD_TYPE) "
	@echo "MCU                  = $(MCU) "
	@echo "F_CPU                = $(F_CPU) "
	@echo "SYSTEM_TYPE          = $(SYSTEM_TYPE)"
	@echo "PROGRAMMER_MCU       = $(PROGRAMMER_MCU)"
	@echo "AVRDUDE_PROGRAMMERID = $(AVRDUDE_PROGRAMMERID)"

exhelp: help
	@echo ""
	@echo "Detailed help to debug makefile:"
	@echo "CFLAGS               = $(CFLAGS)"
	@echo "CXXFLAGS             = $(CXXFLAGS)"
	@echo "LIBS                 = $(LIBS)"



#### Cleanup ####
clean:
	$(REMOVE) $(TARGET) $(TARGET).map $(DUMPTARGET)
	$(REMOVE) $(OBJDEPS)  
	$(REMOVE) $(addprefix $(DEPDIR)/,$(CFILES:.c=.d)  $(CXXFILES:.cxx=.d)  $(CPPFILES:.cpp=.d)  $(CCFILES:.cc=.d))
	$(REMOVE) $(LST) $(GDBINITFILE)
	$(REMOVE) $(GENASMFILES)
	$(REMOVE) $(HEXTARGET)


distclean: clean
	@echo "---- Nothing else to remove? ----"

#-include $(CFILES:%.c=$(DEPDIR)/%.d)
#-include $(CPPFILES:%.cpp=$(DEPDIR)/%.d)
#-include $(CXXFILES:%.cxx=$(DEPDIR)/%.d)
#-include $(CCFILES:%.cc=$(DEPDIR)/%.d)

