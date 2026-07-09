import json, os, datetime, calendar, csv
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.widget import Widget
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

COLORS = {
    'Ranná': (0.15,0.55,0.85,1),
    'Poobedná': (0.85,0.55,0.15,1),
    'Nočná': (0.32,0.32,0.82,1),
    'Voľno': (0.25,0.65,0.25,1),
    'Dovolenka': (0.75,0.45,0.85,1),
    'PN': (0.85,0.25,0.25,1),
    'Školenie': (0.5,0.5,0.5,1),
    '': (0.20,0.20,0.22,1),
    'bez typu': (0.20,0.20,0.22,1),
}
HODINY = {'Ranná':8,'Poobedná':8,'Nočná':12,'Školenie':8}
PATTERN = ['Ranná','Ranná','Poobedná','Poobedná','Nočná','Nočná','Voľno','Voľno']

# Jednoduché SK sviatky 2025-2027 pre zvýraznenie
SK_SVIATKY = {
    "01-01","01-06","05-01","05-08","07-05","08-29","09-01","09-15","11-01","11-17","12-24","12-25","12-26"
}

class RowButton(Button):
    def __init__(self, typ='', is_holiday=False, **kwargs):
        super().__init__(**kwargs)
        base = COLORS.get(typ, COLORS[''])
        # sviatok mierne zosvetli
        if is_holiday and typ in COLORS:
            base = (min(base[0]+0.15,1), min(base[1]+0.15,1), min(base[2]+0.15,1), 1)
        self.background_normal=''; self.background_color=base
        self.color=(1,1,1,1); self.size_hint_y=None; self.height=dp(54)
        self.halign='left'; self.valign='middle'; self.padding=(dp(14),dp(6))
        self.bind(size=lambda *a: setattr(self,'text_size',(self.width-dp(28),None)))

class ZSSKApp(App):
    def build(self):
        self.data_file=os.path.join(self.user_data_dir,'data.json')
        self._ensure()
        today=datetime.date.today()
        self.cur_year, self.cur_month = today.year, today.month

        root=BoxLayout(orientation='vertical',padding=dp(6),spacing=dp(4))
        with root.canvas.before:
            Color(0.08,0.08,0.10,1); self.bg=Rectangle(size=root.size,pos=root.pos)
            root.bind(size=lambda *a: setattr(self.bg,'size',root.size))

        # ---- HLAVICKA 2 RIADKY ----
        header=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(98),spacing=dp(6))
        nav=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        b_prev=Button(text='<',size_hint_x=None,width=dp(52),background_normal='',background_color=(0.3,0.3,0.33,1))
        b_next=Button(text='>',size_hint_x=None,width=dp(52),background_normal='',background_color=(0.3,0.3,0.33,1))
        self.lbl_month=Label(text='',font_size='19sp',bold=True)
        b_prev.bind(on_press=lambda x:self.shift_month(-1)); b_next.bind(on_press=lambda x:self.shift_month(1))
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next)
        header.add_widget(nav)

        actions=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(6))
        b_mesiac=Button(text='Mesiac',background_normal='',background_color=(0.35,0.35,0.38,1))
        b_stats=Button(text='Stats',background_normal='',background_color=(0.18,0.45,0.32,1))
        b_export=Button(text='Export',background_normal='',background_color=(0.15,0.38,0.68,1))
        b_fix=Button(text='Oprav typy',background_normal='',background_color=(0.65,0.42,0.12,1))
        b_mesiac.bind(on_press=self.open_month_picker); b_stats.bind(on_press=self.open_stats)
        b_export.bind(on_press=self.export_csv); b_fix.bind(on_press=self.auto_fill_types)
        for b in [b_mesiac,b_stats,b_export,b_fix]: actions.add_widget(b)
        header.add_widget(actions)
        root.add_widget(header)

        self.lbl_info=Label(size_hint_y=None,height=dp(24),color=(0.7,0.85,1,1),font_size='12sp'); root.add_widget(self.lbl_info)

        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None,padding=dp(2))
        self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)

        b_add=Button(text='+ Pridať zmenu',size_hint_y=None,height=dp(56),background_normal='',background_color=(0,0.42,0.78,1),font_size='18sp',bold=True)
        b_add.bind(on_press=lambda x:self.open_editor()); root.add_widget(b_add)

        self.refresh(); return root

    def _ensure(self):
        if not os.path.exists(self.data_file):
            data=[]
            if os.path.exists('data.json'):
                try:
                    with open('data.json',encoding='utf-8') as f: data=json.load(f)
                except: pass
            os.makedirs(os.path.dirname(self.data_file),exist_ok=True)
            with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

    def load(self):
        try:
            with open(self.data_file,encoding='utf-8') as f: d=json.load(f)
        except: d=[]
        out=[]
        for x in d:
            if not isinstance(x, dict): continue
            # migrácia kľúčov z PC verzie
            if 'date' not in x:
                if 'datum' in x: x['date']=x.pop('datum')
                elif 'Datum' in x: x['date']=x.pop('Datum')
            # typ môže byť pod rôznymi názvami
            if 'zmena' not in x:
                if 'typ' in x: x['zmena']=x.pop('typ')
                elif 'type' in x: x['zmena']=x.pop('type')
                else: x['zmena']=''
            if 'poznamka' not in x:
                if 'poznámka' in x: x['poznamka']=x.pop('poznámka')
                elif 'note' in x: x['poznamka']=x.pop('note')
                else: x['poznamka']=''
            # normalizuj prázdne
            if x.get('zmena') is None: x['zmena']=''
            out.append(x)
        return out

    def save(self,d):
        with open(self.data_file,'w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2)

    def month_key(self): return f"{self.cur_year:04d}-{self.cur_month:02d}"
    def shift_month(self,delta):
        m=self.cur_month+delta; y=self.cur_year
        while m>12: m-=12; y+=1
        while m<1: m+=12; y-=1
        self.cur_year,self.cur_month=y,m; self.refresh()

    def is_holiday(self, date_str):
        try:
            mmdd=date_str[5:10]  # YYYY-MM-DD -> MM-DD
            return mmdd in SK_SVIATKY
        except: return False

    def suggest_next_type(self):
        data=sorted([d for d in self.load() if d.get('date')], key=lambda x:x['date'])
        if not data: return 'Ranná'
        last=data[-1].get('zmena','')
        if last in PATTERN:
            idx=PATTERN.index(last)
            # nájdi ďalší iný typ, ale ak sú dvojice, posuň o 1
            return PATTERN[(idx+1) % len(PATTERN)]
        return 'Ranná'

    def refresh(self):
        self.grid.clear_widgets(); data=self.load(); mk=self.month_key()
        filtered=[d for d in data if d.get('date','').startswith(mk)]
        self.lbl_month.text=mk
        total_h=sum(HODINY.get(d.get('zmena',''),0) for d in filtered)
        nocne=sum(1 for d in filtered if d.get('zmena')=='Nočná')
        bez=sum(1 for d in filtered if not d.get('zmena'))
        info=f"{len(filtered)}/{len(data)} • {total_h}h • Nočné: {nocne}"
        if bez: info+=f" • Bez: {bez}"
        self.lbl_info.text=info
        if not filtered:
            self.grid.add_widget(Label(text='Žiadne záznamy\nKlikni + Pridať',size_hint_y=None,height=dp(80),color=(0.6,0.6,0.6,1))); return
        for item in sorted(filtered,key=lambda x:x.get('date',''),reverse=True):
            typ=item.get('zmena',''); date=item.get('date','?')
            poznamka=item.get('poznamka','').strip()
            holiday=self.is_holiday(date)
            label=f"{date}  •  {typ or 'bez typu'}"
            if poznamka: label+=f"  – {poznamka}"
            if holiday: label+="  ★ sviatok"
            btn=RowButton(typ=typ, is_holiday=holiday, text=label)
            # nájdi index v originálnom liste
            try: idx=data.index(item)
            except: idx=0
            btn.bind(on_press=lambda inst,i=idx: self.open_editor(i)); self.grid.add_widget(btn)

    # ---- EDITOR - OPRAVA ČIERNEJ PLOCHY ----
    def open_editor(self,index=None):
        data=self.load(); is_edit=index is not None; it=data[index] if is_edit else {}
        suggested=self.suggest_next_type() if not is_edit else it.get('zmena','Ranná')
        popup=Popup(title='Upraviť' if is_edit else 'Pridať zmenu',size_hint=(0.92,None),height=dp(380),auto_dismiss=False,separator_color=(0.2,0.6,0.9,1),title_align='left')
        box=BoxLayout(orientation='vertical',spacing=dp(12),padding=[dp(16),dp(14),dp(16),dp(12)])

        def row(lbl_text, widget):
            r=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(10))
            l=Label(text=lbl_text,size_hint_x=0.32,halign='right',valign='middle',color=(0.85,0.85,0.85,1))
            l.bind(size=lambda inst,*a: setattr(inst,'text_size',(inst.width,None)))
            r.add_widget(l); r.add_widget(widget); return r

        ed_date=TextInput(text=it.get('date',datetime.date.today().strftime('%Y-%m-%d')),multiline=False,write_tab=False,font_size='15sp',size_hint_y=None,height=dp(44),background_color=(1,1,1,1),foreground_color=(0,0,0,1))
        ed_typ=Spinner(text=suggested or 'Ranná',values=['Ranná','Poobedná','Nočná','Voľno','Dovolenka','PN','Školenie',''],background_normal='',background_color=(0.38,0.38,0.40,1),color=(1,1,1,1),size_hint_y=None,height=dp(44))
        ed_pozn=TextInput(text=it.get('poznamka',''),hint_text='Poznámka (voliteľné)',multiline=False,font_size='14sp',size_hint_y=None,height=dp(44))

        box.add_widget(row('Dátum',ed_date)); box.add_widget(row('Typ',ed_typ)); box.add_widget(row('Poznámka',ed_pozn))
        box.add_widget(Widget(size_hint_y=None,height=dp(6)))

        btns=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(10))
        b1=Button(text='Zrušiť',background_normal='',background_color=(0.38,0.38,0.40,1))
        b2=Button(text='Uložiť',background_normal='',background_color=(0.16,0.52,0.28,1),bold=True)
        btns.add_widget(b1); btns.add_widget(b2)
        if is_edit:
            b3=Button(text='Vymazať',background_normal='',background_color=(0.68,0.18,0.18,1)); btns.add_widget(b3)
            b3.bind(on_press=lambda x:(self.confirm_delete(index,popup)))
        box.add_widget(btns)
        popup.content=box
        b1.bind(on_press=popup.dismiss)
        b2.bind(on_press=lambda x:(self.save_item(index,ed_date.text,ed_typ.text,ed_pozn.text),popup.dismiss()))
        popup.open()

    def confirm_delete(self, idx, parent_popup):
        confirm=Popup(title='Vymazať?',size_hint=(0.82,None),height=dp(180),separator_color=(0.9,0.2,0.2,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(14))
        box.add_widget(Label(text='Naozaj vymazať tento záznam?\nAkcia je nevratná.',halign='center'))
        row=BoxLayout(size_hint_y=None,height=dp(46),spacing=dp(10))
        b_no=Button(text='Nie',background_normal='',background_color=(0.4,0.4,0.42,1))
        b_yes=Button(text='Áno, vymazať',background_normal='',background_color=(0.75,0.2,0.2,1))
        b_no.bind(on_press=confirm.dismiss)
        b_yes.bind(on_press=lambda x:(self.delete(idx),confirm.dismiss(),parent_popup.dismiss()))
        row.add_widget(b_no); row.add_widget(b_yes); box.add_widget(row); confirm.content=box; confirm.open()

    def save_item(self,i,d,t,p):
        data=self.load()
        d=d.strip()
        # validácia dátumu
        try: datetime.date.fromisoformat(d)
        except:
            self.lbl_info.text='Chyba: dátum musí byť YYYY-MM-DD'; return
        new={'date':d,'zmena':t.strip(),'poznamka':p.strip()}
        if i is None: data.append(new)
        else: data[i]=new
        self.save(data); self.refresh()

    def delete(self,i): d=self.load(); del d[i]; self.save(d); self.refresh()

    def auto_fill_types(self,*a):
        data=self.load(); mk=self.month_key(); c=0
        for d in data:
            if d.get('date','').startswith(mk):
                cur=d.get('zmena','').strip()
                if not cur or cur=='bez typu':
                    try: day=int(d['date'].split('-')[2]); d['zmena']=PATTERN[(day-1)%len(PATTERN)]; c+=1
                    except: continue
        if c==0:
            # skús vyplniť celý mesiac ak je prázdny
            self.ask_fill_whole_month()
            return
        self.save(data); self.refresh()
        self.show_info(f'Doplnené {c} záznamov podľa turnusu\n{PATTERN}')

    def ask_fill_whole_month(self):
        # ak je mesiac úplne prázdny alebo všetko bez typu, ponúkni vyplniť celý mesiac
        popup=Popup(title='Vyplniť mesiac?',size_hint=(0.88,None),height=dp(240),separator_color=(0.8,0.5,0.15,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(14))
        box.add_widget(Label(text=f'Mesiac {self.month_key()} má 0 prázdnych typov.\nChceš vygenerovať celý mesiac podľa turnusu?',halign='center'))
        row=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(10))
        b_no=Button(text='Zrušiť',background_normal='',background_color=(0.4,0.4,0.42,1))
        b_yes=Button(text='Vygenerovať 1-31',background_normal='',background_color=(0.65,0.42,0.12,1),bold=True)
        b_no.bind(on_press=popup.dismiss)
        def gen(*_):
            self.fill_whole_month(); popup.dismiss()
        b_yes.bind(on_press=gen)
        row.add_widget(b_no); row.add_widget(b_yes); box.add_widget(row); popup.content=box; popup.open()

    def fill_whole_month(self):
        data=self.load(); days=calendar.monthrange(self.cur_year,self.cur_month)[1]
        existing={d['date']:d for d in data if d.get('date','').startswith(self.month_key())}
        added=0
        for day in range(1,days+1):
            ds=f"{self.cur_year:04d}-{self.cur_month:02d}-{day:02d}"
            if ds not in existing:
                data.append({'date':ds,'zmena':PATTERN[(day-1)%len(PATTERN)],'poznamka':''}); added+=1
            else:
                if not existing[ds].get('zmena'): existing[ds]['zmena']=PATTERN[(day-1)%len(PATTERN)]; added+=1
        self.save(data); self.refresh(); self.show_info(f'Vygenerovaných {added} dní')

    # ---- MESIAC PICKER - OPRAVA PREKRYVU ----
    def open_month_picker(self,*a):
        temp_year=[self.cur_year]
        popup=Popup(title='Vyber mesiac',size_hint=(0.92,None),height=dp(460),auto_dismiss=True,separator_color=(0.2,0.6,0.9,1))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))

        year_box=BoxLayout(size_hint_y=None,height=dp(50),spacing=dp(10))
        b_minus=Button(text='- rok',size_hint_x=None,width=dp(78),background_normal='',background_color=(0.32,0.32,0.34,1))
        b_plus=Button(text='+ rok',size_hint_x=None,width=dp(78),background_normal='',background_color=(0.32,0.32,0.34,1))
        lbl_year=Label(text=str(temp_year[0]),font_size='18sp',bold=True,size_hint_x=1)
        def chg(d):
            temp_year[0]+=d; lbl_year.text=str(temp_year[0])
        b_minus.bind(on_press=lambda x: chg(-1)); b_plus.bind(on_press=lambda x: chg(1))
        year_box.add_widget(b_minus); year_box.add_widget(lbl_year); year_box.add_widget(b_plus)
        box.add_widget(year_box)

        # Grid - fix: size_hint_y=1, row_default_height, žiadny bind na minimum_height ktorý kolabuje
        grid=GridLayout(cols=3,spacing=dp(8),size_hint_y=1,row_default_height=dp(52),row_force_default=True)
        for m in range(1,13):
            is_cur=(m==self.cur_month and temp_year[0]==self.cur_year)
            bg=(0.15,0.55,0.85,1) if is_cur else (0.24,0.24,0.26,1)
            b=Button(text=f"{m:02d}\n{calendar.month_abbr[m]}",background_normal='',background_color=bg,font_size='13sp',halign='center')
            # zachyti mm a rok v čase kliku
            def make_cb(mm):
                return lambda inst: (setattr(self,'cur_year',temp_year[0]), setattr(self,'cur_month',mm), popup.dismiss(), self.refresh())
            b.bind(on_press=make_cb(m))
            grid.add_widget(b)
        box.add_widget(grid)

        b_close=Button(text='Zavrieť',size_hint_y=None,height=dp(48),background_normal='',background_color=(0.36,0.36,0.38,1))
        b_close.bind(on_press=popup.dismiss); box.add_widget(b_close)
        popup.content=box; popup.open()

    def open_stats(self,*a):
        data=[d for d in self.load() if d.get('date','').startswith(self.month_key())]
        cnt={}; hours={}
        for d in data:
            k=d.get('zmena','') or 'bez typu'
            cnt[k]=cnt.get(k,0)+1
            hours[k]=hours.get(k,0)+HODINY.get(d.get('zmena',''),0)
        total_h=sum(hours.values())
        popup=Popup(title='Prehľad',size_hint=(0.90,None),height=dp(420),separator_color=(0.2,0.6,0.4,1))
        root=BoxLayout(orientation='vertical',padding=dp(12),spacing=dp(8))
        title=Label(text=f"Mesiac: {self.month_key()}  •  {len(data)} záznamov",size_hint_y=None,height=dp(26),bold=True)
        root.add_widget(title)

        scroll=ScrollView(size_hint_y=1)
        grid=GridLayout(cols=1,spacing=dp(4),size_hint_y=None,padding=dp(2))
        grid.bind(minimum_height=grid.setter('height'))
        if not cnt:
            grid.add_widget(Label(text='Žiadne dáta',size_hint_y=None,height=dp(30)))
        else:
            for k in sorted(cnt.keys(), key=lambda x: (x=='bez typu', x)):
                v=cnt[k]; h=hours.get(k,0)
                row=BoxLayout(size_hint_y=None,height=dp(36),spacing=dp(8))
                row.add_widget(Label(text=k,size_hint_x=0.45,halign='left',color=(1,1,1,1)))
                row.add_widget(Label(text=f"{v}x",size_hint_x=0.2,halign='center',color=(0.8,0.9,1,1)))
                row.add_widget(Label(text=f"{h}h",size_hint_x=0.25,halign='right',color=(0.7,1,0.7,1)))
                grid.add_widget(row)
            grid.add_widget(Widget(size_hint_y=None,height=dp(8)))
            grid.add_widget(Label(text=f"Celkom hodín: {total_h}h   •   Nočné: {cnt.get('Nočná',0)}",size_hint_y=None,height=dp(30),bold=True))
        scroll.add_widget(grid); root.add_widget(scroll)

        btn=Button(text='OK',size_hint_y=None,height=dp(48),background_normal='',background_color=(0.22,0.45,0.32,1))
        btn.bind(on_press=popup.dismiss); root.add_widget(btn); popup.content=root; popup.open()

    def show_info(self,msg):
        p=Popup(title='Info',size_hint=(0.84,None),height=dp(220),separator_color=(0.2,0.6,0.9,1))
        b=BoxLayout(orientation='vertical',padding=dp(14),spacing=dp(10))
        b.add_widget(Label(text=msg,halign='center'))
        btn=Button(text='OK',size_hint_y=None,height=dp(44),background_normal='',background_color=(0.32,0.32,0.34,1)); btn.bind(on_press=p.dismiss); b.add_widget(btn); p.content=b; p.open()

    def export_csv(self,*a):
        # export do user_data_dir - bez permission problémov na Android 13+
        fname=f"zsskzmeny_{self.month_key()}.csv"
        out=os.path.join(self.user_data_dir,fname)
        try:
            with open(out,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f); w.writerow(['datum','zmena','poznamka','hodiny'])
                for d in sorted(self.load(), key=lambda x:x.get('date','')):
                    typ=d.get('zmena',''); h=HODINY.get(typ,0)
                    w.writerow([d.get('date'),typ,d.get('poznamka',''),h])
            self.lbl_info.text=f'Export OK: {fname}'
            self.show_info(f'Export hotový:\n{out}\n\n{len(self.load())} riadkov')
        except Exception as e: self.lbl_info.text=f'Chyba exportu: {e}'; self.show_info(f'Chyba: {e}')

if __name__=='__main__': ZSSKApp().run()
