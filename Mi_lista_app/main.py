import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

from database import inicializar_base_datos, obtener_elementos_activos, agregar_producto_disponible
from views.shopping_list import ShoppingListScreen
from views.pantry import PantryScreen
from views.menu_planner import MenuPlannerScreen
# (Se eliminó la importación de history_charts)

class ListaComprasApp(MDApp):
    """
    App de Compras & Despensa - Edición Morada Elegante y Moderna.
    """
    def build(self):
        self.title = "Lista de Compras & Despensa"
        
        # Gama de colores Morados
        self.theme_cls.primary_palette = "DeepPurple"
        self.theme_cls.primary_hue = "500"
        self.theme_cls.accent_palette = "Purple"
        self.theme_cls.theme_style = "Light"

        inicializar_base_datos()
        self._cargar_datos_demo_si_esta_vacio()

        pantalla_principal = MDScreen(name="main_container")
        
        # Barra de navegación inferior con fondo lavanda ultra suave
        bottom_nav = MDBottomNavigation(
            panel_color=(0.97, 0.95, 0.99, 1)
        )

        # Pestaña 1: Compras
        tab_lista = MDBottomNavigationItem(
            name="tab_lista",
            text="Compras",
            icon="cart-outline",
        )
        shopping_screen = ShoppingListScreen(name="shopping_list")
        tab_lista.add_widget(shopping_screen)
        tab_lista.bind(on_tab_press=lambda *x: shopping_screen.actualizar_vista())

        # Pestaña 2: Despensa
        tab_despensa = MDBottomNavigationItem(
            name="tab_despensa",
            text="Despensa",
            icon="package-variant-closed",
        )
        pantry_screen = PantryScreen(name="pantry")
        tab_despensa.add_widget(pantry_screen)
        tab_despensa.bind(on_tab_press=lambda *x: pantry_screen.actualizar_vista_despensa())

        # Pestaña 3: Menús (Planificador)
        tab_menu = MDBottomNavigationItem(
            name="tab_menu",
            text="Menús",
            icon="silverware-fork-knife",
        )
        menu_screen = MenuPlannerScreen(name="menu_planner")
        tab_menu.add_widget(menu_screen)
        tab_menu.bind(on_tab_press=lambda *x: menu_screen.actualizar_vista() if hasattr(menu_screen, 'actualizar_vista') else None)

        # Añadimos únicamente las 3 pestañas requeridas a la barra de navegación
        bottom_nav.add_widget(tab_lista)
        bottom_nav.add_widget(tab_despensa)
        bottom_nav.add_widget(tab_menu)

        pantalla_principal.add_widget(bottom_nav)

        sm = MDScreenManager()
        sm.add_widget(pantalla_principal)

        return sm

    def _cargar_datos_demo_si_esta_vacio(self):
        elementos = obtener_elementos_activos()
        if not elementos:
            productos_demo = [
                ("Manzanas", "Frutas y Verduras", 2.50, 1),
                ("Leche Entera", "Lácteos", 1.20, 2),
                ("Jabón Líquido", "Limpieza", 3.80, 1),
                ("Pan de Molde", "Panadería", 1.80, 1),
                ("Arroz Extra", "Abarrotes", 1.10, 2)
            ]
            
            for nombre, categoria, _, _ in productos_demo:
                agregar_producto_disponible(nombre, categoria)
                
            from database import obtener_ruta_db
            import sqlite3
            conexion = sqlite3.connect(obtener_ruta_db())
            cursor = conexion.cursor()
            try:
                for i, (_, _, precio, cantidad) in enumerate(productos_demo, start=1):
                    cursor.execute('''
                        INSERT INTO lista_compras (producto_id, precio_estimado, cantidad, estado)
                        VALUES (?, ?, ?, 'pendiente')
                    ''', (i, precio, cantidad))
                conexion.commit()
            finally:
                conexion.close()


if __name__ == "__main__":
    ListaComprasApp().run()