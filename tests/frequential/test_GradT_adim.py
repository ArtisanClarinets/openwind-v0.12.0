#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright (C) 2019-2025, INRIA
#
# This file is part of Openwind.
#
# Openwind is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Openwind is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Openwind.  If not, see <https://www.gnu.org/licenses/>.
#
# For more informations about authors, see the CONTRIBUTORS file

import numpy as np
from openwind import ImpedanceComputation
import unittest

F1 = 1000
F2 = 1001
frequencies = np.arange(F1, F2, 1)

def GradT(x):
    return 37 - (37 - 21) * x / 0.6

# ----------------
# Tested Geometry cyl-disc-cone
# ----------------
tested_geom =  [[0, 0.3, 0.005, 0.005, 'linear'], [0.3, 0.6, 0.01, 0.02, 'linear']]
ordre = 10
lenEle = 0.09

class TestGradTAdmi(unittest.TestCase):

    def createImpedanceComputation(self):
        self.impedances = dict()
        for losses in [False, True]:
            self.impedances[losses]=dict()
            print("Test with losses = %s" % str(losses))
            result_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=GradT,
                                                 l_ele=lenEle, order=ordre, losses=losses,
                                                 nondim=True)
            result_dim = ImpedanceComputation(frequencies, tested_geom, temperature=GradT,
                                              l_ele=lenEle, order=ordre, losses=losses,
                                              nondim=False)
            self.impedances[losses]['ND']  = result_nondim.impedance
            self.impedances[losses]['DIM'] = result_dim.impedance
            
    
    def test_launch(self):
        self.createImpedanceComputation()
        losses = False
        err = np.linalg.norm(self.impedances[losses]['ND'] - self.impedances[losses]['DIM']) / np.linalg.norm(self.impedances[losses]['DIM'])
        print("Impedance difference adim/non-adim with temperature gradient:", err)
        self.assertLess(err,1e-12, msg = "Adim/non-adim give different results (but shouldn't).")
        
        losses = True
        err = np.linalg.norm(self.impedances[losses]['ND'] - self.impedances[losses]['DIM']) / np.linalg.norm(self.impedances[losses]['DIM'])
        print("Impedance difference adim/non-adim with temperature gradient:", err)
        self.assertLess(err,1e-12, msg = "Adim/non-adim give different results (but shouldn't).")

if __name__ == "__main__":
    unittest.main()
