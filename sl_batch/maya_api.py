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

def resolve_controls(raw_names):
    """
    Разрешает сырые имена контролов из set.json (с учетом неймспейсов).
    Возвращает список актуальных путей к объектам в сцене, отфильтровывая удаленные.
    """
    if not raw_names:
        return []
        
    # Определяем целевой неймспейс по текущему выделению в сцене (если есть)
    sel = cmds.ls(sl=True) or []
    target_ns = ""
    if sel and ':' in sel[0]:
        target_ns = sel[0].rsplit(':', 1)[0] + ":"
        
    valid_objs = []
    for name in raw_names:
        # Очищаем "сырое" имя от старых неймспейсов и путей DAG
        base_name = name.rsplit(':', 1)[-1].split('|')[-1]
        
        # Шаг 1. Прямое совпадение (например, объект не в референсе)
        if cmds.objExists(name):
            valid_objs.append(name)
            continue
            
        # Шаг 2. Подставляем неймспейс от выделенного объекта
        if target_ns:
            guess = target_ns + base_name
            if cmds.objExists(guess):
                valid_objs.append(guess)
                continue
                
        # Шаг 3. Глобальный поиск в сцене по базовому имени
        found = cmds.ls("*:" + base_name, r=True) or cmds.ls("*:*" + base_name, r=True) or cmds.ls(base_name, r=True)
        # Фильтруем то, что реально существует
        found = [obj for obj in found if cmds.objExists(obj)]
        if found:
            valid_objs.append(found[0])
            
    # Возвращаем список с сохранением порядка, удаляя возможные дубликаты
    seen = set()
    return [x for x in valid_objs if not (x in seen or seen.add(x))]