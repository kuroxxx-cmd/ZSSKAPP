from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import json, os

class ZSSKApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        header = Label(text='ZSSK Zmeny', font_size='24sp', size_hint_y=None, height=50)
        root.add_widget(header)

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=4, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        scroll.add_widget(grid)
        root.add_widget(scroll)

        try:
            if os.path.exists('data.json'):
                with open('data.json', encoding='utf-8') as f:
                    data = json.load(f)
                header.text = f'Načítané: {len(data)} záznamov'

                for i, z in enumerate(data):
                    # berieme len polia ktoré máš v JSON-e
                    datum = z.get('datum', z.get('date', '?'))
                    zmena = z.get('zmena', z.get('smena', '?'))
                    poznamka = z.get('poznamka', '')
                    txt = f"{i+1}. {datum} – {zmena} {poznamka}"
                    lbl = Label(text=txt, size_hint_y=None, height=30, halign='left', valign='middle')
                    # toto zaručí zalomenie textu bez použitia root_window
                    lbl.bind(width=lambda inst, w: setattr(inst, 'text_size', (w-10, None)))
                    grid.add_widget(lbl)
            else:
                header.text = 'data.json nenájdený'
        except Exception as e:
            header.text = f'Chyba: {e}'

        return root

if __name__ == '__main__':
    ZSSKApp().run()
