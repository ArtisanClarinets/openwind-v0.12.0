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

from openwind.technical import InstrumentGeometry, Player
from openwind.continuous import InstrumentPhysics
from openwind.temporal import TemporalSolver


class TestEnergyConservativeComponent(unittest.TestCase):

    def check_conservative_instrument(self, instru_geom, player=Player("ZERO_FLOW"),
                                      disc_mass=False, nondim=False):
        instru_phy = InstrumentPhysics(instru_geom, 25, player, losses=False,
                                       discontinuity_mass=disc_mass,
                                       radiation_category='closed',
                                       nondim=nondim)
        t_solver = TemporalSolver(instru_phy, l_ele=1e-1, order=2)

        # Put some energy in the pipes.
        for tpipe in t_solver.t_pipes:
            np.random.seed(0) # Seed every time because order may be unpredictable
            tpipe.add_pressure(np.random.random(tpipe.nH1))

        t_solver.one_step()

        n_steps = int(np.ceil(0.01 / t_solver.get_dt()))
        t_solver.run_simulation_steps(n_steps,
                                      energy_check=True,
                                      enable_tracker_display=False)

        self.assertEqual(t_solver.energy_check.dissipated_total, 0.0,
                         msg='Instrument dissipates energy and should not!')

    def test_pipe(self):
        print('\n' + '-'*20 + '\nPipe')
        shape = [[0  , 8e-3],
         [0.2, 8e-3]]
        mm = InstrumentGeometry(shape)
        self.check_conservative_instrument(mm)

    def test_T_junction(self):
        print('\n' + '-'*20 + '\nT_junction')
        shape = [[0.0, 8e-3],
                 [0.2, 8e-3]]
        holes = [[0.15, 0.03, 3e-3]]
        mm = InstrumentGeometry(shape, holes)
        self.check_conservative_instrument(mm)

    def test_T_junction_nondim(self):
        print('\n' + '-'*20 + '\nT_junction')
        shape = [[0.0, 8e-3],
                 [0.2, 8e-3]]
        holes = [[0.15, 0.03, 3e-3]]
        mm = InstrumentGeometry(shape, holes)
        self.check_conservative_instrument(mm, nondim=True)

    def test_simple_junction(self):
        print('\n' + '-'*20 + '\nSimple Junction')
        shape = [[0  , 8e-3],
                 [0.15, 8e-3],
                 [0.2, 8e-3]]
        mm = InstrumentGeometry(shape)
        self.check_conservative_instrument(mm)

    def test_disc_junction(self):
        print('\n' + '-'*20 + '\nDiscontinuity Junction')
        shape = [[0  , 8e-3],
                 [0.15, 8e-3],
                 [0.15, 12e-3],
                 [0.2, 8e-3]]
        mm = InstrumentGeometry(shape)
        self.check_conservative_instrument(mm)
        print('\n**With Mass**')
        self.check_conservative_instrument(mm, disc_mass=True)

    def test_valve(self):
        print('\n' + '-'*20 + '\nValve')
        geom = [[0, 0.005], [0.1, 0.005], [0.7, 0.005]]
        holes = [['variety', 'label', 'position', 'radius', 'chimney', 'reconnection'],
                 ['valve', 'piston', 0.1, 3e-3, 0.1, 0.15]]
        fing_chart = [['label', 'A', 'B'],
                      ['piston', 'o', 'x']]
        mm = InstrumentGeometry(geom, holes, fing_chart)
        player = Player("ZERO_FLOW", [('B', 0), ('A', 8e-3)], transition_duration=5e-3)
        self.check_conservative_instrument(mm, player=player)
        print('\n**With Mass**')
        self.assertRaises(ValueError, self.check_conservative_instrument, mm, player=player, disc_mass=True)

if __name__ == "__main__":
    unittest.main()
