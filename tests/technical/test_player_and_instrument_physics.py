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

"""
Testing features of the Player class
and their interaction with InstrumentPhysics.
"""

import unittest

from openwind import Player, InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.technical.temporal_curves import constant_with_initial_ramp
from openwind.technical import Score


class TestPlayerAndPBM(unittest.TestCase):

    def test_player_and_instru_phy(self):
        temperature = 27
        fixed_value = 5.68
        variable_value = constant_with_initial_ramp(54315.2, 134.2)
        shape = [[0,1],[1,1]]
        mm = InstrumentGeometry(shape)
        note_events = [('do',0.0)]
        player = Player("OBOE", note_events)
        player.update_curve("mouth_pressure", variable_value)
        player.update_curve("opening", fixed_value)

        instru_phy = InstrumentPhysics(mm, temperature, player, losses=False)

        self.assertEqual(instru_phy.excitator_model.mouth_pressure.get_value(1.23),
                         variable_value(1.23))
        self.assertEqual(instru_phy.excitator_model.opening.get_value(1.76),
                         fixed_value)

        # update d'un excitatorparameter
        player.update_curve("mouth_pressure", fixed_value)
        instru_phy._update_player()

        self.assertEqual(instru_phy.excitator_model.mouth_pressure.get_value(1),
                         fixed_value)

    def test_player_score(self):
        player = Player()
        player.update_score([('note1', 1), ('note2', 2)],
                            transition_duration=0.2)
        test_score = player.get_score()
        self.assertEqual(type(test_score), Score)
        check_events = [('note1', .5), ('note1', 1.5), ('note2',5)]
        for note_name, time in check_events:
            self.assertEqual(test_score.get_notes_at_time(time)[0][0],
                             note_name)
        trans = test_score.get_notes_at_time(1.9)
        for name, prop in trans:
            self.assertAlmostEqual(prop, .5)


    def test_modification_excitator_type(self):
        player = Player("WOODWIND_REED")
        # Modifying excitator_type is forbidden
        with self.assertRaises(ValueError):
            player.update_curve("excitator_type","Flow")


    def test_modification_defaults(self):
        player = Player("WOODWIND_REED")
        with self.assertRaises(ValueError):
            player.set_defaults("UNITARY_FLOW")


    def test_invalid_param_name(self):
        player = Player("WOODWIND_REED")
        with self.assertRaises(ValueError):
            player.update_curve("foo",8)

    def test_flute_player(self):
        player = Player('FLUTE')
        shape = [[0,1],[1,1]]
        mm = InstrumentGeometry(shape)
        instru_phy = InstrumentPhysics(mm, 25, player, losses=False)

    def test_flute_to_recorder(self):
        my_recorder = Player('FLUTE')
        new_params = {'section':5e-6,
                      'radiation_category': 'window',
                       'edge_angle': 15, # the edge angle in degree
                      'wall_thickness': 5e-3, # the wall thickness in meter
                      'noise_level':1e-6}
        my_recorder.update_curves(new_params) # set the new control parameters
        shape = [[0,1],[1,1]]
        mm = InstrumentGeometry(shape)
        instru_phy = InstrumentPhysics(mm, 25, my_recorder, losses=False)

if __name__ == "__main__":
    unittest.main()
