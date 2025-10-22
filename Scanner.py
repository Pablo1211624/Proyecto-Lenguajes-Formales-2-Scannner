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
    exp = op.get("exp")
    raiz_n = op.get("raiz_n")
    if t == "SUMA":
        return sum(nums) if nums else None
    if t == "RESTA":
        if not nums: return None
        return nums[0] - sum(nums[1:]) if len(nums) > 1 else nums[0]
    if t == "MULTIPLICACION":
        if not nums: return None
        acc = 1.0
        for x in nums: acc *= x
        return acc
    if t == "DIVISION":
        if not nums: return None
        if len(nums) == 1: return float('inf') if nums[0] == 0 else nums[0]
        acc = nums[0]
        for x in nums[1:]:
            if x == 0: return float('inf')
            acc /= x
        return acc
    if t == "MOD":
        if len(nums) < 2: return None
        acc = nums[0]
        for x in nums[1:]:
            try:
                acc = acc % x
            except ZeroDivisionError:
                return float('inf')
        return acc
    if t == "POTENCIA":
        if exp is not None:
            if not nums: return None   # falta base
            return nums[0] ** exp
        if len(nums) == 2:
            return nums[0] ** nums[1]
        return None
    if t == "RAIZ":
        if not nums: return None  # falta radicando
        n = raiz_n if raiz_n is not None else 2.0  # por defecto raíz cuadrada
        x = nums[0]
        try:
            # Si n es par y x<0 → NaN
            if n % 2 == 0 and x < 0:
                return float('nan')
            return x ** (1.0 / n)
        except Exception:
            return float('nan')
    if t == "INVERSO":
        if not nums: return None
        return (1.0 / nums[0]) if nums[0] != 0 else float('inf')
    return None

def simbolo(t):
    return {
        "SUMA": "+",
        "RESTA": "-",
        "MULTIPLICACION": "*",
        "DIVISION": "/",
        "POTENCIA": "^",
        "MOD": "%"
    }.get(t)

def main():
    ruta = "Entrada1.txt"
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            texto = f.read()
    except Exception as e:
        print("No se pudo leer:", e); return

    i, n = 0, len(texto)
    errores = []
    pila_ops = []   # cada operacion
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
            pila_ops.append({"tipo": op, "nums": [], "tiene_subop": False, "exp": None, "raiz_n": None})
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
            res = resultado_de(actual) 
            historico.append({"tipo": tipo, "nums": nums[:], "res": res, "compleja": actual["tiene_subop"], "exp": actual.get("exp"),"raiz_n": actual.get("raiz_n")})
            if pila_ops:
                pila_ops[-1]["nums"].append(res if res is not None else 0.0)
                pila_ops[-1]["tiene_subop"] = True
            i += len("</Operacion>")
            continue

        if texto.startswith("<P>", i):
            i += len("<P>")
            contenido, i2 = leer_hasta(texto, i, "</P>")
            if contenido is None:
                errores.append(("Falta </P>", i))
                break
            val = contenido.strip()
            if not dfa_numero(val):
                errores.append((f"Exponente <P> no es número válido: '{val}'", i))
            else:
                if not pila_ops:
                    errores.append(("Etiqueta <P> fuera de una <Operacion>", i))
                else:
                    pila_ops[-1]["exp"] = float(val)
            i = i2
            continue

        if texto.startswith("<R>", i):
            i += len("<R>")
            contenido, i2 = leer_hasta(texto, i, "</R>")
            if contenido is None:
                errores.append(("Falta </R>", i)); break
            val = contenido.strip()
            if not dfa_numero(val):
                errores.append((f"Índice de raíz <R> no es número válido: '{val}'", i))
            else:
                if not pila_ops:
                    errores.append(("Etiqueta <R> fuera de una <Operacion>", i))
                else:
                    pila_ops[-1]["raiz_n"] = float(val)
            i = i2
            continue
    
        # <Numero> </Numero>
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
        if tipo in {"SUMA","RESTA","MULTIPLICACION","DIVISION","MOD"} and simb and len(nums) >= 2:
            expr = f" {simb} ".join(str(x) for x in nums)
            print(f"{expr} = {round(res, 6)}\n")
        elif tipo == "POTENCIA":
            base = nums[0] if nums else None
            if op.get("exp") is not None and base is not None:
                print(f"{base}^{op['exp']} = {round(res, 6)}\n")
            elif len(nums) == 2:
                print(f"{nums[0]}^{nums[1]} = {round(res, 6)}\n")
            else:
                print("(POTENCIA: base/exp insuficiente)\n")
        elif tipo == "RAIZ":
            n = op.get("raiz_n", 2)
            if nums:
                if n == 2 or n == 2.0:
                    print(f"√({nums[0]}) = {round(res, 6)}\n")
                else:
                    print(f"raíz_{n}({nums[0]}) = {round(res, 6)}\n")
            else:
                print("(RAIZ: radicando faltante)\n")
        elif tipo == "INVERSO" and len(nums) >= 1:
            print(f"1/({nums[0]}) = {round(res, 6)}\n")
        else:
            print("(operadores insuficientes o aridad inválida)\n")

    if errores:
        print("ERRORES:")
        for msg, pos in errores:
            print(f"- {msg} (pos {pos})")


if __name__ == "__main__":
    main()
