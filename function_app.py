import logging
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import azure.functions as func
from zeep import Client

# 1. Se define la aplicación de la función y el nivel de autenticación por defecto.
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# URL del WSDL (Definición del servicio)
WSDL_URL = 'https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService?WSDL'
# URL del Endpoint real (Forzamos HTTPS para evitar problemas con la URL interna del WSDL)
SERVICE_URL = 'https://www.superfinanciera.gov.co/SuperfinancieraWebServiceTRM/TCRMServicesWebService/TCRMServicesWebService'

def obtener_trm_vigente(fecha_consulta_str: str | None = None):
    """
    Obtiene la Tasa Representativa del Mercado (TRM) desde el servicio SOAP de la Superfinanciera.

    Args:
        fecha_consulta_str (str | None): Fecha en formato 'YYYY-MM-DD' para consultar la TRM.
                                         Si es None, se usa la fecha actual de Colombia.

    Returns:
        tuple: Una tupla con (valor_trm, status_code, error_message).
               - valor_trm (float | None): El valor de la TRM si fue exitoso.
               - status_code (int): Código de estado HTTP (200, 404, 502).
               - error_message (str | None): Mensaje de error si falló.
    """
    try:
        if not fecha_consulta_str:
            zona_horaria_colombia = ZoneInfo("America/Bogota")
            fecha_actual = datetime.now(zona_horaria_colombia)
            fecha_a_usar = fecha_actual.strftime('%Y-%m-%d')
        else:
            fecha_a_usar = fecha_consulta_str

        client = Client(WSDL_URL)

        # CRITICO: Forzar la dirección del servicio a la URL pública HTTPS.
        # El WSDL de la Superfinanciera a veces devuelve direcciones internas (http://app-sfc...)
        # que no son accesibles desde fuera, causando fallos de conexión.
        client.service._binding_options['address'] = SERVICE_URL

        response = client.service.queryTCRM(fecha_a_usar)

        if response is None:
             return (None, 404, f"No se encontró información de TRM para la fecha {fecha_a_usar}.")

        valor_trm = response.value

        if valor_trm:
            return (float(valor_trm), 200, None)
        else:
            return (None, 404, f"La entidad retornó datos vacíos para la fecha {fecha_a_usar}.")

    except Exception as e:
        # Registramos el error completo para diagnóstico interno, pero retornamos un mensaje genérico al cliente si es necesario
        logging.error(f"Error al consultar SOAP Superfinanciera: {str(e)}")
        return (None, 502, f"Error de comunicación con el servicio externo: {str(e)}")

@app.route(route="GetTrm", methods=["get"])
def GetTrm(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function Trigger HTTP para obtener la TRM.

    Parámetros de consulta (Query Params):
        fecha (opcional): Fecha en formato 'YYYY-MM-DD'. Si no se envía, usa la fecha actual.

    Retorna:
        JSON con el valor de la TRM, unidad, fecha y fuente.
    """
    logging.info('Se ha recibido una solicitud para obtener la TRM (Oficial Superfinanciera).')

    fecha_param = req.params.get('fecha')

    if fecha_param:
        try:
            datetime.strptime(fecha_param, '%Y-%m-%d')
        except ValueError:
            return func.HttpResponse(
                json.dumps({"error": "Formato de fecha inválido. Utilice AAAA-MM-DD."}),
                status_code=400,
                mimetype="application/json"
            )

    trm, status_code, error_message = obtener_trm_vigente(fecha_param)

    if error_message:
        return func.HttpResponse(
            json.dumps({"error": error_message}),
            status_code=status_code,
            mimetype="application/json"
        )
    else:
        response_data = {
            "valor": trm,
            "unidad": "COP",
            "fecha_consulta": fecha_param if fecha_param else datetime.now(ZoneInfo("America/Bogota")).strftime('%Y-%m-%d'),
            "fuente": "Superfinanciera de Colombia (SOAP)"
        }
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )