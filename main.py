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
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

# ---------- TÉMY ----------
THEMES = {
    'tmava': {
        'name': 'Tmavá (aktuálna)',
        'bg': (0.07,0.09,0.14,1),
        'header_bg': (0.12,0.16,0.22,1),
        'card_bg': (0.14,0.18,0.26,1),
        'row_bg': (0.20,0.20,0.24,1),
        'text': (0.96,0.97,0.99,1),
        'subtext': (0.58,0.66,0.78,1),
        'accent': (0.15,0.55,0.85,1),
        'btn_mesiac': (0.32,0.34,0.38,1),
        'btn_turnus': (0.55,0.32,0.18,1),
        'btn_stats': (0.18,0.45,0.32,1),
        'btn_export': (0.15,0.38,0.68,1),
        'btn_oprav': (0.65,0.42,0.12,1),
        'btn_settings': (0.35,0.35,0.38,1),
        'btn_primary': (0,0.42,0.78,1),
        'btn_save': (0.12,0.55,0.25,1),
    },
    'zssk': {
        'name': 'ZSSK / PROSOFT svetlá',
        # z tvojho 1. obrázka: oranžový header #E65100, biela plocha
        'bg': (0.96,0.96,0.96,1),
        'header_bg': (0.90,0.31,0.0,1),  # #E64F00
        'card_bg': (1,1,1,1),
        'row_bg': (0.93,0.93,0.95,1),
        'text': (0.13,0.13,0.15,1),
        'subtext': (0.45,0.48,0.53,1),
        'accent': (0.90,0.31,0.0,1),
        'btn_mesiac': (0.35,0.35,0.38,1),
        'btn_turnus': (0.90,0.31,0.0,1),
        'btn_stats': (0.20,0.60,0.30,1),
        'btn_export': (0.12,0.42,0.75,1),
        'btn_oprav': (0.92,0.60,0.0,1),
        'btn_settings': (0.45,0.45,0.48,1),
        'btn_primary': (0.90,0.31,0.0,1),
        'btn_save': (0.18,0.55,0.22,1),
    }
}

SHIFT_TYPES = [
    "Štandardný výkon","T.V. (Turnus voľno)","0006-Hodi.povinn.škol.a","0007-Hod.nariadenej lek.prehliad.",
    "0011-Nevysporiad.hod.nad FPČ","0014-Hodiny školenia","2125-Príplatok za real. AP-1","2160-Prípl.za sť.nástup a.",
    "2190-Prípl.sťaž.pr.režim","3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r.","3120-Štúdium popri zamest.",
    "3191-Náhrada za vyšetrenie","3440-Náhr.m.Ost.prek.nep","4181-Náhr.za pr.poh.v p.","8000-Nemoc","8020-OČR"
]
COLORS_DARK = {'Štandardný výkon':(0.15,0.55,0.85,1),'T.V. (Turnus voľno)':(0.25,0.30,0.35,1),'Ranná':(0.15,0.55,0.85,1),'Poobedná':(0.85,0.55,0.15,1),'Nočná':(0.32,0.32,0.82,1),'Voľno':(0.25,0.65,0.25,1),'Dovolenka':(0.75,0.45,0.85,1)}
COLORS_LIGHT = {'Štandardný výkon':(0.12,0.42,0.75,1),'T.V. (Turnus voľno)':(0.75,0.75,0.78,1),'Ranná':(0.12,0.42,0.75,1),'Poobedná':(0.90,0.45,0.05,1),'Nočná':(0.25,0.25,0.70,1),'Voľno':(0.20,0.60,0.28,1),'Dovolenka':(0.70,0.40,0.80,1)}
PATTERN = ['Ranná','Ranná','Poobedná','Poobedná','Nočná','Nočná','Voľno','Voľno']
SK_SVIATKY_FIX = {"01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"}

class ShiftCalculator:
    def __init__(self): self.rates={"meal_a":9.30,"meal_b":13.80,"meal_c":21.00}
    def parse_time(self,s):
        try:
            if not s or s.strip() in ("","-"): return None
            p=s.replace(".",":").split(":"); h=int(p[0]); m=int(p[1]) if len(p)>1 else 0
            return datetime.time(h,m)
        except: return None
    def get_easter_date(self,year):
        a=year%19; b=year//100; c=year%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
        h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; L=(32+2*e+2*i-h-k)%7; m=(a+11*h+22*L)//451; month=(h+L-7*m+114)//31; day=((h+L-7*m+114)%31)+1
        return datetime.date(year,month,day)
    def is_slovak_holiday(self,d):
        if d.strftime("%m-%d") in SK_SVIATKY_FIX: return True
        e=self.get_easter_date(d.year)
        return d in (e-datetime.timedelta(days=2), e+datetime.timedelta(days=1))
    def calculate_shift(self,date_str,start_str,end_str,plan="",pc_s="",pc_e="",pnp_s="",pnp_e="",shift_type="",meal_o="",other=""):
        st=self.parse_time(start_str); et=self.parse_time(end_str); pt=self.parse_time(plan)
        pcs=self.parse_time(pc_s); pce=self.parse_time(pc_e); pnps=self.parse_time(pnp_s); pnpe=self.parse_time(pnp_e)
        try: sd=datetime.datetime.strptime(date_str,"%Y-%m-%d").date()
        except: return None
        total=0; night=sat=sun=hol=0; pnp=0; overtime=0; has=False
        is_vac=shift_type in ["3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r."]
        is_abs=shift_type in ["3440-Náhr.m.Ost.prek.nep","8000-Nemoc","8020-OČR","3191-Náhrada za vyšetrenie"]
        if is_vac or is_abs:
            am=308
            if pt: am=pt.hour*60+pt.minute
            return {"total_hours":"-","night_hours":"-","saturday_hours":"-","sunday_hours":"-","holiday_hours":"-","pnp_hours":"-","pnp_minutes":0,"overtime":"-","meal_allowance":0.0,"other_allowance":0.0,"vacation_minutes":am,"is_holiday":self.is_slovak_holiday(sd),"is_weekend":sd.weekday() in (5,6)}
        if pnps and pnpe:
            psdt=datetime.datetime.combine(sd,pnps); pedt=datetime.datetime.combine(sd+datetime.timedelta(days=1),pnpe) if pnpe<pnps else datetime.datetime.combine(sd,pnpe)
            pnp=int((pedt-psdt).total_seconds()/60); pnp=max(0,pnp)
        if st and et:
            has=True; sdt=datetime.datetime.combine(sd,st); edt=datetime.datetime.combine(sd+datetime.timedelta(days=1),et) if et<st else datetime.datetime.combine(sd,et)
            total=int((edt-sdt).total_seconds()/60); total=max(0,total-pnp)
            curr=sdt
            while curr<edt:
                if curr.hour>=22 or curr.hour<6: night+=1
                if curr.weekday()==5: sat+=1
                elif curr.weekday()==6: sun+=1
                if self.is_slovak_holiday(curr.date()): hol+=1
                curr+=datetime.timedelta(minutes=1)
        elif pt and shift_type not in ["Štandardný výkon","T.V. (Turnus voľno)","4181-Náhr.za pr.poh.v p.",""]: has=True; total=pt.hour*60+pt.minute
        if shift_type=="4181-Náhr.za pr.poh.v p.": has=False; total=0
        if pt and has:
            pm=pt.hour*60+pt.minute
            if total>pm: overtime=total-pm
        meal=0.0; meal_code=""
        if meal_o and meal_o.strip()!="":
            try: meal=float(meal_o.replace(",",".")); meal_code="M"
            except: pass
        pc_m=0; has_pc=False
        if pcs and pce: has_pc=True; ps=datetime.datetime.combine(sd,pcs); pe=datetime.datetime.combine(sd+datetime.timedelta(days=1),pce) if pce<pcs else datetime.datetime.combine(sd,pce); pc_m=int((pe-ps).total_seconds()/60)
        no_meal=any(shift_type.startswith(x) for x in ["0011","2125","2160","2190","4181","40"])
        if not meal_code and not no_meal and (has or has_pc):
            ev=pc_m if has_pc else total+pnp
            eh=ev/60.0
            if 5<=eh<=12: meal=self.rates["meal_a"]
            elif 12<eh<=18: meal=self.rates["meal_b"]
            elif eh>18: meal=self.rates["meal_c"]
        other_a=0.0
        if shift_type.startswith("2125") and total>0: other_a=round(total/60.0,2); has=False; total=0
        elif other and other.strip()!="":
            try: other_a=float(other.replace(",","."))
            except: pass
        def fmt(m): return f"{m//60:02d}:{m%60:02d}" if m else "00:00"
        return {"total_hours":fmt(total) if has else "-","night_hours":fmt(night) if night else "-","saturday_hours":fmt(sat) if sat else "-","sunday_hours":fmt(sun) if sun else "-","holiday_hours":fmt(hol) if hol else "-","pnp_hours":fmt(pnp) if pnp else "-","pnp_minutes":pnp,"overtime":fmt(overtime) if overtime else "-","meal_allowance":round(meal,2),"other_allowance":round(other_a,2),"vacation_minutes":0,"is_holiday":self.is_slovak_holiday(sd),"is_weekend":sd.weekday() in (5,6)}

class TimePickerPopup(Popup):
    def __init__(self,initial="08:00",callback=None,**kw):
        super().__init__(**kw); self.callback=callback; self.title="Nastaviť čas"; self.size_hint=(0.85,0.5); self.separator_color=(0.9,0.31,0.0,1)
        try: h,m=initial.split(":"); hi=int(h); mi=int(m)
        except: hi,mi=8,0
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        row=BoxLayout(spacing=dp(10))
        self.sp_h=Spinner(text=f"{hi:02d}",values=[f"{i:02d}" for i in range(24)],size_hint_x=0.5,font_size='20sp')
        self.sp_m=Spinner(text=f"{mi:02d}",values=[f"{i:02d}" for i in range(60)],size_hint_x=0.5,font_size='20sp')
        row.add_widget(self.sp_h); row.add_widget(Label(text=":",font_size='22sp',size_hint_x=None,width=dp(20))); row.add_widget(self.sp_m); box.add_widget(row)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(10))
        b1=Button(text="Zrušiť",background_normal='',background_color=(0.4,0.4,0.42,1)); b2=Button(text="Potvrdiť",background_normal='',background_color=(0.9,0.31,0.0,1),bold=True)
        b1.bind(on_press=self.dismiss); b2.bind(on_press=self.confirm); btns.add_widget(b1); btns.add_widget(b2); box.add_widget(btns); self.content=box
    def confirm(self,*a):
        if self.callback: self.callback(f"{self.sp_h.text}:{self.sp_m.text}")
        self.dismiss()

class FilePickerPopup(Popup):
    def __init__(self, start_dirs, callback, **kw):
        super().__init__(**kw); self.callback=callback; self.title="Vyber súbor JSON"; self.size_hint=(0.92,0.85)
        box=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        self.lbl_path=Label(text=",".join(start_dirs)[:80],size_hint_y=None,height=dp(24),font_size='10sp',color=(0.6,0.6,0.6,1)); box.add_widget(self.lbl_path)
        scroll=ScrollView(); grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        files=[]
        for d in start_dirs:
            if os.path.exists(d):
                try:
                    for f in os.listdir(d):
                        if f.lower().endswith(('.json','.csv')): files.append(os.path.join(d,f))
                except: pass
        files=sorted(files, reverse=True)[:80]
        if not files: grid.add_widget(Label(text="Žiadne JSON/CSV v Download ani v app priečinku\nSkopíruj súbor do Download",size_hint_y=None,height=dp(60)))
        for fp in files:
            b=Button(text=os.path.basename(fp),size_hint_y=None,height=dp(44),background_normal='',background_color=(0.2,0.3,0.45,1),halign='left'); b.bind(on_press=lambda inst,p=fp: (self.callback(p), self.dismiss())); grid.add_widget(b)
        scroll.add_widget(grid); box.add_widget(scroll)
        b_close=Button(text="Zavrieť",size_hint_y=None,height=dp(44),background_normal='',background_color=(0.36,0.36,0.38,1)); b_close.bind(on_press=self.dismiss); box.add_widget(b_close)
        self.content=box

class ZSSKApp(App):
    def build(self):
        self.calculator=ShiftCalculator()
        self.data_file=os.path.join(self.user_data_dir,'data.json')
        self.turnus_file=os.path.join(self.user_data_dir,'turnus.json')
        self.emp_file=os.path.join(self.user_data_dir,'employee.json')
        self._ensure_files()
        self.employee=self.load_employee()
        today=datetime.date.today()
        self.cur_year=self.employee.get('cur_year',today.year); self.cur_month=self.employee.get('cur_month',today.month)
        self.theme_key=self.employee.get('theme','tmava'); self.theme=THEMES.get(self.theme_key, THEMES['tmava'])

        root=BoxLayout(orientation='vertical',padding=dp(4),spacing=dp(3))
        with root.canvas.before:
            Color(*self.theme['bg']); self.bg=Rectangle(size=root.size,pos=root.pos)
            root.bind(size=lambda *a: (setattr(self.bg,'size',root.size), setattr(self.bg,'pos',root.pos)))

        # HEADER 2 riadky
        header=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(110),spacing=dp(4))
        with header.canvas.before:
            Color(*self.theme['header_bg']); self.header_bg=Rectangle(size=header.size,pos=header.pos)
            header.bind(size=lambda *a: (setattr(self.header_bg,'size',header.size), setattr(self.header_bg,'pos',header.pos)))
        nav=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6),padding=dp(6))
        b_prev=Button(text='◀',size_hint_x=None,width=dp(52),background_normal='',background_color=(0,0,0,0.15),color=self.theme['text'] if self.theme_key=='zssk' else (1,1,1,1))
        b_next=Button(text='▶',size_hint_x=None,width=dp(52),background_normal='',background_color=(0,0,0,0.15),color=self.theme['text'] if self.theme_key=='zssk' else (1,1,1,1))
        self.lbl_month=Label(text='',font_size='18sp',bold=True,color=(1,1,1,1) if self.theme_key!='zssk' else (1,1,1,1))
        b_prev.bind(on_press=lambda x:self.shift_month(-1)); b_next.bind(on_press=lambda x:self.shift_month(1))
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next); header.add_widget(nav)

        # Akcie - horizontálny scroll aby sa neprekrývali na mobile
        actions_scroll=ScrollView(size_hint_y=None,height=dp(52),do_scroll_y=False,do_scroll_x=True,bar_width=0)
        actions=GridLayout(cols=6,spacing=dp(6),size_hint_x=None,height=dp(48),padding=(dp(6),0)); actions.bind(minimum_width=actions.setter('width')); actions.row_default_height=dp(44)
        # width dynamicky
        for txt,key,fn in [
            ('Mesiac','btn_mesiac',self.open_month_picker),
            ('Turnus','btn_turnus',self.open_turnus_generator),
            ('Stats','btn_stats',self.open_stats),
            ('Export','btn_export',self.open_export_menu),
            ('Oprav','btn_oprav',self.show_oprav_info),
            ('⚙ Nastav','btn_settings',self.open_settings),
        ]:
            b=Button(text=txt,size_hint_x=None,width=dp(84),background_normal='',background_color=self.theme[key],font_size='12sp')
            b.bind(on_press=fn); actions.add_widget(b)
        actions_scroll.add_widget(actions); header.add_widget(actions_scroll)
        root.add_widget(header)

        # KPI
        self.kpi_box=BoxLayout(size_hint_y=None,height=dp(60),spacing=dp(6),padding=dp(4))
        self.lbl_kpi_main=Label(font_size='11sp',color=self.theme['text'],halign='left'); self.lbl_kpi_night=Label(font_size='11sp',color=self.theme['text'],halign='left'); self.lbl_kpi_meal=Label(font_size='11sp',color=self.theme['text'],halign='left')
        for l in [self.lbl_kpi_main,self.lbl_kpi_night,self.lbl_kpi_meal]: l.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width,None)))
        self.kpi_box.add_widget(self.lbl_kpi_main); self.kpi_box.add_widget(self.lbl_kpi_night); self.kpi_box.add_widget(self.lbl_kpi_meal); root.add_widget(self.kpi_box)
        self.lbl_info=Label(size_hint_y=None,height=dp(20),color=self.theme['subtext'],font_size='11sp'); root.add_widget(self.lbl_info)

        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(5),size_hint_y=None,padding=dp(2)); self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)

        bottom=BoxLayout(size_hint_y=None,height=dp(56),spacing=dp(6),padding=dp(4))
        b_add=Button(text='+ Pridať zmenu',background_normal='',background_color=self.theme['btn_primary'],font_size='16sp',bold=True)
        b_pay=Button(text='💰 Výplata',size_hint_x=None,width=dp(108),background_normal='',background_color=self.theme['btn_stats'])
        b_add.bind(on_press=lambda x:self.open_editor()); b_pay.bind(on_press=self.open_payroll); bottom.add_widget(b_add); bottom.add_widget(b_pay); root.add_widget(bottom)

        self.refresh(); return root

    def _ensure_files(self):
        os.makedirs(self.user_data_dir,exist_ok=True)
        if not os.path.exists(self.data_file):
            with open(self.data_file,'w',encoding='utf-8') as f: json.dump([],f)
        if not os.path.exists(self.turnus_file):
            # predvolený turnus - letný prázdninový ako placeholder
            with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump({"active":"Leto 2026","profiles":{"Leto 2026":[]}},f,ensure_ascii=False,indent=2)
        if not os.path.exists(self.emp_file):
            with open(self.emp_file,'w',encoding='utf-8') as f: json.dump({"name":"Miroslav Kurek","id":"20 814","role":"Rušňovodič","base_salary":"1484.00","norm_hours":"160:00","cur_year":datetime.date.today().year,"cur_month":datetime.date.today().month,"theme":"tmava"},f,ensure_ascii=False,indent=2)

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
        tf=self.load_turnus_file(); act=tf.get('active'); prof=tf.get('profiles',{}).get(act,[]); return prof, act, tf
    def load_employee(self):
        try:
            with open(self.emp_file,encoding='utf-8') as f: return json.load(f)
        except: return {}
    def save_employee(self):
        self.employee['cur_year']=self.cur_year; self.employee['cur_month']=self.cur_month; self.employee['theme']=self.theme_key
        with open(self.emp_file,'w',encoding='utf-8') as fp: json.dump(self.employee,fp,ensure_ascii=False,indent=2)

    def month_key(self): return f"{self.cur_year:04d}-{self.cur_month:02d}"
    def shift_month(self,d):
        m=self.cur_month+d; y=self.cur_year
        while m>12: m-=12; y+=1
        while m<1: m+=12; y-=1
        self.cur_year,self.cur_month=y,m; self.save_employee(); self.refresh()

    def refresh(self):
        all_data=self.load_data(); month_data=[d for d in all_data if d.get('date','').startswith(self.month_key())]
        month_data=sorted(month_data, key=lambda x:(x.get('date',''),x.get('start','')))
        self.lbl_month.text=f"{self.month_key()} • {len(month_data)} záznamov"
        self.grid.clear_widgets()
        totals={"worked":0,"night":0,"sat":0,"sun":0,"hol":0,"pnp":0,"meal":0.0,"other":0.0,"overtime":0,"vacation":0}
        theme_colors=COLORS_LIGHT if self.theme_key=='zssk' else COLORS_DARK
        for s in month_data:
            calc=self.calculator.calculate_shift(s.get('date',''),s.get('start',''),s.get('end',''),s.get('plan',''),s.get('pc_start',''),s.get('pc_end',''),s.get('pnp_start',''),s.get('pnp_end',''),s.get('shift_type',''),s.get('meal_override',''),s.get('other_premiums',''))
            if calc:
                def p(h):
                    try: return int(h.split(':')[0])*60+int(h.split(':')[1]) if ':' in h else 0
                    except: return 0
                totals['worked']+=p(calc.get('total_hours','0:00')) if calc.get('total_hours')!='-' else 0
                totals['night']+=p(calc.get('night_hours','0:00')); totals['sat']+=p(calc.get('saturday_hours','0:00')); totals['sun']+=p(calc.get('sunday_hours','0:00')); totals['hol']+=p(calc.get('holiday_hours','0:00')); totals['pnp']+=calc.get('pnp_minutes',0); totals['overtime']+=p(calc.get('overtime','0:00')); totals['meal']+=calc.get('meal_allowance',0.0); totals['other']+=calc.get('other_allowance',0.0); totals['vacation']+=calc.get('vacation_minutes',0)
            typ=s.get('shift_type') or 'Štandardný výkon'; base=theme_colors.get(typ, theme_colors.get('Štandardný výkon'))
            if calc and calc.get('is_holiday'): base=(min(base[0]+0.15,1),min(base[1]+0.15,1),min(base[2]+0.15,1),1)
            btn=Button(size_hint_y=None,height=dp(68),background_normal='',background_color=base,color=(1,1,1,1) if self.theme_key=='tmava' else (0.1,0.1,0.1,1) if typ=='T.V. (Turnus voľno)' else (1,1,1,1),halign='left',valign='middle',padding=(dp(12),dp(6)),markup=True)
            date=s.get('date',''); start=s.get('start',''); end=s.get('end',''); trains=f"{s.get('train_first','')} {s.get('route_from','')}→{s.get('train_last','')} {s.get('route_to','')}".strip() or s.get('note','')[:36]
            total=calc.get('total_hours','-') if calc else '-'; night=calc.get('night_hours','-') if calc else '-'
            btn.text=f"[b]{date}[/b] {typ}\n{start}-{end} | {total} N:{night} {trains}"; btn.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width-dp(24),None)))
            btn.bind(on_press=lambda inst,uid=s['uid']: self.open_editor(uid)); self.grid.add_widget(btn)
        def fmt(m): return f"{m//60:02d}:{m%60:02d}"
        self.lbl_kpi_main.text=f"Fond: {fmt(totals['worked'])} | Dov:{fmt(totals['vacation'])}\nNadčas:{fmt(totals['overtime'])}"
        self.lbl_kpi_night.text=f"Nočná:{fmt(totals['night'])}\nSo:{fmt(totals['sat'])} Ne:{fmt(totals['sun'])}"
        self.lbl_kpi_meal.text=f"Sviatok:{fmt(totals['hol'])} PNP:{fmt(totals['pnp'])}\nStravné:{totals['meal']:.2f}€ Iné:{totals['other']:.2f}€"
        self.current_totals=totals

    # ---- EDITOR (z v8) ----
    def open_editor(self,uid=None):
        all_data=self.load_data(); edit=None
        if uid:
            for d in all_data:
                if d.get('uid')==uid: edit=d; break
        is_new=edit is None
        if is_new: edit={"uid":str(uuid.uuid4()),"date":f"{self.month_key()}-01","shift_type":"Štandardný výkon","train_first":"","route_from":"","train_last":"","route_to":"","turnus":"","start":"","end":"","pc_start":"","pc_end":"","plan":"","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":""}
        popup=Popup(title='Upraviť' if not is_new else 'Pridať zmenu',size_hint=(0.96,0.92),separator_color=self.theme['accent'],auto_dismiss=False)
        root=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10)); scroll=ScrollView(); form=GridLayout(cols=1,spacing=dp(10),size_hint_y=None,padding=dp(4)); form.bind(minimum_height=form.setter('height'))
        def add_row(lbl,w):
            b=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(68),spacing=dp(4)); b.add_widget(Label(text=lbl,size_hint_y=None,height=dp(20),halign='left',font_size='12sp',color=self.theme['subtext'])); b.add_widget(w); form.add_widget(b); return b
        inp_date=TextInput(text=edit.get('date',''),multiline=False,size_hint_y=None,height=dp(40)); add_row('Dátum YYYY-MM-DD',inp_date)
        sp_type=Spinner(text=edit.get('shift_type') or 'Štandardný výkon',values=SHIFT_TYPES,size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['row_bg']); add_row('Mzdový druh',sp_type)
        row_t=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6)); it=TextInput(text=edit.get('turnus',''),hint_text='TD',multiline=False,size_hint_x=0.3); itf=TextInput(text=edit.get('train_first',''),hint_text='Vlak 1.',multiline=False); itl=TextInput(text=edit.get('train_last',''),hint_text='Vlak posl.',multiline=False); row_t.add_widget(it); row_t.add_widget(itf); row_t.add_widget(itl); add_row('Turnus + Vlaky',row_t)
        row_r=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6)); irf=TextInput(text=edit.get('route_from',''),hint_text='Z',multiline=False); irt=TextInput(text=edit.get('route_to',''),hint_text='Do',multiline=False); row_r.add_widget(irf); row_r.add_widget(irt); add_row('Trať',row_r)
        def time_row(label,key):
            r=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6)); inp=TextInput(text=edit.get(key,''),hint_text='HH:MM',multiline=False); btn=Button(text='🕒',size_hint_x=None,width=dp(48),background_normal='',background_color=self.theme['btn_export']); btn.bind(on_press=lambda *_: TimePickerPopup(initial=inp.text or "08:00",callback=lambda v:setattr(inp,'text',v)).open()); r.add_widget(inp); r.add_widget(btn); add_row(label,r); return inp
        ins=time_row('Nástup','start'); ine=time_row('Koniec','end'); ipl=time_row('Plán FPČ','plan'); ipcs=time_row('PC zač','pc_start'); ipce=time_row('PC koniec','pc_end'); ipnps=time_row('PNP zač','pnp_start'); ipnpe=time_row('PNP koniec','pnp_end')
        im=TextInput(text=edit.get('meal_override',''),hint_text='prázdne=auto',multiline=False,size_hint_y=None,height=dp(40)); add_row('Stravné override €',im)
        io=TextInput(text=edit.get('other_premiums',''),hint_text='Iné €',multiline=False,size_hint_y=None,height=dp(40)); add_row('Iné príplatky',io)
        ino=TextInput(text=edit.get('note',''),multiline=True,size_hint_y=None,height=dp(70)); add_row('Poznámka',ino)
        lbl_prev=Label(text='Náhľad: -',size_hint_y=None,height=dp(50),color=self.theme['subtext'],font_size='12sp'); form.add_widget(lbl_prev)
        def upd(*_):
            c=self.calculator.calculate_shift(inp_date.text,ins.text,ine.text,ipl.text,ipcs.text,ipce.text,ipnps.text,ipnpe.text,sp_type.text,im.text,io.text)
            if c: lbl_prev.text=f"Odprac:{c['total_hours']} Nočná:{c['night_hours']} So:{c['saturday_hours']} Ne:{c['sunday_hours']} Sv:{c['holiday_hours']} Strava:{c['meal_allowance']}€"
        for w in [inp_date,ins,ine,ipl,ipcs,ipce,ipnps,ipnpe,im,io]: w.bind(text=lambda *a: upd()); sp_type.bind(text=lambda *a: upd()); upd()
        scroll.add_widget(form); root.add_widget(scroll)
        btns=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(8)); bc=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); bd=Button(text='Zmazať',background_normal='',background_color=(0.75,0.2,0.2,1),size_hint_x=None,width=dp(86)); bs=Button(text='Uložiť',background_normal='',background_color=self.theme['btn_save'],bold=True)
        bc.bind(on_press=popup.dismiss)
        def do_del(*_):
            if not is_new: nd=[d for d in all_data if d.get('uid')!=uid]; self.save_data(nd); self.refresh(); popup.dismiss()
        def do_save(*_):
            try: datetime.datetime.strptime(inp_date.text,"%Y-%m-%d")
            except: self.show_info('Zlý dátum, formát YYYY-MM-DD'); return
            ns={"uid":edit['uid'],"date":inp_date.text.strip(),"shift_type":sp_type.text,"train_first":itf.text,"route_from":irf.text,"train_last":itl.text,"route_to":irt.text,"turnus":it.text,"start":ins.text,"end":ine.text,"pc_start":ipcs.text,"pc_end":ipce.text,"plan":ipl.text,"pnp_start":ipnps.text,"pnp_end":ipnpe.text,"meal_override":im.text,"other_premiums":io.text,"note":ino.text}
            if is_new: all_data.append(ns)
            else:
                for i,d in enumerate(all_data):
                    if d.get('uid')==uid: all_data[i]=ns; break
            self.save_data(sorted(all_data,key=lambda x:(x.get('date',''),x.get('start','')))); self.refresh(); popup.dismiss()
        bd.bind(on_press=do_del); bs.bind(on_press=do_save); btns.add_widget(bc); 
        if not is_new: btns.add_widget(bd)
        btns.add_widget(bs); root.add_widget(btns); popup.content=root; popup.open()

    # ---- NASTAVENIA + TÉMA ----
    def open_settings(self,*a):
        popup=Popup(title='⚙ Nastavenia',size_hint=(0.92,0.88),separator_color=self.theme['accent'])
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        box.add_widget(Label(text='Farebná schéma',size_hint_y=None,height=dp(24),bold=True,color=self.theme['text']))
        sp_theme=Spinner(text=THEMES[self.theme_key]['name'],values=[v['name'] for v in THEMES.values()],size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['row_bg'])
        box.add_widget(sp_theme)
        # zamestnanec
        for lbl,key in [('Meno','name'),('Os. číslo','id'),('Základná mzda €','base_salary'),('Norma hodín','norm_hours')]:
            row=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8)); row.add_widget(Label(text=lbl,size_hint_x=0.4,halign='left',color=self.theme['text'])); ti=TextInput(text=str(self.employee.get(key,'')),multiline=False,size_hint_x=0.6); ti._key=key; row.add_widget(ti); box.add_widget(row)
        lbl_info=Label(text='Zmena témy sa prejaví po reštarte aplikácie',font_size='11sp',color=self.theme['subtext'],size_hint_y=None,height=dp(24)); box.add_widget(lbl_info)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); b_cancel=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b_save=Button(text='Uložiť',background_normal='',background_color=self.theme['btn_save'],bold=True)
        def save(*_):
            # ulož theme
            for k,v in THEMES.items():
                if v['name']==sp_theme.text: self.theme_key=k; break
            # ulož ostatné TextInputy
            for child in box.children:
                if isinstance(child,BoxLayout):
                    for w in child.children:
                        if isinstance(w,TextInput) and hasattr(w,'_key'): self.employee[w._key]=w.text
            self.save_employee(); popup.dismiss(); self.show_info(f'Téma nastavená na: {THEMES[self.theme_key]["name"]}\nReštartuj aplikáciu pre plné použitie.')
        b_cancel.bind(on_press=popup.dismiss); b_save.bind(on_press=save); btns.add_widget(b_cancel); btns.add_widget(b_save); box.add_widget(btns)
        popup.content=box; popup.open()

    # ---- EXPORT / IMPORT NOVÉ ----
    def open_export_menu(self,*a):
        popup=Popup(title='Export / Import',size_hint=(0.92,None),height=dp(560),separator_color=self.theme['accent'])
        box=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(12))
        btns=[
            ('Export CSV (mesiac)',self.export_csv),
            ('Export JSON (všetko)',self.export_json),
            ('Report TXT',self.export_report),
            ('--- IMPORT ---',None),
            ('Import zmien z JSON',self.import_shifts_picker),
            ('Import turnusu z JSON',self.import_turnus_picker),
            ('Export turnusu',self.export_turnus),
        ]
        for txt,fn in btns:
            if fn is None: box.add_widget(Label(text=txt,size_hint_y=None,height=dp(24),bold=True,color=self.theme['text'])); continue
            b=Button(text=txt,size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_export']); b.bind(on_press=lambda inst,f=fn: (f(), popup.dismiss() if 'Import' not in txt else None)); box.add_widget(b)
        b_c=Button(text='Zavrieť',size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_settings']); b_c.bind(on_press=popup.dismiss); box.add_widget(b_c)
        popup.content=box; popup.open()

    def get_download_dirs(self):
        dirs=[self.user_data_dir]
        for p in ["/storage/emulated/0/Download","/sdcard/Download","/storage/emulated/0/Documents","./"]:
            if os.path.exists(p): dirs.append(p)
        return dirs

    def import_shifts_picker(self,*a):
        def on_pick(path):
            try:
                with open(path,encoding='utf-8') as f: data=json.load(f)
                # podporuje formát z PC aj z mobilu
                if isinstance(data,dict) and 'shifts_data' in data: new_shifts=data['shifts_data']
                elif isinstance(data,list): new_shifts=data
                else: self.show_info('Neznámy formát JSON'); return
                existing=self.load_data(); existing_dates={d['date'] for d in existing}
                added=0
                for s in new_shifts:
                    if not isinstance(s,dict): continue
                    if 'date' not in s and 'datum' in s: s['date']=s['datum']
                    if 'date' not in s: continue
                    # ak už existuje rovnaký dátum + nástup, preskoč alebo nahraď
                    if s.get('date') not in existing_dates:
                        if 'uid' not in s: s['uid']=str(uuid.uuid4())
                        existing.append(s); added+=1
                self.save_data(sorted(existing,key=lambda x:x.get('date',''))); self.refresh(); self.show_info(f'Import hotový: {added} nových záznamov z {os.path.basename(path)}')
            except Exception as e: self.show_info(f'Chyba importu: {e}')
        FilePickerPopup(self.get_download_dirs(), on_pick).open()

    def import_turnus_picker(self,*a):
        def on_pick(path):
            try:
                with open(path,encoding='utf-8') as f: data=json.load(f)
                # data môže byť list šablón alebo dict s profilmi
                tf=self.load_turnus_file()
                profile_name=os.path.splitext(os.path.basename(path))[0]
                if isinstance(data,list): tf['profiles'][profile_name]=data; tf['active']=profile_name
                elif isinstance(data,dict) and 'profiles' in data: tf=data
                else: self.show_info('Neplatný turnus JSON - očakáva sa list alebo {profiles:..}'); return
                self.save_turnus_file(tf); self.show_info(f'Turnus importovaný ako profil "{profile_name}" a nastavený ako aktívny. Teraz v generátore použije nové šablóny.')
            except Exception as e: self.show_info(f'Chyba: {e}')
        FilePickerPopup(self.get_download_dirs(), on_pick).open()

    def export_turnus(self,*a):
        tf=self.load_turnus_file(); fname=f"turnus_{tf.get('active','profil')}_{self.month_key()}.json"; out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',encoding='utf-8') as f: json.dump(tf,f,ensure_ascii=False,indent=2)
            self.show_info(f'Turnus exportovaný:\n{out}\n\nSkopíruj ho do Download a po prázdninách nahraj nový turnus cez Import turnusu.')
        except Exception as e: self.show_info(f'Chyba: {e}')

    # ---- TURNUS GENERÁTOR S PROFILMI ----
    def open_turnus_generator(self,*a):
        prof, active_name, full = self.get_active_turnus()
        popup=Popup(title=f'Generátor - aktívny turnus: {active_name}',size_hint=(0.94,0.86),separator_color=self.theme['btn_turnus'])
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        box.add_widget(Label(text=f'Aktívny profil: {active_name} ({len(prof)} šablón)\nAk je prázdny, použije sa PATTERN fallback',font_size='11sp',color=self.theme['subtext'],size_hint_y=None,height=dp(46)))
        row_prof=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8)); sp_prof=Spinner(text=active_name,values=list(full.get('profiles',{}).keys()),size_hint_x=0.7,background_normal='',background_color=self.theme['row_bg']); b_set=Button(text='Nastav aktívny',size_hint_x=0.3,background_normal='',background_color=self.theme['btn_turnus'])
        def set_active(*_):
            full['active']=sp_prof.text; self.save_turnus_file(full); self.show_info(f'Aktívny turnus zmenený na {sp_prof.text}'); popup.dismiss()
        b_set.bind(on_press=set_active); row_prof.add_widget(sp_prof); row_prof.add_widget(b_set); box.add_widget(row_prof)
        inp_td=TextInput(text='1',hint_text='TD na 1.deň',multiline=False,size_hint_y=None,height=dp(44)); inp_len=TextInput(text='8',hint_text='Dĺžka turnusu',multiline=False,size_hint_y=None,height=dp(44))
        box.add_widget(inp_td); box.add_widget(inp_len); lbl=Label(text='',font_size='11sp',color=self.theme['subtext']); box.add_widget(lbl)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8)); b_cancel=Button(text='Zrušiť',background_normal='',background_color=self.theme['btn_settings']); b_gen=Button(text='Generovať mesiac',background_normal='',background_color=self.theme['btn_oprav'],bold=True)
        b_cancel.bind(on_press=popup.dismiss)
        def gen(*_):
            try: start_td=int(inp_td.text); turn_len=int(inp_len.text)
            except: lbl.text='Zadaj čísla'; return
            data=self.load_data(); turnus_data=full['profiles'].get(full['active'],[])
            days_in_month=calendar.monthrange(self.cur_year,self.cur_month)[1]; keep=[d for d in data if not d.get('date','').startswith(self.month_key())]; new_month=[]
            for day in range(1,days_in_month+1):
                ds=f"{self.cur_year:04d}-{self.cur_month:02d}-{day:02d}"; cur_td=((start_td-1+day-1)%turn_len)+1; date_obj=datetime.date(self.cur_year,self.cur_month,day); is_hol=self.calculator.is_slovak_holiday(date_obj); target="Sv" if is_hol else ["Po","Ut","St","Št","Pi","So","Ne"][date_obj.weekday()]
                match=None
                for t in turnus_data:
                    if str(t.get('td'))==str(cur_td) and target in t.get('days',[]): match=t; break
                if match: shift={"uid":str(uuid.uuid4()),"date":ds,"shift_type":match.get('shift_type','Štandardný výkon'),"train_first":match.get('train_first',''),"route_from":match.get('route_from',''),"train_last":match.get('train_last',''),"route_to":match.get('route_to',''),"turnus":str(cur_td),"start":match.get('start',''),"end":match.get('end',''),"pc_start":match.get('pc_start',''),"pc_end":match.get('pc_end',''),"plan":match.get('plan',''),"pnp_start":match.get('pnp_start',''),"pnp_end":match.get('pnp_end',''),"meal_override":match.get('meal_override',''),"other_premiums":match.get('other_premiums',''),"note":""}
                else: typ=PATTERN[(day-1)%len(PATTERN)]; is_tv=typ in ('Voľno',); shift={"uid":str(uuid.uuid4()),"date":ds,"shift_type":"T.V. (Turnus voľno)" if is_tv else "Štandardný výkon","train_first":"T.V." if is_tv else "","route_from":"","train_last":"T.V." if is_tv else "","route_to":"","turnus":str(cur_td),"start":"","end":"","pc_start":"","pc_end":"","plan":"08:00" if not is_tv else "","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":typ}
                new_month.append(shift)
            keep.extend(new_month); self.save_data(keep); self.refresh(); popup.dismiss(); self.show_info(f'Vygenerovaných {len(new_month)} dní pre {self.month_key()} z profilu {full["active"]}')
        b_gen.bind(on_press=gen); btns.add_widget(b_cancel); btns.add_widget(b_gen); box.add_widget(btns); popup.content=box; popup.open()

    # ---- OPRAV VYSVETLENIE ----
    def show_oprav_info(self,*a):
        popup=Popup(title='Čo robí tlačidlo Oprav?',size_hint=(0.90,None),height=dp(420),separator_color=self.theme['btn_oprav'])
        box=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10))
        txt="Tlačidlo Oprav (pôvodne Oprav typy) slúži na rýchlu opravu starých dát.\n\n1. Prejde všetky záznamy v aktuálnom mesiaci\n2. Ak záznam nemá vyplnený Mzdový druh / Typ zmeny (prázdne pole)\n3. Doplní ho podľa pozície dňa v mesiaci podľa vzoru:\n   PATTERN = Ranná,Ranná,Poobedná,Poobedná,Nočná,Nočná,Voľno,Voľno\n\nPríklad: 1.deň = Ranná, 7.deň = Voľno, 9.deň = Ranná atď.\n\nNEMAŽE existujúce typy, len dopĺňa prázdne.\n\nAk používaš turnusové šablóny, používaj radšej Generátor turnusu, ten vygeneruje celý mesiac presne podľa TD."
        box.add_widget(Label(text=txt,halign='left',font_size='12sp',color=self.theme['text']))
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        b_cancel=Button(text='Zavrieť',background_normal='',background_color=self.theme['btn_settings']); b_run=Button(text='Spustiť Oprav',background_normal='',background_color=self.theme['btn_oprav'],bold=True)
        b_cancel.bind(on_press=popup.dismiss)
        def run(*_):
            data=self.load_data(); ch=0
            for d in data:
                if d.get('date','').startswith(self.month_key()) and not d.get('shift_type'):
                    try: day=int(d['date'].split('-')[2]); d['shift_type']=PATTERN[(day-1)%len(PATTERN)]; ch+=1
                    except: pass
            self.save_data(data); self.refresh(); popup.dismiss(); self.show_info(f'Opravených {ch} záznamov')
        b_run.bind(on_press=run); row.add_widget(b_cancel); row.add_widget(b_run); box.add_widget(row); popup.content=box; popup.open()

    # ---- OSTATNÉ ----
    def open_month_picker(self,*a):
        temp_year=[self.cur_year]; popup=Popup(title='Vyber mesiac',size_hint=(0.92,None),height=dp(470),separator_color=self.theme['accent'])
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        year_box=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10)); bm=Button(text='- rok',size_hint_x=None,width=dp(78),background_normal='',background_color=self.theme['btn_settings']); bp=Button(text='+ rok',size_hint_x=None,width=dp(78),background_normal='',background_color=self.theme['btn_settings']); ly=Label(text=str(temp_year[0]),font_size='18sp',bold=True,color=self.theme['text'])
        def chg(d): temp_year[0]+=d; ly.text=str(temp_year[0])
        bm.bind(on_press=lambda x: chg(-1)); bp.bind(on_press=lambda x: chg(1)); year_box.add_widget(bm); year_box.add_widget(ly); year_box.add_widget(bp); box.add_widget(year_box)
        grid=GridLayout(cols=3,spacing=dp(8),size_hint_y=1,row_default_height=dp(52),row_force_default=True)
        for m in range(1,13):
            is_cur=(m==self.cur_month and temp_year[0]==self.cur_year); bg=self.theme['accent'] if is_cur else self.theme['row_bg']
            b=Button(text=f"{m:02d}\n{calendar.month_abbr[m]}",background_normal='',background_color=bg,font_size='13sp')
            def make_cb(mm): return lambda inst: (setattr(self,'cur_year',temp_year[0]), setattr(self,'cur_month',mm), self.save_employee(), popup.dismiss(), self.refresh())
            b.bind(on_press=make_cb(m)); grid.add_widget(b)
        box.add_widget(grid); bc=Button(text='Zavrieť',size_hint_y=None,height=dp(48),background_normal='',background_color=self.theme['btn_settings']); bc.bind(on_press=popup.dismiss); box.add_widget(bc); popup.content=box; popup.open()

    def open_stats(self,*a):
        data=[d for d in self.load_data() if d.get('date','').startswith(self.month_key())]; cnt={}; hours={}
        for d in data:
            k=d.get('shift_type','bez typu') or 'bez typu'; cnt[k]=cnt.get(k,0)+1
            c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
            if c and c.get('total_hours')!='-':
                try: h=int(c['total_hours'].split(':')[0]); hours[k]=hours.get(k,0)+h
                except: pass
        popup=Popup(title=f'Prehľad {self.month_key()}',size_hint=(0.92,None),height=dp(500)); root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8)); scroll=ScrollView(); grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        if not cnt: grid.add_widget(Label(text='Žiadne dáta',size_hint_y=None,height=dp(30),color=self.theme['text']))
        else:
            for k in sorted(cnt.keys()):
                row=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(8)); row.add_widget(Label(text=k,size_hint_x=0.6,halign='left',font_size='12sp',color=self.theme['text'])); row.add_widget(Label(text=f"{cnt[k]}x / {hours.get(k,0)}h",size_hint_x=0.4,halign='right',font_size='12sp',color=self.theme['subtext'])); grid.add_widget(row)
            grid.add_widget(Label(text=f"Celkom: {len(data)} zmien",size_hint_y=None,height=dp(30),bold=True,color=self.theme['text']))
        scroll.add_widget(grid); root.add_widget(scroll); b=Button(text='OK',size_hint_y=None,height=dp(48),background_normal='',background_color=self.theme['btn_stats']); b.bind(on_press=popup.dismiss); root.add_widget(b); popup.content=root; popup.open()

    def open_payroll(self,*a):
        t=self.current_totals; base=float(self.employee.get('base_salary','1484').replace(',','.')) if self.employee.get('base_salary') else 1484.0; norm_s=self.employee.get('norm_hours','160:00')
        try: nh,nm=map(int,norm_s.split(':')); norm_dec=nh+nm/60.0
        except: norm_dec=160.0
        hod=base/norm_dec if norm_dec>0 else 9.27; worked_h=t.get('worked',0)/60.0; night_h=t.get('night',0)/60.0; sat_h=t.get('sat',0)/60.0; sun_h=t.get('sun',0)/60.0; hol_h=t.get('hol',0)/60.0
        sum_base=worked_h*hod; sum_night=night_h*2.10; sum_sat=sat_h*2.63; sum_sun=sun_h*5.26; sum_hol=hol_h*13.88; hruba=sum_base+sum_night+sum_sat+sum_sun+sum_hol+t.get('other',0)+65.0; cista=hruba*0.73; k_vyp=cista+t.get('meal',0)
        popup=Popup(title=f'Výplata odhad {self.month_key()}',size_hint=(0.92,None),height=dp(460)); box=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(6))
        for txt in [f"Základ: {sum_base:.2f}€ ({worked_h:.1f}h x {hod:.2f})",f"Nočné: {sum_night:.2f}€",f"Víkend So+Ne: {(sum_sat+sum_sun):.2f}€",f"Sviatok: {sum_hol:.2f}€",f"Iné: {t.get('other',0):.2f}€ + 65€ prémia","---",f"HRUBÁ: {hruba:.2f}€",f"ČISTÁ ~73%: {cista:.2f}€",f"Stravné: {t.get('meal',0):.2f}€",f"SPOLU K VÝPLATE: {k_vyp:.2f}€"]:
            box.add_widget(Label(text=txt,font_size='13sp',halign='left',size_hint_y=None,height=dp(26),color=self.theme['text']))
        b=Button(text='Zavrieť',size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_settings']); b.bind(on_press=popup.dismiss); box.add_widget(b); popup.content=box; popup.open()

    def export_csv(self,*a):
        fname=f"zsskzmeny_{self.month_key()}.csv"; out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['datum','mzdovy_druh','turnus','nastup','koniec','plan','celkom','nocna','sobota','nedela','sviatok','stravne','poznamka'])
                for d in sorted(self.load_data(),key=lambda x:x.get('date','')):
                    if not d.get('date','').startswith(self.month_key()): continue
                    c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                    w.writerow([d.get('date'),d.get('shift_type'),d.get('turnus'),d.get('start'),d.get('end'),d.get('plan'),c.get('total_hours') if c else '',c.get('night_hours') if c else '',c.get('saturday_hours') if c else '',c.get('sunday_hours') if c else '',c.get('holiday_hours') if c else '',c.get('meal_allowance') if c else '',d.get('note','')])
            self.show_info(f'CSV export: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def export_json(self,*a):
        fname=f"zsskzmeny_all_{datetime.date.today().isoformat()}.json"; out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',encoding='utf-8') as f: json.dump({"employee_info":self.employee,"shifts_data":self.load_data(),"turnus":self.load_turnus_file()},f,ensure_ascii=False,indent=2)
            self.show_info(f'JSON export: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def export_report(self,*a):
        fname=f"report_{self.month_key()}.txt"; out=os.path.join(self.user_data_dir,fname)
        try:
            lines=[f"PREVÁDZKOVÝ ZÁZNAM {self.month_key()}",f"Zamestnanec: {self.employee.get('name','')} {self.employee.get('id','')}","="*60]
            for d in sorted([x for x in self.load_data() if x.get('date','').startswith(self.month_key())],key=lambda x:x.get('date','')):
                c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                lines.append(f"{d.get('date')} {d.get('shift_type')[:24]:24} {d.get('start',''):5}-{d.get('end',''):5} {c.get('total_hours','-') if c else '-':5} N:{c.get('night_hours','-') if c else '-'} {d.get('note','')}")
            with open(out,'w',encoding='utf-8') as f: f.write("\n".join(lines)); self.show_info(f'Report: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')
    def show_info(self,msg):
        p=Popup(title='Info',size_hint=(0.86,None),height=dp(280)); b=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10)); b.add_widget(Label(text=msg,halign='center',color=self.theme['text'])); btn=Button(text='OK',size_hint_y=None,height=dp(44),background_normal='',background_color=self.theme['btn_settings']); btn.bind(on_press=p.dismiss); b.add_widget(btn); p.content=b; p.open()

if __name__=='__main__': ZSSKApp().run()
