from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
import json, os

class ZSSKApp(App):
    def build(self):
        root = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # hlavička
        self.header = Label(text='ZSSK Zmeny', font_size='24sp', size_hint_y=None, height=50)
        root.add_widget(self.header)

        # scroll zoznam
        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))

        try:
            with open('data.json', encoding='utf-8') as f:
                data = json.load(f)
            self.header.text = f'Načítané: {len(data)} záznamov'

            for i, zaznam in enumerate(data):
                # zobrazíme len prvých pár položiek zo záznamu, aby sa zmestil
                text = f"{i+1}. {zaznam.get('datum','')} – {zaznam.get('zmena','')} – {zaznam.get('poznamka','')}"
                lbl = Label(text=text, size_hint_y=None, height=30, halign='left', valign='middle')
                lbl.text_size = (self.root_window.width - 20, None) if hasattr(self, 'root_window') else (400, None)
                grid.add_widget(lbl)
        except Exception as e:
            self.header.text = f'Chyba: {e}'

        scroll.add_widget(grid)
        root.add_widget(scroll)
        return root

if __name__ == '__main__':
    ZSSKApp().run()
