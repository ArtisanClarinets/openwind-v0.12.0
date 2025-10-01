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

"""
Test for openwind.frequential.frequential_pressure_condition.
"""

import numpy as np
import unittest

from openwind import InstrumentGeometry, InstrumentPhysics, Player
from openwind.frequential import (FrequentialSolver,
                                  FrequentialPressureCondition)

tol = 1e-10
class TestPressureCond(unittest.TestCase):
    def test_pressure_condition(self):
        shape = [[0.0, 2e-3], [0.8, 8e-3]]
        fs = np.arange(20, 2000, 1)
        geom = InstrumentGeometry(shape)
        phys = InstrumentPhysics(geom, 25, Player(), losses=True, radiation_category='perfectly_open')
        fsolver = FrequentialSolver(phys, fs, order=10, l_ele=0.5)

        # Check that the right class was instantiated
        rad_comp = fsolver.f_components['bell_radiation']
        assert isinstance(rad_comp, FrequentialPressureCondition), \
            "FSolver failed to instantiate FrequentialPressureCondition correctly"

        fsolver.solve(interp=True,
                      # interp_grid=0.01
                      )

        # plt.figure("Ah_nodiag matrix")
        # plt.imshow(abs(fsolver.Ah_nodiag.todense() != 0))

        # plt.figure("Impedance")
        # fsolver.plot_impedance()

        # plt.figure("Pressure profile")
        # fsolver.plot_pressure_at_freq(1000)

        # Check that the boundary condition is verified
        err = abs(fsolver.pressure[0][-1]) / max(abs(fsolver.pressure[0]))
        self.assertLess(err, tol, f"Pressure condition failed")

if __name__ == "__main__":
    unittest.main()
