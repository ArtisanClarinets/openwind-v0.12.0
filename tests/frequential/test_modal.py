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

options = dict(temperature=25, l_ele=0.1, order=5)
class TestNewLosses(unittest.TestCase):


    def test_modal_simple_cyl_lossless(self):
        """
        Modal computation and direct computation should coincide exactly on lossless cylinder.
        """
        shape = [[0,1e-3],[0.2,1e-3]]
        fs = [300]

        res_direct = ImpedanceComputation(fs, shape, radiation_category='unflanged', losses=False, compute_method='FEM', **options)
        res_modal  = ImpedanceComputation(fs, shape, radiation_category='unflanged', losses=False, compute_method='modal', use_rad1dof=True, **options)
        err = np.abs(res_direct.impedance - res_modal.impedance) / np.abs(res_direct.impedance)
        self.assertLess(np.max(err), 1e-10)

    def test_modal_simple_cyl(self):
        """
        Modal computation and direct computation should coincide exactly on lossy cylinder with several radiation categories.
        """
        shape = [[0,1e-3],[0.2,1e-3]]
        fs = [50,200,2000]

        rad_cats = ['planar_piston', 'unflanged', 'infinite_flanged',
                    'closed', 'perfectly_open']

        for rad_cat in rad_cats:
            res_direct = ImpedanceComputation(fs, shape, radiation_category=rad_cat, losses='diffrepr', compute_method='FEM', **options)
            res_modal  = ImpedanceComputation(fs, shape, radiation_category=rad_cat, losses='diffrepr', compute_method='modal', use_rad1dof=True, **options)
            err = np.abs(res_direct.impedance - res_modal.impedance) / np.abs(res_direct.impedance)
            self.assertLess(np.max(err), 1e-10)


    def test_modal_cyl_junc(self):
        """
        Modal computation and direct computation should coincide exactly on lossy cylinder cut in half.
        """
        shape = [[0,1e-3],[0.1, 1e-3],[0.2,1e-3]]
        fs = [50,200,2000]
        res_direct = ImpedanceComputation(fs, shape, losses='diffrepr', compute_method='FEM', **options)
        res_modal  = ImpedanceComputation(fs, shape, losses='diffrepr', compute_method='modal', use_rad1dof=True, **options)

        err = np.abs(res_direct.impedance - res_modal.impedance) / np.abs(res_direct.impedance)
        self.assertLess(np.max(err), 1e-10)


    def test_modal_wood(self):
        """
        Modal computation and direct computation should coincide exactly on lossy instrument with holes and junctions.
        """
        shape = [[0,1e-2],[0.1, 3e-2],[0.2,1e-2]]
        holes = [['variety',  'label',  'position',  'radius',   'length'],
                 ['hole',     'hole1',  0.05,         3e-3,       0.11],
                 ['hole',     'hole2',  0.12,         5e-3,       0.07],
                 ['hole',     'hole3',  0.18,         2e-3,       0.22],]
        fs = [50,200,2000]
        res_direct = ImpedanceComputation(fs, shape, holes, losses='diffrepr', compute_method='FEM', **options)
        res_modal  = ImpedanceComputation(fs, shape, holes, losses='diffrepr', compute_method='modal', use_rad1dof=True, **options)

        err = np.abs(res_direct.impedance - res_modal.impedance) / np.abs(res_direct.impedance)
        self.assertLess(np.max(err), 1e-10)

    def test_modal_valves(self):
        """
        Modal computation and direct computation should coincide exactly on lossy instrument with valves and junctions.
        """
        shape = [[0,3e-3],[0.1, 3e-3],[0.2,5e-3]]
        holes = [['variety',  'label',  'position', 'reconnection',  'radius',   'length'],
                ['valve',    'piston1',  0.05,        .07,           2e-3,       0.02],
                ['valve',    'piston2',  0.12,        .14,           3e-3,       0.07]]

        fs = [50,200,2000]
        res_direct = ImpedanceComputation(fs, shape, holes, spherical_waves=True, losses='diffrepr', compute_method='FEM', **options)
        res_modal  = ImpedanceComputation(fs, shape, holes, spherical_waves=True, losses='diffrepr', compute_method='modal', use_rad1dof=True, **options)

        err = np.abs(res_direct.impedance - res_modal.impedance) / np.abs(res_direct.impedance)
        self.assertLess(np.max(err), 1e-10)

    def test_modal_regression(self):
        """
        Check that the results of modal computation do not change
        significantly during an update.
        """
        shape = [[0,1e-3],[0.2,3e-3]]
        fs = [50,200,2000]
        old_result = np.array([
                2.3166647639051154e+06+9.5054405809479430e+06j,
                4.4977292836323399e+06+3.7478338064532593e+07j,
                5.3419764256932028e+07+1.8512385280883744e+08j])
        res = ImpedanceComputation(fs, shape,
                                   humidity=0, carbon=0,
                                   ref_phy_coef='Chaigne_Kergomard',
                                   losses='diffrepr',
                                   compute_method='modal', use_rad1dof=True, **options)

        err = np.abs(old_result - res.impedance) / np.abs(old_result)
        self.assertLess(np.max(err), 1e-10)
        old_f = [ 606.355702838236 , 1213.5017137128402, 1357.2275987981639,
               2169.6864125978454, 3001.6934963487643]
        old_Q = [15.22742913164018  ,  0.5000010261617428, 20.38291187210939  ,
               25.291943529406087 , 29.53752343813481  ]
        old_Z = [8.403219306638292e+08+1.7882579319851413e+07j,
               5.097689236190434e+07+2.1182174519316515e+08j,
               8.782055969218820e+08+2.0487710806640670e+07j,
               7.703517170162202e+08+1.7333127897759173e+07j,
               6.695672959724513e+08+1.5152874549209984e+07j]
        (f,Q,Z) = res.resonance_peaks()
        err_f = np.abs(old_f - f) / np.abs(old_f)
        err_Q = np.abs(old_Q - Q) / np.abs(old_Q)
        err_Z = np.abs(old_Z - Z) / np.abs(old_Z)
        self.assertLess(np.max(err_f), 1e-10)
        self.assertLess(np.max(err_Q), 1e-10)
        self.assertLess(np.max(err_Z), 1e-10)



if __name__ == "__main__":
    unittest.main()
