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

from openwind.continuous import Physics, radiation_model, Scaling


class RadiationTest(unittest.TestCase):

    Zc = 1316705.7717195274

    def get_cst(self):
        kr = np.linspace(1e-3, 4, 10)
        radius = 1e-2
        temperature = 20
        rho, celerity = Physics(temperature, humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard').get_coefs(0, 'rho', 'c')
        omegas = kr*celerity/radius
        opening_factor = 1
        return omegas, radius, rho, celerity, opening_factor

    def comp_ZY(self, rad_model, Zref):
        cst = self.get_cst()
        Z_model = rad_model.get_impedance(*cst)
        Y_model = rad_model.get_admitance(*cst)
        norme_Z = np.linalg.norm(Z_model)
        norme_Y = np.linalg.norm(1/Y_model)
        err_Z = np.abs(norme_Z - Zref)/Zref
        self.assertLess(err_Z, 1e-10, msg='Wrong impedance')
        err_Y = np.abs(norme_Y - Zref)/Zref
        self.assertLess(err_Y, 1e-10, msg='Wrong admittance')

    def comp_temp_coef(self, rad_model, coef_ref):
        om, r, rho, c, of = self.get_cst()
        coef_model = rad_model.compute_temporal_coefs(r, rho, c, of)
        self.assertTrue(np.allclose(coef_model, coef_ref, rtol=1e-10,
                                    atol=1e-14),
                        msg='Coef:{}; expect:{}'.format(coef_model, coef_ref))

    def no_temp_ceof(self, rad_model):
        om, r, rho, c, of = self.get_cst()
        args = (r, rho, c, of)
        self.assertRaises(NotImplementedError,
                          rad_model.compute_temporal_coefs, *args)

    def test_planar_piston(self):
        rad_model = radiation_model('planar_piston')
        Zref = 4225821.261509177
        coef_ref = (40452.3271275593, 0.6939565594515954, self.Zc)
        self.comp_ZY(rad_model, Zref)
        self.comp_temp_coef(rad_model, coef_ref)

    def test_unflanged(self):
        rad_model = radiation_model('unflanged')
        Zref = 3828154.5773234414
        coef_ref = (55987.284716964496, 0.6646516378651401, self.Zc)
        self.comp_ZY(rad_model, Zref)
        self.comp_temp_coef(rad_model, coef_ref)

    def test_total_transmission(self):
        rad_model = radiation_model('total_transmission')
        Zref = 4163789.2469234276
        coef_ref = (0.0, 1, 1316705.7717195274)
        self.comp_ZY(rad_model, Zref)
        self.comp_temp_coef(rad_model, coef_ref)

    def test_infinite_flanged(self):
        rad_model = radiation_model('infinite_flanged')
        Zref = 4016971.262159942
        coef_ref = (41691.35711135784, 0.737118529367156, self.Zc)
        self.comp_ZY(rad_model, Zref)
        self.comp_temp_coef(rad_model, coef_ref)

    def test_closed(self):
        rad_model = radiation_model("closed")
        cst = self.get_cst()
        Y_closed = rad_model.get_admitance(*cst)
        norme_Y = np.linalg.norm(Y_closed)
        self.assertEqual(norme_Y, 0, msg=('For a closed hole, the '
                                          'admittance should be 0'))
        coef_ref = (0, 0, self.Zc)
        self.comp_temp_coef(rad_model, coef_ref)

    def test_perfectly_open(self):
        rad_open = radiation_model("perfectly_open")
        cst = self.get_cst()
        Z_open = rad_open.get_impedance(*cst)
        norme_Z = np.linalg.norm(Z_open)
        self.assertEqual(norme_Z, 0, msg=('For a perfectly open hole, the '
                                          'impedance should be 0'))
        self.no_temp_ceof(rad_open)

    def test_unflanged_2nd_order(self):
        rad_model = radiation_model('unflanged_2nd_order')
        Zref = 3590438.0842348826
        self.comp_ZY(rad_model, Zref)
        self.no_temp_ceof(rad_model)

    def test_flanged_2nd_order(self):
        rad_model = radiation_model('flanged_2nd_order')
        Zref = 3723986.878907296
        self.comp_ZY(rad_model, Zref)
        self.no_temp_ceof(rad_model)

    def test_unflanged_non_causal(self):
        rad_model = radiation_model('unflanged_non_causal')
        Zref = 3656042.36116922
        self.comp_ZY(rad_model, Zref)
        self.no_temp_ceof(rad_model)

    def test_flanged_non_causal(self):
        rad_model = radiation_model('flanged_non_causal')
        Zref = 3696347.7017998663
        self.comp_ZY(rad_model, Zref)
        self.no_temp_ceof(rad_model)

    def test_pulsating_sphere(self):
        rad_model = radiation_model(('pulsating_sphere', np.pi/4))
        Zref = 3295283.0678285435
        self.comp_ZY(rad_model, Zref)
        self.no_temp_ceof(rad_model)

    def test_from_data(self):
        rad_data = radiation_model('unflanged')
        om, r, rho, c, of = self.get_cst()
        coef_data = rad_data.compute_temporal_coefs(r, rho, c, of)
        Z_data = rad_data.get_impedance(om, r, rho, c, of)
        data = ((om/(2*np.pi), Z_data/coef_data[-1]), 20, r )
        kwargs = dict(humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
        rad_model = radiation_model(('from_data', data, kwargs))
        self.comp_ZY(rad_model, np.linalg.norm(Z_data))
        self.comp_temp_coef(rad_model, coef_data)


if __name__ == '__main__':
    unittest.main()
