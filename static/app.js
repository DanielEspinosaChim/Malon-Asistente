const btn = document.getElementById('btn-hablar');
const mouth = document.getElementById('mouth-img');
const statusText = document.getElementById('status');

// Configuración de Voz (Browser side)
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
const synthesis = window.speechSynthesis;
recognition.lang = 'es-MX';

function animarBoca(texto) {
    const map = { 'a': 'A', 'e': 'E', 'i': 'I', 'o': 'O', 'u': 'O' };
    let i = 0;
    
    const interval = setInterval(() => {
        if (!synthesis.speaking) {
            mouth.src = "/avatar/mouth_neutral.png";
            clearInterval(interval);
            return;
        }
        const letra = texto[i]?.toLowerCase();
        const imgName = map[letra] || 'neutral';
        mouth.src = `/avatar/mouth_${imgName}.png`;
        i = (i + 1) % texto.length;
    }, 90);
}

btn.onclick = () => {
    recognition.start();
    statusText.innerText = "Maleón está escuchando...";
};

recognition.onresult = async (event) => {
    const userText = event.results[0][0].transcript;
    statusText.innerText = "Maleón está pensando...";

    // Enviamos el texto al backend FastAPI
    const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: userText })
    });
    
    const data = await response.json();

    // Hacemos que el navegador hable la respuesta
    const utterance = new SpeechSynthesisUtterance(data.reply);
    utterance.lang = 'es-MX';
    utterance.onstart = () => animarBoca(data.reply);
    
    synthesis.speak(utterance);
    statusText.innerText = "Maleón respondiendo...";
};