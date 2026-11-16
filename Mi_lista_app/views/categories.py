from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock

import sqlite3
from database import obtener_ruta_db

class CategoriesAdminScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.layout_principal = MDBoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        
        lbl_titulo = MDLabel(text="⚙️ Administración de Pasillos y Catálogo", font_style="H6", bold=True, size_hint_y=None, height=dp(40))
        self.layout_principal.add_widget(lbl_titulo)
        
        scroll = ScrollView()
        self.contenedor_scroll = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15))
        self.contenedor_scroll.bind(minimum_height=self.contenedor_scroll.setter('height'))
        
        card_nuevo_pasillo = MDCard(orientation='vertical', padding=dp(15), spacing=dp(10), size_hint_y=None, height=dp(150), elevation=2, radius=[16, 16, 16, 16])
        card_nuevo_pasillo.add_widget(MDLabel(text="Crear Nuevo Pasillo / Categoría", font_style="Subtitle1", bold=True))
        
        self.txt_nuevo_pasillo = MDTextField(hint_text="Nombre del Pasillo (Ej. Congelados)", mode="rectangle", size_hint_y=None, height=dp(45))
        card_nuevo_pasillo.add_widget(self.txt_nuevo_pasillo)
        
        btn_crear_pasillo = MDRaisedButton(text="Guardar Pasillo", size_hint_x=1)
        btn_crear_pasillo.bind(on_release=self.crear_pasillo)
        card_nuevo_pasillo.add_widget(btn_crear_pasillo)
        
        self.contenedor_scroll.add_widget(card_nuevo_pasillo)
        
        self.layout_catalogo = MDBoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        self.layout_catalogo.bind(minimum_height=self.layout_catalogo.setter('height'))
        
        self.contenedor_scroll.add_widget(self.layout_catalogo)
        scroll.add_widget(self.contenedor_scroll)
        self.layout_principal.add_widget(scroll)
        self.add_widget(self.layout_principal)
        
        Clock.schedule_once(lambda dt: self.cargar_catalogo(), 0.1)

    def obtener_categorias_unicas(self):
        db_path = obtener_ruta_db()
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT DISTINCT categoria FROM productos_disponibles ORDER BY categoria")
        categorias = [row[0] for row in cursor.fetchall()]
        conexion.close()
        if not categorias:
            categorias = ["Otros", "Frutas y Verduras", "Lácteos", "Limpieza"]
        return categorias

    def crear_pasillo(self, instance):
        nombre_pasillo = self.txt_nuevo_pasillo.text.strip().capitalize()
        if not nombre_pasillo:
            return
        db_path = obtener_ruta_db()
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute('INSERT OR IGNORE INTO productos_disponibles (nombre, categoria) VALUES (?, ?)', (f"Ejemplo - {nombre_pasillo}", nombre_pasillo))
            conexion.commit()
            self.txt_nuevo_pasillo.text = ""
            self.cargar_catalogo()
        finally:
            conexion.close()

    def cargar_catalogo(self):
        self.layout_catalogo.clear_widgets()
        lbl_cat_titulo = MDLabel(text="📦 Catálogo de Productos Registrados", font_style="H6", bold=True, size_hint_y=None, height=dp(35))
        self.layout_catalogo.add_widget(lbl_cat_titulo)
        
        db_path = obtener_ruta_db()
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        cursor.execute("SELECT id, nombre, categoria FROM productos_disponibles ORDER BY categoria, nombre")
        productos = cursor.fetchall()
        conexion.close()
        
        categorias_disponibles = self.obtener_categorias_unicas()
        
        for prod in productos:
            prod_id, nombre_prod, categoria_actual = prod
            card_prod = MDCard(orientation='vertical', padding=dp(12), spacing=dp(8), size_hint_y=None, height=dp(140), elevation=1, radius=[12, 12, 12, 12])
            
            txt_nombre = MDTextField(text=nombre_prod, hint_text="Nombre del producto", mode="rectangle", size_hint_y=None, height=dp(40))
            
            fila_controles = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(45), spacing=dp(10))
            
            btn_categoria = MDRaisedButton(text=f"Pasillo: {categoria_actual}", size_hint_x=0.6)
            
            seleccion_cat = {"categoria": categoria_actual}
            menu_items = [{"text": cat, "viewclass": "OneLineListItem", "on_release": lambda x=cat: seleccionar_opcion_menu(x)} for cat in categorias_disponibles]
            dropdown_menu = MDDropdownMenu(caller=btn_categoria, items=menu_items, width_mult=4)
            
            def seleccionar_opcion_menu(cat_elegida):
                seleccion_cat["categoria"] = cat_elegida
                btn_categoria.text = f"Pasillo: {cat_elegida}"
                dropdown_menu.dismiss()

            btn_categoria.bind(on_release=lambda x: dropdown_menu.open())
            
            btn_guardar = MDIconButton(icon="content-save-edit", theme_text_color="Custom", text_color=(0.1, 0.5, 0.8, 1), size_hint_x=0.2)
            
            def guardar_cambios(instance, p_id=prod_id, t_nom=txt_nombre, sel=seleccion_cat):
                nuevo_n = t_nom.text.strip().capitalize()
                nueva_c = sel["categoria"]
                if nuevo_n:
                    self.actualizar_en_db(p_id, nuevo_n, nueva_c)
                    self.cargar_catalogo()

            btn_guardar.bind(on_release=guardar_cambios)
            fila_controles.add_widget(btn_categoria)
            fila_controles.add_widget(btn_guardar)
            card_prod.add_widget(txt_nombre)
            card_prod.add_widget(fila_controles)
            self.layout_catalogo.add_widget(card_prod)

    def actualizar_en_db(self, producto_id, nuevo_nombre, nueva_categoria):
        db_path = obtener_ruta_db()
        conexion = sqlite3.connect(db_path)
        cursor = conexion.cursor()
        try:
            cursor.execute('UPDATE productos_disponibles SET nombre = ?, categoria = ? WHERE id = ?', (nuevo_nombre, nueva_categoria, producto_id))
            conexion.commit()
        finally:
            conexion.close()