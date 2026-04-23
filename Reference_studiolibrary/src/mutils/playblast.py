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

import os
import sys
import logging
import subprocess
import mutils
import shutil

from studiolibrary.librarywindow import LibraryWindow
try:
    import maya.cmds
except Exception:
    import traceback
    traceback.print_exc()


__all__ = [
    "playblast",
]

logger = logging.getLogger(__name__)


# Valid Renderers:
# [u'vp2Renderer', u'base_OpenGL_Renderer',
#  u'hwRender_OpenGL_Renderer', u'stub_Renderer']
DEFAULT_PLAYBLAST_RENDERER = None


class PlayblastError(Exception):
    """Base class for exceptions in this module."""
    pass


def playblast(filename, modelPanel, startFrame, endFrame, width, height, step=1):
    """
    Wrapper for Maya's Playblast command.
    
    :type filename: str
    :type modelPanel: str
    :type startFrame: int
    :type endFrame: int
    :type width: int
    :type height: int
    :type step: list[int]
    :rtype: str
    """
    logger.info(u"Playblasting '{filename}'".format(filename=filename))

    if startFrame == endFrame and os.path.exists(filename):
        os.remove(filename)

    frame = [i for i in range(startFrame, endFrame + 1, step)]

    modelPanel = modelPanel or mutils.currentModelPanel()
    if maya.cmds.modelPanel(modelPanel, query=True, exists=True):
        maya.cmds.setFocus(modelPanel)
        if DEFAULT_PLAYBLAST_RENDERER:
            maya.cmds.modelEditor(
                modelPanel,
                edit=True,
                rendererName=DEFAULT_PLAYBLAST_RENDERER
            )

    name, compression = os.path.splitext(filename)
    filename = filename.replace(compression, "")
    compression = compression.replace(".", "")
    if maya.cmds.optionVar(exists="VideoSettingsSize"):
        width = maya.cmds.optionVar(q='VideoSettingsSize')
        height = width
    if maya.cmds.optionVar(exists="VideoSettingsImageFormat"):
        imageFormat = maya.cmds.optionVar(q='VideoSettingsImageFormat')
        if imageFormat == 0:
            compression = 'jpg'
        elif imageFormat == 1:
            compression = 'png'

    offScreen = mutils.isLinux()

    path = maya.cmds.playblast(
        format="image",
        viewer=False,
        percent=100,
        quality=100,
        frame=frame,
        width=width,
        height=height,
        filename=filename,
        endTime=endFrame,
        startTime=startFrame,
        offScreen=offScreen,
        forceOverwrite=True,
        showOrnaments=False,
        compression=compression,
    )

    if not path:
        raise PlayblastError("Playblast was canceled")

    src = path.replace("####", str(int(0)).rjust(4, "0"))

    if startFrame == endFrame:
        dst = src.replace(".0000.", ".")
        logger.info("Renaming '%s' => '%s" % (src, dst))
        os.rename(src, dst)
        src = dst

    logger.info(u"Playblasted '%s'" % src)
    return src

def playblastMovie(filename, modelPanel, startFrame, endFrame, width, height, step=1, video=False):
    """
    Wrapper for Maya's Playblast command.
    
    :type filename: str
    :type modelPanel: str
    :type startFrame: int
    :type endFrame: int
    :type width: int
    :type height: int
    :type step: list[int]
    :rtype: str
    """
    logger.info(u"Playblasting '{filename}'".format(filename=filename))

    if startFrame == endFrame and os.path.exists(filename):
        os.remove(filename)

    frame = [i for i in range(startFrame, endFrame + 1, step)]

    modelPanel = modelPanel or mutils.currentModelPanel()
    if maya.cmds.modelPanel(modelPanel, query=True, exists=True):
        maya.cmds.setFocus(modelPanel)
        if DEFAULT_PLAYBLAST_RENDERER:
            maya.cmds.modelEditor(
                modelPanel,
                edit=True,
                rendererName=DEFAULT_PLAYBLAST_RENDERER
            )

    name, compression = os.path.splitext(filename)
    filename = filename.replace(compression, "")
    compression = compression.replace(".", "")
    pbFormat = "qt"#maya.cmds.optionVar(q='playblastFormat')
    pbCompress = "H.264"#maya.cmds.optionVar(q='playblastCompression')
    if maya.cmds.optionVar(exists="VideoSettingsSize"):
        width = maya.cmds.optionVar(q='VideoSettingsSize')
        height = width
    offScreen = mutils.isLinux()

    path = maya.cmds.playblast(
        format=pbFormat,
        viewer=False,
        percent=100,
        quality=100,
        frame=frame,
        width=width,
        height=height,
        filename=filename,
        endTime=endFrame,
        startTime=startFrame,
        offScreen=offScreen,
        forceOverwrite=True,
        showOrnaments=False,
        compression=pbCompress,
        editorPanelName=modelPanel
    )

    if not path:
        raise PlayblastError("Playblast was canceled")
    
    if maya.cmds.optionVar(exists="VideoSettingsConvertMp4") and maya.cmds.optionVar(q='VideoSettingsConvertMp4') == 1:
        inputFile = filename + '.mov'
        outputFile = filename + '.mp4'
        print("ffmpeg input: " + inputFile)
        print("ffmpeg output: " + outputFile)
        ffmpegPath = LibraryWindow.instance().ffmpegPath()
        exePath = os.path.dirname(os.path.abspath(__file__))
        if len(ffmpegPath) > 0:
            exePath = ffmpegPath
        exePath = os.path.join(exePath, "ffmpeg")
        if sys.platform == "win32" or sys.platform == "win64" or sys.platform == "cygwin":
            exePath += ".exe"
        if os.path.isfile(exePath):
            args = [exePath, '-i', inputFile, '-vcodec', 'h264', outputFile]
            print(args)
            subprocess.call(args)
            os.remove(inputFile)
        else:
            raise PlayblastError("There is no ffmpeg executable! You need to set up correct path to ffmpeg in settings.")

    frame = [startFrame]
    path = maya.cmds.playblast(
        format="image",
        viewer=False,
        percent=100,
        quality=100,
        frame=frame,
        width=width,
        height=height,
        filename=filename,
        endTime=startFrame,
        startTime=startFrame,
        offScreen=offScreen,
        forceOverwrite=True,
        showOrnaments=False,
        compression=compression,
    )
    
    if not path:
        raise PlayblastError("Playblast was canceled")

    src = path
    src = path.replace("####", str(int(0)).rjust(4, "0"))
    
    #if startFrame == endFrame:
    dst = src.replace(".0000.", ".")
    logger.info("Renaming '%s' => '%s" % (src, dst))
    os.rename(src, dst)
    src = dst
    
    logger.info(u"Playblasted '%s'" % src)
    return src