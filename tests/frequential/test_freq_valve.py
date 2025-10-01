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


freq = 743.2
temp = 25

class TestValveFreq(unittest.TestCase):
    """
    This test check if the valve has the same effect than modifying the main
    bore geometry by adding a piece of tube.
    """

    def imped_with_valve(self, disc_mass, note):
        geom = [[0, 0.005], [0.1, 0.005], [0.7, 0.005]]
        valves = [['variety','label',   'position', 'radius',   'chimney', 'reconnection'],
                  ['valve',  'piston',  0.1,        3e-3,       0.1,        0.15]]
        fing_chart = [['label', 'depress', 'press'],
                      ['piston', 'o', 'x']]
        f_solve = ImpedanceComputation(freq, geom, valves, fing_chart,
                                       temperature=temp, note=note,
                                       discontinuity_mass=disc_mass)
        return f_solve.impedance

    def imped_eq_depress_valve(self, disc_mass):
        geom_wo = [[0, 0.005], [0.1, 0.005], [.15, .005], [0.7, 0.005]]
        f_solve = ImpedanceComputation(freq, geom_wo,
                                       temperature=temp,
                                       discontinuity_mass=disc_mass)
        return f_solve.impedance

    def imped_eq_press_valve(self, disc_mass):
        geom_with = [[0, 0.005], [0.1, 0.005], [0.1, .003], [0.2, .003],
                     [.2, .005], [0.75, 0.005]]
        f_solve = ImpedanceComputation(freq, geom_with,
                                       temperature=temp,
                                       discontinuity_mass=disc_mass)
        return f_solve.impedance


    def compare_valve_mainbore(self, disc_mass, note):
        Z_instru = self.imped_with_valve(disc_mass, note)
        if note == 'press':
            Z_ref = self.imped_eq_press_valve(disc_mass)
        else:
            Z_ref = self.imped_eq_depress_valve(disc_mass)
        self.assertLess(np.linalg.norm(Z_instru-Z_ref)/np.linalg.norm(Z_ref), 1e-10,
                        msg=f"in test_freq_valve/compare_valve_mainbore {Z_instru} expected : {Z_ref}")

    def test_without_masses_press(self):
        self.compare_valve_mainbore(False, 'press')

    def test_without_masses_depress(self):
        self.compare_valve_mainbore(False, 'depress')

    def test_with_masses_press(self):
        self.compare_valve_mainbore(True, 'press')

    def test_with_masses_depress(self):
        self.compare_valve_mainbore(True, 'depress')

if __name__ == "__main__":
    unittest.main()
