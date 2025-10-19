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


if __name__ == "__main__":
    main()