# -*- coding: utf-8 -*-
from __future__ import absolute_import
from maya import cmds

def current_time():
    try:
        return int(cmds.currentTime(q=True) or 1)
    except Exception:
        return 1

def set_time(frame):
    try:
        cmds.currentTime(int(frame), e=True)
    except Exception:
        pass

def list_selection():
    return cmds.ls(sl=True) or []

def get_any_model_panel():
    try:
        visible = [p for p in cmds.getPanel(vis=True) if cmds.getPanel(to=p) == "modelPanel"]
        if visible:
            return visible[0]
    except Exception:
        pass
    try:
        mp = cmds.getPanel(type="modelPanel")
        if mp:
            return mp[0]
    except Exception:
        pass
    return None

def ensure_camera(name, tx, ty, tz, rx, ry, rz, focal):
    if not cmds.objExists(name):
        tr, sh = cmds.camera()
        try: cmds.rename(tr, name)
        except Exception: pass
    try:
        cmds.setAttr("%s.translate" % name, tx, ty, tz, type="double3")
        cmds.setAttr("%s.rotate" % name, rx, ry, rz, type="double3")
    except Exception:
        pass
    try:
        shape = (cmds.listRelatives(name, s=True, f=False) or [None])[0]
        if shape:
            cmds.setAttr("%s.focalLength" % shape, focal)
    except Exception:
        pass
