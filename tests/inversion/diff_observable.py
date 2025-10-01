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
np.random.seed(0) # seed the PRNG for reproducibility
import unittest

from openwind.inversion import observation as obs

class DesignTest(unittest.TestCase):


    def assert_diff_equal(self, observable, diff_observable, tol=1e-7):
        ReZ = np.random.rand(2)
        ImZ =  1j*np.random.rand(2)
        dZ = 1e-8


        Delta_obs_Re = (observable(ReZ + dZ + ImZ) - observable(ReZ + ImZ))/dZ
        Delta_obs_Im = (observable(ReZ + 1j*dZ + ImZ) - observable(ReZ + ImZ))/dZ
        Delta_obs = 0.5*(Delta_obs_Re -1j*Delta_obs_Im)

        Delta_obs_conj_Re = (observable(ReZ + dZ + ImZ).conjugate() - observable(ReZ + ImZ).conjugate())/dZ
        Delta_obs_conj_Im = (observable(ReZ + 1j*dZ + ImZ).conjugate() - observable(ReZ + ImZ).conjugate())/dZ
        Delta_obs_conj = 0.5*(Delta_obs_conj_Re -1j*Delta_obs_conj_Im)


        diff_obs, diff_obs_conj = diff_observable(ReZ + ImZ)

        err_obs = np.linalg.norm((diff_obs - Delta_obs))
        err_obs_conj = np.linalg.norm((diff_obs_conj - Delta_obs_conj))
        self.assertLess(err_obs, tol)
        self.assertLess(err_obs_conj, tol)

    def test_impedance(self):
        self.assert_diff_equal(obs.impedance, obs.diff_impedance_wrZ)

    def test_reflection(self):
        self.assert_diff_equal(obs.reflection, obs.diff_reflection_wrZ)

    def test_modulus_impedance(self):
        self.assert_diff_equal(obs.module_square, obs.diff_module_square_wrZ)

    def test_phase_impedance(self):
        self.assert_diff_equal(obs.impedance_phase,
                               obs.diff_impedance_phase_wrZ, tol=1e-5)

    def test_phase_reflection(self):
        self.assert_diff_equal(obs.reflection_phase,
                               obs.diff_reflection_phase_wrZ, tol=1e-5)

    def test_modulus_reflection(self):
        self.assert_diff_equal(obs.reflection_modulus_square,
                               obs.diff_reflection_modulus_square_wrZ)

if __name__ == '__main__':
    unittest.main()

# dZ = 1e-8

# ReZ = np.random.rand()
# ImZ =  1j*np.random.rand()


# Delta_obs_Re = (obs.impedance(ReZ + dZ + ImZ) - obs.impedance(ReZ + ImZ))/dZ
# Delta_obs_Im = (obs.impedance(ReZ + 1j*dZ + ImZ) - obs.impedance(ReZ + ImZ))/dZ
# Delta_obs = 0.5*(Delta_obs_Re -1j*Delta_obs_Im)

# Delta_obs_conj_Re = (obs.impedance(ReZ + dZ - ImZ) - obs.impedance(ReZ - ImZ))/dZ
# Delta_obs_conj_Im = (obs.impedance(ReZ - 1j*dZ - ImZ) - obs.impedance(ReZ - ImZ))/dZ
# Delta_obs_conj = 0.5*(Delta_obs_conj_Re -1j*Delta_obs_conj_Im)


# diff_obs, diff_obs_conj = obs.diff_impedance_wrZ(ReZ + ImZ)

# err_obs = np.linalg.norm((diff_obs - Delta_obs))
# err_obs_conj = np.linalg.norm((diff_obs_conj - Delta_obs_conj))
