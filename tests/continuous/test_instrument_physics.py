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
from pathlib import Path

from numpy import pi, sin

from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics

class TestInstrumentPhysics(unittest.TestCase):

    def test_construction(self):
        """Check that we succeed at instantiating InstrumentPhysics."""
        parent_path = str(Path(__file__).parent.absolute().parent)
        path = parent_path + '/models/'
        player = Player()
        for nondim in [True, False]:
            for files in [(path + 'mkmodel_test1',),
                          (path + 'mkmodel_test2',),
                          (path + 'complex_parts_example.csv',),
                          (path + 'mkmodel_test2', path + 'mkmodel_test_holes1'),
                          (path + 'trompette_simplifiee.csv',
                            path + 'trompette_simplifiee_trous.csv')
                          ]:
                print("Checking InstrumentPhysics on files {}".format(files))

                mm = InstrumentGeometry(*files)
                instru_physics = InstrumentPhysics(mm, 25, player, nondim=nondim, losses=False)
                # No verification, just check that no exception is raised.

    def test_temperature_entry(self):
        """Check that InstrumentPhysics correctly treats temperature.

        - Pipe entry temperature
        - Temperature in a hole
        - Temperature inside all pipes
        """
        for nondim in [True, False]:
            shape = [[1.7, 1], [2, 1], [pi, 1]]
            holes = [['label',   'position', 'radius', 'chimney'],
                     ['hole1',    2.71828,          1,   1.41421]]
            temperature = lambda x: 25+sin(x)
            T0 = 273.15
            instru_geom = InstrumentGeometry(shape, holes)
            player = Player()
            instru_physics = InstrumentPhysics(instru_geom, temperature,
                                               player, nondim=nondim,
                                               losses=False)

            # Check entry temperature
            (temp_entry_K,) = instru_physics.get_entry_coefs("T") # in Kelvin
            ratio = temp_entry_K/(T0+temperature(shape[0][0]))
            self.assertLess(abs(ratio-1), 1e-16)

            # Check hole temperature
            hole_pipe, _ = instru_physics.netlist.get_pipe_and_ends("hole1")
            # entry
            ratio = hole_pipe.get_physics().T(0) / (T0+temperature(holes[1][1]))
            self.assertLess(abs(ratio - 1), 1e-16)
            # exit
            ratio = hole_pipe.get_physics().T(1) / (T0+temperature(holes[1][1]))
            self.assertLess(abs(ratio - 1), 1e-16)

            # Check temperature in all the pipes
            netlist = instru_physics.netlist
            pipe_dict = netlist.pipes
            for pipe_name in pipe_dict:
                if pipe_name.startswith("bore"):
                    pipe, _ = netlist.get_pipe_and_ends(pipe_name)
                    x0, x1 = pipe.get_endpoints_position_value()
                    print(pipe_name, x0, x1)
                    ratio = pipe.get_physics().T(0) / (T0+temperature(x0))
                    self.assertLess(abs(ratio - 1), 1e-16)
                    ratio = pipe.get_physics().T(1) / (T0+temperature(x1))
                    self.assertLess(abs(ratio - 1), 1e-16)


if __name__ == "__main__":
    unittest.main()
