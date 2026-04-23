# -*- coding: utf-8 -*-
"""
sl_batch_import_v2.py — Maya 2022 (Py2-compatible)

Batch Import для Studio Library с учётом новых правил:
- Длительности клипов берём из pose.json (metadata.startFrame/endFrame) в папках .anim
- План раскладки (start/end для каждого клипа) строим ДО импорта, используя глобальные CURRENT_START и GAP_FRAMES
- Импортируем ВСЕ анимации по плану
- В САМОМ КОНЦЕ обрамляем каждый клип idle-позами на кадрах (start-1) и (end+1)
- Ноду AnimAssistant заполняем планом (только клипы)

Глобальные параметры (условия задачи) вынесены наверх.
"""

from __future__ import unicode_literals, print_function

import os
import re
import sys
import json
import shutil
import tempfile
import time
import traceback
from maya import cmds

# -----------------------------------------------
# ГЛОБАЛЬНЫЕ ПАРАМЕТРЫ (условия задачи)
# -----------------------------------------------
CURRENT_START = 1        # стартовый кадр первого клипа
GAP_FRAMES = 5          # отступ между клипами (в кадрах)
DEFAULT_DURATION = 50   # дефолт для клипов без валидной длительности в pose.json

# Имена поз, которые считаем idle (приоритет — по порядку)
IDLE_CANDIDATES = ["idle", "wait_pose"]

# -----------------------------------------------
# Константы ноды AnimAssistant и служебные
# -----------------------------------------------
ASSIST_NODE = "AnimAssistant"
ASSIST_ATTRS = ["AnimationClipName", "StartFrame", "EndFrame"]
THUMB_BASENAME = "thumbnail"

# -----------------------------------------------
# Утиль
# -----------------------------------------------
def _u(s):
    try:
        return s.decode('utf-8') if isinstance(s, str) else unicode(s)
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

def _read_text_safe(path):
    f = open(path, 'rb')
    try:
        data = f.read()
    finally:
        f.close()
    try:
        return data.decode('utf-8')
    except Exception:
        return data.decode('cp1251', 'ignore')

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
    try:
        import studiolibrary
        try:
            from studiolibrary.widgets.librarywindow import libraryWindow
            win = libraryWindow()
        except Exception:
            win = studiolibrary.main.window()
    except Exception:
        return None

    if not win:
        return None

    try:
        lib = win.library()
        items = lib.selectedItems() or lib.breadcrumbs()
        item = items[-1] if items else None
        path = item.path() if item else None
        return path
    except Exception:
        return None

# -----------------------------------------------
# -------------------- SET (.set) ----------------
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

def _get_sl_main_window():
    try:
        import studiolibrary
        try:
            from studiolibrary.widgets.librarywindow import libraryWindow
            return libraryWindow()
        except Exception:
            return studiolibrary.main.window()
    except Exception:
        return None

def _create_set_from_selection(library_folder, default_name="controls"):
    sel = cmds.ls(sl=True, transforms=True) or []
    if not sel:
        _warn(u"Выделите контролы в сцене и повторите.")
        return None

    ts = time.strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(library_folder, _nice_name("%s_%s" % (default_name, ts)) + ".set")
    _ensure_dir(folder)

    try:
        from mutils import selectionset as mu_sel
        mu_sel.saveSelectionSet(os.path.join(folder, "set.json"), sel, metadata=None)
    except Exception:
        data = {"metadata": {}, "objects": {n: {} for n in sel}}
        with open(os.path.join(folder, "set.json"), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # Превью не обязательно для импорта — пропускаем
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
# Скан папки SL + длительность из pose.json
# -----------------------------------------------

def _scan_items(base_folder):
    items = []
    for name in os.listdir(base_folder):
        low = name.lower()
        full = os.path.join(base_folder, name)
        if not os.path.isdir(full):
            continue
        if low.endswith(".anim"):
            items.append({"type": "anim", "name": name[:-5], "path": full})
        elif low.endswith(".pose"):
            items.append({"type": "pose", "name": name[:-5], "path": full})
    return items


def _read_duration_from_pose_json(anim_dir):
    """Возвращает длительность клипа из anim_dir по metadata.startFrame/endFrame.
    Если нет данных — None.
    """
    pose_json = os.path.join(anim_dir, "pose.json")
    if not os.path.exists(pose_json):
        return None
    try:
        with open(pose_json, 'r') as f:
            data = json.load(f) or {}
        meta = data.get('metadata') or {}
        s = meta.get('startFrame')
        e = meta.get('endFrame')
        if s is None or e is None:
            return None
        s = int(round(float(s)))
        e = int(round(float(e)))
        if e < s:
            return None
        return e - s + 1
    except Exception as e:
        _warn("pose.json parse error in %s: %s" % (anim_dir, e))
        return None

# -----------------------------------------------
# Группировка/сортировка анимаций
# -----------------------------------------------

def _group_key(name):
    base = (name or '').lower()
    base = re.sub(r'(_in|_out|^in_|^out_|\bto\b)', '', base)
    base = re.sub(r'(\d+)$', '', base)
    base = base.replace('__', '_').strip('_')
    return base


def _sort_anim_names(names):
    def weight(nm):
        low = nm.lower()
        if low in ("idle", "wait_pose"):
            return (0, _group_key(low), low)
        if low in ("walk", "normal_move"):
            return (1, _group_key(low), low)
        return (2, _group_key(low), low)
    return sorted(names, key=weight)

# -----------------------------------------------
# План клипов (только словари, без импорта)
# -----------------------------------------------

def _build_plan_from_fs(base_folder):
    """Сканируем папку, читаем длительности из pose.json, строим план раскладки.
    Возвращает: (plan, poses)
      plan = [ {"name": name, "path": anim_path, "dur": dur, "start": s, "end": e}, ... ]
      poses = { name_lower : pose_path }
    """
    items = _scan_items(base_folder)
    if not items:
        return [], {}

    # Позы
    poses = {it["name"].lower(): it["path"] for it in items if it["type"] == "pose"}

    # Анимации
    anims = [it for it in items if it["type"] == "anim"]
    names = [it["name"] for it in anims]
    names_sorted = _sort_anim_names(names)

    # Быстрый доступ по имени → путь
    path_by_name = {it["name"].lower(): it["path"] for it in anims}

    # Длительности из pose.json
    dur_by_name = {}
    for nm in names_sorted:
        low = nm.lower()
        p = path_by_name.get(low)
        dur = _read_duration_from_pose_json(p)
        if dur is None or dur <= 0:
            dur = DEFAULT_DURATION
        dur_by_name[low] = int(dur)

    # Раскладка кадров
    plan = []
    current = int(CURRENT_START)
    gap = int(GAP_FRAMES)
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
    for attr in ASSIST_ATTRS:
        plug = "{0}.{1}".format(ASSIST_NODE, attr)
        try:
            val = cmds.getAttr(plug)
        except Exception:
            val = None
        if val is None:
            cmds.setAttr(plug, "", type="string")


def _write_anim_assistant_from_plan(plan):
    _ensure_anim_node()
    names = []
    starts = []
    ends = []
    for i, c in enumerate(plan):
        nn = str(i+1).zfill(2)
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
# Импорт анимации + применение позы
# -----------------------------------------------

def _import_anim(anim_dir, objects, start_frame):
    """Импортирует анимацию и сдвигает ключи так, чтобы клип начинался на start_frame.
    Возвращает фактическую длительность из плана не вычисляется здесь.
    """
    from mutils import Animation
    anim = Animation.fromPath(anim_dir)
    anim.load(objects=objects, option="replace")

    try:
        # Грубый сдвиг: смещаем все ключи относительно текущего min playback
        min_t = int(cmds.playbackOptions(q=True, min=True))
        offset = int(start_frame) - min_t
        if offset:
            all_nodes = objects or (cmds.ls(sl=True) or [])
            if all_nodes:
                cmds.keyframe(all_nodes, edit=True, relative=True, timeChange=offset)
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

# -----------------------------------------------
# Поиск idle-позы в библиотеке
# -----------------------------------------------

def _find_idle_pose_path(poses_dict):
    for nm in IDLE_CANDIDATES:
        p = poses_dict.get(nm.lower())
        if p and os.path.isdir(p):
            return p
    return None

# -----------------------------------------------
# MAIN: батч‑импорт
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

    # 1) план + позы из файловой системы
    plan, poses = _build_plan_from_fs(base_folder)
    if not plan:
        _warn(u"В папке нет .anim/.pose")
        return

    # 2) записываем план в AnimAssistant (без idle)
    _write_anim_assistant_from_plan(plan)

    # 3) импорт всех клипов по плану
    for it in plan:
        _import_anim(it["path"], objects, start_frame=it["start"])

    # 4) финальное обрамление idle-позами
    idle_path = _find_idle_pose_path(poses)
    if idle_path:
        placed = 0
        seen_frames = set()
        for it in plan:
            s = it["start"] - 1
            e = it["end"] + 1
            # допускаем кадр 0
            for fr in (s, e):
                if fr in seen_frames:
                    continue  # избежать двойного применения, если совпадает
                if fr < 0:
                    continue
                if _apply_pose_at_frame(idle_path, objects, fr):
                    seen_frames.add(fr)
                    placed += 1
        _info(u"Idle поз установлено: %d" % placed)
    else:
        _info(u"Idle-поза не найдена в библиотеке — обрамление пропущено.")

    _info(u"Batch Import: импортировано анимаций: %d" % len(plan))

# -----------------------------------------------
# Кнопка в UI Studio Library
# -----------------------------------------------

def _on_ui_click():
    try:
        folder = _selected_folder_path_from_sl()
        if not folder:
            res = cmds.fileDialog2(cap="Select Studio Library Folder", fm=3)
            folder = res[0] if res else None
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


def _append_button_to_toolbar():
    win = _get_sl_main_window()
    if not win:
        raise RuntimeError("Studio Library window not found")

    try:
        from PySide2 import QtWidgets
    except Exception:
        from Qt import QtWidgets

    if win.findChild(QtWidgets.QPushButton, "BatchImportButton"):
        return True

    btn = QtWidgets.QPushButton(u"Batch Import", win)
    btn.setObjectName("BatchImportButton")
    btn.setToolTip(_u("Импорт анимаций в таймлайн + список в AnimAssistant (dur from pose.json)"))
    btn.clicked.connect(lambda: _on_ui_click())

    toolbars = win.findChildren(QtWidgets.QToolBar)
    if toolbars:
        toolbars[0].addWidget(btn)
    else:
        layout = win.layout() or QtWidgets.QVBoxLayout(win)
        layout.addWidget(btn)

    return True


def install_patch():
    try:
        ok = _append_button_to_toolbar()
        if ok:
            _info("Batch Import v2: patch installed.")
    except Exception:
        tb = traceback.format_exc()
        try:
            _warn(_u("Patch error:\n") + _u(tb))
        except Exception:
            _warn("Patch error (traceback decode failed)")

# -----------------------------------------------
# Сниппет для шелф‑кнопки
# -----------------------------------------------
SHELF_SNIPPET = r'''
import sys
from maya import cmds
BASE = r"{BASE}"
if BASE not in sys.path:
    sys.path.append(BASE)
try:
    import sl_batch_import_v2 as sl_bi
    try:
        reload(sl_bi)  # Py2.7
    except Exception:
        pass
    sl_bi.install_patch()
except Exception as e:
    cmds.warning("Не удалось установить Batch Import v2: %s" % e)
'''
