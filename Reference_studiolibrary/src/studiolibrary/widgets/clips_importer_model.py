import os
import imp
import mutils
from studiovendor.Qt import QtGui, QtCore, QtWidgets
from studiolibrary.widgets.fieldwidgets import PathFieldWidget, EnumFieldWidget
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

class ClipsImporterModel():
    def __init__(self, view):
        self._view = view
        self._clipPathWidgets = []
        self._charsetComboWidgets = []
        self._camera = None
        self._displayLights = None
    
    def refreshUi(self, outputFolder):
        self.setCameras()
        self._view.outputFolderLineEdit.setText(outputFolder)
        self._modelPanel = mutils.cmds.currentModelPanel()
        self.updateRemoveButton()
    
    def onStartImport(self):
        if self._modelPanel:
            return True
        return False

    def setProgressValue(self, value):
        self._view.importProgressBar.setValue(value)

    def displayTextures(self):
        cmds.setFocus(self._modelPanel)
        modelPanel = mutils.cmds.currentModelPanel()
        if modelPanel:
            editor = cmds.modelPanel(modelPanel, query=True, modelEditor=True)
            self._displayLights = cmds.modelEditor(editor, query=True, displayLights=True)
    
    def restoreDisplayLightsMode(self):
        modelPanel = mutils.cmds.currentModelPanel()
        if modelPanel and self._displayLights:
            editor = cmds.modelPanel(modelPanel, query=True, modelEditor=True)
            cmds.modelEditor(editor, edit=True, displayLights=self._displayLights, displayTextures=True, displayAppearance='smoothShaded')
        self._displayLights = None

    def setCameras(self):
        cameras = self.getCameras()
        shortNameCameras = cmds.listRelatives(cameras, parent=1)
        panel = cmds.getPanel(withFocus=True)
        selectedCamera = cmds.lookThru(panel, q=True)
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
            self._view.cameraComboBox.addItem(name)
        self._view.cameraComboBox.setCurrentIndex(shortNameCameras.index(selectedCamera))
    
    def onSetOutputFolder(self, path):
        self._view.outputFolderLineEdit.setText(path)
    
    def onAddClipsFolderButton(self):
        data = {"name": "path", "type": "path", "value": ""}
        pathWidget = PathFieldWidget()
        pathWidget.setData(data=data)
        pathWidget.setMaximumHeight(20)
        self.addWidgetsToLayout(self._view.clipsLayout, [pathWidget])
        self._clipPathWidgets.append(pathWidget)

        charsetsComboWidget = EnumFieldWidget()
        charsetsComboWidget.setMaximumHeight(20)
        charsetsComboWidget.setItems(self.getCharsets())
        self._charsetComboWidgets.append(charsetsComboWidget)
        self.addWidgetsToLayout(self._view.charSetsLayout, [charsetsComboWidget])

        return pathWidget
    
    def onRemoveClipsFolderButton(self):
        self.removeLastAddedWidgetFromLayout([self._view.clipsLayout, self._view.charSetsLayout])
    
    def onCameraIndexChange(self, index):
        if not index:
            index = self._view.cameraComboBox.currentIndex()
        cameras = self.getCameras()
        self.setCamera(cameras[index])
    
    def setCamera(self, name):
        panel = cmds.getPanel( withFocus=True )
        cmds.lookThru(panel, name)
        self._camera = name

    def addWidgetsToLayout(self, layout, widgets):
        prevWidgets = []
        widgetsOnTop = 2
        while layout.count() > widgetsOnTop:
            prevWidgets.append(layout.takeAt(widgetsOnTop))
        for widget in widgets:
            layout.addWidget(widget)
        for widget in prevWidgets:
            layout.addItem(widget)
        self.updateRemoveButton()
    
    def removeLastAddedWidgetFromLayout(self, layouts):
        widgetsOnTop = 2
        for layout in layouts:
            layout.takeAt(widgetsOnTop)
        self._charsetComboWidgets[-1].setParent(None)
        del self._charsetComboWidgets[-1]
        self._clipPathWidgets[-1].setParent(None)
        del self._clipPathWidgets[-1]
        self.updateRemoveButton()
    
    def updateRemoveButton(self):
        self._view.removeClipsButton.setEnabled(len(self._charsetComboWidgets) > 0)
    
    def getClipsPaths(self):
        paths = []
        for widget in self._clipPathWidgets:
            paths.append(widget.value())
        return paths
    
    def getSelectedCharsets(self):
        charsets = []
        for widget in self._charsetComboWidgets:
            charsets.append(widget.value())
        return charsets

    def getSelectedCamera(self):
        return self._view.cameraComboBox.currentText()
    
    def getOutputPath(self):
        return self._view.outputFolderLineEdit.text()

    def getCharsets(self):
        chars = cmds.ls(type='character')
        if not chars:
            return []
        return chars
    
    def getCameras(self):
        cameras = cmds.ls(cameras=True)
        if not cameras:
            return []
        return cameras
    
    def getSceneReferences(self):
        allReferences = cmds.ls( references=True )
        references = []
        for ref in allReferences:
            if not cmds.file(referenceNode=ref, query=True, deferReference=True):
                references.append(ref)
        return references

    def getReferenceFile(self, ref):
        refFile = cmds.referenceQuery(ref, filename=True)
        refName = os.path.basename(refFile)
        return refName
    
    def getCharsetsFiles(self):
        charsetMap = {}
        charsets = self.getCharsets()
        references = self.getSceneReferences()
        for ref in references:
            cmds.file(unloadReference=ref)

            newCharsets = self.getCharsets()
            refCharsets = [s for s in charsets if not s in newCharsets]
            for refCharset in refCharsets:
                charsetMap[refCharset] = ref

            refFile = cmds.referenceQuery(ref, filename=True)
            cmds.file(refFile, loadReference=ref)
        print(charsetMap)
        return charsetMap

    def loadRefsForCharsets(self, charsetClipPathPairs, charsetFilesMap):
        loadedRefs = self.getSceneReferences()
        neededRefs = []
        #load needed refs
        for charset, clipPath in charsetClipPathPairs:
            refName = charsetFilesMap[charset]
            if not refName in loadedRefs:
                refFile = cmds.referenceQuery(refName, filename=True)
                cmds.file(refFile, loadReference=refName)
            neededRefs.append(refName)
        #unload not needed refs
        for ref in loadedRefs:
            if not ref in neededRefs:
                cmds.file(unloadReference=ref)
    
    def applyClipToScene(self, clipName, charsetClipPathPairs, charsetFilesMap):
        print("Applying clipName:" + clipName)
        print("Charsets and files: " + str(charsetClipPathPairs))
        self.loadRefsForCharsets(charsetClipPathPairs, charsetFilesMap)
        print("Loaded refs: " + str(self.getSceneReferences()))
        self.displayTextures()

        homeName = cmds.cameraView(camera=self._camera)
        cmds.cameraView(homeName, e=True, camera=self._camera, ab=True)

        sTime = 10000
        eTime = 0
        charsets = []
        for charset, clipPath in charsetClipPathPairs:
            charsets.append(charset)
            oldClips = cmds.ls(type='animClip')
            print("Charset: " + charset + ", clip path: " + clipPath)
            self.importClip(charset, clipPath)
            allClips = cmds.ls(type='animClip')
            allClips = [s for s in allClips if not s in oldClips]
            for item in allClips:
                if clipName in item and "Source" in item:
                    sourceNode = item
                    break

            sTime = min(sTime, cmds.getAttr(sourceNode + '.sourceStart'))
            eTime = max(eTime, cmds.getAttr(sourceNode + '.sourceEnd'))
            cmds.clip(charset, e=True, active=sourceNode )
        cmds.playbackOptions(minTime=sTime, maxTime=eTime)
        self.setCamera(self._camera)
        cmds.cameraView( homeName, e=True, camera=self._camera, sc=True )
        cmds.cameraView(homeName, e=True, camera=self._camera, rb=True)
        self.restoreDisplayLightsMode()
        return tuple((sTime, eTime))
    
    def waitIdleTasks(self):
        tasks = cmds.evalDeferred(list=True)
        cmds.timer( s=True )
        while len(tasks) > 0:
            utils.processIdleEvents()
            tasks = cmds.evalDeferred(list=True)

            if cmds.timer(lap=True) > 15:
                print("Wait break by timer")
                break
        cmds.timer( e=True )

    def selectCharsets(self, clearSelection, charsetClipPathPairs):
        print("selectCharsets start")
        if clearSelection:
            cmds.select(clear=True)
        charsets = []
        for charset, clipPath in charsetClipPathPairs:
            charsets.append(charset)
        cmds.select(charsets)
        for charset in charsets:
            mel.eval('selectNodesInCharacter("' + charset + '");')
        #cmds.refresh(force=True)
        self.waitIdleTasks()
        print("selectCharsets finish")
    
    def getCurrentSelection(self):
        return cmds.ls(selection=True) or []
    
    def getFileName(self):
        return cmds.file(q=True, l=True)[0]
        
    def resetCurrentScene(self, fullReset):
        if fullReset:
            cmds.file( self.getFileName(), open=True, force=True, ignoreVersion=True, options="v=0;")
        else:
            mel.eval('delete (`ls -type "animCurveTL" -type "animCurveTA" -type "animCurveTU"`)');

    def importClip(self, charset, filename):
        self.setCurrentCharset(charset)
        ext = os.path.splitext(filename)[1].lower()[1:]
        scriptsPath = mel.eval('getenv MAYA_LOCATION')+'/scripts/others'
        mel.eval('source "' + scriptsPath + '/doImportClipArgList.mel"')
        mel.eval('global int $gImportClipToCharacter = 1;')
        mel.eval('global int $gScheduleClipOnCharacter = 1;')
        mel.eval('global string $gImportToCharacter = "' + charset + '";')
        return mel.eval('clipEditorImportClip("' + filename + '", "' + ext + '")')
    def setCurrentCharset(self, charset):
        mel.eval('setCurrentCharacters({"' + charset + '"})')