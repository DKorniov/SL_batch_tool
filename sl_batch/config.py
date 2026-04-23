# -*- coding: utf-8 -*-

# Камеры
ISO1_NAME = "isometric_1"
ISO7_NAME = "isometric_7"

ISO1_PARAMS = dict(tx=25, ty=28, tz=35, rx=-20, ry=38, rz=0, focal=40.0)
ISO7_PARAMS = dict(tx=22, ty=40, tz=22, rx=-45, ry=45, rz=0, focal=35.0)

# Спец-позы
SPECIAL_POSE_IDLE_ALIASES = {"idle", "wait_pose", "idle_pose"}
SPECIAL_POSE_WALK_ALIASES = {"walk", "normal_move"}

# Превью
THUMB_BASENAME = "thumbnail"
THUMB_W, THUMB_H = 480, 270

# Политика перезаписи по умолчанию
DEFAULT_EXPORT_POLICY = "only_missing"
