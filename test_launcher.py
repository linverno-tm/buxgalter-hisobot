# -*- coding: utf-8 -*-
"""Launcher zaxira zanjiri: tarmoq yo'q -> kesh yo'q -> .exe ichidagi nusxa."""
import sys, os, importlib.util
spec = importlib.util.spec_from_file_location('lnch', 'launcher.py')
L = importlib.util.module_from_spec(spec); spec.loader.exec_module(L)

# Tarmoqni ataylab uzamiz
L.DEFAULT_BASE_URL = "https://raw.githubusercontent.com/___yoq___/___yoq___/main"
L.NETWORK_TIMEOUT = 2
os.environ.pop('BH_UPDATE_URL', None)

log = []
print("=== Tarmoq YO'Q, kesh YO'Q -> zaxiradan yuklanishi kerak ===")
try:
    ui, origins = L.boot(lambda s: (log.append(s), print('   ' + s))[1] if False else log.append(s))
    for s in log: print('  ' + s)
    print()
    print('  bh_ui.main mavjud:', hasattr(ui, 'main'))
    print('  manbalar:', origins)
    ok = all(v == 'zaxira' for v in origins.values()) and hasattr(ui, 'main')
    print()
    print('NATIJA:', 'ZAXIRA ZANJIRI ISHLAYDI' if ok else 'MUAMMO')
except Exception as e:
    for s in log: print('  ' + s)
    print('XATO:', e)
    sys.exit(1)

# Endi kesh to'ldirilganini tekshiramiz (zaxiradan yuklansa kesh yozilmaydi)
print()
print("=== Sog'lomlik tekshiruvi ===")
print('  bo\'sh matn       ->', L.sanity_ok('', 'app/ui.py'))
print('  HTML xato sahifa ->', L.sanity_ok('<!DOCTYPE html><h1>404</h1>', 'app/ui.py'))
print('  main() yo\'q ui   ->', L.sanity_ok('def boshqa():\n    pass\n'*5, 'app/ui.py'))
print('  to\'g\'ri modul    ->', L.sanity_ok('def main():\n    return 0\n'+'# '*40, 'app/ui.py'))
