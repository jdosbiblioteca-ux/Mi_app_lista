from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.clock import Clock

class HistoryChartsScreen(MDScreen):
    """
    Vista de Gráficas y Estadísticas: Diseño limpio unificado.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.md_bg_color = (0.97, 0.98, 0.99, 1)
        
        self.layout_principal = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(10)
        )
        
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(40)
        )
        
        lbl_titulo = MDLabel(
            text="Estadísticas",
            font_style="H6",
            bold=True,
            theme_text_color="Custom",
            text_color=(0.12, 0.16, 0.22, 1)
        )
        header_layout.add_widget(lbl_titulo)
        self.layout_principal.add_widget(header_layout)
        
        self.contenedor_grafica = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(10),
            padding=[0, dp(4), 0, dp(10)]
        )
        
        self.layout_principal.add_widget(self.contenedor_grafica)
        self.add_widget(self.layout_principal)
        
        Clock.schedule_once(lambda dt: self.actualizar_vista(), 0.1)

    def on_enter(self):
        self.actualizar_vista()

    def actualizar_vista(self):
        self.contenedor_grafica.clear_widgets()
        
        card_stats = MDCard(
            orientation='vertical',
            padding=dp(24),
            size_hint_y=None,
            size_hint_x=1,
            height=dp(120),
            elevation=0,
            radius=[18, 18, 18, 18],
            md_bg_color=(1, 1, 1, 1)
        )
        card_stats.add_widget(
            MDLabel(
                text="No hay suficientes datos de compras en este mes para generar estadísticas.",
                halign="center",
                font_style="Subtitle1",
                theme_text_color="Custom",
                text_color=(0.4, 0.45, 0.55, 1)
            )
        )
        self.contenedor_grafica.add_widget(card_stats)