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
class Inversion1paramUnbounded(unittest.TestCase):
    """
    Test the inversion of 1 params in two cones.
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
        temperature = 20
        radiation = 'planar_piston'
        nondim = True
        return temperature, nondim, radiation

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
        target_geom = [[0, .1, 5e-3, 5e-3, 'linear'],
                       [0.1, .25, 5e-3, 5e-3, 'linear']]
        target_hole = []
        lengthElem = 0.05
        order_target = 8

        noise_ratio = 0

        temperature, nondim, radiation = self.get_options()

        bore_target = InstrumentGeometry(target_geom, target_hole)
        phy_target = InstrumentPhysics(bore_target, temperature, Player(),
                                       losses=True, nondim=nondim,
                                       radiation_category=radiation, **dry_air)

        freq_target = FrequentialSolver(phy_target, frequencies,
                                        l_ele=lengthElem, order=order_target)
        freq_target.solve()
        TARGET = freq_target.imped/freq_target.get_ZC_adim()

        # Noise
        TARGET = TARGET + noise_ratio*TARGET*np.random.randn(len(TARGET))
        return TARGET

    def creat_inverse(self, losses=True):
        """Generate the inverse problem"""
        observable = 'impedance'
        initial_geom = [[0, .1, 5e-3, '5e-3', 'linear'],
                        [0.1, .25, '5e-3', '~4.5e-3', 'linear']]
        initial_hole = []
        order_optim = 6
        lengthElem = 0.05

        frequencies = np.array([50])

        targets = self.creat_targets(frequencies)

        temperature, nondim, radiation = self.get_options()

        bore_modif = InstrumentGeometry(initial_geom, initial_hole)
        phy_modif = InstrumentPhysics(bore_modif, temperature, Player(),
                                      losses=losses, nondim=nondim,
                                      radiation_category=radiation, **dry_air)
        inverse = InverseFrequentialResponse(phy_modif, frequencies, targets,
                                             observable=observable,
                                             l_ele=lengthElem,
                                             order=order_optim)
        return inverse

    def compute_grad_gradient(self, losses, expected_val):
        """
        Test the coherence between the three gradient compuation

        (finite-difference, frechet and adjoint-state methods)
        """
        inverse = self.creat_inverse(losses)
        GradAdj = inverse.get_cost_grad_hessian([], grad_type='adjoint')[1]
        GradFrech = inverse.get_cost_grad_hessian([], grad_type='frechet')[1]

        stepsize = 1e-6
        GradStep = inverse.get_cost_grad_hessian([], grad_type='finite diff',
                                                 stepSize=stepsize)[1]

        err = np.abs((GradAdj - GradFrech)/GradFrech)
        msgAF = ('\nAdjoint and Frechet method give different result:'
                 '\n  {}'.format(err))
        self.assertTrue(np.allclose(GradAdj, GradFrech, rtol=1e-12,
                                    atol=1e-14), msg=msgAF)

        errSF = np.abs((GradStep - GradFrech)/GradFrech)
        msgSF = ('\nFinite-diff and Frechet method give different '
                 'result:\n  {}'.format(errSF))
        self.assertTrue(np.allclose(GradStep, GradFrech, rtol=1e-6,
                                    atol=1e-14), msg=msgSF)

        msgF = ('\nFrechet method give wrong result:\n  {} vs '
                '{}'.format(GradFrech.tolist(), expected_val))
        self.assertTrue(np.allclose(GradFrech, expected_val, rtol=1e-10,
                                    atol=1e-14), msg=msgF)

    def test_grad_nolosses(self):
        self.skipTest('redondant with gradient computation test')
        self.compute_grad_gradient(False, -1.014102047416502)

    def test_grad_ZK(self):
        self.compute_grad_gradient(True, -1.162576978058976e+01)

    def test_grad_keefe(self):
        self.skipTest('redondant with gradient computation test')
        self.compute_grad_gradient('keefe', -1.167140404290028e+01)

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
                                   atol=1e-16),
                        msg='The initial cost is wrong: {} vs '
                        '{}'.format(res.cost_evol[0], start_cost))

        self.assertTrue(np.isclose(stop_cost, res.cost, rtol=tol_cost,
                                   atol=1e-16),
                        msg='The ending cost is wrong: {} vs '
                        '{}'.format(res.cost, stop_cost))

        self.assertTrue(np.allclose(res.x, stop_params,
                                    rtol=tol_params, atol=1e-16),
                        msg='The ending param are wrong: {} vs'
                        ' {}'.format(res.x, stop_params))

        msg_iter = ('The number of iterations is wrong: '
                    '{} vs {}'.format(res.nit, n_iter))
        self.assertLessEqual(np.abs(res.nit - n_iter), tol_iter,
                             msg=msg_iter)

    def test_LM(self):
        """Test the home-made LM algorithm"""
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 4
        self.valide_algo('LM', start_cost, stop_cost, stop_params, n_iter)

    def test_BFGS(self):
        """Test the scipy BFGS algorithm"""
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 6
        self.valide_algo('BFGS', start_cost, stop_cost, stop_params, n_iter)

    def test_lm(self):
        """Test the scipy lm algorithm"""
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 6
        self.valide_algo('lm', start_cost, stop_cost, stop_params,
                         n_iter)

    def test_trf(self):
        """Test the scipy trf algorithm"""
        self.skipTest("Redondant with lm")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 5
        self.valide_algo('trf', start_cost, stop_cost, stop_params,
                         n_iter)

    def test_GN(self):
        """Test the home-made GN algorithm"""
        self.skipTest("Redondant with LM")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 4
        self.valide_algo('GN', start_cost, stop_cost, stop_params, n_iter)

    def test_QN(self):
        """Test the home-made QN algorithm"""
        self.skipTest("Redondant with BFGS")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 6
        self.valide_algo('QN', start_cost, stop_cost, stop_params, n_iter)

    def test_steepest(self):
        """Test the home-made steepest algorithm"""
        self.skipTest("Redondant with BFGS")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 30
        self.valide_algo('steepest', start_cost, stop_cost, stop_params,
                         n_iter)

    def test_NewtonCG(self):
        """Test the scipy Newton-CG algorithm"""
        self.skipTest("Redondant with BGFS")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 4
        self.valide_algo('Newton-CG', start_cost, stop_cost, stop_params,
                         n_iter)

    def test_dogbox(self):
        """Test the scipy dogbox algorithm"""
        self.skipTest("Redondant with trf")
        start_cost = 0.0026005946965617574
        stop_cost = 0
        stop_params = [0.005]
        n_iter = 5
        self.valide_algo('dogbox', start_cost, stop_cost, stop_params,
                         n_iter)


if __name__ == '__main__':
    unittest.main()
