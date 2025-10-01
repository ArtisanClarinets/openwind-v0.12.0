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

temperature = 25
dry_air = dict( humidity=0, carbon=0, ref_phy_coef='Chaigne_Kergomard')
# ----------------
# Tested Geometry cyl-disc-cone
# ----------------
tested_geom = [[0, 5e-3],
               [0.2, 5e-3]]
ordre = 10
lenEle = 0.07

ref_value_no_damping = 447766.01048075 + 1j*10935095.38528343


print("Test one cylinder without losses")
imped_nondim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                         l_ele=lenEle, order=ordre, losses=False,
                         nondim=True, radiation_category='planar_piston', **dry_air)
err_nondim = np.abs(imped_nondim.impedance - ref_value_no_damping)/np.abs(ref_value_no_damping)
imped_dim = ImpedanceComputation(frequencies, tested_geom, temperature=temperature,
                      l_ele=lenEle, order=ordre, losses=False,
                      nondim=False, radiation_category='planar_piston', **dry_air)
err_dim = np.abs(imped_dim.impedance - ref_value_no_damping)/np.abs(ref_value_no_damping)
err = np.linalg.norm(imped_nondim.impedance - imped_dim.impedance) / np.linalg.norm(imped_dim.impedance)
if err > 1e-10:
    raise Exception("Adim/non-adim give different results (but shouldn't).")

if err_nondim > 1e-10:
    raise Exception("The nondimenzionalized computation fails.")

if err_dim > 1e-10:
    raise Exception("The dimenzionalized computation fails.")
