document.getElementById('analyzerForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const submitBtn = document.getElementById('submitBtn');
    const resultBox = document.getElementById('resultBox');
    const resultFlag = document.getElementById('resultFlag');

    submitBtn.innerText = "Procesando con IA...";
    submitBtn.disabled = true;
    resultBox.style.display = "none";

    const LAMBDA_URL = "https://h3xkovdplj64egbetyhv7q46um0kxjej.lambda-url.eu-north-1.on.aws/";

    const payload = {
        client_name: document.getElementById('clientName').value,
        business_name: document.getElementById('businessName').value,
        days_since_last_reply: parseInt(document.getElementById('days').value),
        budget_summary: document.getElementById('budget').value,
        thread_content: document.getElementById('thread').value
    };

    try {
        const response = await fetch(LAMBDA_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        // Lambda devuelve el JSON dentro de .body como string — parseamos dos veces
        const raw = await response.json();
        const data = typeof raw.body === 'string' ? JSON.parse(raw.body) : raw;

        const isAlert = data.classification === "SITUACION_DE_ALERTA";

        resultFlag.className = "result-flag " + (isAlert ? "is-alert" : "is-clear");
        document.getElementById('resultStatus').innerText = isAlert
            ? "Situación de alerta detectada"
            : "Sin acción requerida";

        const resultNote = document.getElementById('resultNote');
        const emailContent = document.getElementById('emailContent');

        if (isAlert && data.follow_up_email) {
            resultNote.innerText = "El cliente ha roto una promesa de respuesta o mostró interés real sin continuar.";
            emailContent.style.display = "block";
            document.getElementById('mailSubject').innerText = data.follow_up_email.subject;
            document.getElementById('mailBody').innerText = data.follow_up_email.body;
        } else {
            resultNote.innerText = "No se detectan señales claras de abandono. No se ha redactado correo de seguimiento.";
            emailContent.style.display = "none";
        }

        resultBox.style.display = "block";
    } catch (error) {
        alert("Error al conectar con el servidor: " + error.message);
    } finally {
        submitBtn.innerText = "Analizar Conversación";
        submitBtn.disabled = false;
    }
});
