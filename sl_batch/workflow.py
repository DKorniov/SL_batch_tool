# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from . import config, utils
from .types import ExportResult, ExportPolicy_only_missing, ExportPolicy_overwrite_all

class BatchExportWorkflow(object):
    def __init__(self, cameras, sets, anim_reader, playblast, anim_exporter,
                 pose_exporter, scanner, resolver, ui):
        self.cameras = cameras
        self.sets = sets
        self.anim_reader = anim_reader
        self.playblast = playblast
        self.anim_exporter = anim_exporter
        self.pose_exporter = pose_exporter
        self.scanner = scanner
        self.resolver = resolver
        self.ui = ui

    def _collect_special_names_present(self, clip_map):
        names = set()
        for n in (list(config.SPECIAL_POSE_IDLE_ALIASES) + list(config.SPECIAL_POSE_WALK_ALIASES)):
            if n in clip_map:
                names.add(n)
        return names

    def _apply_policy_for_dir(self, dir_path, policy):
        exists = os.path.isdir(dir_path)
        if not exists: return "create"
        if policy == ExportPolicy_only_missing: return "skip"
        if policy == ExportPolicy_overwrite_all:
            utils.safe_rmtree(dir_path); return "recreate"
        return "cancel"

    def run(self, folder_path):
        self.cameras.ensure_cameras()

        set_folder, ctrls = self.sets.pick_or_create(folder_path, self.ui)
        if not ctrls:
            return ExportResult()

        clips = self.anim_reader.read_clips()
        if not clips:
            utils.warn(u"Список анимаций пуст (AnimAssistant).")
            return ExportResult()

        clip_map = self.anim_reader.to_map(clips)
        special_present = self._collect_special_names_present(clip_map)

        exists_anim, exists_pose = self.scanner.scan_items(folder_path, clips)

        safe_all_anim = set([utils.nice_name(c.name) for c in clips])
        existing_safe_anim = set(exists_anim.keys())
        missing_anim = sorted(list(safe_all_anim - existing_safe_anim))
        conflict_anim = sorted(list(existing_safe_anim & safe_all_anim))

        safe_all_pose = set([utils.nice_name(n) for n in special_present])
        existing_safe_pose = set([utils.nice_name(n) for n in exists_pose.keys() if n in special_present])
        missing_pose = sorted(list(safe_all_pose - existing_safe_pose))
        conflict_pose = sorted(list(existing_safe_pose & safe_all_pose))

        policy = ExportPolicy_only_missing
        if conflict_anim or conflict_pose:
            policy = self.resolver.ask_policy(conflict_anim, missing_anim, conflict_pose, missing_pose)
            if policy == "cancel":
                utils.warn(u"Экспорт отменён пользователем.")
                return ExportResult()

        results, skipped = [], []

        # Этап 1: экспорт .anim
        for c in clips:
            name, start, end = c.name, int(c.start), int(c.end)
            safe = utils.nice_name(name)
            anim_dir = os.path.join(folder_path, safe + ".anim")

            action = self._apply_policy_for_dir(anim_dir, policy)
            if action == "skip":
                skipped.append(anim_dir); continue
            if action == "cancel":
                return ExportResult(results, skipped)

            utils.ensure_dir(anim_dir)
            try:
                icon, seq = self.playblast.capture(
                    camera=config.ISO1_NAME, start=start, end=end,
                    base_dir=anim_dir, basename=config.THUMB_BASENAME,
                    w=config.THUMB_W, h=config.THUMB_H
                )
            except Exception:
                icon, seq = "", ""

            self.anim_exporter.save_anim(ctrls, anim_dir, start, end, icon_file=icon, sequence_dir=seq)
            results.append(anim_dir)

        # Этап 2: позы (idle/walk алиасы) по старт-кадрам
        for pose_name in sorted(special_present):
            start_frame, _ = clip_map[pose_name]
            safe = utils.nice_name(pose_name)
            pose_dir = os.path.join(folder_path, safe + "_pose.pose")

            action = self._apply_policy_for_dir(pose_dir, policy)
            if action == "skip":
                skipped.append(pose_dir); continue
            if action == "cancel":
                return ExportResult(results, skipped)

            self.pose_exporter.save_pose(ctrls, pose_dir, frame=int(start_frame),
                                         icon_file=None, camera_for_icon=config.ISO7_NAME)

        utils.info(u"<hl>Batch Export</hl>: %d items" % len(results))
        return ExportResult(results, skipped)
