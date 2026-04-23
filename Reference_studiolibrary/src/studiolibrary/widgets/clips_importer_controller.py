from PySide2 import QtCore, QtGui, QtWidgets, QtMultimedia, QtMultimediaWidgets
from studiolibrary.widgets.clips_importer import Ui_Dialog
from studiolibrarymaya.basesavewidget import BaseSaveWidget
from studiolibrarymaya.animitem import AnimItem
from studiolibrary.widgets.videothumbnailwidget import VideoThumbnailWidget
from studiolibrary.librarywindow import LibraryWindow
from maya import OpenMayaUI as omui
import maya.utils as utils
from shiboken2 import wrapInstance
import os
from studiolibrary.widgets.messagebox import MessageBox
import maya .cmds as cmds
from pymel.core import *
import maya.mel as mel

AnimClipsFileExtensions = ['.ma', '.mb']

def maya_main_window():
    '''
    Return the Maya main window widget as a Python object
    '''
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class ClipsImporterControler(QtWidgets.QDialog):
    def __init__(self, studioLibraryWindow, parent=maya_main_window()):
        super(ClipsImporterControler, self).__init__(parent)
        self._model = None
        self._studioLibraryWindow = studioLibraryWindow
        self._currentAnimPath = None
    
    def setModel(self, model):
        self._model = model
        if self._model:
            self._model.refreshUi(self._studioLibraryWindow.selectedFolderPath())

    def onStopImportButton(self):
        print("stop")

    def onCameraIndexChange(self, index):
        self._model.onCameraIndexChange(index)

    def onAddClipsFolderButton(self):
        widget = self._model.onAddClipsFolderButton()
    
    def onRemoveClipsFolderButton(self):
        widget = self._model.onRemoveClipsFolderButton()
    
    def onSetOuputFolder(self):
        path = self._studioLibraryWindow.path()

        if not path:
            path = os.path.expanduser("~")

        path = QtWidgets.QFileDialog.getExistingDirectory(
            None,
            "Browse Folder",
            path
        )
        if path and self._model:
            self._model.onSetOutputFolder(path)

    def onStartButton(self):
        if not self._model.onStartImport():
            title = "Can not start import"
            text = "Make focus on main window's panel, please"
            MessageBox.critical(None, title, text)
            return
        self.startImport()
        
    def startImport(self):
        inViewMessage(amg='Start import clips', pos='midCenter', fade=True)
        self._model.setProgressValue(5)
        clipsPaths = self._model.getClipsPaths()
        #clipsPaths = ['C:/Users/omelyanchuk-m/Desktop/maya/TEST _scripts_file/Emma/Clips', 'C:/Users/omelyanchuk-m/Desktop/maya/TEST _scripts_file/Marco/Clips', 'C:/Users/omelyanchuk-m/Desktop/maya/TEST _scripts_file/Pizza']
        print("Clips paths: " + str(clipsPaths))
        if len(clipsPaths) == 0 or len([x for x in clipsPaths if clipsPaths.count(x) > 1 or len(x) == 0]) > 0:
            print("Invalid clips paths")
            return

        selectedCharsets = self._model.getSelectedCharsets()
        #selectedCharsets = ['Emma_CHT', 'Marco_CHT', 'Pizza_CHT']
        if len(selectedCharsets) == 0 or len([x for x in selectedCharsets if selectedCharsets.count(x) > 1 or len(x) == 0]) > 0:
            print("Invalid clips charsets")
            return
        if len(selectedCharsets) != len(clipsPaths):
            print("clips paths and chrasets different count")
            return
        
        camera = self._model.getSelectedCamera()
        #camera = 'Group1|GUI_Facial_Cam'
        if len(camera) == 0:
            print("Invalid camera")
            return
        
        outputPath = self._model.getOutputPath()
        #outputPath = 'C:/Users/omelyanchuk-m/Desktop/maya/studio_library'
        if len(outputPath) == 0:
            print("Invalid output folder path")
            return

        folderPaths = []
        index = -1
        #ref files to not include them in the anim files list
        self._model.setProgressValue(10)
        charsetRefMap = self._model.getCharsetsFiles()
        self._model.setProgressValue(15)
        print("charsetRefMap: " + str(charsetRefMap))
        refFiles = []
        for refName in charsetRefMap.values():
            refFiles.append(self._model.getReferenceFile(refName))
        #refFiles = ['Emma_Rig.ma', 'Marco_Rig.ma', 'Pizza_Rig.ma']
        
        #collect .ma and .mb anim clips files for each folder/charset pair
        for clipsPath in clipsPaths:
            index += 1
            charSetName = selectedCharsets[index]
            if not os.path.isdir(clipsPath):
                print("Clips path is not folder: " + clipsPath)
                return
            clipsNamesList = self.collectFileNames(clipsPath, refFiles)
            if len(clipsNamesList) == 0:
                print("Clips folder " + clipsPath + " is empty")
                return
            folderPaths.append(tuple((charSetName, clipsNamesList)))
        
        #find common clip files for charsets
        intersections = []
        for index in range(0, len(folderPaths)):
            charSetName, clipsNamesList = folderPaths[index]
            intersections.append(tuple(([charSetName], clipsNamesList)))
            self.findCommonClipsFromIndex(folderPaths, index+1, clipsNamesList, [charSetName], intersections)
        for charsets, clipsIntersections in intersections:
            for checkCharsets, checkClipsIntersections in intersections:
                if len(checkCharsets) > len(charsets) and len(charsets) == len(self.findCommonClips(charsets, checkCharsets)):
                    uniqClips = [x for x in clipsIntersections if x not in checkClipsIntersections]
                    del clipsIntersections[:]
                    clipsIntersections.extend(uniqClips)
        intersections = [s for s in intersections if len(s[1]) > 0]
        if len(selectedCharsets) > 1:
            intersections = [s for s in intersections if len(s[0]) > 1]
        print("Charset/clip names list: " + str(intersections))

        animsCount = 0
        for charsets, clipNames in intersections:
            animsCount += len(clipNames)

        progress = 20
        step = max(1, (100 - progress) / animsCount)
        #apply clips to scene step by step
        showCaptureWindow = True
        for charsets, clipNames in intersections:
            for clipName in clipNames:
                progress += step
                self._model.setProgressValue(progress)
                cmds.delete(all=1, channels=1)
                Allclips = cmds.clip(q=1, allClips=1)
                cmds.delete(Allclips)
                selectedFolder = outputPath#self._studioLibraryWindow.selectedFolderPath()
                savePath = os.path.join(selectedFolder, clipName+AnimItem.EXTENSION).replace("\\","/")
                queries = [{"filters": [("path", "is", savePath)]}]
                existingItems = self._studioLibraryWindow.library().findItems(queries)
                if len(existingItems) > 0:
                    continue
                charsetClipPathPairs = []
                for charset in charsets:
                    charsetClipPathPairs.append(tuple((charset, self.findClipPath(charset, clipName, selectedCharsets, clipsPaths))))
                #self._model.selectCharsets(True, charsetClipPathPairs)
                startFrame, endFrame = self._model.applyClipToScene(clipName, charsetClipPathPairs, charsetRefMap)
                try:
                    BaseSaveWidget.makeThumbnail(showCaptureWindow, startFrame, endFrame, 1, True, self._capturedCallback, self, self._studioLibraryWindow, doExec=True)
                    showCaptureWindow = False
                except Exception as e:
                    self.onImportFinished()
                    raise e
                if not self._currentAnimPath:
                    print("No thumbnail for anim:" + str(clipName))
                    continue
                item = AnimItem()
                thumbnailPath = VideoThumbnailWidget.getThumbnailInDir(self._currentAnimPath)
                self._model.selectCharsets(False, charsetClipPathPairs)
                objects = self._model.getCurrentSelection()
                BaseSaveWidget.saveNewItem(savePath, thumbnailPath, item, self._currentAnimPath, self._studioLibraryWindow, objects=objects,
                     frameRange=tuple((int(startFrame), int(endFrame))), fileType='mayaAscii', bakeConnected=False, byFrame=1)
                self._currentAnimPath = None
                self._model.resetCurrentScene(False)
        self.onImportFinished()
    
    def stopPlay(self):
        self._model.waitIdleTasks()

    def onImportFinished(self):
        self._model.setProgressValue(100)
        self._studioLibraryWindow.sync()
        self._model.resetCurrentScene(True)
        informBox('FINISH', 'Import Completed !!!', 'OK')
        self._model.setProgressValue(0)

    def _capturedCallback(self, src):
        path = os.path.dirname(src)
        self._currentAnimPath = path

    def findClipPath(self, charset, clipName, selectedCharsets, clipsPaths):
        index = selectedCharsets.index(charset)
        path = clipsPaths[index]
        return self.findFileInFolder(clipName, path)
    
    def findFileInFolder(self, clipName, path):
        if not os.path.isdir(path):
            return None
        for file in os.listdir(path):
            currentFilePath = os.path.join(path, file).replace("\\","/")
            if os.path.isdir(currentFilePath):
                fileInFolder = self.findFileInFolder(clipName, currentFilePath)
                if fileInFolder:
                    return fileInFolder
            else:
                fileName, extension = os.path.splitext(file)
                if fileName == clipName and extension in AnimClipsFileExtensions:
                    return currentFilePath
        return None
                
    def findCommonClipsFromIndex(self, folderPaths, startIndex, clipsNamesList, charsets, intersections):
        for subIndex in range(startIndex, len(folderPaths)):
            currentCharsets = list(charsets)
            subCharSetName, subClipsNamesList = folderPaths[subIndex]
            commonClips = self.findCommonClips(clipsNamesList, subClipsNamesList)
            currentCharsets.append(subCharSetName)
            intersections.append(tuple((currentCharsets, commonClips)))
            self.findCommonClipsFromIndex(folderPaths, subIndex+1, commonClips, currentCharsets, intersections)

    
    def collectFileNames(self, clipsPath, refFiles):
        clipsNamesList = []
        for file in os.listdir(clipsPath):
            if os.path.isdir(os.path.join(clipsPath, file)):
                clipsNamesList.extend(self.collectFileNames(os.path.join(clipsPath, file), refFiles))
            if file in refFiles:
                continue
            fileName, extension = os.path.splitext(file)
            if not extension in AnimClipsFileExtensions:
                continue
            clipsNamesList.append(fileName)
        return clipsNamesList

    def findCommonClips(self, list1, list2):
        result = []
        for element in list1:
            if element in list2:
                result.append(element)
        return result
                
    def getClipsCharName(self, fileList, charSetName):
        charSetName = charSetName.lower()
        
        for endIndex in range(len(charSetName-1), 1):
            currentLookUp = charSetName[0, endIndex]
            success = True
            for fileName in fileList:
                if fileName.lower().index(currentLookUp) != 0:
                    success = False
                    break
            if success:
                return fileName[0, len(currentLookUp)-1]
        return ''
    
    def getClipsNamesWithoutCharName(self, fileList, charSetName):
        delimiter = '_'
        newNames = []
        for fileName in fileList:
            newFileName = fileName[len(charSetName)-1:-1]
            newFileName.trim(delimiter)
            newNames.append(newFileName)
        return newNames
