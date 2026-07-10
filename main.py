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
from kivy.metrics import dp, sp
from kivy.graphics import Color, Rectangle
from kivy.core.window import Window

# ---------- KONSTANTY Z PC VERZIE ----------
SHIFT_TYPES = [
    "Štandardný výkon",
    "T.V. (Turnus voľno)",
    "0006-Hodi.povinn.škol.a",
    "0007-Hod.nariadenej lek.prehliad.",
    "0011-Nevysporiad.hod.nad FPČ",
    "0014-Hodiny školenia",
    "2125-Príplatok za real. AP-1",
    "2160-Prípl.za sť.nástup a.",
    "2190-Prípl.sťaž.pr.režim",
    "3000-Dovolenka - bežný rok",
    "3010-Riad.dovol.min.r.",
    "3120-Štúdium popri zamest.",
    "3191-Náhrada za vyšetrenie",
    "3440-Náhr.m.Ost.prek.nep",
    "4181-Náhr.za pr.poh.v p.",
    "8000-Nemoc",
    "8020-OČR"
]

COLORS = {
    'Štandardný výkon': (0.15,0.55,0.85,1),
    'T.V. (Turnus voľno)': (0.25,0.30,0.35,1),
    'Ranná': (0.15,0.55,0.85,1),
    'Poobedná': (0.85,0.55,0.15,1),
    'Nočná': (0.32,0.32,0.82,1),
    'Voľno': (0.25,0.65,0.25,1),
    'Dovolenka': (0.75,0.45,0.85,1),
    'PN': (0.85,0.25,0.25,1),
    'Školenie': (0.5,0.5,0.5,1),
    '3000-Dovolenka - bežný rok': (0.2,0.7,0.4,1),
    '4181-Náhr.za pr.poh.v p.': (0.6,0.4,0.1,1),
    '': (0.20,0.20,0.22,1),
}
HODINY_ODHAD = {'Ranná':8,'Poobedná':8,'Nočná':12,'Školenie':8}
PATTERN = ['Ranná','Ranná','Poobedná','Poobedná','Nočná','Nočná','Voľno','Voľno']

SK_SVIATKY_FIX = {"01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"}

# ---------- KALKULATOR Z PC (bez zmeny logiky) ----------
class ShiftCalculator:
    def __init__(self):
        self.rates = {"meal_a": 9.30, "meal_b": 13.80, "meal_c": 21.00}
    def parse_time(self, s):
        try:
            if not s or s.strip() in ("","-"): return None
            parts = s.replace(".",":").split(":")
            h=int(parts[0]); m=int(parts[1]) if len(parts)>1 else 0
            return datetime.time(h,m)
        except: return None
    def get_easter_date(self, year):
        a=year%19; b=year//100; c=year%100; d=b//4; e=b%4; f=(b+8)//25; g=(b-f+1)//3
        h=(19*a+b-d-g+15)%30; i=c//4; k=c%4; L=(32+2*e+2*i-h-k)%7
        m=(a+11*h+22*L)//451; month=(h+L-7*m+114)//31; day=((h+L-7*m+114)%31)+1
        return datetime.date(year,month,day)
    def is_slovak_holiday(self, date_obj):
        if date_obj.strftime("%m-%d") in SK_SVIATKY_FIX: return True
        easter=self.get_easter_date(date_obj.year)
        if date_obj in (easter-datetime.timedelta(days=2), easter+datetime.timedelta(days=1)): return True
        return False
    def calculate_shift(self, date_str, start_str, end_str, plan_length_str="", pc_start_str="", pc_end_str="", pnp_start_str="", pnp_end_str="", shift_type="", meal_override="", other_premiums=""):
        start_time=self.parse_time(start_str); end_time=self.parse_time(end_str)
        plan_time=self.parse_time(plan_length_str); pc_start=self.parse_time(pc_start_str); pc_end=self.parse_time(pc_end_str)
        pnp_start=self.parse_time(pnp_start_str); pnp_end=self.parse_time(pnp_end_str)
        try: start_date=datetime.datetime.strptime(date_str,"%Y-%m-%d").date()
        except: return None
        total_minutes=0; night_minutes=0; saturday_minutes=0; sunday_minutes=0; holiday_minutes=0
        pnp_minutes=0; overtime_minutes=0; has_main_shift=False
        is_vacation=shift_type in ["3000-Dovolenka - bežný rok","3010-Riad.dovol.min.r."]
        is_absence=shift_type in ["3440-Náhr.m.Ost.prek.nep","8000-Nemoc","8020-OČR","3191-Náhrada za vyšetrenie"]
        if is_vacation or is_absence:
            abs_mins=308
            if plan_time: abs_mins=plan_time.hour*60+plan_time.minute
            elif start_time and end_time:
                sd=datetime.datetime.combine(start_date,start_time); ed=datetime.datetime.combine(start_date,end_time)
                if ed<sd: ed+=datetime.timedelta(days=1)
                abs_mins=int((ed-sd).total_seconds()/60)
            return {"total_hours":"-","total_hours_dec":0,"night_hours":"-","saturday_hours":"-","sunday_hours":"-","holiday_hours":"-","pnp_hours":"-","pnp_minutes":0,"overtime":"-","meal_allowance":0.0,"other_allowance":0.0,"vacation_minutes":abs_mins,"absence_minutes":abs_mins if is_absence else 0,"is_weekend":start_date.weekday() in (5,6),"is_holiday":self.is_slovak_holiday(start_date)}
        if pnp_start and pnp_end:
            pnp_start_dt=datetime.datetime.combine(start_date,pnp_start)
            if pnp_end < pnp_start: pnp_end_dt=datetime.datetime.combine(start_date+datetime.timedelta(days=1),pnp_end)
            else: pnp_end_dt=datetime.datetime.combine(start_date,pnp_end)
            pnp_minutes=int((pnp_end_dt-pnp_start_dt).total_seconds()/60)
            if pnp_minutes<0: pnp_minutes=0
        if start_time and end_time:
            has_main_shift=True
            start_dt=datetime.datetime.combine(start_date,start_time)
            end_dt=datetime.datetime.combine(start_date+datetime.timedelta(days=1),end_time) if end_time<start_time else datetime.datetime.combine(start_date,end_time)
            total_minutes=int((end_dt-start_dt).total_seconds()/60)
            if pnp_minutes>0: total_minutes=max(0,total_minutes-pnp_minutes)
            curr=start_dt; step=datetime.timedelta(minutes=1)
            pnp_start_dt_real=None; pnp_end_dt_real=None
            if pnp_start and pnp_end:
                base=start_date
                if pnp_start<start_time: base+=datetime.timedelta(days=1)
                pnp_start_dt_real=datetime.datetime.combine(base,pnp_start)
                edp=base+datetime.timedelta(days=1) if pnp_end<pnp_start else base
                pnp_end_dt_real=datetime.datetime.combine(edp,pnp_end)
            while curr<end_dt:
                in_pnp=False
                if pnp_start_dt_real and pnp_end_dt_real and pnp_start_dt_real<=curr<pnp_end_dt_real: in_pnp=True
                if not in_pnp:
                    if curr.hour>=22 or curr.hour<6: night_minutes+=1
                    if curr.weekday()==5: saturday_minutes+=1
                    elif curr.weekday()==6: sunday_minutes+=1
                    if self.is_slovak_holiday(curr.date()): holiday_minutes+=1
                curr+=step
        elif plan_time and shift_type not in ["Štandardný výkon","T.V. (Turnus voľno)","4181-Náhr.za pr.poh.v p.",""]:
            has_main_shift=True; total_minutes=plan_time.hour*60+plan_time.minute
        if shift_type=="4181-Náhr.za pr.poh.v p.": has_main_shift=False; total_minutes=0
        total_hours_decimal=total_minutes/60.0
        if plan_time and has_main_shift:
            pm=plan_time.hour*60+plan_time.minute
            if total_minutes>pm: overtime_minutes=total_minutes-pm
        meal_allowance=0.0; meal_code=""
        if meal_override and meal_override.strip()!="":
            try: meal_allowance=float(meal_override.replace(",",".")); meal_code="Manuálne"
            except: pass
        pc_minutes=0; has_pc=False
        if pc_start and pc_end:
            has_pc=True
            pc_s=datetime.datetime.combine(start_date,pc_start)
            pc_e=datetime.datetime.combine(start_date+datetime.timedelta(days=1),pc_end) if pc_end<pc_start else datetime.datetime.combine(start_date,pc_end)
            pc_minutes=int((pc_e-pc_s).total_seconds()/60)
        no_meal=any(shift_type.startswith(x) for x in ["0011","2125","2160","2190","4181","40"])
        if not meal_code and not no_meal and (has_main_shift or has_pc):
            eval_m=pc_minutes if has_pc else (total_minutes+pnp_minutes)
            eh=eval_m/60.0
            if 5<=eh<=12: meal_allowance=self.rates["meal_a"]
            elif 12<eh<=18: meal_allowance=self.rates["meal_b"]
            elif eh>18: meal_allowance=self.rates["meal_c"]
        other_allowance=0.0
        if shift_type.startswith("2125") and total_minutes>0:
            other_allowance=round(total_minutes/60.0,2); has_main_shift=False; total_minutes=0
        elif other_premiums and other_premiums.strip()!="":
            try: other_allowance=float(other_premiums.replace(",","."))
            except: pass
        def fmt(m): return f"{m//60:02d}:{m%60:02d}" if m!=0 else "00:00"
        return {"total_hours":fmt(total_minutes) if has_main_shift else "-","total_hours_dec":round(total_hours_decimal,2),"night_hours":fmt(night_minutes) if night_minutes>0 else "-","saturday_hours":fmt(saturday_minutes) if saturday_minutes>0 else "-","sunday_hours":fmt(sunday_minutes) if sunday_minutes>0 else "-","holiday_hours":fmt(holiday_minutes) if holiday_minutes>0 else "-","pnp_hours":fmt(pnp_minutes) if pnp_minutes>0 else "-","pnp_minutes":pnp_minutes,"overtime":fmt(overtime_minutes) if overtime_minutes>0 else "-","meal_allowance":round(meal_allowance,2),"other_allowance":round(other_allowance,2),"vacation_minutes":0,"absence_minutes":0,"is_weekend":start_date.weekday() in (5,6),"is_holiday":self.is_slovak_holiday(start_date)}

# ---------- UI KOMPONENTY ----------
class TimePickerPopup(Popup):
    def __init__(self, initial="08:00", callback=None, **kw):
        super().__init__(**kw)
        self.callback=callback
        self.title="Nastaviť čas"; self.size_hint=(0.85,0.6); self.separator_color=(0.2,0.6,0.9,1)
        try: h,m=initial.split(":"); hi=int(h); mi=int(m)
        except: hi,mi=8,0
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        row=BoxLayout(spacing=dp(10))
        self.sp_h=Spinner(text=f"{hi:02d}", values=[f"{i:02d}" for i in range(24)], size_hint_x=0.5, font_size='20sp')
        self.sp_m=Spinner(text=f"{mi:02d}", values=[f"{i:02d}" for i in range(60)], size_hint_x=0.5, font_size='20sp')
        row.add_widget(self.sp_h); row.add_widget(Label(text=":",font_size='22sp',size_hint_x=None,width=dp(20))); row.add_widget(self.sp_m)
        box.add_widget(row)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(10))
        b_cancel=Button(text="Zrušiť",background_normal='',background_color=(0.4,0.4,0.42,1))
        b_ok=Button(text="Potvrdiť",background_normal='',background_color=(0.15,0.55,0.85,1),bold=True)
        b_cancel.bind(on_press=self.dismiss); b_ok.bind(on_press=self.confirm)
        btns.add_widget(b_cancel); btns.add_widget(b_ok); box.add_widget(btns)
        self.content=box
    def confirm(self,*a):
        if self.callback: self.callback(f"{self.sp_h.text}:{self.sp_m.text}")
        self.dismiss()

class RowButton(Button):
    def __init__(self, shift, calc_result, **kw):
        super().__init__(**kw)
        typ=shift.get('shift_type') or shift.get('zmena','')
        base=COLORS.get(typ, (0.20,0.20,0.22,1))
        # sviatok/weekend zosvetlenie
        if calc_result and calc_result.get('is_holiday'): base=(min(base[0]+0.18,1), min(base[1]+0.18,1), min(base[2]+0.18,1),1)
        self.background_normal=''; self.background_color=base
        self.color=(1,1,1,1); self.size_hint_y=None; self.height=dp(72)
        self.halign='left'; self.valign='middle'; self.padding=(dp(12),dp(6))
        date=shift.get('date','')
        start=shift.get('start',''); end=shift.get('end','')
        trains=f"{shift.get('train_first','')} {shift.get('route_from','')} → {shift.get('train_last','')} {shift.get('route_to','')}".strip()
        if not trains: trains=shift.get('poznamka','') or shift.get('note','')
        total=calc_result.get('total_hours','-') if calc_result else '-'
        night=calc_result.get('night_hours','-') if calc_result else '-'
        self.text=f"[b]{date}[/b]  {typ}\n{start}-{end} | {total} | N:{night}  {trains[:36]}"
        self.markup=True
        self.bind(size=lambda *a: setattr(self,'text_size',(self.width-dp(24),None)))

class ZSSKApp(App):
    def build(self):
        self.calculator=ShiftCalculator()
        self.data_file=os.path.join(self.user_data_dir,'data.json')
        self.turnus_file=os.path.join(self.user_data_dir,'turnus.json')
        self.emp_file=os.path.join(self.user_data_dir,'employee.json')
        self._ensure_files()
        self.employee=self.load_employee()
        today=datetime.date.today()
        self.cur_year=self.employee.get('cur_year', today.year)
        self.cur_month=self.employee.get('cur_month', today.month)

        root=BoxLayout(orientation='vertical',padding=dp(6),spacing=dp(4))
        with root.canvas.before:
            Color(0.07,0.09,0.14,1); self.bg=Rectangle(size=root.size,pos=root.pos)
            root.bind(size=lambda *a: (setattr(self.bg,'size',root.size), setattr(self.bg,'pos',root.pos)))

        # ---- HEADER 2 RIADKY (opravený prekryv) ----
        header=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(104),spacing=dp(6))
        nav=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        b_prev=Button(text='◀',size_hint_x=None,width=dp(56),background_normal='',background_color=(0.30,0.32,0.36,1),font_size='18sp')
        b_next=Button(text='▶',size_hint_x=None,width=dp(56),background_normal='',background_color=(0.30,0.32,0.36,1),font_size='18sp')
        self.lbl_month=Label(text='',font_size='19sp',bold=True)
        b_prev.bind(on_press=lambda x:self.shift_month(-1)); b_next.bind(on_press=lambda x:self.shift_month(1))
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next)
        header.add_widget(nav)

        actions=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(6))
        for txt,col,fn in [
            ('Mesiac',(0.32,0.34,0.38,1),self.open_month_picker),
            ('Turnus',(0.55,0.32,0.18,1),self.open_turnus_generator),
            ('Stats',(0.18,0.45,0.32,1),self.open_stats),
            ('Export',(0.15,0.38,0.68,1),self.open_export_menu),
            ('Oprav',(0.65,0.42,0.12,1),self.auto_fill_types),
        ]:
            b=Button(text=txt,background_normal='',background_color=col,font_size='12sp')
            b.bind(on_press=fn); actions.add_widget(b)
        header.add_widget(actions)
        root.add_widget(header)

        # KPI ako v PC verzii
        self.kpi_box=BoxLayout(size_hint_y=None,height=dp(62),spacing=dp(6))
        self.lbl_kpi_main=Label(text='Načítavam...',font_size='11sp',halign='left')
        self.lbl_kpi_night=Label(text='',font_size='11sp',halign='left')
        self.lbl_kpi_meal=Label(text='',font_size='11sp',halign='left')
        for l in [self.lbl_kpi_main,self.lbl_kpi_night,self.lbl_kpi_meal]:
            l.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width,None)))
        self.kpi_box.add_widget(self.lbl_kpi_main); self.kpi_box.add_widget(self.lbl_kpi_night); self.kpi_box.add_widget(self.lbl_kpi_meal)
        root.add_widget(self.kpi_box)

        self.lbl_info=Label(size_hint_y=None,height=dp(22),color=(0.7,0.85,1,1),font_size='11sp'); root.add_widget(self.lbl_info)

        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(5),size_hint_y=None,padding=dp(2))
        self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)

        bottom=BoxLayout(size_hint_y=None,height=dp(58),spacing=dp(6))
        b_add=Button(text='+ Pridať zmenu (PC štýl)',background_normal='',background_color=(0,0.42,0.78,1),font_size='16sp',bold=True)
        b_pay=Button(text='💰 Výplata',size_hint_x=None,width=dp(110),background_normal='',background_color=(0.15,0.55,0.45,1))
        b_add.bind(on_press=lambda x:self.open_editor()); b_pay.bind(on_press=self.open_payroll)
        bottom.add_widget(b_add); bottom.add_widget(b_pay); root.add_widget(bottom)

        self.refresh(); return root

    # ---- PERSISTENCIA ----
    def _ensure_files(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        if not os.path.exists(self.data_file):
            data=[]
            if os.path.exists('data.json'):
                try:
                    with open('data.json',encoding='utf-8') as f: data=json.load(f)
                except: pass
            with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)
        if not os.path.exists(self.turnus_file):
            with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump([],f)
        if not os.path.exists(self.emp_file):
            with open(self.emp_file,'w',encoding='utf-8') as f: json.dump({"name":"Miroslav Kurek","id":"20 814","role":"Rušňovodič","base_salary":"1484.00","norm_hours":"160:00","cur_year":datetime.date.today().year,"cur_month":datetime.date.today().month},f,ensure_ascii=False,indent=2)

    def load_data(self):
        try:
            with open(self.data_file,encoding='utf-8') as f: d=json.load(f)
        except: d=[]
        out=[]
        for x in d:
            if not isinstance(x,dict): continue
            # migrácia starých kľúčov
            if 'date' not in x:
                if 'datum' in x: x['date']=x.pop('datum')
            if 'shift_type' not in x:
                if 'zmena' in x: x['shift_type']=x.pop('zmena')
                elif 'typ' in x: x['shift_type']=x.pop('typ')
                else: x['shift_type']=''
            if 'note' not in x:
                if 'poznamka' in x: x['note']=x.pop('poznamka')
                elif 'poznámka' in x: x['note']=x.pop('poznámka')
                else: x['note']=''
            for k in ['train_first','route_from','train_last','route_to','turnus','start','end','pc_start','pc_end','plan','pnp_start','pnp_end','meal_override','other_premiums']:
                if k not in x: x[k]=''
            if 'uid' not in x: x['uid']=str(uuid.uuid4())
            out.append(x)
        return out

    def save_data(self, data): 
        with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

    def load_turnus(self):
        try:
            with open(self.turnus_file,encoding='utf-8') as f: return json.load(f)
        except: return []
    def save_turnus(self,d):
        with open(self.turnus_file,'w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2)

    def load_employee(self):
        try:
            with open(self.emp_file,encoding='utf-8') as f: return json.load(f)
        except: return {}
    def save_employee(self):
        self.employee['cur_year']=self.cur_year; self.employee['cur_month']=self.cur_month
        with open(self.emp_file,'w',encoding='utf-8') as f: json.dump(self.employee,f,ensure_ascii=False,indent=2)

    # ---- LOGIKA MESIACA ----
    def month_key(self): return f"{self.cur_year:04d}-{self.cur_month:02d}"
    def shift_month(self,d):
        m=self.cur_month+d; y=self.cur_year
        while m>12: m-=12; y+=1
        while m<1: m+=12; y-=1
        self.cur_year,self.cur_month=y,m; self.save_employee(); self.refresh()

    def refresh(self):
        all_data=self.load_data()
        month_data=[d for d in all_data if d.get('date','').startswith(self.month_key())]
        month_data=sorted(month_data, key=lambda x: (x.get('date',''), x.get('start','')))
        self.lbl_month.text=f"{self.month_key()} • {len(month_data)} záznamov"
        self.grid.clear_widgets()
        totals={"worked":0,"night":0,"sat":0,"sun":0,"hol":0,"pnp":0,"meal":0.0,"other":0.0,"overtime":0,"vacation":0}
        for s in month_data:
            calc=self.calculator.calculate_shift(s.get('date',''), s.get('start',''), s.get('end',''), s.get('plan',''), s.get('pc_start',''), s.get('pc_end',''), s.get('pnp_start',''), s.get('pnp_end',''), s.get('shift_type',''), s.get('meal_override',''), s.get('other_premiums',''))
            if calc:
                def p(h): 
                    try: return int(h.split(':')[0])*60+int(h.split(':')[1]) if ':' in h else 0
                    except: return 0
                totals['worked']+=p(calc.get('total_hours','0:00')) if calc.get('total_hours')!='-' else 0
                totals['night']+=p(calc.get('night_hours','0:00')); totals['sat']+=p(calc.get('saturday_hours','0:00'))
                totals['sun']+=p(calc.get('sunday_hours','0:00')); totals['hol']+=p(calc.get('holiday_hours','0:00'))
                totals['pnp']+=calc.get('pnp_minutes',0); totals['overtime']+=p(calc.get('overtime','0:00'))
                totals['meal']+=calc.get('meal_allowance',0.0); totals['other']+=calc.get('other_allowance',0.0)
                totals['vacation']+=calc.get('vacation_minutes',0)
            btn=RowButton(s, calc); btn.bind(on_press=lambda inst,uid=s['uid']: self.open_editor(uid))
            self.grid.add_widget(btn)
        # KPI
        def fmt(m): return f"{m//60:02d}:{m%60:02d}"
        self.lbl_kpi_main.text=f"Fond: {fmt(totals['worked'])} | Dov: {fmt(totals['vacation'])}\nNadčas: {fmt(totals['overtime'])}"
        self.lbl_kpi_night.text=f"Nočná: {fmt(totals['night'])}\nSo: {fmt(totals['sat'])} Ne: {fmt(totals['sun'])}"
        self.lbl_kpi_meal.text=f"Sviatok: {fmt(totals['hol'])} PNP:{fmt(totals['pnp'])}\nStravné: {totals['meal']:.2f}€ Iné:{totals['other']:.2f}€"
        self.current_totals=totals

    # ---- EDITOR - PLNÝ PC ŠTÝL ----
    def open_editor(self, uid=None):
        all_data=self.load_data()
        edit=None
        if uid:
            for d in all_data:
                if d.get('uid')==uid: edit=d; break
        is_new=edit is None
        if is_new:
            edit={"uid":str(uuid.uuid4()),"date":f"{self.month_key()}-01","shift_type":"Štandardný výkon","train_first":"","route_from":"","train_last":"","route_to":"","turnus":"","start":"","end":"","pc_start":"","pc_end":"","plan":"","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":""}

        popup=Popup(title='Upraviť zmenu' if not is_new else 'Pridať zmenu', size_hint=(0.96,0.92), separator_color=(0.2,0.6,0.9,1), auto_dismiss=False)
        root=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(10))
        scroll=ScrollView(size_hint_y=1)
        form=GridLayout(cols=1,spacing=dp(10),size_hint_y=None,padding=dp(4)); form.bind(minimum_height=form.setter('height'))

        # helper na riadok
        def add_row(label_text, widget):
            box=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(68),spacing=dp(4))
            box.add_widget(Label(text=label_text,size_hint_y=None,height=dp(20),halign='left',font_size='12sp',color=(0.7,0.8,0.95,1)))
            box.add_widget(widget); form.add_widget(box); return box

        inp_date=TextInput(text=edit.get('date',''),multiline=False,size_hint_y=None,height=dp(40))
        add_row('Dátum (YYYY-MM-DD)', inp_date)

        sp_type=Spinner(text=edit.get('shift_type') or 'Štandardný výkon', values=SHIFT_TYPES, size_hint_y=None,height=dp(44),background_normal='',background_color=(0.25,0.28,0.32,1))
        add_row('Mzdový druh / Typ zmeny', sp_type)

        # Turnus + vlaky
        row_turnus=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
        inp_turnus=TextInput(text=edit.get('turnus',''),hint_text='TD',multiline=False,size_hint_x=0.3)
        inp_train_first=TextInput(text=edit.get('train_first',''),hint_text='Vlak 1.',multiline=False,size_hint_x=0.35)
        inp_train_last=TextInput(text=edit.get('train_last',''),hint_text='Vlak posl.',multiline=False,size_hint_x=0.35)
        row_turnus.add_widget(inp_turnus); row_turnus.add_widget(inp_train_first); row_turnus.add_widget(inp_train_last)
        add_row('Turnus + Vlaky', row_turnus)

        row_route=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
        inp_from=TextInput(text=edit.get('route_from',''),hint_text='Z',multiline=False)
        inp_to=TextInput(text=edit.get('route_to',''),hint_text='Do',multiline=False)
        row_route.add_widget(inp_from); row_route.add_widget(inp_to)
        add_row('Trať Z → Do', row_route)

        # Časy
        def time_row(label, key):
            r=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(6))
            inp=TextInput(text=edit.get(key,''),hint_text='HH:MM',multiline=False)
            btn=Button(text='🕒',size_hint_x=None,width=dp(48),background_normal='',background_color=(0.25,0.45,0.65,1))
            def pick(*_):
                TimePickerPopup(initial=inp.text or "08:00", callback=lambda v: setattr(inp,'text',v)).open()
            btn.bind(on_press=pick); r.add_widget(inp); r.add_widget(btn)
            add_row(label, r); return inp

        inp_start=time_row('Nástup', 'start')
        inp_end=time_row('Koniec', 'end')
        inp_plan=time_row('Plán (FPČ)', 'plan')
        inp_pc_s=time_row('PC začiatok', 'pc_start')
        inp_pc_e=time_row('PC koniec', 'pc_end')
        inp_pnp_s=time_row('PNP začiatok', 'pnp_start')
        inp_pnp_e=time_row('PNP koniec', 'pnp_end')

        inp_meal=TextInput(text=edit.get('meal_override',''),hint_text='napr. 9.30 alebo prázdne = auto',multiline=False,size_hint_y=None,height=dp(40))
        add_row('Stravné override (€) - prázdne = automatika z PC', inp_meal)
        inp_other=TextInput(text=edit.get('other_premiums',''),hint_text='Iné príplatky €',multiline=False,size_hint_y=None,height=dp(40))
        add_row('Iné príplatky / 2125 = hodiny sa počítajú ako €', inp_other)
        inp_note=TextInput(text=edit.get('note',''),hint_text='Poznámka',multiline=True,size_hint_y=None,height=dp(70))
        add_row('Poznámka', inp_note)

        # náhľad kalkulácie live
        lbl_preview=Label(text='Náhľad: -',size_hint_y=None,height=dp(50),color=(0.6,1,0.6,1),font_size='12sp')
        form.add_widget(lbl_preview)
        def update_preview(*_):
            c=self.calculator.calculate_shift(inp_date.text, inp_start.text, inp_end.text, inp_plan.text, inp_pc_s.text, inp_pc_e.text, inp_pnp_s.text, inp_pnp_e.text, sp_type.text, inp_meal.text, inp_other.text)
            if c: lbl_preview.text=f"Odprac: {c['total_hours']} | Nočná:{c['night_hours']} So:{c['saturday_hours']} Ne:{c['sunday_hours']} Sv:{c['holiday_hours']} Stravné:{c['meal_allowance']}€"
        for w in [inp_date,inp_start,inp_end,inp_plan,inp_pc_s,inp_pc_e,inp_pnp_s,inp_pnp_e,inp_meal,inp_other]: w.bind(text=lambda *a: update_preview())
        sp_type.bind(text=lambda *a: update_preview()); update_preview()

        scroll.add_widget(form); root.add_widget(scroll)

        btns=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(8))
        b_cancel=Button(text='Zrušiť',background_normal='',background_color=(0.4,0.4,0.42,1))
        b_del=Button(text='Zmazať',background_normal='',background_color=(0.75,0.2,0.2,1),size_hint_x=None,width=dp(86))
        b_save=Button(text='Uložiť',background_normal='',background_color=(0.12,0.55,0.25,1),bold=True)
        b_cancel.bind(on_press=popup.dismiss)
        def do_delete(*_):
            if not is_new:
                nd=[d for d in all_data if d.get('uid')!=uid]; self.save_data(nd); self.refresh(); popup.dismiss()
        def do_save(*_):
            try: datetime.datetime.strptime(inp_date.text,"%Y-%m-%d")
            except: self.show_info('Zlý formát dátumu, použite YYYY-MM-DD'); return
            new_shift={"uid":edit['uid'],"date":inp_date.text.strip(),"shift_type":sp_type.text,"train_first":inp_train_first.text,"route_from":inp_from.text,"train_last":inp_train_last.text,"route_to":inp_to.text,"turnus":inp_turnus.text,"start":inp_start.text,"end":inp_end.text,"pc_start":inp_pc_s.text,"pc_end":inp_pc_e.text,"plan":inp_plan.text,"pnp_start":inp_pnp_s.text,"pnp_end":inp_pnp_e.text,"meal_override":inp_meal.text,"other_premiums":inp_other.text,"note":inp_note.text,"zmena":sp_type.text,"poznamka":inp_note.text}
            if is_new: all_data.append(new_shift)
            else:
                for i,d in enumerate(all_data):
                    if d.get('uid')==uid: all_data[i]=new_shift; break
            self.save_data(sorted(all_data, key=lambda x: (x.get('date',''), x.get('start','')))); self.refresh(); popup.dismiss()
        b_del.bind(on_press=do_delete); b_save.bind(on_press=do_save)
        btns.add_widget(b_cancel); 
        if not is_new: btns.add_widget(b_del)
        btns.add_widget(b_save); root.add_widget(btns)
        popup.content=root; popup.open()

    # ---- TURNUS GENERATOR (ako PC) ----
    def open_turnus_generator(self,*a):
        popup=Popup(title='Generátor turnusu - ako PC verzia', size_hint=(0.94,0.82), separator_color=(0.9,0.5,0.15,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        box.add_widget(Label(text='TD na 1. deň v mesiaci a dĺžka turnusu\nGeneruje celý mesiac podľa šablón alebo PATTERN fallback',font_size='12sp',size_hint_y=None,height=dp(50)))
        inp_td=TextInput(text='1',hint_text='TD na 1.deň',multiline=False,size_hint_y=None,height=dp(44))
        inp_len=TextInput(text='8',hint_text='Dĺžka turnusu (napr. 8)',multiline=False,size_hint_y=None,height=dp(44))
        box.add_widget(inp_td); box.add_widget(inp_len)
        lbl=Label(text='',font_size='11sp',color=(0.8,0.9,1,1)); box.add_widget(lbl)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        b_cancel=Button(text='Zrušiť',background_normal='',background_color=(0.4,0.4,0.42,1)); b_gen=Button(text='Generovať',background_normal='',background_color=(0.75,0.45,0.12,1),bold=True)
        b_cancel.bind(on_press=popup.dismiss)
        def gen(*_):
            try: start_td=int(inp_td.text); turn_len=int(inp_len.text)
            except: lbl.text='Chyba: zadaj čísla'; return
            data=self.load_data(); turnus_data=self.load_turnus()
            days_in_month=calendar.monthrange(self.cur_year,self.cur_month)[1]
            existing={d['date']:d for d in data if not d.get('date','').startswith(self.month_key())}
            new_month=[]
            added=0
            for day in range(1,days_in_month+1):
                ds=f"{self.cur_year:04d}-{self.cur_month:02d}-{day:02d}"
                cur_td=((start_td-1+day-1)%turn_len)+1
                date_obj=datetime.date(self.cur_year,self.cur_month,day)
                is_hol=self.calculator.is_slovak_holiday(date_obj)
                wd=["Po","Ut","St","Št","Pi","So","Ne"][date_obj.weekday()]; target="Sv" if is_hol else wd
                match=None
                for t in turnus_data:
                    if str(t.get('td'))==str(cur_td) and target in t.get('days',[]):
                        match=t; break
                if match:
                    shift={"uid":str(uuid.uuid4()),"date":ds,"shift_type":match.get('shift_type','Štandardný výkon'),"train_first":match.get('train_first',''),"route_from":match.get('route_from',''),"train_last":match.get('train_last',''),"route_to":match.get('route_to',''),"turnus":str(cur_td),"start":match.get('start',''),"end":match.get('end',''),"pc_start":match.get('pc_start',''),"pc_end":match.get('pc_end',''),"plan":match.get('plan',''),"pnp_start":match.get('pnp_start',''),"pnp_end":match.get('pnp_end',''),"meal_override":match.get('meal_override',''),"other_premiums":match.get('other_premiums',''),"note":""}
                else:
                    typ=PATTERN[(day-1)%len(PATTERN)]; is_tv=typ in ('Voľno',)
                    shift={"uid":str(uuid.uuid4()),"date":ds,"shift_type":"T.V. (Turnus voľno)" if is_tv else "Štandardný výkon","train_first":"T.V." if is_tv else "","route_from":"","train_last":"T.V." if is_tv else "","route_to":"","turnus":str(cur_td),"start":"","end":"","pc_start":"","pc_end":"","plan":"08:00" if not is_tv else "","pnp_start":"","pnp_end":"","meal_override":"","other_premiums":"","note":typ,"zmena":typ}
                new_month.append(shift); added+=1
            # zmaž starý mesiac a pridaj nový
            keep=[d for d in data if not d.get('date','').startswith(self.month_key())]
            keep.extend(new_month); self.save_data(keep); self.refresh(); popup.dismiss(); self.show_info(f'Vygenerovaných {added} dní pre {self.month_key()}')
        b_gen.bind(on_press=gen); btns.add_widget(b_cancel); btns.add_widget(b_gen); box.add_widget(btns)
        popup.content=box; popup.open()

    # ---- OPRAV TYPY (vylepšené) ----
    def auto_fill_types(self,*a):
        data=self.load_data(); changed=0
        for d in data:
            if d.get('date','').startswith(self.month_key()) and not d.get('shift_type'):
                try: day=int(d['date'].split('-')[2]); d['shift_type']=PATTERN[(day-1)%len(PATTERN)]; changed+=1
                except: pass
        self.save_data(data); self.refresh(); self.show_info(f'Opravených {changed} záznamov')

    # ---- MESIAC PICKER ----
    def open_month_picker(self,*a):
        temp_year=[self.cur_year]
        popup=Popup(title='Vyber mesiac',size_hint=(0.92,None),height=dp(470),separator_color=(0.2,0.6,0.9,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        year_box=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10))
        b_minus=Button(text='- rok',size_hint_x=None,width=dp(78),background_normal='',background_color=(0.32,0.32,0.34,1))
        b_plus=Button(text='+ rok',size_hint_x=None,width=dp(78),background_normal='',background_color=(0.32,0.32,0.34,1))
        lbl_year=Label(text=str(temp_year[0]),font_size='18sp',bold=True)
        def chg(d): temp_year[0]+=d; lbl_year.text=str(temp_year[0])
        b_minus.bind(on_press=lambda x: chg(-1)); b_plus.bind(on_press=lambda x: chg(1))
        year_box.add_widget(b_minus); year_box.add_widget(lbl_year); year_box.add_widget(b_plus); box.add_widget(year_box)
        grid=GridLayout(cols=3,spacing=dp(8),size_hint_y=1,row_default_height=dp(52),row_force_default=True)
        for m in range(1,13):
            is_cur=(m==self.cur_month and temp_year[0]==self.cur_year); bg=(0.15,0.55,0.85,1) if is_cur else (0.24,0.24,0.26,1)
            b=Button(text=f"{m:02d}\n{calendar.month_abbr[m]}",background_normal='',background_color=bg,font_size='13sp',halign='center')
            def make_cb(mm): return lambda inst: (setattr(self,'cur_year',temp_year[0]), setattr(self,'cur_month',mm), self.save_employee(), popup.dismiss(), self.refresh())
            b.bind(on_press=make_cb(m)); grid.add_widget(b)
        box.add_widget(grid)
        b_close=Button(text='Zavrieť',size_hint_y=None,height=dp(48),background_normal='',background_color=(0.36,0.36,0.38,1)); b_close.bind(on_press=popup.dismiss); box.add_widget(b_close)
        popup.content=box; popup.open()

    # ---- STATS ----
    def open_stats(self,*a):
        data=[d for d in self.load_data() if d.get('date','').startswith(self.month_key())]
        cnt={}; hours={}
        for d in data:
            k=d.get('shift_type','bez typu') or 'bez typu'; cnt[k]=cnt.get(k,0)+1
            c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
            if c and c.get('total_hours')!='-':
                try: h=int(c['total_hours'].split(':')[0]); hours[k]=hours.get(k,0)+h
                except: pass
        popup=Popup(title=f'Prehľad {self.month_key()}',size_hint=(0.92,None),height=dp(500))
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
        scroll=ScrollView(); grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None); grid.bind(minimum_height=grid.setter('height'))
        if not cnt: grid.add_widget(Label(text='Žiadne dáta',size_hint_y=None,height=dp(30)))
        else:
            for k in sorted(cnt.keys()):
                row=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(8))
                row.add_widget(Label(text=k,size_hint_x=0.6,halign='left',font_size='12sp')); row.add_widget(Label(text=f"{cnt[k]}x / {hours.get(k,0)}h",size_hint_x=0.4,halign='right',font_size='12sp',color=(0.7,1,0.7,1)))
                grid.add_widget(row)
            grid.add_widget(Label(text=f"Celkom: {len(data)} zmien",size_hint_y=None,height=dp(30),bold=True))
        scroll.add_widget(grid); root.add_widget(scroll)
        b=Button(text='OK',size_hint_y=None,height=dp(48),background_normal='',background_color=(0.22,0.45,0.32,1)); b.bind(on_press=popup.dismiss); root.add_widget(b)
        popup.content=root; popup.open()

    # ---- VÝPLATA (zjednodušený mzdový modul) ----
    def open_payroll(self,*a):
        t=self.current_totals; base=float(self.employee.get('base_salary','1484').replace(',','.')) if self.employee.get('base_salary') else 1484.0
        norm_s=self.employee.get('norm_hours','160:00'); 
        try: nh,nm=map(int,norm_s.split(':')); norm_dec=nh+nm/60.0
        except: norm_dec=160.0
        hod=base/norm_dec if norm_dec>0 else 9.27
        worked_h=t.get('worked',0)/60.0; night_h=t.get('night',0)/60.0; sat_h=t.get('sat',0)/60.0; sun_h=t.get('sun',0)/60.0; hol_h=t.get('hol',0)/60.0
        sum_base=worked_h*hod; sum_night=night_h*2.10; sum_sat=sat_h*2.63; sum_sun=sun_h*5.26; sum_hol=hol_h*13.88
        hruba=sum_base+sum_night+sum_sat+sum_sun+sum_hol+t.get('other',0)+65.0; cista=hruba*0.73; k_vyp=cista+t.get('meal',0)
        popup=Popup(title=f'Výplata odhad {self.month_key()}',size_hint=(0.92,None),height=dp(460))
        box=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(6))
        for txt in [f"Základ: {sum_base:.2f}€ ({worked_h:.1f}h x {hod:.2f})", f"Nočné: {sum_night:.2f}€", f"Víkend So+Ne: {(sum_sat+sum_sun):.2f}€", f"Sviatok: {sum_hol:.2f}€", f"Iné: {t.get('other',0):.2f}€ + 65€ prémia", f"---", f"HRUBÁ: {hruba:.2f}€", f"ČISTÁ ~73%: {cista:.2f}€", f"Stravné: {t.get('meal',0):.2f}€", f"SPOLU K VÝPLATE: {k_vyp:.2f}€"]:
            box.add_widget(Label(text=txt,font_size='13sp',halign='left',size_hint_y=None,height=dp(26)))
        b=Button(text='Zavrieť',size_hint_y=None,height=dp(44),background_normal='',background_color=(0.32,0.32,0.34,1)); b.bind(on_press=popup.dismiss); box.add_widget(b)
        popup.content=box; popup.open()

    # ---- EXPORT ----
    def open_export_menu(self,*a):
        popup=Popup(title='Export',size_hint=(0.86,None),height=dp(380),separator_color=(0.2,0.6,0.9,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))
        for txt,fn in [('Export CSV (mesiac)',self.export_csv),('Export JSON (všetko)',self.export_json),('Report TXT (ako PC)',self.export_report)]:
            b=Button(text=txt,size_hint_y=None,height=dp(48),background_normal='',background_color=(0.22,0.34,0.55,1)); b.bind(on_press=lambda inst,f=fn: (f(), popup.dismiss())); box.add_widget(b)
        b_c=Button(text='Zrušiť',size_hint_y=None,height=dp(44),background_normal='',background_color=(0.36,0.36,0.38,1)); b_c.bind(on_press=popup.dismiss); box.add_widget(b_c)
        popup.content=box; popup.open()

    def export_csv(self,*a):
        fname=f"zsskzmeny_{self.month_key()}.csv"; out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['datum','mzdovy_druh','turnus','nastup','koniec','plan','pc_start','pc_end','pnp_start','pnp_end','celkom','nocna','sobota','nedela','sviatok','pnp','nadcas','stravne','ine','vlak','poznamka'])
                for d in sorted(self.load_data(), key=lambda x:x.get('date','')):
                    if not d.get('date','').startswith(self.month_key()): continue
                    c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                    w.writerow([d.get('date'),d.get('shift_type'),d.get('turnus'),d.get('start'),d.get('end'),d.get('plan'),d.get('pc_start'),d.get('pc_end'),d.get('pnp_start'),d.get('pnp_end'), c.get('total_hours') if c else '', c.get('night_hours') if c else '', c.get('saturday_hours') if c else '', c.get('sunday_hours') if c else '', c.get('holiday_hours') if c else '', c.get('pnp_hours') if c else '', c.get('overtime') if c else '', c.get('meal_allowance') if c else '', c.get('other_allowance') if c else '', f"{d.get('train_first','')} {d.get('route_from','')} {d.get('train_last','')} {d.get('route_to','')}", d.get('note','')])
            self.show_info(f'CSV export: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')

    def export_json(self,*a):
        fname=f"zsskzmeny_all_{datetime.date.today().isoformat()}.json"; out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',encoding='utf-8') as f: json.dump({"employee_info":self.employee,"shifts_data":self.load_data(),"turnus_data":self.load_turnus()},f,ensure_ascii=False,indent=2)
            self.show_info(f'JSON export: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')

    def export_report(self,*a):
        fname=f"report_{self.month_key()}.txt"; out=os.path.join(self.user_data_dir,fname)
        try:
            lines=[f"PREVÁDZKOVÝ ZÁZNAM {self.month_key()}", f"Zamestnanec: {self.employee.get('name','')} {self.employee.get('id','')}", "="*60]
            for d in sorted([x for x in self.load_data() if x.get('date','').startswith(self.month_key())], key=lambda x:x.get('date','')):
                c=self.calculator.calculate_shift(d.get('date',''),d.get('start',''),d.get('end',''),d.get('plan',''),d.get('pc_start',''),d.get('pc_end',''),d.get('pnp_start',''),d.get('pnp_end',''),d.get('shift_type',''),d.get('meal_override',''),d.get('other_premiums',''))
                lines.append(f"{d.get('date')} {d.get('shift_type')[:24]:24} {d.get('start',''):5}-{d.get('end',''):5} {c.get('total_hours','-') if c else '-':5} N:{c.get('night_hours','-') if c else '-'} {d.get('note','')}")
            with open(out,'w',encoding='utf-8') as f: f.write("\n".join(lines))
            self.show_info(f'Report: {out}')
        except Exception as e: self.show_info(f'Chyba: {e}')

    def show_info(self,msg):
        p=Popup(title='Info',size_hint=(0.86,None),height=dp(260)); b=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10))
        b.add_widget(Label(text=msg,halign='center')); btn=Button(text='OK',size_hint_y=None,height=dp(44),background_normal='',background_color=(0.32,0.32,0.34,1)); btn.bind(on_press=p.dismiss); b.add_widget(btn); p.content=b; p.open()

if __name__=='__main__': ZSSKApp().run()
