# -*- coding: utf-8 -*-
"""
Buxgalteriya hisoboti generatori - LAUNCHER

Bu fayl .exe ichiga kompilyatsiya qilinadi va DEYARLI HECH QACHON o'zgarmaydi.
Butun mantiq GitHub'dagi app/ modullarida turadi va har ishga tushganda
yangilanadi.

Yuklash zanjiri:
  1. GitHub raw -> manifest.json  (modullar ro'yxati + sha256)
  2. Har bir modul yuklanadi, sha256 tekshiriladi, keshga yoziladi
  3. exec() bilan modulga aylantiriladi (bog'liqlik tartibida)
  4. bh_ui.main() chaqiriladi
  5. Xato bo'lsa -> kesh -> .exe ichidagi zaxira nusxa

MUHIM: bu fayl faqat standart kutubxonani import qiladi.
Qolgan hamma narsa exec() qilingan modullar ichida.
"""

import os
import sys
import json
import types
import hashlib
import traceback

APP_NAME = "BuxgalterHisobot"
LAUNCHER_VERSION = "1.0.0"

# ---------------------------------------------------------------------------
# Yangilanish manzili.
# O'zgartirish uchun .exe yonida `update_url.txt` fayl yaratib, unga
# to'liq raw-base URL yozish kifoya (qayta kompilyatsiya shart emas).
# ---------------------------------------------------------------------------
DEFAULT_BASE_URL = "https://raw.githubusercontent.com/linverno-tm/buxgalter-hisobot/main"

NETWORK_TIMEOUT = 6  # soniya

# Modullar EXEC TARTIBI. manifest.json bo'lmasa shu ro'yxat ishlatiladi.
FALLBACK_MODULES = [
    ("bh_config", "app/config.py"),
    ("bh_db", "app/db.py"),
    ("bh_parsers", "app/parsers.py"),
    ("bh_matching", "app/matching.py"),
    ("bh_fifo", "app/fifo.py"),
    ("bh_report", "app/report.py"),
    ("bh_ui", "app/ui.py"),
]


# ---------------------------------------------------------------------------
# Yo'llar
# ---------------------------------------------------------------------------
def cache_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME, "code")
    os.makedirs(d, exist_ok=True)
    return d


def data_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME)
    os.makedirs(d, exist_ok=True)
    return d


def bundled_dir():
    """PyInstaller --add-data bilan o'ralgan zaxira nusxa joyi."""
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))


def exe_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def base_url():
    override = os.path.join(exe_dir(), "update_url.txt")
    try:
        if os.path.isfile(override):
            u = open(override, "r", encoding="utf-8").read().strip()
            if u.startswith("http"):
                return u.rstrip("/")
    except Exception:
        pass
    env = os.environ.get("BH_UPDATE_URL", "").strip()
    if env.startswith("http"):
        return env.rstrip("/")
    return DEFAULT_BASE_URL.rstrip("/")


# ---------------------------------------------------------------------------
# Tarmoq
# ---------------------------------------------------------------------------
def http_get(url, timeout=NETWORK_TIMEOUT):
    import urllib.request

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "%s-launcher/%s" % (APP_NAME, LAUNCHER_VERSION),
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def sha256_hex(data):
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Manba olish: tarmoq -> kesh -> zaxira
# ---------------------------------------------------------------------------
def sanity_ok(text, rel_path):
    """Yarim yuklangan yoki HTML xato sahifasi ishga tushmasin."""
    if not text or len(text) < 40:
        return False
    low = text.lstrip()[:200].lower()
    if low.startswith("<!doctype") or low.startswith("<html"):
        return False
    if "404: not found" in text[:200].lower():
        return False
    # har bir modul kamida bitta def yoki class'ga ega bo'lishi kerak
    if "def " not in text and "class " not in text:
        return False
    if rel_path.endswith("ui.py") and "def main" not in text:
        return False
    return True


def fetch_source(rel_path, expected_sha, log):
    """(source_text, origin) qaytaradi. Hech narsa topilmasa (None, sabab)."""
    cache_path = os.path.join(cache_dir(), rel_path.replace("/", "__"))

    # 1) Tarmoq
    try:
        raw = http_get("%s/%s" % (base_url(), rel_path))
        got = sha256_hex(raw)
        if expected_sha and got != expected_sha:
            log("  ! %s: sha256 mos kelmadi, rad etildi" % rel_path)
        else:
            text = raw.decode("utf-8")
            if sanity_ok(text, rel_path):
                try:
                    with open(cache_path, "w", encoding="utf-8", newline="") as f:
                        f.write(text)
                except Exception:
                    pass
                return text, "tarmoq"
            log("  ! %s: mazmun tekshiruvidan o'tmadi" % rel_path)
    except Exception as e:
        log("  . %s: tarmoq yo'q (%s)" % (rel_path, type(e).__name__))

    # 2) Kesh
    try:
        if os.path.isfile(cache_path):
            text = open(cache_path, "r", encoding="utf-8").read()
            if sanity_ok(text, rel_path):
                return text, "kesh"
    except Exception:
        pass

    # 3) Zaxira (.exe ichidagi)
    for cand in (
        os.path.join(bundled_dir(), rel_path.replace("/", os.sep)),
        os.path.join(bundled_dir(), os.path.basename(rel_path)),
    ):
        try:
            if os.path.isfile(cand):
                text = open(cand, "r", encoding="utf-8").read()
                if sanity_ok(text, rel_path):
                    return text, "zaxira"
        except Exception:
            pass

    return None, "topilmadi"


def load_manifest(log):
    try:
        raw = http_get("%s/manifest.json" % base_url())
        m = json.loads(raw.decode("utf-8"))
        mods = [(x["name"], x["path"], x.get("sha256")) for x in m["modules"]]
        try:
            with open(os.path.join(cache_dir(), "manifest.json"), "wb") as f:
                f.write(raw)
        except Exception:
            pass
        log("  manifest: tarmoqdan, versiya %s" % m.get("version", "?"))
        return mods
    except Exception as e:
        log("  manifest: tarmoqdan olinmadi (%s)" % type(e).__name__)

    try:
        p = os.path.join(cache_dir(), "manifest.json")
        if os.path.isfile(p):
            m = json.loads(open(p, "r", encoding="utf-8").read())
            log("  manifest: keshdan")
            return [(x["name"], x["path"], x.get("sha256")) for x in m["modules"]]
    except Exception:
        pass

    try:
        p = os.path.join(bundled_dir(), "manifest.json")
        if os.path.isfile(p):
            m = json.loads(open(p, "r", encoding="utf-8").read())
            log("  manifest: zaxiradan")
            return [(x["name"], x["path"], x.get("sha256")) for x in m["modules"]]
    except Exception:
        pass

    log("  manifest: qat'iy ro'yxat ishlatildi")
    return [(n, p, None) for n, p in FALLBACK_MODULES]


# ---------------------------------------------------------------------------
# Yuklash va ishga tushirish
# ---------------------------------------------------------------------------
def boot(log):
    mods = load_manifest(log)
    origins = {}
    loaded = []

    for item in mods:
        name, rel, sha = (item + (None,))[:3] if len(item) == 2 else item
        text, origin = fetch_source(rel, sha, log)
        if text is None:
            raise RuntimeError(
                "'%s' moduli topilmadi (%s).\n\n"
                "Internetni tekshiring yoki dasturni qayta o'rnating." % (rel, origin)
            )
        origins[name] = origin
        mod = types.ModuleType(name)
        mod.__file__ = rel
        mod.__package__ = ""
        # Modullar bir-birini oddiy `import bh_db` orqali topishi uchun
        sys.modules[name] = mod
        try:
            code = compile(text, "<%s>" % rel, "exec")
            exec(code, mod.__dict__)
        except Exception:
            sys.modules.pop(name, None)
            raise RuntimeError(
                "'%s' modulida xato:\n\n%s" % (rel, traceback.format_exc(limit=6))
            )
        loaded.append(name)
        log("  + %-14s <- %s" % (name, origin))

    ui = sys.modules.get("bh_ui")
    if ui is None or not hasattr(ui, "main"):
        raise RuntimeError("bh_ui.main() topilmadi.")

    cfg = sys.modules.get("bh_config")
    ver = getattr(cfg, "VERSION", "?") if cfg else "?"
    log("  yuklandi: %d modul, core versiya %s" % (len(loaded), ver))

    return ui, origins


def show_fatal(msg):
    sys.stderr.write(msg + "\n")
    try:
        import tkinter as tk
        from tkinter import scrolledtext

        r = tk.Tk()
        r.title("Ishga tushirib bo'lmadi - %s" % APP_NAME)
        r.geometry("760x420")
        r.minsize(420, 260)

        bar = tk.Frame(r, padx=12, pady=10)
        bar.pack(side="bottom", fill="x")
        tk.Button(bar, text="Yopish", width=14, command=r.destroy).pack(side="right")

        tk.Label(
            r, text="Dastur ishga tushmadi", font=("Segoe UI", 13, "bold"),
            anchor="w", padx=12, pady=(12, 4),
        ).pack(fill="x")

        t = scrolledtext.ScrolledText(r, wrap="word", font=("Consolas", 9))
        t.pack(fill="both", expand=True, padx=12, pady=(0, 8))
        t.insert("1.0", msg)
        t.configure(state="disabled")
        r.mainloop()
    except Exception:
        pass


def main():
    lines = []

    def log(s):
        lines.append(s)
        try:
            sys.stderr.write(s + "\n")
        except Exception:
            pass

    log("%s launcher %s" % (APP_NAME, LAUNCHER_VERSION))
    log("  manba: %s" % base_url())

    try:
        ui, origins = boot(log)
    except Exception as e:
        show_fatal("%s\n\n--- jurnal ---\n%s" % (e, "\n".join(lines)))
        return 1

    try:
        ui.main(
            launcher_info={
                "launcher_version": LAUNCHER_VERSION,
                "base_url": base_url(),
                "origins": origins,
                "data_dir": data_dir(),
                "cache_dir": cache_dir(),
                "boot_log": lines,
            }
        )
    except TypeError:
        # Eski core.py argumentsiz main() bo'lsa
        ui.main()
    except Exception:
        show_fatal(
            "Dastur ishlayotganda xato:\n\n%s\n\n--- jurnal ---\n%s"
            % (traceback.format_exc(), "\n".join(lines))
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
