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

F1 = 1000
F2 = 1001
frequencies = np.arange(F1, F2, 1)

temperature = 25
ordre = 10
lenEle = 3e-2

dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
# ----------------
# Tested Geometry cone
# ----------------
#tested_file = 'cone.txt'
tested_geom = [[0, 5e-3],
               [0.2, 10e-3]]
ref_value_damping = 260122.39629807 + 3390973.9706133j


print("Test of one cone with losses")
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
# Tested Geometry two cones
# ----------------
#tested_file = 'double_cone.txt'
tested_geom = [[0, 5e-3],
               [0.1, 10e-3],
               [0.2, 3e-3]]

ref_value_damping = 140224.59873365+4543295.37955805j


print("Test of two cones with losses")
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
# Tested Geometry cyl-disc-cone
# ----------------
lenEle = 1.05e-2
#tested_file = 'micro-trompette.txt'
tested_geom = [[0, 8.4e-3],
               [1e-3, 8.4e-3],
               [0.1, 7e-3],
               [1.4187041e-1, 6.1e-2]]

ref_value_damping = 212359.80709452-3974127.1485432j

print("Test of a micro-trumpet with losses")
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
