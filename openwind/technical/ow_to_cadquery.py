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

import os
import numpy as np
import warnings

# try:
#     import cadquery as cq
# except ImportError:
#     warnings.warn('The OWtoCadQuery class requires the CadQuery library, which does not appear to be installed.')


from openwind.design import Cone


class OWtoCadQuery():
    """
    Generate the 3D geometry of an instrument coming from OW with CadQuery .

    CadQuery is an open-source and free librairy. It can be downloaded here:
    https://cadquery.readthedocs.io/en/latest/installation.html


    Parameters
    ----------
    instrument_geometry : openwind.technical.instrument_geometry.InstrumentGeometry
        The instrument geometry. See: :py:class:`InstrumentGeometry<openwind.technical.instrument_geometry.InstrumentGeometry>`.
    leveled_chimney : booelan, optional
        If true the wall width of the main bore is adjusted to fit the chimney
        length. Otherwise, the chimney are made of tubes protruding of the wall.
        The default is True.
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



    def __init__(self, instrument_geometry, leveled_chimney=True, angles=None,
                 step=2, wall_width=3, chim_width=2):
        self.instru_geom = instrument_geometry
        if len(instrument_geometry.valves)>0:
            warnings.warn('The valves (or piston) of brass instrument, are not'
                          ' handled by this tool. Only the main bore '
                          '(unwrapped) and the holes are managed.\n', stacklevel=2)

        self.leveled_chimney = leveled_chimney
        self.wall_width = wall_width
        self.chim_width = chim_width
        self.step=step
        if angles is None:
            angles = [0]*len(self.instru_geom.holes)
        if len(angles) != len(self.instru_geom.holes):
            raise ValueError(f'Please indicate one angle per hole: here {len(angles)} angles for {len(self.instru_geom.holes)} holes.')
        self.angles = angles

        try:
            self.cq = __import__('cadquery')
        except ImportError as err:
            raise ImportError("This feature needs the library CadQuery, please install it.") from err

        # try:
        self._construction = self.cq.Assembly(name='Construction_Stages')
        # except NameError:
        #     raise ImportError("This feature needs the library CadQuery, please install it.")
        self._3Dinstrument = self.build_instru3D()

    @staticmethod
    def _fuse_list3D(list3D):
        if not list3D:
            raise ValueError("Empty solid list to fuse")
        base = list3D[0]
        if len(list3D)>1:
            for s in list3D[1:]:
                base = base.fuse(s)
        return base

    # @staticmethod
    def _make_pipe(self, x, y, label='label', origin=0, orientation='H', theta=0):
        if orientation=='V':
            coordinates = [(_y,_x) for _x,_y in zip(x,y)]
            end_ax_rot = (0,1)
        else:
            coordinates = [(_x,_y) for _x,_y in zip(x,y)]
            end_ax_rot = (1,0)
        wp_loc = self.cq.Workplane('XY').center(origin, 0)
        profile = wp_loc.polyline(coordinates).close()
        pipe = profile.revolve(axisStart=(0,0), axisEnd=end_ax_rot).rotate((0,0,0),(1,0,0), theta)
        return pipe.val()

    def get_3Dobject(self):
        return self._3Dinstrument

    def build_instru3D(self):
        """
        Generate the 3D object

        Returns
        -------
        full_instru3D : cadquery object
            The cadquery object corresponding to the final instrument.

        """
        main_bore3D = self.build_main_bore()
        # print('The main bore has been generated')
        if len(self.instru_geom.holes)>0:
            bore_drilled = self.drill_holes_in_mainbore(main_bore3D)
            # print('The main bore has been drilled')
            if not self.leveled_chimney:
                holes_chim3D = self.build_holes_chimneys()
                # print('The chimney pipes have been generated')
                full_instru3D = self._fuse_list3D([bore_drilled, holes_chim3D])
                # print('All elements have been fused.')
            else:
                full_instru3D = bore_drilled
        else:
            full_instru3D = main_bore3D
        return full_instru3D

    def export(self, filename, tolerance=2, angularTolerance=0.1,
               with_construction_stages=True, exportType=None,
               **kwargs):
        """
        Export the 3D-object in a file and, if needed, generates a mesh.

        Parameters
        ----------
        filename : str
            The full filename (with path).
        tolerance : float, optional
            The deflection tolerance in mm. The default is 2.
        angularTolerance : float, optional
            The angular reference in rad. The default is 0.1.
        with_construction_stages: bool, optional
            Only used for step files, if True, save also all the objects used for
            the construction stages. The default is True.
        **kwargs : dict()
            Other keyword arguments for :py:func:`cadquery.exporters.export()`.

        See Also
        --------
        :py:func:`cadquery.exporters.export()`: the original export function from
        CadQuery

        """
        label, ext = os.path.splitext(os.path.basename(filename))
        assembly = self.cq.Assembly(name='Openwind-3D')
        assembly.add(self._3Dinstrument, name='full instrument')
        if with_construction_stages and (ext.lower()=='.step' or exportType=='STEP'):
            assembly.add(self._construction)
        assembly.export(filename, tolerance=tolerance*1e-3,
                        angularTolerance=angularTolerance, exportType=exportType,
                        **kwargs)

    def build_main_bore(self):
        """
        Build the 3D-object corresponding to the main bore.

        Returns
        -------
        main_bore3D : CadQuery object
            The main bore in 3D.

        """

        pos_in, rad_in = self._get_mb_internal_geom()

        # adaptation of the wall width at the location of the chimney
        pos_out = np.array(pos_in)
        rad_out = np.array(rad_in) + self.wall_width
        for hole in self.instru_geom.holes:
            hole_pos, hole_length, hole_max_rad, main_radius = self._hole_characteristics(hole)
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


        position_face = pos_in + np.flip(pos_out).tolist()
        radius_face = rad_in + np.flip(rad_out).tolist()

        main_bore3D = self._make_pipe(position_face, radius_face, 'Main_Bore')
        self._construction.add(main_bore3D, name='Main Bore', color=self.cq.Color('green'))
        return main_bore3D

    def drill_holes_in_mainbore(self, main_bore3D):
        """
        Drill the main bore by the hole.

        Following the value of the option `leveled_chimney` this correspond to
        the final holes or they are wider in order to add the chimney pipe
        during the next step.

        Parameters
        ----------
        main_bore3D : CadQuery 3D object
            The main bore in 3D.

        Returns
        -------
        bore_drilled : CadQuery 3D object
            The main bore, drilled, in 3D.

        """
        holes_reamer3D = self._build_holes_reamer()
        self._construction.add(holes_reamer3D, name='holes drill bit', color=self.cq.Color('red'))
        bore_drilled = main_bore3D.cut(holes_reamer3D)
        self._construction.add(bore_drilled, name='Bore drilled', color=self.cq.Color('green'))
        return bore_drilled

    def _build_holes_reamer(self):
        holes_reamer = [self._get_reamer_hole(h, a)
                        for h, a in zip(self.instru_geom.holes, self.angles)]
        return self._fuse_list3D(holes_reamer)

    def build_holes_chimneys(self):
        """
        Build the chimney pipes.

        Only if option `leveled_chimney` is set to False.

        Returns
        -------
        CadQuery 3D object
            The ensemble of the chimney pipes.

        """
        holes_chim  = self._fuse_list3D([self._get_chimney(h, a)
                                         for h, a in zip(self.instru_geom.holes, self.angles)])
        mb_reamer = self._get_reamer_mb()
        cutted_chim = holes_chim.cut(mb_reamer)

        self._construction.add(holes_chim, name='Full chimneys', color=self.cq.Color('orange'))
        self._construction.add(mb_reamer, name='Reamer', color=self.cq.Color('red'))
        self._construction.add(cutted_chim, name='Bored Chimneys', color=self.cq.Color('green'))

        return cutted_chim

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


    def _get_reamer_mb(self):
        pos_in, rad_in = self._get_mb_internal_geom()
        x_reamer = [pos_in[0]] + pos_in + [pos_in[-1]]
        y_reamer = [0] + rad_in + [0]
        reamer = self._make_pipe(x_reamer, y_reamer, origin=0, orientation="H")
        return reamer


    def _hole_characteristics(self, hole):
        hole_pos = hole.position.get_value()*1e3
        hole_length = hole.shape.get_length()*1e3
        hole_max_rad = max(hole.shape.get_radius_at(np.linspace(0,1,10)))*1e3 + self.chim_width
        main_radius = self.instru_geom.get_main_bore_radius_at(hole_pos*1e-3)*1e3
        return hole_pos, hole_length, hole_max_rad, main_radius

    def _get_reamer_hole(self, hole, angle):
        hole_pos, hole_length, hole_max_rad, main_radius = self._hole_characteristics(hole)
        # we prolongate the reamer to be sure to pass trough the MB wall
        top = hole_length + main_radius + 2*self.wall_width
        if self.leveled_chimney:
            x = np.array([0, 1])
            rad_shape = (hole.shape.get_radius_at(x)*1e3).tolist()
            pos_shape = (hole.shape.get_position_from_xnorm(x)*1e3).tolist()
            x_chem = [0] + pos_shape + [top, top]
            y_chem = [0] + rad_shape + [rad_shape[-1], 0]
        else: # if we add the chimney after, we drill with a cylinder
            x_chem = [0, 0, top, top]#, 0]
            y_chem = [0, hole_max_rad, hole_max_rad, 0]#, 0]
        Hole_reamer3D = self._make_pipe(x_chem, y_chem, hole.label + '_reamer', origin=hole_pos,
                                 orientation='V', theta=angle)
        return Hole_reamer3D

    def _get_chimney(self, hole, angle):
        hole_pos, hole_length, hole_max_rad, main_radius = self._hole_characteristics(hole)
        xs = np.array([0, 1])
        rad_shape_flip = np.flip(hole.shape.get_radius_at(xs) * 1e3).tolist()
        pos_shape_flip = np.flip(hole.shape.get_position_from_xnorm(xs) * 1e3 + main_radius).tolist()

        x_chem = [0, hole_length + main_radius] + pos_shape_flip + [0]
        y_chem = [hole_max_rad, hole_max_rad] + rad_shape_flip + [rad_shape_flip[-1]]

        hole_solid = self._make_pipe(x_chem, y_chem, origin=hole_pos, orientation="V", theta=angle)
        return hole_solid

    @staticmethod
    def _plot3D_layout():
        try:
            import plotly.graph_objs as go
        except ImportError as err:
            msg = "The 3D visualization requires plotly."
            raise ImportError(msg) from err

        fig = go.Figure()

        fig.update_layout(scene_aspectmode="data",
                          margin=dict(l=0, r=0, t=0, b=0),
                          # plot_bgcolor='#f8f9fa',
                          # font={"size":16},
                          scene=dict(xaxis=dict(visible=False, showbackground=False, showticklabels=False),
                                     yaxis=dict(visible=False, showbackground=False, showticklabels=False),
                                     zaxis=dict(visible=False, showbackground=False, showticklabels=False)
                                     ),
                          )
        return fig

    @staticmethod
    def _plot3D_texturesmenu():
        textures = {"Neutral": dict(color="rgb(120, 120, 130)",
                                    lighting=dict(ambient=0.5, diffuse=0.75, specular=0.5, roughness=0.45, fresnel=0.1),
                                    ),
                    'Boxwood':dict(color = "rgb(215, 190, 120)",
                                   lighting = dict(ambient=0.35, diffuse=0.7, specular=0.5, roughness=0.35, fresnel=0.12),
                                   ),
                    'Brass':dict(color ="rgb(150, 120, 50)",
                                 lighting = dict(ambient=0.25, diffuse=0.6, specular=1.8, roughness=0.2, fresnel=0.3),
                                 ),
                    'Ebony':dict(color = "rgb(35, 28, 22)",
                                 lighting = dict(ambient=0.25, diffuse=0.7, specular=0.9, roughness=0.3, fresnel=0.15),
                                 ),
                    }

        buttons = []
        for name, tex in textures.items():
            buttons.append(dict(label=name, method="update", args=[tex]))

        menu =dict(type="dropdown",
                   x=0.05, y=.95, xanchor="left", yanchor="bottom",
                   buttons=buttons,
                   bgcolor="rgba(255,255,255,0.8)"
                   )
        return menu, textures

    def _add_3Dplot(self, fig, textures=dict()):
        verts, faces = self._3Dinstrument.tessellate(tolerance=2e-3,
                                                     angularTolerance=0.1)
        V = np.array([v.toTuple() for v in verts])
        F = np.array(faces, dtype=int)

        if isinstance(textures, dict) and len(textures)>1:
            first = next(iter(textures))
            default = textures[first]
        else:
            default = dict()

        fig.add_mesh3d(x=list(V[:,0]), y=list(V[:,1]), z=list(V[:,2]),
                       i=list(F[:,0]), j=list(F[:,1]), k=list(F[:,2]),
                       flatshading=False,
                       opacity=1.0,
                       **default
                       )
        return fig

    def plot_3Dobject(self):
        fig = self._plot3D_layout()
        menu, textures = self._plot3D_texturesmenu()
        fig.update_layout(updatemenus=[menu])
        fig.add_annotation(x=0.05, y=.95,xanchor="right", yanchor="bottom",
                           showarrow=False,
                           text="Textures:",
                           font={"size":16, 'weight':'bold'}
                           )
        fig = self._add_3Dplot(fig, textures)
        return fig
