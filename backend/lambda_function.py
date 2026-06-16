import json
import os
from google import genai
from google.genai import types

def lambda_handler(event, context):
    try:
        gemini_key = os.environ.get("GEMINI_API_KEY")
        if not gemini_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"success": False, "error": "Falta la variable GEMINI_API_KEY en AWS"})
            }
        
        client = genai.Client(api_key=gemini_key)
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
        
        response_filtro = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"Historial de correos:\n{thread_content}",
            config=types.GenerateContentConfig(system_instruction=system_filtro, temperature=0.1)
        )
        
        clasificacion = response_filtro.text.strip()
        clasificacion = "SITUACION_DE_ALERTA" if "SITUACION_DE_ALERTA" in clasificacion else "SIN_ACCION"
            
        if clasificacion == "SIN_ACCION":
            return {
                "statusCode": 200,
                "headers": { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" },
                "body": json.dumps({
                    "success": True, "classification": "SIN_ACCION", "follow_up_email": None
                })
            }
            
        # FASE 2: Copwriter comercial avanzado (Gemini 1.5 Pro)
        prompt_redaccion = f"Cliente: {client_name}\nDías silencio: {days_since_last_reply}\nPresupuesto: {budget_summary}\nHilo:\n{thread_content}"
        system_redaccion = (
            f"Eres el director comercial de la empresa '{business_name}'. Redacta un email de seguimiento "
            "altamente persuasivo y empático basado en los detalles del presupuesto. Añade escasez sutil. "
            "Devuelve tu respuesta exclusivamente en formato JSON estructurado con las llaves: 'subject' y 'body'."
        )
        
        response_redaccion = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=prompt_redaccion,
            config=types.GenerateContentConfig(
                system_instruction=system_redaccion, temperature=0.7, response_mime_type="application/json"
            )
        )
        
        email_data = json.loads(response_redaccion.text)
        
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