import os
import json
import uuid
from typing import Optional, Dict

BASE_DIR = os.path.dirname(__file__)
IMAGES_DIR = os.path.join(BASE_DIR, "item_images")
MAP_PATH = os.path.join(BASE_DIR, "item_images.json")

def _ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    if not os.path.exists(MAP_PATH):
        with open(MAP_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)

def _load_map() -> Dict[str, str]:
    _ensure_dirs()
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _save_map(mapping: Dict[str, str]):
    with open(MAP_PATH, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2)

def get_item_image(item_id: int) -> Optional[str]:
    mapping = _load_map()
    path = mapping.get(str(item_id))
    return path if path and os.path.exists(path) else None

def has_item_image(item_id: int) -> bool:
    return get_item_image(item_id) is not None

def save_item_image(item_id: int, uploaded_file) -> str:
    # Streamlit UploadedFile
    _ensure_dirs()
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        ext = ".png"
    filename = f"{item_id}_{uuid.uuid4().hex}{ext}"
    dest_path = os.path.join(IMAGES_DIR, filename)
    with open(dest_path, "wb") as out:
        out.write(uploaded_file.getbuffer())

    mapping = _load_map()
    old = mapping.get(str(item_id))
    if old and os.path.exists(old) and old != dest_path:
        try:
            os.remove(old)
        except OSError:
            pass
    mapping[str(item_id)] = dest_path
    _save_map(mapping)
    return dest_path

def remove_item_image(item_id: int):
    mapping = _load_map()
    old = mapping.pop(str(item_id), None)
    if old and os.path.exists(old):
        try:
            os.remove(old)
        except OSError:
            pass
    _save_map(mapping)