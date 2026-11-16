from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.pickers import MDDatePicker
from kivymd.uix.fitimage import FitImage
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.clock import Clock
from datetime import datetime

from database import (
    obtener_recetas,
    guardar_receta,
    actualizar_receta_db,
    eliminar_receta_db,
    programar_menu_por_fecha,
    obtener_menu_mensual,
    convertir_receta_a_lista,
    eliminar_menu_programado_db
)

class MenuPlannerScreen(MDScreen):
    """
    Planificador mensual con diseño en armonía de tonos morados.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.md_bg_color = (0.97, 0.95, 0.99, 1)
        
        self.layout_principal = MDBoxLayout(
            orientation='vertical',
            padding=[dp(12), dp(10), dp(12), dp(10)],
            spacing=dp(10)
        )
        
        # --- ENCABEZADO TIPO TARJETA CON IMAGEN DE FONDO ---
        header_card = MDCard(
            orientation='vertical',
            size_hint_y=None,
            height=dp(135),  # Altura amplia para albergar imagen, título centrado y botones a la izquierda
            padding=0,
            spacing=0,
            elevation=0,
            radius=[16, 16, 16, 16],
            md_bg_color=(0.93, 0.89, 0.97, 1)
        )
        
        header_layout = FloatLayout(size_hint=(1, 1))
        
        # Imagen de fondo "images/menu.png"
        fondo_imagen = FitImage(
            source="images/menu.png",
            radius=[16, 16, 16, 16],
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        header_layout.add_widget(fondo_imagen)
        
        # Contenido interior
        contenido_interno = MDBoxLayout(
            orientation='vertical',
            size_hint=(1, 1),
            padding=[dp(16), dp(12), dp(16), dp(12)],
            spacing=dp(10),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        
        # Título CENTRADO y en color BLANCO
        lbl_titulo = MDLabel(
            text="Planificador",
            font_style="H5",
            bold=True,
            halign="center",
            size_hint_y=None,
            height=dp(34),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1)
        )
        lbl_titulo.bind(size=lambda s, w: setattr(s, 'text_size', w))
        
        # Contenedor de botones ALINEADO A LA IZQUIERDA
        botones_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint=(None, None),
            size=(dp(290), dp(36)),
            spacing=dp(8)
        )
        
        btn_gestionar = MDRaisedButton(
            text="Recetas",
            font_size="11sp",
            size_hint_x=None,
            width=dp(90),
            elevation=0,
            md_bg_color=(0.65, 0.55, 0.75, 0.9),
            text_color=(1, 1, 1, 1)
        )
        btn_gestionar.bind(on_release=lambda x: self.abrir_dialogo_gestionar_recetas())

        btn_programar_fecha = MDRaisedButton(
            text="+ Programar",
            font_size="11sp",
            size_hint_x=None,
            width=dp(105),
            elevation=0,
            md_bg_color=(0.78, 0.68, 0.88, 0.9),
            text_color=(0.28, 0.18, 0.38, 1)
        )
        btn_programar_fecha.bind(on_release=lambda x: self.abrir_dialogo_programar_calendario())

        btn_nueva_receta = MDRaisedButton(
            text="+ Receta",
            font_size="11sp",
            size_hint_x=None,
            width=dp(85),
            elevation=0,
            md_bg_color=(0.38, 0.25, 0.50, 0.9),
            text_color=(1, 1, 1, 1)
        )
        btn_nueva_receta.bind(on_release=lambda x: self.abrir_dialogo_crear_receta())
        
        botones_layout.add_widget(btn_gestionar)
        botones_layout.add_widget(btn_programar_fecha)
        botones_layout.add_widget(btn_nueva_receta)
        
        contenido_interno.add_widget(lbl_titulo)
        contenido_interno.add_widget(botones_layout)
        
        header_layout.add_widget(contenido_interno)
        header_card.add_widget(header_layout)
        self.layout_principal.add_widget(header_card)
        
        scroll = ScrollView(size_hint=(1, 1))
        self.contenedor_menu = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(10),
            padding=[0, dp(4), 0, dp(10)]
        )
        self.contenedor_menu.bind(minimum_height=self.contenedor_menu.setter('height'))
        
        scroll.add_widget(self.contenedor_menu)
        self.layout_principal.add_widget(scroll)
        self.add_widget(self.layout_principal)
        
        self.dialogo_activo = None
        
        Clock.schedule_once(lambda dt: self.actualizar_vista(), 0.1)

    def on_enter(self):
        self.actualizar_vista()

    def formatear_fecha_amigable(self, fecha_str):
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d")
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
            meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
            return f"{dias[dt.weekday()]}, {dt.day:02d} de {meses[dt.month - 1]}"
        except Exception:
            return fecha_str

    def actualizar_vista(self):
        self.contenedor_menu.clear_widgets()
        
        menus_mensuales = obtener_menu_mensual()
        if menus_mensuales:
            dias_dict = {}
            for item in menus_mensuales:
                menu_id, fecha, tipo_comida, nombre_receta, ingredientes, instrucciones, receta_id = item
                if fecha not in dias_dict:
                    dias_dict[fecha] = []
                dias_dict[fecha].append(item)

            for fecha, items_dia in sorted(dias_dict.items()):
                fecha_bonita = self.formatear_fecha_amigable(fecha)
                
                card_dia = MDCard(
                    orientation='vertical',
                    padding=dp(12),
                    spacing=dp(8),
                    size_hint_y=None,
                    size_hint_x=1,
                    elevation=0,
                    radius=[18, 18, 18, 18],
                    md_bg_color=(1, 1, 1, 1)
                )
                card_dia.bind(minimum_height=card_dia.setter('height'))
                
                card_dia.add_widget(MDLabel(
                    text=fecha_bonita.upper(),
                    font_style="Caption",
                    bold=True,
                    size_hint_y=None,
                    height=dp(22),
                    theme_text_color="Custom",
                    text_color=(0.55, 0.35, 0.75, 1)
                ))
                
                for item in items_dia:
                    menu_id, fecha, tipo_comida, nombre_receta, ingredientes, instrucciones, receta_id = item
                    
                    fila_m = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(36), spacing=dp(4))
                    
                    lbl_menu_txt = MDLabel(
                        text=f"{tipo_comida}: {nombre_receta}",
                        font_style="Body2",
                        bold=True,
                        size_hint_x=0.68,
                        theme_text_color="Custom",
                        text_color=(0.28, 0.18, 0.38, 1)
                    )
                    lbl_menu_txt.bind(on_touch_down=lambda inst, touch, nom=nombre_receta, ing=ingredientes, ins=instrucciones: 
                                      self.verificar_clic_receta(inst, touch, nom, ing, ins))
                    
                    btn_add_lista = MDIconButton(
                        icon="cart-plus",
                        theme_text_color="Custom",
                        text_color=(0.48, 0.32, 0.64, 1),
                        size_hint_x=0.14,
                        pos_hint={"center_y": 0.5}
                    )
                    btn_add_lista.bind(on_release=lambda x, rid=receta_id: self.enviar_ingredientes_a_lista(rid))
                    
                    btn_eliminar = MDIconButton(
                        icon="trash-can-outline",
                        theme_text_color="Custom",
                        text_color=(0.85, 0.35, 0.35, 1),
                        size_hint_x=0.14,
                        pos_hint={"center_y": 0.5}
                    )
                    btn_eliminar.bind(on_release=lambda x, m_id=menu_id: self.eliminar_menu_programado(m_id))
                    
                    fila_m.add_widget(lbl_menu_txt)
                    fila_m.add_widget(btn_add_lista)
                    fila_m.add_widget(btn_eliminar)
                    card_dia.add_widget(fila_m)
                
                self.contenedor_menu.add_widget(card_dia)
        else:
            card_vacia = MDCard(
                orientation='vertical',
                padding=dp(20),
                size_hint_y=None,
                size_hint_x=1,
                height=dp(80),
                elevation=0,
                radius=[18, 18, 18, 18],
                md_bg_color=(1, 1, 1, 1)
            )
            card_vacia.add_widget(MDLabel(
                text="No hay menús programados.\nPulsa '+ Programar' para añadir uno.",
                halign="center",
                font_style="Body2",
                theme_text_color="Custom",
                text_color=(0.45, 0.38, 0.55, 1)
            ))
            self.contenedor_menu.add_widget(card_vacia)

    def verificar_clic_receta(self, widget, touch, nombre, ingredientes, instrucciones):
        if widget.collide_point(*touch.pos):
            self.mostrar_dialogo_detalle_receta(nombre, ingredientes, instrucciones)

    def mostrar_dialogo_detalle_receta(self, nombre, ingredientes, instrucciones):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        instrucciones_texto = instrucciones if instrucciones else "No se especificaron pasos de preparación."
        texto_completo = f"Ingredientes:\n{ingredientes}\n\nPreparacion / Pasos:\n{instrucciones_texto}"
        
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(140), padding=[dp(4), dp(4), dp(4), dp(4)])
        contenido.add_widget(MDLabel(text=texto_completo, size_hint_y=None, height=dp(120), theme_text_color="Custom", text_color=(0.28, 0.18, 0.38, 1)))

        self.dialogo_activo = MDDialog(
            title=f"Receta: {nombre}",
            type="custom",
            content_cls=contenido,
            buttons=[
                MDRaisedButton(text="CERRAR", on_release=lambda x: self.dialogo_activo.dismiss(), md_bg_color=(0.38, 0.25, 0.50, 1), text_color=(1, 1, 1, 1))
            ]
        )
        self.dialogo_activo.open()

    def eliminar_menu_programado(self, menu_id):
        eliminar_menu_programado_db(menu_id)
        self.actualizar_vista()

    def enviar_ingredientes_a_lista(self, receta_id):
        convertir_receta_a_lista(receta_id)
        self.mostrar_alerta("Aviso", "Ingredientes añadidos a tu lista de compras.")

    def abrir_dialogo_crear_receta(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(170), padding=[dp(4), dp(4), dp(4), dp(4)])
        
        txt_nombre = MDTextField(hint_text="Nombre de la receta", mode="rectangle")
        txt_ingredientes = MDTextField(hint_text="Ingredientes (separados por coma)", mode="rectangle")
        txt_instrucciones = MDTextField(hint_text="Preparación / Pasos (Opcional)", mode="rectangle")
        
        contenido.add_widget(txt_nombre)
        contenido.add_widget(txt_ingredientes)
        contenido.add_widget(txt_instrucciones)
        
        def guardar(instance):
            nom = txt_nombre.text.strip().capitalize()
            ings = txt_ingredientes.text.strip()
            inst = txt_instrucciones.text.strip()
            if nom and ings:
                guardar_receta(nom, ings, inst)
                self.dialogo_activo.dismiss()
                self.actualizar_vista()

        btn_cancelar = MDRaisedButton(text="CANCELAR", on_release=lambda x: self.dialogo_activo.dismiss(), md_bg_color=(0.98, 0.85, 0.85, 1), text_color=(0.70, 0.20, 0.20, 1))
        btn_guardar = MDRaisedButton(text="GUARDAR", on_release=guardar, md_bg_color=(0.38, 0.25, 0.50, 1), text_color=(1, 1, 1, 1))

        self.dialogo_activo = MDDialog(
            title="Nueva Receta",
            type="custom",
            content_cls=contenido,
            buttons=[btn_cancelar, btn_guardar]
        )
        self.dialogo_activo.open()

    def abrir_dialogo_gestionar_recetas(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        recetas = obtener_recetas()
        if not recetas:
            self.mostrar_alerta("Aviso", "No hay recetas guardadas todavía.")
            return

        contenido_principal = MDBoxLayout(orientation='vertical', spacing=dp(8), size_hint_y=None, height=dp(230), padding=[dp(4), dp(4), dp(4), dp(4)])

        scroll_recetas = ScrollView(size_hint=(1, 1))
        box_recetas = MDBoxLayout(orientation='vertical', spacing=dp(6), size_hint_y=None)
        box_recetas.bind(minimum_height=box_recetas.setter('height'))

        for r in recetas:
            r_id, r_nom, r_ing, r_inst = r[0], r[1], r[2], r[3]
            
            fila = MDBoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40), spacing=dp(4))
            lbl = MDLabel(text=r_nom, font_style="Body2", size_hint_x=0.60, theme_text_color="Custom", text_color=(0.28, 0.18, 0.38, 1))
            
            btn_editar = MDIconButton(
                icon="pencil-outline",
                theme_text_color="Custom",
                text_color=(0.55, 0.45, 0.65, 1),
                size_hint_x=0.20
            )
            btn_editar.bind(on_release=lambda x, rid=r_id, rnom=r_nom, ring=r_ing, rinst=r_inst: self.abrir_dialogo_editar_receta(rid, rnom, ring, rinst))

            btn_borrar = MDIconButton(
                icon="trash-can-outline",
                theme_text_color="Custom",
                text_color=(0.85, 0.35, 0.35, 1),
                size_hint_x=0.20
            )
            btn_borrar.bind(on_release=lambda x, rid=r_id: self.borrar_receta_y_refrescar(rid))

            fila.add_widget(lbl)
            fila.add_widget(btn_editar)
            fila.add_widget(btn_borrar)
            box_recetas.add_widget(fila)

        scroll_recetas.add_widget(box_recetas)
        contenido_principal.add_widget(scroll_recetas)

        btn_cerrar = MDRaisedButton(
            text="CERRAR",
            on_release=lambda x: self.dialogo_activo.dismiss(),
            md_bg_color=(0.38, 0.25, 0.50, 1),
            text_color=(1, 1, 1, 1)
        )

        self.dialogo_activo = MDDialog(
            title="Mis Recetas",
            type="custom",
            content_cls=contenido_principal,
            buttons=[btn_cerrar]
        )
        self.dialogo_activo.open()

    def abrir_dialogo_editar_receta(self, r_id, nombre, ingredientes, instrucciones):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(170), padding=[dp(4), dp(4), dp(4), dp(4)])
        
        txt_nombre = MDTextField(text=nombre, hint_text="Nombre de la receta", mode="rectangle")
        txt_ingredientes = MDTextField(text=ingredientes, hint_text="Ingredientes (separados por coma)", mode="rectangle")
        txt_instrucciones = MDTextField(text=instrucciones if instrucciones else "", hint_text="Preparación / Pasos (Opcional)", mode="rectangle")
        
        contenido.add_widget(txt_nombre)
        contenido.add_widget(txt_ingredientes)
        contenido.add_widget(txt_instrucciones)
        
        def guardar_cambios(instance):
            nom = txt_nombre.text.strip().capitalize()
            ings = txt_ingredientes.text.strip()
            inst = txt_instrucciones.text.strip()
            if nom and ings:
                actualizar_receta_db(r_id, nom, ings, inst)
                self.dialogo_activo.dismiss()
                self.actualizar_vista()

        btn_cancelar = MDRaisedButton(text="CANCELAR", on_release=lambda x: self.dialogo_activo.dismiss(), md_bg_color=(0.98, 0.85, 0.85, 1), text_color=(0.70, 0.20, 0.20, 1))
        btn_guardar = MDRaisedButton(text="GUARDAR", on_release=guardar_cambios, md_bg_color=(0.38, 0.25, 0.50, 1), text_color=(1, 1, 1, 1))

        self.dialogo_activo = MDDialog(
            title="Editar Receta",
            type="custom",
            content_cls=contenido,
            buttons=[btn_cancelar, btn_guardar]
        )
        self.dialogo_activo.open()

    def borrar_receta_y_refrescar(self, r_id):
        eliminar_receta_db(r_id)
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
        self.actualizar_vista()
        self.abrir_dialogo_gestionar_recetas()

    def abrir_dialogo_programar_calendario(self):
        if self.dialogo_activo:
            self.dialogo_activo.dismiss()
            
        recetas = obtener_recetas()
        if not recetas:
            self.mostrar_alerta("Aviso", "Primero debes crear al menos una receta.")
            return
            
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(150), padding=[dp(4), dp(4), dp(4), dp(4)])
        
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        btn_fecha = MDRaisedButton(
            text=f"Fecha: {fecha_actual}",
            size_hint_x=1,
            md_bg_color=(0.92, 0.88, 0.96, 1),
            text_color=(0.38, 0.25, 0.50, 1)
        )
        seleccion_fecha = {"fecha": fecha_actual}
        
        def mostrar_calendario(instance):
            def al_guardar_fecha(instance_date_picker, value, date_range):
                seleccion_fecha["fecha"] = value.strftime("%Y-%m-%d")
                btn_fecha.text = f"Fecha: {seleccion_fecha['fecha']}"
                date_dialog.dismiss()

            date_dialog = MDDatePicker()
            date_dialog.bind(on_save=al_guardar_fecha)
            date_dialog.open()

        btn_fecha.bind(on_release=mostrar_calendario)

        btn_tipo = MDRaisedButton(
            text="Tipo: Almuerzo",
            size_hint_x=1,
            md_bg_color=(0.92, 0.88, 0.96, 1),
            text_color=(0.38, 0.25, 0.50, 1)
        )
        seleccion_tipo = {"tipo": "Almuerzo"}
        
        tipos_menu = ["Desayuno", "Almuerzo", "Cena"]
        items_tipo = [
            {"text": t, "viewclass": "OneLineListItem", "on_release": lambda tp=t: seleccionar_tipo_dropdown(tp)}
            for t in tipos_menu
        ]
        dropdown_tipo = MDDropdownMenu(caller=btn_tipo, items=items_tipo, width_mult=4)
        
        def seleccionar_tipo_dropdown(tp):
            seleccion_tipo["tipo"] = tp
            btn_tipo.text = f"Tipo: {tp}"
            dropdown_tipo.dismiss()
            
        btn_tipo.bind(on_release=lambda x: dropdown_tipo.open())

        btn_receta = MDRaisedButton(
            text="Elegir receta", 
            size_hint_x=1, 
            md_bg_color=(0.92, 0.88, 0.96, 1), 
            text_color=(0.38, 0.25, 0.50, 1)
        )
        seleccion_receta = {"receta_id": None, "nombre": "Elegir receta"}
        
        menu_items = [
            {"text": r[1], "viewclass": "OneLineListItem", "on_release": lambda rid=r[0], rnom=r[1]: seleccionar_receta_dropdown(rid, rnom)}
            for r in recetas
        ]
        dropdown_receta = MDDropdownMenu(caller=btn_receta, items=menu_items, width_mult=4)
        
        def seleccionar_receta_dropdown(rid, rnom):
            seleccion_receta["receta_id"] = rid
            seleccion_receta["nombre"] = rnom
            btn_receta.text = rnom
            dropdown_receta.dismiss()
            
        btn_receta.bind(on_release=lambda x: dropdown_receta.open())
        
        contenido.add_widget(btn_fecha)
        contenido.add_widget(btn_tipo)
        contenido.add_widget(btn_receta)
        
        def confirmar(instance):
            if seleccion_receta["receta_id"] is not None:
                programar_menu_por_fecha(seleccion_fecha["fecha"], seleccion_tipo["tipo"], seleccion_receta["receta_id"])
                self.dialogo_activo.dismiss()
                self.actualizar_vista()
            else:
                self.mostrar_alerta("Aviso", "Por favor selecciona una receta.")

        btn_cancelar = MDRaisedButton(text="CANCELAR", on_release=lambda x: self.dialogo_activo.dismiss(), md_bg_color=(0.98, 0.85, 0.85, 1), text_color=(0.70, 0.20, 0.20, 1))
        btn_programar = MDRaisedButton(text="PROGRAMAR", on_release=confirmar, md_bg_color=(0.38, 0.25, 0.50, 1), text_color=(1, 1, 1, 1))

        self.dialogo_activo = MDDialog(
            title="Programar Menú",
            type="custom",
            content_cls=contenido,
            buttons=[btn_cancelar, btn_programar]
        )
        self.dialogo_activo.open()

    def mostrar_alerta(self, titulo, mensaje):
        contenido = MDBoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(60), padding=[dp(4), dp(4), dp(4), dp(4)])
        contenido.add_widget(MDLabel(text=mensaje, halign="center", theme_text_color="Custom", text_color=(0.28, 0.18, 0.38, 1)))

        btn_entendido = MDRaisedButton(
            text="ENTENDIDO",
            on_release=lambda x: self.dialogo_activo.dismiss(),
            md_bg_color=(0.38, 0.25, 0.50, 1),
            text_color=(1, 1, 1, 1)
        )

        self.dialogo_activo = MDDialog(
            title=titulo,
            type="custom",
            content_cls=contenido,
            buttons=[btn_entendido]
        )
        self.dialogo_activo.open()