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
error_tot = 0

F1 = 100
F2 = 1000
fs = np.linspace(F1, F2, 10)
temp = 29 # °C

subdiv = 500  # subdiv for TMM with losses


tested_file = parent_path + '/models/test_TMMFEM_file'
ordre = 10
lenEle = 0.09

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
# expected values
# treshAccept = 1e-9
# values = {'adimF,lossF,PH1':3.9470846712861387e-11, 'adimF,lossT,PH1':4.098602094628109e-05,
#           'adimT,lossT,PH1':4.0986021109048974e-05, 'adimT,lossF,PH1':5.581980574303354e-13}


class TestTMMFEM(unittest.TestCase):

    def compute_deviation(self, losses, adim, convention):
        print('\nCurrent test : loss%s, adim %s and convention %s' % ('y' if losses else 'less', adim, convention))
        # state = 'adim%s,loss%s,%sH1' % ('T' if adim else 'F', 'T' if losses else 'F', 'P' if convention == 'PH1' else 'V')

        res_TMM = ImpedanceComputation(fs, tested_file, temperature=temp, losses=losses,
                         compute_method='TMM', nb_sub=subdiv,
                         convention=convention,
                         nondim=adim, discontinuity_mass=False,
                         reff_tmm_losses='integral',
                         radiation_category='planar_piston', **dry_air)
        zTMM = res_TMM.impedance

        res_FEM = ImpedanceComputation(fs, tested_file, temperature=temp, losses=losses,
                         compute_method='FEM', l_ele=lenEle, order=ordre,
                         convention=convention,
                         nondim=adim, discontinuity_mass=False,
                         radiation_category='planar_piston', **dry_air)
        zFEM = res_FEM.impedance

        # *** DEBUG ***
        #plt.semilogy(fs, zTMM, fs, zFEM)
        #while True:
        #    plt.pause(1)

        error = np.linalg.norm(zFEM - zTMM) / np.linalg.norm(zTMM)
        # it is ok that the two computations are different
        # self.assertLess(np.abs(error - values[state]), treshAccept,f"In test_TMMFEM {zFEM} and {zTMM} are too different")
        # delta_error = np.abs(error - values[state])

        # if delta_error > treshAccept:
        #     print('Error: FEM-TMM l2error = %e ; Expected = %e ; Diff = %.2e' % (error, values[state], delta_error))
        #     #error_tot = error_tot + 1
        # else:
        #     print('Passed: FEM-TMM l2error = %.2e ; Expected = %.2e ; Diff = %.2e' % (error, values[state], delta_error))
        # print()
        return error

    def test_TMM_FEM_lossless_adim(self):
        error = self.compute_deviation(False, True, 'PH1')
        self.assertLess(error, 1e-10,f"In lossless, adim, TMM and FEM gives too different results {error}")

    def test_TMM_FEM_lossless_dim(self):
        error = self.compute_deviation(False, False, 'PH1')
        self.assertLess(error, 1e-10,f"In lossless, dim, TMM and FEM gives too different results {error}")

    def test_TMM_FEM_lossy_adim(self):
        error = self.compute_deviation(True, True, 'PH1')
        self.assertLess(error, 1e-7,f"In lossy, adim, TMM and FEM gives too different results {error}")

    def test_TMM_FEM_lossy_dim(self):
        error = self.compute_deviation(True, True, 'PH1')
        self.assertLess(error, 1e-7,f"In lossless, adim, TMM and FEM gives too different results {error}")


if __name__ == "__main__":
    unittest.main()
