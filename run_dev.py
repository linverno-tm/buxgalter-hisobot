# -*- coding: utf-8 -*-
"""Ishlab chiqish rejimida ishga tushirish (GitHub'siz, to'g'ridan-to'g'ri app/ dan)."""
import sys, os, importlib
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app'))
for n, m in [('bh_config','config'),('bh_db','db'),('bh_parsers','parsers'),
             ('bh_matching','matching'),('bh_fifo','fifo'),('bh_report','report'),
             ('bh_ui','ui')]:
    sys.modules[n] = importlib.import_module(m)
import bh_ui
sys.exit(bh_ui.main({'launcher_version': 'dev', 'base_url': 'lokal (app/)',
                     'origins': {'bh_ui': 'lokal'}}))
