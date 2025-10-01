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

import unittest

import numpy as np
np.random.seed(0) # seed the PRNG for reproducibility

from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.frequential import FrequentialSolver
from openwind.inversion import InverseFrequentialResponse

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
class InversionDiscontinuity(unittest.TestCase):
    """
    Test the inversion of cross-section discontinuity without constraint.
    """

    def get_options(self):
        """
        Fix the computation options similar for target and inverse problem.

        Returns
        -------
        temperature : float
            The temperature.
        losses : string, boolean
            The losses type.
        nondim : boolean
            Scaling the equations.
        radiation : string
            The type of radiation condition.

        """
        radiation = 'planar_piston'
        losses = True
        nondim = True
        temperature = 20
        return temperature, losses, nondim, radiation

    def creat_targets(self, frequencies):
        """
        Create the targets

        Parameters
        ----------
        frequencies : array

        Returns
        -------
        TARGET : array
            the target impedance

        """
        target_geom = [[0, 0.1, 5e-3, 5e-3, 'linear'],
                       [0.1, 0.2, 8e-3, 10e-3, 'linear']]
        target_hole = []
        lengthElem = 0.05
        order_target = 8

        noise_ratio = 0

        temperature, losses, nondim, radiation = self.get_options()

        bore_target = InstrumentGeometry(target_geom, target_hole)
        phy_target = InstrumentPhysics(bore_target, temperature, Player(),
                                       losses=losses, nondim=nondim,
                                       radiation_category=radiation, **dry_air)

        freq_target = FrequentialSolver(phy_target, frequencies,
                                        l_ele=lengthElem, order=order_target)
        freq_target.solve()
        TARGET = freq_target.imped/freq_target.get_ZC_adim()

        # Noise
        TARGET = TARGET + noise_ratio*TARGET*np.random.randn(len(TARGET))
        return TARGET

    def creat_inverse(self):
        """Generate the inverse problem"""
        observable = 'impedance'
        initial_geom = [[0, 0.1, 5e-3, '~5e-3', 'linear'],
                        [0.1, 0.2, '~10e-3', 10e-3, 'linear']]
        initial_hole = []
        order_optim = 6
        lengthElem = 0.05

        frequencies = np.array([50])

        targets = self.creat_targets(frequencies)

        temperature, losses, nondim, radiation = self.get_options()

        bore_modif = InstrumentGeometry(initial_geom, initial_hole)
        phy_modif = InstrumentPhysics(bore_modif, temperature, Player(),
                                      losses=losses, nondim=nondim,
                                      radiation_category=radiation, **dry_air)
        inverse = InverseFrequentialResponse(phy_modif, frequencies, targets,
                                             observable=observable,
                                             l_ele=lengthElem,
                                             order=order_optim)
        return inverse

    def test_gradient(self):
        """
        Test the coherence between the three gradient compuation

        (finite-difference, frechet and adjoint-state methods)
        """
        inverse = self.creat_inverse()
        GradAdj = inverse.get_cost_grad_hessian([], grad_type='adjoint')[1]
        GradFrech = inverse.get_cost_grad_hessian([], grad_type='frechet')[1]

        stepsize = 1e-8
        GradStep = inverse.get_cost_grad_hessian([], grad_type='finite diff',
                                                 stepSize=stepsize)[1]

        msgAF = ('Adjoint and Frechet method give different result:\n '
                 '{}'.format(np.abs(GradAdj-GradFrech)/GradFrech))
        self.assertTrue(np.allclose(GradAdj, GradFrech, rtol=1e-10,
                                    atol=1e-14), msg=msgAF)
        msgSF = ('Finite-diff and Frechet method give different result:\n '
                 '{}'.format(np.abs(GradStep-GradFrech)/GradFrech))
        self.assertTrue(np.allclose(GradStep, GradFrech, rtol=1e-8,
                                    atol=1e-14), msg=msgSF)

        expected_val = [6.868041101964790e+00, 7.275297302321262e-01]
        msgF = ('Frechet method give wrong result:\n  {} vs '
                '{}'.format(GradFrech, expected_val))
        self.assertTrue(np.allclose(GradFrech, expected_val, rtol=1e-10,
                                    atol=1e-14), msg=msgF)

    def valide_algo(self, algo, start_cost, stop_cost, stop_params, n_iter,
                    tol_cost=1e-10, tol_params=1e-6, tol_iter=1):
        """
        Test the inversion

        Parameters
        ----------
        algo : string
            The algorithm tested
        start_cost : float
            The expected initial cost value.
        stop_cost : float
            The expected ending cost value.
        stop_params : list(float)
            The expected final param values.
        n_iter : int
            The expected number of function evaluation.
        tol_cost : float, optional
            The deviation tolerance on costs. The default is 1e-10.
        tol_params : float, optional
            The deviation tolerance on param. The default is 1e-6.
        tol_iter : float, optional
            The deviation tolerance on iteration. The default is 1.
        """
        inverse = self.creat_inverse()

        res = inverse.optimize_freq_model(algorithm=algo)

        self.assertTrue(np.isclose(res.cost_evol[0], start_cost, rtol=tol_cost,
                                   atol=1e-15),
                        msg='The initial cost is wrong: {} vs '
                        '{}'.format(res.cost_evol[0], start_cost))

        self.assertTrue(np.isclose(stop_cost, res.cost, rtol=tol_cost,
                                   atol=1e-15),
                        msg='The ending cost is wrong: {} vs '
                        '{}'.format(res.cost, stop_cost))

        self.assertTrue(np.allclose(res.x, stop_params,
                                    rtol=tol_params, atol=1e-15),
                        msg='The ending param are wrong: {} vs'
                        ' {}'.format(res.x, stop_params))

        msg_iter = ('The number of iterations is wrong: '
                    '{} vs {}'.format(res.nit, n_iter))
        self.assertLessEqual(np.abs(res.nit - n_iter), tol_iter,
                             msg=msg_iter)

    def test_LM(self):
        """Test the home-made LM algorithm"""
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 2.3449422965732076e-18
        stop_params = [0.005, 0.008]
        n_iter = 13
        self.valide_algo('LM', start_cost, stop_cost, stop_params, n_iter)

    def test_BFGS(self):
        """Test the scipy BFGS algorithm"""
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 4.171812426772785e-20
        stop_params = [0.005, 0.008]
        n_iter = 29
        self.valide_algo('BFGS', start_cost, stop_cost, stop_params, n_iter)

    def test_trf(self):
        """Test the scipy trf algorithm"""
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 7.006182232227659e-28
        stop_params = [0.005, 0.008]
        n_iter = 5
        self.valide_algo('trf', start_cost, stop_cost, stop_params,
                         n_iter)

    def test_GN(self):
        """Test the home-made GN algorithm"""
        self.skipTest("Redondant with LM")
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 6.770758886774151e-28
        stop_params = [0.005, 0.008]
        n_iter = 4
        self.valide_algo('GN', start_cost, stop_cost, stop_params, n_iter)

    def test_QN(self):
        """Test the home-made QN algorithm"""
        self.skipTest("Redondant with BFGS")
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 5.02229936207779e-23
        stop_params = [0.005, 0.008]
        n_iter = 21
        self.valide_algo('QN', start_cost, stop_cost, stop_params, n_iter)

    def test_dogbox(self):
        """Test the scipy dogbox algorithm"""
        self.skipTest("Redondant with trf")
        start_cost = 0.0009186128021806313
        stop_cost = 0  # 6.927255481446417e-28
        stop_params = [0.005, 0.008]
        n_iter = 5
        self.valide_algo('dogbox', start_cost, stop_cost, stop_params,
                         n_iter)


if __name__ == '__main__':
    unittest.main()
