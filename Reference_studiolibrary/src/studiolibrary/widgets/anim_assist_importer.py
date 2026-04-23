import os
import imp
import mutils
from studiovendor.Qt import QtGui, QtCore, QtWidgets
from studiolibrary.widgets.fieldwidgets import PathFieldWidget, EnumFieldWidget
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils
from studiolibrarymaya.basesavewidget import BaseSaveWidget
from studiolibrarymaya.animitem import AnimItem
from studiolibrary.widgets.videothumbnailwidget import VideoThumbnailWidget
from studiolibrary.widgets.anim_assist_helper import AnimAssistHelper
import studiolibrary

class AnimAssistImporter():
    def __init__(self, studioLibraryWindow):
        self._studioLibraryWindow = studioLibraryWindow
        self._list = []
        self._currentAnimPath = None
        self._modelPanel = None
        self.importAnimList()
        self.selectAllCS()
        self.importAnims()

    def importAnimList(self):
        if not cmds.objExists("AnimAssistant"):
            return False
        self._list = AnimAssistHelper.getAnimAssistAnims()
        return True
    
    def selectAllCS(self):
        charsets = cmds.ls(type='character')
        for charset in charsets:
            mel.eval('selectNodesInCharacter("' + charset + '");')

    def importAnims(self):
        showCaptureWindow = True
        mbTitle = "Overwrite item"
        studiolibrary.widgets.MessageBox.resetEnableDontShowCheckBox(mbTitle)
        modelPanel = mutils.cmds.currentModelPanel()
        if not modelPanel:
            return
        for animParams in self._list:
            selectedFolder = self._studioLibraryWindow.selectedFolderPath()
            savePath = os.path.join(selectedFolder, animParams.name()+AnimItem.EXTENSION).replace("\\","/")
            queries = [{"filters": [("path", "is", savePath)]}]
            existingItems = self._studioLibraryWindow.library().findItems(queries)
            try:
                BaseSaveWidget.makeThumbnail(showCaptureWindow, animParams.begin(), animParams.end(), 1, True, self._capturedCallback, None, self._studioLibraryWindow, doExec=True, modelPanel=modelPanel)
                showCaptureWindow = False
            except Exception as e:
                self.onImportFinished()
                raise e
            if not self._currentAnimPath:
                self.onImportFinished()
                print("No thumbnail for anim:" + str(animParams.name()))
                return
            
            if len(existingItems) > 0:
                name, button = studiolibrary.widgets.MessageBox.input(
                    self._studioLibraryWindow,
                    mbTitle,
                    "Overwrite item or change name?",
                    inputText=animParams.name(),
                    enableDontShowCheckBox=True
                )
                if button != QtWidgets.QDialogButtonBox.Ok:
                    continue
                if name != animParams.name():
                    animParams.setName(name)
                    savePath = os.path.join(selectedFolder, animParams.name()+AnimItem.EXTENSION).replace("\\","/")
                else:
                    for existItem in existingItems:
                        existItem.delete()

            self.selectAllCS()
            item = AnimItem()
            thumbnailPath = VideoThumbnailWidget.getThumbnailInDir(self._currentAnimPath)
            objects = self.getCurrentSelection()
            BaseSaveWidget.saveNewItem(savePath, thumbnailPath, item, self._currentAnimPath, self._studioLibraryWindow, objects=objects,
                    frameRange=tuple((animParams.begin(), animParams.end())), fileType='mayaAscii', bakeConnected=False, byFrame=1)
            self._currentAnimPath = None
        self.onImportFinished()
    
    def _capturedCallback(self, src):
        path = os.path.dirname(src)
        self._currentAnimPath = path
    
    def onImportFinished(self):
        print("Import is done")
        self._studioLibraryWindow.sync()
    
    def getCurrentSelection(self):
        return cmds.ls(selection=True) or []