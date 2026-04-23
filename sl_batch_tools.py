# -*- coding: utf-8 -*-
"""
sl_batch_import_v3.py — Maya 2022 (Py3; Py2-толерантно)

Batch Import для Studio Library по новой схеме:
- Сканируем папку SL, для КАЖДОЙ .anim читаем pose.json и берём длительность: dur = endFrame - startFrame + 1
- Формируем план раскладки ТОЛЬКО на словарях: сортируем имена клипов (idle/wait → walk/normal_move → остальные),
  приклеиваем длительности, считаем start/end при CURRENT и GAP
- Сразу заполняем ноду AnimAssistant по плану (только клипы)
- Импортируем ВСЕ клипы по рассчитанным окнам
- В САМОМ КОНЦЕ: idle-позой обрамляем каждый клип на кадрах (start-1) и (end+1)
"""

from __future__ import print_function

import os
import re
import json
import traceback
from maya import cmds

# -----------------------------------------------
# ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ («условия задачи»)
# -----------------------------------------------
CURRENT = 1            # первый кадр для первого клипа
GAP = 5                # зазор между клипами (в кадрах)
DEFAULT_DURATION = 50  # запасной случай, если pose.json битый/пустой

# Имена, которые считаем idle (приоритет — по порядку)
IDLE_CANDIDATES = ["idle", "wait_pose"]

# Имена, которые считаем «ходьбой» для группировки
WALK_CANDIDATES = ["walk", "normal_move"]

# Константы для ноды AnimAssistant
ASSIST_NODE = "AnimAssistant"
ASSIST_ATTRS = ["AnimationClipName", "StartFrame", "EndFrame"]


# -----------------------------------------------
# Утиль
# -----------------------------------------------
try:
    unicode  # noqa
except NameError:
    unicode = str

def _u(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode('utf-8')
    except Exception:
        try:
            return unicode(s)
        except Exception:
            return u""

def _warn(msg):
    try:
        cmds.warning(_u(msg))
    except Exception:
        print("# Warning:", _u(msg))

def _info(msg):
    try:
        print(_u(msg))
    except Exception:
        pass

def _ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def _nice_name(name):
    s = re.sub(r'[^0-9a-zA-Z_\-]+', '_', (name or '').strip())
    s = re.sub(r'__+', '_', s).strip('_')
    return s or "item"


# -----------------------------------------------
# Studio Library: текущая папка / окно
# -----------------------------------------------
def _selected_folder_path_from_sl():
    """
    Пытаемся взять выбранную папку в окне Studio Library.
    Если не получилось — спрашиваем диалогом.
    """
    try:
        import studiolibrary
        lib = studiolibrary.library()
        paths = lib.selectedPaths()
        if paths:
            return paths[0]
    except Exception:
        pass
    res = cmds.fileDialog2(cap="Select Studio Library Folder", fm=3)
    return res[0] if res else None

def _get_sl_main_window():
    try:
        import shiboken2
        from PySide2 import QtWidgets
        import maya.OpenMayaUI as omui
        ptr = omui.MQtUtil.findWindow("StudioLibrary")
        if ptr:
            return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
        for w in QtWidgets.QApplication.topLevelWidgets():
            try:
                if "Studio Library" in w.windowTitle():
                    return w
            except Exception:
                pass
    except Exception:
        pass
    return None


# -----------------------------------------------
# Скан папки SL + чтение длительностей из pose.json
# -----------------------------------------------
def _scan_items(base_folder):
    """
    Возвращает список элементов в папке:
      [{ "type": "anim"/"pose", "name": <без .anim/.pose>, "path": <абс путь> }, ...]
    """
    items = []
    for name in os.listdir(base_folder):
        full = os.path.join(base_folder, name)
        if not os.path.isdir(full):
            continue
        low = name.lower()
        if low.endswith(".anim"):
            items.append({"type": "anim", "name": name[:-5], "path": full})
        elif low.endswith(".pose"):
            items.append({"type": "pose", "name": name[:-5], "path": full})
    return items

def _read_duration_from_pose_json(anim_dir):
    """
    Читает <anim_dir>/pose.json, берёт metadata.startFrame/endFrame.
    Возвращает dur = endFrame - startFrame + 1, либо None.
    """
    pose_json = os.path.join(anim_dir, "pose.json")
    if not os.path.exists(pose_json):
        return None
    try:
        with open(pose_json, "r") as f:
            data = json.load(f) or {}
        meta = data.get("metadata") or {}
        s = meta.get("startFrame")
        e = meta.get("endFrame")
        if s is None or e is None:
            return None
        s = int(round(float(s)))
        e = int(round(float(e)))
        if e < s:
            return None
        return int(e - s + 1)
    except Exception as e:
        _warn("pose.json parse error in %s: %s" % (anim_dir, e))
        return None


# -----------------------------------------------
# Группировка/сортировка имён клипов
# -----------------------------------------------
def _group_key(name):
    base = (name or "").lower()
    base = re.sub(r'(_in|_out|^in_|^out_|\bto\b)', '', base)
    base = re.sub(r'(\d+)$', '', base)
    base = base.replace('__', '_').strip('_')
    return base

def _sort_anim_names(names):
    """
    Порядок: idle/wait → walk/normal_move → остальные (по group_key, затем по имени)
    """
    def weight(nm):
        low = nm.lower()
        if low in IDLE_CANDIDATES:
            return (0, _group_key(low), low)
        if low in WALK_CANDIDATES:
            return (1, _group_key(low), low)
        return (2, _group_key(low), low)
    return sorted(names, key=weight)


# -----------------------------------------------
# План: только словари (без действий в сцене)
# -----------------------------------------------
def _build_plan_from_fs(base_folder):
    """
    Делим содержимое на позы и анимации, читаем dur из pose.json для .anim,
    сортируем имена, считаем start/end по CURRENT и GAP.

    Возвращает: (plan, poses)
      plan  = [{"name": <str>, "path": <anim_path>, "dur": <int>, "start": <int>, "end": <int>}, ...]
      poses = { <name_lower>: <pose_dir> }
    """
    items = _scan_items(base_folder)
    if not items:
        return [], {}

    poses = {it["name"].lower(): it["path"] for it in items if it["type"] == "pose"}
    anims = [it for it in items if it["type"] == "anim"]

    # индекс пути по имени
    path_by_name = {it["name"].lower(): it["path"] for it in anims}

    # имена для сортировки
    names_sorted = _sort_anim_names([it["name"] for it in anims])

    # длительности
    dur_by_name = {}
    for nm in names_sorted:
        low = nm.lower()
        p = path_by_name.get(low)
        dur = _read_duration_from_pose_json(p)
        if dur is None or dur <= 0:
            dur = DEFAULT_DURATION
        dur_by_name[low] = int(dur)

    # раскладка
    plan = []
    current = int(CURRENT)
    gap = int(GAP)
    for nm in names_sorted:
        low = nm.lower()
        dur = int(dur_by_name[low])
        start = current
        end = start + dur - 1
        plan.append({
            "name": nm,
            "path": path_by_name[low],
            "dur": dur,
            "start": start,
            "end": end,
        })
        current = end + 1 + gap

    return plan, poses


# -----------------------------------------------
# AnimAssistant
# -----------------------------------------------
def _ensure_anim_node():
    if not cmds.objExists(ASSIST_NODE):
        cmds.createNode("geometryVarGroup", n=ASSIST_NODE, ss=True)
    for attr in ASSIST_ATTRS:
        if not cmds.attributeQuery(attr, n=ASSIST_NODE, exists=True):
            cmds.addAttr(ASSIST_NODE, ln=attr, dt="string")
    # инициализируем пустыми строками (чтобы getAttr не падал)
    for attr in ASSIST_ATTRS:
        plug = "{0}.{1}".format(ASSIST_NODE, attr)
        try:
            val = cmds.getAttr(plug)
        except Exception:
            val = None
        if val is None:
            cmds.setAttr(plug, "", type="string")

def _write_anim_assistant_from_plan(plan):
    """
    В AnimAssistant пишем ТОЛЬКО клипы.
    Формат имён — 01|name_start-end (как и раньше).
    """
    _ensure_anim_node()
    names = []
    starts = []
    ends = []
    for i, c in enumerate(plan):
        nn = str(i + 1).zfill(2)
        names.append("%s|%s_%d-%d" % (nn, c["name"], c["start"], c["end"]))
        starts.append(str(c["start"]))
        ends.append(str(c["end"]))
    cmds.setAttr(ASSIST_NODE + ".AnimationClipName", " ".join(names), type="string")
    cmds.setAttr(ASSIST_NODE + ".StartFrame", " ".join(starts), type="string")
    cmds.setAttr(ASSIST_NODE + ".EndFrame", " ".join(ends), type="string")
    try:
        from maya import mel
        mel.eval("AnimLiUpdate()")
    except Exception:
        pass


# -----------------------------------------------
# Импорт анимаций и применение поз
# -----------------------------------------------
def _import_anim(anim_dir, objects, start_frame):
    """
    Загружает .anim на указанные objects.
    После загрузки грубо сдвигает ВСЕ ключи этих объектов так, чтобы minPlayback совпал со start_frame.
    (Детальный оффсет по каждому клипу опционален и может быть добавлен отдельно).
    """
    from mutils import Animation
    anim = Animation.fromPath(anim_dir)
    anim.load(objects=objects, option="replace")

    try:
        # смещение относительно текущего min playback
        min_t = int(cmds.playbackOptions(q=True, min=True))
        offset = int(start_frame) - min_t
        if offset:
            nodes = objects or (cmds.ls(sl=True) or [])
            if nodes:
                cmds.keyframe(nodes, edit=True, relative=True, timeChange=offset)
    except Exception as e:
        _warn("Offset error: %s" % e)

def _apply_pose_at_frame(pose_dir, objects, frame):
    from mutils import Pose
    try:
        cmds.currentTime(int(frame), e=True)
        pose = Pose.fromPath(pose_dir)
        pose.load(objects=objects)
        return True
    except Exception as e:
        _warn("Pose apply error @%s: %s" % (frame, e))
        return False

def _find_idle_pose_path(poses_dict):
    """
    Возвращает путь к idle-позе по приоритету IDLE_CANDIDATES, либо None.
    """
    for nm in IDLE_CANDIDATES:
        p = poses_dict.get(nm.lower())
        if p and os.path.isdir(p):
            return p
    return None


# -----------------------------------------------
# SET (.set): выбор/создание и список контролов
# (упрощённо: читаем только set.json существующего .set
#  или создаём из выделения, если ничего нет)
# -----------------------------------------------
def _find_set_folders(library_folder):
    out = []
    for name in os.listdir(library_folder):
        p = os.path.join(library_folder, name)
        if os.path.isdir(p) and name.lower().endswith(".set") and \
           os.path.exists(os.path.join(p, "set.json")):
            out.append(p)
    return sorted(out)

def _read_objects_from_set(set_folder):
    path = os.path.join(set_folder, "set.json")
    try:
        with open(path, "r") as f:
            data = json.load(f) or {}
        objs = data.get("objects") or {}
        return [str(k) for k in objs.keys()]
    except Exception as e:
        _warn("Cannot read set.json: %s" % e)
        return []

def _prompt_choose_set(parent, items):
    try:
        from PySide2 import QtWidgets
    except Exception:
        from Qt import QtWidgets
    labels = [os.path.basename(p) for p in items]
    item, ok = QtWidgets.QInputDialog.getItem(
        parent, u"Выбор набора контролов",
        u"Найдено несколько .set — выберите:", labels, 0, False
    )
    if ok and item in labels:
        return items[labels.index(item)]
    return None

def _create_set_from_selection(library_folder, default_name="controls"):
    sel = cmds.ls(sl=True, transforms=True) or []
    if not sel:
        _warn(u"Выделите контролы в сцене и повторите.")
        return None
    from time import strftime
    folder = os.path.join(library_folder, _nice_name("%s_%s" % (default_name, strftime("%Y%m%d_%H%M%S"))) + ".set")
    _ensure_dir(folder)
    # пробуем через mutils.selectionset; если нет — пишем минимальный JSON
    try:
        from mutils import selectionset as mu_sel
        mu_sel.saveSelectionSet(os.path.join(folder, "set.json"), sel, metadata=None)
    except Exception:
        data = {"metadata": {}, "objects": {n: {} for n in sel}}
        with open(os.path.join(folder, "set.json"), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    _info(u"<hl>Создан сет</hl>: %s" % os.path.basename(folder))
    return folder

def _pick_or_create_set(library_folder):
    parent = _get_sl_main_window()
    sets = _find_set_folders(library_folder)
    chosen = None

    if not sets:
        chosen = _create_set_from_selection(library_folder)
        if not chosen:
            return None, []
    elif len(sets) == 1:
        chosen = sets[0]
    else:
        chosen = _prompt_choose_set(parent, sets)
        if not chosen:
            _warn(u"Сет не выбран.")
            return None, []

    objects = _read_objects_from_set(chosen)
    if not objects:
        _warn(u"В выбранном сете нет объектов.")
    return chosen, objects


# -----------------------------------------------
# MAIN: батч-импорт
# -----------------------------------------------
def import_batch(base_folder):
    if not base_folder or not os.path.isdir(base_folder):
        raise RuntimeError("Invalid folder for import")

    # 0) сет контролов
    set_folder, objects = _pick_or_create_set(base_folder)
    if not set_folder or not objects:
        _warn(u"Не удалось получить контролы для импорта.")
        return
    _info(u"Контролов в сете: %d" % len(objects))

    # 1) план + позы (только из файлов)
    plan, poses = _build_plan_from_fs(base_folder)
    if not plan:
        _warn(u"В папке нет .anim/.pose")
        return

    # 2) записываем план в AnimAssistant (без idle)
    _write_anim_assistant_from_plan(plan)

    # 3) импорт всех клипов по плану
    for it in plan:
        _import_anim(it["path"], objects, start_frame=it["start"])

    # 4) финальное обрамление idle-позами на кадрах (start-1) и (end+1)
    idle_path = _find_idle_pose_path(poses)
    if idle_path:
        placed = 0
        seen_frames = set()
        for it in plan:
            s = it["start"] - 1   # допускаем 0 для первого клипа
            e = it["end"] + 1
            for fr in (s, e):
                if fr in seen_frames:
                    continue  # не дублируем, если совпали точки
                if fr < 0:
                    continue
                if _apply_pose_at_frame(idle_path, objects, fr):
                    seen_frames.add(fr)
                    placed += 1
        _info(u"Idle поз установлено: %d" % placed)
    else:
        _info(u"Idle-поза не найдена в библиотеке — обрамление пропущено.")

    _info(u"Batch Import v3: импортировано анимаций: %d" % len(plan))


# -----------------------------------------------
# Кнопка в UI Studio Library
# -----------------------------------------------
def _on_ui_click():
    try:
        folder = _selected_folder_path_from_sl()
        if not folder:
            _warn(u"Batch Import: папка не выбрана.")
            return
        import_batch(folder)
    except Exception:
        tb = traceback.format_exc()
        try:
            _warn(u"Batch Import error:\n" + _u(tb))
        except Exception:
            _warn(u"Batch Import error (traceback decode failed)")

def _append_button_to_sl_toolbar():
    """
    Добавляет две кнопки ('Btch_Import' и 'Btch_Export') в тулбар Studio Library.
    Если тулбара нет — кладёт их в общий QHBoxLayout в layout окна.
    """
    try:
        from PySide2 import QtWidgets
    except Exception:
        from Qt import QtWidgets

    win = _get_sl_main_window()
    if not win:
        raise RuntimeError("Studio Library window not found")

    # проверим, не созданы ли уже
    if win.findChild(QtWidgets.QPushButton, "BatchImportButton") and \
       win.findChild(QtWidgets.QPushButton, "BatchExportButton"):
        return True

    # создаём контейнер с горизонтальным расположением
    container = QtWidgets.QWidget(win)
    hbox = QtWidgets.QHBoxLayout(container)
    hbox.setContentsMargins(0, 0, 0, 0)
    hbox.setSpacing(4)

    # --- Кнопка Import ---
    btn_imp = QtWidgets.QPushButton(u"Btch_Import", container)
    btn_imp.setObjectName("BatchImportButton")
    btn_imp.setToolTip(_u("Импорт клипов по длительностям из pose.json + план в AnimAssistant + idle-обрамление"))
    btn_imp.clicked.connect(lambda: _on_click_import())
    hbox.addWidget(btn_imp)

    # --- Кнопка Export ---
    btn_exp = QtWidgets.QPushButton(u"Btch_Export", container)
    btn_exp.setObjectName("BatchExportButton")
    btn_exp.setToolTip(_u("Экспорт клипов из AnimAssistant в выбранную папку SL"))
    btn_exp.clicked.connect(lambda: _on_click_export())
    hbox.addWidget(btn_exp)

    # пробуем добавить в тулбар, иначе в основной layout окна
    try:
        toolbars = win.findChildren(QtWidgets.QToolBar)
    except Exception:
        toolbars = []

    if toolbars:
        toolbars[0].addWidget(container)
    else:
        layout = win.layout() or QtWidgets.QVBoxLayout(win)
        layout.addWidget(container)

    return True


def install_patch():
    try:
        ok = _append_button_to_sl_toolbar()
        if ok:
            _info("Batch Import v3: UI patched.")
    except Exception:
        tb = traceback.format_exc()
        try:
            _warn(_u("Patch error:\n") + _u(tb))
        except Exception:
            _warn("Patch error (traceback decode failed)")


# -----------------------------------------------
# Сниппет для полки (Shelf)
# -----------------------------------------------
SHELF_SNIPPET = r'''
import sys
from maya import cmds
BASE = r"{BASE}"
if BASE not in sys.path:
    sys.path.append(BASE)
try:
    import sl_batch_import_v3 as sl_bi3
    try:
        reload(sl_bi3)  # Py2.7
    except Exception:
        pass
    sl_bi3.install_patch()
except Exception as e:
    cmds.warning("Не удалось установить Batch Import v3: %s" % e)
'''
