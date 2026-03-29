import sqlite3
from contextlib import contextmanager
import json
from datetime import datetime
from pathlib import Path

# Ruta de la base de datos
DB_PATH = Path(__file__).parent.parent / "data" / "finanzas.db"

@contextmanager
def get_db():
    """Context manager para manejar la conexión a la base de datos"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Inicializa las tablas si no existen"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla de bolsillos (estado actual)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bolsillos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT UNIQUE NOT NULL,
                monto INTEGER NOT NULL DEFAULT 0,
                porcentaje INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de transacciones (historial)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transacciones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL,  -- 'ingreso' o 'gasto'
                bolsillo TEXT,       -- solo para gastos
                monto INTEGER NOT NULL,
                descripcion TEXT,
                fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de configuración (meta, etc.)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS config (
                clave TEXT PRIMARY KEY,
                valor TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabla de CDT
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cdt (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                capital INTEGER NOT NULL,
                tasa REAL NOT NULL,
                meses INTEGER NOT NULL,
                fecha_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar bolsillos por defecto si no existen
        bolsillos_default = [
            ("migracion", 0, 35),
            ("vida_diaria", 0, 50),
            ("liquidez", 0, 10),
            ("disfrute", 0, 5),
        ]
        
        for nombre, monto, porcentaje in bolsillos_default:
            cursor.execute("""
                INSERT OR IGNORE INTO bolsillos (nombre, monto, porcentaje)
                VALUES (?, ?, ?)
            """, (nombre, monto, porcentaje))
        
        # Insertar configuración por defecto
        cursor.execute("""
            INSERT OR IGNORE INTO config (clave, valor)
            VALUES (?, ?)
        """, ("meta_total", "15000000"))
        
        cursor.execute("""
            INSERT OR IGNORE INTO config (clave, valor)
            VALUES (?, ?)
        """, ("ultimo_ingreso_mensual", "0"))
        
        conn.commit()

def cargar_estado():
    """Carga el estado actual desde la base de datos"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Cargar bolsillos
        cursor.execute("SELECT nombre, monto FROM bolsillos")
        bolsillos = {row["nombre"]: row["monto"] for row in cursor.fetchall()}
        
        # Cargar meta
        cursor.execute("SELECT valor FROM config WHERE clave = 'meta_total'")
        meta = int(cursor.fetchone()["valor"])
        
        # Cargar último ingreso - CORREGIDO
        cursor.execute("SELECT valor FROM config WHERE clave = 'ultimo_ingreso_mensual'")
        ultimo_valor = cursor.fetchone()
        if ultimo_valor and ultimo_valor["valor"]:
            # Convertir a float primero, luego a int
            ultimo_ingreso = int(float(ultimo_valor["valor"]))
        else:
            ultimo_ingreso = 0
        
        return {
            "bolsillos": bolsillos,
            "meta_total": meta,
            "ultimo_ingreso_mensual": ultimo_ingreso,
        }

def guardar_transaccion(tipo, monto, bolsillo=None, descripcion=None):
    """Guarda una transacción en el historial"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO transacciones (tipo, bolsillo, monto, descripcion)
            VALUES (?, ?, ?, ?)
        """, (tipo, bolsillo, monto, descripcion))
        conn.commit()

def actualizar_bolsillo(nombre, nuevo_monto):
    """Actualiza el monto de un bolsillo"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bolsillos 
            SET monto = ?, updated_at = CURRENT_TIMESTAMP
            WHERE nombre = ?
        """, (nuevo_monto, nombre))
        conn.commit()

def actualizar_config(clave, valor):
    """Actualiza un valor de configuración"""
    with get_db() as conn:
        cursor = conn.cursor()
        # Guardar como string pero asegurar formato correcto
        if isinstance(valor, (int, float)):
            valor_str = str(int(valor))  # Convertir a entero sin decimales
        else:
            valor_str = str(valor)
        
        cursor.execute("""
            UPDATE config 
            SET valor = ?, updated_at = CURRENT_TIMESTAMP
            WHERE clave = ?
        """, (valor_str, clave))
        conn.commit()

def obtener_historial(limite=50):
    """Obtiene las últimas transacciones"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM transacciones 
            ORDER BY fecha DESC 
            LIMIT ?
        """, (limite,))
        return [dict(row) for row in cursor.fetchall()]

def obtener_fondo_migratorio():
    """Calcula el fondo total (bolsillo migración + CDT)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Obtener migración
        cursor.execute("SELECT monto FROM bolsillos WHERE nombre = 'migracion'")
        migracion = cursor.fetchone()["monto"]
        
        # Obtener CDT activo (el más reciente)
        cursor.execute("""
            SELECT capital FROM cdt 
            ORDER BY fecha_inicio DESC 
            LIMIT 1
        """)
        cdt_row = cursor.fetchone()
        cdt = cdt_row["capital"] if cdt_row else 0
        
        return migracion + cdt