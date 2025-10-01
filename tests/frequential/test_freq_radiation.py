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

from openwind import ImpedanceComputation
from openwind.continuous import radiation_model, Physics

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
class FreqRadiationTest(unittest.TestCase):

    def comp_impedance(self, radiation, Zref,
                       use_rad1dof=False):
        geom = [[0, 0.1, 5e-3, 8e-3, 'linear'],
                [0.1, 0.3, 5e-3, 30e-3, 'exponential'],
                ]
        holes = [['label',   'position', 'type',     'radius',   'chimney'],
                 ['h1',      0.05,       'linear',   3e-3,       5e-3],
                 ['h2',      0.25,       'linear',   15e-3,      7e-3]
                 ]
        fs = 500
        temp = 20
        result = ImpedanceComputation(fs, geom, holes, temperature=temp,
                                      radiation_category=radiation,
                                      use_rad1dof=use_rad1dof,
                                      nondim=True, **dry_air,
                                      #nondim=(not use_rad1dof)
                                              )
        err = np.linalg.norm(result.impedance - Zref)/np.linalg.norm(Zref)
        self.assertLess(err, 1e-10,
                        msg='{} expected:{}'.format(result.impedance, Zref))

    def test_planar_piston(self):
        Zref = 100146.52907524+3633075.67699185j
        self.comp_impedance('planar_piston', Zref)

    def test_unflanged(self):
        Zref = 92155.33811511+3499804.70267282j
        self.comp_impedance('unflanged', Zref)

    def test_rad1dof(self):
        Zref = 92155.33811511+3499804.70267282j
        self.comp_impedance('unflanged', Zref, use_rad1dof=True)

    def test_total_transmission(self):
        Zref = 10435403.71371405-2389919.76278411j
        self.comp_impedance('total_transmission', Zref)

    def test_infinite_flanged(self):
        Zref = 99738.42332203+3618630.53220803j
        self.comp_impedance('infinite_flanged', Zref)

    def test_closed(self):
        Zref = 49204265.81464024+78277715.24580312j
        self.comp_impedance('closed', Zref)

    def test_perfectly_open(self):
        Zref = 80517.98668552+3163335.86713584j
        self.comp_impedance('perfectly_open', Zref)

    def test_unflanged_2nd_order(self):
        Zref = 92153.62712776+3499677.82271025j
        self.comp_impedance('unflanged_2nd_order', Zref)

    def test_flanged_2nd_order(self):
        Zref = 99722.68448264+3617495.97607932j
        self.comp_impedance('flanged_2nd_order', Zref)

    def test_unflanged_non_causal(self):
        Zref = 92159.42011828+3499866.66207752j
        self.comp_impedance('unflanged_non_causal', Zref)

    def test_flanged_non_causal(self):
        Zref = 99725.25986392+3617576.88942296j
        self.comp_impedance('flanged_non_causal', Zref)

    def test_pulsating_sphere(self):
        Zref = [9065646.47789145-5077731.08248055j]
        self.comp_impedance('pulsating_sphere', Zref)

    def test_pulsating_sphere_angle(self):
        Zref = 90895.54405071+3491606.02575172j
        self.comp_impedance(('pulsating_sphere', np.pi/4), Zref)

    def test_from_data(self):
        rad_data = radiation_model('unflanged')
        kr = np.linspace(1e-3, 4, 10)
        r = 1e-3
        temperature = 20
        rho, c = Physics(temperature).get_coefs(0, 'rho', 'c')
        om = kr*c/r

        Z_data = rad_data.get_impedance(om, r, rho, c, 1)
        data = ((om/(2*np.pi), Z_data*np.pi*r**2/(rho*c)), 20, r)

        Zref = 145956.23613047+3487788.50711403j
        self.comp_impedance(('from_data', data), Zref)

    def test_bell_sphere_holes_flanged(self):
        Zref = 99311.16580312+3618133.83215068j
        rad = {'bell': 'pulsating_sphere', 'holes': 'infinite_flanged'}
        self.comp_impedance(rad, Zref)

    def test_1per_hole(self):
        Zref = 2600487.36572566-19821947.67792789j
        rad = {'bell': 'unflanged', 'h1': 'closed', 'h2': 'infinite_flanged'}
        self.comp_impedance(rad, Zref)


if __name__ == '__main__':
    unittest.main()
