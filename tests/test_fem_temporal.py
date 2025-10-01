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
import numpy.fft

from openwind import  Player, InstrumentGeometry, InstrumentPhysics
from openwind.temporal import TemporalSolver, RecordingDevice
from openwind.frequential import FrequentialSolver


temperature = 20.5
shape = [[0.0, 5e-3], [0.1, 5e-3], [0.1, 7e-3], [0.2, 5e-3]]
holes = [[0.15, 0.03, 3e-3]]
l_ele = 0.04
order = 4

player = Player('IMPULSE_400us')


class TestFEMvsTemporal(unittest.TestCase):

        def get_Ztemporal(self, instru_physics, duration):
            t_solver = TemporalSolver(instru_physics, l_ele=l_ele, order=order)

            res = RecordingDevice()
            t_solver.run_simulation(duration, callback=res.callback, enable_tracker_display=False)
            res.stop_recording()

            # Compute impedance from simu
            ts = res.ts
            p0, v0 = res.values['entrance_flow_source_pressure'], res.values['entrance_flow_source_flow']
            # Window the end of the impulse response to reduce artifacts
            window = np.hanning(len(p0))
            window[:len(p0)//2] = 1
            p0w, v0w = np.array(p0) * window, np.array(v0)*window

            p0_hat, v0_hat = numpy.fft.fft(p0w), numpy.fft.fft(v0w)

            Z = p0_hat / v0_hat
            fs_fft = numpy.fft.fftfreq(len(p0), ts[1]-ts[0])
            mask = (fs_fft > 100) * (fs_fft < 2000)

            Z = Z[mask]
            fs_fft = fs_fft[mask]
            return fs_fft, Z


        def compareZ_fem_temporal(self, losses=False, nondim=False,
                                  spherical_waves=False,
                                  radiation_category='planar_piston',
                                  disc_mass=False, tresh=5e-3, duration=0.02):
            print('*'*50)
            print("Performing simulation with losses =", losses,
                  "; nondim =", nondim, "; spherical_waves =", spherical_waves,
                  "; radiation_category =", radiation_category,
                  "; disc_mass =", disc_mass)

            instrument_geometry = InstrumentGeometry(shape, holes)
            instru_physics = InstrumentPhysics(instrument_geometry, temperature,
                                               player=player, losses=losses,
                                               radiation_category=radiation_category,
                                               nondim=nondim,
                                               spherical_waves=spherical_waves,
                                               discontinuity_mass=disc_mass)

            fs_fft, Z = self.get_Ztemporal(instru_physics, duration)
            # Compare with FEM
            f_fem = FrequentialSolver(instru_physics, fs_fft, l_ele=l_ele, order=order)
            f_fem.solve()
            # Compute error
            Z_fem = f_fem.impedance
            err = sum(abs(np.log(abs(Z_fem)) - np.log(abs(Z))))/sum(abs(np.log(abs(Z_fem))))
            print("Relative error on log(abs(Z)) is :",err)
            self.assertLess(err, tresh, msg="FEM and temporal simulation give very different results.")

        def test_default(self):
            self.compareZ_fem_temporal(duration=.03)

        def test_nondim(self):
            self.compareZ_fem_temporal(nondim=True, duration=.03)

        def test_spherical_waves(self):
            self.compareZ_fem_temporal(spherical_waves=True, duration=.03)

        def test_lossy(self):
            self.compareZ_fem_temporal(losses='diffrepr8')

        def test_open(self):
            self.compareZ_fem_temporal(radiation_category='perfectly_open', duration=.04)

        def test_disc_mass(self):
            self.compareZ_fem_temporal(disc_mass=True, duration=.03)

        def test_lossy_sphere(self):
            self.compareZ_fem_temporal(losses='diffrepr8', spherical_waves=True)

        def test_lossy_open(self):
            self.compareZ_fem_temporal(losses='diffrepr8', radiation_category='perfectly_open')

if __name__ == '__main__':
    unittest.main()
