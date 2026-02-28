import os
import re
from datetime import datetime

import pdfplumber


DEFAULT_YEAR = 2025


def _normalizar_numero(valor):
    if valor is None:
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    negativo = texto.startswith('-') or texto.startswith('(') and texto.endswith(')')
    texto = re.sub(r'[^0-9,.-]', '', texto)

    if not texto:
        return None

    if ',' in texto and '.' in texto:
        if texto.rfind(',') > texto.rfind('.'):
            texto = texto.replace('.', '').replace(',', '.')
        else:
            texto = texto.replace(',', '')
    elif ',' in texto:
        partes = texto.split(',')
        if len(partes) == 2 and len(partes[1]) in (1, 2):
            texto = texto.replace(',', '.')
        else:
            texto = texto.replace(',', '')

    try:
        numero = float(texto)
    except ValueError:
        return None

    if negativo and numero > 0:
        numero = -numero

    return numero


def _normalizar_fecha(fecha):
    texto = (fecha or '').strip()
    if not texto:
        return ''

    match_sin_anio = re.fullmatch(r'(\d{2})[/-](\d{2})', texto)
    if match_sin_anio:
        mes = int(match_sin_anio.group(1))
        dia = int(match_sin_anio.group(2))
        return f"{dia:02d}/{mes:02d}/{DEFAULT_YEAR}"

    match_con_anio = re.fullmatch(r'(\d{2})[/-](\d{2})[/-](\d{2,4})', texto)
    if match_con_anio:
        p1 = int(match_con_anio.group(1))
        p2 = int(match_con_anio.group(2))
        anio = int(match_con_anio.group(3))
        if anio < 100:
            anio += 2000

        if p1 > 12 and p2 <= 12:
            dia, mes = p1, p2
        else:
            mes, dia = p1, p2

        return f"{dia:02d}/{mes:02d}/{anio:04d}"

    formatos = [
        '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y',
        '%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%m-%d-%Y', '%m-%d-%y',
        '%d/%m', '%d-%m', '%m/%d', '%m-%d'
    ]

    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).strftime('%d/%m/%Y')
        except ValueError:
            continue

    return texto


def _extraer_desde_tablas(archivo_pdf):
    transacciones = []
    with pdfplumber.open(archivo_pdf) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                continue

            for table in tables:
                if not table or len(table) <= 1:
                    continue

                for row in table[1:]:
                    if not row or len(row) < 4:
                        continue

                    fecha = (row[0] or '').strip() if row[0] else ''
                    descripcion = (row[1] or '').strip() if len(row) > 1 and row[1] else ''
                    deposito = row[2] if len(row) > 2 else None
                    retiro = row[3] if len(row) > 3 else None

                    if not fecha or not descripcion:
                        continue

                    if fecha.lower() in ('date', 'fecha'):
                        continue

                    monto_deposito = _normalizar_numero(deposito)
                    monto_retiro = _normalizar_numero(retiro)

                    if monto_deposito and monto_deposito != 0:
                        monto = abs(monto_deposito)
                        tipo = 'deposito'
                    elif monto_retiro and monto_retiro != 0:
                        monto = abs(monto_retiro)
                        tipo = 'retiro'
                    else:
                        continue

                    transacciones.append({
                        'fecha': _normalizar_fecha(fecha),
                        'descripcion': descripcion,
                        'monto': monto,
                        'tipo': tipo
                    })
    return transacciones


def _extraer_desde_ocr(archivo_pdf):
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError:
        print("⚠️ OCR no disponible: instala pymupdf, pytesseract y pillow")
        return []

    tesseract_cmd = os.getenv('TESSERACT_CMD')
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    date_pattern = re.compile(r'^\s*(\d{2}[/-]\d{2}(?:[/-]\d{2,4})?|\d{4}[/-]\d{2}[/-]\d{2})\b')
    amount_pattern = re.compile(r'[-(]?\$?\d{1,3}(?:[.,]\d{3})*[.,]\d{2}\)?')

    transacciones = []

    try:
        with fitz.open(archivo_pdf) as doc:
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                image = Image.frombytes('RGB', [pix.width, pix.height], pix.samples)
                texto = pytesseract.image_to_string(image, lang='eng+spa')

                for linea in texto.splitlines():
                    linea_limpia = ' '.join(linea.split())
                    if not linea_limpia:
                        continue

                    match_fecha = date_pattern.search(linea_limpia)
                    if not match_fecha:
                        continue

                    texto_sin_fecha = linea_limpia[match_fecha.end():].strip()
                    montos_en_linea = amount_pattern.findall(texto_sin_fecha)
                    montos_normalizados = [m for m in (_normalizar_numero(x) for x in montos_en_linea) if m is not None]

                    if not montos_normalizados:
                        continue

                    fecha = _normalizar_fecha(match_fecha.group(1))

                    texto_minus = texto_sin_fecha.lower()
                    if 'beginning balance' in texto_minus or 'ending totals' in texto_minus:
                        continue

                    if len(montos_en_linea) >= 2:
                        monto_raw = montos_en_linea[0]
                    else:
                        monto_raw = montos_en_linea[-1]

                    monto = _normalizar_numero(monto_raw)
                    if monto is None or monto == 0:
                        continue

                    fin_desc = texto_sin_fecha.find(monto_raw)
                    descripcion = texto_sin_fecha[:fin_desc].strip(' -:') if fin_desc >= 0 else texto_sin_fecha
                    if not descripcion:
                        descripcion = 'Movimiento OCR'

                    transacciones.append({
                        'fecha': fecha,
                        'descripcion': descripcion,
                        'monto': abs(monto),
                        'tipo': 'retiro' if monto < 0 else 'deposito'
                    })
    except pytesseract.TesseractNotFoundError:
        print("⚠️ No se encontró Tesseract OCR. Instálalo o define TESSERACT_CMD")
        return []
    except Exception as e:
        print(f"⚠️ Error en OCR: {e}")
        return []

    return transacciones

def extraer_transacciones(archivo_pdf):
    try:
        transacciones = _extraer_desde_tablas(archivo_pdf)
        if transacciones:
            return transacciones

        print("⚠️ No se detectaron tablas con texto. Intentando OCR...")
        transacciones = _extraer_desde_ocr(archivo_pdf)
    except Exception as e:
        print(f"Error al leer PDF: {e}")
        return []

    return transacciones