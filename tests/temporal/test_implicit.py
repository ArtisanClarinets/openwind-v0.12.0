
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
Test the consistence between implicit and explicit scheme for tonehole
"""
import unittest

import numpy as np

from openwind import (Player, InstrumentGeometry, InstrumentPhysics,
                      TemporalSolver)
from openwind.technical.temporal_curves import gate
from openwind.temporal import RecordingDevice






def get_ig():
    """
    Generate Instrument Geometry

    Returns
    -------
    ig : TYPE
        DESCRIPTION.

    """

    instrument = [[0.0, 300e-3, 5e-3, 5e-3, 'linear'],
                  [300e-3, 500e-3, 5e-3, 50e-3, 'bessel', 0.7]]
    holes = [['x', 'l', 'r', 'label'],
             [150e-3, 8e-3, 2e-3, 'hole1']]

    fing_chart = [['label', 'A', 'B'],
                  ['hole1', 'o', 'x']
                  ]


    ig = InstrumentGeometry(instrument, holes, fing_chart)

    return ig


def get_player(duration):
    """
    Get the player

    Parameters
    ----------
    duration : TYPE
        DESCRIPTION.

    Returns
    -------
    player : TYPE
        DESCRIPTION.

    """
    # Select reed parameters
    player = Player('CLARINET')
    player.update_curve("width", 2e-2)

    # duration = 0.05   # simulation time in seconds
    t_ramp = 1e-3 # Ramp time
    t1 = 0.0 # Time when to start blowing
    t2 = duration - t_ramp # Time when to stop blowing

    pmax = 2000 # Maximal blowing pressure
    player.update_curve("mouth_pressure", gate(t1, t1+t_ramp, t2-t_ramp, t2, a=pmax))
    return player


def get_solver(ig, player, implicit=True):
    """
    Get the temporal solver using implicit or explicit scheme for the tonehole

    Parameters
    ----------
    ig : TYPE
        DESCRIPTION.
    player : TYPE
        DESCRIPTION.
    implicit : TYPE, optional
        DESCRIPTION. The default is True.

    Returns
    -------
    t_solver : TYPE
        DESCRIPTION.

    """
    ip = InstrumentPhysics(ig, player=player,
                           losses=False,  # no viscothermal losses
                           temperature=20,
                           assembled_toneholes=implicit,
                           )


    t_solver = TemporalSolver(ip, l_ele=0.01, order=4)
    return t_solver


def get_signal(solver, score, duration, dt):
    """
    run simulation and extract the signal

    Parameters
    ----------
    solver : TYPE
        DESCRIPTION.
    score : TYPE
        DESCRIPTION.
    duration : TYPE
        DESCRIPTION.
    dt : TYPE
        DESCRIPTION.

    Returns
    -------
    time : TYPE
        DESCRIPTION.
    signal : TYPE
        DESCRIPTION.

    """
    player.update_score(score)
    solver._set_dt(dt)

    # print(solver)
    solver.reset()
    rec = RecordingDevice(record_energy=False)
    solver.run_simulation(duration, callback=rec.callback,
                          enable_tracker_display=False,
                          )
    rec.stop_recording()

    time = rec.ts
    signal = rec.values['bell_radiation_pressure']
    return time, signal



duration = 0.01
ig = get_ig()
player = get_player(duration)
solver_implicit = get_solver(ig, player)
solver_explicit = get_solver(ig, player, implicit=False)

# %%


class TestImplicitHole(unittest.TestCase):


    def test_open(self):
        delta_t = 2e-6
        t_imp, sig_imp = get_signal(solver_implicit, [('A',0)], duration, delta_t)
        t_exp, sig_exp = get_signal(solver_explicit, [('A',0)], duration, delta_t)
        err = np.linalg.norm(sig_imp - sig_exp) / np.linalg.norm(sig_exp)
        print(f"Relative error: {err:.1e}")
        self.assertLess(err, 1e-2)

    def test_closed(self):
        delta_t = 2e-6
        t_imp, sig_imp = get_signal(solver_implicit, [('B',0)], duration, delta_t)
        t_exp, sig_exp = get_signal(solver_explicit, [('B',0)], duration, delta_t)
        err = np.linalg.norm(sig_imp - sig_exp) / np.linalg.norm(sig_exp)
        print(f"Relative error: {err:.1e}")
        self.assertLess(err, 1e-3)

    @unittest.skip('Mass issue when hole is open or closed during simulation')
    def test_openclosed(self):
        delta_t = 2e-6
        score = [('A',0), ('B',duration/2)]
        t_imp, sig_imp = get_signal(solver_implicit, score, duration, delta_t)
        t_exp, sig_exp = get_signal(solver_explicit, score, duration, delta_t)
        err = np.linalg.norm(sig_imp - sig_exp) / np.linalg.norm(sig_exp)
        print(f"Relative error: {err:.1e}")
        self.assertLess(err, 1e-2)

if __name__ == "__main__":
    unittest.main()


    # plt.figure()
    # plt.plot(t_imp, sig_imp)
    # plt.plot(t_exp, sig_exp)
