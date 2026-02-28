import json
import os

def cargar_patrones():
    if os.path.exists('data/patrones.json'):
        with open('data/patrones.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def guardar_patrones(patrones):
    os.makedirs('data', exist_ok=True)
    with open('data/patrones.json', 'w', encoding='utf-8') as f:
        json.dump(patrones, f, ensure_ascii=False, indent=2)

def propuesta_patron(descripcion, patrones, tipo=None):
    for clave, valor in patrones.items():
        if clave.lower() in descripcion.lower():
            if isinstance(valor, dict) and tipo:
                return valor.get(tipo)
            return valor
    return None