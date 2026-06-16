# SmartFollowUp AI 🚀 — Sistema Serverless de Recuperación de Presupuestos Fríos

![AWS Lambda](https://img.shields.io/badge/AWS_Lambda-FF9900?style=for-the-badge&logo=aws-lambda&logoColor=white)
![Google Gemini](https://img.shields.io/badge/Google_Gemini-8E75FF?style=for-the-badge&logo=googlegemini&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)
![Python](https://img.shields.io/badge/Python_3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript_ES6-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)

SmartFollowUp AI es una solución de software de arquitectura **Serverless** y desacoplada diseñada para optimizar el ciclo de venta de PYMEs y profesionales independientes. La aplicación automatiza la auditoría de hilos de correos electrónicos comerciales, detecta situaciones de pérdida de contacto (*ghosting*) por parte del cliente y genera respuestas de seguimiento altamente personalizadas y persuasivas utilizando Inteligencia Artificial avanzada.

---

## 🏗️ Arquitectura y Flujo del Sistema

El proyecto implementa un patrón de diseño moderno basado en la separación absoluta de responsabilidades (*Frontend/Backend decoupled architecture*):

```text
[ Cliente Web (Vercel) ] 
       │ (Petición HTTP POST con JSON Payload)
       ▼
[ AWS Lambda Proxy (Python) ] ➔ Consume de forma segura la GEMINI_API_KEY cifrada
       │
       ├─► (Fase 1: Filtrado Lógico) ➔ Gemini 1.5 Flash (Clasificación rápida)
       │       │ 
       │       └─► Si el estado es "SIN_ACCION" ➔ Corta ejecución (Ahorro de recursos)
       │
       └─► (Fase 2: Redacción Persuasiva) ➔ Gemini 1.5 Pro (Generación de Copywriting)
               │
               ▼ (Retorno de JSON Estructurado)
[ Cliente Web (Vercel) ] ➔ Renderizado e interacción del usuario

Para garantizar la viabilidad económica y la escalabilidad del sistema en entornos de producción, el backend implementa una estrategia de Model Routing en dos fases:

Fase 1 (Clasificación Lógica - Gemini 1.5 Flash): Evalúa el historial cronológico de mensajes. Actúa como un filtro booleano rápido para identificar si la conversación realmente está congelada (SITUACION_DE_ALERTA) o si ya ha concluido/espera respuesta interna (SIN_ACCION). Si no requiere alerta, el flujo se interrumpe inmediatamente.

Fase 2 (Copywriting Premium - Gemini 1.5 Pro): Solo se invoca si la Fase 1 da luz verde. Este modelo avanzado procesa los detalles complejos del presupuesto (importes, materiales, objeciones) para redactar una propuesta de seguimiento contextualizada y empática, forzando la salida en formato JSON nativo mediante Structured Outputs.

Costo Operativo Cero en Reposo ($0/m): Al estar desplegado sobre infraestructuras 100% serverless (Vercel para el estático y AWS Lambda para el cómputo), el coste de mantenimiento del software es nulo mientras no reciba tráfico.

Seguridad de Credenciales (Zero Client Exposure): La clave de la API de Google nunca viaja ni se almacena en el navegador del usuario. El backend en AWS actúa como un proxy seguro, protegiendo los secretos mediante variables de entorno cifradas en la infraestructura cloud.

Mitigación de Errores de CORS: Configuración manual de cabeceras HTTP de control de acceso (Access-Control-Allow-Origin: "*") en el controlador de AWS Lambda, permitiendo la comunicación fluida y segura entre dominios cruzados.

Agnóstico del Entorno (BYOK Ready): El código fuente está completamente desacoplado del aprovisionamiento de cuentas, facilitando un modelo Bring Your Own Key donde cada despliegue o cliente puede aislar sus costes inyectando su propia clave.

Configuración e Instalación Local / Cloud
1. Requisitos Previos
Cuenta en AWS (Capa gratuita disponible).

Cuenta en Google AI Studio para la obtención de una API Key (Plan gratuito o de desarrollo).

Entorno local con Python 3.12 y pip configurados.

2. Despliegue del Backend (AWS Lambda)
Instala las dependencias del SDK oficial unificado de Google en la carpeta del backend de tu entorno local:

Bash
cd backend
pip install google-genai -t .
Comprime el archivo lambda_function.py junto con las carpetas generadas por pip en un archivo .zip.

Sube el paquete a tu función AWS Lambda (Runtime: Python 3.12).

En la configuración de AWS Lambda, aumenta el Timeout general a 30 segundos y añade la siguiente Variable de Entorno:

GEMINI_API_KEY = [Tu clave secreta de Google AI Studio]

Habilita una Function URL pública con autenticación de tipo NONE.

3. Configuración del Frontend
Abre el archivo frontend/script.js.

Sustituye el valor de la constante LAMBDA_URL por la URL pública que te proporcionó tu función de AWS Lambda en el paso anterior:

JavaScript
const LAMBDA_URL = "[https://tu-url-de-lambda.on.aws/](https://tu-url-de-lambda.on.aws/)";
Despliega la carpeta frontend en Vercel de manera estática.

 Licencia
Este proyecto está bajo la Licencia MIT. Consulta el archivo para más detalles.