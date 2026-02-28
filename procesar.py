import pdfplumber
import json
import os
from datetime import datetime
from extractor import extraer_transacciones
from aprendizaje import cargar_patrones, guardar_patrones, propuesta_patron
from generador_excel import generate_excel


class ProcesadorCartola:
    def __init__(self, archivo_pdf, archivo_salida=None, archivo_referencia=None):
        self.archivo_pdf = archivo_pdf
        self.archivo_salida = archivo_salida
        self.archivo_referencia = archivo_referencia
        self.patrones = cargar_patrones()
        self.transacciones = []
        self.salida = []
    
    def extraer_pdf(self):
        """Extrae transacciones del PDF"""
        print(f"\n📄 Leyendo PDF: {self.archivo_pdf}")
        self.transacciones = extraer_transacciones(self.archivo_pdf)
        print(f"✓ Se encontraron {len(self.transacciones)} transacciones\n")
    
    def procesar_interactivo(self):
        """Procesa cada transacción con propuestas interactivas"""
        for idx, trans in enumerate(self.transacciones, 1):
            print(f"\n{'='*60}")
            print(f"Transacción {idx}/{len(self.transacciones)}")
            print(f"{'='*60}")
            print(f"Fecha: {trans['fecha']}")
            print(f"Monto: ${trans['monto']:,.2f}")
            print(f"Descripción: {trans['descripcion']}\n")
            
            # Proponer Glosa y Cuenta
            propuesta_glosa = propuesta_patron(trans['descripcion'], self.patrones, tipo='glosa')
            propuesta_cuenta = propuesta_patron(trans['descripcion'], self.patrones, tipo='cuenta')
            
            print(f"Propuesta:")
            print(f"  📝 Glosa: {propuesta_glosa}")
            print(f"  💳 Cuenta (2da): {propuesta_cuenta}\n")
            
            # Confirmación del usuario
            while True:
                respuesta = input("¿Confirmar? (s=sí, n=no, e=editar): ").strip().lower()
                
                if respuesta == 's':
                    glosa_final = propuesta_glosa
                    cuenta_final = propuesta_cuenta
                    print("✓ Confirmado\n")
                    break
                
                elif respuesta == 'e':
                    glosa_final = input("  Nueva Glosa: ").strip()
                    cuenta_final = input("  Nueva Cuenta: ").strip()
                    
                    # Guardar aprendizaje
                    self.patrones[trans['descripcion']] = {
                        'glosa': glosa_final,
                        'cuenta': cuenta_final
                    }
                    guardar_patrones(self.patrones)
                    print("✓ Cambios guardados y patrón aprendido\n")
                    break
                
                elif respuesta == 'n':
                    glosa_final = input("  Ingresa Glosa correcta: ").strip()
                    cuenta_final = input("  Ingresa Cuenta correcta: ").strip()
                    
                    # Guardar aprendizaje
                    self.patrones[trans['descripcion']] = {
                        'glosa': glosa_final,
                        'cuenta': cuenta_final
                    }
                    guardar_patrones(self.patrones)
                    print("✓ Aprendizaje actualizado\n")
                    break
            
            # Agregar a salida (3 líneas por transacción)
            self.agregar_lineas_excel(trans, glosa_final, cuenta_final, idx)
    
    def agregar_lineas_excel(self, trans, glosa, cuenta_2da, num_transaccion):
        """Genera 3 líneas contables por transacción"""
        monto = float(trans['monto'])
        fecha = trans['fecha']
        descripcion = (trans['descripcion'] or '').upper()
        analisis = descripcion.split()[0] if descripcion else ''

        cuenta_banco = '1110100201'
        cuenta_contraparte = str(cuenta_2da).strip() if cuenta_2da else '1110700100'
        glosa_encabezado = glosa if glosa else 'Glosa Enc'

        debito_banco = monto if trans.get('tipo') == 'deposito' else 0
        credito_banco = monto if trans.get('tipo') == 'retiro' else 0
        debito_contraparte = credito_banco
        credito_contraparte = debito_banco
        
        # Línea 1: Encabezado comprobante
        self.salida.append({
            'N Comprob': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': '',
            'C.Costo': '',
            'Análisis': '',
            'RUT': '',
            'Producto': '',
            'Glosa': glosa_encabezado,
            'Debe': monto,
            'Haber': monto,
            'Incluir Libros': '1',
            'Fecha Emis.': '',
            'Fecha Vcto.': '',
            'Flujo Efect.': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
        
        # Línea 2: Cuenta banco
        self.salida.append({
            'N Comprob': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': cuenta_banco,
            'C.Costo': '',
            'Análisis': analisis,
            'RUT': '',
            'Producto': '',
            'Glosa': descripcion,
            'Debe': debito_banco,
            'Haber': credito_banco,
            'Incluir Libros': '1',
            'Fecha Emis.': '',
            'Fecha Vcto.': '',
            'Flujo Efect.': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
        
        # Línea 3: Cuenta contraparte
        self.salida.append({
            'N Comprob': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': cuenta_contraparte,
            'C.Costo': '',
            'Análisis': analisis,
            'RUT': '',
            'Producto': '',
            'Glosa': descripcion,
            'Debe': debito_contraparte,
            'Haber': credito_contraparte,
            'Incluir Libros': '1',
            'Fecha Emis.': '',
            'Fecha Vcto.': '',
            'Flujo Efect.': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
    
    def generar_excel(self):
        """Genera archivo Excel con las transacciones procesadas"""
        if self.archivo_salida:
            archivo_salida = self.archivo_salida
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_salida = f"salida_{timestamp}.xlsx"

        base, ext = os.path.splitext(archivo_salida)
        if ext.lower() == '.xls':
            archivo_salida = f"{base}.xlsx"
            print(f"⚠️ El formato .xls no está soportado en esta configuración. Se usará: {archivo_salida}")

        carpeta_salida = os.path.dirname(archivo_salida)
        if carpeta_salida:
            os.makedirs(carpeta_salida, exist_ok=True)

        generate_excel(self.salida, archivo_salida, template_path=self.archivo_referencia)
        print(f"\n✓ Excel generado: {archivo_salida}")
        return archivo_salida
    
    def procesar(self):
        """Flujo completo de procesamiento"""
        self.extraer_pdf()
        if not self.transacciones:
            print("❌ No se encontraron transacciones")
            return
        self.procesar_interactivo()
        self.generar_excel()
        print("✓ Proceso completado!")


def main():
    if len(__import__('sys').argv) < 2:
        print("Uso: python procesar.py <archivo_pdf> [archivo_excel_salida] [archivo_excel_referencia]")
        return
    
    archivo_pdf = __import__('sys').argv[1]
    archivo_salida = __import__('sys').argv[2] if len(__import__('sys').argv) >= 3 else None
    archivo_referencia = __import__('sys').argv[3] if len(__import__('sys').argv) >= 4 else None
    
    if not os.path.exists(archivo_pdf):
        print(f"❌ El archivo {archivo_pdf} no existe")
        return
    
    procesador = ProcesadorCartola(
        archivo_pdf,
        archivo_salida=archivo_salida,
        archivo_referencia=archivo_referencia
    )
    procesador.procesar()


if __name__ == "__main__":
    main()