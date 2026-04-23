# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from . import maya_api as mx
from . import utils

class PlayblastService(object):
    def capture(self, camera, start, end, base_dir, basename, w, h):
        """
        Возвращает (first_frame_jpg, sequence_dir)
        """
        try:
            from mutils import playblast as mu_playblast
        except Exception:
            utils.warn("mutils.playblast not available")
            return "", ""

        start = int(start); end = int(end)
        utils.ensure_dir(base_dir)
        seq_dir = os.path.join(base_dir, "sequence")
        utils.ensure_dir(seq_dir)
        filename = os.path.join(seq_dir, basename + ".jpg")

        panel = mx.get_any_model_panel()
        if panel:
            try:
                from maya import cmds
                cmds.modelPanel(panel, e=True, cam=camera)
            except Exception:
                pass

        first_frame_path = mu_playblast.playblast(
            filename=filename, modelPanel=panel,
            startFrame=start, endFrame=end,
            width=w, height=h, step=1
        )
        return first_frame_path, os.path.dirname(first_frame_path or seq_dir)
