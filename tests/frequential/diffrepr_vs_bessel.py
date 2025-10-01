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
from openwind.continuous.thermoviscous_models import ThermoviscousDiffusiveRepresentation
#import matplotlib.pyplot as plt

frequencies = np.array([100, 500, 1500, 5000])
loss_models = [(ThermoviscousDiffusiveRepresentation('diffrepr0'),'diffrepr0'),
               (ThermoviscousDiffusiveRepresentation('diffrepr2'),'diffrepr2'),
               (ThermoviscousDiffusiveRepresentation('diffrepr4'),'diffrepr4'),
               (ThermoviscousDiffusiveRepresentation('diffrepr6'),'diffrepr6'),
               (ThermoviscousDiffusiveRepresentation('diffrepr8'),'diffrepr8'),
               (ThermoviscousDiffusiveRepresentation('diffrepr16'),'diffrepr16')
               ]
expected_rel_errs = [1.005133620123669e-01, 3.500041086441295e-02,
                     8.898567732532611e-03, 2.026158495019459e-03,
                     4.537465632533206e-04, 2.893176005456879e-06
                     ]

temperature = 25
ordre = 10
lenEle = 0.05

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

tested_geom = [[0, 4e-3],
               [0.1, 4e-3]]

class TestDiffrepr(unittest.TestCase):

    def test_diffrepr(self):
        result_bessel = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                 l_ele=lenEle, order=ordre, losses='bessel',
                                 nondim=True, convention='PH1',
                                 radiation_category='planar_piston', **dry_air)

        for (losses, name), expected_rel_err in zip(loss_models, expected_rel_errs):
            result_diffrepr = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                                     l_ele=lenEle, order=ordre, losses=losses,
                                     nondim=True, convention='PH1',
                                     radiation_category='planar_piston', **dry_air)
            rel_err = np.sum(np.abs(result_diffrepr.impedance - result_bessel.impedance)) / np.sum(np.abs(result_bessel.impedance))
            print("{}'s relative error on impedance (compared to bessel) is {:.15e}".format(name, rel_err))
            self.assertLess(abs(rel_err - expected_rel_err), 1e-10, "Model error between bessel and {} has varied.".format(name))

            #if abs(rel_err - expected_rel_err) > 1e-10:
            #    raise Exception("Model error between bessel and {} has varied.".format(name))



if __name__ == "__main__":
    unittest.main()
