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
import matplotlib.pyplot as plt

from numpy import exp, nan_to_num
from openwind import simulate
from openwind.technical import InstrumentGeometry, Player
from openwind.continuous import InstrumentPhysics
from openwind.temporal import TemporalReed1dof, TemporalSolver

np.random.seed(0)

#%% test d'energie
player = Player('LIPS')
player.update_curve('contact_pulsation',300)#300)
player.update_curve('contact_exponent',4)
shape = [[0.0, 5e-3],
         [.6, 5e-3]]
CFL = 0.9
rec  = simulate(0.13, shape, player=player, losses=False, temperature=20,
                l_ele=0.1, order=2,
                radiation_category='planar_piston',
                theta_scheme_parameter=1/12,
                cfl_alpha=CFL,
                record_energy=True, nondim=True)

signal_out= rec.values['bell_radiation_pressure']
y = rec.values['entrance_reed1dof_source_y']

assert(np.min(y)<0)

# plt.plot(rec.ts, y, '-o')
# plt.legend()
#%% Plot energy balance

dt = rec.ts[1] - rec.ts[0]
e_tot = rec.values['bell_radiation_E']+rec.values['bore0_E']+rec.values['entrance_reed1dof_source_E']
dissip = rec.values['bore0_Q'] + rec.values['bell_radiation_Q']+rec.values['entrance_reed1dof_source_Q']
relative_ener_var = (np.diff(e_tot)+dissip[1:])/(dt*np.max(np.abs(e_tot)))

err = np.max(np.abs(relative_ener_var))
assert(err<1e-11)
print("Success! TLips NL energy balance OK.")
