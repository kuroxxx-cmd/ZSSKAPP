import json, os, datetime, csv
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

COLORS = {
    'Ranná': (0.2,0.6,0.9,1),
    'Poobedná': (0.9,0.6,0.2,1),
    'Nočná': (0.3,0.3,0.8,1),
    'Voľno': (0.3,0.7,0.3,1),
    'Dovolenka': (0.8,0.5,0.9,1),
    'PN': (0.9,0.3,0.3,1),
    'Školenie': (0.6,0.6,0.6,1),
    '?': (0.15,0.15,0.18,1)
}

class RowButton(Button):
    def __init__(self, typ='?', **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = COLORS.get(typ, COLORS['?'])
        self.color = (1,1,1,1)
        self.size_hint_y = None
        self.height = dp(48)
        self.halign = 'left'
        self.valign = 'middle'
        self.padding = (dp(12), dp(6))
        self.bind(size=self._upd)
    def _upd(self, *a):
        self.text_size = (self.width - dp(20), None)

class ZSSKApp(App):
    def build(self):
        self.data_file = os.path.join(self.user_data_dir, 'data.json')
        self._ensure_data()

        root = BoxLayout(orientation='vertical', padding=dp(8), spacing=dp(6))
        with root.canvas.before:
            Color(0.07,0.07,0.09,1)
            self.bg = Rectangle(size=root.size, pos=root.pos)
            root.bind(size=lambda *a: setattr(self.bg,'size',root.size))

        # TOP
        top = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(6))
        self.lbl_count = Label(text='', font_size='18sp', halign='left')
        self.lbl_count.bind(size=lambda i,v: setattr(i,'text_size',v))
        btn_filter = Button(text='Mesiac', size_hint_x=None, width=dp(80))
        btn_export = Button(text='Export', size_hint_x=None, width=dp(80), background_color=(0.2,0.5,0.8,1))
        btn_filter.bind(on_press=self.choose_month)
        btn_export.bind(on_press=self.export_csv)
        top.add_widget(self.lbl_count); top.add_widget(btn_filter); top.add_widget(btn_export)
        root.add_widget(top)

        self.lbl_stats = Label(text='', size_hint_y=None, height=dp(24), color=(0.8,0.9,1,1), font_size='13sp')
        root.add_widget(self.lbl_stats)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=dp(4), size_hint_y=None, padding=dp(2))
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        btn_add = Button(text='+ Pridať zmenu', size_hint_y=None, height=dp(54), background_color=(0,0.45,0.8,1), font_size='18sp')
        btn_add.bind(on_press=lambda x: self.open_editor())
        root.add_widget(btn_add)

        self.current_month = datetime.date.today().strftime('%Y-%m')
        self.refresh()
        return root

    def _ensure_data(self):
        if not os.path.exists(self.data_file):
            data=[]
            if os.path.exists('data.json'):
                try:
                    with open('data.json', encoding='utf-8') as f: data=json.load(f)
                except: pass
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

    def load(self):
        try:
            with open(self.data_file,encoding='utf-8') as f: data=json.load(f)
        except: data=[]
        # oprava starých záznamov bez 'zmena'
        for d in data:
            if 'zmena' not in d: d['zmena']=''
            if 'date' not in d and 'datum' in d: d['date']=d.pop('datum')
        return data

    def save(self,data):
        with open(self.data_file,'w',encoding='utf-8') as f: json.dump(data,f,ensure_ascii=False,indent=2)

    def refresh(self):
        self.grid.clear_widgets()
        data = self.load()
        filtered = [d for d in data if d.get('date','').startswith(self.current_month)]
        self.lbl_count.text = f'{self.current_month} • {len(filtered)}/{len(data)}'
        # štatistika hodín
        hours_map={'Ranná':8,'Poobedná':8,'Nočná':12,'Školenie':8}
        total_h = sum(hours_map.get(d.get('zmena',''),0) for d in filtered)
        counts = {}
        for d in filtered: counts[d.get('zmena','')] = counts.get(d.get('zmena',''),0)+1
        stats = ' | '.join([f"{k}:{v}" for k,v in counts.items() if k])
        self.lbl_stats.text = f"Hodiny: {total_h}h  •  {stats}"

        for idx, z in enumerate(reversed(filtered)):
            date = z.get('date','?'); typ = z.get('zmena',''); pozn = z.get('poznamka','')
            txt = f"{date}  •  {typ}" + (f"  – {pozn}" if pozn else "")
            btn = RowButton(typ=typ, text=txt)
            real_idx = len(data)-1 - [i for i,d in enumerate(data) if d.get('date','').startswith(self.current_month)][::-1][idx]
            # jednoduchšie: nájdi index v pôvodnom
            orig_idx = next(i for i,d in enumerate(data) if d==z)
            btn.bind(on_press=lambda inst,i=orig_idx: self.open_editor(i))
            self.grid.add_widget(btn)

    def open_editor(self, index=None):
        data=self.load(); is_edit=index is not None; item=data[index] if is_edit else {}
        popup = Popup(title='Upraviť' if is_edit else 'Pridať zmenu', size_hint=(0.92,0.6))
        box = BoxLayout(orientation='vertical', spacing=dp(8), padding=dp(12))
        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None); grid.bind(minimum_height=grid.setter('height')); grid.height=dp(180)
        ed_date = TextInput(text=item.get('date',datetime.date.today().strftime('%Y-%m-%d')), multiline=False, size_hint_y=None, height=dp(40))
        ed_typ = Spinner(text=item.get('zmena','Ranná'), values=list(COLORS.keys())[:-1], size_hint_y=None, height=dp(40))
        ed_pozn = TextInput(text=item.get('poznamka',''), hint_text='Poznámka', multiline=False, size_hint_y=None, height=dp(40))
        for lbl,w in [('Dátum',ed_date),('Typ',ed_typ),('Poznámka',ed_pozn)]:
            grid.add_widget(Label(text=lbl, size_hint_x=0.3, halign='right')); grid.add_widget(w)
        box.add_widget(grid)
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        b1=Button(text='Zrušiť'); b2=Button(text='Uložiť', background_color=(0.2,0.6,0.3,1)); btns.add_widget(b1); btns.add_widget(b2)
        if is_edit:
            b3=Button(text='Vymazať', background_color=(0.8,0.2,0.2,1)); btns.add_widget(b3); b3.bind(on_press=lambda x: (self.delete(index), popup.dismiss()))
        box.add_widget(btns); popup.content=box
        b1.bind(on_press=popup.dismiss)
        b2.bind(on_press=lambda x: (self.save_item(index, ed_date.text, ed_typ.text, ed_pozn.text), popup.dismiss()))
        popup.open()

    def save_item(self,index,date,typ,pozn):
        data=self.load(); new={'date':date.strip(),'zmena':typ,'poznamka':pozn.strip()}
        if index is None: data.append(new)
        else: data[index]=new
        self.save(data); self.refresh()

    def delete(self,index):
        data=self.load(); del data[index]; self.save(data); self.refresh()

    def choose_month(self,*a):
        # jednoduchý výber +/- mesiac
        y,m = map(int,self.current_month.split('-'))
        m+=1
        if m>12: m=1; y+=1
        self.current_month=f"{y:04d}-{m:02d}"
        self.refresh()

    def export_csv(self,*a):
        data=self.load()
        # OPRAVA: ukladáme do app priečinka, nie /sdcard
        out = os.path.join(self.user_data_dir, 'zsskzmeny_export.csv')
        try:
            with open(out,'w',newline='',encoding='utf-8') as f:
                w=csv.writer(f); w.writerow(['datum','zmena','poznamka'])
                for d in data: w.writerow([d.get('date'),d.get('zmena'),d.get('poznamka')])
            self.lbl_stats.text = f'Export OK: {out}'
        except Exception as e:
            self.lbl_stats.text = f'Chyba: {e}'

if __name__ == '__main__':
    ZSSKApp().run()
