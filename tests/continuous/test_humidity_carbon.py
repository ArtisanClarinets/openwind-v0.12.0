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

from openwind.continuous import Physics

coefs = ('c', 'gamma', 'Cp',   'rho', 'mu', 'kappa')
ref_CK_20 = (343.3700171691432, 1.402, 1004.16, 1.2046925976462561, 1.807064e-05, 0.02573503088)
ref_RR_dry = (343.3981674520097, 1.4021139129752003, 1006.0348578821599, 1.2043178612458099, 1.8206e-05, 0.025562)

ref_RR_RH30 = (343.7735353862884, 1.401530299328096, 1009.7837652029905, 1.2011814376778678, 1.8206e-05, 0.025562)
ref_RR_CO2 = (339.8638691545591, 1.3962854201752002, 999.69967101216, 1.22428380764581, 1.8206e-05, 0.025562)
ref_RR_all = (338.6435360438358, 1.392593022245728, 1001.6355571933937, 1.2300848827552207, 1.8206e-05, 0.025562)
ref_RR_Zuck = (338.6435360438358, 1.392593022245728, 1001.6355571933937, 1.2300848827552207, 1.813419606539143e-05, 0.025177130226948664)
ref_RR_Tsi = (338.6435360438358, 1.392593022245728, 1001.6355571933937, 1.2300848827552207, 1.810812337575281e-05, 0.025490819180092997)

class HumidityTest(unittest.TestCase):


    def test_CK(self):
        with self.assertWarns(Warning):
            Phy_CK = Physics(temp =20, ref_phy_coef='Chaigne_Kergomard')
        CK_20 = Phy_CK.get_coefs(0, *coefs)
        # print(CK_20)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_CK_20[k]/CK_20[k], 1., 15, msg=f'\nFor Chaigne and Kergomard, "{coef}" is not equal to the ref value:\nref:{ref_CK_20[k]}\nnow:{CK_20[k]}')

    def test_wrong_RH(self):
        with self.assertRaises(ValueError):
            Phy_RR = Physics(temp=20, humidity=10, carbon=0)
        with self.assertRaises(ValueError):
            Phy_RR = Physics(temp=20, humidity=-.1, carbon=0)

    def test_wrong_Carbon(self):
        with self.assertRaises(ValueError):
            Phy_RR = Physics(temp=20, humidity=0, carbon=10)
        with self.assertRaises(ValueError):
            Phy_RR = Physics(temp=20, humidity=0, carbon=-.1)

    def test_wrong_Temperature(self):
        with  self.assertWarns(Warning):
            Phy_RR = Physics(temp=293, humidity=0, carbon=0)

    def test_RR_dry(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR', humidity=0, carbon=0)
        RR_dry = Phy_RR.get_coefs(0, *coefs)
        # print(RR_dry)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_dry[k]/RR_dry[k], 1., 15, msg=f'\nFor dry air, "{coef}" is not equal to the ref value:\nref:{ref_RR_dry[k]}\nnow:{RR_dry[k]}')

    def test_RR_RH30(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR', humidity=.3, carbon=0)
        RR_RH30 = Phy_RR.get_coefs(0, *coefs)
        # print(RR_RH30)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_RH30[k]/RR_RH30[k], 1., 15, msg=f'\nFor moist air, "{coef}" is not equal to the ref value:\nref:{ref_RR_RH30[k]}\nnow:{RR_RH30[k]}')

    def test_RR_CO2(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR', humidity=0, carbon=.04)
        RR_CO2 = Phy_RR.get_coefs(0, *coefs)
        # print(RR_CO2)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_CO2[k]/RR_CO2[k], 1., 15, msg=f'\nFor air with CO2, "{coef}" is not equal to the ref value:\nref:{ref_RR_CO2[k]}\nnow:{RR_CO2[k]}')

    def test_RR_all(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR', humidity=.40, carbon=.06)
        RR_all = Phy_RR.get_coefs(0, *coefs)
        # print(RR_all)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_all[k]/RR_all[k], 1., 15, msg=f'\nFor moist air with CO2, "{coef}" is not equal to the ref value:\nref:{ref_RR_all[k]}\nnow:{RR_all[k]}')

    def test_RR_Zuck(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR_Zuckerwar', humidity=.4, carbon=.06)
        RR_Zuck = Phy_RR.get_coefs(0, *coefs)
        # print(RR_Zuck)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_Zuck[k]/RR_Zuck[k], 1., 15, msg=f'\nFor Zuckerwar model of visco-thermal quantities, "{coef}" is not equal to the ref value:\nref:{ref_RR_Zuck[k]}\nnow:{RR_Zuck[k]}')

    def test_RR_Tsi(self):
        Phy_RR = Physics(temp =20, ref_phy_coef='RR_Tsilingiris', humidity=.4, carbon=.06)
        RR_Tsi = Phy_RR.get_coefs(0, *coefs)
        # print(RR_Tsi)
        for k, coef in enumerate(coefs):
            self.assertAlmostEqual(ref_RR_Tsi[k]/RR_Tsi[k], 1., 15, msg=f'\nFor Tsilingiris model of visco-thermal quantities, "{coef}" is not equal to the ref value:\nref:{ref_RR_Tsi[k]}\nnow:{RR_Tsi[k]}')

if __name__ == '__main__':
    unittest.main()
