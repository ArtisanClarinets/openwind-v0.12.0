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

F1 = 1000
F2 = 1001
frequencies = np.arange(F1, F2, 1)

temperature = 25
ordre = 10
lenEle = 3e-2

# ----------------
# Tested Geometry cyl disc cone
# ----------------
#tested_file = 'cone.txt'
tested_geom = [[0, 0.1, 5e-3, 5e-3, 'linear'],
               [0.1, 0.2, 8e-3, 10e-3, 'linear']]
ref_value_mass = 1051784.01738368 + 6739608.3948181j
ref_value_wo_mass = 1023315.9226162 + 6656105.82543338j
tol = 1e-10

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

class TestSectionDiscontinuity(unittest.TestCase):
    def test_two_cones_with_mass(self):
        print("Test of two cones with discontinuity masses")
        imped_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                 l_ele=lenEle, order=ordre, losses=True,
                                 nondim=True, discontinuity_mass=True,
                                 radiation_category='planar_piston', **dry_air)
        err_nondim = np.abs(imped_nondim.impedance - ref_value_mass)/np.abs(ref_value_mass)
        imped_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                              l_ele=lenEle, order=ordre, losses=True,
                              nondim=False, discontinuity_mass=True,
                              radiation_category='planar_piston', **dry_air)
        err_dim = np.abs(imped_dim.impedance - ref_value_mass)/np.abs(ref_value_mass)
        err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)

        self.assertLess(err,tol, msg="Adim/non-adim give different results (but shouldn't).")
        self.assertLess(err_nondim, tol, msg="The nondimenzionalized computation fails.")
        self.assertLess(err_dim, tol, msg="The dimenzionalized computation fails.")


# %%
    def test_two_cones_no_mass(self):
        print("Test of two cones without discontinuity masses")
        imped_nondim_wo = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                 l_ele=lenEle, order=ordre, losses=True,
                                 nondim=True, discontinuity_mass=False,
                                 radiation_category='planar_piston', **dry_air)
        err_nondim_wo = np.abs(imped_nondim_wo.impedance - ref_value_wo_mass)/np.abs(ref_value_wo_mass)
        imped_dim_wo = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                              l_ele=lenEle, order=ordre, losses=True,
                              nondim=False, discontinuity_mass=False,
                              radiation_category='planar_piston', **dry_air)
        err_dim_wo = np.abs(imped_dim_wo.impedance - ref_value_wo_mass)/np.abs(ref_value_wo_mass)
        err_wo = np.linalg.norm(imped_nondim_wo.impedance - imped_dim_wo.impedance) / np.linalg.norm(imped_dim_wo.impedance)

        self.assertLess(err_wo,tol, msg="Adim/non-adim give different results (but shouldn't).")
        self.assertLess(err_nondim_wo, tol, msg="The nondimenzionalized computation fails.")
        self.assertLess(err_dim_wo, tol, msg="The dimenzionalized computation fails.")




if __name__ == "__main__":
    unittest.main()
