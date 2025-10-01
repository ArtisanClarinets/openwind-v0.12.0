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

from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.frequential import FrequentialSolver
from openwind.inversion import InverseFrequentialResponse

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
class Inversion3paramsBounded(unittest.TestCase):
    """
    Test the inversion of 1 params in two cones.
    """

    def __init__(self, *args, **kwargs):
        super(Inversion3paramsBounded, self).__init__(*args, **kwargs)
        self.frequencies = np.linspace(20, 200, 3)
        self.create_targets()
        self.create_physics()

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
        losses = True
        nondim = True
        radiation = 'planar_piston'
        return temperature, losses, nondim, radiation

    def create_targets(self):
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
        target_hole = [[0.05, 3e-3, 3e-3, 'linear']]
        fing_chart = [['label', 'note0', 'note1'],
                      ['hole1', 'x', 'o']]
        lengthElem = 0.01
        order_target = 10

        temperature, losses, nondim, radiation = self.get_options()

        bore_target = InstrumentGeometry(target_geom, target_hole, fing_chart)
        phy_target = InstrumentPhysics(bore_target, temperature, Player(),
                                       losses=losses, nondim=nondim,
                                       radiation_category=radiation, **dry_air)

        freq_target = FrequentialSolver(phy_target, self.frequencies,
                                        note='note0',
                                        l_ele=lengthElem, order=order_target)
        freq_target.solve()
        TARGET = [freq_target.imped/freq_target.get_ZC_adim()]

        freq_target.set_note('note1')
        freq_target.solve()
        TARGET.append(freq_target.imped/freq_target.get_ZC_adim())

        self.targets = TARGET

    def create_physics(self):
        """generate the instruments physics necessary to compute the inverse"""
        initial_geom = [[0, .1, 5e-3, '0<~7e-3', 'linear'],
                        [0.1, '0.1<~0.2<0.5', '0<~7e-3', 5e-3, 'linear']]
        initial_hole = [[0.05, 3e-3, '~2e-3%', 'linear']]
        fing_chart = [['label', 'note0', 'note1'],
                      ['hole1', 'x', 'o']]

        temperature, losses, nondim, radiation = self.get_options()

        bore_modif = InstrumentGeometry(initial_geom, initial_hole, fing_chart)
        self.phy_modif = InstrumentPhysics(bore_modif, temperature, Player(),
                                           losses=losses, nondim=nondim,
                                           radiation_category=radiation, **dry_air)

    def create_inverse(self):
        """Generate the inverse problem"""
        order_optim = 8
        lengthElem = 0.01

        inverse = InverseFrequentialResponse(self.phy_modif, self.frequencies,
                                             self.targets,
                                             notes=['note0', 'note1'],
                                             observable='impedance',
                                             l_ele=lengthElem,
                                             order=order_optim)
        return inverse

    def compute_grad_gradient(self, expected_val):
        """
        Test the coherence between the three gradient compuation

        (finite-difference, frechet and adjoint-state methods)
        """
        inverse = self.create_inverse()
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

    def valide_algo(self, algo, n_iter, tol_cost=1e-10, tol_params=1e-8,
                    tol_iter=1):
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
        stop_cost = 0
        stop_params = [5e-3, 25e-2, .6]
        start_cost = 0.12731324042823186

        inverse = self.create_inverse()

        res = inverse.optimize_freq_model(algorithm=algo, iter_detailed=False)

        self.assertTrue(np.allclose(res.x, stop_params,
                                    rtol=tol_params, atol=1e-14),
                        msg='The ending param are wrong: {} vs'
                        ' {}'.format(res.x.tolist(), stop_params))

        self.assertTrue(np.isclose(res.cost_evol[0], start_cost, rtol=tol_cost,
                                   atol=1e-16),
                        msg='The initial cost is wrong: {} vs '
                        '{}'.format(res.cost_evol[0], start_cost))

        self.assertLess(stop_cost, tol_cost, msg='The ending cost is wrong: '
                        '{} vs {}'.format(res.cost, stop_cost))

        msg_iter = ('The number of iterations is wrong: '
                    '{} vs {}'.format(res.nit, n_iter))
        self.assertLessEqual(np.abs(res.nit - n_iter), tol_iter,
                             msg=msg_iter)

    def test_grad(self):
        expect = [29.06346411721491, -1.8439794613683365, -0.07403202870742899]
        self.compute_grad_gradient(expect)

    def test_trust_constr(self):
        """Test the scipy 'trust-constr' algorithm"""
        n_iter = 26
        self.valide_algo('trust-constr', n_iter, tol_params=1e-3)

    def test_trf(self):
        """Test the scipy trf algorithm"""
        n_iter = 8
        self.valide_algo('trf', n_iter)

    def test_BFGS(self):
        """Test the scipy 'L-BFGS-B' algorithm"""
        self.skipTest("Redondant with 'trust-constr' ")
        n_iter = 28
        self.valide_algo('L-BFGS-B', n_iter, tol_params=1e-3)

    def test_SLSQP(self):
        """Test the scipy 'SLSQP' algorithm"""
        self.skipTest("Redondant with 'trust-constr' ")
        n_iter = 15
        self.valide_algo('SLSQP', n_iter, tol_params=1e-3)

    def test_dogbox(self):
        """Test the scipy dogbox algorithm"""
        self.skipTest("Redondant with trf")
        n_iter = 8
        self.valide_algo('dogbox', n_iter, tol_params=1e-9)


if __name__ == '__main__':
    unittest.main()
