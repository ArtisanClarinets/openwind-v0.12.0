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

import unittest
import numpy as np

from openwind.technical import InstrumentGeometry, AdjustInstrumentGeometry

class AdjustInstrumentGeometryTest(unittest.TestCase):

    def test_adjust_spline_one_cone(self):
        x_targ = np.linspace(0,.5,10)
        r_targ = np.linspace(5e-3,1e-2,10) + 2e-3*np.sin(x_targ*2*np.pi)
        Geom = np.array([x_targ, r_targ]).T.tolist()
        # creation of a geometry which will be adjusted on the prevous one
        geom_adjust = [[0, .5, 5e-3, '~5e-3', 'spline',
                        '.15', '.3', '~5e-3', '~5e-3']]
        # the corresponding InstrumentGeometry object are instanciated
        target_test = InstrumentGeometry(Geom)
        adjust_test = InstrumentGeometry(geom_adjust)
        # the AdjustInstrumentGeometry is instanciated from the two instrument geometries
        test = AdjustInstrumentGeometry(adjust_test, target_test)
        # the optimization process is carried out
        adjusted = test.optimize_geometry(iter_detailed=False)

if __name__ == "__main__":
    unittest.main()
