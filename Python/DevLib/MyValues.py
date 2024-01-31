#!/usr/bin/env python3
#
# MyValues
#
# Author: Maurik Holtrop
#
# This is a helper class to allow values to be set like a list for any of the chips.
#

class MyValues:
    """Class for getting the value of the chip, which mimics a list."""

    def __init__(self, getter, max_num):
        self._getter = getter
        self._MAX = max_num
        self._n = 0

    def __getitem__(self, idx):
        return self._getter(idx)

    def __setitem__(self, idx, val):
        raise ValueError("The ADC values cannot be written to, only read.")

    def __len__(self):
        return self._MAX

    def __iter__(self):
        self._n = 0
        return self

    def __next__(self):
        if self._n < len(self):
            result = self[self._n]
            self._n += 1
            return result
        else:
            raise StopIteration

    def __repr__(self):
        return str(self)

    def __str__(self):
        tmp_list = [x for x in self]
        return str(tmp_list)
