#
#  Electronics.py
#
#  Author: Maurik Holtrop - 2020
#
#  This file currently only contains one class "Resistor" which helps with computations involving resistors.
#
#
import numbers
import math


class Resistor:
    """Simple implementation of a resistor class, that includes checks on the max power of the
    combined resistors."""

    def __init__(self, resistance=0., power=1./8.):   # The required initializer.
        self.r = resistance
        self.p_max = power

    def __add__(self, other):        # Implement the "+" operation.
        value = self.r + other.r
        if math.isinf(self.r) or math.isinf(other.r):
            power = 0.
        elif self.r == 0:
            return Resistor(other.r, other.p_max)
        elif other.r == 0:
            return Resistor(self.r, self.p_max)
        else:
            i2_max = min(self.p_max / self.r, other.p_max / other.r)  # I_max squared.
            power = i2_max*(self.r + other.r)
        return Resistor(value, power)

    def __mul__(self, other):                           # Implement the "*" operation. We use this for parallel.
        if isinstance(other, numbers.Number) or \
                isinstance(other, numbers.Real):         # But if other is a number, then multiply.
            return Resistor(self.r * other, self.p_max * other)  # Power rating for n series is just n*p
        if self.r == 0 or other.r == 0:
            return Resistor(0, math.inf)                # A zero ohm resistor has infinite power :-)
        elif math.isinf(self.r):
            return Resistor(other.r, other.p_max)
        elif math.isinf(other.r):
            return Resistor(self.r, self.p_max)
        else:
            value = self.r * other.r / (self.r + other.r)
            v2_max = min(self.p_max * self.r, other.p_max * other.r)  # V_max squared.
            power = v2_max*(1 / self.r + 1 / other.r)
            return Resistor(value, power)  # Return the parallel equivalent resistor

    def __or__(self, other):                            # An alternate for "*" could be "|", but no one uses that.
        return self.__mul__(other)

    def __rmul__(self, other):                        # Note, __rmul__ is called for 2*R situation.
        return Resistor(self.r * other, self.p_max * other)   # Then other is always a number, so no need to test.

    def __truediv__(self, other):                        # Implement division with "/".
        if isinstance(other, numbers.Number) or \
                isinstance(other, numbers.Real):            # If other is a number, then divide the value
            return Resistor(self.r / other, self.p_max)  # and return a Resistor.
        if other.r == 0:                                # If other is zero, you get an open connection = infinity.
            return Resistor(math.inf, self.p_max)
        else:
            return self.r / other.r  # Divide resistors: returns a number! Power info is lost.

    def __floordiv__(self, other):                     # Implement integer division "//"
        if isinstance(other, numbers.Number) or \
                isinstance(other, numbers.Real):          # If other is a number, then divide the value
            return Resistor(self.r // other, self.p_max)  # Returns a Resistor.
        if other.r == 0:                              # If other is zero, you get an open connection = infinity.
            return Resistor(math.inf, self.p_max)
        else:
            return self.r // other.r  # Integer Divide resistors: returns a number! Power info is lost.

    def __rtruediv__(self, other):                     # This is for  2/R so a number on the left.
        return other / self.r  # Returns a number!     # Other is always a number, return a number.

    def __rfloordiv__(self, other):                    # This is for 2//R so number on the left.
        return other // self.r  # Returns a number!    # Other is always a number, return a number.

    def power_i(self, current):                               # Calculate the power used for current I.
        return current * current * self.r

    def check_power_i(self, current):                          # Check if power rating is sufficient for current I
        return self.power_i(current) < self.p_max

    def power_v(self, v_in):                               # Calculate the power used if connected to voltage V
        return v_in * v_in / self.r

    def check_power_v(self, v_in):                          # Check the power rating if connected to voltage V.
        return self.power_v(v_in) < self.p_max

    def __str__(self):                                # Print a sensible string with the resistance and the power.
        return f"{self.r:.2f}Ω, {self.p_max:.2f}W"

    def __repr__(self):  # Print a sensible string with the resistance and the power.
        return str(self.r) + "Ω," + str(self.p_max) + "W"

    @property                                         # This makes "R" a property of the resistor.
    def r(self):
        return self._resistance

    @r.setter                                         # This allows you to set the property R
    def r(self, r_new):
        if r_new >= 0:                                  # We test to make sure the value makes sense.
            self._resistance = r_new
        else:
            print("Error, you cannot have a negative resistance. (At least not here.)")
            self._resistance = 0

    @property                                        # This allows you to set the property Pmax
    def p_max(self):
        return self._power

    @p_max.setter
    def p_max(self, power):                                # This allows you to set Pmax.
        if power >= 0:
            self._power = power
        else:
            print("Error - we cannot have negative power.")
            self._power = 0
