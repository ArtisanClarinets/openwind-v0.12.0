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
from openwind import ImpedanceComputation

F1 = 2000
F2 = 2001
frequencies = np.arange(F1, F2, 1)
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
temperature = 25

ref_value_damping = 2439755.43368212+12253572.5726607j

ordre = 10
lenEle = 0.07
# ----------------
# Tested Geometry cyl
# ----------------
tested_geom = [[0, 5e-3],
               [0.2, 5e-3]]

print("Test one cylinder with losses")
imped_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                         l_ele=lenEle, order=ordre, losses=True,
                         nondim=True, radiation_category='planar_piston', **dry_air)
err_nondim = np.abs(imped_nondim.impedance - ref_value_damping)/np.abs(ref_value_damping)
imped_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                      l_ele=lenEle, order=ordre, losses=True,
                      nondim=False, radiation_category='planar_piston', **dry_air)
err_dim = np.abs(imped_dim.impedance - ref_value_damping)/np.abs(ref_value_damping)
err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)
if err > 1e-10:
    raise Exception("Adim/non-adim give different results (but shouldn't).")

if err_nondim > 1e-10:
    raise Exception("The nondimenzionalized computation fails.")

if err_dim > 1e-10:
    raise Exception("The dimenzionalized computation fails.")

# ----------------
# Tested Geometry cyl_cyl
# ----------------
tested_geom = [[0, 5e-3],
               [0.1, 5e-3],
               [0.2, 5e-3]]
print("Test one 'redouble cylinder' with losses")
imped_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                         l_ele=lenEle, order=ordre, losses=True,
                         nondim=True, radiation_category='planar_piston', **dry_air)
err_nondim = np.abs(imped_nondim.impedance - ref_value_damping)/np.abs(ref_value_damping)
imped_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                      l_ele=lenEle, order=ordre, losses=True,
                      nondim=False, radiation_category='planar_piston', **dry_air)
err_dim = np.abs(imped_dim.impedance - ref_value_damping)/np.abs(ref_value_damping)
err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)
if err > 1e-10:
    raise Exception("Adim/non-adim give different results (but shouldn't).")

if err_nondim > 1e-10:
    raise Exception("The nondimenzionalized computation fails.")

if err_dim > 1e-10:
    raise Exception("The dimenzionalized computation fails.")
