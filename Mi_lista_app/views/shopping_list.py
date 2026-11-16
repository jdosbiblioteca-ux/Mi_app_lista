from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.fitimage import FitImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.app import App

from database import (
    obtener_elementos_activos, 
    actualizar_elemento_lista, 
    actualizar_producto_catalogo,
    obtener_ruta_db,
    agregar_a_lista_compras,
    finalizar_compra_db,
    agregar_producto_disponible,
    obtener_categorias_existentes,
    eliminar_elemento_lista_db
)
import sqlite3

class ShoppingListScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Fondo lavanda pastel ultra suave
        self.md_bg_color = (0.97, 0.95, 0.99, 1)
        
        self.layout_principal = MDBoxLayout(
            orientation='vertical', 
            padding=[dp(12), dp(10), dp(12), dp(10)], 
            spacing=dp(8)
        )
        
        # --- ENCABEZADO TIPO TARJETA CON IMAGEN DE FONDO ---
        header_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(96),
            padding=0,
            spacing=0,
            elevation=0,
            radius=[16, 16, 16, 16],
            md_bg_color=(0.93, 0.89, 0.97, 1)
        )
        
        # Usamos un FloatLayout para superponer la imagen de fondo y los textos/botones encima
        header_layout = FloatLayout(size_hint=(1, 1))
        
        # Imagen de fondo "images/lista.png" ajustada con esquinas redondeadas
        fondo_imagen = FitImage(
            source="images/lista.png",
            radius=[16, 16, 16, 16],
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        header_layout.add_widget(fondo_imagen)
        
        # Contenido interior (Título y botones) encima de la imagen
        contenido_interno = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=dp(8),
            spacing=dp(6),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Título en BLANCO para resaltar sobre la imagen
        lbl_titulo = MDLabel(
            text="Mi Lista de Compras",
            font_style="H5",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(30),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)  # Color blanco solicitado
        )
        
        header_actions = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(dp(310), dp(38)),
            spacing=dp(10),
            pos_hint={'center_x': 0.28, 'center_y': 0.5}  # Alineado a la izquierda sin forzar al centro
        )
        
        # Botón Finalizar Compra: Morado medio con TEXTO BLANCO
        btn_finalizar = MDRaisedButton(
            text="Finalizar Compra",
            font_size="12sp",
            size_hint_x=0.6,
            elevation=0,
            md_bg_color=(0.58, 0.45, 0.70, 0.9),  # Ligeramente semitransparente para ver la imagen de fondo
            text_color=(1, 1, 1, 1)  # Letras blancas
        )
        btn_finalizar.bind(on_release=self.ejecutar_finalizar_directo)
        
        # Botón Añadir: Morado Oscuro Profundo con texto blanco
        btn_agregar_superior = MDRaisedButton(
            text="+ Añadir",
            font_size="12sp",
            size_hint_x=0.4,
            elevation=0,
            md_bg_color=(0.38, 0.25, 0.50, 0.9),  # Ligeramente semitransparente
            text_color=(1, 1, 1, 1)
        )
        btn_agregar_superior.bind(on_release=lambda x: self.abrir_formulario_manual())
        
        header_actions.add_widget(btn_finalizar)
        header_actions.add_widget(btn_agregar_superior)
        
        contenido_interno.add_widget(lbl_titulo)
        contenido_interno.add_widget(header_actions)
        
        header_layout.add_widget(contenido_interno)
        header_card.add_widget(header_layout)
        self.layout_principal.add_widget(header_card)
        
        self.scroll_view = ScrollView(size_hint=(1, 1))
        self.contenedor_pasillos = MDBoxLayout(
            orientation='vertical', 
            size_hint_y=None, 
            size_hint_x=1,
            spacing=dp(10),
            padding=[0, dp(2), 0, dp(10)]
        )
        self.contenedor_pasillos.bind(minimum_height=self.contenedor_pasillos.setter('height'))
        self.scroll_view.add_widget(self.contenedor_pasillos)
        
        self.layout_principal.add_widget(self.scroll_view)
        
        self.panel_total = MDCard(
            orientation='horizontal',
            size_hint_y=None,
            size_hint_x=1,
            height=dp(56),
            padding=[dp(16), dp(8), dp(16), dp(8)],
            elevation=0,
            radius=[16, 16, 16, 16],
            md_bg_color=(1, 1, 1, 1)
        )
        
        self.lbl_total_titulo = MDLabel(
            text="Total Estimado", 
            font_style="Subtitle1", 
            bold=True, 
            halign="left", 
            theme_text_color="Custom", 
            text_color=(0.45, 0.38, 0.55, 1)
        )
        self.lbl_total_valor = MDLabel(
            text="$0.00", 
            font_style="H5", 
            bold=True, 
            halign="right", 
            theme_text_color="Custom", 
            text_color=(0.06, 0.72, 0.51, 1)  # Verde menta para el total
        )
        
        self.panel_total.add_widget(self.lbl_total_titulo)
        self.panel_total.add_widget(self.lbl_total_valor)
        self.layout_principal.add_widget(self.panel_total)
        
        self.add_widget(self.layout_principal)
        
        self.precios_actuales = {}
        self.comprados_locales = set()
        self.dialogo_activo = None
        
        Clock.schedule_once(lambda dt: self.actualizar_vista(), 0.1)

    def on_enter(self):
        self.actualizar_vista()

    def actualizar_vista(self):
        self.contenedor_pasillos.clear_widgets()
        elementos = obtener_elementos_activos()
        
        if not elementos:
            card_vacia = MDCard(
                orientation='vertical', 
                padding=dp(24), 
                size_hint_y=None, 
                size_hint_x=1,
                height=dp(110), 
                elevation=0, 
                radius=[18, 18, 18, 18],
                md_bg_color=(1, 1, 1, 1)
            )
            card_vacia.add_widget(
                MDLabel(
                    text="¡Tu lista está vacía!\nAñade un producto para empezar.", 
                    halign="center", 
                    font_style="Subtitle1", 
                    theme_text_color="Custom", 
                    text_color=(0.45, 0.38, 0.55, 1)
                )
            )
            self.contenedor_pasillos.add_widget(card_vacia)
            self.precios_actuales.clear()
            self.comprados_locales.clear()
            self.recalcular_total()
            return

        categorias_dict = {}
        for item in elementos:
            cat = item[2] if item[2] else "Otros"
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
            
            lbl_pasillo = MDLabel(
                text=categoria.upper(), 
                font_style="Caption", 
                bold=True, 
                size_hint_y=None, 
                height=dp(24),
                theme_text_color="Custom",
                text_color=(0.55, 0.35, 0.75, 1)
            )
            card_pasillo.add_widget(lbl_pasillo)
            
            for item in productos:
                item_id, nombre, cat_name, precio_est, cantidad, estado, producto_id = item
                
                fila_item = MDBoxLayout(
                    orientation='horizontal', 
                    size_hint_y=None, 
                    size_hint_x=1,
                    height=dp(38), 
                    spacing=dp(6)
                )
                
                es_comprado = (item_id in self.comprados_locales)
                color_texto = (0.6, 0.55, 0.65, 1) if es_comprado else (0.28, 0.18, 0.38, 1)
                
                lbl_info = MDLabel(
                    text=nombre, 
                    font_style="Body1", 
                    size_hint_x=0.40,
                    size_hint_y=None,
                    height=dp(32),
                    pos_hint={"center_y": 0.5},
                    theme_text_color="Custom",
                    text_color=color_texto
                )
                lbl_info.bind(on_touch_down=lambda inst, touch, i_id=item_id, p_id=producto_id, nom=nombre, cant=cantidad, prec=precio_est: 
                              self.verificar_pulsacion_larga(inst, touch, i_id, p_id, nom, cant, prec))
                
                card_cantidad = MDCard(
                    size_hint_x=0.15,
                    size_hint_y=None,
                    height=dp(28),
                    pos_hint={"center_y": 0.5},
                    radius=[14, 14, 14, 14],
                    md_bg_color=(0.92, 0.88, 0.96, 1) if not es_comprado else (0.90, 0.90, 0.90, 1),
                    elevation=0
                )
                lbl_cant = MDLabel(
                    text=f"x{cantidad}",
                    halign="center",
                    valign="center",
                    bold=True,
                    font_style="Caption",
                    theme_text_color="Custom",
                    text_color=(0.48, 0.32, 0.64, 1) if not es_comprado else (0.5, 0.5, 0.5, 1)
                )
                card_cantidad.add_widget(lbl_cant)
                
                if item_id not in self.precios_actuales:
                    self.precios_actuales[item_id] = float(precio_est) if precio_est else 0.0
                
                txt_precio = MDTextField(
                    text=str(self.precios_actuales[item_id]) if self.precios_actuales[item_id] > 0 else "",
                    hint_text="Precio",
                    mode="line",
                    size_hint_x=0.27,
                    size_hint_y=None,
                    height=dp(34),
                    pos_hint={"center_y": 0.5},
                    font_size="13sp"
                )
                
                def al_cambiar_precio(instance, value, i_id=item_id):
                    try:
                        self.precios_actuales[i_id] = float(value) if value.strip() != "" else 0.0
                    except ValueError:
                        self.precios_actuales[i_id] = 0.0
                    self.recalcular_total()

                txt_precio.bind(text=al_cambiar_precio)
                
                icono_estado = "check-circle" if es_comprado else "check-circle-outline"
                color_icono = (0.06, 0.72, 0.51, 1) if es_comprado else (0.65, 0.58, 0.75, 1)
                
                btn_comprado = MDIconButton(
                    icon=icono_estado,
                    theme_text_color="Custom",
                    text_color=color_icono,
                    size_hint_x=0.18,
                    pos_hint={"center_y": 0.5}
                )
                
                def alternar_comprado(instance, i_id=item_id):
                    if i_id in self.comprados_locales:
                        self.comprados_locales.remove(i_id)
                    else:
                        self.comprados_locales.add(i_id)
                    self.actualizar_vista()

                btn_comprado.bind(on_release=alternar_comprado)
                
                fila_item.add_widget(lbl_info)
                fila_item.add_widget(card_cantidad)
                fila_item.add_widget(txt_precio)
                fila_item.add_widget(btn_comprado)
                card_pasillo.add_widget(fila_item)
                
            self.contenedor_pasillos.add_widget(card_pasillo)
            
        self.recalcular_total()

    def abrir_formulario_manual(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(130), padding=dp(8))
        txt_nombre = MDTextField(hint_text="Nombre del producto", mode="rectangle")
        
        btn_pasillo = MDRaisedButton(text="Seleccionar Pasillo", size_hint_x=1, md_bg_color=(0.92, 0.88, 0.96, 1), text_color=(0.28, 0.18, 0.38, 1))
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
        contenido.add_widget(btn_pasillo)
        
        def guardar_nuevo_producto(instance):
            nom = txt_nombre.text.strip().capitalize()
            cat = pasillo_seleccionado["pasillo"]
            if nom:
                p_id = agregar_producto_disponible(nom, cat)
                if p_id:
                    agregar_a_lista_compras(producto_id=p_id, precio_estimado=0.0, cantidad=1)
            self.dialogo_activo.dismiss()
            self.actualizar_vista()

        self.dialogo_activo = MDDialog(
            title="Añadir Producto",
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
                    on_release=guardar_nuevo_producto
                )
            ]
        )
        self.dialogo_activo.open()

    def ejecutar_finalizar_directo(self, instance):
        supermercado = "Supermercado General"
        finalizar_compra_db(supermercado, self.precios_actuales)
        self.precios_actuales.clear()
        self.comprados_locales.clear()
        self.actualizar_vista()
        
        try:
            from views.pantry import PantryScreen
            def buscar_y_actualizar(widget):
                if isinstance(widget, PantryScreen):
                    widget.actualizar_vista_despensa()
                    return True
                for hijo in widget.children:
                    if buscar_y_actualizar(hijo):
                        return True
                return False
            app = App.get_running_app()
            if app and app.root:
                buscar_y_actualizar(app.root)
        except Exception as e:
            print("Error actualizando despensa:", e)

    def verificar_pulsacion_larga(self, widget, touch, item_id, producto_id, nombre, cantidad, precio):
        if widget.collide_point(*touch.pos):
            self.abrir_dialogo_edicion(item_id, producto_id, nombre, cantidad, precio)

    def abrir_dialogo_edicion(self, item_id, producto_id, nombre_actual, cantidad_actual, precio_actual):
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(130), padding=dp(8))
        txt_nuevo_nombre = MDTextField(text=nombre_actual, hint_text="Nombre del producto", mode="rectangle")
        txt_nueva_cantidad = MDTextField(text=str(cantidad_actual), hint_text="Cantidad", mode="rectangle", input_filter="int")
        contenido.add_widget(txt_nuevo_nombre)
        contenido.add_widget(txt_nueva_cantidad)
        
        def guardar_cambios_dialogo(instance):
            try:
                nueva_cant = int(txt_nueva_cantidad.text) if txt_nueva_cantidad.text.strip() else 1
            except ValueError:
                nueva_cant = 1
            nuevo_nom = txt_nuevo_nombre.text.strip().capitalize()
            actualizar_elemento_lista(item_id, cantidad=nueva_cant, precio_estimado=precio_actual)
            if nuevo_nom:
                actualizar_producto_catalogo(producto_id, nuevo_nom, nueva_categoria="General")
            self.dialogo_activo.dismiss()
            self.actualizar_vista()

        def eliminar_elemento(instance):
            eliminar_elemento_lista_db(item_id)
            if item_id in self.precios_actuales:
                del self.precios_actuales[item_id]
            if item_id in self.comprados_locales:
                self.comprados_locales.remove(item_id)
            self.dialogo_activo.dismiss()
            self.actualizar_vista()

        self.dialogo_activo = MDDialog(
            title="Opciones de Producto",
            type="custom",
            content_cls=contenido,
            buttons=[
                MDRaisedButton(
                    text="ELIMINAR", 
                    md_bg_color=(0.98, 0.85, 0.85, 1), 
                    text_color=(0.70, 0.20, 0.20, 1),
                    on_release=eliminar_elemento
                ),
                MDRaisedButton(
                    text="GUARDAR", 
                    md_bg_color=(0.38, 0.25, 0.50, 1), 
                    text_color=(1, 1, 1, 1),
                    on_release=guardar_cambios_dialogo
                )
            ],
        )
        self.dialogo_activo.open()

    def recalcular_total(self):
        total = sum(self.precios_actuales.values())
        self.lbl_total_valor.text = f"${total:.2f}"