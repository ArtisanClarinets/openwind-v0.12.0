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
import warnings

from openwind import InstrumentGeometry
from openwind.design import Cone

# import sys
# sys.path.insert(0, '/usr/lib/freecad-python3/lib')
try:
    import FreeCAD
    import Part
except ImportError:
    warnings.warn('FreeCAD is not install on this environnement.\n'
                  'The "OWtoFreeCAD" has been designed to be loaded directly on FreeCAD GUI.')

class OWtoFreeCAD():
    """
    Compute with FreeCAD the 3D geometry of an instrument coming from OW.

    FreeCAD is an open-source and free software. It can be downloaded here:
    https://www.freecadweb.org


    Parameters
    ----------
    doc : App.Document
        The FreeCAD document in which build the 3D objects.
    mainbore : str or list
        The main bore geometry. See: :py:class:`InstrumentGeometry<openwind.technical.instrument_geometry.InstrumentGeometry>`.
    holes : str or list, optional
        The holes geometry. See: :py:class:`InstrumentGeometry<openwind.technical.instrument_geometry.InstrumentGeometry>`..
        The default is list() (no holes).
    leveled_chimney : booelan, optional
        If true the wall width of the main bore is adjusted to fit the chimney
        length. Otherwise, the chimney are made of tubes protruding of the wall.
        The default is False.
    angles : list of float, optional
        The angle of the hole around the main bore. If indicated the list must
        have the same length than the number of holes The default is None.
    step : float, optional
        The step with which slice the non-conical part, in mm. The default is 2.
    wall_width : float, optional
        The wall width of the main bore in mm. The default is 3.
    chim_width : float, optional
        The wall width of the chimney in mm (only used if ``leveled_chimney=True``).
        The default is 2.

    """


    def __init__(self, doc, mainbore, holes=list(), leveled_chimney=False, angles=None,
                 step=2, wall_width=3, chim_width=2):
        self.doc = doc
        self.instru_geom = InstrumentGeometry(mainbore, holes)
        self.leveled_chimney = leveled_chimney
        self.wall_width = wall_width
        self.chim_width = chim_width
        self.step=step
        if angles is None:
            angles = [0]*len(self.instru_geom.holes)
        if len(angles) != len(self.instru_geom.holes):
            raise ValueError(f'Please indicate one angle per hole: here {len(angles)} angles for {len(self.instru_geom.holes)} holes.')
        self.angles = angles

    def build_instru3D(self):
        main_bore3D = self.build_main_bore()
        print('The main bore has been generated')
        if len(self.instru_geom.holes)>0:
            holes_reamer3D = self.build_holes_reamer()
            print( 'The holes reamer have been generated')
            bore_drilled =self.drill_main_bore(main_bore3D, holes_reamer3D)
            print('The main bore has been drilled')
            if not self.leveled_chimney:
                holes_chim3D = self.build_holes_chimneys()
                print('The chimney pipes have been generated')
                full_instru3D = self.fuse_list3D([bore_drilled, holes_chim3D], 'Full_Instru')
                print('All elements have been fused.')
            else:
                full_instru3D = bore_drilled
        else:
            full_instru3D = main_bore3D
        self.doc.recompute()
        return full_instru3D


    def build_main_bore(self):

        pos_in, rad_in = self._get_mb_internal_geom()

        # adaptation of the wall width at the location of the chimney
        pos_out = np.array(pos_in)
        rad_out = np.array(rad_in) + self.wall_width
        for hole in self.instru_geom.holes:
            hole_pos, hole_length, hole_max_rad, main_radius = self.hole_characteristics(hole)
            if self.leveled_chimney: # if leveled chimney: the width is set equal to the chimney height
                rad_mb = hole_length + main_radius
            else: # else it is set smaller
                rad_mb = main_radius + min(self.wall_width, 0.9*hole_length)
            pos_up = hole_pos - 1.1*hole_max_rad
            pos_down = hole_pos + 1.1*hole_max_rad
            rad_out = np.append(np.append(rad_out[pos_out<pos_up], [rad_mb, rad_mb]),
                                rad_out[pos_out>pos_down])
            pos_out = np.append(np.append(pos_out[pos_out<pos_up], [pos_up, pos_down]),
                                pos_out[pos_out>pos_down])


        position_face = pos_in + np.flip(pos_out).tolist() + [pos_in[0]]
        radius_face = rad_in + np.flip(rad_out).tolist() + [rad_in[0]]

        Main_bore3D = self._make_pipe(position_face, radius_face, 'Main_Bore')

        return Main_bore3D

    def build_holes_reamer(self):
        holes_reamer = list()
        for k, hole in enumerate(self.instru_geom.holes):
            holes_reamer.append(self.get_reamer_hole(hole, self.angles[k]))
        return self.fuse_list3D(holes_reamer, "Holes_Reamer")

    def build_holes_chimneys(self):
        holes_chim = list()
        for k, hole in enumerate(self.instru_geom.holes):
            holes_chim.append(self.get_chimney(hole, self.angles[k]))
        return self.fuse_list3D(holes_chim, "Holes_Chimney")

    def drill_main_bore(self, main_bore3D, holes_reamer3D):
        # bore_drilled = BOPTools.JoinFeatures.makeCutout(name='Drilled_Bore')
        # bore_drilled.Base = main_bore3D
        # bore_drilled.Tool = holes_reamer3D
        # bore_drilled.Proxy.execute(bore_drilled)
        # bore_drilled.purgeTouched()
        # for obj in bore_drilled.ViewObject.Proxy.claimChildren():
        #     obj.ViewObject.hide()
        bore_drilled = self.doc.addObject('Part::Cut', 'Drilled_Bore')
        bore_drilled.Base = main_bore3D
        bore_drilled.Tool = holes_reamer3D
        main_bore3D.Visibility = False
        holes_reamer3D.Visibility = False
        # self.doc.recompute()
        return bore_drilled

    def fuse_list3D(self, list3D, name):
        if len(list3D)>1:
            fused = self.doc.addObject("Part::MultiFuse", name)
            fused.Shapes = list3D
            self.doc.recompute()
            return fused
        else:
            return list3D[0]

    def _make_pipe(self, x, y, label, origin=0, orientation='H', theta=0):
        # create a new object
        pipe = self.doc.addObject('PartDesign::Body', label)

        # create the sketch of the surface
        sketch = pipe.newObject('Sketcher::SketchObject')

        # place the coordinate system
        if orientation=='H':
            sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(origin, 0, 0),
                                                 FreeCAD.Rotation(0, 0, 0, 1))
        elif orientation=='V':
            sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(origin, 0, 0),
                                             FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0),
                                                          -theta))

        # create the sketch
        assert(x[0]==x[-1] and y[0]==y[-1]) # the surface must be closed
        for i in range(len(x) - 1):
            sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(x[i],y[i],0),
                                                FreeCAD.Vector(x[i+1],y[i+1],0)),
                               False)

        # do the revolution
        Revolution = pipe.newObject("PartDesign::Revolution")
        Revolution.Profile = sketch
        if orientation=='H':
            Revolution.ReferenceAxis = (sketch, ['H_Axis'])
        elif orientation=='V':
            Revolution.ReferenceAxis = (sketch, ['V_Axis'])
        Revolution.Angle = 360.0
        Revolution.Reversed = 1
        return pipe

    def _get_mb_internal_geom(self):
        radius = list()
        position = list()
        for shape in self.instru_geom.main_bore_shapes:
            if shape.__class__ == Cone:
                x = np.array([0, 1])
            else:
                N = max(11, int(np.ceil(shape.get_length()*1e3/self.step)))
                x = np.linspace(0, 1, N)
            rad_shape = (shape.get_radius_at(x)*1e3).tolist()
            pos_shape = (shape.get_position_from_xnorm(x)*1e3).tolist()
            if len(radius)>0 and np.isclose(rad_shape[0],radius[-1]):
                radius += rad_shape[1:]
                position += pos_shape[1:]
            else:
                radius += rad_shape
                position += pos_shape
        return position, radius


    def get_reamer_mb(self):
        pos_in, rad_in = self._get_mb_internal_geom()
        x_reamer = [pos_in[0]] + pos_in + [pos_in[-1], pos_in[0]]
        y_reamer = [0] + rad_in + [0, 0]
        return x_reamer, y_reamer


    def hole_characteristics(self, hole):
        hole_pos = hole.position.get_value()*1e3
        hole_length = hole.shape.get_length()*1e3
        hole_max_rad = max(hole.shape.get_radius_at(np.linspace(0,1,10)))*1e3 + self.chim_width
        main_radius = self.instru_geom.get_main_bore_radius_at(hole_pos*1e-3)*1e3
        return hole_pos, hole_length, hole_max_rad, main_radius

    def get_reamer_hole(self, hole, angle):
        hole_pos, hole_length, hole_max_rad, main_radius = self.hole_characteristics(hole)
        # we prolongate the reamer to be sure to pass trough the MB wall
        top = hole_length + main_radius + 2*self.wall_width
        if self.leveled_chimney:
            x = np.array([0, 1])
            rad_shape = (hole.shape.get_radius_at(x)*1e3).tolist()
            pos_shape = (hole.shape.get_position_from_xnorm(x)*1e3).tolist()
            x_chem = [0] + rad_shape + [rad_shape[-1], 0, 0]
            y_chem = [0] + pos_shape + [top, top, 0]
        else: # if we add the chimney after, we drill with a cylinder
            x_chem = [0, hole_max_rad, hole_max_rad, 0, 0]
            y_chem = [0, 0, top, top, 0]
        Hole_reamer3D = self._make_pipe(x_chem, y_chem, hole.label + '_reamer', origin=hole_pos,
                                 orientation='V', theta=angle)
        return Hole_reamer3D

    def cut_chem(self, Cx, Cy, Hole3D):
        Sketch = Hole3D.newObject('Sketcher::SketchObject')
        Sketch.Placement = FreeCAD.Placement(FreeCAD.Vector(0, 0, 0),
                                             FreeCAD.Rotation(FreeCAD.Vector(1, 0, 0), 0))#-theta))

    	#	We build the main bore reamer
        N_interne = len(Cx)
        for j in range(N_interne-1):
            Sketch.addGeometry(Part.LineSegment(FreeCAD.Vector(Cx[j],Cy[j],0),
                                                FreeCAD.Vector(Cx[j+1],Cy[j+1],0)),
                               False)

        # We use it to cut the chimney
        Decoupe = Hole3D.newObject('PartDesign::Groove')
        Decoupe.Profile = Sketch
        Decoupe.ReferenceAxis = (Sketch, ['H_Axis'])
        Decoupe.Angle = 360.0
        Decoupe.Midplane = 0
        Decoupe.Reversed = 1
        return

    def get_chimney(self, hole, angle):
        hole_pos, hole_length, hole_max_rad, main_radius = self.hole_characteristics(hole)
        x = np.array([0, 1])
        rad_shape_flip = np.flip(hole.shape.get_radius_at(x)*1e3).tolist()
        pos_shape_flip = np.flip(hole.shape.get_position_from_xnorm(x)*1e3 + main_radius).tolist()

        x_chem = [hole_max_rad, hole_max_rad] + rad_shape_flip + [rad_shape_flip[-1], hole_max_rad]
        y_chem = [0, hole_length+main_radius] + pos_shape_flip + [0, 0]


        Hole3D = self._make_pipe(x_chem, y_chem, hole.label, origin=hole_pos, orientation='V', theta=angle)
        x_reamer, y_reamer =  self.get_reamer_mb()
        self.cut_chem(x_reamer, y_reamer, Hole3D)
        return Hole3D
