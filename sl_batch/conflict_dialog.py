# -*- coding: utf-8 -*-
from __future__ import absolute_import
from . import utils
from .types import ExportPolicy_only_missing, ExportPolicy_overwrite_all

class ConflictResolverDialog(object):
    def __init__(self, ui):
        self.ui = ui

    def ask_policy(self, conflict_anim, missing_anim, conflict_pose, missing_pose):
        # если конфликтов нет — по умолчанию "only_missing"
        if not (conflict_anim or conflict_pose):
            return ExportPolicy_only_missing

        try:
            from PySide2 import QtWidgets
        except Exception:
            return ExportPolicy_only_missing

        lines = []
        if conflict_anim:
            lines.append(u"Существующие анимации:")
            lines.extend([u"• " + utils.u(nm) for nm in sorted(conflict_anim)[:15]])
            if len(conflict_anim) > 15: lines.append(u"…")
            lines.append(u"")
        if missing_anim:
            lines.append(u"Отсутствуют анимации (%d):" % len(missing_anim))
            lines.extend([u"• " + utils.u(nm) for nm in sorted(missing_anim)[:15]])
            if len(missing_anim) > 15: lines.append(u"…")
            lines.append(u"")
        if conflict_pose:
            lines.append(u"Существующие позы:")
            lines.extend([u"• " + utils.u(nm) + u"_pose" for nm in sorted(conflict_pose)[:15]])
            if len(conflict_pose) > 15: lines.append(u"…")
            lines.append(u"")
        if missing_pose:
            lines.append(u"Отсутствуют позы (%d):" % len(missing_pose))
            lines.extend([u"• " + utils.u(nm) + u"_pose" for nm in sorted(missing_pose)[:15]])
            if len(missing_pose) > 15: lines.append(u"…")

        msg = u"\n".join(lines) if lines else u"Проверка завершена."

        parent = self.ui.main_window()
        box = QtWidgets.QMessageBox(parent)
        box.setWindowTitle(u"Конфликт имён")
        box.setText(msg)
        box.setInformativeText(u"Перезаписать все конфликтующие элементы?\n"
                               u"Да — перезаписать всё\n"
                               u"Нет — сохранять только недостающие\n"
                               u"Отмена — ничего не делать")
        yes = box.addButton(u"Да (перезаписать всё)", QtWidgets.QMessageBox.YesRole)
        no  = box.addButton(u"Нет (только недостающие)", QtWidgets.QMessageBox.NoRole)
        cancel = box.addButton(u"Отмена", QtWidgets.QMessageBox.RejectRole)
        box.setDefaultButton(no)
        box.exec_()

        clicked = box.clickedButton()
        if clicked is yes:
            return ExportPolicy_overwrite_all
        if clicked is no:
            return ExportPolicy_only_missing
        return "cancel"
