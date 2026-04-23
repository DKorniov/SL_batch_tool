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
        import os
        from maya import cmds
        from . import utils

        # Попытка 1: Актуальное API вашей версии Studio Library (через Singleton окна)
        try:
            window = None
            # Сначала пробуем специфичный для Maya класс
            try:
                from studiolibrarymaya import mayalibrarywindow
                window = mayalibrarywindow.MayaLibraryWindow.instance()
            except ImportError:
                pass
            
            # Если не вышло, пробуем базовый класс
            if not window:
                try:
                    from studiolibrary import librarywindow
                    window = librarywindow.LibraryWindow.instance()
                except ImportError:
                    pass

            # Если окно найдено, берем путь так же, как это делает сама Studio Library
            if window:
                path = window.selectedFolderPath()
                if not path:
                    path = window.path()
                    
                if path and os.path.isdir(path):
                    utils.info(u"Найден путь через API (LibraryWindow.instance): " + path)
                    return path
        except Exception as e:
            utils.warn(u"Ошибка API Studio Library (instance): " + str(e))

        # Попытка 2: Стандартное API (на случай, если скрипт запустят на другой версии SL)
        try:
            import studiolibrary
            lib = studiolibrary.library()
            if lib:
                paths = lib.selectedPaths()
                if paths and os.path.isdir(paths[0]):
                    utils.info(u"Найден путь через API (studiolibrary.library): " + paths[0])
                    return paths[0]
        except Exception:
            pass

        # Попытка 3: Парсинг интерфейса (Qt Fallback)
        try:
            from PySide2 import QtWidgets
            win = self.main_window()
            if win:
                # Ищем адресную строку (обычно QLineEdit)
                line_edits = win.findChildren(QtWidgets.QLineEdit)
                for le in line_edits:
                    text = le.text()
                    if text and os.path.isdir(text):
                        utils.info(u"Найден путь через PySide (QLineEdit): " + text)
                        return text
        except Exception as e:
            utils.warn(u"Ошибка поиска пути через PySide: " + str(e))

        # Попытка 4: Фолбэк на ручной выбор (cmds.fileDialog2)
        utils.warn(u"Не удалось автоматически определить папку Studio Library. Выберите вручную.")
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
    import_wf = BatchImportWorkflow(
        sets=SelectionSetService(),
        ui=ui
    )

    try:
        from PySide2 import QtWidgets
    except Exception:
        utils.warn("PySide2 not available; UI buttons not installed.")
        return

    win = ui.main_window()
    if not win: 
        utils.warn("Studio Library window not found.")
        return

    # --- УДАЛЕНИЕ СТАРОГО UI (ВМЕСТО БЛОКИРОВКИ) ---
    old_container = win.findChild(QtWidgets.QWidget, "SLBatchButtonsContainer")
    if old_container:
        old_container.setParent(None)
        old_container.deleteLater()
    
    # На всякий случай удаляем осиротевшие кнопки, если они остались от старых версий
    for btn_name in ["BatchImportButton", "BatchExportButton"]:
        old_btn = win.findChild(QtWidgets.QPushButton, btn_name)
        if old_btn:
            old_btn.setParent(None)
            old_btn.deleteLater()

    # --- СОЗДАНИЕ НОВОГО UI ---
    container = QtWidgets.QWidget(win)
    container.setObjectName("SLBatchButtonsContainer") # Даем имя контейнеру, чтобы легко его находить и удалять
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

    utils.info(u"<hl>Batch Import/Export успешно обновлены и установлены</hl>")
