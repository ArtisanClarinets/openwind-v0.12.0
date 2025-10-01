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

F1 = 1200
F2 = 1201
frequencies = np.arange(F1, F2, 1)
tol = 1e-10

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
# %%
class TestConeGradTemp(unittest.TestCase):



    def error_computation(self, tested_geom, temperature, losses, lenEle, ordre, ref_value):
        imped_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                 l_ele=lenEle, order=ordre, losses=losses, nondim=True,
                                 radiation_category='planar_piston', **dry_air)
        err_nondim = np.abs(imped_nondim.impedance - ref_value)/np.abs(ref_value)

        imped_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                              l_ele=lenEle, order=ordre, losses=losses, nondim=False,
                              radiation_category='planar_piston', **dry_air)
        err_dim = np.abs(imped_dim.impedance - ref_value)/np.abs(ref_value)

        err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)
        return err_nondim, err_dim, err

    def test_doubleconeTemp(self):

        # ----------------
        # Double cone without losses
        # ----------------
        tested_geom = [[0, 5e-3],
                       [0.1, 10e-3],
                       [0.5, 3e-3]]
        ordre = 10
        lenEle = 1e-1


        def temperature(x):
            return 37 - (37-25)*x/tested_geom[-1][0]

        ref_value = 30045.39841385 + 10052489.84456801j

        print("Test double cone without losses")
        err_nondim, err_dim, err = self.error_computation(tested_geom, temperature, False, lenEle, ordre, ref_value)

        self.assertLess(err_nondim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err_dim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err, tol, msg="Adim/non-adim give different results (but shouldn't).")


    def test_doubleconeTemp_losses(self):
        # ----------------
        # Double cone with losses
        # ----------------
        tested_geom = [[0, 5e-3],
                       [0.1, 10e-3],
                       [0.5, 3e-3]]
        ordre = 10
        lenEle = 1e-1


        def temperature(x):
            return 37 - (37-25)*x/tested_geom[-1][0]

        ref_value_damping = 1873196.04041024+11350562.70761363j

        print("Test double cone with losses")
        err_nondim, err_dim, err = self.error_computation(tested_geom, temperature, True, lenEle, ordre, ref_value_damping)
        self.assertLess(err_nondim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err_dim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err, tol, msg="Adim/non-adim give different results (but shouldn't).")



    def test_trumpetTemp(self):
        # ----------------
        # Micro trumpet without losses
        # ----------------
        tested_geom = [[0, 8.4e-3],
                       [1e-3, 8.4e-3],
                       [0.1, 7e-3],
                       [1.4187041e-1, 6.1e-2]]


        def temperature(x):
            return 37 - (37-25)*x/tested_geom[-1][0]


        ordre = 10
        lenEle = 1.05e-2
        ref_value = 61216.50352838 - 1968957.35751782j

        print("Test micro trumpet without losses ")
        err_nondim, err_dim, err = self.error_computation(tested_geom, temperature, False, lenEle, ordre, ref_value)
        self.assertLess(err_nondim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err_dim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err, tol, msg="Adim/non-adim give different results (but shouldn't).")

    def test_trumpetTemp_losses(self):
        # ----------------
        # Micro trumpet with losses
        # ----------------
        tested_geom = [[0, 8.4e-3],
                       [1e-3, 8.4e-3],
                       [0.1, 7e-3],
                       [1.4187041e-1, 6.1e-2]]


        def temperature(x):
            return 37 - (37-25)*x/tested_geom[-1][0]


        ordre = 10
        lenEle = 1.05e-2
        ref_value_damping = 104119.29673464-1922121.04364236j

        print("Test micro trumpet with losses ")
        err_nondim, err_dim, err = self.error_computation(tested_geom, temperature, True, lenEle, ordre, ref_value_damping)
        self.assertLess(err_nondim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")
        self.assertLess(err_dim, tol, msg="The computation with gradient temperature is not "
                          + "consistent with the previous versions.")

        self.assertLess(err, tol, msg="Adim/non-adim give different results (but shouldn't).")


if __name__ == "__main__":
    unittest.main()
