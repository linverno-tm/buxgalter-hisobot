# -*- coding: utf-8 -*-
"""
bh_report - "КАМЕРАЛ ТЕКШИРУВЛАР" ko'rinishidagi Excel hisobotini yozadi.

Varaqlar mavjud fayldagidek:
    касса YYYY  - kassa cheklari (20 ustun)
    YYYY ТХ     - tovar harakati (22 ustun, ikki qavatli sarlavha)
    Xatolar     - YANGI: tekshiruv natijalari
    Ma'lumot    - YANGI: hisobot qanday yig'ilgani

Chiqish formati .xlsx. Eski fayl .xls (BIFF8) edi, lekin Python'da .xls
yozish kutubxonalari tashlab yuborilgan. .xlsx Excel'da bir xil ochiladi.
"""

import os
import datetime
from decimal import Decimal

import bh_config as C
import bh_db as DB
import bh_fifo as F


NUM_MONEY = '#,##0.00'
NUM_QTY = '#,##0.####'
NUM_DATE = 'DD.MM.YYYY'


def _styles(wb):
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    thin = Side(style="thin", color="9AA0A6")
    med = Side(style="medium", color="44546A")
    return {
        "title": {"font": Font(name="Calibri", size=14, bold=True, color="1F3864"),
                  "align": Alignment(horizontal="center", vertical="center")},
        "hdr": {"font": Font(name="Calibri", size=9, bold=True, color="FFFFFF"),
                "fill": PatternFill("solid", fgColor="44546A"),
                "align": Alignment(horizontal="center", vertical="center",
                                   wrap_text=True),
                "border": Border(left=thin, right=thin, top=med, bottom=thin)},
        "sub": {"font": Font(name="Calibri", size=9, bold=True, color="FFFFFF"),
                "fill": PatternFill("solid", fgColor="5B7397"),
                "align": Alignment(horizontal="center", vertical="center",
                                   wrap_text=True),
                "border": Border(left=thin, right=thin, top=thin, bottom=med)},
        "cell": {"font": Font(name="Calibri", size=9),
                 "align": Alignment(vertical="top", wrap_text=True),
                 "border": Border(left=thin, right=thin, top=thin, bottom=thin)},
        "num": {"font": Font(name="Calibri", size=9),
                "align": Alignment(horizontal="right", vertical="top"),
                "border": Border(left=thin, right=thin, top=thin, bottom=thin)},
        "total": {"font": Font(name="Calibri", size=10, bold=True),
                  "fill": PatternFill("solid", fgColor="D9E2F3"),
                  "align": Alignment(horizontal="right", vertical="center"),
                  "border": Border(left=thin, right=thin, top=med, bottom=med)},
        "warn": {"fill": PatternFill("solid", fgColor="FFF2CC")},
        "err": {"fill": PatternFill("solid", fgColor="FCE4E4")},
    }


def _apply(cell, st, number_format=None):
    if "font" in st:
        cell.font = st["font"]
    if "fill" in st:
        cell.fill = st["fill"]
    if "align" in st:
        cell.alignment = st["align"]
    if "border" in st:
        cell.border = st["border"]
    if number_format:
        cell.number_format = number_format


def _f(v):
    """Decimal -> Excel raqami (float). Excel Decimal'ni tushunmaydi."""
    if v is None:
        return None
    if isinstance(v, Decimal):
        return float(v)
    return v


# ===========================================================================
# ТХ varag'i
# ===========================================================================
def write_tx_sheet(wb, cx, year, owner_name, S):
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet("%d ТХ" % year)
    rows = F.year_rows(cx, year)
    tot = F.year_totals(rows)
    ncol = len(C.TX_COLUMNS)

    # --- 1-satr: sarlavha ---
    ws.merge_cells(start_row=1, start_column=2, end_row=1, end_column=ncol)
    c = ws.cell(row=1, column=2, value="%s ning %d йил товар хисоботи" % (owner_name, year))
    _apply(c, S["title"])
    ws.row_dimensions[1].height = 26

    # --- 2-satr: jami ko'rsatkichlar ---
    ws.cell(row=2, column=11, value="Кирим жами:")
    ws.cell(row=2, column=12, value=_f(tot["in_sum"])).number_format = NUM_MONEY
    ws.cell(row=2, column=14, value="Чиқим жами:")
    ws.cell(row=2, column=15, value=_f(tot["out_sum"])).number_format = NUM_MONEY
    ws.cell(row=2, column=17, value="Қолдиқ:")
    ws.cell(row=2, column=18, value=_f(tot["close_sum"])).number_format = NUM_MONEY
    ws.cell(row=2, column=20, value="Соф фойда:")
    ws.cell(row=2, column=21, value=_f(tot["profit"])).number_format = NUM_MONEY
    for col in (11, 14, 17, 20):
        ws.cell(row=2, column=col).font = S["total"]["font"]

    # --- 3-4 satr: ikki qavatli sarlavha ---
    hr, sr = 3, 4
    for i, (_idx, name, width) in enumerate(C.TX_COLUMNS):
        col = i + 1
        ws.column_dimensions[get_column_letter(col)].width = width
    # guruhlanmagan ustunlar 3-4 satrni egallaydi
    grouped = set()
    for a, b, _t in C.TX_GROUPS:
        grouped.update(range(a, b + 1))
    for i, (idx, name, _w) in enumerate(C.TX_COLUMNS):
        col = i + 1
        if idx in grouped:
            continue
        ws.merge_cells(start_row=hr, start_column=col, end_row=sr, end_column=col)
        _apply(ws.cell(row=hr, column=col, value=name), S["hdr"])
    for a, b, title in C.TX_GROUPS:
        ws.merge_cells(start_row=hr, start_column=a + 1, end_row=hr, end_column=b + 1)
        _apply(ws.cell(row=hr, column=a + 1, value=title), S["hdr"])
        for idx in range(a, b + 1):
            _apply(ws.cell(row=sr, column=idx + 1, value=C.TX_COLUMNS[idx][1]), S["sub"])
    ws.row_dimensions[hr].height = 34
    ws.row_dimensions[sr].height = 18

    # --- ma'lumot satrlari ---
    r = sr + 1
    for n, d in enumerate(rows, start=1):
        vals = [
            n,
            C.parse_date(d["date"]),
            d["name"],
            ("маркировкаланган" if d["is_marked"] else
             ("маркировкасиз" if d["is_marked"] is False else "")),
            ("%s - %s" % (d["mxik"], d["mxik_name"])).strip(" -") if d["mxik"] else "",
            d["unit"],
            _f(d["sale_price"]),
            _f(d["open_qty"]), _f(d["cost"]), _f(d["open_sum"]),
            _f(d["in_qty"]), _f(d["cost"]), _f(d["in_sum"]),
            _f(d["out_qty"]), _f(d["cost"]), _f(d["out_sum"]),
            _f(d["close_qty"]), _f(d["cost"]), _f(d["close_sum"]),
            _f(d["sale_qty"]),
            _f(d["sale_price"]), _f(d["sale_sum"]),
        ]
        for i, v in enumerate(vals):
            cell = ws.cell(row=r, column=i + 1, value=v)
            if i == 1:
                _apply(cell, S["cell"], NUM_DATE)
            elif i in (0,):
                _apply(cell, S["num"], '0')
            elif i in (7, 10, 13, 16, 19):
                _apply(cell, S["num"], NUM_QTY)
            elif i >= 6:
                _apply(cell, S["num"], NUM_MONEY)
            else:
                _apply(cell, S["cell"])
        if d.get("shortfall"):
            for i in range(ncol):
                ws.cell(row=r, column=i + 1).fill = S["err"]["fill"]
        elif d["close_qty"] < 0:
            for i in range(ncol):
                ws.cell(row=r, column=i + 1).fill = S["warn"]["fill"]
        r += 1

    # --- jami satri ---
    _apply(ws.cell(row=r, column=1, value="ЖАМИ"), S["total"])
    for col in range(2, ncol + 1):
        _apply(ws.cell(row=r, column=col), S["total"])
    pairs = [(8, tot["open_qty"]), (10, tot["open_sum"]),
             (11, tot["in_qty"]), (13, tot["in_sum"]),
             (14, tot["out_qty"]), (16, tot["out_sum"]),
             (17, tot["close_qty"]), (19, tot["close_sum"]),
             (20, tot["out_qty"]), (22, tot["sale_sum"])]
    for col, val in pairs:
        cell = ws.cell(row=r, column=col, value=_f(val))
        _apply(cell, S["total"], NUM_QTY if col in (8, 11, 14, 17, 20) else NUM_MONEY)

    ws.freeze_panes = ws.cell(row=sr + 1, column=4)
    if r > sr + 1:
        ws.auto_filter.ref = "A%d:%s%d" % (sr, get_column_letter(ncol), r - 1)
    ws.sheet_view.zoomScale = 90
    return len(rows), tot


# ===========================================================================
# Kassa varag'i
# ===========================================================================
def write_kassa_sheet(wb, cx, year, S):
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet("касса %d" % year)
    widths = [34, 16, 16, 19, 11, 46, 10, 15, 13, 13, 13, 15, 15, 14, 19, 13,
              14, 16, 20, 11]
    for i, w in enumerate(widths):
        ws.column_dimensions[get_column_letter(i + 1)].width = w

    for i, h in enumerate(C.KASSA_HEADERS):
        _apply(ws.cell(row=1, column=i + 1, value=h), S["hdr"])
    ws.row_dimensions[1].height = 32

    r = 2
    n = 0
    for d in cx.execute("""
            SELECT l.*, d.doc_no, d.doc_date, d.pos_id, d.partner_tin, d.check_type,
                   d.total_gross, d.total_vat, d.is_return
            FROM doc_line l JOIN document d ON d.id=l.document_id
            WHERE l.kind='chiqim' AND d.doc_year=?
            ORDER BY d.doc_date, d.doc_no, l.line_no""", (year,)):
        cash = DB.D(0)
        card = DB.D(d["total_gross"])
        vals = [
            "", d["partner_tin"], d["pos_id"], d["doc_date"], d["doc_no"],
            d["raw_name"], _f(DB.D(d["qty"])), _f(DB.D(d["amount_gross"])),
            0, 0, _f(DB.D(d["vat_amount"])),
            _f(cash), _f(card), _f(DB.D(d["total_vat"])),
            d["mxik"], d["unit_raw"], d["barcode"], "", d["marking_code"],
            d["check_type"],
        ]
        for i, v in enumerate(vals):
            cell = ws.cell(row=r, column=i + 1, value=v)
            if i == 6:
                _apply(cell, S["num"], NUM_QTY)
            elif i in (7, 8, 9, 10, 11, 12, 13):
                _apply(cell, S["num"], NUM_MONEY)
            else:
                _apply(cell, S["cell"])
        if d["is_return"]:
            for i in range(len(vals)):
                ws.cell(row=r, column=i + 1).fill = S["warn"]["fill"]
        r += 1
        n += 1

    ws.freeze_panes = "A2"
    if n:
        ws.auto_filter.ref = "A1:%s%d" % (get_column_letter(len(C.KASSA_HEADERS)), r - 1)
    ws.sheet_view.zoomScale = 90
    return n


# ===========================================================================
# Xatolar varag'i (YANGI)
# ===========================================================================
def write_issues_sheet(wb, cx, years, S):
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet("Xatolar")
    heads = ["Yil", "Daraja", "Turi", "Tavsif", "Manba", "ID"]
    widths = [8, 16, 26, 96, 12, 8]
    for i, (h, w) in enumerate(zip(heads, widths)):
        ws.column_dimensions[get_column_letter(i + 1)].width = w
        _apply(ws.cell(row=1, column=i + 1, value=h), S["hdr"])
    ws.row_dimensions[1].height = 22

    r = 2
    q = "SELECT * FROM issue WHERE resolved=0"
    args = []
    if years:
        q += " AND (year IS NULL OR year IN (%s))" % ",".join("?" * len(years))
        args = list(years)
    q += (" ORDER BY CASE severity WHEN 'xato' THEN 0 WHEN 'ogohlantirish' "
          "THEN 1 ELSE 2 END, year, code")
    n = 0
    for d in cx.execute(q, args):
        vals = [d["year"], d["severity"],
                C.ISSUE_TITLES.get(d["code"], d["code"]), d["message"],
                d["ref_table"], d["ref_id"]]
        for i, v in enumerate(vals):
            cell = ws.cell(row=r, column=i + 1, value=v)
            _apply(cell, S["cell"])
        if d["severity"] == C.SEVERITY_ERROR:
            for i in range(len(heads)):
                ws.cell(row=r, column=i + 1).fill = S["err"]["fill"]
        elif d["severity"] == C.SEVERITY_WARN:
            for i in range(len(heads)):
                ws.cell(row=r, column=i + 1).fill = S["warn"]["fill"]
        r += 1
        n += 1

    ws.freeze_panes = "A2"
    if n:
        ws.auto_filter.ref = "A1:F%d" % (r - 1)
    return n


# ===========================================================================
# Ma'lumot varag'i (YANGI)
# ===========================================================================
def write_info_sheet(wb, cx, years, S, totals_by_year):
    from openpyxl.utils import get_column_letter

    ws = wb.create_sheet("Ma'lumot", 0)
    ws.column_dimensions["A"].width = 40
    ws.column_dimensions["B"].width = 30
    ws.column_dimensions["C"].width = 22
    ws.column_dimensions["D"].width = 22
    ws.column_dimensions["E"].width = 22

    r = 1
    _apply(ws.cell(row=r, column=1, value="Hisobot qanday yig'ilgani"), S["title"])
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
    r += 2

    st = DB.stats(cx)
    info = [
        ("Yaratilgan sana", datetime.datetime.now().strftime("%d.%m.%Y %H:%M")),
        ("Dastur versiyasi", C.VERSION),
        ("QQS stavkasi", "%s%%" % (C.VAT_RATE * 100)),
        ("", ""),
        ("Import qilingan fayl", st["files"]),
        ("Kirim hujjati (faktura)", st["docs_in"]),
        ("Chiqim hujjati (chek)", st["docs_out"]),
        ("Kirim satri", st["lines_in"]),
        ("Chiqim satri", st["lines_out"]),
        ("Mahsulot kartochkasi", st["products"]),
        ("Bog'lanmagan satr", st["unmatched"]),
        ("Ochiq tekshiruv yozuvi", st["issues"]),
    ]
    for k, v in info:
        if k:
            ws.cell(row=r, column=1, value=k).font = S["cell"]["font"]
            ws.cell(row=r, column=2, value=v).font = S["total"]["font"]
        r += 1

    r += 1
    _apply(ws.cell(row=r, column=1, value="Yillar bo'yicha"), S["hdr"])
    for i, h in enumerate(["Kirim (tannarx)", "Chiqim (tannarx)",
                           "Qoldiq (tannarx)", "Sotuv (QQS bilan)"]):
        _apply(ws.cell(row=r, column=i + 2, value=h), S["hdr"])
    r += 1
    for y in years:
        t = totals_by_year.get(y)
        if not t:
            continue
        ws.cell(row=r, column=1, value=y).font = S["total"]["font"]
        for i, k in enumerate(("in_sum", "out_sum", "close_sum", "sale_sum")):
            c = ws.cell(row=r, column=i + 2, value=_f(t[k]))
            c.number_format = NUM_MONEY
        r += 1

    r += 1
    notes = [
        "Eslatmalar:",
        "  - Qizil bo'yalgan satr: tovar sotilgan, lekin kirim hujjati topilmadi "
        "(tannarx taxminiy).",
        "  - Sariq bo'yalgan satr: davr oxiriga qoldiq manfiy yoki chek qaytarilgan.",
        "  - Davr boshiga qoldiq o'tgan yildan avtomatik ko'chiriladi (FIFO).",
        "  - Chiqim tannarxi FIFO bo'yicha: eng eski partiyadan yechiladi.",
        "  - Kassa 'Нархи' ustuni satr SUMMASI (QQS ichida), birlik narxi emas.",
    ]
    for t in notes:
        ws.cell(row=r, column=1, value=t).font = S["cell"]["font"]
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=5)
        r += 1
    return ws


# ===========================================================================
# Asosiy
# ===========================================================================
def generate(cx, out_path, years=None, owner_name=None, progress=None):
    """
    Hisobotni yozadi. (yo'l, statistika) qaytaradi.
    """
    import openpyxl

    years = years or DB.available_years(cx)
    years = sorted(y for y in years if y)
    if not years:
        raise ValueError("Hisobot uchun ma'lumot yo'q - avval fayllarni import qiling.")

    owner_name = owner_name or DB.get_setting(cx, "owner_name", "Ташкилот")

    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    S = _styles(wb)

    stats = {"years": {}, "kassa_rows": 0, "tx_rows": 0}
    totals_by_year = {}
    steps = len(years) * 2 + 2
    step = 0

    for y in years:
        F.validate_year(cx, y)
        n = write_kassa_sheet(wb, cx, y, S)
        stats["kassa_rows"] += n
        step += 1
        if progress:
            progress(step, steps, "касса %d" % y)

    for y in years:
        nrows, tot = write_tx_sheet(wb, cx, y, owner_name, S)
        stats["tx_rows"] += nrows
        stats["years"][y] = tot
        totals_by_year[y] = tot
        step += 1
        if progress:
            progress(step, steps, "%d ТХ" % y)

    n_iss = write_issues_sheet(wb, cx, years, S)
    stats["issues"] = n_iss
    step += 1
    if progress:
        progress(step, steps, "Xatolar")

    write_info_sheet(wb, cx, years, S, totals_by_year)
    step += 1
    if progress:
        progress(step, steps, "Ma'lumot")

    d = os.path.dirname(os.path.abspath(out_path))
    if d and not os.path.isdir(d):
        os.makedirs(d, exist_ok=True)
    wb.save(out_path)
    wb.close()
    return out_path, stats


def default_filename(years):
    ys = sorted(y for y in (years or []) if y)
    if not ys:
        rng = "hisobot"
    elif len(ys) == 1:
        rng = "%d" % ys[0]
    else:
        rng = "%d-%d" % (ys[0], ys[-1])
    return "КАМЕРАЛ ТЕКШИРУВЛАР %s.xlsx" % rng
