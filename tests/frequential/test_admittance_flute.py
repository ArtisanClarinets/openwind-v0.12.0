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

from openwind import ImpedanceComputation, Player, InstrumentGeometry, InstrumentPhysics, FrequentialSolver
from openwind.continuous import radiation_model


Rp = 5e-3
geom = [[0, .5, Rp, Rp, 'cone']]
temperature = 25
freq = np.linspace(100, 800, 20)
# freq = np.linspace(100, 3000, 2000)
Rw = 4e-3


result_pipe = ImpedanceComputation(freq, geom, temperature=temperature, nondim=True)
Zp = result_pipe.impedance # response of the pipe alone

rho, celerity = result_pipe.get_entry_coefs('rho', 'c') # phy. quantities for rad impedance computation
my_rad = radiation_model('infinite_flanged')
Zw = my_rad.get_impedance(2*np.pi*freq, Rw, rho, celerity, opening_factor=1)

Zref =  Zp + Zw
Zc_w = rho*celerity/(np.pi*Rw**2)


class TestFluteAdmittance(unittest.TestCase):

    def test_simple_rad(self):
        my_player = Player('FLUTE')
        my_player.update_curve('radiation_category', 'infinite_flanged')
        my_player.update_curve('section', np.pi*Rw**2)
        result_flute = ImpedanceComputation(freq, geom, player=my_player, temperature=temperature)

        errZ = np.linalg.norm(Zref - result_flute.impedance)/np.linalg.norm(Zref)
        self.assertLess(errZ, 1e-12, 'The impedance of the flute does not equal Zw+Zp')

        errZ_adim = np.linalg.norm(Zref/Zc_w - result_flute.impedance/result_flute.Zc)/np.linalg.norm(Zref/Zc_w)
        self.assertLess(errZ_adim, 1e-12, 'The scaled impedance of the flute does not equal (Zw+Zp)/Zcw')

    def test_simple_rad_adim(self):
        my_player = Player('FLUTE')
        my_player.update_curve('radiation_category', 'infinite_flanged')
        my_player.update_curve('section', np.pi*Rw**2)
        result_flute = ImpedanceComputation(freq, geom, player=my_player, temperature=temperature, nondim=True)

        errZ = np.linalg.norm(Zref - result_flute.impedance)/np.linalg.norm(Zref)
        self.assertLess(errZ, 1e-12, 'The impedance of the flute does not equal Zw+Zp')

        errZ_adim = np.linalg.norm(Zref/Zc_w - result_flute.impedance/result_flute.Zc)/np.linalg.norm(Zref/Zc_w)
        self.assertLess(errZ_adim, 1e-12, 'The scaled impedance of the flute does not equal (Zw+Zp)/Zcw')

    def test_window_rad(self):
        my_recorder = Player('FLUTE')
        new_params = {'section':np.pi*Rw**2,
                      'radiation_category': 'window',
                       'edge_angle': 15, # the edge angle in degree
                      'wall_thickness': 5e-3} # the wall thickness in meter
        my_recorder.update_curves(new_params) # set the new control parameters

        instru_geom = InstrumentGeometry(geom)
        instru_phy = InstrumentPhysics(instru_geom, temperature, my_recorder, True, nondim=True)
        result_recorder = FrequentialSolver(instru_phy, freq)
        result_recorder.solve()
        Zrecorder = result_recorder.impedance
        Zc_rec = result_recorder.get_ZC_adim()

        my_rad = instru_phy.excitator_model.get_rad_model_window(np.pi*Rp**2)
        rho, celerity = instru_phy.get_entry_coefs('rho', 'c')
        Zwindow = my_rad.get_impedance(2*np.pi*freq, Rw, rho, celerity, 1)

        Ztot = Zp + Zwindow

        errZ = np.linalg.norm(Ztot - Zrecorder)/np.linalg.norm(Ztot)
        self.assertLess(errZ, 1e-12, 'The impedance of the flute does not equal Zw+Zp')

        errZ_adim = np.linalg.norm(Ztot/Zc_w - Zrecorder/Zc_rec)/np.linalg.norm(Ztot/Zc_w)
        self.assertLess(errZ_adim, 1e-12, 'The scaled impedance of the flute does not equal (Zw+Zp)/Zcw')

    def test_transverse_flute(self):
        # transverse flute, placing the source at a side hole
        geom_trans = [[-0.03, 0.5, 5e-3, 5e-3, 'linear']]
        hole_trans =[['label', 'x', 'r', 'l'],
                     ['emb', 0, 4e-3, 7e-3],
                     ]
        fing_trans = [['label', 'A'],
                      ['entrance', 'x']
                      ]
        my_trans = Player('FLUTE')
        result_trans = ImpedanceComputation(freq, geom_trans, hole_trans, fing_trans,
                                            player=my_trans, source_location='emb',
                                            temperature=temperature, nondim=True,
                                            note='A')
        # transverse flute, including the embouchure hole in the main bore.
        geom_strai = [[-7e-3, 0, 4e-3,4e-3, 'linear'], # embouchure hole chimney
                      [0, 0.5, 5e-3, 5e-3, 'linear']]
        hole_strai = [['label', 'x', 'r', 'l'],
                      ['cork', 1e-6, 5e-3, 0.03],
                     ]
        fing_strai = [['label', 'A'],
                      ['cork', 'x']
                      ]
        result_straight = ImpedanceComputation(freq, geom_strai, hole_strai, fing_strai,
                                               player=my_trans, source_location='entrance',
                                               temperature=temperature, nondim=True,
                                               note='A')
        err = np.linalg.norm(result_trans.impedance - result_straight.impedance)/np.linalg.norm(result_trans.impedance)
        self.assertLess(err, 5e-2, 'The 2 way to compute transverse flute impedance give too different result')

if __name__ == "__main__":
    unittest.main()
