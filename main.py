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
    'Nočná': (0.35,0.35,0.85,1),
    'Voľno': (0.25,0.65,0.25,1),
    'Dovolenka': (0.75,0.45,0.85,1),
    'PN': (0.85,0.25,0.25,1),
    'Školenie': (0.5,0.5,0.5,1),
    '': (0.18,0.18,0.20,1)
}

HODINY = {'Ranná':8,'Poobedná':8,'Nočná':12,'Školenie':8}

class RowButton(Button):
    def __init__(self, typ='', **kwargs):
        super().__init__(**kwargs)
        self.background_normal=''; self.background_color=COLORS.get(typ, COLORS[''])
        self.color=(1,1,1,1); self.size_hint_y=None; self.height=dp(48); self.halign='left'; self.valign='middle'
        self.padding=(dp(12),dp(6)); self.bind(size=lambda *a: setattr(self,'text_size',(self.width-dp(20),None)))

class ZSSKApp(App):
    def build(self):
        self.data_file=os.path.join(self.user_data_dir,'data.json')
        self._ensure()
        self.cur_year, self.cur_month = 2026, 7  # start na tvojich dátach

        root=BoxLayout(orientation='vertical',padding=dp(8),spacing=dp(6))
        with root.canvas.before:
            Color(0.06,0.06,0.08,1); self.bg=Rectangle(size=root.size,pos=root.pos); root.bind(size=lambda *a: setattr(self.bg,'size',root.size))

        # TOP NAV
        nav=BoxLayout(size_hint_y=None,height=dp(52),spacing=dp(4))
        b_prev=Button(text='<',size_hint_x=None,width=dp(44)); b_prev.bind(on_press=lambda x:self.shift_month(-1))
        b_next=Button(text='>',size_hint_x=None,width=dp(44)); b_next.bind(on_press=lambda x:self.shift_month(1))
        self.lbl_month=Label(text='',font_size='18sp',bold=True)
        b_pick=Button(text='Mesiac',size_hint_x=None,width=dp(78)); b_pick.bind(on_press=self.open_month_picker)
        b_stat=Button(text='Stats',size_hint_x=None,width=dp(68),background_color=(0.2,0.6,0.4,1)); b_stat.bind(on_press=self.open_stats)
        b_exp=Button(text='Export',size_hint_x=None,width=dp(72),background_color=(0.15,0.4,0.75,1)); b_exp.bind(on_press=self.export_csv)
        nav.add_widget(b_prev); nav.add_widget(self.lbl_month); nav.add_widget(b_next); nav.add_widget(b_pick); nav.add_widget(b_stat); nav.add_widget(b_exp)
        root.add_widget(nav)

        self.lbl_info=Label(size_hint_y=None,height=dp(26),color=(0.7,0.85,1,1),font_size='13sp'); root.add_widget(self.lbl_info)

        scroll=ScrollView(); self.grid=GridLayout(cols=1,spacing=dp(3),size_hint_y=None,padding=dp(2)); self.grid.bind(minimum_height=self.grid.setter('height')); scroll.add_widget(self.grid); root.add_widget(scroll)

        b_add=Button(text='+ Pridať zmenu',size_hint_y=None,height=dp(56),background_color=(0,0.45,0.8,1),font_size='18sp'); b_add.bind(on_press=lambda x:self.open_editor()); root.add_widget(b_add)
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
        self.cur_year, self.cur_month=y,m; self.refresh()

    def refresh(self):
        self.grid.clear_widgets(); data=self.load(); mk=self.month_key()
        filtered=[d for d in data if d.get('date','').startswith(mk)]
        self.lbl_month.text=mk
        total_h=sum(HODINY.get(d.get('zmena',''),0) for d in filtered)
        nocne=sum(1 for d in filtered if d.get('zmena')=='Nočná')
        self.lbl_info.text=f"{len(filtered)}/{len(data)} záznamov • {total_h}h • Nočné: {nocne}"
        if not filtered:
            self.grid.add_widget(Label(text='Žiadne záznamy pre tento mesiac\nPridaj prvú zmenu',size_hint_y=None,height=dp(80),color=(0.6,0.6,0.6,1))); return
        # zorad od najnovšieho
        filtered_sorted=sorted(filtered,key=lambda x:x.get('date',''),reverse=True)
        for item in filtered_sorted:
            date=item.get('date','?'); typ=item.get('zmena',''); pozn=item.get('poznamka','')
            txt=f"{date}  •  {typ or 'bez typu'}" + (f"  – {pozn}" if pozn else "")
            btn=RowButton(typ=typ,text=txt)
            idx=data.index(item)
            btn.bind(on_press=lambda inst,i=idx: self.open_editor(i))
            self.grid.add_widget(btn)

    # ----- EDITOR -----
    def open_editor(self,index=None):
        data=self.load(); is_edit=index is not None; it=data[index] if is_edit else {}
        popup=Popup(title='Upraviť' if is_edit else 'Pridať zmenu',size_hint=(0.92,0.58))
        box=BoxLayout(orientation='vertical',spacing=dp(8),padding=dp(12))
        grid=GridLayout(cols=2,spacing=dp(8),size_hint_y=None); grid.bind(minimum_height=grid.setter('height')); grid.height=dp(160)
        ed_date=TextInput(text=it.get('date',datetime.date.today().strftime('%Y-%m-%d')),multiline=False,size_hint_y=None,height=dp(40))
        ed_typ=Spinner(text=it.get('zmena','Ranná') or 'Ranná',values=['Ranná','Poobedná','Nočná','Voľno','Dovolenka','PN','Školenie'],size_hint_y=None,height=dp(40))
        ed_pozn=TextInput(text=it.get('poznamka',''),hint_text='Poznámka',multiline=False,size_hint_y=None,height=dp(40))
        for l,w in [('Dátum',ed_date),('Typ',ed_typ),('Poznámka',ed_pozn)]:
            grid.add_widget(Label(text=l,size_hint_x=0.32,halign='right')); grid.add_widget(w)
        box.add_widget(grid)
        btns=BoxLayout(size_hint_y=None,height=dp(48),spacing=dp(8))
        b1=Button(text='Zrušiť'); b2=Button(text='Uložiť',background_color=(0.2,0.6,0.3,1)); btns.add_widget(b1); btns.add_widget(b2)
        if is_edit:
            b3=Button(text='Vymazať',background_color=(0.8,0.2,0.2,1)); btns.add_widget(b3); b3.bind(on_press=lambda x:(self.delete(index),popup.dismiss()))
        box.add_widget(btns); popup.content=box
        b1.bind(on_press=popup.dismiss); b2.bind(on_press=lambda x:(self.save_item(index,ed_date.text,ed_typ.text,ed_pozn.text),popup.dismiss()))
        popup.open()

    def save_item(self,i,date,typ,pozn):
        d=self.load(); new={'date':date.strip(),'zmena':typ,'poznamka':pozn.strip()}
        if i is None: d.append(new)
        else: d[i]=new
        self.save(d); self.refresh()
    def delete(self,i): d=self.load(); del d[i]; self.save(d); self.refresh()

    # ----- MONTH PICKER -----
    def open_month_picker(self,*a):
        popup=Popup(title='Vyber mesiac',size_hint=(0.9,0.75))
        box=BoxLayout(orientation='vertical',spacing=dp(6),padding=dp(10))
        year_box=BoxLayout(size_hint_y=None,height=dp(44),spacing=dp(8))
        self.lbl_pick_year=Label(text=str(self.cur_year))
        b_y1=Button(text='- rok',size_hint_x=None,width=dp(70)); b_y2=Button(text='+ rok',size_hint_x=None,width=dp(70))
        def chg(d): 
            self.cur_year+=d; self.lbl_pick_year.text=str(self.cur_year)
        b_y1.bind(on_press=lambda x: chg(-1)); b_y2.bind(on_press=lambda x: chg(1))
        year_box.add_widget(b_y1); year_box.add_widget(self.lbl_pick_year); year_box.add_widget(b_y2); box.add_widget(year_box)
        grid=GridLayout(cols=3,spacing=dp(6))
        for m in range(1,13):
            b=Button(text=f"{m:02d} - {calendar.month_abbr[m]}"); b.bind(on_press=lambda inst,mm=m: (setattr(self,'cur_month',mm), popup.dismiss(), self.refresh()))
            grid.add_widget(b)
        box.add_widget(grid)
        btns=BoxLayout(size_hint_y=None,height=dp(44)); b_close=Button(text='Zavrieť'); b_close.bind(on_press=popup.dismiss); btns.add_widget(b_close); box.add_widget(btns)
        popup.content=box; popup.open()

    # ----- STATS -----
    def open_stats(self,*a):
        data=[d for d in self.load() if d.get('date','').startswith(self.month_key())]
        cnt={}; 
        for d in data: cnt[d.get('zmena','')]=cnt.get(d.get('zmena',''),0)+1
        txt=f"Mesiac: {self.month_key()}\n\n"
        for k,v in cnt.items(): txt+=f"{k or 'bez typu'}: {v}\n"
        txt+=f"\nNočné: {cnt.get('Nočná',0)}\nVoľno: {cnt.get('Voľno',0)}\nDovolenka: {cnt.get('Dovolenka',0)}\nCelkom hodín: {sum(HODINY.get(k,0)*v for k,v in cnt.items())}h"
        popup=Popup(title='Prehľad',size_hint=(0.85,0.6)); box=BoxLayout(orientation='vertical',padding=dp(12)); box.add_widget(Label(text=txt,halign='left')); b=Button(text='OK',size_hint_y=None,height=dp(44)); b.bind(on_press=popup.dismiss); box.add_widget(b); popup.content=box; popup.open()

    def export_csv(self,*a):
        out=os.path.join(self.user_data_dir,'zsskzmeny_export.csv')
        try:
            with open(out,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['datum','zmena','poznamka']); [w.writerow([d.get('date'),d.get('zmena'),d.get('poznamka')]) for d in self.load()]
            self.lbl_info.text=f'Export OK: {os.path.basename(out)}'
        except Exception as e: self.lbl_info.text=f'Chyba: {e}'

if __name__=='__main__': ZSSKApp().run()
