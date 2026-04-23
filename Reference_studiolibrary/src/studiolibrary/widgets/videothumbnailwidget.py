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

from studiovendor.Qt import QtGui
from studiovendor.Qt import QtCore
from studiovendor.Qt import QtWidgets
from studiovendor.Qt import QtMultimedia
from studiovendor.Qt import QtMultimediaWidgets

from studioqt import ImageSequence
import studioqt
import os
from threading import Timer

__all__ = ['VideoThumbnailWidget']
supported_video_types = ['mov', 'avi', 'mp4']

first_time_play = True

class VideoThumbnailWidget(QtWidgets.QWidget):

    def __init__(self, parent=None, groupWidget=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.setObjectName("studioLibraryVideoThumbnailWidget")
        self.setWindowTitle("Save Item")

        self._path = None
        self.playlist = None
        self.gview = None
        self._size = None
        self._groupWidget = groupWidget
        self._shouldPlay = False
        self.mediaPlayer = None

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().setMargin(0)

        if self._groupWidget:
            self._groupWidget.toggled.connect(self.onGroupWidgetToggled)
    
    def createPlayer(self, fileName):
        print("createPlayer")
        self.scene = QtWidgets.QGraphicsScene()
        self.gview = QtWidgets.QGraphicsView(self.scene)#, parent = self)
        self.gview.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gview.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.gview.setViewportMargins(0, 0, 0, 0)
        self.videoWidget = QtMultimediaWidgets.QGraphicsVideoItem()
        self.scene.addItem(self.videoWidget)

        self.mediaPlayer = QtMultimedia.QMediaPlayer(self, QtMultimedia.QMediaPlayer.VideoSurface)
        self.mediaPlayer.setVideoOutput(self.videoWidget)

        self.playlist = QtMultimedia.QMediaPlaylist()
        if fileName:
            self.playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(fileName)))
            self.playlist.setCurrentIndex(0)
        self.playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.CurrentItemInLoop)
        self.mediaPlayer.setPlaylist(self.playlist)
        self.layout().addWidget(self.gview)
        self.mediaPlayer.videoAvailableChanged.connect(self.videoAvailableChanged)

        if self._size:
            self.setSize(self._size.width(), self._size.height())
    
    def videoAvailableChanged (self, videoAvailable):
        print("videoAvailableChanged: " + str(videoAvailable))
        if not videoAvailable and self._shouldPlay and not self._groupWidget.isChecked():
            return
        self._shouldPlay = videoAvailable
        if self._groupWidget and not self._groupWidget.isChecked():
            print("videoAvailableChanged: toggle hided")
            return
        if videoAvailable:
            self.mediaPlayer.play()

    def onGroupWidgetToggled(self, vis):
        print("onGroupWidgetToggled: " + str(vis) + ", should play:" + str(self._shouldPlay))
        if not self._shouldPlay:
            return
        if vis:
            if not self.playlist:
                self.createPlayer(self._path)
            else:
                self.mediaPlayer.play()
        elif not vis:
            #self.mediaPlayer.stop()
            self.destroyPlayer()

    def openVideoFile(self):
        if self.isPlaying():
            os.startfile(self.currentFilename())

    def isPlaying(self):
        return self._path != None

    def setSize(self, w, h):
        """
        Reimplemented so that the icon size is set at the same time.

        :type w: int
        :type h: int
        :rtype: None
        """
        #print("setSize: " + str(w) + "," + str(h))
        self._size = QtCore.QSize(w, h)
        self.resize(w, h)
        if self.gview:
            self.videoWidget.setSize(self._size)
            #self.gview.fitInView(0, 0, self._size.width(), self._size.height())
            self.scene.setSceneRect(0, 0, self._size.width(), self._size.height())
            #self.gview.setFixedSize(self._size.width(), self._size.height())
            self.gview.setGeometry(0, 0, self._size.width(), self._size.height())

    def stopPlay(self):
        print("stopPlay")
        if self.isPlaying() and self.mediaPlayer:
            self.destroyPlayer()
            self._path = None
    
    def destroyPlayer(self):
        if self.isPlaying() and self.mediaPlayer:
            self.layout().removeWidget(self.gview)
            self.mediaPlayer.stop()
            self.mediaPlayer.setPlaylist(None)
            self.playlist.clear()
            del self.playlist
            self.playlist = None
            self.mediaPlayer.setVideoOutput(None)
            self.scene.removeItem(self.videoWidget)
            del self.videoWidget
            self.videoWidget = None
            del self.scene
            self.scene = None
            del self.gview
            self.gview = None
            del self.mediaPlayer
            self.mediaPlayer = None

    def playFile(self, filePath):
        fileName, extension = os.path.splitext(os.path.basename(filePath))
        extension = extension.lower()[1:]
        if extension in supported_video_types:
            print("playFile: " + str(filePath))
            if not self.playlist:
                if not self._groupWidget or self._groupWidget.isChecked():
                    self.createPlayer(filePath)
                else:
                    self._shouldPlay = True
            else:
                self.playlist.clear()
                self.playlist.addMedia(QtMultimedia.QMediaContent(QtCore.QUrl.fromLocalFile(filePath)))
                self.playlist.setCurrentIndex(0)
            #self.mediaPlayer.play()

            self._path = filePath
            return True
        return False

    @staticmethod
    def isVideoThumbnail(path):
        if not os.path.isdir(path):
            return False
        for file in os.listdir(path):
            fileName, extension = os.path.splitext(os.path.basename(os.path.join(path, file)))
            extension = extension.lower()[1:]
            if extension in supported_video_types:
                return True
        return False

    def playFileFromDir(self, path):
        for file in os.listdir(path):
            if self.playFile(os.path.join(path, file)):
                return

    def setPath(self, path):
        """
        Set a single frame image sequence.
        
        :type path: str
        """
        print("setPath:" + path)
        if os.path.isdir(path):
            self.playFileFromDir(path)
        else:
            self.playFile(path)
        self.setVisible(self.isPlaying())
        if self.currentFilename():
            print("video path: " + self.currentFilename() + ", visible: " + str(self.isPlaying()))

    def currentFilename(self):
        return self._path
    
    def dirname(self):
        if self._path != None:
            if os.path.isdir(self._path):
                return self._path
            else:
                return os.path.dirname(self._path)
        return None
    
    def firstFrame(self):
        if self._path != None:
            if os.path.isdir(self._path):
                return VideoThumbnailWidget.getThumbnailInDir(self._path)
            else:
                return VideoThumbnailWidget.getThumbnailInDir(os.path.dirname(self._path))
        return None
    
    @staticmethod
    def getThumbnailInDir(path):
        for file in os.listdir(path):
            fileName, extension = os.path.splitext(os.path.basename(file))
            if (fileName == "thumbnail") and (extension == ".jpg" or extension ==  ".png"):
                filePath = os.path.join(path, file)
                return filePath
        return None