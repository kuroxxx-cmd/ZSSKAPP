import datetime

SK_SVIATKY_FIX={"01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"}

class ShiftCalculator:
    def __init__(self, rates=None): 
        self.rates = rates or {"meal_a":9.30,"meal_b":13.80,"meal_c":21.00}
        
    def update_rates(self, rates):
        self.rates = rates
        
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
        if is_vac or is_abs:
            abs_mins=308
            if ptt: abs_mins=ptt.hour*60+ptt.minute
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
