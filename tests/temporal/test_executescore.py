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

""" Test features related to the score execution in temporal domain."""


import unittest
import numpy as np

from openwind.technical import InstrumentGeometry, Score, Player
from openwind.continuous import InstrumentPhysics
from openwind.temporal import TemporalSolver
from openwind.temporal import ExecuteScore

# a simple instrument with one hole ...
geom = [[0, 0.5, 2e-3, 10e-3, 'linear']]
hole = [['label', 'position', 'radius', 'chimney'],
        ['hole1', .25, 3e-3, 5e-3]]
# ... and 2 fingerings
fingerings = [['label', 'note1', 'note2'],
              ['hole1', 'o', 'x']]
instrument = InstrumentGeometry(geom, hole, fingerings)
player = Player()
instrument_physics = InstrumentPhysics(instrument, 20, player, False)
temporalsolver = TemporalSolver(instrument_physics, l_ele=0.01,
                                        order=4)
class TestExecuteScore(unittest.TestCase):

    def test_default_value(self):
        score_execution = ExecuteScore(instrument.fingering_chart,
                                       temporalsolver.t_components)
        self.assertFalse(score_execution._score.is_score())
        # I don't know how to check that all holes are open
        temporalsolver.run_simulation(.005)

    def test_update_score(self):
        note_events = [('note1', .002), ('note2', .003), ('note1', .004)]
        score = Score (note_events, 1e-4)
        score_execution = ExecuteScore(instrument.fingering_chart,
                                       temporalsolver.t_components)
        score_execution.set_score(score)
        self.assertEqual(score_execution._score, score)
        self.assertTrue(score_execution._score.is_score())

    def test_run_score(self):
        note_events = [('note1', .002), ('note2', .003), ('note1', .004)]
        player.update_score(note_events, 1e-5)
        temporalsolver.run_simulation(.005)

    def test_mismatch_note_names(self):
        strange_notes = [('Do', .002), ('Re', .003), ('E', .004)]
        player.update_score(strange_notes, 1e-5)
        with self.assertRaises(ValueError):
            temporalsolver.run_simulation(.005)


if __name__ == "__main__":
    unittest.main()
