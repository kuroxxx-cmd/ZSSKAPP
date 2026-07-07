import json, os, datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner

class ZSSKApp(App):
    def build(self):
        self.title = "ZSSK Zmeny"
        self.data_file = os.path.join(self.user_data_dir, 'data.json')
        self._ensure_data()

        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        self.header = Label(text='Načítané: 0', font_size='22sp', size_hint_y=None, height=40)
        root.add_widget(self.header)

        scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=3, size_hint_y=None)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        scroll.add_widget(self.grid)
        root.add_widget(scroll)

        btn_add = Button(text='+ Pridať zmenu', size_hint_y=None, height=50, background_color=(0.2,0.6,0.9,1))
        btn_add.bind(on_press=self.open_add_popup)
        root.add_widget(btn_add)

        self.refresh_list()
        return root

    def _ensure_data(self):
        if not os.path.exists(self.data_file):
            try:
                if os.path.exists('data.json'):
                    with open('data.json', encoding='utf-8') as f:
                        data = json.load(f)
                else:
                    data = []
                os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except:
                with open(self.data_file, 'w', encoding='utf-8') as f:
                    json.dump([], f)

    def load_data(self):
        try:
            with open(self.data_file, encoding='utf-8') as f:
                return json.load(f)
        except:
            return []

    def save_data(self, data):
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def refresh_list(self):
        self.grid.clear_widgets()
        data = self.load_data()
        self.header.text = f'Načítané: {len(data)} záznamov'
        for z in reversed(data[-200:]):
            date = z.get('date') or z.get('datum') or '?'
            zmena = z.get('zmena') or '?'
            pozn = z.get('poznamka') or ''
            txt = f"{date} – {zmena} {pozn}".strip()
            lbl = Label(text=txt, size_hint_y=None, height=28, halign='left', valign='middle')
            lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w-10, None)))
            self.grid.add_widget(lbl)

    def open_add_popup(self, *args):
        content = BoxLayout(orientation='vertical', spacing=8, padding=10)
        today = datetime.date.today().strftime('%Y-%m-%d')
        self.in_date = TextInput(text=today, hint_text='Dátum RRRR-MM-DD', size_hint_y=None, height=40, multiline=False)
        self.in_typ = Spinner(text='Ranná', values=['Ranná','Poobedná','Nočná','Voľno','Dovolenka','PN'], size_hint_y=None, height=40)
        self.in_pozn = TextInput(hint_text='Poznámka', size_hint_y=None, height=40, multiline=False)

        content.add_widget(Label(text='Dátum:', size_hint_y=None, height=20))
        content.add_widget(self.in_date)
        content.add_widget(Label(text='Typ:', size_hint_y=None, height=20))
        content.add_widget(self.in_typ)
        content.add_widget(Label(text='Poznámka:', size_hint_y=None, height=20))
        content.add_widget(self.in_pozn)

        btns = BoxLayout(size_hint_y=None, height=45, spacing=10)
        btn_cancel = Button(text='Zrušiť')
        btn_save = Button(text='Uložiť')
        btns.add_widget(btn_cancel)
        btns.add_widget(btn_save)
        content.add_widget(btns)

        self.popup = Popup(title='Pridať zmenu', content=content, size_hint=(0.9,0.6))
        btn_cancel.bind(on_press=self.popup.dismiss)
        btn_save.bind(on_press=self.save_new)
        self.popup.open()

    def save_new(self, *args):
        data = self.load_data()
        new = {
            'date': self.in_date.text.strip(),
            'zmena': self.in_typ.text,
            'poznamka': self.in_pozn.text.strip()
        }
        data.append(new)
        self.save_data(data)
        self.popup.dismiss()
        self.refresh_list()

if __name__ == '__main__':
    ZSSKApp().run()
