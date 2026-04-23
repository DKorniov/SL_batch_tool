# -*- coding: utf-8 -*-
from __future__ import absolute_import

class Clip(object):
    """Простой контейнер для клипа (Py2-friendly)."""
    __slots__ = ("name", "start", "end")

    def __init__(self, name, start, end):
        self.name = name
        try:
            self.start = int(start)
        except Exception:
            self.start = start
        try:
            self.end = int(end)
        except Exception:
            self.end = end

# Политики перезаписи (строки, чтобы не тянуть enum)
ExportPolicy_overwrite_all = "overwrite_all"
ExportPolicy_only_missing  = "only_missing"

class ExportResult(object):
    """Результат выполнения пайплайна."""
    __slots__ = ("items", "skipped")

    def __init__(self, items=None, skipped=None):
        self.items = items or []
        self.skipped = skipped or []
