# -*- coding: utf-8 -*-
"""Bitta fayl / ko'p fayl / papka - hammasi navbatga tushadimi?"""
import sys, os, importlib, tempfile, shutil, glob
sys.path.insert(0,'app')
import config
T=os.path.join(tempfile.gettempdir(),'bh_drop'); shutil.rmtree(T,ignore_errors=True); os.makedirs(T)
config.app_data_dir=lambda:T; config.db_path=lambda:os.path.join(T,'x.db')
sys.modules['bh_config']=config
for n,m in [('bh_db','db'),('bh_parsers','parsers'),('bh_matching','matching'),
            ('bh_fifo','fifo'),('bh_report','report'),('bh_ui','ui')]:
    sys.modules[n]=importlib.import_module(m)
import bh_ui as U
import tkinter as tk

FAK=os.environ.get('BH_TEST_FAKTURA', os.path.expanduser(r'~\OneDrive\Desktop\FAKTURA'))
CHQ=os.environ.get('BH_TEST_CHIQIM', os.path.expanduser(r'~\OneDrive\Desktop\CHIQIM'))
fak=sorted(glob.glob(os.path.join(FAK,'*.xls')))
chq=sorted(glob.glob(os.path.join(CHQ,'*.xlsx')))

root=tk.Tk()
app=U.App(root,{'origins':{'bh_ui':'lokal'}})
root.update_idletasks(); root.update()
print('drag&drop backend:', app._dnd or 'YO\'Q (tugmalar orqali ishlaydi)')
print()

def show(t):
    kinds={}
    for _p,k in app.queued_files: kinds[k]=kinds.get(k,0)+1
    print('  %-34s navbat=%-3d  %s' % (t, len(app.queued_files), kinds))

app.queued_files=[]
app._accept([fak[0]]); show('1) BITTA faktura tashlandi')

app.queued_files=[]
app._accept(fak[:10]); show('2) 10 TA faktura birdan')

app.queued_files=[]
app._accept([FAK]); show('3) butun PAPKA')

app.queued_files=[]
app._accept(fak[:5]+chq[:2]+[CHQ]); show('4) ARALASH (5 fayl + 2 fayl + papka)')

app._accept(fak[:5]); show('5) o\'sha 5 tasi QAYTA tashlandi')

app.scan_folders(); show('6) papka skani ustiga qo\'shildi')

# tur almashtirish
app.queued_files=[(fak[0],'chiqim')]
app.tbl_files.tree.selection_set('0')
app._toggle_kind(); show('7) turi ikki marta bosib almashtirildi')

print()
print('  Turlari to\'g\'ri aniqlandimi:')
app.queued_files=[]
app._accept(fak[:3]+chq[:2])
for p,k in app.queued_files:
    print('     %-8s %-8s %s' % (k, U.P.sniff(p), os.path.basename(p)[:44]))
root.destroy()
print()
print('NATIJA: bitta ham, ko\'p ham, papka ham, aralash ham ishlaydi')
