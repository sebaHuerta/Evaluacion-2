#!/usr/bin/env python3
"""
poblar_biblioteca_50.py  -  Requerimiento 2 (parte Python) de la Evaluación Parcial N° 2.

Qué hace, en 4 pasos (los mismos números aparecen como comentarios más abajo):
  PASO 1. Inicia sesión en la API (POST /loginViaBasic) y obtiene el token.
  PASO 2. Lee el catálogo actual para saber cuál es el último id y seguir desde ahí.
  PASO 3. Crea 50 libros al azar (autor, título e ISBN) con POST /books.
  PASO 4. Lista TODOS los libros (con ISBN) ordenados por autor.

Cómo se ejecuta (dentro de la VM DEVASC, en una terminal):
    cd ~/biblioteca
    python3 poblar_biblioteca_50.py

Opciones (todas son opcionales):
    --base URL           dirección base de la API (por defecto http://library.demo.local/api/v1)
    --usuario / --clave  credenciales del login (por defecto las del laboratorio: cisco / Cisco123!)
    --cantidad 50        cuántos libros crear
    --solo-listar        NO crea nada, solo muestra el catálogo (úsalo si ya corriste el script una vez)

IMPORTANTE: antes de correrlo, crea en Postman los libros 5, 6 y 7 (Parte 1 de la guía).
Si lo corres dos veces vas a tener 100 libros nuevos y no 50.
"""

import argparse
import random
import sys
import time
import unicodedata

import requests

BASE_POR_DEFECTO = "http://library.demo.local/api/v1"
MAX_PAGINAS = 200          # tope de seguridad al recorrer las páginas de la API
PAUSA_ENTRE_PAGINAS = 0.4  # segundos entre consultas, para no superar el límite de la API
REINTENTOS_429 = 6         # veces que se reintenta si la API responde "demasiadas consultas"

# Nombres de los campos tal como los entrega la API.
F_ID, F_TITULO, F_AUTOR, F_ISBN = "id", "title", "author", "isbn"

NOMBRES = ["Camila", "Matías", "Valentina", "Benjamín", "Javiera", "Sebastián", "Francisca",
           "Nicolás", "Constanza", "Felipe", "Daniela", "Ignacio", "Catalina", "Tomás",
           "Fernanda", "Joaquín", "Antonia", "Diego", "Isidora", "Vicente"]
APELLIDOS = ["González", "Muñoz", "Rojas", "Díaz", "Pérez", "Soto", "Contreras", "Silva",
             "Martínez", "Sepúlveda", "Morales", "Rodríguez", "López", "Fuentes", "Hernández",
             "Torres", "Araya", "Flores", "Espinoza", "Valenzuela"]

TEMAS = ["Redes", "Seguridad Informática", "Python", "Automatización", "Cloud Computing",
         "Linux", "APIs REST", "Programabilidad", "Virtualización", "Ciberseguridad",
         "Telepresencia", "Infraestructura", "Bases de Datos", "DevOps", "Microservicios"]
FORMATOS = ["Guía práctica de {t}", "Fundamentos de {t}", "{t} para principiantes",
            "Manual avanzado de {t}", "Introducción a {t}", "{t}: casos reales",
            "Laboratorios de {t}", "Domina {t} paso a paso", "El gran libro de {t}"]


def extraer_lista(datos):
    """Acepta que la API responda una lista o un objeto que contiene la lista."""
    if isinstance(datos, list):
        return datos
    if isinstance(datos, dict):
        for valor in datos.values():
            if isinstance(valor, list):
                return valor
    return []


def pedir(metodo, url, **kwargs):
    """Hace la consulta HTTP; si la API responde 429 (demasiadas consultas), espera y reintenta.

    Todas las llamadas del script pasan por aquí. El 429 ("Too Many Requests") es la forma que
    tiene la API de decir "vas muy rápido": esperamos 1, 2, 4, 8... segundos y probamos de nuevo.
    """
    espera = 1
    for _ in range(REINTENTOS_429):
        r = requests.request(metodo, url, timeout=15, **kwargs)
        if r.status_code != 429:
            return r
        try:
            pedida = float(r.headers.get("Retry-After", ""))   # a veces la API indica cuánto esperar
        except ValueError:
            pedida = 0
        pausa = max(espera, pedida)
        print(f"[aviso] la API respondió 429 (demasiadas consultas); espero {pausa:.0f} s y reintento")
        time.sleep(pausa)
        espera = min(espera * 2, 16)
    return r


def iniciar_sesion(base, usuario, clave):
    """PASO 1: igual que en Postman (Authorization > Basic Auth), pero con auth=(usuario, clave)."""
    r = pedir("POST", f"{base}/loginViaBasic", auth=(usuario, clave))
    if r.status_code != 200 or not r.json().get("token"):
        sys.exit(f"No se pudo iniciar sesión (HTTP {r.status_code}): {r.text[:150]}")
    print(f"POST {base}/loginViaBasic -> HTTP {r.status_code} (token obtenido)")
    return r.json()["token"]


# Consultas que se intentan para cada página, de la más completa a la más simple.
CONSULTAS = [
    {"includeISBN": "true", "sortBy": "author"},
    {"includeISBN": "true"},
    {},
]


def pedir_pagina(base, cabeceras, pagina):
    """Pide una página de GET /books. Si la consulta completa falla, prueba con otras más simples.

    Devuelve (respuesta, parametros_usados); parametros_usados es None si ninguna funcionó.
    """
    ultima = None
    for consulta in CONSULTAS:
        params = dict(consulta)
        if pagina is not None:
            params["page"] = pagina
        for intento in range(2):                    # un reintento breve por si fue un fallo pasajero
            ultima = pedir("GET", f"{base}/books", params=params, headers=cabeceras)
            if ultima.status_code == 200:
                return ultima, params
            if ultima.status_code == 429:           # límite de consultas: probar otra variante no ayuda
                return ultima, None
            time.sleep(0.5)
    return ultima, None


def obtener_catalogo(base, cabeceras):
    """Lee TODAS las páginas de GET /books (la API entrega 10 libros por página).

    Si pidiéramos solo una vez, veríamos únicamente los primeros 10 libros. Por eso se pide la
    página inicial y luego page=1, page=2, ... hasta que ya no aparezcan libros nuevos.

    Devuelve (estado_http_primera_pagina, lista_de_libros_sin_repetidos).
    """
    vistos = {}
    sin_nuevos = 0
    fallidas = 0
    estado = None
    for pagina in [None] + list(range(1, MAX_PAGINAS)):
        r, usados = pedir_pagina(base, cabeceras, pagina)
        etiqueta = "inicial" if pagina is None else pagina
        if usados is None:                          # ninguna consulta funcionó para esta página
            if pagina is None:
                r.raise_for_status()
            fallidas += 1
            print(f"[aviso] la página {etiqueta} no respondió (HTTP {r.status_code}); sigo con la siguiente")
            if fallidas >= 3:                       # tres fallos seguidos: no hay más páginas
                break
            continue
        fallidas = 0
        if pagina is None:
            estado = r.status_code
        if "sortBy" not in usados:
            print(f"[aviso] página {etiqueta}: la API no aceptó sortBy; el orden se aplica en el script")
        if "includeISBN" not in usados:
            print(f"[aviso] página {etiqueta}: la API no entregó el ISBN en esta consulta")
        nuevos = [l for l in extraer_lista(r.json()) if l.get(F_ID) not in vistos]
        for libro in nuevos:
            vistos[libro[F_ID]] = libro
        sin_nuevos = 0 if nuevos else sin_nuevos + 1
        if sin_nuevos >= 2:                         # dos páginas seguidas sin libros nuevos
            break
        time.sleep(PAUSA_ENTRE_PAGINAS)             # respeta el límite de consultas de la API
    return estado, list(vistos.values())


def clave_autor(libro):
    """Clave para ordenar por autor sin distinguir mayúsculas ni tildes; desempata por id."""
    autor = unicodedata.normalize("NFD", str(libro.get(F_AUTOR, "")))
    autor = "".join(c for c in autor if not unicodedata.combining(c)).casefold()
    id_ = str(libro.get(F_ID, ""))
    return autor, (int(id_) if id_.isdigit() else 0)


def isbn_aleatorio(usados):
    """ISBN de 13 dígitos que empieza con 978 y que no se repite con ninguno ya usado."""
    while True:
        isbn = "978" + "".join(random.choices("0123456789", k=10))
        if isbn not in usados:
            usados.add(isbn)
            return isbn


def libro_aleatorio(nuevo_id, usados):
    """Arma el diccionario de un libro con autor, título e ISBN al azar (lo que pide el enunciado)."""
    autor = f"{random.choice(NOMBRES)}_{random.choice(APELLIDOS)}"
    titulo = random.choice(FORMATOS).format(t=random.choice(TEMAS))
    return {
        F_ID: nuevo_id,
        F_TITULO: titulo,
        F_AUTOR: autor,
        F_ISBN: isbn_aleatorio(usados),
    }


def imprimir_catalogo(libros):
    print(f"\n{'ID':>3} | {'ISBN':<14} | {'AUTOR':<23} | TÍTULO")
    print("-" * 80)
    for l in libros:
        print(f"{str(l.get(F_ID)):>3} | {str(l.get(F_ISBN, 'n/d')):<14} | "
              f"{str(l.get(F_AUTOR)):<23} | {l.get(F_TITULO)}")
    print("-" * 80)
    print(f"Total de libros en el catálogo: {len(libros)}")


def main():
    ap = argparse.ArgumentParser(description="Carga masiva de libros a la API de la Biblioteca")
    ap.add_argument("--base", default=BASE_POR_DEFECTO, help="URL base de la API")
    ap.add_argument("--usuario", default="cisco")
    ap.add_argument("--clave", default="Cisco123!")
    ap.add_argument("--cantidad", type=int, default=50)
    ap.add_argument("--solo-listar", action="store_true")
    args = ap.parse_args()
    base = args.base.rstrip("/")

    try:
        # PASO 1: login -> token. Con él armamos el encabezado que exige la API para crear libros.
        token = iniciar_sesion(base, args.usuario, args.clave)
        cabeceras = {"X-API-KEY": token}
        # PASO 2: leemos el catálogo actual (para continuar la numeración de ids).
        estado, existentes = obtener_catalogo(base, cabeceras)
    except requests.RequestException as e:
        sys.exit(f"No se pudo conectar con la API en {base}: {e}")
    print(f"GET {base}/books -> HTTP {estado} ({len(existentes)} libros existentes)")

    # PASO 3: crear los libros al azar (se omite si usas --solo-listar).
    if not args.solo_listar:
        ids_num = [int(l[F_ID]) for l in existentes if str(l.get(F_ID, "")).isdigit()]
        siguiente = (max(ids_num) + 1) if ids_num else 1
        isbn_usados = {str(l.get(F_ISBN)) for l in existentes}

        ok = fallidos = 0
        for i in range(args.cantidad):
            libro = libro_aleatorio(siguiente + i, isbn_usados)
            try:
                r = pedir("POST", f"{base}/books", json=libro, headers=cabeceras)
            except requests.RequestException as e:
                fallidos += 1
                print(f"[ERROR] id {libro[F_ID]}: {e}")
                continue
            if r.status_code == 401:
                sys.exit("[401] Token inválido o vencido: vuelve a ejecutar el script para iniciar sesión.")
            if r.status_code in (200, 201):
                ok += 1
                print(f"[{r.status_code}] id {libro[F_ID]:>3} | {libro[F_AUTOR]:<22} | {libro[F_TITULO]}")
            else:
                fallidos += 1
                print(f"[{r.status_code}] id {libro[F_ID]} rechazado: {r.text[:120]}")
        print(f"\nResumen: {ok} creados, {fallidos} con error")

    # PASO 4: listado final de la totalidad de libros (todas las páginas), ordenado por autor.
    # La API ordena solo dentro de cada página de 10 libros, por eso el orden final se aplica aquí.
    if args.solo_listar:
        todos = existentes                          # ya se leyó el catálogo completo arriba
    else:
        estado, todos = obtener_catalogo(base, cabeceras)
    print(f"\nGET {base}/books?includeISBN=true&sortBy=author (todas las páginas) -> HTTP {estado}")
    imprimir_catalogo(sorted(todos, key=clave_autor))


if __name__ == "__main__":
    main()
