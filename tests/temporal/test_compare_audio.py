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

from pathlib import Path
from openwind.technical.temporal_curves import gate
from openwind import simulate, Player, InstrumentGeometry

from openwind.temporal.utils import scaling_player

path = str(Path(__file__).parent)
threshold = 10  # number of digits in error
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
duration = 0.01

class TestCompareAudio(unittest.TestCase):

    def simu_clar_no_hole(self, nondim, player):
        # 50cm cylinder, no holes
        instrument = [[0.0, 5e-3],
                      [0.2, 5e-3],
                      [0.2, 7e-3],
                      [0.5, 5e-3]]
        holes = []

        # duration = 0.01  # simulation duration
        rec = simulate(duration,
                       instrument,
                       holes,
                       player=player,
                       losses='diffrepr',
                       temperature=20, **dry_air,
                       l_ele=0.03, order=4,  # Discretization parameters
                       nondim=nondim,
                       )

        new_simulation = rec.values['bell_radiation_pressure']
        return new_simulation

    def test_clarinet_no_holes(self):
        # duration = 0.01

        player = Player('CLARINET')
        player.update_curve("width", 2e-2)
        player.update_curve("mouth_pressure",
                            gate(0, 0.05*duration, 0.9*duration, duration, a=2500))
        player.update_curve("contact_pulsation", 0)

        new_simulation = self.simu_clar_no_hole(False, player)

        #np.savetxt('compare_audio_testfile_noholes.txt', new_simulation, delimiter=',')

        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_noholes.txt',
                                          delimiter=',')
        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for no holes = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_clarinet_hole(self):
        # each test has to have a corresponding testfile.txt in the same folder

        # 50cm cylinder, with 1 hole
        instrument = [[0.0, 5e-3],
                      [0.5, 5e-3]]
        holes = [['label', 'position', 'radius', 'chimney'],
                 ['hole1', .25, 3e-3, 20e-3]]
        # ... and a fingering chart
        fingerings = [['label', 'note1', 'note2'],
                      ['hole1', 'o', 'x']]

        # duration = 0.01  # simulation duration

        player = Player('CLARINET', [('note1', 0), ('note2', 0.005)],
                        transition_duration=1e-3)
        # Parameters of the reed can be changed manually
        # Available parameters are:
        # "opening", "mass","section","pulsation","dissip","width",
        # "mouth_pressure","model","contact_pulsation","contact_exponent"
        player.update_curve("width", 2e-2)
        player.update_curve("mouth_pressure",
                            gate(0, 0.05*duration, 0.9*duration, duration, a=2500))
        player.update_curve("contact_pulsation", 0)


        rec = simulate(duration,
                       instrument,
                       holes,
                       fingerings,
                       player=player,
                       losses='diffrepr',
                       temperature=20, **dry_air,
                       l_ele=0.05, order=4,  # Discretization parameters
                       nondim=False,
                       )

        new_simulation = rec.values['bell_radiation_pressure']

        # np.savetxt('compare_audio_testfile_holes.txt', new_simulation, delimiter=',')

        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_holes.txt',
                                          delimiter=',')
        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for 1 hole = {}'.format(err))

        self.assertAlmostEqual(err, 0.0, threshold)

    def simulate_valve(self, nondim):
        instrument = [[0.0, 5e-3], [0.5, 5e-3]]
        holes = [['label', 'variety', 'position', 'radius', 'chimney', 'reconnection'],
                 ['hole1', 'hole', .2, 3e-3, 20e-3, '/'],
                 ['piston', 'valve', .3, 3e-3, 5e-2, .4]]
        # ... and a fingering chart
        fingerings = [['label', 'note1', 'note2'],
                      ['hole1', 'o', 'o'],
                      ['piston', 'o', 'x']]

        # duration = 0.01  # simulation duration

        player = Player('CLARINET', [('note1', 0), ('note2', 0.005)],
                        transition_duration=1e-3)
        player.update_curve("width", 2e-2)
        player.update_curve("mouth_pressure",
                            gate(0, 0.05*duration, 0.9*duration, duration, a=2500))
        player.update_curve("contact_pulsation", 0)


        rec = simulate(duration,
                       instrument,
                       holes,
                       fingerings,
                       player=player,
                       discontinuity_mass=False,
                       losses='diffrepr',
                       temperature=20, **dry_air,
                       l_ele=0.05, order=4,  # Discretization parameters
                       nondim=nondim,
                       )

        new_simulation = rec.values['bell_radiation_pressure']
        return new_simulation

    def test_valve(self):
        new_simulation = self.simulate_valve(False)
        # np.savetxt('compare_audio_testfile_valve.txt', new_simulation, delimiter=',')

        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_valve.txt',
                                          delimiter=',')
        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for valve dim = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_valve_nondim(self):
        new_simulation = self.simulate_valve(False)
        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_valve.txt',
                                          delimiter=',')
        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for valve nondim = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_clarinet_scaled(self):
        # 50cm cylinder, no holes
        instrument = [[0.0, 5e-3],
                      [0.2, 5e-3],
                      [0.2, 7e-3],
                      [0.5, 5e-3]]
        holes = []

        # duration = 0.01  # simulation duration
        temperature = 20

        # scaled the clarinet dict
        player_dim = Player('CLARINET')
        player_dim.update_curve("width", 2e-2)
        player_dim.update_curve("mouth_pressure",
                            gate(0, 0.05*duration, 0.9*duration, duration, a=2500))
        player_dim.update_curve("contact_pulsation", 0)

        # scaled the player dict
        player_dict_dim = player_dim.control_parameters
        player_dict_dim['excitator_type'] = 'Reed1dof'
        instru_geom = InstrumentGeometry(instrument)
        scaled_dict = scaling_player(player_dict_dim, instru_geom, temperature, **dry_air)
        gamma =  gate(0, 0.05*duration, 0.9*duration, duration, a=2500/scaled_dict['closing_pressure'])
        scaled_dict['gamma'] = gamma
        player = Player(scaled_dict)

        new_simulation = self.simu_clar_no_hole(True, player)

        #np.savetxt('compare_audio_testfile_noholes.txt', new_simulation, delimiter=',')

        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_noholes.txt',
                                          delimiter=',')

        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for no holes scaled = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def simulate_flute(self, nondim, nn_linear_losses=True):
        temperature=25
        instrument = [[0.0, 6.6e-3],
                      [0.2, 6.6e-3]]
        # duration = 0.01
        player = Player('SOPRANO_RECORDER')
        player.update_curve('noise_level', 0) #to avoid random simulation...
        player.update_curve('jet_velocity', gate(-0.05*duration, 0.05*duration, 0.9*duration, duration, a=25))
        if not nn_linear_losses:
            player.update_curve('loss_mag', 0)

        rec = simulate(duration,
                       instrument,
                       player=player,
                       losses='diffrepr',
                       temperature=temperature, **dry_air,
                       l_ele=0.03, order=4,  # Discretization parameters
                       nondim=nondim,
                       )
        new_simulation = rec.values['entrance_flute_source_flow']
        return new_simulation

    def test_flute_dim(self):
        new_simulation = self.simulate_flute(False)
        # np.savetxt('compare_audio_testfile_flute.txt', new_simulation, delimiter=',')
        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_flute.txt',
                                          delimiter=',')

        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for Flute = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_flute_scaled(self):
        new_simulation = self.simulate_flute(True)
        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_flute.txt',
                                          delimiter=',')

        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for Flute scaled = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_flute_scaled_wo_nl_losses(self):
        new_simulation = self.simulate_flute(True, False)
        # np.savetxt('compare_audio_testfile_flute_wo_nnlin_losses.txt', new_simulation, delimiter=',')
        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_flute_wo_nnlin_losses.txt',
                                          delimiter=',')

        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for Flute scaled = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, threshold)

    def test_transverse_flute(self):
        # transverse flute, placing the source at a side hole
        geom_trans = [[-0.05, 0.5, 5e-3, 5e-3, 'linear']]
        hole_trans =[['label', 'x', 'r', 'l'],
                     ['embouchure', 0, 4e-3, 20e-3],
                     ]
        fing_trans = [['label', 'A'],
                      ['entrance', 'x']
                      ]
        temperature=25
        # duration = 0.01
        my_trans = Player('FLUTE', note_events=[('A', 0)])
        my_trans.update_curve('noise_level', 0)
        my_trans.update_curve('jet_velocity', gate(-0.05*duration, 0.05*duration, 0.9*duration, duration, a=25))

        rec = simulate(duration,
                       geom_trans, hole_trans, fing_trans,
                       player=my_trans,
                       losses='diffrepr',
                       temperature=temperature, **dry_air,
                       l_ele=0.03, order=4,  # Discretization parameters
                       nondim=True,
                       source_location='embouchure'
                       )
        new_simulation = rec.values['embouchure_flute_source_flow']
        # np.savetxt('compare_audio_testfile_transverse_flute.txt', new_simulation, delimiter=',')
        reference_simulation = np.loadtxt(path + '/compare_audio_testfile_transverse_flute.txt',
                                          delimiter=',')
        err = (np.linalg.norm(new_simulation - reference_simulation)
               / np.linalg.norm(reference_simulation))
        print('err for Transverse Flute = {}'.format(err))
        self.assertAlmostEqual(err, 0.0, 9)



if __name__ == '__main__':
    unittest.main()
    # suite = unittest.TestSuite()
    # suite.addTest(TestCompareAudio("test_transverse_flute"))
    # runner = unittest.TextTestRunner()
    # runner.run(suite)
