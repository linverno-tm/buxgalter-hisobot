# -*- coding: utf-8 -*-
"""
manifest.json ni qayta yozadi (har modulning sha256 i bilan).

HAR `git push` DAN OLDIN ishga tushiring:

    python make_manifest.py
    git add -A && git commit -m "..." && git push

sha256 nima uchun kerak:
  - yarim yuklangan fayl ishga tushmaydi
  - o'rtadagi kimdir kodni almashtirsa, launcher rad etadi va keshdagi
    ishonchli nusxaga qaytadi
"""

import os
import io
import json
import hashlib
import datetime

# EXEC TARTIBI. Bog'liqlik tartibi: keyingisi oldingisini import qiladi.
MODULES = [
    ("bh_config", "app/config.py"),
    ("bh_db", "app/db.py"),
    ("bh_parsers", "app/parsers.py"),
    ("bh_matching", "app/matching.py"),
    ("bh_fifo", "app/fifo.py"),
    ("bh_report", "app/report.py"),
    ("bh_ui", "app/ui.py"),
]

HERE = os.path.dirname(os.path.abspath(__file__))


def core_version():
    """app/config.py dagi VERSION ni o'qiydi."""
    p = os.path.join(HERE, "app", "config.py")
    for line in io.open(p, encoding="utf-8"):
        if line.startswith("VERSION"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "0"


def main():
    mods = []
    total = 0
    print("Modullar:")
    for name, rel in MODULES:
        p = os.path.join(HERE, rel.replace("/", os.sep))
        if not os.path.isfile(p):
            raise SystemExit("TOPILMADI: %s" % rel)
        raw = open(p, "rb").read()

        # Sog'lomlik tekshiruvi - buzuq fayl push bo'lib ketmasin
        txt = raw.decode("utf-8")
        compile(txt, rel, "exec")
        if rel.endswith("ui.py") and "def main" not in txt:
            raise SystemExit("XATO: %s ichida main() yo'q" % rel)

        sha = hashlib.sha256(raw).hexdigest()
        mods.append({"name": name, "path": rel, "sha256": sha,
                     "bytes": len(raw)})
        total += len(raw)
        print("  %-14s %-18s %8d bayt  %s" % (name, rel, len(raw), sha[:16]))

    man = {
        "version": core_version(),
        "generated": datetime.datetime.now().isoformat(timespec="seconds"),
        "modules": mods,
    }
    out = os.path.join(HERE, "manifest.json")
    with io.open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(man, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print("\nmanifest.json yozildi.  versiya=%s  jami=%.1f KB"
          % (man["version"], total / 1024.0))
    print("Endi: git add -A && git commit -m \"...\" && git push")


if __name__ == "__main__":
    main()
