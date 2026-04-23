# -*- coding: utf-8 -*-
from __future__ import absolute_import
from maya import cmds
from . import utils, config

class StudioLibraryUi(object):
    def main_window(self):
        try:
            import shiboken2
            from PySide2 import QtWidgets
            import maya.OpenMayaUI as omui
            ptr = omui.MQtUtil.findWindow("StudioLibrary")
            if ptr:
                return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
            for w in QtWidgets.QApplication.topLevelWidgets():
                try:
                    if "Studio Library" in w.windowTitle():
                        return w
                except Exception:
                    pass
        except Exception:
            pass
        return None

    def selected_folder_path(self):
        try:
            import studiolibrary
            lib = studiolibrary.library()
            paths = lib.selectedPaths()
            if paths:
                return paths[0]
        except Exception:
            pass
        sel = cmds.fileDialog2(cap="Select Studio Library Folder", fm=3)
        return sel[0] if sel else None

def _on_click_export(workflow, ui):
    folder = ui.selected_folder_path()
    if not folder: return
    workflow.run(folder)

def _on_click_import(workflow, ui):
    folder = ui.selected_folder_path()
    if not folder: return
    workflow.run(folder)

def install_patch():
    # DI для обоих воркфлоу
    from .cameras import CameraManager
    from .sets import SelectionSetService
    from .animassistant import AnimAssistantReader
    from .playblast import PlayblastService
    from .exporters import AnimationExporter, PoseExporter
    from .scanner import LibraryScanner
    from .conflict_dialog import ConflictResolverDialog
    from .workflow import BatchExportWorkflow

    # Импорт: только то, что реально нужно в новой логике
    from .importers import AnimLoader, PoseApplier
    from .import_workflow import BatchImportWorkflow


    ui = StudioLibraryUi()

    # Экспорт
    export_wf = BatchExportWorkflow(
        cameras=CameraManager(),
        sets=SelectionSetService(),
        anim_reader=AnimAssistantReader(),
        playblast=PlayblastService(),
        anim_exporter=AnimationExporter(),
        pose_exporter=PoseExporter(),
        scanner=LibraryScanner(),
        resolver=ConflictResolverDialog(ui),
        ui=ui
    )

    # Импорт
    from .import_workflow import BatchImportWorkflow

    import_wf = BatchImportWorkflow(
    sets=SelectionSetService(),
    ui=ui
    )


    # --- Добавляем общий контейнер с двумя кнопками ---
    try:
        from PySide2 import QtWidgets
    except Exception:
        utils.warn("PySide2 not available; UI buttons not installed.")
        return

    win = ui.main_window()
    if not win: 
        utils.warn("Studio Library window not found.")
        return

    # Если обе кнопки уже есть — ничего не делаем
    if win.findChild(QtWidgets.QPushButton, "BatchImportButton") and \
       win.findChild(QtWidgets.QPushButton, "BatchExportButton"):
        utils.info(u"Batch Import/Export уже установлены")
        return

    container = QtWidgets.QWidget(win)
    hbox = QtWidgets.QHBoxLayout(container)
    hbox.setContentsMargins(0, 0, 0, 0)
    hbox.setSpacing(4)

    # Import
    btn_imp = QtWidgets.QPushButton(u"Btch_Import", container)
    btn_imp.setObjectName("BatchImportButton")
    btn_imp.setToolTip(utils.u(u"Импорт клипов по длительностям из pose.json + план в AnimAssistant + idle-обрамление"))
    btn_imp.clicked.connect(lambda: _on_click_import(import_wf, ui))
    hbox.addWidget(btn_imp)

    # Export
    btn_exp = QtWidgets.QPushButton(u"Btch_Export", container)
    btn_exp.setObjectName("BatchExportButton")
    btn_exp.setToolTip(utils.u(u"Экспорт клипов из AnimAssistant в выбранную папку SL"))
    btn_exp.clicked.connect(lambda: _on_click_export(export_wf, ui))
    hbox.addWidget(btn_exp)

    # Встраиваем контейнер либо в тулбар, либо в корневой лейаут
    toolbars = win.findChildren(QtWidgets.QToolBar)
    if toolbars:
        toolbars[0].addWidget(container)
    else:
        layout = win.layout() or QtWidgets.QVBoxLayout(win)
        layout.insertWidget(0, container)

    utils.info(u"<hl>Batch Import/Export установлены</hl>")
