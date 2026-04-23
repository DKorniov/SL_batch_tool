import os
import imp
import mutils
from studiovendor.Qt import QtGui, QtCore, QtWidgets
import maya.cmds as cmds
import maya.mel as mel
import maya.utils as utils

class AssistAnimParams():
    def __init__(self, name, begin, end):
        self._name = name
        self._begin = begin
        self._end = end
    
    def setName(self, name):
        self._name = name
    def setBegin(self, begin):
        self._begin = begin
    def setEnd(self, end):
        self._end = end

    def name(self):
        return self._name
    def begin(self):
        return self._begin
    def end(self):
        return self._end

class AnimAssistHelper():    

    @staticmethod
    def createAnimAssitAttr():
        if cmds.objExists("AnimAssistant"):
            return
        cmds.createNode("geometryVarGroup", name="AnimAssistant", skipSelect=True)
        selection = cmds.ls(selection=True) or []
        cmds.select(clear=True)
        cmds.select('AnimAssistant')
        cmds.addAttr(dataType="string", longName="AnimationClipName")
        cmds.addAttr(dataType="string", longName="StartFrame")
        cmds.addAttr(dataType="string", longName="EndFrame")
        cmds.addAttr(dataType="string", longName="PlayblastPt")
        cmds.addAttr(dataType="string", longName="PlayblastPost")
        cmds.addAttr(dataType="string", longName="PlayblastPre")
        cmds.select(clear=True)
        cmds.select(selection)

    @staticmethod
    def getAnimAssistAnims():
        AnimAssistHelper.createAnimAssitAttr()

        animListStr = cmds.getAttr("AnimAssistant.AnimationClipName")
        if not animListStr:
            return []
        print(animListStr)
        animList = animListStr.split(" ")
        anims = []
        for animStr in animList:
            if not ("|" in animStr):
                continue
            withoutNum = animStr.split("|")[1]
            nameAndBegin, end = withoutNum.split("-")
            begin = nameAndBegin.split("_")[-1]
            name = nameAndBegin[0:len(nameAndBegin)-len(begin)-1]
            anims.append(AssistAnimParams(name, int(begin), int(end)))
            #print(anims[-1])

        return anims
    
    @staticmethod
    def setAnimAssistAnims(anims):
        AnimAssistHelper.createAnimAssitAttr()
        animsStr = ''
        startStr = ''
        endStr = ''
        num = 0
        for anim in anims:
            if len(animsStr) != 0:
                animsStr += ' '
                startStr += ' '
                endStr += ' '
            animsStr += ("%03d" % (num,)) + "|" + anim.name() + "_" + str(anim.begin()) + "-" + str(anim.end())
            startStr += str(anim.begin())
            endStr += str(anim.end())
            num += 1
        cmds.setAttr("AnimAssistant.AnimationClipName", animsStr, type="string")
        cmds.setAttr("AnimAssistant.StartFrame", startStr, type="string")
        cmds.setAttr("AnimAssistant.EndFrame", endStr, type="string")
        if mel.eval('exists ' + "RefreshAnimList"):
            mel.eval('RefreshAnimList;')
    
    @staticmethod
    def addOrReplaceAnimAssistAnim(newAnim):
        anims = AnimAssistHelper.getAnimAssistAnims()
        found = False
        for anim in anims:
            if anim.name() == newAnim.name():
                found = True
                anim.setBegin(newAnim.begin())
                anim.setEnd(newAnim.end())
        if not found:
            anims.append(newAnim)
        AnimAssistHelper.setAnimAssistAnims(anims)