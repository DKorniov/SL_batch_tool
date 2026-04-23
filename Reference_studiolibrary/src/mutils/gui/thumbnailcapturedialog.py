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

try:
    import maya.cmds
except Exception:
    import traceback
    traceback.print_exc()

import studioqt

import mutils.gui
import mutils.gui.modelpanelwidget


__all__ = [
    "thumbnailCapture",
    "thumbnailCaptureExec",
    "ThumbnailCaptureDialog",
    ]


_instance = None


def thumbnailCapture(
        path,
        startFrame=None,
        endFrame=None,
        step=1,
        clearCache=False,
        captured=None,
        show=False,
        modifier=True,
        video=False,
        delegate=None,
        beforeCaprtureCallback=None,
        modelPanel=None
):
    """
    Capture a playblast and save it to the given path.

    :type path: str
    :type startFrame: int or None
    :type endFrame:  int or None
    :type step: int
    :type clearCache: bool
    :type captured: func or None
    :rtype: ThumbnailCaptureDialog
    """

    global _instance

    def _clearCache():
        dirname = os.path.dirname(path)
        if os.path.exists(dirname):
            shutil.rmtree(dirname)

    if _instance:
        _instance.close()

    d = mutils.gui.ThumbnailCaptureDialog(
        path=path,
        startFrame=startFrame,
        endFrame=endFrame,
        step=step,
        video=video,
        delegate=delegate,
        beforeCaprtureCallback=beforeCaprtureCallback,
        modelPanel=modelPanel
    )

    if captured:
        d.captured.connect(captured)

    if clearCache:
        d.capturing.connect(_clearCache)

    d.show()

    if not show and not (modifier and studioqt.isControlModifier()):
        d.capture()
        d.close()

    _instance = d

    return _instance

def thumbnailCaptureExec(
        path,
        startFrame=None,
        endFrame=None,
        step=1,
        clearCache=False,
        captured=None,
        show=False,
        modifier=True,
        video=False,
        delegate=None,
        beforeCaprtureCallback=None,
        modelPanel=None
):
    """
    Capture a playblast and save it to the given path.

    :type path: str
    :type startFrame: int or None
    :type endFrame:  int or None
    :type step: int
    :type clearCache: bool
    :type captured: func or None
    :rtype: ThumbnailCaptureDialog
    """

    global _instance

    def _clearCache():
        dirname = os.path.dirname(path)
        if os.path.exists(dirname):
            shutil.rmtree(dirname)

    if _instance:
        _instance.close()

    d = mutils.gui.ThumbnailCaptureDialog(
        path=path,
        startFrame=startFrame,
        endFrame=endFrame,
        step=step,
        video=video,
        delegate=delegate,
        beforeCaprtureCallback=beforeCaprtureCallback,
        modelPanel=modelPanel
    )

    if captured:
        d.captured.connect(captured)

    if clearCache:
        d.capturing.connect(_clearCache)

    if show:
        d.exec_()
    else:
        d.show()
        d.capture()
    d.close()

    return d

class ThumbnailCaptureDialog(QtWidgets.QDialog):

    DEFAULT_WIDTH = 250
    DEFAULT_HEIGHT = 250

    captured = QtCore.Signal(str)
    capturing = QtCore.Signal(str)

    def __init__(self, path="", parent=None, startFrame=None, endFrame=None, step=1, video=False, delegate=None, beforeCaprtureCallback=None, modelPanel=None):
        """
        :type path: str
        :type parent: QtWidgets.QWidget
        :type startFrame: int
        :type endFrame:  int
        :type step: int
        """
        parent = parent or mutils.gui.mayaWindow()

        QtWidgets.QDialog.__init__(self, parent)

        self._path = path
        self._step = step
        self._endFrame = None
        self._startFrame = None
        self._capturedPath = None
        self._video = video
        self._delegate = delegate
        self._beforeCaprtureCallback = beforeCaprtureCallback
        self._modelPanel = modelPanel

        if endFrame is None:
            endFrame = int(maya.cmds.currentTime(query=True))

        if startFrame is None:
            startFrame = int(maya.cmds.currentTime(query=True))

        self.setEndFrame(endFrame)
        self.setStartFrame(startFrame)

        self.setObjectName("CaptureWindow")
        self.setWindowTitle("Capture Window")

        self._captureButton = QtWidgets.QPushButton("Capture")
        self._captureButton.clicked.connect(self.capture)

        self._modelPanelWidget = mutils.gui.modelpanelwidget.ModelPanelWidget(self)

        vbox = QtWidgets.QVBoxLayout(self)
        vbox.setObjectName(self.objectName() + "Layout")
        vbox.addWidget(self._modelPanelWidget)
        vbox.addWidget(self._captureButton)

        cameraHBox = QtWidgets.QHBoxLayout(self)
        cameraLabel = QtWidgets.QLabel()
        cameraLabel.setText("Camera:")
        cameraLabel.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        cameraHBox.addWidget(cameraLabel)
        cameraCombo = QtWidgets.QComboBox()
        cameraHBox.addWidget(cameraCombo)
        cameraCombo.currentIndexChanged.connect(self.onCameraIndexChange)
        vbox.addLayout(cameraHBox)

        cameras = self.getCameras()
        shortNameCameras = maya.cmds.listRelatives(cameras, parent=1)
        panel = maya.cmds.getPanel(withFocus=True)
        if self._modelPanel:
            panel = self._modelPanel
        selectedCamera = maya.cmds.lookThru(panel, q=True)
        names = []
        deep = -1
        while deep > -100:
            for cameraIndex in range(0, len(cameras)):
                camera = cameras[cameraIndex]
                shortName = camera
                if '|' in shortName:
                    shortName = shortName.split("|")[deep]
                    if deep != -1:
                        shortName = camera.split("|")[0] + '|' + shortName
                else:
                    shortName = shortNameCameras[cameraIndex]
                if shortName in names:
                    names.clear()
                    deep -= 1
                    break
                names.append(shortName)
            if len(names) == len(cameras):
                break
        for name in names:
            cameraCombo.addItem(name)
        cameraCombo.setCurrentIndex(shortNameCameras.index(selectedCamera))

        self.setLayout(vbox)

        width = (self.DEFAULT_WIDTH * 1.5)
        height = (self.DEFAULT_HEIGHT * 1.5) + 50

        self.setWidthHeight(width, height)
        self.centerWindow()

    def getCameras(self):
        cameras = maya.cmds.ls(cameras=True)
        if not cameras:
            return []
        return cameras
    
    def onCameraIndexChange(self, index):
        cameras = self.getCameras()
        panel = maya.cmds.getPanel( withFocus=True )
        if panel:
            maya.cmds.lookThru(panel, cameras[index])
        if self._modelPanel and self._modelPanel != panel:
            maya.cmds.lookThru(self._modelPanel, cameras[index])

    def path(self):
        """
        Return the destination path.

        :rtype: str
        """
        return self._path

    def setPath(self, path):
        """
        Set the destination path.

        :type path: str
        """
        self._path = path

    def endFrame(self):
        """
        Return the end frame of the playblast.

        :rtype: int
        """
        return self._endFrame

    def setEndFrame(self, endFrame):
        """
        Specify the end frame of the playblast.

        :type endFrame: int
        """
        self._endFrame = int(endFrame)

    def startFrame(self):
        """
        Return the start frame of the playblast.

        :rtype: int
        """
        return self._startFrame

    def setStartFrame(self, startFrame):
        """
        Specify the start frame of the playblast.

        :type startFrame: int
        """
        self._startFrame = int(startFrame)

    def step(self):
        """
        Return the step amount of the playblast.

        Example:
            if step is set to 2 it will playblast every second frame.

        :rtype: int
        """
        return self._step
    
    def video(self):
        """
        Return the type of the playblast.

        :rtype: bool
        """
        return self._video

    def setStep(self, step):
        """
        Set the step amount of the playblast.

        :type step: int
        """
        self._step = step

    def setWidthHeight(self, width, height):
        """
        Set the width and height of the window.

        :type width: int
        :type height: int
        :rtype: None
        """
        x = self.geometry().x()
        y = self.geometry().y()
        self.setGeometry(x, y, width, height)

    def centerWindow(self):
        """
        Center the widget to the center of the desktop.

        :rtype: None
        """
        geometry = self.frameGeometry()
        pos = QtWidgets.QApplication.desktop().cursor().pos()
        screen = QtWidgets.QApplication.desktop().screenNumber(pos)
        centerPoint = QtWidgets.QApplication.desktop().screenGeometry(
            screen).center()
        geometry.moveCenter(centerPoint)
        self.move(geometry.topLeft())

    def capturedPath(self):
        """
        Return the location of the captured playblast.

        :rtype:
        """
        return self._capturedPath

    def capture(self):
        """
        Capture a playblast and save it to the given path.

        :rtype: None
        """
        path = self.path()

        self.capturing.emit(path)

        modelPanel = self._modelPanelWidget.name()
        startFrame = self.startFrame()
        endFrame = self.endFrame()
        step = self.step()
        width = self.DEFAULT_WIDTH
        height = self.DEFAULT_HEIGHT

        if self._delegate and self._beforeCaprtureCallback:
            callback = getattr(self._delegate, self._beforeCaprtureCallback)
            callback()
        try:
            if self.video():
                self._capturedPath = mutils.playblast.playblastMovie(
                    path,
                    modelPanel,
                    startFrame,
                    endFrame,
                    width,
                    height,
                    step=step
                )
            else:
                self._capturedPath = mutils.playblast.playblast(
                    path,
                    modelPanel,
                    startFrame,
                    endFrame,
                    width,
                    height,
                    step=step
                )
        except Exception as e:
            raise e
        finally:
            self.accept()

        self.captured.emit(self._capturedPath)
        return self._capturedPath
