import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta
import os

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================
np.random.seed(42)
random.seed(42)

NUM_TRANSACCIONES = 500_000
FECHA_INICIO = pd.Timestamp('2024-01-01')
FECHA_FIN = pd.Timestamp('2025-12-31')

# ============================================================
# 1. DIMENSIÓN PRODUCTOS
# ============================================================
categorias = {
    'Tecnología': {
        'subcategorias': ['Celulares', 'Computadores', 'Tablets', 'Accesorios'],
        'banda_base': [300, 800, 400, 50],
        'banda_alto': [1200, 2000, 1000, 200]
    },
    'Electrodomésticos': {
        'subcategorias': ['Refrigeración', 'Lavado', 'Cocción', 'Climatización'],
        'banda_base': [600, 500, 400, 700],
        'banda_alto': [2000, 1500, 1200, 1800]
    },
    'Oficina': {
        'subcategorias': ['Papelería', 'Mobiliario', 'Impresión'],
        'banda_base': [5, 150, 100],
        'banda_alto': [50, 800, 500]
    },
    'Audio y Video': {
        'subcategorias': ['Televisores', 'Parlantes', 'Proyectores'],
        'banda_base': [500, 80, 400],
        'banda_alto': [3000, 500, 1500]
    },
    'Gaming': {
        'subcategorias': ['Consolas', 'Videojuegos', 'Periféricos'],
        'banda_base': [300, 40, 30],
        'banda_alto': [600, 70, 120]
    }
}

marcas_por_categoria = {
    'Tecnología': ['TechPro', 'Innova', 'SmartLife'],
    'Electrodomésticos': ['ElectroHogar', 'CoolLine', 'HomeEase'],
    'Oficina': ['OfficeLine', 'ErgoMax', 'PrintPlus'],
    'Audio y Video': ['SonicView', 'AudioMaster', 'VisionPro'],
    'Gaming': ['GameForce', 'PlaySphere', 'HyperX']
}

productos = []
id_producto = 1

for cat, info in categorias.items():
    for sub_idx, sub in enumerate(info['subcategorias']):
        marcas = marcas_por_categoria[cat]
        for marca in marcas:
            num_productos = random.randint(2, 3)
            for _ in range(num_productos):
                nombre = f"{marca} {sub} {random.choice(['Pro','Max','Lite','Plus'])}"
                precio_lista = round(random.uniform(info['banda_base'][sub_idx], info['banda_alto'][sub_idx]), 2)
                if precio_lista < 200:
                    banda = 'Bajo'
                elif precio_lista < 800:
                    banda = 'Medio'
                else:
                    banda = 'Alto'
                productos.append({
                    'id_producto': id_producto,
                    'nombre_producto': nombre,
                    'categoria': cat,
                    'subcategoria': sub,
                    'marca': marca,
                    'precio_lista': precio_lista,   # ← CORREGIDO: incluir precio de lista
                    'banda_precio': banda
                })
                id_producto += 1

dim_productos = pd.DataFrame(productos)
print(f"Productos creados: {len(dim_productos)}")

# ============================================================
# 2. DIMENSIÓN CLIENTES
# ============================================================
paises_ciudades = {
    'Colombia': ['Bogotá', 'Medellín', 'Cali', 'Barranquilla', 'Cartagena'],
    'México': ['CDMX', 'Guadalajara', 'Monterrey', 'Puebla', 'Tijuana'],
    'Perú': ['Lima', 'Arequipa', 'Trujillo', 'Cusco', 'Chiclayo'],
    'Chile': ['Santiago', 'Valparaíso', 'Concepción', 'La Serena', 'Antofagasta'],
    'Argentina': ['Buenos Aires', 'Córdoba', 'Rosario', 'Mendoza', 'La Plata']
}

segmentos = ['Consumidor', 'Corporativo', 'Pyme']
tipos_cliente = ['Nuevo', 'Recurrente', 'VIP']

clientes = []
for id_cliente in range(1, 1001):
    pais = random.choice(list(paises_ciudades.keys()))
    ciudad = random.choice(paises_ciudades[pais])
    fecha_alta = FECHA_INICIO - timedelta(days=random.randint(30, 365))
    clientes.append({
        'id_cliente': id_cliente,
        'nombre_cliente': f"Cliente {id_cliente:04d}",
        'segmento': random.choice(segmentos),
        'tipo_cliente': random.choice(tipos_cliente),
        'pais': pais,
        'ciudad': ciudad,
        'fecha_alta': fecha_alta.strftime('%Y-%m-%d')
    })

dim_clientes = pd.DataFrame(clientes)
print(f"Clientes creados: {len(dim_clientes)}")

# ============================================================
# 3. HECHOS: VENTAS (500,000+ transacciones)
# ============================================================
region_por_pais = {
    'Colombia': 'Norte',
    'México': 'Norte',
    'Perú': 'Centro',
    'Chile': 'Sur',
    'Argentina': 'Sur'
}

fechas_posibles = pd.date_range(FECHA_INICIO, FECHA_FIN, freq='D')
pesos = np.ones(len(fechas_posibles))
for i, f in enumerate(fechas_posibles):
    if f.month in [11, 12]:
        pesos[i] = 2.5
    elif f.month in [6, 7]:
        pesos[i] = 1.2
pesos = pesos / pesos.sum()

ids_venta = np.arange(1, NUM_TRANSACCIONES + 1)
fechas = np.random.choice(fechas_posibles, size=NUM_TRANSACCIONES, p=pesos)
ids_producto = np.random.choice(dim_productos['id_producto'], size=NUM_TRANSACCIONES)
ids_cliente = np.random.choice(dim_clientes['id_cliente'], size=NUM_TRANSACCIONES)
cantidades = np.random.randint(1, 8, size=NUM_TRANSACCIONES)

# Ahora sí: usar precio_lista desde el DataFrame
producto_dict = dim_productos.set_index('id_producto')['precio_lista'].to_dict()

costos_unitarios = []
descuentos_pct = []
precios_venta = []

for pid in ids_producto:
    precio_lista = producto_dict[pid]
    # Precio de venta real: variación ±10% sobre el precio de lista
    pv = precio_lista * np.random.uniform(0.9, 1.1)
    precios_venta.append(round(pv, 2))

    # Costo: entre 40% y 80% del precio de lista (margen variable por producto)
    costo = precio_lista * np.random.uniform(0.4, 0.8)
    costos_unitarios.append(round(costo, 2))

    # Descuento aplicado en esta transacción
    if np.random.random() < 0.3:
        desc = np.random.uniform(0.05, 0.4)
    else:
        desc = 0.0
    descuentos_pct.append(round(desc, 2))

precios_venta = np.array(precios_venta)
costos_unitarios = np.array(costos_unitarios)
descuentos_pct = np.array(descuentos_pct)

ingresos = cantidades * precios_venta * (1 - descuentos_pct)
costos_totales = cantidades * costos_unitarios
margen = ingresos - costos_totales
margen_pct = np.where(ingresos > 0, margen / ingresos, 0)
es_promocion = descuentos_pct > 0.15

cliente_pais_dict = dim_clientes.set_index('id_cliente')['pais'].to_dict()
cliente_ciudad_dict = dim_clientes.set_index('id_cliente')['ciudad'].to_dict()
paises = [cliente_pais_dict[cid] for cid in ids_cliente]
ciudades = [cliente_ciudad_dict[cid] for cid in ids_cliente]
regiones = [region_por_pais[p] for p in paises]

canales = np.random.choice(['Tienda Física', 'Online', 'Distribuidor'],
                           size=NUM_TRANSACCIONES, p=[0.5, 0.35, 0.15])

fact_ventas = pd.DataFrame({
    'id_venta': ids_venta,
    'fecha': fechas,
    'id_cliente': ids_cliente,
    'id_producto': ids_producto,
    'cantidad': cantidades,
    'precio_unitario': precios_venta.round(2),
    'costo_unitario': costos_unitarios.round(2),
    'descuento_pct': descuentos_pct,
    'ingreso': ingresos.round(2),
    'costo_total': costos_totales.round(2),
    'margen': margen.round(2),
    'margen_pct': margen_pct.round(4),
    'es_promocion': es_promocion,
    'pais': paises,
    'region': regiones,
    'canal': canales,
    'ciudad': ciudades
})

fact_ventas.dropna(inplace=True)
print(f"Transacciones generadas: {len(fact_ventas)}")
print(fact_ventas.head())

# ============================================================
# 4. GUARDAR CSV
# ============================================================
os.makedirs('data', exist_ok=True)

dim_productos.to_csv('data/dim_productos.csv', index=False)
dim_clientes.to_csv('data/dim_clientes.csv', index=False)
fact_ventas.to_csv('data/fact_ventas.csv', index=False)

print("\nArchivos guardados en 'data/':")
print("- dim_productos.csv")
print("- dim_clientes.csv")
print("- fact_ventas.csv")