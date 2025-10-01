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

"""Test netlist."""


import unittest

from openwind.continuous import Netlist


# --- Placeholder classes for actual Pipes, Radiation, etc.
class MyComponent:
    def __init__(self, label='foo'):
        self.label = label

class MyPipe(MyComponent):
    pass

class MyRadiation(MyComponent):
    pass

class MyJunction(MyComponent):
    pass


# --- Placeholder classes for FrequentialComponents or TemporalComponents
class MySpecialPipe:
    def __init__(self, pipe, truc):
        pass
    def get_ends(self):
        return "left special end!", "right special end!"

class MySpecialRadiation:
    def __init__(self, rad, ends):
        # accepts exactly one end
        self.end, = ends

class MySpecialJunction:
    def __init__(self, junc, ends):
        # accepts exactly two ends
        self.end_a, self.end_b = ends


# Tells the netlist how to translate the components into
# "specialized" components.
def convert_pipe(pipe):
    return MySpecialPipe(pipe, None)

def convert_pipe_bad(pipe):
    return MySpecialPipe  # Not instantiated

def convert_connector(comp, ends):
    if isinstance(comp, MyRadiation):
        return MySpecialRadiation(comp, ends)
    if isinstance(comp, MyJunction):
        return MySpecialJunction(comp, ends)

dict_ = {MyPipe: MySpecialPipe,
         MyRadiation:MySpecialRadiation,
         MyJunction:MySpecialJunction}


class NetlistTest(unittest.TestCase):

    def test_simple(self):
        net = Netlist()
        end_0, end_1 = net.add_pipe(MyPipe('foo'))
        end_2, end_3 = net.add_pipe(MyPipe('bar'))

        net.add_connector(MyRadiation('left_radiation'), end_0)
        net.add_connector(MyJunction('middle_junction'), end_1, end_2)
        with self.assertRaises(ValueError):
            # Raises an exception because some pipe-ends are not
            # connected to anything
            net.convert_with_structure(convert_pipe, convert_connector)

        with self.assertRaises(ValueError):
            # Raises an exception because end_1 is already connected
            # to something
            net.add_connector(MyRadiation('right_radiation'), end_1)

        net.add_connector(MyRadiation('right_radiation'), end_3)
        s_pipes, s_connectors = \
            net.convert_with_structure(convert_pipe, convert_connector)

        with self.assertRaises(ValueError):
            net.convert_with_structure(convert_pipe_bad, convert_connector)

        self.assertEqual(len(s_pipes), 2)
        self.assertIsInstance(s_pipes['foo'], MySpecialPipe)
        self.assertEqual(len(s_connectors), 3)
        self.assertIsInstance(s_connectors['left_radiation'],
                              MySpecialRadiation)
        self.assertEqual(s_connectors['left_radiation'].end, "left special end!")


    def test_repeated_labels(self):
        net = Netlist()
        end_0, end_1 = net.add_pipe(MyPipe('foo'))
        with self.assertRaises(ValueError):
            net.add_pipe(MyPipe('foo'))

        net.add_connector(MyRadiation('same_label'), end_0)
        with self.assertRaises(ValueError):
            net.add_connector(MyRadiation('same_label'), end_1)

    def test_bad_number_of_ends(self):
        net = Netlist()
        end_0, end_1 = net.add_pipe(MyPipe('foo'))
        net.add_connector(MyRadiation('same_label'), end_0, end_1)

        with self.assertRaises(ValueError):
            # MySpecialRadiation raises an exception because it receives
            # two ends
            net.convert_with_structure(convert_pipe, convert_connector)


if __name__ == '__main__':
    unittest.main()
