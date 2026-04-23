# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from maya import cmds
from . import utils
from .sets import SelectionSetService
from .animassistant_io import AnimAssistantPlanReader, AnimAssistantWriter
from .plan import PlanBuilder
from .importers import AnimLoader, PoseApplier

class ImportResult(object):
    __slots__ = ("imported", "placed_idle", "skipped")
    def __init__(self, imported=0, placed_idle=0, skipped=None):
        self.imported = int(imported)
        self.placed_idle = int(placed_idle)
        self.skipped = skipped or []


class BatchImportWorkflow(object):
    def __init__(self, sets=None, ui=None):
        self.sets = sets or SelectionSetService()
        self.ui = ui
        self.loader = AnimLoader()
        self.pose = PoseApplier()

    @staticmethod
    def _keyize(nm):
        import re
        s = re.sub(r'[^0-9a-zA-Z_\-]+', '_', (nm or '').strip().lower())
        s = re.sub(r'__+', '_', s).strip('_')
        return s or "item"

    def _scan_fs(self, base_folder):
        anim_by_key, poses_by_key = {}, {}
        for name in os.listdir(base_folder):
            full = os.path.join(base_folder, name)
            if not os.path.isdir(full):
                continue
            low = name.lower()
            if low.endswith(".anim"):
                anim_by_key[self._keyize(name[:-5])] = full
            elif low.endswith(".pose"):
                poses_by_key[self._keyize(name[:-5])] = full
        return anim_by_key, poses_by_key

    def _resolve_anim_path(self, clip_name, anim_by_key):
        return anim_by_key.get(self._keyize(clip_name))

    def _find_idle_pose(self, poses_by_key):
        for cand in ("idle", "wait_pose"):
            p = poses_by_key.get(self._keyize(cand))
            if p and os.path.isdir(p):
                return p
        return None

    def run(self, base_folder):
        if not base_folder or not os.path.isdir(base_folder):
            raise RuntimeError("Invalid folder for import")

        # 0) контрол-сет
        set_folder, objects = self.sets.pick_or_create(base_folder, self.ui)
        if not set_folder or not objects:
            utils.warn(u"Не удалось получить контролы для импорта.")
            return ImportResult()

        utils.info(u"Контролов в сете: %d" % len(objects))

        # 1) читаем AnimAssistant; если пуст — строим план из ФС и пишем в ноду
        reader = AnimAssistantPlanReader()
        items = reader.read_items()
        if not items:
            utils.info(u"AnimAssistant пуст — строю план из папки и записываю в ноду…")
            plan, _poses = PlanBuilder(
                current_start=1, gap_frames=5, default_duration=50,
                idle_candidates=("idle", "wait_pose")
            ).build_plan_from_fs(base_folder)
            if not plan:
                utils.warn(u"В папке нет .anim/.pose — импорт отменён.")
                return ImportResult()
            AnimAssistantWriter().write_from_plan(plan)
            items = reader.read_items()
            if not items:
                utils.warn(u"Не удалось прочитать список из AnimAssistant после записи — импорт отменён.")
                return ImportResult()

        # 2) скан ФС
        anim_by_key, poses_by_key = self._scan_fs(base_folder)

        # 3) импорт через Studio Library: currentTime=True, option="merge"
        #    (чтобы клипы накапливались, а не затирали друг друга)
        try:
            prev_auto = cmds.autoKeyframe(q=True, state=True)
            cmds.autoKeyframe(state=False)
        except Exception:
            prev_auto = None

        imported = 0
        skipped = []

        for it in items:
            anim_path = self._resolve_anim_path(it["name"], anim_by_key)
            if not anim_path:
                utils.warn(u"Не найден .anim для: %s" % it["name"])
                skipped.append(it["name"])
                continue

            # ключевой шаг — поставить курсор на StartFrame клипа
            try:
                cmds.currentTime(int(it["start"]), e=True)
            except Exception:
                pass

            ok = self.loader.import_anim_at_current_time(
                anim_dir=anim_path,
                objects=objects,
                option="merge",      # можно заменить на "insert", если нужно «только в пустые места»
                connect=False
            )
            if ok:
                imported += 1
            else:
                skipped.append(it["name"])

        if prev_auto is not None:
            try:
                cmds.autoKeyframe(state=prev_auto)
            except Exception:
                pass

        # 4) idle-обрамление после всего
        idle_pose = self._find_idle_pose(poses_by_key)
        placed_idle = 0
        if idle_pose:
            try:
                from mutils import Pose
                pose = Pose.fromPath(idle_pose)
                seen = set()
                for it in items:
                    for fr in (it["start"] - 1, it["end"] + 1):
                        if fr < 0 or fr in seen:
                            continue
                        try:
                            cmds.currentTime(int(fr), e=True)
                            pose.load(objects=objects)
                            seen.add(fr)
                            placed_idle += 1
                        except Exception:
                            pass
                utils.info(u"Idle поз установлено: %d" % placed_idle)
            except Exception:
                utils.info(u"Idle-поза найдена, но mutils.Pose недоступен — обрамление пропущено.")
        else:
            utils.info(u"Idle-поза не найдена — обрамление пропущено.")

        utils.info(u"Batch Import: импортировано анимаций: %d" % imported)
        return ImportResult(imported=imported, placed_idle=placed_idle, skipped=skipped)

