# -*- coding: utf-8 -*-
from __future__ import absolute_import
import re
from maya import cmds
from . import utils  # нужен utils.nice_name

ASSIST_NODE = "AnimAssistant"
ASSIST_ATTRS = ["AnimationClipName", "StartFrame", "EndFrame"]


def _ensure_anim_node():
    if not cmds.objExists(ASSIST_NODE):
        cmds.createNode("geometryVarGroup", n=ASSIST_NODE, ss=True)
    for attr in ASSIST_ATTRS:
        if not cmds.attributeQuery(attr, n=ASSIST_NODE, exists=True):
            cmds.addAttr(ASSIST_NODE, ln=attr, dt="string")
    for attr in ASSIST_ATTRS:
        plug = "%s.%s" % (ASSIST_NODE, attr)
        try:
            val = cmds.getAttr(plug)
        except Exception:
            val = None
        if val is None:
            cmds.setAttr(plug, "", type="string")


class AnimAssistantWriter(object):
    """Записывает план в ноду AnimAssistant в формате: 'NN|safe_name_start-end'."""
    def write_from_plan(self, plan):
        _ensure_anim_node()
        names, starts, ends = [], [], []
        for i, c in enumerate(plan):
            nn = str(i + 1).zfill(2)
            safe = utils.nice_name(c["name"])  # критично: безопасное имя без пробелов
            s = int(c["start"]); e = int(c["end"])
            names.append("%s|%s_%d-%d" % (nn, safe, s, e))
            starts.append(str(s))
            ends.append(str(e))
        cmds.setAttr(ASSIST_NODE + ".AnimationClipName", " ".join(names), type="string")
        cmds.setAttr(ASSIST_NODE + ".StartFrame", " ".join(starts), type="string")
        cmds.setAttr(ASSIST_NODE + ".EndFrame", " ".join(ends), type="string")
        try:
            from maya import mel
            mel.eval("AnimLiUpdate()")
        except Exception:
            pass


class AnimAssistantPlanReader(object):
    """Читает список клипов из ноды AnimAssistant."""
    _name_re = re.compile(r'^(?:\d+\|)?(?P<base>.+?)(?:_[0-9]+-[0-9]+)?$')

    @staticmethod
    def _get(attr):
        plug = "%s.%s" % (ASSIST_NODE, attr)
        try:
            return cmds.getAttr(plug) or ""
        except Exception:
            return ""

    def read_items(self):
        """
        [{"raw": "01|walk_56-100", "name": "walk", "start": 56, "end": 100}, ...]
        """
        names_raw = (self._get("AnimationClipName") or "").split()
        starts    = (self._get("StartFrame") or "").split()
        ends      = (self._get("EndFrame") or "").split()
        n = min(len(names_raw), len(starts), len(ends))
        out = []
        for i in range(n):
            raw = names_raw[i]
            try:
                s = int(round(float(starts[i])))
                e = int(round(float(ends[i])))
            except Exception:
                continue
            m = self._name_re.match((raw or "").strip())
            base = (m.group("base") if m else raw).strip()
            # нормализуем так же, как писали — важно для сопоставления с .anim
            out.append({"raw": raw, "name": utils.nice_name(base), "start": s, "end": e})
        return out
