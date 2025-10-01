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
import unittest
from openwind import ImpedanceComputation

frequencies = np.array([2000])
temperature = 25
ordre = 1
lenEle = 0.07

tested_geom = [[0, 1e-3],
               [0.1, 6e-3],
               #[0.22, 8e-3]
               ]


class TestDiffreprPlus(unittest.TestCase):
    def test_dr(self):
                
        first_result = None
        for losses in ['diffrepr', 'diffrepr+']:
            for nondim in [True, False]:
                print('losses=',losses,'; nondim=',nondim)
                result = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                  l_ele=lenEle, order=ordre, losses=losses,
                                  nondim=nondim)
                if first_result is None:
                    first_result = result.impedance
                else:
                    err = np.linalg.norm(result.impedance - first_result) / np.linalg.norm(result.impedance)
                    print('err = {:.3e}'.format(err))
                    self.assertLess(err, 1e-12, "Results should be the same for diffrepr/diffrepr+ and with/without nondim.")
                    
        print("OK : diffrepr and diffrepr+, with or without nondim, all give the same results.")

if __name__ == "__main__":
    unittest.main()
