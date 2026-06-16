import json
import os
import urllib.request
import urllib.error

# Cabeceras CORS reutilizables
CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Max-Age": "86400"
}

def build_response(status_code, body_dict):
    return {
        "statusCode": status_code,
        "headers": CORS_HEADERS,
        "body": json.dumps(body_dict, ensure_ascii=False)
    }

def call_gemini_api(model, system_instruction, prompt, is_json=False):
    api_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.1 if "flash" in model else 0.7
        }
    }
    
    if is_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise Exception(f"Gemini API error {e.code}: {error_body}")

def lambda_handler(event, context):
    # Detectar método HTTP — compatible con API Gateway v1, v2 y Lambda URL
    http_method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method", "")
        or "POST"
    ).upper()

    # Preflight CORS — respuesta inmediata con todas las cabeceras
    if http_method == "OPTIONS":
        return {
            "statusCode": 204,
            "headers": CORS_HEADERS,
            "body": ""
        }

    if http_method != "POST":
        return build_response(405, {"success": False, "error": "Método no permitido"})

    try:
        # Validar API key
        if not os.environ.get("GEMINI_API_KEY"):
            return build_response(500, {"success": False, "error": "Falta GEMINI_API_KEY en variables de entorno"})

        # Parsear body — Lambda URL y API Gateway lo envían igual
        raw_body = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            import base64
            raw_body = base64.b64decode(raw_body).decode("utf-8")
        
        body_data = json.loads(raw_body)

        client_name          = body_data.get("client_name", "Cliente")
        business_name        = body_data.get("business_name", "Nuestra Empresa")
        days_since_last_reply = body_data.get("days_since_last_reply", 7)
        budget_summary       = body_data.get("budget_summary", "")
        thread_content       = body_data.get("thread_content", "")

        if not thread_content:
            return build_response(400, {"success": False, "error": "El campo thread_content es obligatorio"})

        # FASE 1 — Clasificador (Gemini Flash, barato y rápido)
        system_filtro = (
            "Eres un auditor lógico de flujos de venta por correo electrónico. "
            "Analiza el historial de mensajes adjunto. Determina si el cliente ha dejado de responder "
            "rompiendo una promesa de respuesta o tras mostrar interés real. "
            "Responde ESTRICTAMENTE con una de estas dos palabras en mayúsculas:\n"
            "- SITUACION_DE_ALERTA\n"
            "- SIN_ACCION"
        )

        clasificacion_raw = call_gemini_api(
            model="gemini-1.5-flash",
            system_instruction=system_filtro,
            prompt=f"Historial de correos:\n{thread_content}"
        ).strip()

        clasificacion = "SITUACION_DE_ALERTA" if "SITUACION_DE_ALERTA" in clasificacion_raw else "SIN_ACCION"

        if clasificacion == "SIN_ACCION":
            return build_response(200, {
                "success": True,
                "classification": "SIN_ACCION",
                "follow_up_email": None
            })

        # FASE 2 — Redacción (Gemini Pro, calidad máxima)
        system_redaccion = (
            f"Eres el director comercial de '{business_name}'. Redacta un email de seguimiento "
            "altamente persuasivo y empático basado en los detalles del presupuesto. Añade escasez sutil. "
            "Devuelve EXCLUSIVAMENTE un objeto JSON válido con las claves 'subject' y 'body'. "
            "Sin explicaciones, sin bloques de código, sin texto adicional."
        )

        prompt_redaccion = (
            f"Cliente: {client_name}\n"
            f"Días de silencio: {days_since_last_reply}\n"
            f"Presupuesto enviado: {budget_summary}\n"
            f"Hilo de correos:\n{thread_content}"
        )

        texto_redaccion = call_gemini_api(
            model="gemini-1.5-pro",
            system_instruction=system_redaccion,
            prompt=prompt_redaccion,
            is_json=True
        )

        # Limpieza defensiva por si Gemini añade backticks igualmente
        texto_limpio = texto_redaccion.strip()
        if texto_limpio.startswith("```"):
            texto_limpio = texto_limpio.split("```")[1]
            if texto_limpio.startswith("json"):
                texto_limpio = texto_limpio[4:]
        texto_limpio = texto_limpio.strip()

        email_data = json.loads(texto_limpio)

        return build_response(200, {
            "success": True,
            "classification": "SITUACION_DE_ALERTA",
            "follow_up_email": {
                "subject": email_data.get("subject", ""),
                "body": email_data.get("body", "")
            }
        })

    except json.JSONDecodeError as e:
        return build_response(502, {"success": False, "error": f"Respuesta inválida de Gemini: {str(e)}"})
    except Exception as e:
        return build_response(500, {"success": False, "error": str(e)})