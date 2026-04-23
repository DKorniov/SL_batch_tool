# -*- coding: utf-8 -*-
from __future__ import absolute_import
from maya import cmds
from . import utils

class AnimLoader(object):
    """
    Тонкая обёртка вокруг Studio Library:
    - грузим .anim в ТЕКУЩИЙ кадр таймлайна (эмуляция режима "Current time")
    - режим вставки по умолчанию: MERGE (чтобы не затирать ранее импортированное)
    """
    def import_anim_at_current_time(self, anim_dir, objects, option="merge", connect=False):
        try:
            from studiolibrarymaya import animitem
        except Exception as e:
            utils.warn(u"Studio Library недоступна (studiolibrarymaya.animitem): %s" % e)
            return False

        objs = objects or (cmds.ls(sl=True) or [])
        if not objs:
            utils.warn(u"Нет объектов для импорта.")
            return False

        try:
            animitem.load(
                anim_dir,
                objects=objs,
                option=option,          # "merge" | "insert" | "replace all" | "delete all keys"
                connect=connect,
                currentTime=True,       # <-- ключ: вставить от текущего кадра
                setTimeRange=False      # не менять диапазон плейбека
            )
            return True
        except Exception as e:
            utils.warn(u"Ошибка animitem.load(%s): %s" % (anim_dir, e))
            return False


class PoseApplier(object):
    def apply_pose_at_frame(self, pose_dir, objects, frame):
        from mutils import Pose
        try:
            cmds.currentTime(int(frame), e=True)
            pose = Pose.fromPath(pose_dir)
            pose.load(objects=objects)
            return True
        except Exception as e:
            utils.warn("Pose apply error @%s: %s" % (frame, e))
            return False
