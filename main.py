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

class CardButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0.15,0.15,0.18,1)
        self.color = (0.95,0.95,0.95,1)
        self.size_hint_y = None
        self.height = 44
        self.halign = 'left'
        self.valign = 'middle'
        self.bind(size=self._update_text)
    def _update_text(self, *a):
        self.text_size = (self.width-20, None)

class ZSSKApp(App):
    def build(self):
        self.title = "ZSSK Zmeny PRO"
        self.data_file = os.path.join(self.user_data_dir, 'data.json')
        self._ensure_data()

        root = BoxLayout(orientation='vertical', spacing=6, padding=6)
        with root.canvas.before:
            Color(0.05,0.05,0.07,1)
            self.bg = Rectangle(size=root.size, pos=root.pos)
            root.bind(size=lambda *a: setattr(self.bg,'size',root.size))

        # header
        header = BoxLayout(size_hint_y=None, height=50, spacing=6)
        self.lbl_count = Label(text='Načítané: 0', font_size='20sp', halign='left')
        self.lbl_count.bind(size=lambda i,v: setattr(i,'text_size',(v[0],None)))
        btn_export = Button(text='Export CSV', size_hint_x=None, width=110, background_color=(0.2,0.5,0.8,1))
        btn_export.bind(on_press=self.export_csv)
        header.add_widget(self.lbl_count)
        header.add_widget(btn_export)
        root.add_widget(header)

        # stats
        self.stats = Label(text='', size_hint_y=None, height=28, color=(0.7,0.8,1,1))
        root.add_widget(self.stats)

        # list
        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=4, size_hint_y=None, padding=2)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        # add button
        btn_add = Button(text='+ Pridať zmenu', size_hint_y=None, height=52, background_color=(0,0.45,0.8,1), font_size='18sp')
        btn_add.bind(on_press=lambda x: self.open_editor())
        root.add_widget(btn_add)

        self.refresh()
        return root

    def _ensure_data(self):
        if not os.path.exists(self.data_file):
            data=[]
            if os.path.exists('data.json'):
                try:
                    with open('data.json', encoding='utf-8') as f:
                        data=json.load(f)
                except: pass
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file,'w',encoding='utf-8') as f:
                json.dump(data,f,ensure_ascii=False,indent=2)

    def load(self):
        try:
            with open(self.data_file,encoding='utf-8') as f:
                return json.load(f)
        except: return []

    def save(self,data):
        with open(self.data_file,'w',encoding='utf-8') as f:
            json.dump(data,f,ensure_ascii=False,indent=2)

    def refresh(self):
        self.grid.clear_widgets()
        data = self.load()
        self.lbl_count.text = f'Načítané: {len(data)} záznamov'

        # štatistika aktuálny mesiac
        now = datetime.date.today()
        month_data = [d for d in data if (d.get('date') or d.get('datum','')).startswith(now.strftime('%Y-%m'))]
        counts = {}
        for d in month_data:
            t = d.get('zmena','?')
            counts[t]=counts.get(t,0)+1
        self.stats.text = ' | '.join([f"{k}:{v}" for k,v in counts.items()]) or 'Tento mesiac žiadne záznamy'

        for idx, z in enumerate(reversed(data)):
            date = z.get('date') or z.get('datum') or '?'
            typ = z.get('zmena') or '?'
            pozn = z.get('poznamka') or ''
            txt = f"{date}  •  {typ}" + (f"  – {pozn}" if pozn else "")
            btn = CardButton(text=txt)
            btn.bind(on_press=lambda inst, i=len(data)-1-idx: self.open_editor(i))
            self.grid.add_widget(btn)

    def open_editor(self, index=None):
        data = self.load()
        is_edit = index is not None
        item = data[index] if is_edit else {}

        content = BoxLayout(orientation='vertical', spacing=10, padding=12)
        self.ed_date = TextInput(text=item.get('date') or item.get('datum') or datetime.date.today().strftime('%Y-%m-%d'),
                                 hint_text='RRRR-MM-DD', multiline=False, size_hint_y=None, height=44)
        self.ed_typ = Spinner(text=item.get('zmena','Ranná'),
                              values=['Ranná','Poobedná','Nočná','Voľno','Dovolenka','PN','Školenie'],
                              size_hint_y=None, height=44)
        self.ed_pozn = TextInput(text=item.get('poznamka',''), hint_text='Poznámka', multiline=False, size_hint_y=None, height=44)

        for w,l in [(self.ed_date,'Dátum'),(self.ed_typ,'Typ'),(self.ed_pozn,'Poznámka')]:
            content.add_widget(Label(text=l, size_hint_y=None, height=20, halign='left'))
            content.add_widget(w)

        btns = BoxLayout(size_hint_y=None, height=48, spacing=8)
        btn_cancel = Button(text='Zrušiť')
        btn_save = Button(text='Uložiť', background_color=(0.2,0.6,0.3,1))
        btns.add_widget(btn_cancel); btns.add_widget(btn_save)
        if is_edit:
            btn_del = Button(text='Vymazať', background_color=(0.8,0.2,0.2,1))
            btns.add_widget(btn_del)

        content.add_widget(btns)
        self.popup = Popup(title='Upraviť' if is_edit else 'Pridať zmenu', content=content, size_hint=(0.92,0.7))
        btn_cancel.bind(on_press=self.popup.dismiss)
        btn_save.bind(on_press=lambda x: self.save_item(index))
        if is_edit:
            btn_del.bind(on_press=lambda x: self.delete_item(index))
        self.popup.open()

    def save_item(self, index):
        data = self.load()
        new = {'date': self.ed_date.text.strip(), 'zmena': self.ed_typ.text, 'poznamka': self.ed_pozn.text.strip()}
        if index is None:
            data.append(new)
        else:
            data[index]=new
        self.save(data)
        self.popup.dismiss()
        self.refresh()

    def delete_item(self, index):
        data = self.load()
        del data[index]
        self.save(data)
        self.popup.dismiss()
        self.refresh()

    def export_csv(self, *a):
        data = self.load()
        out = os.path.join(os.getenv('EXTERNAL_STORAGE','/sdcard/Download'), 'zsskzmeny_export.csv')
        try:
            os.makedirs(os.path.dirname(out), exist_ok=True)
            with open(out,'w',newline='',encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['datum','zmena','poznamka'])
                for d in data:
                    w.writerow([d.get('date') or d.get('datum'), d.get('zmena'), d.get('poznamka')])
            self.stats.text = f'Exportované do {out}'
        except Exception as e:
            self.stats.text = f'Chyba exportu: {e}'

if __name__ == '__main__':
    ZSSKApp().run()
