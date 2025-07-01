import logging
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import azure.functions as func

# 1. Se define la aplicación de la función y el nivel de autenticación por defecto.
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

def obtener_trm_vigente(fecha_consulta_str: str | None = None):
    """
    Obtiene la Tasa Representativa del Mercado (TRM) para una fecha específica
    o para el día actual si no se especifica una fecha.

    Args:
        fecha_consulta_str (str, optional): La fecha a consultar en formato 'AAAA-MM-DD'.
                                            Si es None, se usa la fecha actual. Defaults to None.
    
    Returns:
        tuple: (valor_trm, status_code, mensaje_error)
    """
    api_url = "https://www.datos.gov.co/resource/32sa-8pi3.json"
    
    try:
        # Si no se provee una fecha, se usa la actual de Colombia.
        if not fecha_consulta_str:
            zona_horaria_colombia = ZoneInfo("America/Bogota")
            fecha_actual = datetime.now(zona_horaria_colombia)
            fecha_a_usar = fecha_actual.strftime('%Y-%m-%d')
        else:
            fecha_a_usar = fecha_consulta_str

        # La consulta ahora compara la fecha truncada de los campos de la API
        # contra la fecha a usar (sin hora), lo cual es robusto.
        query = (
            f"$where=date_trunc_ymd(vigenciadesde) <= '{fecha_a_usar}' "
            f"AND date_trunc_ymd(vigenciahasta) >= '{fecha_a_usar}'"
        )
        
        response = requests.get(f"{api_url}?{query}")
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            trm_valor_str = data[0].get("valor")
            if trm_valor_str:
                return (float(trm_valor_str), 200, None)
        
        return (None, 404, f"No se encontró una TRM vigente para la fecha {fecha_a_usar}.")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error de red o en la solicitud a la API: {e}")
        return (None, 502, "Error al comunicarse con el servicio de TRM externo.")
    except (ValueError, KeyError, IndexError) as e:
        logging.error(f"Error al procesar los datos recibidos: {e}")
        return (None, 500, "Error interno al procesar la respuesta de la TRM.")

@app.route(route="GetTrm", methods=["get"])
def GetTrm(req: func.HttpRequest) -> func.HttpResponse:
    """
    Punto de entrada principal para la Azure Function (modelo v2).
    Acepta un parámetro opcional 'fecha' (AAAA-MM-DD) para consultas históricas.
    """
    logging.info('Se ha recibido una solicitud para obtener la TRM (modelo v2).')

    fecha_param = req.params.get('fecha')

    # Validar el formato de la fecha si se proporciona
    if fecha_param:
        try:
            datetime.strptime(fecha_param, '%Y-%m-%d')
        except ValueError:
            error_response = {
                "error": "Formato de fecha inválido. Utilice AAAA-MM-DD."
            }
            return func.HttpResponse(
                json.dumps(error_response),
                status_code=400,
                mimetype="application/json"
            )

    # Llamar a la lógica de negocio con el parámetro de fecha (puede ser None)
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
            "fecha_consulta": fecha_param if fecha_param else datetime.now(ZoneInfo("America/Bogota")).strftime('%Y-%m-%d')
        }
        return func.HttpResponse(
            json.dumps(response_data),
            status_code=200,
            mimetype="application/json"
        )