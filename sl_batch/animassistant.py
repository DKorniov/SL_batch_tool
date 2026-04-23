# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .types import Clip
from . import utils

class AnimAssistantReader(object):
    def read_clips(self):
        try:
            from studiolibrary.widgets.anim_assist_helper import AnimAssistHelper
        except Exception as e:
            utils.warn("No anim_assist_helper: %s" % e)
            return []
        out = []
        try:
            for ap in (AnimAssistHelper.getAnimAssistAnims() or []):
                name = ap.name()
                begin = int(ap.begin())
                end = int(ap.end())
                if name and begin is not None and end is not None:
                    out.append(Clip(name, begin, end))
        except Exception as e:
            utils.warn("AnimAssistant read error: %s" % e)
        return out

    def to_map(self, clips):
        mp = {}
        for c in clips:
            nm = (c.name or "").strip().lower()
            if not nm:
                continue
            try:
                mp[nm] = (int(c.start), int(c.end))
            except Exception:
                pass
        return mp
