import os
os.environ['KIVY_NO_ARGS'] = '1'
os.environ['KIVY_NO_CONSOLELOG'] = '1'

import json, datetime
from pathlib import Path
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.properties import StringProperty, ObjectProperty
from kivy.clock import Clock

__version__ = "0.2"

DATA_FILE = "data.json"

SHIFT_TYPES = ["Štandardný výkon","T.V. (Turnus voľno)","0006-Hodi.povinn.škol.a","0007-Hod.nariadenej lek.prehliad.","0011-Nevysporiad.hod.nad FPČ","0014-Hodiny školenia","2125-Príplatok za real. AP-1","2160-Prípl.za sť.nástup a.","2190-Prípl.sťaž.pr.režim","3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r.","3120-Štúdium popri zamest.","3191-Náhrada za vyšetrenie","3440-Náhr.m.Ost.prek.nep","4181-Náhr.za pr.poh.v p.","8000-Nemoc","8020-OČR"]

def parse_time(t):
    if not t: return None
    try:
        h,m = str(t).replace('.',':').split(':')[:2]
        return int(h), int(m or 0)
    except: return None

def is_holiday(d):
    md = f"{d.month:02d}-{d.day:02d}"
    fixed = ["01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"]
    return md in fixed

def calc_shift(s):
    is_tv = "T.V." in str(s.get("shift_type","")) or s.get("train_first")=="T.V."
    if is_tv: return {"total":0,"night":0,"sat":0,"sun":0,"hol":0,"txt":"T.V."}
    if not s.get("start") or not s.get("end"): return {"total":0,"night":0,"sat":0,"sun":0,"hol":0}
    try:
        d = datetime.date.fromisoformat(s["date"])
    except: return {"total":0,"night":0,"sat":0,"sun":0,"hol":0}
    st = parse_time(s["start"]); en = parse_time(s["end"])
    if not st or not en: return {"total":0,"night":0,"sat":0,"sun":0,"hol":0}
    start = datetime.datetime.combine(d, datetime.time(st[0], st[1]))
    end = datetime.datetime.combine(d, datetime.time(en[0], en[1]))
    if end <= start: end += datetime.timedelta(days=1)
    total = int((end-start).total_seconds()//60)
    night=sat=sun=hol=0
    cur = start
    while cur < end:
        h = cur.hour + cur.minute/60
        if h >= 22 or h < 6: night+=1
        if cur.weekday()==5: sat+=1
        elif cur.weekday()==6: sun+=1
        if is_holiday(cur): hol+=1
        cur += datetime.timedelta(minutes=1)
    pnp=0
    if s.get("pnp_start") and s.get("pnp_end"):
        ps=parse_time(s["pnp_start"]); pe=parse_time(s["pnp_end"])
        if ps and pe:
            psd=datetime.datetime.combine(d, datetime.time(ps[0],ps[1]))
            ped=datetime.datetime.combine(d, datetime.time(pe[0],pe[1]))
            if ped<=psd: ped+=datetime.timedelta(days=1)
            pnp=int((ped-psd).total_seconds()//60)
            total=max(0,total-pnp)
    return {"total":total,"night":night,"sat":sat,"sun":sun,"hol":hol,"pnp":pnp}

def fmt(m): return f"{m//60:02d}:{m%60:02d}"

class ShiftCard(BoxLayout):
    def __init__(self, data, app, **kw):
        super().__init__(orientation='vertical', size_hint_y=None, height=110, padding=8, spacing=4, **kw)
        self.data=data; self.app=app
        c=calc_shift(data)
        top=BoxLayout(size_hint_y=None,height=22)
        top.add_widget(Label(text=f"{data['date']} {data.get('start','')}–{data.get('end','')} ({fmt(c['total'])})", halign='left', font_size=13, bold=True, size_hint_x=0.7))
        top.add_widget(Label(text=data.get('shift_type','')[:18], font_size=11, color=(0.5,0.7,1,1), size_hint_x=0.3))
        self.add_widget(top)
        mid=Label(text=f"🚂 {data.get('train_first','-')} {data.get('route_from','')} → {data.get('train_last','-')} {data.get('route_to','')} | {data.get('note','')}", font_size=11, color=(0.6,0.7,0.8,1), halign='left', size_hint_y=None, height=20)
        self.add_widget(mid)
        btns=BoxLayout(size_hint_y=None,height=36, spacing=6)
        b1=Button(text="Upraviť", font_size=11, size_hint_x=0.5); b1.bind(on_release=lambda x: app.open_edit(data))
        b2=Button(text="Zmazať", font_size=11, size_hint_x=0.3); b2.bind(on_release=lambda x: app.delete_shift(data))
        b3=Button(text="Kopírovať", font_size=11, size_hint_x=0.4); b3.bind(on_release=lambda x: app.dup_shift(data))
        btns.add_widget(b1); btns.add_widget(b3); btns.add_widget(b2)
        self.add_widget(btns)

class EditPopup(Popup):
    def __init__(self, data, on_save, **kw):
        super().__init__(title="Zmena - všetky polia", size_hint=(0.95,0.95), **kw)
        self.orig=data or {}; self.on_save=on_save
        root=BoxLayout(orientation='vertical')
        scroll=ScrollView()
        grid=GridLayout(cols=1, spacing=8, padding=10, size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        self.inputs={}
        def add_field(key, label, is_spinner=False, is_time=False):
            grid.add_widget(Label(text=label, size_hint_y=None, height=18, font_size=11, color=(0.6,0.7,0.8,1), halign
