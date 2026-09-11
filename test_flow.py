# -*- coding: utf-8 -*-
"""FlowBar: torayganda tugmalar pastga o'tadimi?"""
import sys, os, importlib, tempfile, shutil
sys.path.insert(0,'app')
import config
T=os.path.join(tempfile.gettempdir(),'bh_flow'); shutil.rmtree(T,ignore_errors=True); os.makedirs(T)
config.app_data_dir=lambda:T; config.db_path=lambda:os.path.join(T,'x.db')
sys.modules['bh_config']=config
for n,m in [('bh_db','db'),('bh_parsers','parsers'),('bh_matching','matching'),
            ('bh_fifo','fifo'),('bh_report','report'),('bh_ui','ui')]:
    sys.modules[n]=importlib.import_module(m)
import bh_ui as U
import tkinter as tk
from tkinter import ttk

root=tk.Tk(); root.geometry('1000x300')
fonts=U.setup_style(root,1.0)
holder=ttk.Frame(root); holder.pack(fill='x')
bar=U.FlowBar(holder, scale=1.0); bar.pack(fill='x')
for t in ["Papka tanlash","Fayl qo'shish","Import qilish","Qayta hisoblash"]:
    bar.add(ttk.Button(bar,text=t,style='Ghost.TButton'),'left')
bar.add(ttk.Button(bar,text="Hisobot yaratish",style='Accent.TButton'),'right')
root.update_idletasks(); root.update()

print('%-8s %-6s %-6s %-9s %s' % ('kenglik','qator','balandl','eng_ong','holat'))
ok=True
for w in (1000, 860, 720, 640, 560, 480, 420, 360, 300):
    holder.configure(width=w); bar.configure(width=w)
    holder.pack_propagate(False); holder.configure(height=200)
    root.geometry('%dx300' % w)
    for _ in range(5):
        root.update_idletasks(); root.update()
    btns=bar._left+bar._right
    ys=sorted(set(b.winfo_y() for b in btns))
    maxx=max(b.winfo_x()+b.winfo_width() for b in btns)
    minx=min(b.winfo_x() for b in btns)
    fits = maxx <= bar.winfo_width()+1 and minx >= 0
    ok = ok and fits
    print('%-8d %-6d %-8d %-9d %s' % (bar.winfo_width(), len(ys), bar.winfo_height(), maxx,
                                      'OK - hammasi ichida' if fits else 'XATO - chetga chiqdi'))
print()
print('NATIJA:', 'FlowBar TOGRI ISHLAYDI' if ok else 'MUAMMO')
root.destroy()
