import os
import io
import json
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PIL import Image
from pillow_heif import register_heif_opener

# Inicializar soporte HEIC
def init_image_formats():
    try:
        register_heif_opener()
    except Exception as e:
        print("Error al registrar soporte HEIC:", e)

# Autenticación con cuenta de servicio
def authenticate():
    credentials_info = json.loads(os.environ['GDRIVE_CREDENTIALS'])
    credentials = service_account.Credentials.from_service_account_info(
        credentials_info,
        scopes=['https://www.googleapis.com/auth/drive.readonly']
    )
    return build('drive', 'v3', credentials=credentials)

# Buscar ID de una carpeta por nombre y padre
def get_folder_id(service, folder_name, parent_id=None):
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
    if parent_id:
        query += f" and '{parent_id}' in parents"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    return files[0]['id'] if files else None

# Descargar archivo y guardarlo localmente
def download_file(service, file_id, filename):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    fh.seek(0)
    with open(filename, 'wb') as f:
        f.write(fh.read())

# Obtener archivos dentro de una carpeta
def list_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name, mimeType)').execute()
    return results.get('files', [])

# Convertir imagen a JPG si no existe ya
def convert_and_save_image(input_path, output_path):
    try:
        with Image.open(input_path) as img:
            rgb = img.convert('RGB')
            rgb.save(output_path, 'JPEG', quality=85)
    except Exception as e:
        print(f"Error convirtiendo {input_path}: {e}")

# Script principal
def main():
    init_image_formats()
    service = authenticate()

    # Buscar carpeta "web" y dentro de ella "fotos"
    web_id = get_folder_id(service, 'web')
    if not web_id:
        print("No se encontró la carpeta 'web'")
        return

    fotos_id = get_folder_id(service, 'fotos', web_id)
    if not fotos_id:
        print("No se encontró la carpeta 'fotos' dentro de 'web'")
        return

    # Crear carpeta local si no existe
    Path("fotos").mkdir(exist_ok=True)

    # Descargar imágenes y convertirlas si no existen
    for file in list_files_in_folder(service, fotos_id):
        name, ext = os.path.splitext(file['name'])
        local_jpg_path = f"fotos/{name}.jpg"
        if os.path.exists(local_jpg_path):
            continue
        temp_path = f"temp/{file['name']}"
        Path("temp").mkdir(exist_ok=True)
        download_file(service, file['id'], temp_path)
        convert_and_save_image(temp_path, local_jpg_path)
        os.remove(temp_path)

    # Descargar el archivo catalogo.xlsx
    catalog_file = next((f for f in list_files_in_folder(service, web_id) if f['name'] == 'catalogo.xlsx'), None)
    if catalog_file:
        download_file(service, catalog_file['id'], 'catalogo.xlsx')
        print("Descargado catalogo.xlsx")
    else:
        print("No se encontró catalogo.xlsx")

if __name__ == '__main__':
    main()
