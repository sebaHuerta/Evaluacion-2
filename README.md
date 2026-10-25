# Evaluación 2 - CUY6142

Proyecto de la **Evaluación Parcial N° 2** de la asignatura **CUY6142 - Telepresencia y Entornos Innovadores de Colaboración Humana**.

El caso simula el trabajo de un desarrollador junior en la consultora **API Ltda.**, que apoya a la **Biblioteca Nacional** en dos tareas:

1. Poblar y administrar el catálogo de libros mediante la **API REST de la biblioteca**.
2. Mejorar un prototipo de geolocalización que calcula rutas para llegar a la biblioteca usando **GraphHopper Directions API**.

## Contenido del repositorio

| Archivo | Descripción |
|---|---|
| `Hopper-2.py` | Calcula rutas entre dos ubicaciones con GraphHopper (geocodificación + cálculo de rutas). |
| `poblar_biblioteca_50.py` | Crea 50 libros aleatorios en la API de la biblioteca y lista el catálogo ordenado por autor con ISBN. |

## Requisitos

- Máquina virtual **DEVASC** (Ubuntu 20.04)
- **Python 3**
- Paquete **`requests`**
- Una **API Key de GraphHopper** ([graphhopper.com](https://www.graphhopper.com/)), solo para `Hopper-2.py`
- Acceso a la API de la biblioteca (`http://library.demo.local/api/v1`), solo para `poblar_biblioteca_50.py`

Instalar la dependencia:

```bash
pip3 install requests
```

Clonar el repositorio:

```bash
git clone https://github.com/sebaHuerta/Evaluacion-2.git
cd Evaluacion-2
```

---

## 1. `Hopper-2.py` - Rutas con GraphHopper

### Mejoras realizadas

- Todos los textos de interacción con el usuario están en **español**.
- Distancias y tiempos se muestran con un **máximo de dos decimales**.
- Se puede **salir** del programa escribiendo `s` o `salir` en cualquier pregunta.
- La **narrativa del viaje** (instrucciones paso a paso) se entrega en **español** y numerada.
- Perfiles de transporte en español: `auto`, `bicicleta` y `a pie`.

### Cómo ejecutarlo

1. Definir la API Key como variable de entorno (la clave **no** está escrita en el código):

   ```bash
   export GRAPHHOPPER_API_KEY="tu_api_key"
   ```

   Si no se define, el programa la pedirá por teclado al iniciar.

2. Ejecutar el script:

   ```bash
   python3 Hopper-2.py
   ```

3. Responder las preguntas: perfil de transporte, ubicación de origen y ubicación de destino.
4. Para terminar, escribir `s` o `salir`.

### Ejemplo de uso

```text
Ingrese un perfil de vehículo de la lista: a pie
Ubicación de origen: Plaza de Armas, Santiago, Chile
Ubicación de destino: Avenida Libertador Bernardo O'Higgins 651, Santiago, Chile
...
Distancia recorrida: 1.02 km / 0.63 millas
Duración del viaje: 00:12:36 (12.61 minutos)
=================================================
Narrativa del viaje (paso a paso):
1. Continúe hacia ... ( 0.15 km / 0.09 millas )
2. Gire a la derecha ... ( 0.40 km / 0.25 millas )
...
```

---

## 2. `poblar_biblioteca_50.py` - Carga masiva de libros

### Qué hace

1. Inicia sesión en la API (`POST /loginViaBasic`) y obtiene el token.
2. Lee el catálogo actual para continuar la numeración de los `id`.
3. Crea **50 libros aleatorios** (autor, título e ISBN) con `POST /books`.
4. Lista **todos** los libros, con ISBN, **ordenados por autor**.

### Cómo ejecutarlo

```bash
python3 poblar_biblioteca_50.py
```

Opciones disponibles:

| Opción | Descripción |
|---|---|
| `--base URL` | URL base de la API (por defecto `http://library.demo.local/api/v1`) |
| `--usuario` / `--clave` | Credenciales del login (por defecto las del laboratorio DEVASC) |
| `--cantidad N` | Cantidad de libros a crear (por defecto 50) |
| `--solo-listar` | No crea libros, solo muestra el catálogo ordenado por autor |

Ejemplo, solo para ver el catálogo:

```bash
python3 poblar_biblioteca_50.py --solo-listar
```

> **Importante:** si se ejecuta dos veces sin `--solo-listar`, se crearán 50 libros más.

---

## Seguridad

- La API Key de GraphHopper **no se incluye en el código**: se lee desde la variable de entorno `GRAPHHOPPER_API_KEY`.
- Las URLs que se imprimen en pantalla muestran la clave como `OCULTA`.

## Herramientas utilizadas

- **Postman**: pruebas y consumo de la API REST de la biblioteca.
- **Visual Studio Code**: desarrollo en Python.
- **Git / GitHub**: control de versiones.

## Autor

**Sebastián Huerta** - [sebaHuerta](https://github.com/sebaHuerta)
