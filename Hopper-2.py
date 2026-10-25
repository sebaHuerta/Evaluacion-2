import requests
import urllib.parse
import os

# ==========================================
# CONFIGURACION DE GRAPHHOPPER
# ==========================================

route_url = "https://graphhopper.com/api/1/route"
key = os.getenv("GRAPHHOPPER_API_KEY")

# Si no se definió la variable de entorno, se pide la clave por teclado
if not key:
    key = input("Ingrese su API Key de GraphHopper: ").strip()

# Palabras que permiten salir del programa
opciones_salida = ["s", "salir"]

# ==========================================
# FUNCION DE GEOCODIFICACION
# ==========================================

def geocoding(location, key):

    while location.strip() == "":
        location = input("Ingrese la ubicación nuevamente: ")

    geocode_url = "https://graphhopper.com/api/1/geocode?"

    url = geocode_url + urllib.parse.urlencode({
        "q": location,
        "limit": "1",
        "key": key
    })

    try:
        replydata = requests.get(url, timeout=15)
        json_data = replydata.json()
        json_status = replydata.status_code

        if json_status == 200 and json_data.get("hits"):

            hit = json_data["hits"][0]

            lat = hit["point"]["lat"]
            lng = hit["point"]["lng"]
            name = hit["name"]
            value = hit.get("osm_value", "desconocido")

            country = hit.get("country", "")
            state = hit.get("state", "")

            if state and country:
                new_loc = name + ", " + state + ", " + country

            elif state:
                new_loc = name + ", " + state

            elif country:
                new_loc = name + ", " + country

            else:
                new_loc = name

            # Ocultar API Key al imprimir
            print(
                "URL de la Geocoding API para " + new_loc +
                " (Tipo de ubicación: " + value + ")"
            )

            print(geocode_url + urllib.parse.urlencode({
                "q": location,
                "limit": "1",
                "key": "OCULTA"
            }))

        else:
            lat = None
            lng = None
            new_loc = location

            print("Estado de la Geocoding API:", json_status)
            print("Error:", json_data.get(
                "message", "Ubicación no encontrada"
            ))

    except (requests.RequestException, ValueError) as error:
        print("Error de geocodificación:", error)

        json_status = 0
        lat = None
        lng = None
        new_loc = location

    return json_status, lat, lng, new_loc


# ==========================================
# PROGRAMA PRINCIPAL
# ==========================================

# Perfiles en español -> perfil que entiende la API
perfiles = {
    "auto": "car",
    "bicicleta": "bike",
    "a pie": "foot",
    "car": "car",
    "bike": "bike",
    "foot": "foot"
}

nombres_perfil = {"car": "auto", "bike": "bicicleta", "foot": "a pie"}

while True:

    print("\n+++++++++++++++++++++++++++++++++++++++++++++")
    print("Perfiles de vehículo disponibles en GraphHopper:")
    print("+++++++++++++++++++++++++++++++++++++++++++++")
    print("auto, bicicleta, a pie")
    print("+++++++++++++++++++++++++++++++++++++++++++++")
    print("Escriba 's' o 'salir' en cualquier momento para terminar.")

    vehiculo = input(
        "Ingrese un perfil de vehículo de la lista: "
    ).strip().lower()

    if vehiculo in opciones_salida:
        print("Saliendo del programa...")
        break

    if vehiculo in perfiles:
        vehicle = perfiles[vehiculo]
    else:
        vehicle = "car"
        print(
            "No se ingresó un perfil válido. "
            "Se usará el perfil auto."
        )

    # ======================================
    # UBICACION DE ORIGEN
    # ======================================

    loc1 = input("Ubicación de origen: ").strip()

    if loc1.lower() in opciones_salida:
        print("Saliendo del programa...")
        break

    orig = geocoding(loc1, key)

    if orig[1] is None or orig[2] is None:
        print("Ubicación de origen no válida.")
        continue

    # ======================================
    # UBICACION DE DESTINO
    # ======================================

    loc2 = input("Ubicación de destino: ").strip()

    if loc2.lower() in opciones_salida:
        print("Saliendo del programa...")
        break

    dest = geocoding(loc2, key)

    if dest[1] is None or dest[2] is None:
        print("Ubicación de destino no válida.")
        continue

    # ======================================
    # CONSTRUIR URL DE ROUTING API
    # ======================================

    parameters = {
        "key": key,
        "profile": vehicle,
        "point": [
            f"{orig[1]},{orig[2]}",
            f"{dest[1]},{dest[2]}"
        ],
        "instructions": "true",
        "locale": "es",
        "calc_points": "true"
    }

    try:
        response = requests.get(
            route_url,
            params=parameters,
            timeout=30
        )

        status = response.status_code
        json_data = response.json()

    except (requests.RequestException, ValueError) as error:
        print("Error de la Routing API:", error)
        continue

    print("=================================================")
    print("Estado de la Routing API:", status)

    # Mostrar URL sin exponer la API Key
    safe_parameters = parameters.copy()
    safe_parameters["key"] = "OCULTA"

    safe_url = requests.Request(
        "GET",
        route_url,
        params=safe_parameters
    ).prepare().url

    print("URL de la Routing API:")
    print(safe_url)

    print("=================================================")

    print(
        f"Indicaciones desde {orig[3]} hasta {dest[3]} "
        f"en {nombres_perfil[vehicle]}"
    )

    print("=================================================")

    # ======================================
    # VALIDAR RESULTADO DE ROUTING API
    # ======================================

    if status == 200 and json_data.get("paths"):

        path = json_data["paths"][0]

        distance = path["distance"]
        time = path["time"]

        # Conversion de distancias
        km = distance / 1000
        miles = km / 1.609344

        # Conversion de tiempo
        total_minutes = time / 1000 / 60
        seconds = int(time / 1000)

        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60

        print(
            f"Distancia recorrida: "
            f"{km:.2f} km / {miles:.2f} millas"
        )

        print(
            f"Duración del viaje: "
            f"{hours:02d}:{minutes:02d}:{secs:02d} "
            f"({total_minutes:.2f} minutos)"
        )

        print("=================================================")

        # ==================================
        # MOSTRAR NARRATIVA DEL VIAJE
        # ==================================

        print("Narrativa del viaje (paso a paso):")

        instructions = path.get("instructions", [])

        for numero, instruction in enumerate(instructions, start=1):

            text = instruction.get("text", "")

            step_distance = instruction.get("distance", 0)

            step_km = step_distance / 1000
            step_miles = step_km / 1.609344

            print(
                f"{numero}. {text} "
                f"( {step_km:.2f} km / "
                f"{step_miles:.2f} millas )"
            )

        print("=================================================")

    else:
        print(
            "Mensaje de error:",
            json_data.get(
                "message",
                "No se encontró una conexión entre las ubicaciones"
            )
        )

        print("*************************************************")