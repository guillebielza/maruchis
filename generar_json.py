import pandas as pd
import json

# Leer el archivo Excel
df = pd.read_excel("catalogo.xlsx")

# Crear la lista de productos
productos = []
for _, row in df.iterrows():
    imagenes = [row[col] for col in df.columns if col.startswith("imagen") and pd.notna(row[col])]
    productos.append({
        "nombre": row["nombre"],
        "precio": row["precio"],
        "imagenes": imagenes
    })

# Guardar como archivo JSON
with open("productos.json", "w", encoding="utf-8") as f:
    json.dump(productos, f, indent=2, ensure_ascii=False)

print("✅ productos.json generado con éxito.")
