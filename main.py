
import json, os, datetime
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
            grid.add_widget(Label(text=label, size_hint_y=None, height=18, font_size=11, color=(0.6,0.7,0.8,1), halign='left'))
            if is_spinner:
                w=Spinner(text=self.orig.get(key,"Štandardný výkon"), values=SHIFT_TYPES, size_hint_y=None, height=40)
            else:
                w=TextInput(text=str(self.orig.get(key,"")), multiline=False, size_hint_y=None, height=40, hint_text=label)
                if is_time: w.hint_text="HH:MM"
            self.inputs[key]=w; grid.add_widget(w)
        add_field("date","Dátum (YYYY-MM-DD)")
        add_field("shift_type","Mzdový druh", is_spinner=True)
        add_field("turnus","Turnusový deň")
        add_field("plan","Plán. dĺžka (HH:MM)", is_time=True)
        add_field("start","Nástup *", is_time=True)
        add_field("end","Koniec *", is_time=True)
        add_field("train_first","Prvý vlak")
        add_field("route_from","Trať z")
        add_field("train_last","Posledný vlak")
        add_field("route_to","Trať do")
        add_field("pc_start","Začiatok PC", is_time=True)
        add_field("pc_end","Koniec PC", is_time=True)
        add_field("pnp_start","PNP Od", is_time=True)
        add_field("pnp_end","PNP Do", is_time=True)
        add_field("meal_override","Stravné override (€)")
        add_field("other_premiums","Iné príplatky (€)")
        grid.add_widget(Label(text="Poznámka", size_hint_y=None, height=18, font_size=11))
        self.inputs["note"]=TextInput(text=str(self.orig.get("note","")), size_hint_y=None, height=60, multiline=True); grid.add_widget(self.inputs["note"])
        scroll.add_widget(grid); root.add_widget(scroll)
        foot=BoxLayout(size_hint_y=None, height=50, spacing=10, padding=5)
        b_cancel=Button(text="Zrušiť"); b_cancel.bind(on_release=lambda x: self.dismiss())
        b_save=Button(text="Uložiť", background_color=(0.13,0.77,0.37,1)); b_save.bind(on_release=self.do_save)
        foot.add_widget(b_cancel); foot.add_widget(b_save); root.add_widget(foot)
        self.content=root
    def do_save(self,*a):
        data={k: (w.text if hasattr(w,'text') else w.text) for k,w in self.inputs.items()}
        if not data.get("date"): return
        data["uid"]=self.orig.get("uid") or str(datetime.datetime.now().timestamp())
        self.on_save(data); self.dismiss()

class ZSSKApp(App):
    def build(self):
        self.title="ZSSK Smeny"
        self.shifts=self.load_data()
        self.month=None
        root=BoxLayout(orientation='vertical')
        top=BoxLayout(size_hint_y=None, height=50, padding=5, spacing=5)
        self.month_label=Label(text="", font_size=13)
        btn_prev=Button(text="<", size_hint_x=0.15); btn_prev.bind(on_release=self.prev_month)
        btn_next=Button(text=">", size_hint_x=0.15); btn_next.bind(on_release=self.next_month)
        btn_add=Button(text="+ Pridať", background_color=(0.13,0.77,0.37,1), size_hint_x=0.3); btn_add.bind(on_release=lambda x: self.open_edit(None))
        top.add_widget(btn_prev); top.add_widget(self.month_label); top.add_widget(btn_next); top.add_widget(btn_add)
        root.add_widget(top)
        self.kpi=Label(text="", size_hint_y=None, height=60, font_size=12); root.add_widget(self.kpi)
        self.scroll=ScrollView(); self.list_layout=GridLayout(cols=1, spacing=6, padding=6, size_hint_y=None); self.list_layout.bind(minimum_height=self.list_layout.setter('height'))
        self.scroll.add_widget(self.list_layout); root.add_widget(self.scroll)
        Clock.schedule_once(lambda dt: self.refresh(),0.2)
        return root
    def load_data(self):
        try:
            if os.path.exists(DATA_FILE):
                with open(DATA_FILE, encoding='utf-8') as f: d=json.load(f); return d if isinstance(d,list) else d.get('shifts_data',[])
        except: pass
        return []
    def save_data(self):
        try:
            with open(DATA_FILE,'w',encoding='utf-8') as f: json.dump(self.shifts,f,ensure_ascii=False,indent=2)
        except Exception as e: print(e)
    def get_months(self):
        s=sorted(set([x['date'][:7] for x in self.shifts if x.get('date')]))
        return s
    def refresh(self):
        months=self.get_months()
        if not months: self.month_label.text="Žiadne dáta"; self.list_layout.clear_widgets(); return
        if not self.month: self.month=months[-1]
        self.month_label.text=self.month
        filtered=[x for x in self.shifts if x.get('date','').startswith(self.month)]
        filtered.sort(key=lambda x: x['date'])
        t=n=sa=su=0
        for s in filtered:
            c=calc_shift(s); t+=c['total']; n+=c['night']; sa+=c['sat']; su+=c['sun']
        self.kpi.text=f"Spolu: {fmt(t)} | Noc: {fmt(n)} | SO: {fmt(sa)} NE: {fmt(su)} | Počet: {len(filtered)}"
        self.list_layout.clear_widgets()
        for s in filtered:
            self.list_layout.add_widget(ShiftCard(s,self))
    def prev_month(self,*a):
        m=self.get_months()
        if not m or not self.month: return
        i=m.index(self.month); self.month=m[max(0,i-1)]; self.refresh()
    def next_month(self,*a):
        m=self.get_months()
        if not m or not self.month: return
        i=m.index(self.month); self.month=m[min(len(m)-1,i+1)]; self.refresh()
    def open_edit(self, data):
        def on_save(new_data):
            if data:
                idx=self.shifts.index(data); self.shifts[idx]=new_data
            else:
                self.shifts.append(new_data)
            self.save_data(); self.refresh()
        EditPopup(data or {}, on_save).open()
    def delete_shift(self, data):
        self.shifts.remove(data); self.save_data(); self.refresh()
    def dup_shift(self, data):
        import copy; nd=copy.deepcopy(data); nd['uid']=str(datetime.datetime.now().timestamp()); self.shifts.append(nd); self.save_data(); self.refresh()

if __name__=='__main__':
    ZSSKApp().run()
