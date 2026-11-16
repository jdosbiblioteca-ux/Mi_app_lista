import sqlite3
import os
import requests
from datetime import datetime

def obtener_ruta_db():
    # Forzamos a que la base de datos se guarde siempre localmente en la carpeta del proyecto
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'compras.db')

def inicializar_base_datos(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
        
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    
    # 1. Tabla productos_disponibles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS productos_disponibles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            categoria TEXT NOT NULL,
            barcode TEXT UNIQUE
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE productos_disponibles ADD COLUMN barcode TEXT UNIQUE")
    except sqlite3.OperationalError:
        pass
    
    # 2. Tabla lista_compras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS lista_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            precio_estimado REAL DEFAULT 0.0,
            cantidad INTEGER DEFAULT 1,
            estado TEXT CHECK(estado IN ('pendiente', 'comprado')) DEFAULT 'pendiente',
            FOREIGN KEY (producto_id) REFERENCES productos_disponibles (id) ON DELETE CASCADE
        )
    ''')
    
    # 3. Tabla historial_compras
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historial_compras (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT NOT NULL,
            supermercado TEXT NOT NULL,
            producto_nombre TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            precio_final REAL NOT NULL
        )
    ''')
    
    # 4. Tabla recetas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_receta TEXT NOT NULL UNIQUE,
            ingredientes TEXT NOT NULL,
            instrucciones TEXT
        )
    ''')
    
    # 5. Tabla planificador_menus (con soporte para fecha)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS planificador_menus (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia_semana TEXT NOT NULL,
            tipo_comida TEXT NOT NULL,
            receta_id INTEGER NOT NULL,
            fecha TEXT,
            FOREIGN KEY (receta_id) REFERENCES recetas (id) ON DELETE CASCADE
        )
    ''')
    
    try:
        cursor.execute("ALTER TABLE planificador_menus ADD COLUMN fecha TEXT")
    except sqlite3.OperationalError:
        pass

    # 6. Tabla despensa
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS despensa (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_producto TEXT NOT NULL UNIQUE,
            codigo_barras TEXT UNIQUE,
            categoria_pasillo TEXT NOT NULL,
            stock INTEGER DEFAULT 0
        )
    ''')
    
    conexion.commit()
    conexion.close()

def obtener_categorias_existentes(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT DISTINCT categoria FROM productos_disponibles UNION SELECT DISTINCT categoria_pasillo FROM despensa')
        return [row[0] for row in cursor.fetchall() if row[0]]
    finally:
        conexion.close()

def renombrar_pasillo_db(viejo_nombre, nuevo_nombre, db_path=None):
    """Renombra un pasillo en la despensa y en el catálogo de productos disponibles."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        nuevo = nuevo_nombre.strip().capitalize()
        viejo = viejo_nombre.strip()
        cursor.execute('UPDATE despensa SET categoria_pasillo = ? WHERE categoria_pasillo = ?', (nuevo, viejo))
        cursor.execute('UPDATE productos_disponibles SET categoria = ? WHERE categoria = ?', (nuevo, viejo))
        conexion.commit()
    finally:
        conexion.close()

def eliminar_pasillo_db(nombre_pasillo, db_path=None):
    """Elimina los productos de un pasillo en la despensa."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('DELETE FROM despensa WHERE categoria_pasillo = ?', (nombre_pasillo,))
        conexion.commit()
    finally:
        conexion.close()

def agregar_producto_disponible(nombre, categoria="Otros", db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO productos_disponibles (nombre, categoria)
            VALUES (?, ?)
            ON CONFLICT(nombre) DO UPDATE SET categoria=excluded.categoria
        ''', (nombre.strip().capitalize(), categoria.strip().capitalize()))
        conexion.commit()
        cursor.execute('SELECT id FROM productos_disponibles WHERE nombre = ?', (nombre.strip().capitalize(),))
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conexion.close()

def buscar_producto_por_barcode(barcode, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT id, nombre, categoria FROM productos_disponibles WHERE barcode = ?', (barcode,))
        return cursor.fetchone()
    finally:
        conexion.close()

def agregar_producto_con_barcode(nombre, categoria, barcode, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO productos_disponibles (nombre, categoria, barcode)
            VALUES (?, ?, ?)
        ''', (nombre.strip().capitalize(), categoria.strip().capitalize(), barcode))
        conexion.commit()
        return cursor.lastrowid
    finally:
        conexion.close()

def actualizar_producto_catalogo(producto_id, nuevo_nombre, nueva_categoria, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            UPDATE productos_disponibles
            SET nombre = ?, categoria = ?
            WHERE id = ?
        ''', (nuevo_nombre.strip().capitalize(), nueva_categoria.strip().capitalize(), producto_id))
        conexion.commit()
    finally:
        conexion.close()

def agregar_a_lista_compras(producto_id, precio_estimado=0.0, cantidad=1, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO lista_compras (producto_id, precio_estimado, cantidad, estado)
            VALUES (?, ?, ?, 'pendiente')
        ''', (producto_id, precio_estimado, cantidad))
        conexion.commit()
    finally:
        conexion.close()

def actualizar_elemento_lista(item_id, cantidad, precio_estimado, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            UPDATE lista_compras
            SET cantidad = ?, precio_estimado = ?
            WHERE id = ?
        ''', (cantidad, precio_estimado, item_id))
        conexion.commit()
    finally:
        conexion.close()

def cambiar_estado_comprado(item_id, estado, supermercado="General", precio_final=0.0, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
        
    if estado not in ('pendiente', 'comprado'):
        raise ValueError("El estado debe ser 'pendiente' o 'comprado'")
        
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        if estado == 'comprado':
            cursor.execute('''
                SELECT pd.nombre, lc.cantidad 
                FROM lista_compras lc
                JOIN productos_disponibles pd ON lc.producto_id = pd.id
                WHERE lc.id = ?
            ''', (item_id,))
            resultado = cursor.fetchone()
            
            if resultado:
                prod_nombre, cantidad_item = resultado
                fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute('''
                    INSERT INTO historial_compras (fecha, supermercado, producto_nombre, cantidad, precio_final)
                    VALUES (?, ?, ?, ?, ?)
                ''', (fecha_actual, supermercado.strip().capitalize(), prod_nombre, cantidad_item, precio_final))

        cursor.execute('''
            UPDATE lista_compras
            SET estado = ?
            WHERE id = ?
        ''', (estado, item_id))
        conexion.commit()
    finally:
        conexion.close()

def obtener_elementos_activos(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            SELECT 
                lc.id, 
                pd.nombre, 
                pd.categoria, 
                lc.precio_estimado, 
                lc.cantidad, 
                lc.estado,
                pd.id as producto_id
            FROM lista_compras lc
            JOIN productos_disponibles pd ON lc.producto_id = pd.id
            WHERE lc.estado = 'pendiente'
            ORDER BY pd.categoria, pd.nombre
        ''')
        return cursor.fetchall()
    finally:
        conexion.close()

def finalizar_compra_db(supermercado, precios_actuales_dict=None, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
        
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute("PRAGMA table_info(productos_disponibles)")
        columnas = [col[1] for col in cursor.fetchall()]
        
        if 'barcode' in columnas:
            cursor.execute('''
                SELECT lc.id, pd.nombre, pd.categoria, pd.barcode, lc.cantidad
                FROM lista_compras lc
                JOIN productos_disponibles pd ON lc.producto_id = pd.id
                WHERE lc.estado = 'pendiente'
            ''')
        else:
            cursor.execute('''
                SELECT lc.id, pd.nombre, pd.categoria, NULL, lc.cantidad
                FROM lista_compras lc
                JOIN productos_disponibles pd ON lc.producto_id = pd.id
                WHERE lc.estado = 'pendiente'
            ''')
            
        elementos = cursor.fetchall()
        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        sup_nombre = supermercado.strip().capitalize() if supermercado else "Supermercado General"
        
        for item in elementos:
            item_id, nombre_prod, categoria, barcode, cantidad = item
            precio_final = 0.0
            if precios_actuales_dict and item_id in precios_actuales_dict:
                precio_final = float(precios_actuales_dict[item_id])
                
            cursor.execute('''
                INSERT INTO historial_compras (fecha, supermercado, producto_nombre, cantidad, precio_final)
                VALUES (?, ?, ?, ?, ?)
            ''', (fecha_actual, sup_nombre, nombre_prod, cantidad, precio_final))
            
            cat_val = categoria if categoria else "Otros"
            
            cursor.execute('SELECT id, stock FROM despensa WHERE LOWER(nombre_producto) = LOWER(?)', (nombre_prod,))
            despensa_row = cursor.fetchone()
            
            if despensa_row:
                d_id, stock_actual = despensa_row
                nuevo_stock = stock_actual + cantidad
                cursor.execute('UPDATE despensa SET stock = ?, categoria_pasillo = ? WHERE id = ?', (nuevo_stock, cat_val, d_id))
            else:
                cursor.execute('''
                    INSERT INTO despensa (nombre_producto, codigo_barras, categoria_pasillo, stock)
                    VALUES (?, ?, ?, ?)
                ''', (nombre_prod, barcode, cat_val, cantidad))
                
        cursor.execute('DELETE FROM lista_compras')
        conexion.commit()
    finally:
        conexion.close()

def consumir_producto_db(codigo_barras, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
        
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT id, nombre_producto, categoria_pasillo, stock FROM despensa WHERE codigo_barras = ?', (codigo_barras,))
        row = cursor.fetchone()
        
        if not row:
            return False, "Producto no encontrado en la despensa."
            
        d_id, nombre_prod, categoria, stock = row
        nuevo_stock = max(0, stock - 1)
        cursor.execute('UPDATE despensa SET stock = ? WHERE id = ?', (nuevo_stock, d_id))
        
        cursor.execute('SELECT id FROM productos_disponibles WHERE nombre = ?', (nombre_prod,))
        prod_cat = cursor.fetchone()
        if prod_cat:
            prod_id = prod_cat[0]
        else:
            cursor.execute('INSERT INTO productos_disponibles (nombre, categoria, barcode) VALUES (?, ?, ?)', (nombre_prod, categoria, codigo_barras))
            prod_id = cursor.lastrowid
            
        cursor.execute('''
            INSERT INTO lista_compras (producto_id, precio_estimado, cantidad, estado)
            VALUES (?, 0.0, 1, 'pendiente')
        ''', (prod_id,))
        
        conexion.commit()
        return True, f"¡'{nombre_prod}' consumido y añadido a la lista de compras!"
    finally:
        conexion.close()

def obtener_elementos_despensa(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT id, nombre_producto, codigo_barras, categoria_pasillo, stock FROM despensa ORDER BY categoria_pasillo, nombre_producto')
        return cursor.fetchall()
    finally:
        conexion.close()

def guardar_receta(nombre_receta, ingredientes, instrucciones="", db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO recetas (nombre_receta, ingredientes, instrucciones)
            VALUES (?, ?, ?)
        ''', (nombre_receta.strip().capitalize(), ingredientes.strip(), instrucciones.strip()))
        conexion.commit()
    finally:
        conexion.close()

def obtener_recetas(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT id, nombre_receta, ingredientes, instrucciones FROM recetas ORDER BY nombre_receta')
        return cursor.fetchall()
    finally:
        conexion.close()

def programar_menu(dia_semana, tipo_comida, receta_id, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO planificador_menus (dia_semana, tipo_comida, receta_id)
            VALUES (?, ?, ?)
        ''', (dia_semana.strip().capitalize(), tipo_comida.strip().capitalize(), receta_id))
        conexion.commit()
    finally:
        conexion.close()

def programar_menu_por_fecha(fecha_str, tipo_comida, receta_id, db_path=None):
    """Programa una receta para una fecha específica del mes (YYYY-MM-DD)."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            INSERT INTO planificador_menus (dia_semana, tipo_comida, receta_id, fecha)
            VALUES (?, ?, ?, ?)
        ''', (fecha_str, tipo_comida.strip().capitalize(), receta_id, fecha_str))
        conexion.commit()
    finally:
        conexion.close()

def obtener_menu_semanal(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            SELECT pm.id, pm.dia_semana, pm.tipo_comida, r.nombre_receta, r.ingredientes, r.id
            FROM planificador_menus pm
            JOIN recetas r ON pm.receta_id = r.id
            ORDER BY 
                CASE pm.dia_semana
                    WHEN 'Lunes' THEN 1
                    WHEN 'Martes' THEN 2
                    WHEN 'Miércoles' THEN 3
                    WHEN 'Jueves' THEN 4
                    WHEN 'Viernes' THEN 5
                    WHEN 'Sábado' THEN 6
                    WHEN 'Domingo' THEN 7
                    ELSE 8
                END
        ''')
        return cursor.fetchall()
    finally:
        conexion.close()

def obtener_menu_mensual(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            SELECT pm.id, pm.fecha, pm.tipo_comida, r.nombre_receta, r.ingredientes, r.instrucciones, r.id
            FROM planificador_menus pm
            JOIN recetas r ON pm.receta_id = r.id
            ORDER BY pm.fecha ASC
        ''')
        return cursor.fetchall()
    finally:
        conexion.close()

def convertir_receta_a_lista(receta_id, db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT ingredientes FROM recetas WHERE id = ?', (receta_id,))
        resultado = cursor.fetchone()
        if not resultado:
            return
        texto_ingredientes = resultado[0]
        lineas = []
        for bloque in texto_ingredientes.split('\n'):
            for item in bloque.split(','):
                limpio = item.strip().capitalize()
                if limpio:
                    lineas.append(limpio)
        for nombre_ingrediente in lineas:
            cursor.execute('SELECT id FROM productos_disponibles WHERE nombre = ?', (nombre_ingrediente,))
            prod = cursor.fetchone()
            if prod:
                producto_id = prod[0]
            else:
                cursor.execute('''
                    INSERT INTO productos_disponibles (nombre, categoria)
                    VALUES (?, ?)
                ''', (nombre_ingrediente, 'Despensa'))
                producto_id = cursor.lastrowid
            cursor.execute('''
                INSERT INTO lista_compras (producto_id, precio_estimado, cantidad, estado)
                VALUES (?, 0.0, 1, 'pendiente')
            ''', (producto_id,))
        conexion.commit()
    finally:
        conexion.close()

def obtener_recetas_sugeridas(db_path=None):
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('SELECT DISTINCT LOWER(producto_nombre) FROM historial_compras')
        historial_compras = [row[0] for row in cursor.fetchall()]
        cursor.execute('SELECT LOWER(nombre) FROM productos_disponibles')
        productos_catalogo = [row[0] for row in cursor.fetchall()]
        cursor.execute('SELECT LOWER(nombre_producto) FROM despensa WHERE stock > 0')
        despensa_stock = [row[0] for row in cursor.fetchall()]
        
        inventario_usuario = set(historial_compras + productos_catalogo + despensa_stock)
        
        cursor.execute('SELECT id, nombre_receta, ingredientes, instrucciones FROM recetas')
        recetas = cursor.fetchall()
        
        sugerencias = []
        for r_id, r_nombre, r_ingredientes, r_instrucciones in recetas:
            ingredientes_lista = []
            for bloque in r_ingredientes.split('\n'):
                for item in bloque.split(','):
                    limpio = item.strip().lower()
                    if limpio:
                        ingredientes_lista.append(limpio)
            if not ingredientes_lista:
                continue
            total_ingredientes = len(ingredientes_lista)
            coincidencias = 0
            for ing in ingredientes_lista:
                encontrado = any(ing in inv or inv in ing for inv in inventario_usuario)
                if encontrado:
                    coincidencias += 1
            porcentaje = (coincidencias / total_ingredientes) if total_ingredientes > 0 else 0.0
            sugerencias.append((r_id, r_nombre, r_ingredientes, r_instrucciones, porcentaje))
            
        sugerencias.sort(key=lambda x: x[4], reverse=True)
        return sugerencias
    finally:
        conexion.close()

def eliminar_elemento_lista_db(item_id, db_path=None):
    """Elimina un producto específico de la lista de compras activa."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('DELETE FROM lista_compras WHERE id = ?', (item_id,))
        conexion.commit()
    finally:
        conexion.close()

def eliminar_producto_despensa_db(despensa_id, db_path=None):
    """Elimina un producto por completo del inventario de la despensa."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('DELETE FROM despensa WHERE id = ?', (despensa_id,))
        conexion.commit()
    finally:
        conexion.close()

def eliminar_menu_programado_db(menu_id, db_path=None):
    """Elimina un menú programado del planificador semanal/mensual."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('DELETE FROM planificador_menus WHERE id = ?', (menu_id,))
        conexion.commit()
    finally:
        conexion.close()

def actualizar_receta_db(receta_id, nombre, ingredientes, instrucciones, db_path=None):
    """Actualiza los datos de una receta existente."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('''
            UPDATE recetas 
            SET nombre_receta = ?, ingredientes = ?, instrucciones = ?
            WHERE id = ?
        ''', (nombre.strip().capitalize(), ingredientes.strip(), instrucciones.strip(), receta_id))
        conexion.commit()
    finally:
        conexion.close()

def eliminar_receta_db(receta_id, db_path=None):
    """Elimina una receta del sistema."""
    if db_path is None:
        db_path = obtener_ruta_db()
    conexion = sqlite3.connect(db_path)
    cursor = conexion.cursor()
    try:
        cursor.execute('DELETE FROM recetas WHERE id = ?', (receta_id,))
        conexion.commit()
    finally:
        conexion.close()