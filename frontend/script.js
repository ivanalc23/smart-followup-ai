document.getElementById('analyzerForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const submitBtn = document.getElementById('submitBtn');
    const resultBox = document.getElementById('resultBox');
    
    submitBtn.innerText = "Procesando con IA...";
    submitBtn.disabled = true;
    resultBox.style.display = "none";

    // URL de tu AWS Lambda (La obtendrás en el Paso 4)
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

        const data = await response.json();

        resultBox.className = "result " + (data.classification === "SITUACION_DE_ALERTA" ? "alert" : "no-action");
        document.getElementById('resultStatus').innerText = `Estado detectado: ${data.classification}`;
        
        if (data.classification === "SITUACION_DE_ALERTA" && data.follow_up_email) {
            document.getElementById('emailContent').style.display = "block";
            document.getElementById('mailSubject').innerText = data.follow_up_email.subject;
            document.getElementById('mailBody').innerText = data.follow_up_email.body;
        } else {
            document.getElementById('emailContent').style.display = "none";
            document.getElementById('resultStatus').innerText += " (No se requiere enviar correo de seguimiento)";
        }
        
        resultBox.style.display = "block";
    } catch (error) {
        alert("Error al conectar con el servidor: " + error.message);
    } finally {
        submitBtn.innerText = "Analizar Conversación";
        submitBtn.disabled = false;
    }
});