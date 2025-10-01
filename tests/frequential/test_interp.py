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
Created on Thu Jul 25 14:03:21 2019

@author: guillaume
"""


import numpy as np
import unittest
from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.frequential import FrequentialSolver

nb_error = 0
seuil = 1e-8

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

class TestInterp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        radiation= 'planar_piston'
        cls.f_s = np.arange(20,2000,100)
        player=Player()

        # one cylinder
        mk_mod = InstrumentGeometry([[0, 0.2, 5e-3, 5e-3, 'linear']])
        cls.cyl_phy = InstrumentPhysics(mk_mod, 25, player, convention='PH1', nondim=True,
                                    losses=True, radiation_category=radiation, **dry_air)

        # two cylinders
        mk_mod = InstrumentGeometry([[0, 0.15, 5e-3, 5e-3, 'linear'], [0.15, 0.2, 5e-3, 5e-3, 'linear']])
        cls.two_cyl_phy = InstrumentPhysics(mk_mod, 25, player, convention='PH1', nondim=True,
                                    losses=True, radiation_category=radiation, **dry_air)


    def test_interp_cyl(self):
        ref_values = np.array([51.98838938676154, 264723649.41570306])
        freq_model_FEM = FrequentialSolver(self.cyl_phy, self.f_s, l_ele=0.01, order=5)
        freq_model_FEM.solve(interp=True, interp_grid=0.005)
        calc = np.sum(np.abs(freq_model_FEM.flow)), np.sum(np.abs(freq_model_FEM.pressure))

        self.assertLess(np.linalg.norm(calc-ref_values)/np.linalg.norm(ref_values), seuil,
                        msg = f"In test_interp/test_interp_cyl {calc} expected : {ref_values}")


    # %%
    def test_onmesh_cyl(self):

        ref_values = np.array([128.08987099586176, 654715447.413151])
        freq_model_FEM = FrequentialSolver(self.cyl_phy, self.f_s, l_ele=0.01, order=5)
        freq_model_FEM.solve(interp=True, interp_grid='original')

        calc = np.sum(np.abs(freq_model_FEM.flow)), np.sum(np.abs(freq_model_FEM.pressure))

        self.assertLess(np.linalg.norm(calc-ref_values)/np.linalg.norm(ref_values), seuil,
                        msg = f"In test_interp/test_onmesh_cyl {calc} expected : {ref_values}")


    def test_interp_two_cyl(self):
        ref_values = np.array([51.98838945910531, 264723649.4209072])
        freq_model_FEM = FrequentialSolver(self.two_cyl_phy, self.f_s, l_ele=0.01, order=5)
        freq_model_FEM.solve(interp=True, interp_grid=0.005)

        calc = np.sum(np.abs(freq_model_FEM.flow)), np.sum(np.abs(freq_model_FEM.pressure))
        self.assertLess(np.linalg.norm(calc-ref_values)/np.linalg.norm(ref_values), seuil,
                        msg = f"In test_interp/test_interp_two_cyl {calc} expected : {ref_values}")



if __name__ == "__main__":
    unittest.main()
