import pdfplumber
import json
import os
from datetime import datetime
from extractor import extraer_transacciones
from aprendizaje import CargarPatrones, GuardarPatrones, PropuestaPatron
from generador_excel import GenerarExcel


class ProcesadorCartola:
    def __init__(self, archivo_pdf):
        self.archivo_pdf = archivo_pdf
        self.patrones = CargarPatrones()
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
            propuesta_glosa = PropuestaPatron(trans['descripcion'], self.patrones, tipo='glosa')
            propuesta_cuenta = PropuestaPatron(trans['descripcion'], self.patrones, tipo='cuenta')
            
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
                    GuardarPatrones(self.patrones)
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
                    GuardarPatrones(self.patrones)
                    print("✓ Aprendizaje actualizado\n")
                    break
            
            # Agregar a salida (3 líneas por transacción)
            self.agregar_lineas_excel(trans, glosa_final, cuenta_final, idx)
    
    def agregar_lineas_excel(self, trans, glosa, cuenta_2da, num_transaccion):
        """Genera 3 líneas en el Excel por transacción"""
        fecha = trans['fecha']
        monto = trans['monto']
        
        # Línea 1: Encabezado/Resumen
        self.salida.append({
            'N': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': '',
            'C.Costo': '',
            'Análisis': '',
            'RUT': '',
            'Producto': '',
            'Glosa': glosa,
            'Debe': monto,
            'Haber': monto,
            'Inclui Libros': 1,
            'Fecha2': '',
            'Fecha3': '',
            'Flujo': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
        
        # Línea 2: Débito (Cuenta 1110100201)
        self.salida.append({
            'N': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': '1110100201',
            'C.Costo': '',
            'Análisis': trans['descripcion'].split()[0],
            'RUT': '',
            'Producto': '',
            'Glosa': glosa,
            'Debe': monto,
            'Haber': 0,
            'Inclui Libros': 1,
            'Fecha2': '',
            'Fecha3': '',
            'Flujo': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
        
        # Línea 3: Crédito (Cuenta propuesta)
        self.salida.append({
            'N': num_transaccion,
            'Fecha': fecha,
            'Tipo': 'T',
            'Cuenta': cuenta_2da,
            'C.Costo': '',
            'Análisis': trans['descripcion'].split()[0],
            'RUT': '',
            'Producto': '',
            'Glosa': glosa,
            'Debe': 0,
            'Haber': monto,
            'Inclui Libros': 1,
            'Fecha2': '',
            'Fecha3': '',
            'Flujo': '',
            'Nominal Debe': '',
            'Nominal Haber': ''
        })
    
    def generar_excel(self):
        """Genera el archivo Excel final"""
        nombre_salida = f"salida_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        GenerarExcel(self.salida, nombre_salida)
        print(f"\n✓ Excel generado: {nombre_salida}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python procesar.py <archivo_pdf>")
        sys.exit(1)
    
    archivo = sys.argv[1]
    
    if not os.path.exists(archivo):
        print(f"Error: No se encontró el archivo {archivo}")
        sys.exit(1)
    
    procesador = ProcesadorCartola(archivo)
    procesador.extraer_pdf()
    procesador.procesar_interactivo()
    procesador.generar_excel()
    
    print("\n✅ Proceso completado exitosamente!")