from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
import json, os

class ZSSKApp(App):
    def build(self):
        box = BoxLayout(orientation='vertical', padding=20)
        
        # test že data.json sa načíta
        try:
            if os.path.exists('data.json'):
                with open('data.json', encoding='utf-8') as f:
                    data = json.load(f)
                text = f"ZSSK Zmeny\nNačítané: {len(data)} záznamov"
            else:
                text = "ZSSK Zmeny\n(data.json nenájdený)"
        except Exception as e:
            text = f"Chyba: {e}"
            
        box.add_widget(Label(text=text, font_size='22sp', halign='center'))
        return box

if __name__ == '__main__':
    ZSSKApp().run()
