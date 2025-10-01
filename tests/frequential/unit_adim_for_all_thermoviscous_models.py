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

frequencies = np.array([2000])
temperature = 25
ordre = 1
lenEle = 0.07

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

tested_geom = [[0, 1e-3],
               [0.1, 6e-3],
               #[0.22, 8e-3]
               ]
ref = dict()
ref[False] = [131738.82809993+26252614.69909799j]
ref[True]  = [1639914.05106229+27740144.44861637j]
ref['diffrepr'] = [1639599.2405805+27735602.44588989j]
ref['diffrepr+'] = [1639599.24058048+27735602.44588998j]

class TestThermoviscous(unittest.TestCase):

    # for losses in [False, True, 'diffrepr', 'diffrepr+']:
    def launch_vt_loss(self, losses):
        print("Test adim vs non-adim. losses =", losses)
        result_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                 l_ele=lenEle, order=ordre, losses=losses,
                                 nondim=True, **dry_air)

        result_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                              l_ele=lenEle, order=ordre, losses=losses,
                              nondim=False, **dry_air)

        err = np.linalg.norm(result_nondim.impedance - result_dim.impedance) / np.linalg.norm(result_dim.impedance)
        self.assertLess(err, 1e-12, 'Adim/non-adim give different results (but shouldn t) : err = {:.3e}'.format(err))

        err_dim = np.linalg.norm(result_dim.impedance - ref[losses]) / np.linalg.norm(ref[losses])
        self.assertLess(err_dim, 1e-12, msg=f"Dim computation for thermoviscous models failed for {losses}")

        err_nondim = np.linalg.norm(result_nondim.impedance - ref[losses]) / np.linalg.norm(ref[losses])
        self.assertLess(err_nondim, 1e-12, msg=f"Adim computation for thermoviscous models failed for {losses}")

    def test_vt_false(self):
        self.launch_vt_loss(False)


    def test_vt_true(self):
        self.launch_vt_loss(True)


    def test_vt_diffrepr(self):
        self.launch_vt_loss('diffrepr')


    def test_vt_diffrepr_plus(self):
        self.launch_vt_loss('diffrepr+')



if __name__ == "__main__":
    unittest.main()
