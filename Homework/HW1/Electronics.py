import numbers
import math
class Resistor():

    def __init__(self,R=0,P=1./8.):   # The required initializer.
        self.R = R
        self.Pmax = P

    def __add__(self,other):        # Implement the "+" operation.
        Value = self.R + other.R
        I2_max = min(self.Pmax/self.R,other.Pmax/other.R) # I_max squared.
        Power = I2_max*(self.R + other.R)
        return( Resistor(Value,Power))

    def __mul__(self,other):                           # Implement the "*" operation. We use this for parallel.
        if isinstance(other,numbers.Number):           # But if other is a number, then multiply.
            return(Resistor(self.R * other,self.Pmax)) # Power rating not modified for numeric multiply.
        if self.R == 0 or other.R == 0:
            return(Resistor(0,math.inf))               # A zero ohm resistor has infinite power :-)
        else:
            Value = self.R*other.R/(self.R + other.R)
            V2_max = min(self.Pmax*self.R,other.Pmax*other.R) # V_max squared.
            Power = V2_max*(1/self.R + 1/other.R)
            return( Resistor(Value,Power))             # Return the parallel equivalent resistor

    def __or__(self,other):                            # An alternate for "*" could be "|", but no one uses that.
        if isinstance(other,numbers.Number):
            return(Resistor(self.R * other,self.Pmax)) # Power rating not modified.
        if self.R == 0 or other.R == 0:
            return(Resistor(0,math.inf))               # A zero ohm resistor has infinite power :-)
        else:
            Value = self.R*other.R/(self.R + other.R)
            V2_max = min(self.Pmax*self.R,other.Pmax*other.R) # V_max squared.
            Power = V2_max*(1/self.R + 1/other.R)
            return( Resistor(Value,Power))           # Return the parallel equivalent resistor


    def __rmul__(self,other):                        # Note, __rmul__ is called for 2*R situation.
        return(Resistor(self.R * other,self.Pmax))      # Then other is always a number, so no need to test.

    def __truediv__(self,other):                     # Implement division with "/".
        if isinstance(other,numbers.Number):         # If other is a number, then divide the value
            return(Resistor(self.R /other,self.Pmax))   # and return a Resistor.
        if other.R == 0:                             # If other is zero, you get an open connection = infinity.
            return(Resistor(math.inf,self.Pmax))
        else:
            return( self.R/other.R)                  # Divide resistors: returns a number! Power info is lost.

    def __floordiv__(self,other):                     # Implement integer division "//"
        if isinstance(other,numbers.Number):          # If other is a number, then divide the value
            return(Resistor(self.R //other,self.Pmax))   # Returns a Resistor.
        if other.R == 0:                              # If other is zero, you get an open connection = infinity.
            return(Resistor(math.inf,self.Pmax))
        else:
            return( self.R//other.R)                  # Integer Divide resistors: returns a number! Power info is lost.

    def __rtruediv__(self,other):                     # This is for  2/R so a number on the left.
        return( other/self.R) # Returns a number!     # Other is always a number, return a number.

    def __rfloordiv__(self,other):                    # This is for 2//R so number on the left.
        return( other//self.R) # Returns a number!    # Other is always a number, return a number.

    def PowerI(self,I):                               # Calculate the power used for current I.
        return(I*I*self.R)

    def checkPowerI(self,I):                          # Check if power rating is sufficient for current I
        return( self.PowerI(I)<self.Pmax)

    def PowerV(self,V):                               # Calculate the power used if connected to voltage V
        return(V*V/self.R)

    def checkPowerV(self,V):                          # Check the power rating if connected to voltage V.
        return( self.PowerV(V)<self.Pmax)

    def __str__(self):                                # Print a sensible string with the resistance and the power.
        return( str(self.R)+"Ω," + str(self.Pmax)+"W")

    @property                                         # This makes "R" a property of the resistor.
    def R(self):
        return(self._resistance)

    @R.setter                                         # This allows you to set the property R
    def R(self,Rnew):
        if Rnew>= 0:                                  # We test to make sure the value makes sense.
            self._resistance=Rnew
        else:
            print("Error, you cannot have a negative resistance. (At least not here.)")
            self._resistance=0

    @property                                        # This allows you to set the property Pmax
    def Pmax(self):
        return(self._power)

    @Pmax.setter
    def Pmax(self,P):                                # This allows you to set Pmax.
        if P>= 0:
            self._power=P
        else:
            print("Error - we cannot have negative power.")
            self._power=0
