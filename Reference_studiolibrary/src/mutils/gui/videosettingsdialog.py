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

import studioqt

import mutils.gui
from mutils.gui.videosettings import Ui_settings_preview

try:
    import maya.cmds
except ImportError as error:
    print(error)


__all__ = [
    "InitVideoSettings",
    "ShowVideoSettings",
    "VideoSettingsDialog"
    ]


_instance = None

def InitVideoSettings():
    if not maya.cmds.optionVar(exists="VideoSettingsImageFormat"):
        maya.cmds.optionVar(iv=("VideoSettingsImageFormat", 0))
    if not maya.cmds.optionVar(exists="VideoSettingsSizeIndex"):
        maya.cmds.optionVar(iv=("VideoSettingsSize", 500))
        maya.cmds.optionVar(iv=("VideoSettingsSizeIndex", 0))
    if not maya.cmds.optionVar(exists="VideoSettingsConvertMp4"):
        maya.cmds.optionVar(iv=("VideoSettingsConvertMp4", 1))

def ShowVideoSettings():
    global _instance

    if _instance:
        _instance.close()

    InitVideoSettings()
    d = VideoSettingsDialog()
    videoSettings = Ui_settings_preview()
    videoSettings.setupUi(d)
    d.initValues(videoSettings)

    d.show()

    _instance = d

    return _instance


class VideoSettingsDialog(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        parent = parent or mutils.gui.mayaWindow()

        QtWidgets.QMainWindow.__init__(self, parent)

    def initValues(self, videoSettings):
        videoSettings.sizeComboBox.setCurrentIndex(maya.cmds.optionVar(q='VideoSettingsSizeIndex'))
        videoSettings.checkBoxMp4.setChecked(maya.cmds.optionVar(q='VideoSettingsConvertMp4'))
        videoSettings.radioButtonJpg.setChecked(maya.cmds.optionVar(q='VideoSettingsImageFormat') == 0)
        videoSettings.radioButtonPng.setChecked(maya.cmds.optionVar(q='VideoSettingsImageFormat') == 1)
        

    def onSizeChange(self, index):
        print("onSizeChange" + str(index))
        size = 500
        if index == 1:
            size = 800
        elif index == 2:
            size = 1000
        maya.cmds.optionVar(iv=("VideoSettingsSize", size))
        maya.cmds.optionVar(iv=("VideoSettingsSizeIndex", index))
    
    def onVideoFormatChange(self, index):
        print("onVideoFormatChange" + str(index))
        maya.cmds.optionVar(iv=("VideoSettingsConvertMp4", index != 0))

    def onImageFormatJpg(self):
        print("onImageFormatJpg")
        maya.cmds.optionVar(iv=("VideoSettingsImageFormat", 0))
    
    def onImageFormatPng(self):
        print("onImageFormatPng")
        maya.cmds.optionVar(iv=("VideoSettingsImageFormat", 1))