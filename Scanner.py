import tkinter as tk
from tkinter import filedialog, messagebox
import os

OPERACIONES_PERMITIDAS = [
    "SUMA","RESTA","MULTIPLICACION","DIVISION","POTENCIA","RAIZ","INVERSO","MOD"
]

def es_digito(ch): 
    return '0' <= ch <= '9'

def es_espacio(ch): 
    return ch in ' \t\r\n'

def dfa_numero(cadena):
    """DFA: [+-]?[0-9]+ ('.' [0-9]+)?  -> True/False"""
    i, n = 0, len(cadena)
    if n == 0: 
        return False #cadena vacia
    if cadena[i] in "+-":
        i += 1 #siguiente posicion
        if i >= n: 
            return False #no tiene numeros
    if i >= n or not es_digito(cadena[i]): 
        return False #debe de continuar con un digito
    while i < n and es_digito(cadena[i]): 
        i += 1 #consumo todos los digitos
    if i < n and cadena[i] == '.': #decimales
        i += 1 #salta la poscion del decimal
        if i >= n or not es_digito(cadena[i]): 
            return False #debe de seguir numeros despues del decimal
        while i < n and es_digito(cadena[i]): 
            i += 1 #consume todos los decimales
    return i == n #retorna si la cadena entera es correcta

def saltar_espacios(texto, i):
    n = len(texto)
    while i < n and es_espacio(texto[i]): #verifica que sea un espacio en blanco y los salta
        i += 1
    return i

def leer_identificador(texto, i):
    n = len(texto)
    j = i
    while j < n and (texto[j].isalpha() or texto[j] == '_'): 
        j += 1
    return texto[i:j], j #retorna el identificador leido y la nueva posicion a continuar

def leer_hasta(texto, i, token):
    j = texto.find(token, i)#manda a buscar en el texto el token a partir de i
    if j == -1: #si no existe el token retorna nada y el final del texto
        return None, len(texto)
    return texto[i:j], j + len(token) #si lo cuencuentra devuelve la posicion despues del token

def resultado_de(op):
    t = op["tipo"]
    nums = op["nums"]
    if t == "SUMA" and len(nums) >= 2:
        return nums[0] + nums[1]
    if t == "RESTA" and len(nums) >= 2:
        return nums[0] - nums[1]
    if t == "MULTIPLICACION" and len(nums) >= 2:
        return nums[0] * nums[1]
    if t == "DIVISION" and len(nums) >= 2:
        return (nums[0] / nums[1]) if nums[1] != 0 else float('inf')
    if t == "POTENCIA" and len(nums) >= 2:
        return nums[0] ** nums[1]
    if t == "MOD" and len(nums) >= 2:
        return nums[0] % nums[1]
    if t == "RAIZ" and len(nums) >= 1:
        return (nums[0] ** 0.5) if nums[0] >= 0 else float('nan')
    if t == "INVERSO" and len(nums) >= 1:
        return (1.0 / nums[0]) if nums[0] != 0 else float('inf')
    return None  # insuficientes

def simbolo(t):
    return {
        "SUMA": "+",
        "RESTA": "-",
        "MULTIPLICACION": "*",
        "DIVISION": "/",
        "POTENCIA": "^",
        "MOD": "%"
    }.get(t, None)

def main():
    ruta = "entrada.txt"
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
    except Exception as e:
        print("No se pudo leer:", e); return

    i, n = 0, len(texto)
    errores = []
    pila_ops = []   # cada item: {"tipo":..., "nums":[], "tiene_subop":False}
    historico = []  # para imprimir en el orden de cierre

    while i < n:
        i = saltar_espacios(texto, i)
        if i >= n: break

        # <Operacion= OP>
        if texto.startswith("<Operacion", i):
            i += len("<Operacion")
            i = saltar_espacios(texto, i)
            if i >= n or texto[i] != '=':
                errores.append(("Falta '=' en <Operacion= ... >", i)); break
            i += 1
            i = saltar_espacios(texto, i)
            op, i = leer_identificador(texto, i)
            if op not in OPERACIONES_PERMITIDAS:
                errores.append((f"Operación desconocida '{op}'", i))
            i = saltar_espacios(texto, i)
            if i >= n or texto[i] != '>':
                errores.append(("Falta '>' en <Operacion= ... >", i)); break
            i += 1
            pila_ops.append({"tipo": op, "nums": [], "tiene_subop": False})
            continue

        # </Operacion>
        if texto.startswith("</Operacion>", i):
            if not pila_ops:
                errores.append(("Cierre </Operacion> inesperado", i))
                i += len("</Operacion>")
                continue
            actual = pila_ops.pop()
            tipo = actual["tipo"]
            nums = actual["nums"]
            res = resultado_de(actual)   # <<< FIX
            historico.append({"tipo": tipo, "nums": nums[:], "res": res, "compleja": actual["tiene_subop"]})
            if pila_ops:
                pila_ops[-1]["nums"].append(res if res is not None else 0.0)
                pila_ops[-1]["tiene_subop"] = True
            i += len("</Operacion>")
            continue

        # <Numero> ... </Numero>
        if texto.startswith("<Numero>", i):
            i += len("<Numero>")
            contenido, i2 = leer_hasta(texto, i, "</Numero>")
            if contenido is None:
                errores.append(("Falta </Numero>", i)); break
            numtxt = contenido.strip()
            if not dfa_numero(numtxt):
                errores.append((f"Número mal formado '{numtxt}'", i))
            else:
                if not pila_ops:
                    errores.append(("Número fuera de una <Operacion>", i))
                else:
                    pila_ops[-1]["nums"].append(float(numtxt))
            i = i2
            continue

        # cualquier otro carácter: avanzar
        i += 1

    if pila_ops:
        errores.append(("Etiqueta(s) sin cerrar: Operacion", n))

    # --------- Impresión (en orden de cierre) ----------
    print("Operaciones\n")
    contador_por_tipo = {}
    etiqueta_legible = {
        "SUMA":"Suma","RESTA":"Resta","MULTIPLICACION":"Multiplicacion",
        "DIVISION":"Division","POTENCIA":"Potencia","RAIZ":"Raiz",
        "INVERSO":"Inverso","MOD":"Mod"
    }

    for op in historico:
        tipo, nums, res, es_compleja = op["tipo"], op["nums"], op["res"], op["compleja"]
        contador_por_tipo[tipo] = contador_por_tipo.get(tipo, 0) + 1
        idx = contador_por_tipo[tipo]
        suf = " (compleja)" if es_compleja else ""
        print(f"Operación {etiqueta_legible.get(tipo,tipo)} {idx}{suf}")

        simb = simbolo(tipo)
        if simb and len(nums) >= 2:
            print(f"{nums[0]}{simb}{nums[1]} = {round(res,2)}\n")
        elif tipo == "RAIZ" and len(nums) >= 1:
            print(f"√({nums[0]}) = {round(res,2)}\n")
        elif tipo == "INVERSO" and len(nums) >= 1:
            print(f"1/({nums[0]}) = {round(res,2)}\n")
        else:
            print("(operadores insuficientes)\n")

    if errores:
        print("ERRORES:")
        for msg, pos in errores:
            print(f"- {msg} (pos {pos})")


#interfaz grafica
class interfazGrafica:
#ventana inicial, iniciación de los botones y área de texto
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Analizador de Operaciones Aritméticas")
        self.ventana.geometry("620x600")
        self.ventana.config(bg="#C4CDD2")

        self.archivoActual = None
        self.botones()
        self.Texto()
#área de texto
    def Texto(self):
        self.texto = tk.Text(self.ventana, wrap=tk.WORD, width=60, height=25)
        self.texto.grid(row=1, column=0, columnspan=10, padx=10, pady=10, sticky="nswe")
        
#botones que ejecutan cada una de las 7 acciones. 
    def botones(self):
        self.boton1 = tk.Button(self.ventana, text="Abrir", command=self.abrirArchivo)
        self.boton1.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=16)
        self.boton1.grid(row=0, column=0, padx=10, pady=10)
        
        self.boton2 = tk.Button(self.ventana, text="Guardar", command=self.guardarArchivo)
        self.boton2.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=16)
        self.boton2.grid(row=0, column=1, padx=10, pady=10)

        self.boton3 = tk.Button(self.ventana, text="Guardar como", command=self.guardarComoArchivo)
        self.boton3.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=16)
        self.boton3.grid(row=0, column=2, padx=10, pady=10)

        self.boton4 = tk.Button(self.ventana, text="Analizar", command=self.analizar)
        self.boton4.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=16)
        self.boton4.grid(row=0, column=3, padx=10, pady=10)

        self.boton5 = tk.Button(self.ventana, text="Manual de usuario", command=self.manualUsuario)
        self.boton5.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=18)
        self.boton5.grid(row=2, column=2, padx=10, pady=10)

        self.boton6 = tk.Button(self.ventana, text="Manual técnico", command= self.manualTecnico)
        self.boton6.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=18)
        self.boton6.grid(row=2, column=1, padx=10, pady=10)

        self.boton7 = tk.Button(self.ventana, text="Ayuda", command=self.ayuda)
        self.boton7.config(bg='#FFFFFF', fg="black",borderwidth=2, relief="raised",width=18)
        self.boton7.grid(row=2, column=0, padx=10, pady=10)

#permite abrir un archivo de texto en formato txt
    def abrirArchivo(self):
        try:
            filepath = filedialog.askopenfilename(
                title="Seleccionar archivo",
                filetypes=[("Archivos de texto", "*.txt"), ("Todos los archivos", "*.*")]
            )
            
            if filepath:
                with open(filepath, 'r', encoding='utf-8') as file:
                    contenido = file.read()
                self.texto.delete(1.0, tk.END)
                self.texto.insert(1.0, contenido)
                self.archivoActual = filepath

                messagebox.showinfo("Éxito", f"Se ha cargado el archivo: {os.path.basename(filepath)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el archivo: {str(e)}")

#abre el manual de usuario de forma externa 
    def manualUsuario(self):
        try:
            nombre = "Manual de usuario_proyecto2.pdf"
            if os.path.exists(nombre):
                os.startfile(nombre) 
            else:
                messagebox.showwarning("Error: no se encontró el manual de usuario", 
                                      f"Verificar si el archivo se encuentra en la misma carpeta del programa o si es de nombre: {nombre}"
                                      )     
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el manual de usuario:{str(e)}")

#abre el manual técnico de forma externa 
    def manualTecnico(self):
        try:
            nombre = "Manual técnico_proyecto2.pdf"
            if os.path.exists(nombre):
                os.startfile(nombre) 
            else:
                messagebox.showwarning("Error: no se encontró el manual técnico", 
                                      f"Verificar si el archivo se encuentra en la misma carpeta del programa o si es de nombre: {nombre}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el manual técnico:{str(e)}")

#guardar lo que está escrito en el área de texto con un nombre diferente a la entrada
    def guardarComoArchivo(self):
        try:
            contenido = self.texto.get(1.0, tk.END)
            filepath = filedialog.asksaveasfilename(
                title="Guardar como",
                defaultextension=".txt",
                filetypes=[("Archivos de texto txt", "*.txt"), ("Todos los archivos", "*.*")]
            )  
            if filepath:
                with open(filepath, "w", encoding="utf-8") as archivo:
                    archivo.write(contenido)
                self.archivoActual = filepath

                messagebox.showinfo("Éxito", f"El archivo se guardó como: {os.path.basename(filepath)}")
                
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")

#guardar lo que está escrito en el área de texto sobreescribieno el archivo de entrada  
    def guardarArchivo(self):
        try:
            contenido = self.texto.get(1.0, tk.END)
            if not hasattr(self, 'archivoActual') or not self.archivoActual:
                messagebox.showwarning("Advertencia", "No hay un archivo abierto que se pueda guardar\n" "Primero usar guardar cómo")
                return
            with open(self.archivoActual, "w", encoding="utf-8") as archivo:
                archivo.write(contenido)
            
            messagebox.showinfo("Éxito", f"Archivo guardado: {os.path.basename(self.archivoActual)}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el archivo: {str(e)}")

#sección correspondiente al botón de analizar. Se procesa el texto usando información del main(), se crean los archivos html de resultado y errores junto con el diagrama de operaciones svg creado con xml
    def analizar(self):
        texto = self.texto.get("1.0", tk.END)
        
        if not texto.strip():
            messagebox.showwarning("Advertencia", "No se ha cargado un archivo en el área de texto")
            return
        try:
            resultado = self.procesarTexto(texto)        
            self.crearHTML(resultado)
            self.crearDiagramaSVG(resultado)
            messagebox.showinfo("Analizar completado", 
                               "El análisis se completó exitosamente\n"
                               "Archivos generados:\n"
                               "Resultados.html\n"
                               "Errores.html\n"
                               "diagramaOperaciones.svg")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al analizar: {str(e)}")

    def procesarTexto(self, texto):
        i, n = 0, len(texto)
        errores = []
        pilaOps = []
        historico = []
        contador_global = 0

        while i < n:
            i = saltar_espacios(texto, i)
            if i >= n: 
                break
            if texto.startswith("<Operacion", i):
                i += len("<Operacion")
                i = saltar_espacios(texto, i)
                if i >= n or texto[i] != '=':
                    errores.append(("Error", i, '='))
                    break
                i += 1
                i = saltar_espacios(texto, i)
                op, i = leer_identificador(texto, i)
                if op not in OPERACIONES_PERMITIDAS:
                    errores.append(("Error", i, op))
                i = saltar_espacios(texto, i)
                if i >= n or texto[i] != '>':
                    errores.append(("Error", i, '>'))
                    break
                i += 1
                contador_global += 1
                pilaOps.append({
                    "tipo": op, 
                    "nums": [], 
                    "tieneSubop": False,
                    "id": contador_global
                })
                continue

            if texto.startswith("</Operacion>", i):
                if not pilaOps:
                    errores.append(("Error", i, "</Operacion>"))
                    i += len("</Operacion>")
                    continue
                actual = pilaOps.pop()
                tipo = actual["tipo"]
                nums = actual["nums"]
                res = resultado_de(actual)
                historico.append({
                    "tipo": tipo, 
                    "nums": nums[:], 
                    "res": res, 
                    "compleja": actual["tieneSubop"],
                    "id": actual["id"]
                })
                if pilaOps:
                    pilaOps[-1]["nums"].append(res if res is not None else 0.0)
                    pilaOps[-1]["tieneSubop"] = True
                i += len("</Operacion>")
                continue

            if texto.startswith("<Numero>", i):
                i += len("<Numero>")
                contenido, i2 = leer_hasta(texto, i, "</Numero>")
                if contenido is None:
                    errores.append(("Error", i, "</Numero>"))
                    break
                numtxt = contenido.strip()
                if not dfa_numero(numtxt):
                    errores.append(("Error", i, numtxt))
                else:
                    if not pilaOps:
                        errores.append(("Error", i, "<Numero>"))
                    else:
                        pilaOps[-1]["nums"].append(float(numtxt))
                i = i2
                continue

            i += 1

        if pilaOps:
            errores.append(("Error", n, "Operacion"))

        return {
            "historico": historico,
            "errores": errores,
            "textoOriginal": texto
        }


    def crearDiagramaSVG(self, resultado):
        if "historico" not in resultado or not resultado["historico"]:
            return
        
        operaciones = resultado["historico"]
        ancho = 800
        alto = len(operaciones) * 100 + 100
        margen = 50
        
        svgDiagrama = f'''<?xml version="1.0" encoding="UTF-8"?>
        <svg width="{ancho}" height="{alto}" xmlns="http://www.w3.org/2000/svg">
        <rect width="100%" height="100%" fill="white"/>
        <text x="{ancho//2}" y="30" font-family="Arial" font-size="16" font-weight="bold" text-anchor="middle">Diagrama de jerarquía de operaciones</text>'''
        y_actual = margen + 50
        
        for i, op in enumerate(operaciones):
            tipo = op["tipo"]
            nums = op["nums"]
            res = op["res"]
            es_compleja = op["compleja"]
            x_principal = ancho // 2
            ancho_rect = 80
            alto_rect = 40    
            svgDiagrama += f'<rect x="{x_principal - ancho_rect//2}" y="{y_actual - alto_rect//2}" width="{ancho_rect}" height="{alto_rect}" fill="none" stroke="black" stroke-width="1"/>\n'

            abreviaciones = {
                "SUMA": "+", "RESTA": "-", "MULTIPLICACION": "×", 
                "DIVISION": "÷", "POTENCIA": "^", "RAIZ": "√", 
                "INVERSO": "1/x", "MOD": "%"
            }
            texto_op = abreviaciones.get(tipo, tipo[:4])
            svgDiagrama += f'<text x="{x_principal}" y="{y_actual + 5}" font-family="Arial" font-size="12" text-anchor="middle">{texto_op}</text>\n'

            if res is not None and res == res and abs(res) != float('inf'):
                resultado_texto = f"= {res:.2f}"
                svgDiagrama += f'<text x="{x_principal}" y="{y_actual + 15}" font-family="Arial" font-size="10" text-anchor="middle">{resultado_texto}</text>\n'

            if len(nums) >= 1:
                espacio_operandos = 120
                
                for j, num in enumerate(nums):
                    if j >= 2:
                        break
                        
                    x_operando = x_principal - espacio_operandos + (j *2 * espacio_operandos)
                    y_operando = y_actual + 40

                    svgDiagrama += f'<line x1="{x_principal}" y1="{y_actual + alto_rect//2}" x2="{x_operando}" y2="{y_operando - 10}" stroke="black" stroke-width="1"/>\n'
                    svgDiagrama += f'<rect x="{x_operando - 25}" y="{y_operando}" width="50" height="20" fill="none" stroke="black" stroke-width="1"/>\n'
                    svgDiagrama += f'<text x="{x_operando}" y="{y_operando + 14}" font-family="Arial" font-size="10" text-anchor="middle">{num}</text>\n'

            if es_compleja:
                svgDiagrama += f'<text x="{x_principal + 45}" y="{y_actual - 10}" font-family="Arial" font-size="16" fill="black">(compleja)</text>\n'
            y_actual += 100
        svgDiagrama += '</svg>'

        with open("diagramaOperaciones.svg", "w", encoding="utf-8") as archivo:
            archivo.write(svgDiagrama)

    def crearHTML(self, resultado):
        with open("Resultados.html", "w", encoding="utf-8") as archivo:
            archivo.write("<html><body>\n")
            archivo.write("<h1>Resultados del Analizador de Operaciones Aritméticas</h1>\n")
            
            if "historico" in resultado and resultado["historico"]:
                contadorPorTipo = {}
                etiquetaLegible = {
                    "SUMA": "Suma", "RESTA": "Resta", "MULTIPLICACION": "Multiplicación",
                    "DIVISION": "División", "POTENCIA": "Potencia", "RAIZ": "Raíz",
                    "INVERSO": "Inverso", "MOD": "Módulo"
                }

                for op in resultado["historico"]:
                    tipo, nums, res, esCompleja = op["tipo"], op["nums"], op["res"], op["compleja"]
                    contadorPorTipo[tipo] = contadorPorTipo.get(tipo, 0) + 1
                    idx = contadorPorTipo[tipo]
                    
                    suf = " (compleja)" if esCompleja else ""
                    archivo.write(f"<h3>Operación {etiquetaLegible.get(tipo,tipo)} {idx}{suf}</h3>\n")
                    
                    simb = simbolo(tipo)
                    if simb and len(nums) >= 2:
                        archivo.write(f"<p>{nums[0]} {simb} {nums[1]} = {round(res,2) if res is not None else 'ERROR'}</p>\n")
                    elif tipo == "RAIZ" and len(nums) >= 1:
                        archivo.write(f"<p>√({nums[0]}) = {round(res,2) if res is not None else 'ERROR'}</p>\n")
                    elif tipo == "INVERSO" and len(nums) >= 1:
                        archivo.write(f"<p>1/({nums[0]}) = {round(res,2) if res is not None else 'ERROR'}</p>\n")
                    else:
                        archivo.write("<p>Ha ocurrido un error en el analisis, revisar html de errores</p>\n")
                    archivo.write("<br>\n")
            else:
                archivo.write('<p>No se cumplio con el formato de las operaciones aritméticas. Cargar un archivo o copiar el formato</p>\n')
            
            archivo.write("</body></html>")
        with open("Errores.html", "w", encoding="utf-8") as archivo:
            archivo.write("<html><body>\n")
            archivo.write("<h1>Reporte de errores léxicos</h1>\n")
            
            if "errores" in resultado and resultado["errores"]:
                archivo.write("<table border='1'>\n")
                archivo.write("<tr><th>No.</th><th>Lexema</th><th>Tipo</th><th>COLUMNA</th><th>FILA</th></tr>\n")
                
                for idx, (tipo, pos, lexema) in enumerate(resultado["errores"], 1):
                    texto_hasta_error = resultado["textoOriginal"][:pos]
                    lineas = texto_hasta_error.split('\n')
                    fila = len(lineas)
                    columna = len(lineas[-1]) + 1 if lineas else pos + 1
                    
                    archivo.write(f"<tr><td>{idx}</td><td>{lexema}</td><td>{tipo}</td><td>{columna}</td><td>{fila}</td></tr>\n")
                
                archivo.write("</table>\n")
            else:
                archivo.write('<p>No se encontraron errores léxicos.</p>\n')
            
            archivo.write("</body></html>")

#muestra los datos de los desarrolladores
    def ayuda(self):
        messagebox.showinfo("Datos de los desarrolladores", 
                            "Curso: Lenguajes Formales y Automatas\n" 
                            "sección: 02\n" "-----------------estudiantes-----------------\n" 
                            "González Pérez, Pablo Javier - 1211624\n" 
                            "Miranda Abrego, Andrea Sofía - 1065824\n")
        
#ejecuta como tal la ventana, permite que la ventana siga en ejecución 
    def ejecutar(self):
        self.ventana.mainloop()

if __name__ == "__main__":
    main()

app = interfazGrafica()
app.ejecutar()

