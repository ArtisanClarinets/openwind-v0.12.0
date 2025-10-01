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
This presents how to access to the acoustic fields in the entire instrument.
It presents also how to interpolate data to a specific grid.
"""

import numpy as np
import matplotlib.pyplot as plt

from openwind import ImpedanceComputation

fs = np.arange(100, 5010, 10) # frequencies of interest: 100Hz to 5kHz by steps of 10Hz

# %% Low level implementation

# If you want to have access to the acoustic fields (pressure, flow, energy), it
# is necessary to activate the interpolation with the keyword "interp".
# The acoustic fields are then accessible by using the method "get_pressure_flow()"
# or "get_energy_field()".
# They are 2D matrices  with dimension (len(frequencies), len(x_interp)).

result1 = ImpedanceComputation(fs, 'Oboe_instrument.txt','Oboe_holes.txt', interp=True)
x1, pressure1, flow1 = result1.get_pressure_flow()
x1, energy1 = result1.get_energy_field()

# By default, the interpolation grid is the computation mesh (irregular).
# The keyword 'interp_grid' allows to interpolate the data on a grid
# with a given spacing:
# - if interp_grid is a float, it will be the step
# - if it is a list or an array, it compute the acosutic fields at these specific locations
result = ImpedanceComputation(fs, 'Oboe_instrument.txt','Oboe_holes.txt',
                              interp=True, interp_grid=1e-3)
x, pressure, flow = result.get_pressure_flow()
x, energy = result.get_energy_field()
print(f"The x vector range is [{1000*np.min(x):.1f},{1000*np.max(x):.1f}]mm,"
      f" with a {np.mean(np.diff(x))*1000:.1f}mm step.")
print(f"The flow array shape is {flow.shape}.")
print(f"The pressure array shape is {pressure.shape}.")
print(f"The energy array shape is {energy.shape}.")


# %% Visualization

# You can observe at the flow, pressure and energy for all interpolated points at one
# given frequency, e.g. 500Hz and 1500Hz:
plt.figure()
result.plot_ac_field_at_freq(500, var='flow', label='Flow: 500 Hz')
result.plot_ac_field_at_freq(1500, var='flow', label='Flow: 1500 Hz')

plt.figure()
result.plot_ac_field_at_freq(500, var='pressure', label='Pressure: 500 Hz')
result.plot_ac_field_at_freq(1500, var='pressure', label='Pressure: 1500 Hz')

plt.figure()
result.plot_ac_field_at_freq(500, var='energy', label='Energy: 500 Hz')
result.plot_ac_field_at_freq(1500, var='energy', label='Energy: 1500 Hz')

# You can also display these ac. fields for all frequencies.
result.plot_ac_field(var='pressure')
plt.title('Main Bore')
result.plot_ac_field(var='flow', cmap='gray')
plt.title('Main Bore')

# For the energy it can be interesting to scale by the energy at the entrance for each frequency
# with the keyword "scale_entrance=True"
result.plot_ac_field(var='energy', scale_entrance=True, vmin=-150)
plt.title('Main Bore')

plt.show()

# %% Access of acoustic field in a specific part of the instrument (e.g. chimney holes)

# You can specify in which pipe do you want to make interpolation with the keyword: 'pipes_label'
# By default, only the main bore pipes are observed and plotted.
result2 = ImpedanceComputation(fs, 'Oboe_instrument.txt','Oboe_holes.txt',
                              interp=True, interp_grid=1e-3, pipes_label='main_bore')
# you can also observe a given hole by giving the right pipe label visible in
print(f"Available labels to display the acoustic fields are: {result.get_pipes_label()}")
result3 = ImpedanceComputation(fs, 'Oboe_instrument.txt','Oboe_holes.txt',
                              interp=True, interp_grid=1e-3, pipes_label='hole1')
result3.plot_ac_field(var='pressure')
plt.title('Hole 1')

# or a series of pipe labels
result4 = ImpedanceComputation(fs, 'Oboe_instrument.txt','Oboe_holes.txt',
                              interp=True, interp_grid=1e-3,
                              pipes_label=['bore0', 'bore1', 'bore2_slice0', 'bore2_slice1'])
result4.plot_ac_field(var='pressure')
plt.title('Pipes 0 to 2')

plt.show()


# %% With plotly

# if you have plotly install on you computer you can display this plot in 3D
result.plot_ac_field(var='energy', with_plotly=True, scale_entrance=True)
