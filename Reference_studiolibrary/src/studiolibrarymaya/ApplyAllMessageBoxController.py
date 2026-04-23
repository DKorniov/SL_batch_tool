# Copyright 2020 by Kurt Rathjen. All Rights Reserved.
#
# This library is free software: you can redistribute it and/or modify it 
# under the terms of the GNU Lesser General Public License as published by 
# the Free Software Foundation, either version 3 of the License, or 
# (at your option) any later version. This library is distributed in the 
# hope that it will be useful, but WITHOUT ANY WARRANTY; without even the 
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the GNU Lesser General Public License for more details.
# You should have received a copy of the GNU Lesser General Public
# License along with this library. If not, see <http://www.gnu.org/licenses/>.
"""
The capture dialog is used for creating thumbnails and thumbnail playblasts.

import mutils.gui
print mutils.gui.capture("c:/temp/test.jpg", startFrame=1, endFrame=100)
# c:/temp/test.0001.jpg
"""

import os
import shutil

from studiovendor.Qt import QtCore
from studiovendor.Qt import QtWidgets

import mutils.gui
from studiolibrarymaya.ApplyAllMessageBox import Ui_applyAllMessageBoxDialog



__all__ = [
    "ShowApplyAllMessageBoxDialog",
    ]


_instance = None

def ShowApplyAllMessageBoxDialog(parent=None):
    global _instance

    if _instance:
        _instance.close()

    d = ApplyAllMessageBoxDialog(parent=parent)
    ui = Ui_applyAllMessageBoxDialog()
    ui.setupUi(d)

    d.initParams(ui, parent)

    d.show()

    _instance = d

    return _instance


class ApplyAllMessageBoxDialog(QtWidgets.QDialog):

    windowClosed = QtCore.Signal(int)

    def __init__(self, parent=None):
        parent = parent or mutils.gui.mayaWindow()

        self.initParams()

        QtWidgets.QDialog.__init__(self, parent)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
    
    def initParams(self, ui=None, parent=None):
        if parent:
            self.setStyleSheet(parent.getStyleShit())
            self.updateGeometry()
        self._index = 0
        if ui:
            ui.radioButton_1.setChecked(True)
    
    def updateGeometry(self):
        parentGeometry = self.parent().geometry()

        geometry = self.geometry()
        centerPoint = parentGeometry.center()
        geometry.moveCenter(centerPoint)
        geometry.setY(geometry.y() - 50)
        self.move(geometry.topLeft())

    def onRadioOptionSource(self):
        self._index = 0
    def onRadioOptionQueue(self):
        self._index = 1
    def onRadioOptionEvery100(self):
        self._index = 2

    def accept(self):
        print("accept")
        self.close()
        self.windowClosed.emit(self._index)
    def reject(self):
        print("reject")
        self.close()
    
    def closeEvent(self, *args, **kwargs):
        global _instance
        _instance = None
