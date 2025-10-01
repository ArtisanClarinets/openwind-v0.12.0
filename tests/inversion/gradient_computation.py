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
from openwind.inversion import InverseFrequentialResponse

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
class GradientComputation(unittest.TestCase):
    """
    Test gradient computation for all physics possible options
    """

    def create_inverse_geom_complex(self,):
        """Generate an inverse problem for complex geometry"""
        observable = 'impedance'
        initial_geom = [[0, '~0.1', 5e-3, '0<~8e-3<0.1', 'linear'],
                        ['~0.1', '~0.12', '0<~8e-3<0.1', '~15e-3', 'circle', '~0.05'],
                        ['~0.12', '~0.3', '0<~5e-3<0.1', '0<~30e-3', 'exponential'],
                        ['~0.3', '~0.4', '30e-3', '~10e-3', 'spline', '~0.32', '~20e-3'],
                        ['~0.4', '~0.45', '~10e-3', '~30e-3', 'bessel', '~0.8']
                        ]
        initial_hole = [['label', 'position', 'type', 'radius', 'chimney'],
                        ['h1', '~0.05%', 'linear', '~3e-3', '5e-3'],
                        ['h2', '~0.17', 'linear', '5e-3', '5e-3'],
                        ['h3', '~0.25', 'linear', '~15e-3%', '3e-3<~7e-3'],
                        ]

        order_optim = 10
        lengthElem = 0.01

        frequencies = np.array([500])
        targets = [np.ones_like(frequencies)]

        bore_modif = InstrumentGeometry(initial_geom, initial_hole)
        phy_modif = InstrumentPhysics(bore_modif, 20, Player(),
                                      losses=False, **dry_air)
        inverse = InverseFrequentialResponse(phy_modif, frequencies, targets,
                                             observable=observable,
                                             l_ele=lengthElem,
                                             order=order_optim)
        return inverse

    def compute_grad_gradient_geom_complex(self, expected_val):
        """
        Test the coherence between the three gradient compuation

        (finite-difference, frechet and adjoint-state methods)
        """
        inverse = self.create_inverse_geom_complex()
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
                                    atol=1e-6), msg=msgSF)

        msgF = ('\nFrechet method give wrong result:\n  {} vs '
                '{}'.format(GradFrech.tolist(), expected_val))
        self.assertTrue(np.allclose(GradFrech, expected_val, rtol=1e-10,
                                    atol=1e-14), msg=msgF)

    def create_inverse(self, temperature=20, losses=True,
                       radiation="unflanged", nondim=False,
                       spherical_waves=False, discontinuity_mass=True,
                       matching_volume=False):
        """Generate an inverse problem with simplier geometry"""
        observable = 'impedance'
        initial_geom = [[0, '~0.1', 5e-3, '0<~8e-3<0.1', 'linear'],
                        ['~0.1', 0.3, '0<~5e-3<0.1', '0<~30e-3', 'exponential'],
                        ]
        initial_hole = [['label', 'position', 'type', 'radius', 'chimney'],
                        ['h1', '~0.05%', 'linear', '~3e-3', '5e-3'],
                        ['h2', '0.25', 'linear', '~15e-3%', '3e-3<~7e-3']
                        ]

        order_optim = 5
        lengthElem = 0.01

        frequencies = np.array([500])
        targets = [np.ones_like(frequencies)]

        bore_modif = InstrumentGeometry(initial_geom, initial_hole)
        phy_modif = InstrumentPhysics(bore_modif, temperature, Player(),
                                      losses=losses,
                                      radiation_category=radiation,
                                      nondim=nondim,
                                      spherical_waves=spherical_waves,
                                      discontinuity_mass=discontinuity_mass,
                                      matching_volume=matching_volume, **dry_air)
        inverse = InverseFrequentialResponse(phy_modif, frequencies, targets,
                                             observable=observable,
                                             l_ele=lengthElem,
                                             order=order_optim)
        return inverse

    def grad_temp(self, x):
        return x/0.3*(40 - 20) + 20

    def compute_grad_gradient(self, expected_val, temperature=20, losses=True,
                              radiation="unflanged", nondim=False,
                              spherical_waves=False, discontinuity_mass=True,
                              matching_volume=False):
        """
        Test the coherence between the three gradient compuation

        (finite-difference, frechet and adjoint-state methods)
        """
        inverse = self.create_inverse(temperature, losses,
                                      radiation, nondim,
                                      spherical_waves, discontinuity_mass,
                                      matching_volume)
        GradAdj = inverse.get_cost_grad_hessian([], grad_type='adjoint')[1]
        GradFrech = inverse.get_cost_grad_hessian([], grad_type='frechet')[1]

        stepsize = 1e-7
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
                                    atol=1e-7), msg=msgSF)

        msgF = ('\nFrechet method give wrong result:\n  {} vs '
                '{}'.format(GradFrech.tolist(), expected_val))
        self.assertTrue(np.allclose(GradFrech, expected_val, rtol=1e-10,
                                    atol=1e-14), msg=msgF)

    def test_nolosses(self):
        expect = [2.9798765659158297, -9.648090106568716, 0.32372016077333415,
                  2.0194846159386395, 0.057512946366195535,
                  -18.142141253813133, 0.15912130207950095,
                  -0.4906840108816664, 0.008224728929649204,
                  0.018307686315737592, 0.0032424729268330905,
                  -0.03591180928121167, 0.0024447905155222755,
                  -0.0016702123743510332, -2.763943583344716e-05,
                  0.5688223397513075, -111.05461523853006, 0.6503259425602994,
                  -0.005130746118976072, 0.10323417746773718,
                  -0.0049518116611340784]
        self.compute_grad_gradient_geom_complex(expect)

    def test_ZKlosses(self):
        expect = [3.6995737374485365, -11.94145476936986, -11.566585185738173,
                  -0.9700764424566369, 0.5647434510649036, -105.41061451002298,
                  0.07113426582479268, -0.004276705674644918]
        self.compute_grad_gradient(expect, losses=True)

    def test_keefelosses(self):
        expect = [3.69974324463557, -11.941405060512501, -11.568171058972606,
                  -0.9701963792138515, 0.5647640714191939,
                  -105.42883952329743, 0.07114269428186337,
                  -0.004277207621028083]
        self.compute_grad_gradient(expect, losses='keefe')

    def test_nondim(self):
        expect = [3.6995737374485365, -11.94145476936986, -11.566585185738173,
                  -0.9700764424566369, 0.5647434510649036, -105.41061451002298,
                  0.07113426582479268, -0.004276705674644918]
        self.compute_grad_gradient(expect, nondim=True)

    def test_spherical(self):
        expect = [3.7055787039678685, -11.781386283797639, -11.54640563071219,
                  -0.9597920806373029, 0.5662066264778637, -105.90763771268131,
                  0.0734378175075337, -0.004393616739876231]
        self.compute_grad_gradient(expect, spherical_waves=True)

    def test_discontinuity(self):
        expect = [3.68284577863217, -12.254964012274856, -11.251904610883287,
                  -0.9816198622643563, 0.5630831214301681,
                  -104.53356557780515, 0.07197997870545557,
                  -0.004327584956016528]
        self.compute_grad_gradient(expect, discontinuity_mass=False)

    def test_matchingvolume(self):
        expect = [3.7653072148654685, -12.039193043234423,
                  -12.162719545495326, -1.0281588889697024,
                  0.5715220692619424, -106.7684970878295,
                  0.07049814781007213, -0.004274129642534086]
        self.compute_grad_gradient(expect, matching_volume=True)

    def test_gradtemp(self):
        expect = 0
        self.assertRaises(ValueError, self.compute_grad_gradient, expect,
                          temperature=self.grad_temp)

    def test_rad_flanged(self):
        expect = [3.9334063819801477, -11.168760814176995, -13.769751644781518,
                  -1.1740598414879158, 0.5955026788270903, -115.19512102084501,
                  0.08110924253256505, -0.0052564626117144264]
        self.compute_grad_gradient(expect, radiation='infinite_flanged')

    def test_rad_piston(self):
        expect = [3.9632271180319028, -11.05021733178928, -14.057867426056092,
                  -1.201489892902094, 0.5993889462170912, -116.44238709478307,
                  0.08267390728437621, -0.005399183561117772]
        self.compute_grad_gradient(expect, radiation='planar_piston')

    def test_rad_2ndorder(self):
        expect = [3.6993134559764744, -11.94212443809095, -11.56355576115068,
                  -0.9698378024645327, 0.5647109356078927, -105.39935024945224,
                  0.07113683863065279, -0.004275714172331692]
        self.compute_grad_gradient(expect, radiation='unflanged_2nd_order')

    def test_rad_non_causal(self):
        expect = [3.6996712995865355, -11.940663252999665, -11.565877195168015,
                  -0.9699995763651732, 0.5647611932473457, -105.4158317161555,
                  0.07121438181581116, -0.004278834953862912]
        self.compute_grad_gradient(expect, radiation='unflanged_non_causal')

    def test_rad_open(self):
        expect = [3.083700332091061, -13.321658236670343, -6.433919487278534,
                  -0.511126999759342, 0.4809895613954844, -79.92751964357292,
                  0.04696131985413852, -0.00215455775355673]
        self.compute_grad_gradient(expect, radiation='perfectly_open')

    def test_rad_sphere(self):
        expect = 0
        self.assertRaises(NotImplementedError, self.compute_grad_gradient,
                          expect, radiation=('pulsating_sphere', np.pi/2))

    def test_rad_data(self):
        expect = 0
        data = (np.linspace(100, 2000, 10), np.ones(10)+0j)
        self.assertRaises(NotImplementedError, self.compute_grad_gradient,
                          expect, radiation=('from_data', (data, 20, 1e-2)))

    def test_variable_input(self):
        frequencies = np.array([500])
        targets = [np.ones_like(frequencies)]

        bore_modif = InstrumentGeometry([[0, 0.5, '~0.5', .5, 'linear']])
        phy_modif = InstrumentPhysics(bore_modif, 25, Player(), False)
        self.assertRaises(ValueError, InverseFrequentialResponse, phy_modif,
                          frequencies, targets)


['pulsating_sphere', 'from_data']

if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(GradientComputation("test_gradtemp"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
