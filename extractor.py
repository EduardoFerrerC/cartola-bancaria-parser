import pdfplumber

def extraer_transacciones(archivo_pdf):
    transacciones = []
    try:
        with pdfplumber.open(archivo_pdf) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table and len(table) > 2:
                            for row in table[1:]:
                                if row and len(row) >= 5:
                                    fecha = row[0]
                                    descripcion = row[1]
                                    depositos = row[2] if row[2] else 0
                                    retiros = row[3] if row[3] else 0
                                    if fecha and descripcion and fecha != 'Date':
                                        try:
                                            monto = float(str(depositos).replace(',', '')) if depositos else 0
                                            if monto == 0:
                                                monto = float(str(retiros).replace(',', '')) if retiros else 0
                                            if monto > 0:
                                                transacciones.append({
                                                    'fecha': fecha,
                                                    'descripcion': descripcion.strip(),
                                                    'monto': monto,
                                                    'tipo': 'deposito' if depositos else 'retiro'
                                                })
                                        except (ValueError, AttributeError):
                                            pass
    except Exception as e:
        print(f"Error al leer PDF: {e}")
    return transacciones