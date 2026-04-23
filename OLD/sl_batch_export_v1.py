# -*- coding: utf-8 -*-
# sl_batch_export.py — Maya 2022 (Python 2.7)

from maya import cmds
import os
import re
import json
import shutil
import time

# -------------------- Константы --------------------

ISO1 = "isometric_1"
ISO7 = "isometric_7"

SPECIAL_POSE_IDLE = {"idle", "wail_pose"}
SPECIAL_POSE_WALK = {"walk", "narmal_move"}

# -------------------- Хелперы ----------------------

try:
    unicode  # noqa
except NameError:
    unicode = str

def _U(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode("utf-8")
    except Exception:
        try:
            return unicode(s)
        except Exception:
            return u""

def _warn(msg):
    try:
        cmds.warning(_U(msg))
    except Exception:
        print("# Warning:", _U(msg))

def _info(msg):
    try:
        cmds.inViewMessage(amg=_U(msg), pos="topCenter", fade=True)
    except Exception:
        print(_U(msg))

def _ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p)
    return p

def _nice_name(s):
    return re.sub(r"[^\w\-]+", "_", (s or "").strip().lower())

# -------------------- Камеры/превью ----------------

def _ensure_camera(name, tx=30, ty=30, tz=30, rx=-35, ry=45, rz=0, focal=35.0):
    if not cmds.objExists(name):
        tr, sh = cmds.camera()
        try: cmds.rename(tr, name)
        except Exception: pass
    try:
        cmds.setAttr("%s.translate" % name, tx, ty, tz, type="double3")
        cmds.setAttr("%s.rotate" % name, rx, ry, rz, type="double3")
    except Exception:
        pass
    shape = (cmds.listRelatives(name, s=True, f=False) or [])
    if shape:
        try: cmds.setAttr("%s.focalLength" % shape[0], focal)
        except Exception: pass

def ensure_cameras():
    _ensure_camera(ISO1, tx=25, ty=28, tz=35, rx=-20, ry=38, rz=0, focal=40.0)
    _ensure_camera(ISO7, tx=22, ty=40, tz=22, rx=-45, ry=45, rz=0, focal=35.0)

def _get_any_model_panel():
    try:
        visible = [p for p in cmds.getPanel(vis=True) if cmds.getPanel(to=p) == "modelPanel"]
    except Exception:
        visible = []
    if visible: return visible[0]
    try:
        mp = cmds.getPanel(type="modelPanel")
        if mp: return mp[0]
    except Exception: pass
    return None

def _make_thumbnail_png(camera, frame, out_png, w=480, h=270):
    _ensure_dir(os.path.dirname(out_png))
    cur_panel = None
    try: cur_panel = cmds.getPanel(withFocus=True)
    except Exception: pass
    panel = _get_any_model_panel()
    if panel:
        try: cmds.modelPanel(panel, e=True, cam=camera)
        except Exception: pass
    try: cmds.currentTime(frame, e=True)
    except Exception: pass
    cmds.playblast(
        frame=[frame], format="image", cf=out_png, viewer=False,
        percent=100, compression="png", quality=100, wh=[w, h], forceOverwrite=True
    )
    if cur_panel and cmds.control(cur_panel, exists=True):
        try: cmds.setFocus(cur_panel)
        except Exception: pass
    return out_png

# -------------------- SET (.set) -------------------

def _find_set_folders(library_folder):
    out = []
    for name in os.listdir(library_folder):
        p = os.path.join(library_folder, name)
        if os.path.isdir(p) and name.lower().endswith(".set") and \
           os.path.exists(os.path.join(p, "set.json")):
            out.append(p)
    return sorted(out)

def _read_objects_from_set(set_folder):
    """Читает set.json и возвращает список имён объектов (ключи 'objects')."""
    path = os.path.join(set_folder, "set.json")
    try:
        with open(path, "r") as f:
            data = json.load(f) or {}
        objs = data.get("objects") or {}
        # В SL-формате 'objects' — словарь name -> dict (см. пример set.json):contentReference[oaicite:2]{index=2}
        return [str(k) for k in objs.keys()]
    except Exception as e:
        _warn("Cannot read set.json: %s" % e)
        return []

def _prompt_choose_set(parent, items):
    """Диалог выбора одного сета из списка путей."""
    from PySide2 import QtWidgets
    labels = [os.path.basename(p) for p in items]
    item, ok = QtWidgets.QInputDialog.getItem(parent, u"Выбор набора контролов",
                                              u"Найдено несколько .set — выберите:", labels, 0, False)
    if ok and item in labels:
        return items[labels.index(item)]
    return None

def _create_set_from_selection(library_folder, default_name="controls"):
    """Создаёт SL‑совместимый сет: папка *.set + set.json + thumbnail.png."""
    sel = cmds.ls(sl=True) or []
    if not sel:
        _warn(u"Выделите контролы в сцене и повторите.")
        return None

    # имя папки
    ts = time.strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(library_folder, _nice_name("%s_%s" % (default_name, ts)) + ".set")
    _ensure_dir(folder)

    # set.json через mutils.selectionset
    try:
        from mutils import selectionset as mu_sel
        mu_sel.saveSelectionSet(os.path.join(folder, "set.json"), sel, metadata=None)
    except Exception as e:
        # запасной вариант — пишем минимум сами
        data = {"metadata": {}, "objects": {n: {} for n in sel}}
        with open(os.path.join(folder, "set.json"), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # превью
    thumb = os.path.join(folder, "thumbnail.png")
    try:
        cur = cmds.currentTime(q=True)
    except Exception:
        cur = 1
    try:
        _make_thumbnail_png(ISO1, int(cur), thumb)
    except Exception:
        pass

    _info(u"<hl>Создан сет</hl>: %s" % os.path.basename(folder))
    return folder

def _pick_or_create_set(library_folder):
    """Возвращает (set_folder, objects). Даёт выбрать/создать при необходимости."""
    from PySide2 import QtWidgets
    parent = _get_sl_main_window()

    sets = _find_set_folders(library_folder)
    chosen = None

    if not sets:
        # нет сетов — попросим выделить и создадим новый
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

# ---------------- AnimAssistant → список клипов ----

def _read_anim_list_from_animassistant():
    try:
        from studiolibrary.widgets.anim_assist_helper import AnimAssistHelper
    except Exception as e:
        _warn("No anim_assist_helper: %s" % e)
        return []
    anims = []
    try:
        for ap in (AnimAssistHelper.getAnimAssistAnims() or []):
            name = ap.name()
            begin = int(ap.begin())
            end = int(ap.end())
            if name and begin is not None and end is not None:
                anims.append({"name": name, "start": begin, "end": end})
    except Exception as e:
        _warn("AnimAssistant read error: %s" % e)
    return anims

# ---------------- Сохранение .anim/.pose  ---------

def _save_anim_item(objects, dst_dir, start, end, icon_png=None):
    """Создаёт SL‑item .anim (animation.ma/mb + pose.json + thumbnail.png)."""
    from mutils import animation as mu_animation
    _ensure_dir(dst_dir)

    # гарантируем валидные параметры
    start = int(start); end = int(end)
    meta = {
        "createdBy": "sl_batch_export",
        "time": [start, end],
    }
    icon = icon_png if (icon_png and os.path.exists(icon_png)) else ""

    mu_animation.saveAnim(
        objects=objects,
        path=dst_dir,                 # путь к ПАПКЕ *.anim
        time=(start, end),
        fileType="mayaAscii",
        metadata=meta,                # << было None → теперь словарь
        iconPath=icon,
        sequencePath="",
        bakeConnected=False
    )


def _save_pose_item(objects, dst_dir, icon_png=None):
    """Создаёт SL‑item .pose (pose.json + thumbnail.png)."""
    from mutils import pose as mu_pose
    _ensure_dir(dst_dir)
    pose_json = os.path.join(dst_dir, "pose.json")
    mu_pose.savePose(pose_json, objects=objects)
    if icon_png and os.path.exists(icon_png):
        try: shutil.copyfile(icon_png, os.path.join(dst_dir, "thumbnail.png"))
        except Exception: pass

# ---------------- Основной батч --------------------

def batch_export(folder_path):
    """
    1) Берём сет контролов в SL‑формате (*.set) из целевой папки
       (даём выбрать если несколько, создаём из выделения если нет).
    2) Экспортируем клипы из AnimAssistant в .anim‑папки с превью ISO1.
    3) Для idle/wail_pose и walk/narmal_move — доп. .pose‑папка с превью ISO7.
    """
    ensure_cameras()

    set_folder, ctrls = _pick_or_create_set(folder_path)
    if not ctrls:
        return

    clips = _read_anim_list_from_animassistant()
    if not clips:
        _warn(u"Список анимаций пуст (AnimAssistant).")
        return

    results = []
    for it in clips:
        name  = it.get("name")
        start = int(it.get("start"))
        end   = int(it.get("end"))

        safe = _nice_name(name)
        anim_dir = os.path.join(folder_path, safe + ".anim")

        # превью ISO1 на стартовом кадре
        tmp_icon = os.path.join(folder_path, "__tmp_thumbnail.png")
        try: _make_thumbnail_png(ISO1, start, tmp_icon)
        except Exception: tmp_icon = ""

        _save_anim_item(ctrls, anim_dir, start, end, icon_png=tmp_icon)
        results.append(anim_dir)

        lname = (name or "").strip().lower()
        if lname in SPECIAL_POSE_IDLE or lname in SPECIAL_POSE_WALK:
            pose_dir = os.path.join(folder_path, safe + "_pose.pose")
            tmp_icon_pose = os.path.join(folder_path, "__tmp_thumbnail_pose.png")
            try: _make_thumbnail_png(ISO7, start, tmp_icon_pose)
            except Exception: tmp_icon_pose = ""
            _save_pose_item(ctrls, pose_dir, icon_png=tmp_icon_pose)

        # чистим временные иконки
        for p in (tmp_icon, locals().get("tmp_icon_pose", "")):
            try:
                if p and os.path.exists(p):
                    os.remove(p)
            except Exception:
                pass

    _info(u"<hl>Batch Export</hl>: %d items" % len(results))
    return results

# -------------- Интеграция в SL UI ----------------

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

def _selected_folder_path_from_sl():
    try:
        import studiolibrary
        lib = studiolibrary.library()
        paths = lib.selectedPaths()
        if paths:
            return paths[0]
    except Exception:
        pass
    folder = cmds.fileDialog2(cap="Select Studio Library Folder", fm=3)
    return folder[0] if folder else None

def _append_button_to_sl_toolbar():
    from PySide2 import QtWidgets
    win = _get_sl_main_window()
    if not win: return False

    existing = win.findChild(QtWidgets.QPushButton, "BatchExportButton")
    if existing: return True

    btn = QtWidgets.QPushButton("Batch Export", win)
    btn.setToolTip("Экспорт клипов из AnimAssistant в выбранную папку SL")
    btn.setObjectName("BatchExportButton")
    btn.clicked.connect(lambda: _on_click_batch())

    toolbars = win.findChildren(QtWidgets.QToolBar)
    if toolbars:
        toolbars[0].addWidget(btn)
    else:
        layout = win.layout() or QtWidgets.QVBoxLayout(win)
        layout.insertWidget(0, btn)
    return True

def _on_click_batch():
    folder = _selected_folder_path_from_sl()
    if not folder: return
    batch_export(folder)

def install_patch():
    try:
        _append_button_to_sl_toolbar()
    except Exception as e:
        _warn("Batch export patch error: %s" % e)
