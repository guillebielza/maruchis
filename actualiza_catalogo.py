import os
import io
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from PIL import Image
import pillow_heif
import shutil

# === 1. Autenticación con Service Account ===
import json
credentials_json = os.environ['GDRIVE_CREDENTIALS']
with open('credentials.json', 'w') as f:
    f.write(credentials_json)

gauth = GoogleAuth()
gauth.LoadServiceConfigFile('credentials.json')
drive = GoogleDrive(gauth)

# === 2. Obtener carpeta "web" ===
web_folder = drive.ListFile({
    'q': "title='web' and mimeType='application/vnd.google-apps.folder' and trashed=false"
}).GetList()[0]
web_id = web_folder['id']

# === 3. Obtener archivo catalogo.xlsx ===
catalog_file = drive.ListFile({
    'q': f"'{web_id}' in parents and title = 'catalogo.xlsx' and trashed=false"
}).GetList()
if catalog_file:
    file = catalog_file[0]
    file.GetContentFile("catalogo.xlsx")

# === 4. Obtener carpeta "fotos" dentro de web ===
photos_folder = drive.ListFile({
    'q': f"'{web_id}' in parents and title='fotos' and mimeType='application/vnd.google-apps.folder' and trashed=false"
}).GetList()[0]
photos_id = photos_folder['id']

# === 5. Crear carpeta local si no existe ===
os.makedirs('fotos', exist_ok=True)

# === 6. Procesar imágenes ===
images = drive.ListFile({'q': f"'{photos_id}' in parents and trashed=false"}).GetList()

for img in images:
    file_ext = os.path.splitext(img['title'])[1].lower()
    base_name = os.path.splitext(img['title'])[0]
    dest_path = f"fotos/{base_name}.jpg"

    if os.path.exists(dest_path):
        print(f"{dest_path} ya existe, omitido.")
        continue

    print(f"Procesando: {img['title']}")
    # Descargar archivo temporal
    img.GetContentFile("temp_image" + file_ext)

    try:
        if file_ext == ".heic":
            heif_file = pillow_heif.read_heif("temp_image" + file_ext)
            image = Image.frombytes(
                heif_file.mode, heif_file.size, heif_file.data, "raw"
            )
        else:
            image = Image.open("temp_image" + file_ext)

        # Convertir y guardar en JPG comprimido
        image = image.convert("RGB")
        image.save(dest_path, "JPEG", quality=70)

    except Exception as e:
        print(f"Error al procesar {img['title']}: {e}")
    finally:
        os.remove("temp_image" + file_ext)
