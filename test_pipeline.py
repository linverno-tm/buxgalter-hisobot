# -*- coding: utf-8 -*-
import sys, os, glob, importlib, tempfile
sys.path.insert(0, 'app')
for name, mod in [('bh_config','config'),('bh_db','db'),('bh_parsers','parsers'),
                  ('bh_matching','matching'),('bh_fifo','fifo')]:
    sys.modules[name] = importlib.import_module(mod)
import bh_config as C, bh_db as DB, bh_parsers as P, bh_matching as M, bh_fifo as F

dbp = os.path.join(tempfile.gettempdir(), 'bh_test.db')
for s in ('','-wal','-shm'):
    try: os.remove(dbp+s)
    except OSError: pass
cx = DB.connect(dbp)
eng = M.MatchEngine(cx)

def imp(folder, kind):
    files = P.scan_folder(folder)
    docs = lines = skipped = 0
    for f in files:
        sid, isnew = DB.add_source_file(cx, f, kind)
        if not isnew:
            print('   dublikat fayl otkazildi:', os.path.basename(f)[:50]); continue
        r = P.parse_any(f, kind)
        for w in r['warnings']: print('   !', w)
        a, s, n = F.import_parsed(cx, eng, r, sid)
        docs += a; skipped += s; lines += n
    print('  %s: %d fayl -> %d hujjat, %d satr (%d takror)' % (kind, len(files), docs, lines, skipped))

print('=== IMPORT ===')
imp(os.environ.get('BH_TEST_FAKTURA', os.path.expanduser(r'~\OneDrive\Desktop\FAKTURA')), 'kirim')
imp(os.environ.get('BH_TEST_CHIQIM', os.path.expanduser(r'~\OneDrive\Desktop\CHIQIM')), 'chiqim')

print()
print('=== MOSLASHTIRISH ===')
st = DB.stats(cx)
print('  import paytida bogланgan. Boglanmagan satr:', st['unmatched'])
eng.reload()
done, left = M.auto_match_all(cx)
print('  avtomatik qoshimcha: %d,  qolgan: %d' % (done, left))

tot_out = cx.execute("SELECT COUNT(*) c FROM doc_line WHERE kind='chiqim'").fetchone()['c']
unm = cx.execute("SELECT COUNT(*) c FROM doc_line WHERE kind='chiqim' AND product_id IS NULL").fetchone()['c']
print('  sotuv satri: %d,  boglangan: %d (%.0f%%),  qolgan: %d' % (tot_out, tot_out-unm, 100.0*(tot_out-unm)/tot_out, unm))
print('  usullar:')
for r in cx.execute("SELECT match_method m, COUNT(*) n FROM doc_line WHERE kind='chiqim' AND product_id IS NOT NULL GROUP BY m ORDER BY n DESC"):
    print('     %-12s %d' % (r['m'] or '?', r['n']))

print()
print('=== FIFO ===')
res = F.rebuild_stock(cx)
print('  ', res)

print()
print('=== 2026 HISOBOT ===')
rows = F.year_rows(cx, 2026)
t = F.year_totals(rows)
print('  satr: %d' % t['rows'])
for k in ('open_sum','in_sum','out_sum','close_sum','sale_sum','profit'):
    print('    %-10s %18s' % (k, t[k]))
print('    close_qty  %18s   <- MANFIY BOLMASLIGI KERAK' % t['close_qty'])

print()
print('=== TEKSHIRUV ===')
F.validate_year(cx, 2026)
for r in cx.execute("SELECT severity, code, COUNT(*) n FROM issue WHERE resolved=0 GROUP BY severity, code ORDER BY n DESC"):
    print('  %-14s %-20s %d' % (r['severity'], r['code'], r['n']))
print()
print('  Bogianmagan nomlar (eng katta summa boyicha):')
for r in eng.unmatched_groups(2026)[:8]:
    print('    %9.0f  x%-3d  %s' % (r['amount'], r['n'], (r['raw_name'] or '')[:56]))

print()
print('=== HISOBOT YOZISH ===')
sys.modules['bh_report'] = importlib.import_module('report')
import bh_report as R
DB.set_setting(cx, 'owner_name', 'Test Tashkilot')
out = os.path.join(tempfile.gettempdir(), R.default_filename(DB.available_years(cx)))
p, st = R.generate(cx, out, progress=lambda a,b,m: None)
print('  yozildi:', p)
print('  hajmi: %.1f KB' % (os.path.getsize(p)/1024.0))
print('  kassa satr: %d, ТХ satr: %d, xato: %d' % (st['kassa_rows'], st['tx_rows'], st['issues']))
for y, t in sorted(st['years'].items()):
    print('   %d: kirim=%s chiqim=%s qoldiq=%s sotuv=%s fойда=%s' % (y, t['in_sum'], t['out_sum'], t['close_sum'], t['sale_sum'], t['profit']))
