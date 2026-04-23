# -*- coding: utf-8 -*-
from __future__ import absolute_import
import os
from . import utils

class LibraryScanner(object):
    def scan_items(self, folder_path, clips):
        exists_anim, exists_pose = {}, {}
        all_dirs = [d for d in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, d))]
        low = utils.lowercase_index(all_dirs)
        for c in clips:
            safe = utils.nice_name(c.name)
            anim_dirname = (safe + ".anim").lower()
            pose_dirname = (safe + "_pose.pose").lower()
            if anim_dirname in low:
                exists_anim[safe] = os.path.join(folder_path, low[anim_dirname])
            if pose_dirname in low:
                exists_pose[safe] = os.path.join(folder_path, low[pose_dirname])
        return exists_anim, exists_pose
