# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os, json, time, shutil
from . import utils, config, maya_api as mx

def _capture_icon_for_set(folder):
    # один кадр текущего времени, ISO1, кладём thumbnail.jpg
    try:
        from .playblast import PlayblastService
        ps = PlayblastService()
        cur = mx.current_time()
        icon, _ = ps.capture(
            camera=config.ISO1_NAME, start=cur, end=cur,
            base_dir=folder, basename=config.THUMB_BASENAME,
            w=config.THUMB_W, h=config.THUMB_H
        )
        if icon and os.path.exists(icon):
            shutil.copyfile(icon, os.path.join(folder, "thumbnail.jpg"))
    except Exception:
        pass

class SelectionSetService(object):
    def find_set_folders(self, library_folder):
        out = []
        for name in os.listdir(library_folder):
            p = os.path.join(library_folder, name)
            if os.path.isdir(p) and name.lower().endswith(".set") and \
               os.path.exists(os.path.join(p, "set.json")):
                out.append(p)
        return sorted(out)

    def read_objects(self, set_folder):
        path = os.path.join(set_folder, "set.json")
        try:
            with open(path, "r") as f:
                data = json.load(f) or {}
            objs = data.get("objects") or {}
            return [str(k) for k in objs.keys()]
        except Exception as e:
            utils.warn("Cannot read set.json: %s" % e)
            return []

    def _create_set_from_selection(self, library_folder, default_name="controls"):
        sel = mx.list_selection()
        if not sel:
            utils.warn(u"Выделите контролы в сцене и повторите.")
            return None
        ts = time.strftime("%Y%m%d_%H%M%S")
        folder = os.path.join(library_folder, utils.nice_name("%s_%s" % (default_name, ts)) + ".set")
        utils.ensure_dir(folder)
        # set.json через mutils.selectionset, с фоллбэком
        try:
            from mutils import selectionset as mu_sel
            mu_sel.saveSelectionSet(os.path.join(folder, "set.json"), sel, metadata=None)
        except Exception:
            data = {"metadata": {}, "objects": {n: {} for n in sel}}
            with open(os.path.join(folder, "set.json"), "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        _capture_icon_for_set(folder)
        utils.info(u"<hl>Создан сет</hl>: %s" % os.path.basename(folder))
        return folder

    def _prompt_choose_set(self, parent, items):
        try:
            from PySide2 import QtWidgets
            labels = [os.path.basename(p) for p in items]
            item, ok = QtWidgets.QInputDialog.getItem(parent, u"Выбор набора контролов",
                                                      u"Найдено несколько .set — выберите:",
                                                      labels, 0, False)
            if ok and item in labels:
                return items[labels.index(item)]
        except Exception:
            pass
        return None

    def pick_or_create(self, library_folder, ui):
        sets = self.find_set_folders(library_folder)
        chosen = None
        if not sets:
            chosen = self._create_set_from_selection(library_folder)
            if not chosen:
                return None, []
        elif len(sets) == 1:
            chosen = sets[0]
        else:
            chosen = self._prompt_choose_set(ui.main_window(), sets)
            if not chosen:
                utils.warn(u"Сет не выбран.")
                return None, []
        objects = self.read_objects(chosen)
        if not objects:
            utils.warn(u"В выбранном сете нет объектов.")
        return chosen, objects
