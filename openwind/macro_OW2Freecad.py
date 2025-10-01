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
This file, is a macro designed to be executed from the FreeCAD GUI.
It open a window giving the possibility to chose some parameters and generate
a 3D file corresponding to a given geometry.
"""

import os
import sys
import warnings

# try:
from PySide import QtGui # QtCore,
import FreeCAD
import ImportGui
import Mesh, MeshPart

# add openwind to the path
# ow_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# sys.path.append(ow_path)
try:
    from openwind.technical.ow_to_freecad import OWtoFreeCAD
except ImportError:
    ow_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    print(f'Add {ow_path} to the python path')
    sys.path.append(ow_path)
    from openwind.technical.ow_to_freecad import OWtoFreeCAD

class Ui_OW2FreeCAD(object):

    def __init__(self, MainWindow):
        """
        Fill a window with the GUI to generate 3D file with freecad

        .. warning::
            This class is thank to be used and execute from FreeCAD interface.

        Parameters
        ----------
        MainWindow : QtGui.QMainWindow
            The window in which display the interface.

        """

        self.path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        self.window = MainWindow
        MainWindow.setObjectName(("MainWindow"))
        MainWindow.resize(800, 300)
        MainWindow.setWindowTitle("Openwind to FreeCAD")
        self.centralWidget = QtGui.QWidget(MainWindow)
        self.centralWidget.setObjectName(("centralWidget"))
        self.centralWidget.setStyleSheet("QGroupBox { font-weight: bold; font-size: 14pt;} ")


        input_box = self._input_file_group_box()

        option_Box = self._option_box()

        vbox = QtGui.QGridLayout()
        vbox.setColumnStretch(0, 3)
        vbox.setColumnStretch(1, 1)
        vbox.setColumnStretch(2, 1)
        vbox.setColumnStretch(3, 3)
        vbox.addWidget(input_box, 0, 0, 1, 2)
        vbox.addWidget(option_Box, 0, 2, 2, 2)

        save_Box = QtGui.QGroupBox("Output file")
        save_Box.setMinimumWidth(self.window.size().width()/2-10)
        gridbox = QtGui.QGridLayout()
        gridbox.setColumnStretch(0, 6)
        gridbox.setColumnStretch(1, 1)
        title_label, self.save_path, path_Button = self.get_files('Path to save the 3D object',
                                                                    self.get_save_path,
                                                                    self.on_save_path_clicked)
        gridbox.addWidget(title_label, 3, 0, 1, -1)
        gridbox.addWidget(self.save_path, 4, 0)
        gridbox.addWidget(path_Button, 4,1)
        save_Box.setLayout(gridbox)

        vbox.addWidget(save_Box, 1, 0, 1, 2)

        self.ok_button =  self.validation()
        vbox.addWidget(self.ok_button, 2, 1, 1, 2)

        self.enable_holes_options(False)
        self.centralWidget.setLayout(vbox)
        MainWindow.setCentralWidget(self.centralWidget)


    def _input_file_group_box(self):
        # Create the group box
        groupBox = QtGui.QGroupBox("Input files")
        groupBox.setMinimumWidth(self.window.size().width()/2-10)

        # create the frame
        gridbox = QtGui.QGridLayout()
        gridbox.setColumnStretch(0, 6)
        gridbox.setColumnStretch(1, 1)

        # The mainbore file
        title_mb, self.mb_path, mb_Button = self.get_files('Path of main bore geometry',
                                                                self.get_mb_path, self.on_mb_path_clicked)
        gridbox.addWidget(title_mb, 3, 0, 1, -1)
        gridbox.addWidget(self.mb_path, 4, 0)
        gridbox.addWidget(mb_Button, 4,1)

        # a vertical space
        gridbox.setRowMinimumHeight(5, 10)

        # the hole file
        title_hole, self.hole_path, hole_Button = self.get_files('Path of the holes geometry (let empty if no hole)',
                                            self.get_hole_path, self.on_hole_path_clicked)
        gridbox.addWidget(title_hole, 6, 0, 1, -1)
        gridbox.addWidget(self.hole_path, 7, 0)
        gridbox.addWidget(hole_Button, 7,1)

        groupBox.setLayout(gridbox)

        return groupBox

    def _option_box(self):
        option_Box = QtGui.QGroupBox("Options")
        option_Box.setMinimumWidth(self.window.size().width()/2-10)

        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self._options_mb())
        self.hole_opt = self._options_holes()
        vbox.addWidget(self.hole_opt)
        option_Box.setLayout(vbox)

        return option_Box


    def _options_mb(self):
        mb_opt = QtGui.QGroupBox("Main Bore options")
        mb_opt.setStyleSheet("QGroupBox {font-weight: normal; font-style: italic; font-size: 12pt;} ")

        self.wall_width, leg_width = self.create_spin_box(0.1, 100.0, 3.0,
                                            'Wall width of the main bore',
                                            ('In presence of holes, the width can be locally adpated to make sure\n'
                                            ' that the chimney goes trough the wall.'))


        self.step, leg_step = self.create_spin_box(0.1, 10.0, 2.0,
                                            'Step to slice the non-conical parts',
                                            'Only if the instrument contains non-conical parts')

        gridbox = QtGui.QGridLayout()
        gridbox.setColumnStretch(0, 1)
        gridbox.setColumnStretch(1, 5)

        gridbox.addWidget(self.wall_width, 0, 0)
        gridbox.addWidget(leg_width, 0, 1)

        gridbox.addWidget(self.step, 1, 0)
        gridbox.addWidget(leg_step, 1, 1)

        mb_opt.setLayout(gridbox)

        return mb_opt

    def _options_holes(self):
        hole_opt = QtGui.QGroupBox("Holes options")
        hole_opt.setStyleSheet("QGroupBox {font-weight: normal; font-style: italic; font-size: 12pt;} ")

        self.flush = QtGui.QCheckBox(self.centralWidget)
        self.flush.setChecked(False)
        self.flush.setObjectName(("checkBoxON"))
        self.flush.setText("The chimneys are flush with the external wall")
        self.flush.setToolTip(("If un-checked, the chimneys are made of pipe geting out the main bore pipe.\n"
                                    " Otherwise the main bore wall width is adapted to the chimney length."))
        self.flush.clicked.connect(self.set_flush)


        self.chim_width, leg_chim = self.create_spin_box(0.1, 10.0, 2.0,
                                            'Wall width of the chimneys',
                                            'Only used if the chimney are NOT flush')


        angle_label = QtGui.QLabel(self.centralWidget)
        angle_label.setText('Angle of the Holes around the main axis (in degree):')


        self.angles = QtGui.QLineEdit(self.centralWidget)
        self.angles.setText('None')
        self.angles.setToolTip('Indicate 1 value per hole separated by ";".\n'
                                'If "None", all the holes are aligned')



        gridbox = QtGui.QGridLayout()
        gridbox.setColumnStretch(0, 1)
        gridbox.setColumnStretch(1, 5)

        gridbox.addWidget(self.flush, 0, 0, 1, -1)

        gridbox.addWidget(self.chim_width, 1, 0)
        gridbox.addWidget(leg_chim, 1, 1)

        gridbox.addWidget(angle_label, 2, 0, 1, -1)
        gridbox.addWidget(self.angles, 3, 0, 1, -1)

        hole_opt.setLayout(gridbox)

        return hole_opt

    def enable_holes_options(self, is_enable):
        """Enable or disable the options relative to the holes"""
        QtGui.QWidget.setEnabled(self.hole_opt, is_enable)

    def set_flush(self):
        """Enable-Disable the chimney width following the flush chimney option"""
        QtGui.QWidget.setDisabled(self.chim_width, self.flush.checkState())


    @staticmethod
    def create_spin_box(minimum, maximum, value, text, tip):
        """
        Create a QSpinBox

        Parameters
        ----------
        minimum : float
            Minimal value authorized.
        maximum : float
            Maximal value authorized.
        value : float
            Initial value.
        text : string
            legend of the spin box.
        tip : str
            Tips display when fly over the spin box.

        Returns
        -------
        spinbox : QDoubleSpinBox
            The spin box widget.
        legend : QLabel
            The legend widget .

        """

        spinbox = QtGui.QDoubleSpinBox()
        spinbox.setMinimum(minimum)
        spinbox.setMaximum(maximum)
        spinbox.setSingleStep(0.1)
        spinbox.setValue(value)
        spinbox.setToolTip(tip)
        spinbox.setSuffix(' mm')
        legend = QtGui.QLabel(text)
        return spinbox, legend

    def validation(self):
        """Create the validation button"""
        pushButton = QtGui.QPushButton("OK")
        pushButton.setObjectName(("pushButton"))
        pushButton.setStyleSheet("QPushButton {font-weight: bold; font-size: 14pt;} ")
        pushButton.clicked.connect(self.on_pushButton_clicked) #connection pushButton
        return pushButton

    def get_mb_path(self):
        """Method to get the main bore path"""
        mb_path, Filter = QtGui.QFileDialog.getOpenFileName(None, "Main bore file",
                                                            self.path, "Text file (*.txt *.csv);; openwind file (*.ow)")
        self.mb_path.setText(mb_path)
        self.on_mb_path_clicked()

    def on_mb_path_clicked(self):
        """What to do when the new main bore path is defined"""
        mb_path = self.mb_path.displayText()
        self.path, fname = os.path.split(mb_path)
        full = os.path.splitext(mb_path)[0]
        self.save_path.setText(full.split('_MainBore')[0] + '.stl')
        self.enable_holes_options(fname.endswith('.ow'))


    def get_hole_path(self):
        """Method to get the hole path"""
        hole_path, Filter = QtGui.QFileDialog.getOpenFileName(None, "Hole file",
                                                                self.path, "Text file (*.txt *.csv)")
        self.hole_path.setText(hole_path)

    def on_hole_path_clicked(self):
        """What to do when a hole path is defined: enable the holes options"""
        self.enable_holes_options(len(self.hole_path.displayText())>0)

    def on_save_path_clicked(self):
        """What to do when save path is defined: nothing"""
        pass

    def get_save_path(self):
        """Get save path"""
        save_path, Filter = QtGui.QFileDialog.getSaveFileName(None, "Save 3D object",
                                                                self.path, "STL file (*.stl);; Step file (*.step)")
        self.save_path.setText(save_path)


    def get_files(self, title, connect_push, connect_path):
        """
        Get a file a direction and apply some methods

        Parameters
        ----------
        title : str
            The title the field.
        connect_push : method
            What tot do when the "..." button is pressed.
        connect_path : method
            What to do when the path is modified.

        Returns
        -------
        path_obj : QLineEdit
            The widget with the path.
        y0 : float
            The new vertical position.

        """


        title_label = QtGui.QLabel(title)
        title_label.setText(title)


        path_obj = QtGui.QLineEdit()
        path_obj.textChanged.connect(connect_path)

        path_Button = QtGui.QPushButton('explore')
        path_Button.clicked.connect(connect_push) #connection pushButton

        return title_label, path_obj, path_Button


    def on_pushButton_clicked(self):
        """ What to do when the OK button is pressed"""

        mb_path = self.mb_path.displayText()
        holes_path = self.hole_path.displayText()
        if holes_path == '':
            holes_path = list()

        fname = os.path.split(self.save_path.displayText())[1]
        name = os.path.splitext(fname)[0]

        if self.angles.displayText() in ['None', '', ' ']:
            angles = None
        else:
            try:
                angles =  [float(a) for a in  self.angles.displayText().split(';')]
            except:
                raise ValueError('Angle format not recognized: please indicate values separated by ";".')

        # Create a new FreeCAD document
        doc = FreeCAD.newDocument(name)

        # Build the instrument
        my_instru3D = OWtoFreeCAD(doc, mb_path, holes_path,
                                    leveled_chimney=self.flush.checkState(),
                                    step=self.step.value(),
                                    wall_width=self.wall_width.value(),
                                    chim_width=self.chim_width.value(),
                                    angles=angles)
        full_instru3D = my_instru3D.build_instru3D()
        # Centered the view
        FreeCAD.Gui.SendMsgToActiveView("ViewFit")
        # Save
        if self.save_path.displayText().endswith('step'):
            ImportGui.export([full_instru3D], self.save_path.displayText())
        elif self.save_path.displayText().endswith('stl'):
            my_mesh = doc.addObject("Mesh::Feature","Mesh")
            my_mesh.Mesh = MeshPart.meshFromShape(full_instru3D.Shape, LinearDeflection=0.1, AngularDeflection=0.087, Relative=False)
            Mesh.export([my_mesh], self.save_path.displayText())

        self.window.hide()



        msgBox = QtGui.QMessageBox()
        msgBox.setText("Success! The instrument has been build!\n")
        msgBox.setInformativeText("It has been saved in:\n\n{}".format(self.save_path.displayText()))
        msgBox.exec_()
        FreeCAD.Console.PrintMessage("\nFile saved in:\n{}".format(self.save_path.displayText()))
        self.window.close()


# Generate a window
my_main = QtGui.QMainWindow()
# fill the window
ui = Ui_OW2FreeCAD(my_main)
# show the window
my_main.show()

# except ImportError:
#    warnings.warn('FreeCAD is not install on this environnement.\n'
#                   'The "macro" has been designed to be executed directly on FreeCAD GUI.')
