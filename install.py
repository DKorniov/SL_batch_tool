# -*- coding: utf-8 -*-
import os
import sys
import maya.cmds as cmds
import maya.mel as mel

def onMayaDroppedPythonFile(*args):
    """Эта функция автоматически вызывается Maya при перетаскивании файла во Viewport."""
    # Получаем путь к папке, где лежит этот install.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    current_dir = current_dir.replace("\\", "/") # Унифицируем слеши для Maya
    
    # Формируем код, который будет выполняться при нажатии на кнопку
    button_command = """import sys, traceback
from maya import cmds

BASE_PATH = r"{path}"
if BASE_PATH not in sys.path:
    sys.path.append(BASE_PATH)

# --- ЖЕСТКАЯ ОЧИСТКА КЭША (Hard Reload) ---
# Удаляем все модули пакета sl_batch из памяти, заставляя Maya прочитать свежие файлы с диска
for mod_name in list(sys.modules.keys()):
    if mod_name.startswith('sl_batch'):
        del sys.modules[mod_name]

try:
    # Загружаем скрипт с нуля
    import sl_batch.sl_ui as sl_ui
    sl_ui.install_patch()
except Exception as e:
    cmds.warning(u"Не удалось установить Batch Import/Export: %s" % e)
    traceback.print_exc()
""".format(path=current_dir)

    # Получаем текущую активную полку
    current_shelf = mel.eval("tabLayout -q -selectTab $gShelfTopLevel")
    
    # Создаем кнопку
    cmds.setParent(current_shelf)
    cmds.shelfButton(
        command=button_command,
        annotation="SL Batch Tool: Установка кнопок в Studio Library",
        sourceType="Python",
        imageOverlayLabel="SL_B",
        image="pythonFamily.png", # Стандартная иконка, можно заменить на свою
        style="iconOnly"
    )
    
    cmds.inViewMessage(amg="<hl>SL Batch Tool</hl> скрипт для полки успешно создан!", pos="topCenter", fade=True)
    print("\n[SL Batch Tool] Кнопка успешно добавлена на полку: {}".format(current_shelf))