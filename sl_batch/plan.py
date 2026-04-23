# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os, re, json

def _nice_name(s):
    s = re.sub(r'[^0-9a-zA-Z_\-]+', '_', (s or '').strip())
    s = re.sub(r'__+', '_', s).strip('_')
    return s or "item"

class PlanBuilder(object):
    """
    Сканирует папку SL, читает длительности из pose.json в .anim и
    строит раскладку (start/end) от current_start с зазором gap_frames.
    """
    def __init__(self, current_start=1, gap_frames=5, default_duration=50,
                 idle_candidates=("idle", "wait_pose")):
        self.current_start = int(current_start)
        self.gap = int(gap_frames)
        self.default_duration = int(default_duration)
        self.idle_candidates = [s.lower() for s in idle_candidates]

    def _scan_items(self, base_folder):
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

    def _read_duration_from_pose_json(self, anim_dir):
        pj = os.path.join(anim_dir, "pose.json")
        if not os.path.exists(pj):
            return None
        try:
            with open(pj, "r") as f:
                data = json.load(f) or {}
            meta = data.get("metadata") or {}
            s = meta.get("startFrame"); e = meta.get("endFrame")
            if s is None or e is None:
                return None
            s = int(round(float(s))); e = int(round(float(e)))
            if e < s:
                return None
            return e - s + 1
        except Exception:
            return None

    def _group_key(self, name):
        base = (name or '').lower()
        base = re.sub(r'(_in|_out|^in_|^out_|\bto\b)', '', base)
        base = re.sub(r'(\d+)$', '', base)
        base = base.replace('__', '_').strip('_')
        return base

    def _sort_anim_names(self, names):
        def weight(nm):
            low = nm.lower()
            if low in ("idle", "wait_pose"):
                return (0, self._group_key(low), low)
            if low in ("walk", "normal_move"):
                return (1, self._group_key(low), low)
            return (2, self._group_key(low), low)
        return sorted(names, key=weight)

    def build_plan_from_fs(self, base_folder):
        """Возвращает: (plan, poses_dict)"""
        items = self._scan_items(base_folder)
        if not items:
            return [], {}

        poses = {it["name"].lower(): it["path"] for it in items if it["type"] == "pose"}
        anims = [it for it in items if it["type"] == "anim"]
        names = [it["name"] for it in anims]
        names_sorted = self._sort_anim_names(names)
        path_by_name = {it["name"].lower(): it["path"] for it in anims}

        # длительности
        dur_by_name = {}
        for nm in names_sorted:
            low = nm.lower()
            p = path_by_name.get(low)
            dur = self._read_duration_from_pose_json(p)
            if not dur or dur <= 0:
                dur = self.default_duration
            dur_by_name[low] = int(dur)

        # план
        plan, current = [], int(self.current_start)
        for nm in names_sorted:
            low = nm.lower()
            dur = int(dur_by_name[low])
            start = current
            end = start + dur - 1
            plan.append({"name": nm, "path": path_by_name[low], "dur": dur, "start": start, "end": end})
            current = end + 1 + self.gap

        return plan, poses
