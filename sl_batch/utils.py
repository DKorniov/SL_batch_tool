# -*- coding: utf-8 -*-
from __future__ import print_function
import os, re, shutil

try:
    unicode  # Py2
except NameError:
    unicode = str

def u(s):
    if isinstance(s, unicode):
        return s
    try:
        return s.decode("utf-8")
    except Exception:
        try:
            return unicode(s)
        except Exception:
            return u""

def nice_name(s):
    return re.sub(r"[^\w\-]+", "_", (s or "").strip().lower())

def ensure_dir(p):
    if not os.path.exists(p):
        os.makedirs(p)
    return p

def safe_rmtree(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
    except Exception:
        pass

def lowercase_index(names):
    return {n.lower(): n for n in names}

def warn(msg):
    try:
        from maya import cmds
        cmds.warning(u(msg))
    except Exception:
        print("# Warning:", u(msg))

def info(msg):
    try:
        from maya import cmds
        cmds.inViewMessage(amg=u(msg), pos="topCenter", fade=True)
    except Exception:
        print(u(msg))

