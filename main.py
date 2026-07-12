import json, os, datetime, calendar, uuid, csv
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

THEMES = {
    'tmava': {
        'name': 'Tmavá', 'bg': (0.07,0.09,0.14,1), 'header_bg': (0.12,0.16,0.22,1),
        'card_bg': (0.14,0.18,0.26,1), 'row_bg': (0.20,0.22,0.28,1),
        'input_bg': (0.18,0.20,0.28,1), 'input_fg': (1,1,1,1),
        'text': (0.96,0.97,0.99,1), 'subtext': (0.62,0.70,0.82,1), 'accent': (0.15,0.55,0.85,1),
        'btn_mesiac': (0.32,0.34,0.40,1), 'btn_turnus': (0.55,0.32,0.18,1),
        'btn_stats': (0.18,0.45,0.32,1), 'btn_export': (0.15,0.38,0.68,1),
        'btn_settings': (0.38,0.38,0.42,1), 'btn_primary': (0,0.42,0.78,1), 'btn_save': (0.12,0.55,0.25,1), 'btn_oprav': (0.68,0.42,0.12,1), 'btn_danger': (0.78,0.18,0.18,1),
    },
    'zssk': {
        'name': 'ZSSK / PROSOFT svetlá', 'bg': (0.96,0.96,0.96,1), 'header_bg': (0.90,0.31,0.0,1),
        'card_bg': (1,1,1,1), 'row_bg': (0.92,0.92,0.94,1),
        'input_bg': (1,1,1,1), 'input_fg': (0.15,0.15,0.15,1),
        'text': (0.13,0.13,0.15,1), 'subtext': (0.45,0.48,0.55,1), 'accent': (0.90,0.31,0.0,1),
        'btn_mesiac': (0.35,0.36,0.40,1), 'btn_turnus': (0.90,0.31,0.0,1),
        'btn_stats': (0.20,0.60,0.30,1), 'btn_export': (0.12,0.42,0.75,1),
        'btn_settings': (0.45,0.46,0.50,1), 'btn_primary': (0.90,0.31,0.0,1), 'btn_save': (0.18,0.58,0.24,1), 'btn_oprav': (0.92,0.58,0.05,1), 'btn_danger': (0.85,0.20,0.20,1),
    }
}

SHIFT_TYPES = [
    "Štandardný výkon","T.V. (Turnus voľno)","0006-Hodi.povinn.škol.a","0007-Hod.nariadenej lek.prehliad.",
    "0011-Nevysporiad.hod.nad FPČ","0014-Hodiny školenia","2125-Príplatok za real. AP-1","2160-Prípl.za sť.nástup a.",
    "2190-Prípl.sťaž.pr.režim","3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r.","3120-Štúdium popri zamest.",
    "3191-Náhrada za vyšetrenie","3440-Náhr.m.Ost.prek.nep","4181-Náhr.za pr.poh.v p.","8000-Nemoc","8020-OČR"
]
COLORS_DARK = {'Štandardný výkon':(0.15,0.55,0.85,1),'T.V. (Turnus voľno)':(0.28,0.32,0.38,1),'Ranná':(0.15,0.55,0.85,1),'Poobedná':(0.85,0.55,0.15,1),'Nočná':(0.32,0.32,0.82,1),'Voľno':(0.22,0.60,0.26,1),'Dovolenka':(0.18,0.65,0.38,1)}
COLORS_LIGHT = {'Štandardný výkon':(0.12,0.42,0.75,1),'T.V. (Turnus voľno)':(0.78,0.78,0.80,1),'Ranná':(0.12,0.42,0.75,1),'Poobedná':(0.90,0.45,0.05,1),'Nočná':(0.28,0.28,0.72,1),'Voľno':(0.22,0.62,0.28,1),'Dovolenka':(0.18,0.62,0.34,1)}
PATTERN = ['Ranná','Ranná','Poobedná','Poobedná','Nočná','Nočná','Voľno','Voľno']
SHIFT_TIMES = {
    'Ranná': ('06:00','14:00','08:00'),
    'Poobedná': ('14:00','22:00','08:00'),
    'Nočná': ('22:00','06:00','08:00'),
    'Voľno': ('','',''),
    'Dovolenka': ('','','05:08'),
}
SK_SVIATKY_FIX = {"01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"}

def format_date_display(iso_date):
    """YYYY-MM-DD -> D-M-YYYY napr. 2026-06-15 -> 15-6-2026"""
    try:
        y,m,d = iso_date.split('-')
        return f"{int(d)}-{int(m)}-{y}"
    except:
        return iso_date

class ShiftCalculator:
    def __init__(self): self.rates={"meal_a":9.30,"meal_b":13.80,"meal_c":21.00}
    def parse_time(self,s):
        try:
            if not s or s.strip() in ("","-"): return None
            p=s.replace(".",":").split(":"); return datetime.time(int(p[0]), int(p[1]) if len(p)>1 else 0)
        except: return None
    def get_easter_date(self,y):
        a=y%19; b=y//100; c=y%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3; h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; L=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*L)//451; mo=(h+L-7*m+114)//31; da=((h+L-7*m+114)%31)+1; return datetime.date(y,mo,da)
    def is_slovak_holiday(self,d):
        if d.strftime("%m-%d") in SK_SVIATKY_FIX: return True
        e=self.get_easter_date(d.year); return d in (e-datetime.timedelta(days=2), e+datetime.timedelta(days=1))
    def calculate_shift(self,ds,ss,es,plan="",pcs="",pce="",pnps="",pnpe="",st="",mo="",ot=""):
        stt=self.parse_time(ss); ett=self.parse_time(es); ptt=self.parse_time(plan); pcst=self.parse_time(pcs); pcet=self.parse_time(pce); pnpst=self.parse_time(pnps); pnpet=self.parse_time(pnpe)
        try: sd=datetime.datetime.strptime(ds,"%Y-%m-%d").date()
        except: return None
        def fmt(m): return f"{m//60:02d}:{m%60:02d}"
        tot=night=sat=sun=hol=pnp=over=0; has=False
        is_vac=st in ["3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r.","Dovolenka"]; is_abs=st in ["3440-Náhr.m.Ost.prek.nep","8000-Nemoc","8020-OČR","3191-Náhrada za vyšetrenie"]
        # DOVOLENKA = 5:08 = 308 minút - OPRAVENÉ
        if is_vac or is_abs:
            abs_mins=308
            if ptt: abs_mins=ptt.hour*60+ptt.minute
            elif stt and ett:
                sdt=datetime.datetime.combine(sd,stt); edt=datetime.datetime.combine(sd+datetime.timedelta(days=1),ett) if ett<stt else datetime.datetime.combine(sd,ett)
                abs_mins=int((edt-sdt).total_seconds()/60)
            return {"total_hours":fmt(abs_mins),"night_hours":"-","saturday_hours":"-","sunday_hours":"-","holiday_hours":"-","pnp_hours":"-","pnp_minutes":0,"overtime":"-","meal_allowance":0.0,"other_allowance":0.0,"vacation_minutes":abs_mins,"is_holiday":self.is_slovak_holiday(sd),"is_weekend":sd.weekday() in (5,6)}
        if pnpst and pnpet:
            ps=datetime.datetime.combine(sd,pnpst); pe=datetime.datetime.combine(sd+datetime.timedelta(days=1),pnpet) if pnpet<pnpst else datetime.datetime.combine(sd,pnpet); pnp=int((pe-ps).total_seconds()/60); pnp=max(0,pnp)
        if stt and ett:
            has=True; sdt=datetime.datetime.combine(sd,stt); edt=datetime.datetime.combine(sd+datetime.timedelta(days=1),ett) if ett<stt else datetime.datetime.combine(sd,ett); tot=int((edt-sdt).total_seconds()/60); tot=max(0,tot-pnp); cur=sdt
            while cur<edt:
                if cur.hour>=22 or cur.hour<6: night+=1
                if cur.weekday()==5: sat+=1
                elif cur.weekday()==6: sun+=1
                if self.is_slovak_holiday(cur.date()): hol+=1
                cur+=datetime.timedelta(minutes=1)
        elif ptt and st not in ["T.V. (Turnus voľno)","4181-Náhr.za pr.poh.v p.",""]:
            # OPRAVA: predtým bol vylúčený aj Štandardný výkon, preto generované zmeny mali 0 hodín
            has=True; tot=ptt.hour*60+ptt.minute
        if st=="4181-Náhr.za pr.poh.v p.": has=False; tot=0
        if ptt and has:
            pm=ptt.hour*60+ptt.minute
            if tot>pm: over=tot-pm
        meal=0.0; mc=""
        if mo and mo.strip()!="":
            try: meal=float(mo.replace(",",".")); mc="M"
            except: pass
        pcm=0; hpc=False
        if pcst and pcet: hpc=True; ps=datetime.datetime.combine(sd,pcst); pe=datetime.datetime.combine(sd+datetime.timedelta(days=1),pcet) if pcet<pcst else datetime.datetime.combine(sd,pcet); pcm=int((pe-ps).total_seconds()/60)
        no_meal=any(st.startswith(x) for x in ["0011","2125","2160","2190","4181","40"])
        if not mc and not no_meal and (has or hpc):
            ev=pcm if hpc else tot+pnp; eh=ev/60.0
            if 5<=eh<=12: meal=self.rates["meal_a"]
            elif 12<eh<=18: meal=self.rates["meal_b"]
            elif eh>18: meal=self.rates["meal_c"]
        oa=0.0
        if st.startswith("2125") and tot>0: oa=round(tot/60.0,2); has=False; tot=0
        elif ot and ot.strip()!="":
            try: oa=float(ot.replace(",","."))
            except: pass
        return {"total_hours":fmt(tot) if has else "-","night_hours":fmt(night) if night else "-","saturday_hours":fmt(sat) if sat else "-","sunday_hours":fmt(sun) if sun else "-","holiday_hours":fmt(hol) if hol else "-","pnp_hours":fmt(pnp) if pnp else "-","pnp_minutes":pnp,"overtime":fmt(over) if over else "-","meal_allowance":round(meal,2),"other_allowance":round(oa,2),"vacation_minutes":0,"is_holiday":self.is_slovak_holiday(sd),"is_weekend":sd.weekday() in (5,6)}

class TimePickerPopup(Popup):
    def __init__(self,initial="08:00",callback=None,**kw):
        super().__init__(**kw); self.callback=callback; self.title="Nastaviť čas"; self.size_hint=(0.85,0.5); self.separator_color=(0.9,0.31,0.0,1)
        try: h,m=initial.split(":"); hi=int(h); mi=int(m)
        except: hi,mi=8,0
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        row=BoxLayout(spacing=dp(10)); self.sp_h=Spinner(text=f"{hi:02d}",values=[f"{i:02d}" for i in range(24)],size_hint_x=0.5,font_size='20sp'); self.sp_m=Spinner(text=f"{mi:02d}",values=[f"{i:02d}" for i in range(60)],size_hint_x=0.5,font_size='20sp')
        row.add_widget(self.sp_h); row.add_widget(Label(text=":",font_size='22sp',size_hint_x=None,width=dp(20))); row.add_widget(self.sp_m); box.add_widget(row)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(10)); b1=Button(text="Zrušiť",background_normal='',background_color=(0.4,0.4,0.42,1)); b2=Button(text="Potvrdiť",background_normal='',background_color=(0.9,0.31,0.0,1),bold=True)
        b1.bind(on_press=self.dismiss); b2.bind(on_press=self.confirm); btns.add_widget(b1); btns.add_widget(b2); box.add_widget(btns); self.content=box
    def confirm(self,*a):
        if self.callback: self.callback(f"{self.sp_h.text}:{self.sp_m.text}"); self.dismiss()

class FilePickerPopup(Popup):
    """Vylepšený file picker s navigáciou + možnosťou zadať cestu ručne + systémový picker cez plyer ak je dostupný"""
    def __init__(self, start_dirs, callback, **kw):
        super().__init__(**kw); self.callback=callback; self.title="Vyber súbor - Import/Export"; self.size_hint=(0.96,0.90)
        self.start_dirs = [d for d in start_dirs if os.path.exists(d)]
        self.current_dir = self.start_dirs[0] if self.start_dirs else "."
        try:
            from plyer import filechooser as plyer_fc
            self.has_plyer = True
            self.plyer_fc = plyer_fc
        except:
            self.has_plyer = False
        self.build_ui()
        self.refresh_list()

    def build_ui(self):
        root=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(8))
        self.lbl_path=Label(text=self.current_dir,size_hint_y=None,height=dp(28),font_size='10sp',color=(0.7,0.7,0.7,1),halign='left',text_size=(dp(340),None)); root.add_widget(self.lbl_path)
        # ručné zadanie cesty
        row_manual=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(6))
        self.inp_manual=TextInput(hint_text='Ručne zadaj cestu k súboru',multiline=False,font_size='11sp'); b_go=Button(text='Načítaj',size_hint_x=None,width=dp(70),background_normal='',background_color=(0.2,0.5,0.3,1))
        b_go.bind(on_press=lambda *_: self.try_manual()); row_manual.add_widget(self.inp_manual); row_manual.add_widget(b_go); root.add_widget(row_manual)
        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(3),size_hint_y=None); self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)
        btns=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        b_up=Button(text='⬆ O úroveň vyššie',size_hint_x=0.5,background_normal='',background_color=(0.35,0.35,0.4,1),font_size='11sp'); b_sys=Button(text='📁 Systémový výber',size_hint_x=0.5,background_normal='',background_color=(0.15,0.38,0.68,1),font_size='11sp')
        b_up.bind(on_press=lambda *_: self.go_up()); b_sys.bind(on_press=self.open_system_picker); btns.add_widget(b_up); btns.add_widget(b_sys); root.add_widget(btns)
        bc=Button(text='Zavrieť',size_hint_y=None,height=dp(42),background_normal='',background_color=(0.36,0.36,0.38,1)); bc.bind(on_press=self.dismiss); root.add_widget(bc)
        self.content=root

    def refresh_list(self):
        self.grid.clear_widgets(); self.lbl_path.text=self.current_dir
        try:
            entries=os.listdir(self.current_dir)
        except Exception as e:
            self.grid.add_widget(Label(text=f'Chyba čítania: {e}',size_hint_y=None,height=dp(30))); return
        dirs=[]; files=[]
        for en in sorted(entries):
            fp=os.path.join(self.current_dir,en)
            if os.path.isdir(fp): dirs.append(en)
            elif en.lower().endswith(('.json','.csv','.txt')): files.append(en)
        # najprv priečinky
        for d in dirs:
            if d.startswith('.'): continue
            b=Button(text=f'📁 {d}',size_hint_y=None,height=dp(42),background_normal='',background_color=(0.25,0.28,0.36,1),halign='left',font_size='12sp'); b.bind(on_press=lambda inst,dn=d: self.enter_dir(dn)); self.grid.add_widget(b)
        for f in files:
            b=Button(text=f'📄 {f}',size_hint_y=None,height=dp(42),background_normal='',background_color=(0.18,0.32,0.52,1),halign='left',font_size='11sp'); b.bind(on_press=lambda inst,fn=f: self.select_file(fn)); self.grid.add_widget(b)
        if not dirs and not files:
            self.grid.add_widget(Label(text='Prázdny priečinok',size_hint_y=None,height=dp(30)))

    def enter_dir(self,dirname):
        self.current_dir=os.path.join(self.current_dir,dirname); self.refresh_list()
    def go_up(self):
        parent=os.path.dirname(self.current_dir.rstrip('/'))
        if parent and os.path.exists(parent): self.current_dir=parent; self.refresh_list()
    def select_file(self,filename):
        full=os.path.join(self.current_dir,filename); self.callback(full); self.dismiss()
    def try_manual(self):
        p=self.inp_manual.text.strip()
        if os.path.exists(p): self.callback(p); self.dismiss()
        else:
            # skús aj relatívne k Download
            for base in self.start_dirs:
                cand=os.path.join(base,p)
                if os.path.exists(cand): self.callback(cand); self.dismiss(); return
    def open_system_picker(self,*a):
        if not self.has_plyer:
            # fallback - ponúkni Download priečinky
            for d in ["/storage/emulated/0/Download","/sdcard/Download"]:
                if os.path.exists(d): self.current_dir=d; self.refresh_list(); return
            return
        try:
            self.plyer_fc.open_file(on_selection=lambda sel: self.on_plyer_select(sel))
        except Exception:
            pass
    def on_plyer_select(self,selection):
        if selection and len(selection)>0:
            self.callback(selection[0]); self.dismiss()

class ZSSKApp(App):
    def build(self):
        self.calculator=ShiftCalculator()
        self.data_file=os.path.join(self.user_data_dir,'data.json'); self.turnus_file=os.path.join(self.user_data_dir,'turnus.json'); self.emp_file=os.path.join(self.user_data_dir,'employee.json')
        self._ensure_files(); self.employee=self.load_employee()
        today=datetime.date.today(); self.cur_year=self.employee.get('cur_year',today.year); self.cur_month=self.employee.get('cur_month',today.month)
        self.theme_key=self.employee.get('theme','tmava'); self.theme=THEMES.get(self.theme_key, THEMES['tmava'])
        self.select_mode=False; self.selected_uids=set()
        root=BoxLayout(orientation='vertical',padding=dp(4),spacing=dp(3))
        with root.canvas.before: Color(*self.theme['bg']); self.bg=Rectangle(size=root.size,pos=root.pos); root.bind(size=lambda *a: (setattr(self.bg,'size',root.size), setattr(self.bg,'pos',root.pos)))
        header=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(108),spacing=dp(2))
        with header.canvas.before: Color(*self.theme['header_bg']); self.hbg=Rectangle(size=header.size,pos=header.pos); header.bind(size=lambda *a: (setattr(self.hbg,'size',header.size), setattr(self.hbg,'pos',header.pos)))
        nav=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6),padding=dp(6))
        b_prev=Button(text='◀',size_hint_x=None,width=dp(50),background_normal='',background_color=(0,0,0,0.18)); b_next=Button(text='▶',size_hint_x=None,width=dp(50),background_normal='',background_color=(0,0,0,0.18))
        self.lbl_month=Label(text='',font_size='17sp',bold=True,color=(1,1,1,1)); b_prev.bind(on_press=lambda x:self.shift_month(-1)); b_next.bind(on_press=lambda x:self.shift_month(1))
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next); header.add_widget(nav)
        actions_scroll=ScrollView(size_hint_y=None,height=dp(52),do_scroll_y=False,do_scroll_x=True,bar_width=0)
        actions=GridLayout(cols=5,spacing=dp(6),size_hint_x=None,height=dp(46),padding=(dp(4),0)); actions.bind(minimum_width=actions.setter('width'))
        for txt,key,fn in [('Mesiac','btn_mesiac',self.open_month_picker),('Turnus','btn_turnus',self.open_turnus_manager),('Stats','btn_stats',self.open_stats),('Imp/Exp','btn_export',self.open_export_menu),('⚙ Nastav','btn_settings',self.open_settings)]:
            b=Button(text=txt,size_hint_x=None,width=dp(92) if 'Nastav' not in txt else dp(98),background_normal='',background_color=self.theme[key],font_size='12sp'); b.bind(on_press=fn); actions.add_widget(b)
        actions_scroll.add_widget(actions); header.add_widget(actions_scroll); root.add_widget(header)
        self.kpi_box=BoxLayout(size_hint_y=None,height=dp(64),spacing=dp(4),padding=dp(4))
        self.lbl_kpi_main=Label(font_size='11sp',color=self.theme['text'],halign='left'); self.lbl_kpi_night=Label(font_size='11sp',color=self.theme['text'],halign='left'); self.lbl_kpi_meal=Label(font_size='11sp',color=self.theme['text'],halign='left')
        for l in [self.lbl_kpi_main,self.lbl_kpi_night,self.lbl_kpi_meal]: l.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width,None)))
        self.kpi_box.add_widget(self.lbl_kpi_main); self.kpi_box.add_widget(self.lbl_kpi_night); self.kpi_box.add_widget(self.lbl_kpi_meal); root.add_widget(self.kpi_box)
        self.lbl_info=Label(size_hint_y=None,height=dp(22),color=self.theme['subtext'],font_size='11sp'); root.add_widget(self.lbl_info)
        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None,padding=dp(2)); self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)
        bottom=BoxLayout(size_hint_y=None,height=dp(56),spacing=dp(6),padding=dp(3))
        self.btn_select=Button(text='✓ Výber',size_hint_x=None,width=dp(88),background_normal='',background_color=self.theme['btn_settings'],font_size='12sp')
        self.btn_select.bind(on_press=self.toggle_select_mode)
        b_add=Button(text='+ Pridať zmenu',background_normal='',background_color=self.theme['btn_primary'],font_size='14sp',bold=True)
        b_pay=Button(text='💰 Výplata',size_hint_x=None,width=dp(92),background_normal='',background_color=self.theme['btn_stats'],font_size='11sp')
        b_add.bind(on_press=lambda x:self.open_editor()); b_pay.bind(on_press=self.open_payroll)
        bottom.add_widget(self.btn_select); bottom.add_widget(b_add); bottom.add_widget(b_pay); root.add_widget(bottom)
        self.bulk_bar=BoxLayout(size_hint_y=None,height=dp(0),spacing=dp(6),padding=dp(3),opacity=0)
        self.btn_bulk_del=Button(text='🗑 Zmazať označené (0)',background_normal='',background_color=self.theme['btn_danger'],font_size='12sp')
        self.btn_bulk_month=Button(text='🗑 Vymazať mesiac',size_hint_x=None,width=dp(140),background_normal='',background_color=self.theme['btn_danger'],font_size='11sp')
        self.btn_bulk_cancel=Button(text='Zrušiť výber',size_hint_x=None,width=dp(100),background_normal='',background_color=self.theme['btn_settings'],font_size='11sp')
        self.btn_bulk_del.bind(on_press=self.delete_selected_confirm); self.btn_bulk_month.bind(on_press=self.delete_month_confirm); self.btn_bulk_cancel.bind(on_press=self.toggle_select_mode)
        self.bulk_bar.add_widget(self.btn_bulk_del); self.bulk_bar.add_widget(self.btn_bulk_month); self.bulk_bar.add_widget(self.btn_bulk_cancel); root.add_widget(self.bulk_bar)
        self.refresh(); return root

    def _ensure_files(self):
        os.makedirs(self.user_data_dir,exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file,'w',encoding='utf-8') as f: json.dump([],f)
        if not os.path.exists(self.turnus_file):
            with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump({"active":"Leto 2026","profiles":{"Leto 2026":[]}},f,ensure_ascii=False,indent=2)
        if not os.path.exists(self.emp_file):
            with open(self.emp_file,'w',encoding='utf-8') as f: json.dump({"name":"Miroslav Kurek","id":"20 814","role":"Rušňovodič","base_salary":"1484.00","theme":"tmava","cur_year":datetime.date.today().year,"cur_month":datetime.date.today().month},f,ensure_ascii=False,indent=2)

    def load_data(self):
        try:
            with open(self.data_file,encoding='utf-8') as f: d=json.load(f)
        except: d=[]
        out=[]
        for x in d:
            if not isinstance(x,dict): continue
            if 'date' not in x and 'datum' in x: x['date']=x.pop('datum')
            if 'shift_type' not in x:
                if 'zmena' in x: x['shift_type']=x.pop('zmena')
                else: x['shift_type']=''
            if 'note' not in x:
                if 'poznamka' in x: x['note']=x.pop('poznamka')
                else: x['note']=''
            for k in ['train_first','route_from','train_last','route_to','turnus','start','end','pc_start','pc_end','plan','pnp_start','pnp_end','meal_override','other_premiums']:
                if k not in x: x[k]=''
            if 'uid' not in x: x['uid']=str(uuid.uuid4())
            out.append(x)
        return out
    def save_data(self,data):
        with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
    def load_turnus_file(self):
        try:
            with open(self.turnus_file,encoding='utf-8') as f: j=json.load(f)
            if isinstance(j,dict) and 'profiles' in j: return j
            if isinstance(j,list): return {"active":"Leto 2026","profiles":{"Leto 2026":j}}
        except: pass
        return {"active":"Leto 2026","profiles":{"Leto 2026":[]}}
    def save_turnus_file(self,obj):
        with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
    def get_active_turnus(self):
        tf=self.load_turnus_file(); return tf['profiles'].get(tf.get('active'),[]), tf.get('active',''), tf
    def load_employee(self):
        try:
            with open(self.emp_file,encoding='utf-8') as f: return json.load(f)
        except: return {}
    def save_employee(self):
        self.employee['cur_year']=self.cur_year; self.employee['cur_month']=self.cur_month; self.employee['theme']=self.theme_key
        with open(self.emp_file,'w',encoding='utf-8') as fp: json.dump(self.employee,fp,ensure_ascii=False,indent=2)
    def month_key(self): return f"{self.cur_year:04d}-{self.cur_month:02d}"
    def get_auto_norm_minutes(self,y=None,m=None):
        y=y or self.cur_year; m=m or self.cur_month; days=calendar.monthrange(y,m)[1]; return days*308
    def get_auto_norm_str(self,y=None,m=None):
        mins=self.get_auto_norm_minutes(y,m); return f"{mins//60:02d}:{mins%60:02d}"
    def shift_month(self,d):
        m=self.cur_month+d; y=self.cur_year
        while m>12: m-=12; y+=1
        while m<1: m+=12; y-=1
        self.cur_year,self.cur_month=y,m; self.save_employee(); self.refresh()
    def toggle_select_mode(self,*a):
        self.select_mode=not self.select_mode
        if not self.select_mode:
            self.selected_uids.clear(); self.btn_select.text='✓ Výber'; self.btn_select.background_color=self.theme['btn_settings']; self.bulk_bar.height=dp(0); self.bulk_bar.opacity=0
        else:
            self.selected_uids=set(); self.btn_select.text='✕ Zrušiť'; self.btn_select.background_color=self.theme['btn_oprav']; self.bulk_bar.height=dp(52); self.bulk_bar.opacity=1
        self.refresh(); self.update_bulk_label()
    def toggle_one(self,uid):
        if uid in self.selected_uids: self.selected_uids.remove(uid)
        else: self.selected_uids.add(uid)
        self.update_bulk_label(); self.refresh()
    def update_bulk_label(self):
        cnt=len(self.selected_uids); self.btn_bulk_del.text=f'🗑 Zmazať označené ({cnt})' if cnt else '🗑 Zmazať označené (0)'
        if cnt: self.lbl_info.text=f'Označených {cnt} zmien'
        else:
            if self.select_mode: self.lbl_info.text='Označ zmeny - klik na riadok alebo ☐'
    def delete_selected_confirm(self,*a):
        if not self.selected_uids: self.show_info('Nič nie je označené.'); return
        cnt=len(self.selected_uids); pop=Popup(title='Potvrdiť zmazanie',size_hint=(0.86,None),height=dp(260),separator_color=self.theme['btn_danger'])
        box=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10)); box.add_widget(Label(text=f'Vymazať {cnt} označených zmien?\nNedá sa vrátiť.',halign='center',color=self.theme['text']))
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); b1=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b2=Button(text=f'Áno, zmazať {cnt}',background_normal='',background_color=self.theme['btn_danger'],bold=True)
        b1.bind(on_press=pop.dismiss)
        def do_del(*_):
            data=self.load_data(); new_data=[d for d in data if d.get('uid') not in self.selected_uids]; self.save_data(new_data); self.selected_uids.clear(); pop.dismiss(); self.toggle_select_mode(); self.show_info(f'Zmazaných {cnt}.')
        b2.bind(on_press=do_del); row.add_widget(b1); row.add_widget(b2); box.add_widget(row); pop.content=box; pop.open()
    def delete_month_confirm(self,*a):
        month=self.month_key(); data=[d for d in self.load_data() if d.get('date','').startswith(month)]; cnt=len(data)
        if cnt==0: self.show_info(f'Mesiac {month} je prázdny.'); return
        pop=Popup(title=f'Vymazať mesiac {month}?',size_hint=(0.90,None),height=dp(300),separator_color=self.theme['btn_danger'])
        box=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10)); box.add_widget(Label(text=f'Mesiac {month} má {cnt} záznamov.\nVymazať CELÝ mesiac?',halign='center',color=self.theme['text'],font_size='12sp'))
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); b1=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b2=Button(text=f'Vymazať {cnt}',background_normal='',background_color=self.theme['btn_danger'],bold=True)
        b1.bind(on_press=pop.dismiss)
        def do_del(*_):
            all_data=self.load_data(); keep=[d for d in all_data if not d.get('date','').startswith(month)]; self.save_data(keep); self.selected_uids.clear()
            if self.select_mode: self.toggle_select_mode()
            else: self.refresh()
            pop.dismiss(); self.show_info(f'Mesiac {month} vymazaný.')
        b2.bind(on_press=do_del); row.add_widget(b1); row.add_widget(b2); box.add_widget(row); pop.content=box; pop.open()
    def refresh(self):
        all_data=self.load_data(); month_data=[d for d in all_data if d.get('date','').startswith(self.month_key())]; month_data=sorted(month_data,key=lambda x:(x.get('date',''),x.get('start','')))
        self.lbl_month.text=f"{self.month_key()} • {len(month_data)} záznamov • Norma {self.get_auto_norm_str()}"
        self.grid.clear_widgets(); totals={"worked":0,"night":0,"sat":0,"sun":0,"hol":0,"pnp":0,"meal":0.0,"other":0.0,"overtime":0,"vacation":0}
        theme_colors=COLORS_LIGHT if self.theme_key=='zssk' else COLORS_DARK
        for s in month_data:
            calc=self.calculator.calculate_shift(s.get('date',''),s.get('start',''),s.get('end',''),s.get('plan',''),s.get('pc_start',''),s.get('pc_end',''),s.get('pnp_start',''),s.get('pnp_end',''),s.get('shift_type',''),s.get('meal_override',''),s.get('other_premiums',''))
            if calc:
                def p(h):
                    try: return int(h.split(':')[0])*60+int(h.split(':')[1]) if ':' in h else 0
                    except: return 0
                # pracovné + dovolenka sa ráta osobitne pre saldo
                if calc.get('vacation_minutes',0)>0: totals['vacation']+=calc['vacation_minutes']
                else:
                    totals['worked']+=p(calc.get('total_hours','0:00')) if calc.get('total_hours')!='-' else 0
                totals['night']+=p(calc.get('night_hours','0:00')); totals['sat']+=p(calc.get('saturday_hours','0:00')); totals['sun']+=p(calc.get('sunday_hours','0:00')); totals['hol']+=p(calc.get('holiday_hours','0:00')); totals['pnp']+=calc.get('pnp_minutes',0); totals['overtime']+=p(calc.get('overtime','0:00')); totals['meal']+=calc.get('meal_allowance',0.0); totals['other']+=calc.get('other_allowance',0.0)
            uid=s.get('uid'); typ=s.get('shift_type') or 'Štandardný výkon'; base=theme_colors.get(typ, theme_colors.get(typ.split('-')[0].strip(), (0.3,0.3,0.35,1)))
            # ak je dovolenka, zafarbíme zeleno
            if 'Dovolenka' in typ: base=COLORS_DARK['Dovolenka'] if self.theme_key=='tmava' else COLORS_LIGHT['Dovolenka']
            if calc and calc.get('is_holiday'): base=(min(base[0]+0.14,1),min(base[1]+0.14,1),min(base[2]+0.14,1),1)
            disp_date=format_date_display(s.get('date','')); td=s.get('turnus','') or '?'
            if self.select_mode:
                row=BoxLayout(orientation='horizontal',size_hint_y=None,height=dp(70),spacing=dp(4)); is_sel=uid in self.selected_uids
                cb=Button(text='☑' if is_sel else '☐',size_hint_x=None,width=dp(44),background_normal='',background_color=self.theme['btn_settings'] if not is_sel else self.theme['accent'],font_size='18sp'); cb.bind(on_press=lambda inst,u=uid: self.toggle_one(u))
                main=Button(size_hint_x=1,background_normal='',background_color=base,color=(1,1,1,1) if self.theme_key=='tmava' or 'Voľno' not in typ else (0.15,0.15,0.15,1),halign='left',valign='middle',padding=(dp(8),dp(4)),markup=True)
                st=s.get('start',''); en=s.get('end',''); note=s.get('note','')[:28]
                main.text=f"[b]{disp_date}[/b] TD {td} {typ[:18]}\n{st}-{en} {note}"; main.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width-dp(16),None))); main.bind(on_press=lambda inst,u=uid: self.toggle_one(u)); row.add_widget(cb); row.add_widget(main); self.grid.add_widget(row)
            else:
                btn=Button(size_hint_y=None,height=dp(70),background_normal='',background_color=base,color=(1,1,1,1) if self.theme_key=='tmava' or 'Voľno' not in typ and 'Dovolenka' not in typ else (0.1,0.1,0.1,1) if self.theme_key=='zssk' and 'Voľno' in typ else (1,1,1,1),halign='left',valign='middle',padding=(dp(10),dp(4)),markup=True)
                st=s.get('start',''); en=s.get('end',''); note=s.get('note','')[:30]
                tot=calc.get('total_hours','-') if calc else '-'; ni=calc.get('night_hours','-') if calc else '-'
                btn.text=f"[b]{disp_date}  TD {td}[/b] {typ[:20]}\n{st}-{en} | {tot} N:{ni} {note}"; btn.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width-dp(20),None))); btn.bind(on_press=lambda inst,u=uid: self.open_editor(u)); self.grid.add_widget(btn)
        def fmt(m): return f"{m//60:02d}:{m%60:02d}"
        auto_norm=self.get_auto_norm_minutes(); # saldo = (odprac + dovolenka) - norma
        effective=totals['worked']+totals['vacation']; saldo=effective-auto_norm; sign='+' if saldo>=0 else ''; saldo_str=f"{sign}{fmt(abs(saldo))}" if saldo!=0 else "0:00"
        self.lbl_kpi_main.text=f"Odprac: {fmt(totals['worked'])} Dov:{fmt(totals['vacation'])} / Norma {self.get_auto_norm_str()}\nSaldo: {saldo_str} {'nad' if saldo>0 else 'pod' if saldo<0 else 'OK'}"
        self.lbl_kpi_night.text=f"Nočná:{fmt(totals['night'])}\nSo:{fmt(totals['sat'])} Ne:{fmt(totals['sun'])}"
        self.lbl_kpi_meal.text=f"Sviatok:{fmt(totals['hol'])} PNP:{fmt(totals['pnp'])}\nStravné:{totals['meal']:.2f}€"
        self.current_totals=totals; self.current_saldo=saldo
        if not self.select_mode: self.lbl_info.text=f'{len(month_data)} záznamov • dátum D-M-R • TD zobrazený • klik pre úpravu'

    def open_editor(self,uid=None):
        if self.select_mode:
            if uid: self.toggle_one(uid)
            return
        all_data=self.load_data(); edit=None
        if uid:
            for d in all_data:
                if d.get('uid')==uid: edit=d; break
        is_new=edit is None
        if is_new: edit={"uid":str(uuid.uuid4()),"date":f"{self.month_key()}-01","shift_type":"Štandardný výkon","train_first":"","route_from":"","train_last":"","route_to":"","turnus":"","start":"","end":"","pc_start":"","pc_end":"","plan":"","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":""}
        popup=Popup(title='Upraviť' if not is_new else 'Pridať zmenu',size_hint=(0.96,0.92),separator_color=self.theme['accent'],auto_dismiss=False)
        root=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(8)); scroll=ScrollView(); form=GridLayout(cols=1,spacing=dp(8),size_hint_y=None,padding=dp(4)); form.bind(minimum_height=form.setter('height'))
        def add_row(lbl,widget):
            b=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(66),spacing=dp(2)); b.add_widget(Label(text=lbl,size_hint_y=None,height=dp(18),halign='left',font_size='11sp',color=self.theme['subtext'])); b.add_widget(widget); form.add_widget(b)
        inp_date=TextInput(text=edit.get('date',''),hint_text='YYYY-MM-DD interne, zobrazí sa ako D-M-R',multiline=False,size_hint_y=None,height=dp(40),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); add_row('Dátum (uložené YYYY-MM-DD)',inp_date)
        sp_type=Spinner(text=edit.get('shift_type') or 'Štandardný výkon',values=SHIFT_TYPES,size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['row_bg']); add_row('Mzdový druh / Typ',sp_type)
        row_t=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4)); it=TextInput(text=edit.get('turnus',''),hint_text='TD napr. 5',multiline=False,size_hint_x=0.25,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); itf=TextInput(text=edit.get('train_first',''),hint_text='Vlak 1.',multiline=False,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); itl=TextInput(text=edit.get('train_last',''),hint_text='Vlak posl.',multiline=False,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); row_t.add_widget(it); row_t.add_widget(itf); row_t.add_widget(itl); add_row('Turnusový deň TD + Vlaky',row_t)
        row_r=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4)); irf=TextInput(text=edit.get('route_from',''),hint_text='Z',multiline=False,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); irt=TextInput(text=edit.get('route_to',''),hint_text='Do',multiline=False,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); row_r.add_widget(irf); row_r.add_widget(irt); add_row('Trať Z → Do',row_r)
        def time_row(label,key):
            r=BoxLayout(size_hint_y=None,height=dp(40),spacing=dp(4)); inp=TextInput(text=edit.get(key,''),hint_text='HH:MM',multiline=False,background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); btn=Button(text='🕒',size_hint_x=None,width=dp(44),background_normal='',background_color=self.theme['btn_export']); btn.bind(on_press=lambda *_: TimePickerPopup(initial=inp.text or "08:00",callback=lambda v:setattr(inp,'text',v)).open()); r.add_widget(inp); r.add_widget(btn); add_row(label,r); return inp
        ins=time_row('Nástup','start'); ine=time_row('Koniec','end'); ipl=time_row('Plán FPČ','plan'); ipcs=time_row('PC zač','pc_start'); ipce=time_row('PC koniec','pc_end'); ipnps=time_row('PNP zač','pnp_start'); ipnpe=time_row('PNP koniec','pnp_end')
        im=TextInput(text=edit.get('meal_override',''),hint_text='prázdne=auto',multiline=False,size_hint_y=None,height=dp(38),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); add_row('Stravné override €',im)
        io=TextInput(text=edit.get('other_premiums',''),hint_text='Iné €',multiline=False,size_hint_y=None,height=dp(38),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); add_row('Iné príplatky €',io)
        ino=TextInput(text=edit.get('note',''),multiline=True,size_hint_y=None,height=dp(66),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); add_row('Poznámka',ino)
        lbl_prev=Label(text='Náhľad: -',size_hint_y=None,height=dp(44),color=self.theme['subtext'],font_size='11sp'); form.add_widget(lbl_prev)
        def upd(*_):
            c=self.calculator.calculate_shift(inp_date.text,ins.text,ine.text,ipl.text,ipcs.text,ipce.text,ipnps.text,ipnpe.text,sp_type.text,im.text,io.text)
            if c: lbl_prev.text=f"Odprac:{c['total_hours']} Dov:{c.get('vacation_minutes',0)//60:02d}:{(c.get('vacation_minutes',0)%60):02d} Nočná:{c['night_hours']} Strava:{c['meal_allowance']}€"
        for w in [inp_date,ins,ine,ipl,ipcs,ipce,ipnps,ipnpe,im,io]: w.bind(text=lambda *a: upd()); sp_type.bind(text=lambda *a: upd()); upd()
        scroll.add_widget(form); root.add_widget(scroll)
        btns=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6)); bc=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); bd=Button(text='Zmazať',background_normal='',background_color=(0.78,0.22,0.22,1),size_hint_x=None,width=dp(80)); bs=Button(text='Uložiť',background_normal='',background_color=self.theme['btn_save'],bold=True)
        bc.bind(on_press=popup.dismiss)
        def do_del(*_):
            if not is_new: nd=[d for d in all_data if d.get('uid')!=uid]; self.save_data(nd); self.refresh(); popup.dismiss()
        def do_save(*_):
            try: datetime.datetime.strptime(inp_date.text,"%Y-%m-%d")
            except: self.show_info('Zlý dátum, použite YYYY-MM-DD napr. 2026-06-15'); return
            ns={"uid":edit['uid'],"date":inp_date.text.strip(),"shift_type":sp_type.text,"train_first":itf.text,"route_from":irf.text,"train_last":itl.text,"route_to":irt.text,"turnus":it.text,"start":ins.text,"end":ine.text,"pc_start":ipcs.text,"pc_end":ipce.text,"plan":ipl.text,"pnp_start":ipnps.text,"pnp_end":ipnpe.text,"meal_override":im.text,"other_premiums":io.text,"note":ino.text}
            if is_new: all_data.append(ns)
            else:
                for i,d in enumerate(all_data):
                    if d.get('uid')==uid: all_data[i]=ns; break
            self.save_data(sorted(all_data,key=lambda x:(x.get('date',''),x.get('start','')))); self.refresh(); popup.dismiss()
        bd.bind(on_press=do_del); bs.bind(on_press=do_save); btns.add_widget(bc); 
        if not is_new: btns.add_widget(bd)
        btns.add_widget(bs); root.add_widget(btns); popup.content=root; popup.open()

    # ---------- TURNUS - OPRAVENÝ GENERÁTOR S HODINAMI ----------
    def open_turnus_manager(self,*a):
        prof_list, active_name, full = self.get_active_turnus()
        popup=Popup(title=f'Turnus - aktívny: {active_name}',size_hint=(0.96,0.93),separator_color=self.theme['btn_turnus'],auto_dismiss=False)
        root=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10)); scroll=ScrollView(size_hint_y=1); form=GridLayout(cols=1,spacing=dp(10),size_hint_y=None,padding=dp(2)); form.bind(minimum_height=form.setter('height'))
        box_prof=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(90),spacing=dp(4)); box_prof.add_widget(Label(text='Aktívny profil turnusu',size_hint_y=None,height=dp(18),font_size='11sp',color=self.theme['subtext'])); row_prof=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(6)); sp_prof=Spinner(text=active_name,values=list(full.get('profiles',{}).keys()) or [active_name],size_hint_x=0.65,background_normal='',background_color=self.theme['row_bg']); b_set=Button(text='Nastaviť',size_hint_x=0.35,background_normal='',background_color=self.theme['btn_turnus'])
        def set_active(*_): full['active']=sp_prof.text; self.save_turnus_file(full); popup.title=f'Turnus - aktívny: {sp_prof.text}'; self.show_info(f'Aktívny: {sp_prof.text}')
        b_set.bind(on_press=set_active); row_prof.add_widget(sp_prof); row_prof.add_widget(b_set); box_prof.add_widget(row_prof); box_prof.add_widget(Label(text=f'Počet šablón: {len(prof_list)}',size_hint_y=None,height=dp(18),font_size='10sp',color=self.theme['subtext'])); form.add_widget(box_prof)
        box_td=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(72),spacing=dp(2)); box_td.add_widget(Label(text='TD - turnusový deň na 1. deň v mesiaci (napr. 1)',size_hint_y=None,height=dp(20),font_size='11sp',color=self.theme['text'])); inp_td=TextInput(text='1',multiline=False,size_hint_y=None,height=dp(40),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); box_td.add_widget(inp_td); form.add_widget(box_td)
        box_len=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(72),spacing=dp(2)); box_len.add_widget(Label(text='Dĺžka turnusu - počet dní cyklu (napr. 8, 12)',size_hint_y=None,height=dp(20),font_size='11sp',color=self.theme['text'])); inp_len=TextInput(text='8',multiline=False,size_hint_y=None,height=dp(40),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); box_len.add_widget(inp_len); form.add_widget(box_len)
        box_ie=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(110),spacing=dp(6)); box_ie.add_widget(Label(text='Import / Export turnusu (rieši prázdninový turnus)',size_hint_y=None,height=dp(20),font_size='11sp',bold=True,color=self.theme['text'])); row_ie=BoxLayout(size_hint_y=None,height=dp(42),spacing=dp(6)); b_imp=Button(text='📥 Import',background_normal='',background_color=self.theme['btn_export'],font_size='11sp'); b_exp=Button(text='📤 Export',background_normal='',background_color=self.theme['btn_stats'],font_size='11sp')
        def do_imp(*_):
            def on_pick(path):
                try:
                    with open(path,encoding='utf-8') as f: data=json.load(f); tf=self.load_turnus_file(); name=os.path.splitext(os.path.basename(path))[0]
                    if isinstance(data,list): tf['profiles'][name]=data; tf['active']=name
                    elif isinstance(data,dict) and 'profiles' in data: tf=data
                    else: self.show_info('Neplatný formát'); return
                    self.save_turnus_file(tf); self.show_info(f'Importovaný profil {name}')
                except Exception as e: self.show_info(f'Chyba: {e}')
            FilePickerPopup(self.get_download_dirs(), on_pick).open()
        def do_exp(*_):
            tf=self.load_turnus_file(); out=os.path.join(self.user_data_dir,f"turnus_{tf.get('active','profil')}.json")
            try:
                with open(out,'w',encoding='utf-8') as f: json.dump(tf,f,ensure_ascii=False,indent=2); self.show_info(f'Export: {out}')
            except Exception as e: self.show_info(f'Chyba: {e}')
        b_imp.bind(on_press=do_imp); b_exp.bind(on_press=do_exp); row_ie.add_widget(b_imp); row_ie.add_widget(b_exp); box_ie.add_widget(row_ie); box_ie.add_widget(Label(text='Po prázdninách importuj nový, starý ostane uložený.',size_hint_y=None,height=dp(24),font_size='10sp',color=self.theme['subtext'])); form.add_widget(box_ie)
        lbl=Label(text='',size_hint_y=None,height=dp(20),font_size='11sp',color=self.theme['subtext']); form.add_widget(lbl); scroll.add_widget(form); root.add_widget(scroll)
        btns=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(6)); bc=Button(text='Zavrieť',background_normal='',background_color=self.theme['btn_settings']); bg=Button(text='⚙ Generovať mesiac',background_normal='',background_color=self.theme['btn_oprav'],bold=True); bc.bind(on_press=popup.dismiss)
        def gen(*_):
            try: std=int(inp_td.text); tl=int(inp_len.text)
            except: lbl.text='Zadaj čísla'; return
            data=self.load_data(); _, an, full2=self.get_active_turnus(); td=full2['profiles'].get(full2['active'],[]); dim=calendar.monthrange(self.cur_year,self.cur_month)[1]; keep=[d for d in data if not d.get('date','').startswith(self.month_key())]; nm=[]
            for day in range(1,dim+1):
                ds=f"{self.cur_year:04d}-{self.cur_month:02d}-{day:02d}"; ctd=((std-1+day-1)%tl)+1; dob=datetime.date(self.cur_year,self.cur_month,day); is_h=self.calculator.is_slovak_holiday(dob); tgt="Sv" if is_h else ["Po","Ut","St","Št","Pi","So","Ne"][dob.weekday()]; m=None
                for t in td:
                    if str(t.get('td'))==str(ctd) and tgt in t.get('days',[]): m=t; break
                if m:
                    # použije šablónu z profilu
                    sh={"uid":str(uuid.uuid4()),"date":ds,"shift_type":m.get('shift_type','Štandardný výkon'),"train_first":m.get('train_first',''),"route_from":m.get('route_from',''),"train_last":m.get('train_last',''),"route_to":m.get('route_to',''),"turnus":str(ctd),"start":m.get('start',''),"end":m.get('end',''),"pc_start":m.get('pc_start',''),"pc_end":m.get('pc_end',''),"plan":m.get('plan',''),"pnp_start":m.get('pnp_start',''),"pnp_end":m.get('pnp_end',''),"meal_override":m.get('meal_override',''),"other_premiums":m.get('other_premiums',''),"note":""}
                else:
                    typ=PATTERN[(day-1)%len(PATTERN)]
                    if typ=='Voľno':
                        sh={"uid":str(uuid.uuid4()),"date":ds,"shift_type":"T.V. (Turnus voľno)","train_first":"T.V.","route_from":"","train_last":"T.V.","route_to":"","turnus":str(ctd),"start":"","end":"","pc_start":"","pc_end":"","plan":"","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":typ}
                    else:
                        s,e,p=SHIFT_TIMES[typ]
                        sh={"uid":str(uuid.uuid4()),"date":ds,"shift_type":"Štandardný výkon","train_first":"","route_from":"","train_last":"","route_to":"","turnus":str(ctd),"start":s,"end":e,"pc_start":"","pc_end":"","plan":p,"pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":typ}
                nm.append(sh)
            keep.extend(nm); self.save_data(keep); self.refresh(); popup.dismiss(); self.show_info(f'Vygenerovaných {len(nm)} dní s hodinami (Ranná 06-14, Poobedná 14-22, Nočná 22-06)')
        bg.bind(on_press=gen); btns.add_widget(bc); btns.add_widget(bg); root.add_widget(btns); popup.content=root; popup.open()
    def open_turnus_generator(self,*a): self.open_turnus_manager(*a)
    def get_download_dirs(self):
        ds=[self.user_data_dir]
        for p in ["/storage/emulated/0/Download","/sdcard/Download","/storage/emulated/0/Documents","./"]:
            if os.path.exists(p): ds.append(p)
        return ds
    def open_export_menu(self,*a):
        pop=Popup(title='Import / Export zmien',size_hint=(0.94,None),height=dp(460),separator_color=self.theme['accent']); box=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(12))
        for txt,fn in [('Export CSV (mesiac)',self.export_csv),('Export JSON záloha',self.export_json),('Report TXT',self.export_report),('Import zmien z JSON',self.import_shifts_picker)]:
            b=Button(text=txt,size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_export'],font_size='12sp'); b.bind(on_press=lambda inst,f=fn: f()); box.add_widget(b)
        box.add_widget(Label(text='Import/Export turnusu je v karte Turnus',size_hint_y=None,height=dp(24),font_size='10sp',color=self.theme['subtext']))
        bc=Button(text='Zavrieť',size_hint_y=None,height=dp(40),background_normal='',background_color=self.theme['btn_settings']); bc.bind(on_press=pop.dismiss); box.add_widget(bc); pop.content=box; pop.open()
    def import_shifts_picker(self,*a):
        def on_pick(p):
            try:
                with open(p,encoding='utf-8') as f: data=json.load(f)
                if isinstance(data,dict) and 'shifts_data' in data: ns=data['shifts_data']
                elif isinstance(data,list): ns=data
                else: self.show_info('Neznámy formát'); return
                ex=self.load_data(); ad=0
                for s in ns:
                    if not isinstance(s,dict) or 'date' not in s: continue
                    if 'uid' not in s: s['uid']=str(uuid.uuid4())
                    if not any(e['date']==s['date'] and e.get('start','')==s.get('start','') for e in ex): ex.append(s); ad+=1
                self.save_data(sorted(ex,key=lambda x:x.get('date',''))); self.refresh(); self.show_info(f'Import: {ad} nových z {os.path.basename(p)}')
            except Exception as e: self.show_info(f'Chyba: {e}')
        FilePickerPopup(self.get_download_dirs(), on_pick).open()
    def export_csv(self,*a):
        fn=f"zsskzmeny_{self.month_key()}.csv"; out=os.path.join(self.user_data_dir,fn)
        try:
            with open(out,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['datum','zobraz_datum','TD','mzdovy_druh','nastup','koniec','celkom','nocna','poznamka'])
                for d in sorted(self.load_data(),key=lambda x:x.get('date','')):
                    if not d.get('date','').startswith(self.month_key()): continue
                    c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                    w.writerow([d.get('date'),format_date_display(d.get('date','')),d.get('turnus'),d.get('shift_type'),d.get('start'),d.get('end'),c.get('total_hours') if c else '',c.get('night_hours') if c else '',d.get('note','')])
            self.show_info(f'CSV exportovaný:\n{out}\nOtvor cez file manager v telefóne.')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def export_json(self,*a):
        fn=f"zsskzmeny_all_{datetime.date.today().isoformat()}.json"; out=os.path.join(self.user_data_dir,fn)
        try:
            with open(out,'w',encoding='utf-8') as f: json.dump({"employee_info":self.employee,"shifts_data":self.load_data(),"turnus":self.load_turnus_file()},f,ensure_ascii=False,indent=2); self.show_info(f'JSON záloha:\n{out}')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def export_report(self,*a):
        fn=f"report_{self.month_key()}.txt"; out=os.path.join(self.user_data_dir,fn)
        try:
            lines=[f"ZÁZNAM {self.month_key()} Norma {self.get_auto_norm_str()} Saldo {getattr(self,'current_saldo',0)//60:+d}:{(abs(getattr(self,'current_saldo',0))%60):02d}","="*60]
            for d in sorted([x for x in self.load_data() if x.get('date','').startswith(self.month_key())],key=lambda x:x.get('date','')):
                c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                lines.append(f"{format_date_display(d.get('date',''))} TD {d.get('turnus','?'):2} {d.get('shift_type')[:22]:22} {d.get('start',''):5}-{d.get('end',''):5} {c.get('total_hours','-') if c else '-':5} {d.get('note','')}")
            with open(out,'w',encoding='utf-8') as f: f.write("\n".join(lines)); self.show_info(f'Report:\n{out}')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def open_month_picker(self,*a):
        temp=[self.cur_year]; pop=Popup(title='Vyber mesiac',size_hint=(0.92,None),height=dp(460),separator_color=self.theme['accent']); box=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        yb=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); bm=Button(text='- rok',size_hint_x=None,width=dp(74),background_normal='',background_color=self.theme['btn_settings']); bp=Button(text='+ rok',size_hint_x=None,width=dp(74),background_normal='',background_color=self.theme['btn_settings']); ly=Label(text=str(temp[0]),font_size='17sp',bold=True,color=self.theme['text'])
        def ch(d): temp[0]+=d; ly.text=str(temp[0])
        bm.bind(on_press=lambda x:ch(-1)); bp.bind(on_press=lambda x:ch(1)); yb.add_widget(bm); yb.add_widget(ly); yb.add_widget(bp); box.add_widget(yb)
        grid=GridLayout(cols=3,spacing=dp(6),size_hint_y=1,row_default_height=dp(48),row_force_default=True)
        for m in range(1,13):
            is_cur=(m==self.cur_month and temp[0]==self.cur_year); bg=self.theme['accent'] if is_cur else self.theme['row_bg']
            b=Button(text=f"{m:02d}\n{calendar.month_abbr[m]}",background_normal='',background_color=bg,font_size='12sp')
            def cb(mm): return lambda inst: (setattr(self,'cur_year',temp[0]), setattr(self,'cur_month',mm), self.save_employee(), pop.dismiss(), self.refresh())
            b.bind(on_press=cb(m)); grid.add_widget(b)
        box.add_widget(grid); bc=Button(text='Zavrieť',size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['btn_settings']); bc.bind(on_press=pop.dismiss); box.add_widget(bc); pop.content=box; pop.open()
    def open_stats(self,*a):
        data=[d for d in self.load_data() if d.get('date','').startswith(self.month_key())]; cnt={}
        for d in data: k=d.get('shift_type','bez') or 'bez'; cnt[k]=cnt.get(k,0)+1
        pop=Popup(title=f'Stats {self.month_key()} Norma {self.get_auto_norm_str()}',size_hint=(0.92,None),height=dp(460)); root=BoxLayout(orientation='vertical',padding=dp(10),spacing=dp(6)); sc=ScrollView(); gl=GridLayout(cols=1,spacing=dp(3),size_hint_y=None); gl.bind(minimum_height=gl.setter('height'))
        if not cnt: gl.add_widget(Label(text='Žiadne dáta',size_hint_y=None,height=dp(30),color=self.theme['text']))
        else:
            for k in sorted(cnt): r=BoxLayout(size_hint_y=None,height=dp(34),spacing=dp(6)); r.add_widget(Label(text=k,size_hint_x=0.65,halign='left',font_size='11sp',color=self.theme['text'])); r.add_widget(Label(text=f"{cnt[k]}x",size_hint_x=0.35,halign='right',font_size='11sp',color=self.theme['subtext'])); gl.add_widget(r)
            saldo=getattr(self,'current_saldo',0); gl.add_widget(Label(text=f"Celkom {len(data)} zmien, saldo {saldo//60:+d}h {abs(saldo)%60:02d}m",size_hint_y=None,height=dp(32),bold=True,color=self.theme['text']))
        sc.add_widget(gl); root.add_widget(sc); b=Button(text='OK',size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['btn_stats']); b.bind(on_press=pop.dismiss); root.add_widget(b); pop.content=root; pop.open()
    def open_payroll(self,*a):
        t=self.current_totals; base=float(str(self.employee.get('base_salary','1484')).replace(',','.')) if self.employee.get('base_salary') else 1484.0; saldo=getattr(self,'current_saldo',0)
        try: auto=self.get_auto_norm_minutes(); hod=base/(auto/60) if auto else 9.27
        except: hod=9.27
        wh=t.get('worked',0)/60.0; vh=t.get('vacation',0)/60.0; nh=t.get('night',0)/60.0; sh=t.get('sat',0)/60.0; suh=t.get('sun',0)/60.0; hh=t.get('hol',0)/60.0
        sb=(wh+vh)*hod; sn=nh*2.10; ss=sh*2.63; su=suh*5.26; shol=hh*13.88; hr=sb+sn+ss+su+shol+t.get('other',0)+65; ci=hr*0.73; kv=ci+t.get('meal',0)
        pop=Popup(title=f'Výplata {self.month_key()}',size_hint=(0.92,None),height=dp(500)); box=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(4))
        for txt in [f"Norma {self.get_auto_norm_str()} = {calendar.monthrange(self.cur_year,self.cur_month)[1]} dní × 5:08",f"Odprac+Dov: {(wh+vh):.1f}h × {hod:.2f} = {sb:.2f}€ (Dov {vh:.1f}h = 5:08/deň)",f"Nočné: {sn:.2f}€",f"So+Ne: {(ss+su):.2f}€",f"Sviatok: {shol:.2f}€",f"Iné+65: {t.get('other',0)+65:.2f}€","---",f"HRUBÁ: {hr:.2f}€",f"ČISTÁ ~73%: {ci:.2f}€",f"Stravné: {t.get('meal',0):.2f}€",f"SPOLU: {kv:.2f}€",f"Saldo k norme: {saldo//60:+d}:{(abs(saldo)%60):02d}"]:
            box.add_widget(Label(text=txt,font_size='12sp',halign='left',size_hint_y=None,height=dp(24),color=self.theme['text']))
        b=Button(text='Zavrieť',size_hint_y=None,height=dp(40),background_normal='',background_color=self.theme['btn_settings']); b.bind(on_press=pop.dismiss); box.add_widget(b); pop.content=box; pop.open()
    def open_settings(self,*a):
        pop=Popup(title='⚙ Nastavenia',size_hint=(0.94,0.94),separator_color=self.theme['accent']); root=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(10)); scroll=ScrollView(); form=GridLayout(cols=1,spacing=dp(8),size_hint_y=None,padding=dp(2)); form.bind(minimum_height=form.setter('height'))
        form.add_widget(Label(text='Farebná schéma',size_hint_y=None,height=dp(20),bold=True,color=self.theme['text'],halign='left'))
        sp_theme=Spinner(text=THEMES[self.theme_key]['name'],values=[v['name'] for v in THEMES.values()],size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['row_bg']); form.add_widget(sp_theme)
        auto_str=self.get_auto_norm_str(); days=calendar.monthrange(self.cur_year,self.cur_month)[1]
        form.add_widget(Label(text=f'Norma pre {self.month_key()}: {days} dní × 5:08 = {auto_str}\nDovolenka sa počíta ako 5:08/deň a znižuje normu.',size_hint_y=None,height=dp(44),font_size='11sp',color=self.theme['subtext'],halign='left'))
        inputs={}
        for lbl,key,defv in [('Meno','name',''),('Os. číslo','id',''),('Základná mzda €','base_salary','1484.00')]:
            b=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(62),spacing=dp(2)); b.add_widget(Label(text=lbl,size_hint_y=None,height=dp(18),font_size='11sp',color=self.theme['subtext'],halign='left')); ti=TextInput(text=str(self.employee.get(key,defv)),multiline=False,size_hint_y=None,height=dp(38),background_color=self.theme['input_bg'],foreground_color=self.theme['input_fg']); inputs[key]=ti; b.add_widget(ti); form.add_widget(b)
        form.add_widget(Label(text='Údržba dát',size_hint_y=None,height=dp(24),bold=True,color=self.theme['text']))
        b_oprav=Button(text='Oprav prázdne typy (PATTERN)',size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['btn_oprav'],font_size='11sp')
        def do_oprav(*_):
            data=self.load_data(); ch=0
            for d in data:
                if d.get('date','').startswith(self.month_key()) and not d.get('shift_type'):
                    try: day=int(d['date'].split('-')[2]); d['shift_type']=PATTERN[(day-1)%len(PATTERN)]; ch+=1
                    except: pass
            self.save_data(data); self.refresh(); self.show_info(f'Opravených {ch} záznamov')
        b_oprav.bind(on_press=do_oprav); form.add_widget(b_oprav)
        form.add_widget(Label(text='Nebezpečná zóna',size_hint_y=None,height=dp(28),bold=True,color=self.theme['btn_danger']))
        b_del_month=Button(text=f'🗑 Vymazať celý mesiac {self.month_key()}',size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_danger'],font_size='11sp')
        b_del_month.bind(on_press=lambda *x: (pop.dismiss(), self.delete_month_confirm())); form.add_widget(b_del_month)
        b_del_all=Button(text='🗑 Vymazať VŠETKY zmeny',size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_danger'],font_size='11sp')
        def del_all_confirm(*_):
            pop.dismiss()
            p2=Popup(title='Vymazať všetko?',size_hint=(0.90,None),height=dp(300),separator_color=self.theme['btn_danger']); b=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10)); b.add_widget(Label(text='Vymaže sa celá databáza zmien.\nTurnusy ostanú.',halign='center',color=self.theme['text']))
            r=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); b1=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b2=Button(text='Áno',background_normal='',background_color=self.theme['btn_danger'],bold=True)
            b1.bind(on_press=p2.dismiss)
            def do_wipe(*_):
                self.save_data([]); self.refresh(); p2.dismiss(); self.show_info('Vymazané.')
            b2.bind(on_press=do_wipe); r.add_widget(b1); r.add_widget(b2); b.add_widget(r); p2.content=b; p2.open()
        b_del_all.bind(on_press=del_all_confirm); form.add_widget(b_del_all)
        b_reset=Button(text='♻ Reset aplikácie',size_hint_y=None,height=dp(48),background_normal='',background_color=(0.55,0.05,0.05,1),font_size='11sp',bold=True)
        def reset_confirm(*_):
            pop.dismiss()
            p3=Popup(title='RESET',size_hint=(0.92,None),height=dp(340),separator_color=(0.55,0.05,0.05,1)); b=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10)); b.add_widget(Label(text='Vymaže zmeny, turnusy, nastavenia.\nPokračovať?',halign='left',color=self.theme['text'],font_size='12sp'))
            r=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(8)); b1=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b2=Button(text='RESET',background_normal='',background_color=(0.55,0.05,0.05,1),bold=True)
            b1.bind(on_press=p3.dismiss)
            def do_reset(*_):
                with open(self.data_file,'w',encoding='utf-8') as f: json.dump([],f)
                with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump({"active":"Leto 2026","profiles":{"Leto 2026":[]}},f,ensure_ascii=False,indent=2)
                theme=self.theme_key; self.employee={"name":"","id":"","base_salary":"1484.00","theme":theme,"cur_year":datetime.date.today().year,"cur_month":datetime.date.today().month}; self.save_employee(); self.cur_year=datetime.date.today().year; self.cur_month=datetime.date.today().month; self.selected_uids.clear(); self.select_mode=False; self.refresh(); p3.dismiss(); self.show_info('Reset hotový.')
            b2.bind(on_press=do_reset); r.add_widget(b1); r.add_widget(b2); b.add_widget(r); p3.content=b; p3.open()
        b_reset.bind(on_press=reset_confirm); form.add_widget(b_reset)
        scroll.add_widget(form); root.add_widget(scroll)
        btns=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6)); bc=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); bs=Button(text='Uložiť',background_normal='',background_color=self.theme['btn_save'],bold=True)
        def save(*_):
            for k,v in THEMES.items():
                if v['name']==sp_theme.text: self.theme_key=k; break
            for k,ti in inputs.items(): self.employee[k]=ti.text
            self.save_employee(); pop.dismiss(); self.show_info(f'Uložené. Téma {THEMES[self.theme_key]["name"]} po reštarte.')
        bc.bind(on_press=pop.dismiss); bs.bind(on_press=save); btns.add_widget(bc); btns.add_widget(bs); root.add_widget(btns); pop.content=root; pop.open()
    def show_info(self,msg):
        p=Popup(title='Info',size_hint=(0.86,None),height=dp(320)); b=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); b.add_widget(Label(text=msg,halign='center',color=self.theme['text'],font_size='12sp')); btn=Button(text='OK',size_hint_y=None,height=dp(42),background_normal='',background_color=self.theme['btn_settings']); btn.bind(on_press=p.dismiss); b.add_widget(btn); p.content=b; p.open()

if __name__=='__main__': ZSSKApp().run()
