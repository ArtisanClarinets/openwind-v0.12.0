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

from openwind.technical import InstrumentGeometry, Player
from openwind.discretization import Mesh
from openwind.continuous import InstrumentPhysics
from openwind.frequential import FrequentialSolver

fs = np.array([100])

shape = [[0, 1], [2.1, 3.4], [2.3074, 1.01]]
l_ele = [[0.3, 0.7, 1.0, 0.1], [0.206, 0.0014]]

order = [ [k+1 for k in range(len(l_ele[j]))] for j in range(len(l_ele))]

mk_model = InstrumentGeometry(shape)
player=Player()
instru_phy = InstrumentPhysics(mk_model, 25, player=player, losses=False)
# label of pipes
labels = list(instru_phy.netlist.pipes.keys())
# make a dict with the labels of the pipes
l_eles=dict(zip(labels, l_ele))

orders=dict(zip(labels, order))

fbm = FrequentialSolver(instru_phy, fs, l_ele=l_eles, order=orders)
#mesh = Mesh(instru_phy.netlist._pipes['bore0'], l_ele=l_ele, order=order)
orders_ = fbm.get_orders_mesh()
#assert np.allclose(l_eles, params['l_ele'].l_eles)
assert np.allclose(order[0],orders_[0])
assert np.allclose(order[1],orders_[1])
