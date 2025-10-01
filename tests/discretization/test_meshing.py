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

from openwind.technical.player import Player
from openwind.technical import InstrumentGeometry
from openwind.continuous import InstrumentPhysics
from openwind.discretization import DiscretizedPipe
from openwind.frequential import FrequentialSolver


fs = np.array([100])
temp = 29
player = Player()
# ----------------
# Tested Geometry cyl-disc-cone
# ----------------
shape = [[0, 0.3, 0.005, 0.005, 'linear'], [0.3, 0.6, 0.01, 0.02, 'linear']]
instru = InstrumentGeometry(shape)
ordre = 10
lenEle = 0.09

# -----------------
# Constant temperature, PH1
# -----------------
instru_phy = InstrumentPhysics(instru, temp, player,convention='PH1', nondim=True, losses=False)

for param in [(None, None), (lenEle, None), (lenEle, ordre), (None, ordre)]:
    fbm = FrequentialSolver(instru_phy, fs, l_ele=param[0], order=param[1])
    print(fbm)
    print('mesh succesfully generated')

print('Passed: the meshes are succesfully generated with all the possible options')

# ------------------
# Test sensitivity of meshing to floating point error
# ------------------

# Create a shape of length 5cm, try to mesh it with 1cm elements
shape = [[0.0, 1.0], [0.05000000000000002, 1.0]]
mm = InstrumentGeometry(shape)
instru_physics = InstrumentPhysics(mm, 20,player,  False)
pipe, _ = instru_physics.netlist.get_pipe_and_ends('bore0')
dpipe = DiscretizedPipe(pipe, l_ele=0.01)
assert len(dpipe.mesh.elements) == 5
