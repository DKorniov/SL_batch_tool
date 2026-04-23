# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import config
from . import maya_api as mx

class CameraManager(object):
    def ensure_cameras(self):
        p1 = config.ISO1_PARAMS
        p7 = config.ISO7_PARAMS
        mx.ensure_camera(config.ISO1_NAME, **p1)
        mx.ensure_camera(config.ISO7_NAME, **p7)
