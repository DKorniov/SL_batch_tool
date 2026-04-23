# -*- coding: utf-8 -*-
# sl_batch_export.py — Maya 2022 (Python 2.7)
#
# Batch Export для Studio Library:
# - Читает клипы из AnimAssistant
# - Работает с контрол-сетами в формате SL (*.set: set.json + thumbnail.jpg)
# - Сохраняет .anim (animation.ma/mb + pose.json + thumbnail.jpg + sequence/...)
# - Сохраняет .pose для "спец-анимаций" отдельным этапом по начальным кадрам клипов
# - Превью/секвенции делает через mutils.playblast
# - Спрашивает политику перезаписи при конфликтах (анимации И позы):
#   Перезаписать всё / Только недостающие / Отмена
#   Диалог показывает существующие/отсутствующие анимации и позы с подсчётом

from maya import cmds
import os
import re
import json
import shutil
import time

# -------------------- Константы --------------------

ISO1 = "isometric_1"
ISO7 = "isometric_7"

# Спец-позы (исправлено: wait_pose вместо wail_pose)
SPECIAL_POSE_IDLE = {"idle", "wait_pose","idle_pose"}
SPECIAL_POSE_WALK = {"walk", "normal_move"}

THUMB_BASENAME = "thumbnail"
THUMB_W = 480
THUMB_H = 270

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

def _safe_rmtree(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass

# -------------------- Камеры ----------------------

def _ensure_camera(name, tx=30, ty=30, tz=30, rx=-35, ry=45, rz=0, focal=35.0):
    if not cmds.objExists(name):
        tr, sh = cmds.camera()
        try:
            cmds.rename(tr, name)
        except Exception:
            pass
    try:
        cmds.setAttr("%s.translate" % name, tx, ty, tz, type="double3")
        cmds.setAttr("%s.rotate" % name, rx, ry, rz, type="double3")
    except Exception:
        pass
    shape = (cmds.listRelatives(name, s=True, f=False) or [])
    if shape:
        try:
            cmds.setAttr("%s.focalLength" % shape[0], focal)
        except Exception:
            pass

def ensure_cameras():
    _ensure_camera(ISO1, tx=25, ty=28, tz=35, rx=-20, ry=38, rz=0, focal=40.0)
    _ensure_camera(ISO7, tx=22, ty=40, tz=22, rx=-45, ry=45, rz=0, focal=35.0)

# -------------------- Панель/плейбласт ------------

def _get_any_model_panel():
    try:
        visible = [p for p in cmds.getPanel(vis=True) if cmds.getPanel(to=p) == "modelPanel"]
    except Exception:
        visible = []
    if visible:
        return visible[0]
    try:
        mp = cmds.getPanel(type="modelPanel")
        if mp:
            return mp[0]
    except Exception:
        pass
    return None

def _capture_icon_and_sequence(camera, start, end, base_dir, basename=THUMB_BASENAME, w=THUMB_W, h=THUMB_H):
    """
    Делает плейбласт секвенции через mutils.playblast и возвращает:
      (icon_file, sequence_dir)
    icon_file — путь к первому кадру (jpg), sequence_dir — папка с секвенцией.
    """
    from mutils import playblast as mu_playblast

    start = int(start); end = int(end)
    _ensure_dir(base_dir)
    seq_dir = os.path.join(base_dir, "sequence")
    _ensure_dir(seq_dir)
    filename = os.path.join(seq_dir, basename + ".jpg")

    panel = _get_any_model_panel()
    if panel:
        try:
            cmds.modelPanel(panel, e=True, cam=camera)
        except Exception:
            pass

    first_frame_path = mu_playblast.playblast(
        filename=filename,
        modelPanel=panel,
        startFrame=start,
        endFrame=end,
        width=w,
        height=h,
        step=1
    )
    sequence_dir = os.path.dirname(first_frame_path)
    return first_frame_path, sequence_dir

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
    """Создаёт SL‑совместимый сет: папка *.set + set.json + thumbnail.jpg."""
    sel = cmds.ls(sl=True) or []
    if not sel:
        _warn(u"Выделите контролы в сцене и повторите.")
        return None

    ts = time.strftime("%Y%m%d_%H%M%S")
    folder = os.path.join(library_folder, _nice_name("%s_%s" % (default_name, ts)) + ".set")
    _ensure_dir(folder)

    # set.json через mutils.selectionset (если доступен)
    try:
        from mutils import selectionset as mu_sel
        mu_sel.saveSelectionSet(os.path.join(folder, "set.json"), sel, metadata=None)
    except Exception:
        data = {"metadata": {}, "objects": {n: {} for n in sel}}
        with open(os.path.join(folder, "set.json"), "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # превью — один кадр (current time) через mutils.playblast
    try:
        cur = int(cmds.currentTime(q=True) or 1)
    except Exception:
        cur = 1
    try:
        icon_file, _ = _capture_icon_and_sequence(
            camera=ISO1, start=cur, end=cur, base_dir=folder, basename=THUMB_BASENAME
        )
        if icon_file and os.path.exists(icon_file):
            shutil.copyfile(icon_file, os.path.join(folder, "thumbnail.jpg"))
    except Exception:
        pass

    _info(u"<hl>Создан сет</hl>: %s" % os.path.basename(folder))
    return folder

def _pick_or_create_set(library_folder):
    """Возвращает (set_folder, objects). Даёт выбрать/создать при необходимости."""
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

# --------- AnimAssistant → список клипов ------------

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

def _clip_map(clips):
    """Возвращает {name_lower: (start, end)} по данным AnimAssistant."""
    mp = {}
    for it in clips:
        nm = (it.get("name") or "").strip().lower()
        if not nm:
            continue
        try:
            st = int(it.get("start"))
            en = int(it.get("end"))
            mp[nm] = (st, en)
        except Exception:
            pass
    return mp

# --------- Сохранение .anim/.pose (SL формат) ------

def _save_anim_item(objects, dst_dir, start, end, icon_file=None, sequence_dir=None):
    """
    Создаёт SL‑item .anim:
      - animation.ma/mb
      - pose.json
      - thumbnail.jpg (из icon_file)
      - sequence/ (из sequence_dir)
    """
    from mutils import animation as mu_animation
    _ensure_dir(dst_dir)
    start = int(start); end = int(end)
    meta = {"createdBy": "sl_batch_export", "time": [start, end]}
    icon = icon_file if (icon_file and os.path.exists(icon_file)) else ""
    seq  = sequence_dir if (sequence_dir and os.path.isdir(sequence_dir)) else ""

    mu_animation.saveAnim(
        objects=objects,
        path=dst_dir,                 # ПАПКА *.anim
        time=(start, end),
        fileType="mayaAscii",
        metadata=meta,
        iconPath=icon,                # первый кадр jpg
        sequencePath=seq,             # папка с секвенцией
        bakeConnected=False
    )

def _save_pose_item(objects, dst_dir, frame, prefer_camera=ISO7, icon_file=None):
    """
    Создаёт SL‑item .pose:
      - pose.json (значения строго с указанного кадра)
      - thumbnail.jpg (тот же кадр)
    """
    from mutils import pose as mu_pose
    _ensure_dir(dst_dir)
    pose_json = os.path.join(dst_dir, "pose.json")

    # 1) временно ставим нужный кадр и сохраняем значения позы
    cur = None
    try:
        try:
            cur = cmds.currentTime(q=True)
        except Exception:
            cur = None
        if frame is not None:
            cmds.currentTime(int(frame), e=True)
        mu_pose.savePose(pose_json, objects=objects)
    finally:
        if cur is not None:
            try:
                cmds.currentTime(cur, e=True)
            except Exception:
                pass

    # 2) если иконку не дали — делаем одиночный плейбласт этого же кадра
    if not icon_file or not os.path.exists(icon_file):
        try:
            icon_file, _ = _capture_icon_and_sequence(
                camera=prefer_camera,
                start=int(frame),
                end=int(frame),
                base_dir=dst_dir,
                basename=THUMB_BASENAME
            )
        except Exception:
            icon_file = None

    # 3) кладём thumbnail.jpg рядом
    try:
        if icon_file and os.path.exists(icon_file):
            shutil.copyfile(icon_file, os.path.join(dst_dir, "thumbnail.jpg"))
    except Exception:
        pass


# ------------- Сканы существующих и диалог --------

def _scan_existing_items(folder_path, clips):
    """
    Возвращает:
      exists_anim: {safe_name -> path_to_anim_dir}
      exists_pose: {safe_name -> path_to_pose_dir}
    """
    exists_anim = {}
    exists_pose = {}
    all_dirs = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
    low = {d.lower(): d for d in all_dirs}

    for it in clips:
        safe = _nice_name(it.get("name"))
        anim_dirname = (safe + ".anim").lower()
        pose_dirname = (safe + "_pose.pose").lower()
        if anim_dirname in low:
            exists_anim[safe] = os.path.join(folder_path, low[anim_dirname])
        if pose_dirname in low:
            exists_pose[safe] = os.path.join(folder_path, low[pose_dirname])
    return exists_anim, exists_pose

def _ask_overwrite_policy(conflict_anim, missing_anim, conflict_pose, missing_pose):
    """
    Диалог с подробным отчётом:
      - Существующие анимации
      - Отсутствующие анимации (N штуки)
      - Существующие позы
      - Отсутствующие позы (M штуки)
    Возврат: "overwrite_all" | "only_missing" | "cancel"
    """
    from PySide2 import QtWidgets
    parent = _get_sl_main_window()

    lines = []

    if conflict_anim:
        lines.append(u"Существующие анимации:")
        for nm in sorted(conflict_anim)[:15]:
            lines.append(u"• " + _U(nm))
        if len(conflict_anim) > 15:
            lines.append(u"…")
        lines.append(u"")

    if missing_anim:
        lines.append(u"Отсутствуют анимации (%d штуки):" % len(missing_anim))
        for nm in sorted(missing_anim)[:15]:
            lines.append(u"• " + _U(nm))
        if len(missing_anim) > 15:
            lines.append(u"…")
        lines.append(u"")

    if conflict_pose:
        lines.append(u"Существующие позы:")
        for nm in sorted(conflict_pose)[:15]:
            lines.append(u"• " + _U(nm) + u"_pose")
        if len(conflict_pose) > 15:
            lines.append(u"…")
        lines.append(u"")

    if missing_pose:
        lines.append(u"Отсутствуют позы (%d штуки):" % len(missing_pose))
        for nm in sorted(missing_pose)[:15]:
            lines.append(u"• " + _U(nm) + u"_pose")
        if len(missing_pose) > 15:
            lines.append(u"…")

    msg = u"\n".join(lines) if lines else u"Проверка завершена."

    box = QtWidgets.QMessageBox(parent)
    box.setWindowTitle(u"Конфликт имён")
    box.setText(msg)
    box.setInformativeText(u"Перезаписать все конфликтующие элементы?\n"
                           u"Да — перезаписать всё\n"
                           u"Нет — сохранять только недостающие\n"
                           u"Отмена — ничего не делать")
    yes = box.addButton(u"Да (перезаписать всё)", QtWidgets.QMessageBox.YesRole)
    no  = box.addButton(u"Нет (только недостающие)", QtWidgets.QMessageBox.NoRole)
    cancel = box.addButton(u"Отмена", QtWidgets.QMessageBox.RejectRole)
    box.setDefaultButton(no)
    box.exec_()

    clicked = box.clickedButton()
    if clicked is yes:
        return "overwrite_all"
    if clicked is no:
        return "only_missing"
    return "cancel"

# ---------------- Основной батч --------------------

def batch_export(folder_path):
    """
    1) Выбрать/создать .set и получить список контролов.
    2) Проверить существующие .anim и .pose (для спец-клипов), спросить политику перезаписи.
    3) Экспортировать ВСЕ анимации (.anim + sequence).
    4) Отдельным этапом создать .pose для спец-клипов строго по их start-кадрам.
    """
    ensure_cameras()

    set_folder, ctrls = _pick_or_create_set(folder_path)
    if not ctrls:
        return

    clips = _read_anim_list_from_animassistant()
    if not clips:
        _warn(u"Список анимаций пуст (AnimAssistant).")
        return

    # Карта клипов для точных поз: name_lower -> (start, end)
    clip_by_name = _clip_map(clips)

    # Набор спец-поз, которые реально присутствуют в списке клипов
    special_pose_names = set([n.lower() for n in (list(SPECIAL_POSE_IDLE) + list(SPECIAL_POSE_WALK))])
    special_pose_present = set([n for n in special_pose_names if n in clip_by_name])

    # Скан существующих .anim/.pose
    exists_anim, exists_pose = _scan_existing_items(folder_path, clips)

    # Подготовим множества имён для отчёта
    safe_all_anim = set([_nice_name(it.get("name")) for it in clips])
    existing_safe_anim = set(exists_anim.keys())
    missing_anim = sorted(list(safe_all_anim - existing_safe_anim))
    conflict_anim = sorted(list(existing_safe_anim & safe_all_anim))

    # Для поз — только по тем, что есть среди клипов (special_pose_present)
    safe_all_pose = set([_nice_name(n) for n in special_pose_present])
    existing_safe_pose = set([_nice_name(n) for n in exists_pose.keys() if n in special_pose_present])
    missing_pose = sorted(list(safe_all_pose - existing_safe_pose))
    conflict_pose = sorted(list(existing_safe_pose & safe_all_pose))

    # Спросим политику перезаписи с учётом и анимаций, и поз
    policy = "only_missing"
    if conflict_anim or conflict_pose:
        policy = _ask_overwrite_policy(conflict_anim, missing_anim, conflict_pose, missing_pose)
        if policy == "cancel":
            _warn(u"Экспорт отменён пользователем.")
            return

    results = []
    # -------- Этап 1: экспорт всех .anim ----------
    for it in clips:
        name  = it.get("name")
        start = int(it.get("start"))
        end   = int(it.get("end"))
        safe  = _nice_name(name)

        anim_dir = os.path.join(folder_path, safe + ".anim")

        anim_exists = os.path.isdir(anim_dir)
        if anim_exists and policy == "only_missing":
            # пропускаем существующую анимацию
            continue
        if anim_exists and policy == "overwrite_all":
            _safe_rmtree(anim_dir)

        _ensure_dir(anim_dir)

        # Захват превью/секвенции через mutils.playblast (ISO1)
        try:
            icon_file, seq_dir = _capture_icon_and_sequence(
                camera=ISO1, start=start, end=end, base_dir=anim_dir, basename=THUMB_BASENAME
            )
        except Exception:
            icon_file, seq_dir = "", ""

        # Сохранение айтема
        _save_anim_item(ctrls, anim_dir, start, end, icon_file=icon_file, sequence_dir=seq_dir)
        results.append(anim_dir)

    # -------- Этап 2: точные позы по именам --------
    for pose_name in sorted(special_pose_present):
        pose_start, _pose_end = clip_by_name[pose_name]
        safe = _nice_name(pose_name)
        pose_dir = os.path.join(folder_path, safe + "_pose.pose")

        pose_exists = os.path.isdir(pose_dir)
        if pose_exists and policy == "only_missing":
            continue
        if pose_exists and policy == "overwrite_all":
            _safe_rmtree(pose_dir)

        _save_pose_item(ctrls, pose_dir, frame=int(pose_start), prefer_camera=ISO7)

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
