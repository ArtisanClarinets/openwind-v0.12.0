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

from openwind.technical import Player, InstrumentGeometry
from openwind import ImpedanceComputation
from openwind.continuous import InstrumentPhysics
from openwind.frequential import FrequentialSolver
from pathlib import Path


parent_path = str(Path(__file__).parent.absolute().parent)
path = parent_path + '/models/'
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')

class TestFreqFingering(unittest.TestCase):

    def create_frequential_solver(self):

        player = Player()
        mm = InstrumentGeometry(path + 'mkmodel_test2', path + 'bizarophone_holes', path + 'bizarophone_fingering_chart')
        instru_phy = InstrumentPhysics(mm, 20, player, losses=False, **dry_air)
        fs = np.array([117.1])
        fbm = FrequentialSolver(instru_phy, fs, note=None, l_ele=0.1, order=4)
        return mm.fingering_chart, fbm

    def check_fingering(self, fingering, f_solver, ref_value):
        f_solver.set_note(fingering)
        f_solver.solve()
        value = np.abs(f_solver.impedance[0])
        self.assertAlmostEqual(value/ref_value, 1, places=12,
                               msg='The computed impedance in test_freq_fingering/check_fingering is not the expected ones.')

    def test_set_fingering(self):
        fing_chart, f_solver = self.create_frequential_solver()
        fing1 = fing_chart.fingering_of('do')
        self.check_fingering(fing1, f_solver, 77138.46458580381)

    def test_set_note(self):
        fing_chart, f_solver = self.create_frequential_solver()
        f_solver.set_note('fork')
        f_solver.solve()
        value = np.abs(f_solver.impedance[0])
        ref_value = 77490.7260455152
        self.assertAlmostEqual(value/ref_value, 1, places=12,
                               msg='The computed impedance in test_freq_fingering/test_set_note is not the expected ones.')

    def test_mix(self):
        fing_chart, f_solver = self.create_frequential_solver()
        fing1 = fing_chart.fingering_of('closed')
        fing2 = fing_chart.fingering_of('do')
        fing_mix = fing1.mix(fing2, 0.1)
        # Mix 90% do with 10% fork
        # i.e. open by 10% the lower holes
        self.check_fingering(fing_mix, f_solver, 77802.6416415267)

    def test_valve(self):
        valve_imped = ImpedanceComputation(np.array([117.1]), path + 'mkmodel_test2', path + 'test_valves',
                                           path + 'valve_fingering_chart.txt',
                                           temperature=25, **dry_air)
        value = np.linalg.norm(valve_imped.impedance)
        ref_value = 76513.29882571418
        self.assertAlmostEqual(value/ref_value, 1, places=12)

        valve_imped.set_note('B')
        value = np.linalg.norm(valve_imped.impedance)
        ref_value = 1061437.4128645514
        self.assertAlmostEqual(value/ref_value, 1,places=12)

        valve_imped.set_note('Bb')
        value = np.linalg.norm(valve_imped.impedance)
        ref_value = 1062642.3348207672
        self.assertAlmostEqual(value/ref_value, 1,places=12)

    def create_frequential_solver_fing(self):

        # player = Player()
        # mm = InstrumentGeometry(path + 'mkmodel_test2', path + 'bizarophone_holes', path + 'bizarophone_fingering_chart')
        # instru_phy = InstrumentPhysics(mm, 20, player, losses=False)
        # fs = np.array([117.1])
        # fbm = FrequentialSolver(instru_phy, fs, note=None, l_ele=0.1, order=4)
        # return mm.fingering_chart, fbm
        player = Player()
        mm = InstrumentGeometry(path + 'mkmodel_test2',
                path + 'bizarophone_holes',
                path + 'bizarophone_fingering_chart')
        print(mm.fingering_chart)
        print()
        instru_phy = InstrumentPhysics(mm, 20, player, losses=True, **dry_air)
        #fs = np.arange(20, 1000, 3)
        fs = np.array([100, 165])
        fbm = FrequentialSolver(instru_phy, fs, note=None)
        self.impedance = dict()
        for note in ['open', 'closed', 'fork']:
            print(mm.fingering_chart.fingering_of(note))
            fbm.set_note(note)
            fbm.solve()
            self.impedance[note] = fbm.impedance
        #    plt.semilogy(fs, np.abs(fbm.imped), label=note)

    def test_launch(self):
        tol = 1e-9
        self.create_frequential_solver_fing()
        imp_open_ref = np.array([5952.65299084 -7464.89218213j, 6262.68372976+237045.51783443j])
        self.assertLess(np.sum(np.abs(imp_open_ref - self.impedance['open']))/np.sum(np.abs(imp_open_ref)),
                        tol, msg='The computed impedance in test_freq_fingering/test_launch is not the expected ones.')
        imp_closed_ref = np.array([  1425.65581737 +36418.22108638j, 132452.66431208+815288.30729317j])
        self.assertLess(np.sum(np.abs(imp_closed_ref - self.impedance['closed']))/np.sum(np.abs(imp_closed_ref)),
                        tol, msg='The computed impedance in test_freq_fingering/test_launch is not the expected ones.')
        imp_fork_ref = np.array([ 1432.52717513 +36407.51558258j, 91734.56977689+655486.31871845j])
        self.assertLess(np.sum(np.abs(imp_fork_ref - self.impedance['fork']))/np.sum(np.abs(imp_fork_ref)),
                        tol, msg='The computed impedance in test_freq_fingering/test_launch is not the expected ones.')


if __name__ == "__main__":
    unittest.main()
