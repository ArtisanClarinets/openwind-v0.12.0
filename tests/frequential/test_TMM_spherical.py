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
from pathlib import Path

from openwind import ImpedanceComputation

parent_path = str(Path(__file__).parent.absolute().parent)


fs = [1000]
temp = 29 # °C
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
subdiv = 1  # subdiv for TMM with losses


tested_file = parent_path + '/models/test_TMMFEM_file'

# expected values
treshAccept = 1e-12
values = {'lossF,sphF' : 3.735725386116687e+05-9.504435211563468e+06j,
          'lossF,sphT' : 3.691058559993285e+05-9.469006435801834e+06j,
          'lossF,sphT+A' : 3.689418038469621e+05-9.466966394337203e+06j,
          'lossT,sphF' : 1.446064471151116e+06-7.985034706586331e+06j,
          'lossT,sphT' : 1.436746164524287e+06-7.960037935906338e+06j,
          'lossT,sphT+A' : 1.436266664858311e+06-7.958590624850368e+06j,
          }

class TestTMMFEM_spherical(unittest.TestCase):

    def compute_TMM(self, losses, adim, spherical):
        convention = 'PH1'
        state = 'loss%s,sph%s' % (
            # 'T' if adim else 'F',
            'T' if losses else 'F',
            # 'P' if convention == 'PH1' else 'V',
            'T+A' if spherical == 'spherical_area_corr' else 'T' if spherical else 'F')
        res_TMM = ImpedanceComputation(fs, tested_file, temperature=temp, losses=losses,
                                       compute_method='TMM', nb_sub=subdiv,
                                       convention=convention,
                                       nondim=adim,
                                       spherical_waves=spherical,
                                       **dry_air,
                                       )
        zTMM = res_TMM.impedance[0]

        # print(f" '{state}' : {zTMM:.15e},")

        error = np.linalg.norm(zTMM - values[state])/np.linalg.norm(values[state])
        return error

    # %% lossy adim
    def test_lossy_adim_sph(self):
        error = self.compute_TMM(True, True, True)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")


    def test_lossy_adim_plane(self):
        error = self.compute_TMM(True, True, False)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossy_adim_sphCorr(self):
        error = self.compute_TMM(True, True, 'spherical_area_corr')
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    # %% lossy dim
    def test_lossy_dim_sph(self):
        error = self.compute_TMM(True, False, True)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossy_dim_plane(self):
        error = self.compute_TMM(True, False, False)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossy_dim_sphCorr(self):
        error = self.compute_TMM(True, False, 'spherical_area_corr')
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    # %% lossy adim
    def test_lossless_adim_sph(self):
        error = self.compute_TMM(False, True, True)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossless_adim_plane(self):
        error = self.compute_TMM(False, True, False)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossless_adim_sphCorr(self):
        error = self.compute_TMM(False, True, 'spherical_area_corr')
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    # %% lossless dim
    def test_lossless_dim_sph(self):
        error = self.compute_TMM(False, False, True)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossless_dim_plane(self):
        error = self.compute_TMM(False, False, False)
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")

    def test_lossless_dim_sphCorr(self):
        error = self.compute_TMM(False, False, 'spherical_area_corr')
        self.assertLess(error, treshAccept,f"TMM computation not consistent with previous results: {error}")


if __name__ == "__main__":
    unittest.main()
