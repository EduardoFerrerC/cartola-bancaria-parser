import pdfplumber
import json
import os
from datetime import datetime
from extractor import extraer_transacciones
from aprendizaje import cargar_patrones, guardar_patrones, propuesta_patron
from generador_excel import GenerarExcel


class ProcesadorCartola:
    def __init__(self, archivo_pdf):
        self.archivo_pdf = archivo_pdf
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
        """Genera 3 líneas en el Excel por transacción"""
        monto = float(trans['monto'])
        
        # Línea 1: Débito
        self.salida.append({
            'FECHA': trans['fecha'],
            'REFERENCIA': num_transaccion,
            'GLOSA': glosa,
            'DÉBITO': monto,
            'CRÉDITO': '',
            'SALDO': ''
        })
        
        # Línea 2: Cuenta 2da (Crédito)
        self.salida.append({
            'FECHA': '',
            'REFERENCIA': '',
            'GLOSA': cuenta_2da,
            'DÉBITO': '',
            'CRÉDITO': monto,
            'SALDO': ''
        })
        
        # Línea 3: Vacía
        self.salida.append({
            'FECHA': '',
            'REFERENCIA': '',
            'GLOSA': '',
            'DÉBITO': '',
            'CRÉDITO': '',
            'SALDO': ''
        })
    
    def generar_excel(self):
        """Genera archivo Excel con las transacciones procesadas"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archivo_salida = f"salida_{timestamp}.xlsx"
        GenerarExcel(self.salida, archivo_salida)
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
        print("Uso: python procesar.py <archivo_pdf>")
        return
    
    archivo_pdf = __import__('sys').argv[1]
    
    if not os.path.exists(archivo_pdf):
        print(f"❌ El archivo {archivo_pdf} no existe")
        return
    
    procesador = ProcesadorCartola(archivo_pdf)
    procesador.procesar()


if __name__ == "__main__":
    main()