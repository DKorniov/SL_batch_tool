# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os, shutil
from . import utils

class AnimationExporter(object):
    def save_anim(self, objects, dst_dir, start, end, icon_file, sequence_dir):
        from mutils import animation as mu_animation
        utils.ensure_dir(dst_dir)
        meta = {"createdBy": "sl_batch_export", "time": [int(start), int(end)]}
        icon = icon_file if (icon_file and os.path.exists(icon_file)) else ""
        seq  = sequence_dir if (sequence_dir and os.path.isdir(sequence_dir)) else ""
        mu_animation.saveAnim(
            objects=objects, path=dst_dir,
            time=(int(start), int(end)),
            fileType="mayaAscii",
            metadata=meta, iconPath=icon, sequencePath=seq,
            bakeConnected=False
        )

class PoseExporter(object):
    def save_pose(self, objects, dst_dir, frame, icon_file=None, camera_for_icon="isometric_7"):
        from mutils import pose as mu_pose
        from . import maya_api as mx
        from . import config
        utils.ensure_dir(dst_dir)
        pose_json = os.path.join(dst_dir, "pose.json")

        cur = None
        try:
            cur = mx.current_time()
            mx.set_time(int(frame))
            mu_pose.savePose(pose_json, objects=objects)
        finally:
            if cur is not None:
                mx.set_time(cur)

        if not icon_file:
            try:
                from .playblast import PlayblastService
                ps = PlayblastService()
                icon_file, _ = ps.capture(
                    camera=camera_for_icon, start=int(frame), end=int(frame),
                    base_dir=dst_dir, basename=config.THUMB_BASENAME,
                    w=config.THUMB_W, h=config.THUMB_H
                )
            except Exception:
                icon_file = None

        try:
            if icon_file and os.path.exists(icon_file):
                shutil.copyfile(icon_file, os.path.join(dst_dir, "thumbnail.jpg"))
        except Exception:
            pass
