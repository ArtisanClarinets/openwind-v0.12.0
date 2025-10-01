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

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
class TestNewLosses(unittest.TestCase):

    def test_besselnew_vs_bessel(self):
        """
        Models 'bessel' and 'bessel_new' should coincide exactly on cylinders.
        """
        shape = [[0,1e-3],[0.1,1e-3]]
        fs = [20,200,2000,20000]
        res_old = ImpedanceComputation(fs, shape, temperature=25, l_ele=0.1, order=5, losses='bessel')
        res_new = ImpedanceComputation(fs, shape, temperature=25, l_ele=0.1, order=5, losses='bessel_new')

        err = np.abs(res_old.impedance - res_new.impedance) / np.abs(res_old.impedance)
        self.assertLess(np.max(err), 1e-16)

    def test_besselnew_regression(self):
        """
        Check that the results of model 'bessel_new' do not change
        significantly during an update.
        """
        shape = [[0,1e-3],[0.1,0.07]]
        fs = [20,200,2000,20000]
        old_result = np.array([   1279.32009943  +25384.76685286j,
                                  4336.46788967 +246349.89175882j,
                                208438.61178563+2542740.94714268j,
                                 24885.24435908+4008239.33471344j])
        res = ImpedanceComputation(fs, shape, l_ele=0.1, order=5,
                                   temperature=25,
                                   losses='bessel_new', **dry_air)

        err = np.abs(old_result - res.impedance) / np.abs(old_result)
        self.assertLess(np.max(err), 1e-12)

    def test_sh_regression(self):
        """
        Check that the results of loss model 'sh' do not change
        significantly during an update.

        Note : due to overflow when computing the hypergeometric function,
        the 'sh' model may be unusable for large tubes and/or wide radii.
        """
        shape = [[0,1e-4],[0.03,0.01]]
        fs = [20,200,2000]
        old_result = np.array([ 230654.90492551  +479773.83935865j,
                                506206.69788184 +4171629.18200754j,
                               1610952.30726767+39729834.15176198j])
        res = ImpedanceComputation(fs, shape, l_ele=0.1, order=5,
                                   temperature=25,
                                   losses='sh', **dry_air)

        err = np.abs(old_result - res.impedance) / np.abs(old_result)
        self.assertLess(np.max(err), 4e-12)


if __name__ == "__main__":
    unittest.main()
