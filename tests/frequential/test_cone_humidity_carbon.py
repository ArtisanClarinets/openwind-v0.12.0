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


frequencies = 1200
tol = 1e-12

# %%
class TestConeHumidity(unittest.TestCase):

    @staticmethod
    def grad_temp(x):
        return 37 - (37-25)*x/.5

    @staticmethod
    def grad_humidity(x):
        return 1*(1 -x/.5)

    @staticmethod
    def grad_carbon(x):
        return 0.1*(1 -x/.5)

    def error_computation(self, ref_value, temperature=20, humidity=.3, carbon=.06, label=''):
        tested_geom = [[0, 5e-3],
                       [0.1, 10e-3],
                       [0.5, 3e-3]]
        options = dict(temperature=temperature, humidity=humidity, carbon=carbon,
                       ref_phy_coef='RR')

        imped_nondim = ImpedanceComputation(frequencies, tested_geom, nondim=True, **options)
        err_nondim = np.abs(imped_nondim.impedance - ref_value)/np.abs(ref_value)

        imped_dim = ImpedanceComputation(frequencies, tested_geom, nondim=False, **options)
        err_dim = np.abs(imped_dim.impedance - ref_value)/np.abs(ref_value)

        err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)

        print(label + str(imped_nondim.impedance))

        self.assertLess(err_nondim, tol, msg=label + "The non-dim computation is not "
                          + "consistent with the previous versions.")
        self.assertLess(err_dim, tol, msg=label + "The dim computation is not "
                          + "consistent with the previous versions.")
        self.assertLess(err, tol, msg=label + "Adim/non-adim give different results (but shouldn't).")

    def test_grad_temp(self):
        ref_value = 3322021.16894044+14869961.0165803j
        label = "Test: Grad temp, RH=cst, CO2=cst:"
        self.error_computation(ref_value, temperature=self.grad_temp, label=label)

    def test_grad_humidity(self):
        ref_value = 16196410.00653509+28337779.04548091j
        label = "Test: T=cst, RH=grad, CO2=cst:"
        self.error_computation(ref_value, humidity=self.grad_humidity, label=label)

    def test_grad_CO2(self):
        ref_value = 14820936.71193769+27973396.02317359j
        label = "Test: T=cst, RH=cst, CO2=grad:"
        self.error_computation(ref_value, carbon=self.grad_carbon, label=label)

    def test_all_grad(self):
        ref_value = 2689055.62723308+13545435.00297268j
        label = "Test: T=grad, RH=grad, CO2=grad:"
        self.error_computation(ref_value, temperature=self.grad_temp, humidity=self.grad_humidity, carbon=self.grad_carbon, label=label)

if __name__ == "__main__":
    unittest.main()
