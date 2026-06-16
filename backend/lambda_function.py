import json
import os
import urllib.request

def call_gemini_api(model, system_instruction, prompt, is_json=False):
    """Función nativa para conectar con la API de Gemini sin librerías externas"""
    api_key = os.environ.get("GEMINI_API_KEY")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_instruction}]},
        "generationConfig": {
            "temperature": 0.1 if model == "gemini-1.5-flash" else 0.7
        }
    }
    
    if is_json:
        payload["generationConfig"]["responseMimeType"] = "application/json"
        
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result['candidates'][0]['content']['parts'][0]['text']

def lambda_handler(event, context):
    # 1. Detectar de forma segura el método HTTP (soporta formato AWS 1.0 y 2.0)
    http_method = event.get("httpMethod") or event.get("requestContext", {}).get("http", {}).get("method", "POST")
    
    # 2. RESPUESTA INMEDIATA AL PREFLIGHT (OPTIONS)
    # Si el navegador pregunta por permisos, respondemos con éxito y las cabeceras CORS activas
    if http_method == "OPTIONS":
        return {
            "statusCode": 200,
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
                "Access-Control-Allow-Methods": "POST, OPTIONS",
                "Access-Control-Max-Age": "86400"
            },
            "body": ""
        }

    try:
        if not os.environ.get("GEMINI_API_KEY"):
            return {
                "statusCode": 500,
                "headers": { "Access-Control-Allow-Origin": "*" },
                "body": json.dumps({"success": False, "error": "Falta la variable GEMINI_API_KEY en AWS"})
            }
        
        body_data = json.loads(event.get("body", "{}"))
        client_name = body_data.get("client_name", "Cliente")
        business_name = body_data.get("business_name", "Nuestra Empresa")
        days_since_last_reply = body_data.get("days_since_last_reply", 7)
        budget_summary = body_data.get("budget_summary", "")
        thread_content = body_data.get("thread_content", "")
        
        # FASE 1: Filtro clasificador lógico (Gemini 1.5 Flash)
        system_filtro = (
            "Eres un auditor lógico de flujos de venta por correo electrónico. "
            "Analiza el historial de mensajes adjunto. Determina si el cliente ha dejado de responder "
            "rompiendo una promesa de respuesta o tras mostrar interés real. "
            "Responde ESTRICTAMENTE con una de estas dos palabras en mayúsculas:\n"
            "- SITUACION_DE_ALERTA\n"
            "- SIN_ACCION"
        )
        
        clasificacion = call_gemini_api(
            model='gemini-1.5-flash',
            system_instruction=system_filtro,
            prompt=f"Historial de correos:\n{thread_content}"
        ).strip()
        
        clasificacion = "SITUACION_DE_ALERTA" if "SITUACION_DE_ALERTA" in clasificacion else "SIN_ACCION"
            
        if clasificacion == "SIN_ACCION":
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
                "body": json.dumps({
                    "success": True, "classification": "SIN_ACCION", "follow_up_email": None
                })
            }
            
        # FASE 2: Copywriter comercial avanzado (Gemini 1.5 Pro)
        prompt_redaccion = f"Cliente: {client_name}\nDías silencio: {days_since_last_reply}\nPresupuesto: {budget_summary}\nHilo:\n{thread_content}"
        system_redaccion = (
            f"Eres el director comercial de la empresa '{business_name}'. Redacta un email de seguimiento "
            "altamente persuasivo y empático basado en los detalles del presupuesto. Añade escasez sutil. "
            "Devuelve tu respuesta exclusivamente en formato JSON estructurado con las llaves: 'subject' y 'body'. "
            "No incluyas formatos de texto como ```json."
        )
        
        texto_redaccion = call_gemini_api(
            model='gemini-1.5-pro',
            system_instruction=system_redaccion,
            prompt=prompt_redaccion,
            is_json=True
        )
        
        email_data = json.loads(texto_redaccion)
        
        return {
            "statusCode": 200,
            "headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
            "body": json.dumps({
                "success": True,
                "classification": "SITUACION_DE_ALERTA",
                "follow_up_email": { "subject": email_data.get("subject"), "body": email_data.get("body") }
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": { "Access-Control-Allow-Origin": "*" },
            "body": json.dumps({"success": False, "error": str(e)})
        }