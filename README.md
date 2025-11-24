# API de TRM con Azure Functions (Oficial Superfinanciera)

Este proyecto implementa una API RESTful utilizando **Azure Functions** (modelo de programación v2 en Python) para consultar la Tasa Representativa del Mercado (TRM) de Colombia.

A diferencia de versiones anteriores que dependían de portales de datos abiertos, esta versión se conecta **directamente al Web Service SOAP oficial de la Superintendencia Financiera de Colombia**, garantizando la máxima fiabilidad y disponibilidad del dato.

## Características

- **Fuente Oficial**: Consume el servicio SOAP (`TCRMServicesWebService`) de la Superfinanciera.
- **Interfaz Simplificada**: Expone los datos complejos del SOAP a través de un endpoint REST (JSON) fácil de consumir.
- **Consulta de TRM actual**: Obtiene la TRM vigente para el día en curso (zona horaria de Colombia).
- **Consulta de TRM histórica**: Permite consultar la TRM para una fecha específica.
- **Manejo de Errores**: Gestión robusta de fallos de conexión, timeouts y errores XML/SOAP.

---

## Requisitos Previos

Antes de empezar, asegúrate de tener instalado lo siguiente:

- Python 3.9+
- Azure Functions Core Tools
- Una cuenta de Azure (para el despliegue)

---

## Configuración del Entorno Local

Sigue estos pasos para configurar y ejecutar el proyecto en tu máquina local.

1.  **Clona el repositorio:**
    ```bash
    git clone [https://github.com/juancsanchez/TRM_Colombia_HTTP.git](https://github.com/juancsanchez/TRM_Colombia_HTTP.git)
    cd TRM_Colombia_HTTP
    ```

2.  **Crea un entorno virtual:**
    Es una buena práctica aislar las dependencias del proyecto.
    ```bash
    python -m venv .venv
    ```

3.  **Activa el entorno virtual:**
    -   **Windows (cmd/powershell):**
        ```powershell
        .\.venv\Scripts\Activate.ps1
        ```
    -   **macOS/Linux (bash):**
        ```bash
        source .venv/bin/activate
        ```

4.  **Instala las dependencias:**
    El proyecto requiere `azure-functions`, `zeep` (para SOAP) y `requests`.
    ```bash
    pip install -r requirements.txt
    ```

---

## Ejecución Local

Una vez configurado el entorno, puedes iniciar la Function App localmente.

1.  **Inicia el host de Azure Functions:**
    ```bash
    func start
    ```

2.  El terminal mostrará la URL del endpoint, que será similar a esta:
    ```
    Functions:
            GetTrm: [GET] http://localhost:7071/api/GetTrm
    ```

3.  **Realiza peticiones a la API:**
    Puedes usar `curl` o cualquier cliente de API para probar el endpoint.

    -   **Para obtener la TRM del día actual:**
        ```bash
        curl "http://localhost:7071/api/GetTrm"
        ```

    -   **Para obtener la TRM de una fecha específica:**
        ```bash
        curl "http://localhost:7071/api/GetTrm?fecha=2023-11-15"
        ```

> **Nota:** Al desplegar en Azure, el nivel de autenticación `FUNCTION` requerirá que incluyas una clave de API en la petición. Ejemplo: `.../api/GetTrm?code=<TU_FUNCTION_KEY>`.

---

## Detalles del Endpoint

### `GET /api/GetTrm`

Recupera la TRM vigente consultando el SOAP de la Superfinanciera.

#### Parámetros de Consulta (Query Parameters)

| Parámetro | Tipo   | Opcional | Descripción                               |
| :-------- | :----- | :------- | :---------------------------------------- |
| `fecha`   | string | Sí       | La fecha para la consulta en formato `AAAA-MM-DD`. Si se omite, se usa la fecha actual de Colombia. |

#### Respuestas

-   **`200 OK` - Éxito**
    ```json
    {
      "valor": 4050.11,
      "unidad": "COP",
      "fecha_consulta": "2023-11-15",
      "fuente": "Superfinanciera de Colombia (SOAP)"
    }
    ```

-   **`400 Bad Request` - Formato de fecha inválido**
    ```json
    {
      "error": "Formato de fecha inválido. Utilice AAAA-MM-DD."
    }
    ```

-   **`502 Bad Gateway` - Error de comunicación con Superfinanciera**
    ```json
    {
      "error": "Error de comunicación: <Detalle del error SOAP>"
    }
    ```

---

## Despliegue en Azure

Puedes desplegar esta función en tu suscripción de Azure usando Azure Functions Core Tools:

```bash
func azure functionapp publish <NOMBRE_DE_TU_FUNCTION_APP>