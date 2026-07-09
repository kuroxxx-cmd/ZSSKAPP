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
    '': (0.20,0.20,0.22,1)
}
HODINY = {'Ranná':8,'Poobedná':8,'Nočná':12,'Školenie':8}

class RowButton(Button):
    def __init__(self, typ='', **kwargs):
        super().__init__(**kwargs)
        self.background_normal=''; self.background_color=COLORS.get(typ, COLORS[''])
        self.color=(1,1,1,1); self.size_hint_y=None; self.height=dp(50)
        self.halign='left'; self.valign='middle'; self.padding=(dp(12),dp(6))
        self.bind(size=lambda *a: setattr(self,'text_size',(self.width-dp(24),None)))

class ZSSKApp(App):
    def build(self):
        self.data_file=os.path.join(self.user_data_dir,'data.json')
        self._ensure()
        self.cur_year, self.cur_month = 2026, 7

        root=BoxLayout(orientation='vertical',padding=dp(6),spacing=dp(4))
        with root.canvas.before:
            Color(0.08,0.08,0.10,1); self.bg=Rectangle(size=root.size,pos=root.pos); root.bind(size=lambda *a: setattr(self.bg,'size',root.size))

        # ---- HLAVICKA 2 RIADKY (oprava prekryvu) ----
        header=BoxLayout(orientation='vertical',size_hint_y=None,height=dp(92),spacing=dp(4))
        nav=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(4))
        b_prev=Button(text='<',size_hint_x=None,width=dp(48)); b_next=Button(text='>',size_hint_x=None,width=dp(48))
        self.lbl_month=Label(text='',font_size='18sp',bold=True)
        b_prev.bind(on_press=lambda x:self.shift_month(-1)); b_next.bind(on_press=lambda x:self.shift_month(1))
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next)
        header.add_widget(nav)

        actions=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(4))
        b_mesiac=Button(text='Mesiac'); b_stats=Button(text='Stats',background_color=(0.2,0.6,0.4,1))
        b_export=Button(text='Export',background_color=(0.15,0.4,0.75,1))
        b_fix=Button(text='Oprav typy',background_color=(0.8,0.5,0.15,1))
        b_mesiac.bind(on_press=self.open_month_picker); b_stats.bind(on_press=self.open_stats)
        b_export.bind(on_press=self.export_csv); b_fix.bind(on_press=self.auto_fill_types)
        for b in [b_mesiac,b_stats,b_export,b_fix]: actions.add_widget(b)
        header.add_widget(actions)
        root.add_widget(header)

        self.lbl_info=Label(size_hint_y=None,height=dp(22),color=(0.7,0.85,1,1),font_size='12sp'); root.add_widget(self.lbl_info)

        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(3),size_hint_y=None,padding=dp(2))
        self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)

        b_add=Button(text='+ Pridať zmenu',size_hint_y=None,height=dp(54),background_color=(0,0.45,0.8,1),font_size='18sp')
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
        for x in d:
            if 'date' not in x and 'datum' in x: x['date']=x.pop('datum')
            if 'zmena' not in x: x['zmena']=''
            if 'poznamka' not in x: x['poznamka']=''
        return d
    def save(self,d):
        with open(self.data_file,'w',encoding='utf-8') as f: json.dump(d,f,ensure_ascii=False,indent=2)

    def month_key(self): return f"{self.cur_year:04d}-{self.cur_month:02d}"
    def shift_month(self,delta):
        m=self.cur_month+delta; y=self.cur_year
        while m>12: m-=12; y+=1
        while m<1: m+=12; y-=1
        self.cur_year,self.cur_month=y,m; self.refresh()

    def refresh(self):
        self.grid.clear_widgets(); data=self.load(); mk=self.month_key()
        filtered=[d for d in data if d.get('date','').startswith(mk)]
        self.lbl_month.text=mk
        total_h=sum(HODINY.get(d.get('zmena',''),0) for d in filtered)
        nocne=sum(1 for d in filtered if d.get('zmena')=='Nočná')
        self.lbl_info.text=f"{len(filtered)}/{len(data)} • {total_h}h • Nočné: {nocne}"
        if not filtered:
            self.grid.add_widget(Label(text='Žiadne záznamy\nKlikni + Pridať',size_hint_y=None,height=dp(70),color=(0.6,0.6,0.6,1))); return
        for item in sorted(filtered,key=lambda x:x.get('date',''),reverse=True):
            typ=item.get('zmena',''); txt=f"{item.get('date','?')}  •  {typ or 'bez typu'}" + (f"  – {item.get('poznamka','')}" if item.get('poznamka') else "")
            btn=RowButton(typ=typ,text=txt); idx=data.index(item)
            btn.bind(on_press=lambda inst,i=idx: self.open_editor(i)); self.grid.add_widget(btn)

    # ---- EDITOR OPRAVENÝ (žiadna veľká prázdna plocha) ----
    def open_editor(self,index=None):
        data=self.load(); is_edit=index is not None; it=data[index] if is_edit else {}
        popup=Popup(title='Upraviť' if is_edit else 'Pridať zmenu',size_hint=(0.92,0.62))
        box=BoxLayout(orientation='vertical',spacing=dp(10),padding=dp(12))

        def row(lbl_text, widget):
            r=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
            r.add_widget(Label(text=lbl_text,size_hint_x=0.32,halign='right',valign='middle'))
            r.add_widget(widget); return r

        ed_date=TextInput(text=it.get('date',datetime.date.today().strftime('%Y-%m-%d')),multiline=False)
        ed_typ=Spinner(text=it.get('zmena','Ranná') or 'Ranná',values=['Ranná','Poobedná','Nočná','Voľno','Dovolenka','PN','Školenie',''])
        ed_pozn=TextInput(text=it.get('poznamka',''),hint_text='Poznámka',multiline=False)

        box.add_widget(row('Dátum',ed_date)); box.add_widget(row('Typ',ed_typ)); box.add_widget(row('Poznámka',ed_pozn))
        box.add_widget(Label(size_hint_y=1))  # spacer malý

        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        b1=Button(text='Zrušiť'); b2=Button(text='Uložiť',background_color=(0.2,0.6,0.3,1))
        btns.add_widget(b1); btns.add_widget(b2)
        if is_edit:
            b3=Button(text='Vymazať',background_color=(0.8,0.2,0.2,1)); btns.add_widget(b3)
            b3.bind(on_press=lambda x:(self.delete(index),popup.dismiss()))
        box.add_widget(btns); popup.content=box
        b1.bind(on_press=popup.dismiss); b2.bind(on_press=lambda x:(self.save_item(index,ed_date.text,ed_typ.text,ed_pozn.text),popup.dismiss()))
        popup.open()

    def save_item(self,i,d,t,p):
        data=self.load(); new={'date':d.strip(),'zmena':t,'poznamka':p.strip()}
        if i is None: data.append(new)
        else: data[i]=new
        self.save(data); self.refresh()
    def delete(self,i): d=self.load(); del d[i]; self.save(d); self.refresh()

    def auto_fill_types(self,*a):
        # NOVÁ FUNKCIA: doplní prázdne typy podľa jednoduchého turnusu 4-smenného
        data=self.load(); pattern=['Ranná','Ranná','Poobedná','Poobedná','Nočná','Nočná','Voľno','Voľno']
        mk=self.month_key(); c=0
        for d in data:
            if d.get('date','').startswith(mk) and not d.get('zmena'):
                day=int(d['date'].split('-')[2]); d['zmena']=pattern[(day-1)%len(pattern)]; c+=1
        self.save(data); self.lbl_info.text=f'Doplnené {c} typov turnusom'; self.refresh()

    def open_month_picker(self,*a):
        popup=Popup(title='Vyber mesiac',size_hint=(0.92,0.78))
        box=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(10))
        year_box=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        lbl=Label(text=str(self.cur_year)); b1=Button(text='- rok',size_hint_x=None,width=dp(70)); b2=Button(text='+ rok',size_hint_x=None,width=dp(70))
        def chg(d): self.cur_year+=d; lbl.text=str(self.cur_year)
        b1.bind(on_press=lambda x: chg(-1)); b2.bind(on_press=lambda x: chg(1))
        year_box.add_widget(b1); year_box.add_widget(lbl); year_box.add_widget(b2); box.add_widget(year_box)
        grid=GridLayout(cols=3,spacing=dp(6),size_hint_y=None); grid.bind(minimum_height=grid.setter('height')); grid.height=dp(300)
        for m in range(1,13):
            b=Button(text=f"{m:02d}\n{calendar.month_abbr[m]}"); b.bind(on_press=lambda inst,mm=m: (setattr(self,'cur_month',mm),popup.dismiss(),self.refresh()))
            grid.add_widget(b)
        box.add_widget(grid)
        b_close=Button(text='Zavrieť',size_hint_y=None,height=dp(44)); b_close.bind(on_press=popup.dismiss); box.add_widget(b_close)
        popup.content=box; popup.open()

    def open_stats(self,*a):
        data=[d for d in self.load() if d.get('date','').startswith(self.month_key())]; cnt={}
        for d in data: cnt[d.get('zmena','')]=cnt.get(d.get('zmena',''),0)+1
        txt=f"Mesiac: {self.month_key()}\n\n"
        for k,v in cnt.items(): txt+=f"{k or 'bez typu'}: {v}\n"
        txt+=f"\nCelkom hodín: {sum(HODINY.get(k,0)*v for k,v in cnt.items())}h"
        popup=Popup(title='Prehľad',size_hint=(0.85,0.6)); b=BoxLayout(orientation='vertical',padding=dp(12)); b.add_widget(Label(text=txt,halign='left'))
        btn=Button(text='OK',size_hint_y=None,height=dp(44)); btn.bind(on_press=popup.dismiss); b.add_widget(btn); popup.content=b; popup.open()

    def export_csv(self,*a):
        out=os.path.join(self.user_data_dir,'zsskzmeny_export.csv')
        try:
            with open(out,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['datum','zmena','poznamka'])
                for d in self.load(): w.writerow([d.get('date'),d.get('zmena'),d.get('poznamka')])
            self.lbl_info.text=f'Export: {os.path.basename(out)}'
        except Exception as e: self.lbl_info.text=f'Chyba: {e}'

if __name__=='__main__': ZSSKApp().run()
