from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.fitimage import FitImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock

from database import (
    obtener_elementos_despensa,
    consumir_producto_db,
    agregar_producto_con_barcode,
    renombrar_pasillo_db,
    eliminar_pasillo_db,
    agregar_producto_disponible,
    eliminar_producto_despensa_db,
    obtener_categorias_existentes
)
import sqlite3

class PantryScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.md_bg_color = (0.97, 0.95, 0.99, 1)
        
        self.layout_principal = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(10)
        )
        
        # --- ENCABEZADO TIPO TARJETA ---
        header_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(135),
            padding=0,
            spacing=0,
            elevation=0,
            radius=[16, 16, 16, 16],
            md_bg_color=(0.93, 0.89, 0.97, 1)
        )
        
        header_layout = FloatLayout(size_hint=(1, 1))
        
        fondo_imagen = FitImage(
            source="images/despensa.png",
            radius=[16, 16, 16, 16],
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        header_layout.add_widget(fondo_imagen)
        
        contenido_interno = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(10),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        lbl_titulo = MDLabel(
            text="Mi Despensa",
            font_style="H5",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(34),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        lbl_titulo.bind(size=lambda s, w: setattr(s, 'text_size', w))
        
        btn_container = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(dp(220), dp(36)),
            spacing=dp(8)
        )
        
        btn_nuevo_pasillo = MDRaisedButton(
            text="+ Pasillo",
            font_size="12sp",
            size_hint_x=0.5,
            elevation=0,
            md_bg_color=(0.38, 0.25, 0.50, 0.9),
            text_color=(1, 1, 1, 1)
        )
        btn_nuevo_pasillo.bind(on_release=lambda x: self.abrir_dialogo_crear_pasillo())
        
        btn_nuevo_producto = MDRaisedButton(
            text="+ Producto",
            font_size="12sp",
            size_hint_x=0.5,
            elevation=0,
            md_bg_color=(0.58, 0.45, 0.70, 0.9),
            text_color=(1, 1, 1, 1)
        )
        btn_nuevo_producto.bind(on_release=lambda x: self.abrir_dialogo_agregar_producto_directo())
        
        btn_container.add_widget(btn_nuevo_pasillo)
        btn_container.add_widget(btn_nuevo_producto)
        
        contenido_interno.add_widget(lbl_titulo)
        contenido_interno.add_widget(btn_container)
        
        header_layout.add_widget(contenido_interno)
        header_card.add_widget(header_layout)
        self.layout_principal.add_widget(header_card)
        
        scroll = ScrollView(size_hint=(1, 1))
        self.contenedor_pasillos = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(10),
            padding=[0, dp(4), 0, dp(10)]
        )
        self.contenedor_pasillos.bind(minimum_height=self.contenedor_pasillos.setter('height'))
        
        scroll.add_widget(self.contenedor_pasillos)
        self.layout_principal.add_widget(scroll)
        self.add_widget(self.layout_principal)
        
        self.dialogo_activo = None
        
        Clock.schedule_once(lambda dt: self.actualizar_vista_despensa(), 0.1)

    def on_enter(self):
        self.actualizar_vista_despensa()

    def actualizar_vista_despensa(self):
        self.contenedor_pasillos.clear_widgets()
        elementos = obtener_elementos_despensa()
        
        if not elementos:
            card_vacia = MDCard(
                orientation='vertical',
                padding=dp(24),
                size_hint_y=None,
                size_hint_x=1,
                height=dp(100),
                elevation=0,
                radius=[18, 18, 18, 18],
                md_bg_color=(1, 1, 1, 1)
            )
            card_vacia.add_widget(
                MDLabel(
                    text="Tu despensa está vacía.\n+Añade un producto o Crea un pasillo.",
                    halign="center",
                    font_style="Subtitle1",
                    theme_text_color="Custom",
                    text_color=(0.45, 0.38, 0.55, 1)
                )
            )
            self.contenedor_pasillos.add_widget(card_vacia)
            return

        categorias_dict = {}
        for item in elementos:
            d_id, nombre, barcode, categoria, stock = item
            cat = categoria if categoria else "Otros"
            if cat not in categorias_dict:
                categorias_dict[cat] = []
            categorias_dict[cat].append(item)

        for categoria, productos in categorias_dict.items():
            card_pasillo = MDCard(
                orientation='vertical',
                padding=dp(12),
                spacing=dp(8),
                size_hint_y=None,
                size_hint_x=1,
                elevation=0,
                radius=[18, 18, 18, 18],
                md_bg_color=(1, 1, 1, 1)
            )
            card_pasillo.bind(minimum_height=card_pasillo.setter('height'))
            
            layout_cabecera_pasillo = MDBoxLayout(
                orientation='horizontal',
                size_hint_y=None,
                height=dp(28),
                spacing=dp(2)
            )
            
            lbl_pasillo = MDLabel(
                text=categoria.upper(),
                font_style="Caption",
                bold=True,
                size_hint_x=0.72,
                theme_text_color="Custom",
                text_color=(0.55, 0.35, 0.75, 1)
            )
            
            btn_renombrar = MDIconButton(
                icon="pencil-outline",
                theme_text_color="Custom",
                text_color=(0.55, 0.45, 0.65, 1),
                size_hint_x=0.14,
                pos_hint={"center_y": 0.5}
            )
            btn_renombrar.bind(on_release=lambda x, c=categoria: self.abrir_dialogo_renombrar_pasillo(c))
            
            btn_borrar = MDIconButton(
                icon="delete-outline",
                theme_text_color="Custom",
                text_color=(0.85, 0.35, 0.35, 1),
                size_hint_x=0.14,
                pos_hint={"center_y": 0.5}
            )
            btn_borrar.bind(on_release=lambda x, c=categoria: self.abrir_dialogo_confirmar_borrar(c))
            
            layout_cabecera_pasillo.add_widget(lbl_pasillo)
            layout_cabecera_pasillo.add_widget(btn_renombrar)
            layout_cabecera_pasillo.add_widget(btn_borrar)
            card_pasillo.add_widget(layout_cabecera_pasillo)
            
            for item in productos:
                d_id, nombre, barcode, categoria, stock = item
                
                fila_item = MDBoxLayout(
                    orientation='horizontal',
                    size_hint_y=None,
                    size_hint_x=1,
                    height=dp(38),
                    spacing=dp(4),
                    pos_hint={"center_y": 0.5}
                )
                
                lbl_info = MDLabel(
                    text=nombre,
                    font_style="Body2",
                    size_hint_x=0.48,
                    size_hint_y=None,
                    height=dp(32),
                    pos_hint={"center_y": 0.5},
                    theme_text_color="Custom",
                    text_color=(0.28, 0.18, 0.38, 1)
                )
                
                card_stock = MDCard(
                    size_hint_x=0.24,
                    size_hint_y=None,
                    height=dp(28),
                    pos_hint={"center_y": 0.5},
                    radius=[14, 14, 14, 14],
                    md_bg_color=(0.92, 0.88, 0.96, 1),
                    elevation=0
                )
                lbl_stk = MDLabel(
                    text=f"Stk: {stock}",
                    halign="center",
                    valign="center",
                    bold=True,
                    font_style="Caption",
                    theme_text_color="Custom",
                    text_color=(0.48, 0.32, 0.64, 1)
                )
                card_stock.add_widget(lbl_stk)
                
                btn_consumir = MDIconButton(
                    icon="package-down",
                    theme_text_color="Custom",
                    text_color=(0.48, 0.32, 0.64, 1),
                    size_hint_x=0.14,
                    pos_hint={"center_y": 0.5}
                )
                
                def marcar_agotado(instance, bc=barcode, nom=nombre):
                    if bc:
                        exito, mensaje = consumir_producto_db(bc)
                    else:
                        from database import obtener_ruta_db
                        import sqlite3
                        conexion = sqlite3.connect(obtener_ruta_db())
                        cur = conexion.cursor()
                        cur.execute('SELECT codigo_barras FROM despensa WHERE nombre_producto = ?', (nom,))
                        res = cur.fetchone()
                        conexion.close()
                        if res and res[0]:
                            exito, mensaje = consumir_producto_db(res[0])
                        else:
                            temp_bc = f"TEMP_{nom}"
                            conn = sqlite3.connect(obtener_ruta_db())
                            cur = conn.cursor()
                            cur.execute('UPDATE despensa SET codigo_barras = ? WHERE nombre_producto = ?', (temp_bc, nom))
                            conn.commit()
                            conn.close()
                            exito, mensaje = consumir_producto_db(temp_bc)
                            
                    self.actualizar_vista_despensa()

                btn_consumir.bind(on_release=marcar_agotado)

                btn_eliminar_prod = MDIconButton(
                    icon="trash-can-outline",
                    theme_text_color="Custom",
                    text_color=(0.85, 0.35, 0.35, 1),
                    size_hint_x=0.14,
                    pos_hint={"center_y": 0.5}
                )
                btn_eliminar_prod.bind(on_release=lambda x, p_id=d_id: self.eliminar_producto_despensa(p_id))
                
                fila_item.add_widget(lbl_info)
                fila_item.add_widget(card_stock)
                fila_item.add_widget(btn_consumir)
                fila_item.add_widget(btn_eliminar_prod)
                card_pasillo.add_widget(fila_item)
                
            self.contenedor_pasillos.add_widget(card_pasillo)

    def eliminar_producto_despensa(self, despensa_id):
        eliminar_producto_despensa_db(despensa_id)
        self.actualizar_vista_despensa()

    def abrir_dialogo_crear_pasillo(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(80), padding=dp(6))
        txt_nombre_pasillo = MDTextField(hint_text="Nombre del pasillo", mode="rectangle")
        contenido.add_widget(txt_nombre_pasillo)
        
        def guardar_pasillo(instance):
            nombre = txt_nombre_pasillo.text.strip().capitalize()
            if nombre:
                from database import obtener_ruta_db
                import sqlite3
                conn = sqlite3.connect(obtener_ruta_db())
                cur = conn.cursor()
                try:
                    cur.execute('''
                        INSERT OR IGNORE INTO despensa (nombre_producto, categoria_pasillo, stock)
                        VALUES (?, ?, 0)
                    ''', (f"Ejemplo_{nombre}", nombre))
                    conn.commit()
                finally:
                    conn.close()
                self.dialogo_activo.dismiss()
                self.actualizar_vista_despensa()

        self.dialogo_activo = MDDialog(
            title="Crear Pasillo",
            type="custom",
            content_cls=contenido,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR", 
                    md_bg_color=(0.98, 0.85, 0.85, 1), 
                    text_color=(0.70, 0.20, 0.20, 1), 
                    on_release=lambda x: self.dialogo_activo.dismiss()
                ),
                MDRaisedButton(
                    text="CREAR", 
                    md_bg_color=(0.38, 0.25, 0.50, 1), 
                    text_color=(1, 1, 1, 1), 
                    on_release=guardar_pasillo
                )
            ]
        )
        self.dialogo_activo.open()

    def abrir_dialogo_agregar_producto_directo(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        # Altura aumentada a dp(170) para que el cuadro blanco tenga espacio suficiente y no se encime el título
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=None, height=dp(170), padding=[dp(8), dp(16), dp(8), dp(8)])
        txt_nombre = MDTextField(hint_text="Nombre del producto", mode="rectangle")
        txt_cantidad = MDTextField(text="1", hint_text="Stock inicial", mode="rectangle", input_filter="int")
        
        btn_pasillo = MDRaisedButton(
            text="Seleccionar Pasillo", 
            size_hint_x=1, 
            md_bg_color=(0.92, 0.88, 0.96, 1), 
            text_color=(0.28, 0.18, 0.38, 1)
        )
        pasillo_seleccionado = {"pasillo": "Otros"}
        
        categorias = obtener_categorias_existentes()
        if not categorias:
            categorias = ["Abarrotes", "Lácteos", "Frutas y verduras", "Limpieza", "Panadería", "Otros"]
            
        menu_items = [
            {"text": cat, "viewclass": "OneLineListItem", "on_release": lambda c=cat: seleccionar_cat(c)}
            for cat in categorias
        ]
        
        dropdown_pasillos = MDDropdownMenu(caller=btn_pasillo, items=menu_items, width_mult=4)
        
        def seleccionar_cat(cat):
            pasillo_seleccionado["pasillo"] = cat
            btn_pasillo.text = f"Pasillo: {cat}"
            dropdown_pasillos.dismiss()
            
        btn_pasillo.bind(on_release=lambda x: dropdown_pasillos.open())
        
        contenido.add_widget(txt_nombre)
        contenido.add_widget(txt_cantidad)
        contenido.add_widget(btn_pasillo)
        
        def guardar_producto_directo(instance):
            nom = txt_nombre.text.strip().capitalize()
            cat = pasillo_seleccionado["pasillo"]
            try:
                stock_inicial = int(txt_cantidad.text) if txt_cantidad.text.strip() else 1
            except ValueError:
                stock_inicial = 1
                
            if nom:
                from database import obtener_ruta_db
                import sqlite3
                conn = sqlite3.connect(obtener_ruta_db())
                cur = conn.cursor()
                try:
                    cur.execute('''
                        SELECT id, stock FROM despensa 
                        WHERE nombre_producto = ? AND categoria_pasillo = ?
                    ''', (nom, cat))
                    existe = cur.fetchone()
                    
                    if existe:
                        nuevo_stock = existe[1] + stock_inicial
                        cur.execute('UPDATE despensa SET stock = ? WHERE id = ?', (nuevo_stock, existe[0]))
                    else:
                        cur.execute('''
                            INSERT INTO despensa (nombre_producto, categoria_pasillo, stock)
                            VALUES (?, ?, ?)
                        ''', (nom, cat, stock_inicial))
                    conn.commit()
                finally:
                    conn.close()
                    
                self.dialogo_activo.dismiss()
                self.actualizar_vista_despensa()

        self.dialogo_activo = MDDialog(
            title="Añadir a Despensa",
            type="custom",
            content_cls=contenido,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR", 
                    md_bg_color=(0.98, 0.85, 0.85, 1), 
                    text_color=(0.70, 0.20, 0.20, 1), 
                    on_release=lambda x: self.dialogo_activo.dismiss()
                ),
                MDRaisedButton(
                    text="AÑADIR", 
                    md_bg_color=(0.38, 0.25, 0.50, 1), 
                    text_color=(1, 1, 1, 1), 
                    on_release=guardar_producto_directo
                )
            ]
        )
        self.dialogo_activo.open()

    def abrir_dialogo_renombrar_pasillo(self, viejo_nombre):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(80), padding=dp(6))
        txt_nuevo_nombre = MDTextField(text=viejo_nombre, hint_text="Nuevo nombre", mode="rectangle")
        contenido.add_widget(txt_nuevo_nombre)
        
        def confirmar_renombrar(instance):
            nuevo = txt_nuevo_nombre.text.strip().capitalize()
            if nuevo and nuevo != viejo_nombre:
                renombrar_pasillo_db(viejo_nombre, nuevo)
                self.dialogo_activo.dismiss()
                self.actualizar_vista_despensa()

        self.dialogo_activo = MDDialog(
            title="Renombrar Pasillo",
            type="custom",
            content_cls=contenido,
            buttons=[
                MDRaisedButton(
                    text="CANCELAR", 
                    md_bg_color=(0.98, 0.85, 0.85, 1), 
                    text_color=(0.70, 0.20, 0.20, 1), 
                    on_release=lambda x: self.dialogo_activo.dismiss()
                ),
                MDRaisedButton(
                    text="GUARDAR", 
                    md_bg_color=(0.38, 0.25, 0.50, 1), 
                    text_color=(1, 1, 1, 1), 
                    on_release=confirmar_renombrar
                )
            ]
        )
        self.dialogo_activo.open()

    def abrir_dialogo_confirmar_borrar(self, nombre_pasillo):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        def confirmar_borrado(instance):
            eliminar_pasillo_db(nombre_pasillo)
            self.dialogo_activo.dismiss()
            self.actualizar_vista_despensa()

        self.dialogo_activo = MDDialog(
            title="Eliminar Pasillo",
            text=f"¿Deseas eliminar '{nombre_pasillo}' y sus productos?",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR", 
                    md_bg_color=(0.78, 0.68, 0.88, 1), 
                    text_color=(0.28, 0.18, 0.38, 1), 
                    on_release=lambda x: self.dialogo_activo.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR", 
                    md_bg_color=(0.98, 0.85, 0.85, 1), 
                    text_color=(0.70, 0.20, 0.20, 1), 
                    on_release=confirmar_borrado
                )
            ]
        )
        self.dialogo_activo.open()

    def mostrar_alerta(self, titulo, mensaje):
        self.dialogo_activo = MDDialog(
            title=titulo,
            text=mensaje,
            buttons=[MDRaisedButton(text="ENTENDIDO", on_release=lambda x: self.dialogo_activo.dismiss(), md_bg_color=(0.38, 0.25, 0.50, 1), text_color=(1, 1, 1, 1))]
        )
        self.dialogo_activo.open()