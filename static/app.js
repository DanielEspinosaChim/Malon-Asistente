const btn = document.getElementById('btn-hablar'); 
const mouth = document.getElementById('mouth-img');
const eyes = document.getElementById('eyes-img');
const statusText = document.getElementById('status');
const avatarContainer = document.getElementById('avatar-container');

// --- RECONOCIMIENTO DE VOZ (STT) ---
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'es-MX';
recognition.continuous = true;
recognition.interimResults = true;

let isListening = false;
let finalTranscript = '';

// --- LÓGICA DE PARPADEO ---
function parpadear() {
    eyes.style.opacity = "1";
    setTimeout(() => { eyes.style.opacity = "0"; }, 150);
    setTimeout(parpadear, Math.random() * 4000 + 2000);
}
parpadear();

// --- MAPEO DE BOCAS ---
const mouthMap = { 
    'a': 'A', 'á': 'A', 'e': 'E', 'é': 'E', 'i': 'I', 'í': 'I',
    'o': 'O', 'ó': 'O', 'u': 'O', 'ú': 'O',
    'f': 'F_V', 'v': 'F_V', 'm': 'M_P_B', 'p': 'M_P_B', 'b': 'M_P_B',
    'n': 'N_D', 'd': 'N_D', 'l': 'N_D', 't': 'N_D', 's': 'N_D', 'r': 'N_D'
};

// --- ANIMACIÓN SINCRONIZADA CON AUDIO REAL ---
function animarBocaSincronizada(texto, audio) {
    let currentLetter = 0;
    const interval = setInterval(() => {
        if (audio.paused || audio.ended) {
            mouth.src = "/avatar/mouth_neutral.png";
            clearInterval(interval);
            return;
        }

        const char = texto[currentLetter]?.toLowerCase();
        const mouthSuffix = mouthMap[char] || 'neutral';
        mouth.src = `/avatar/mouth_${mouthSuffix}.png`;

        currentLetter = (currentLetter + 1) % texto.length;
    }, 75);
}

// --- MANEJO DEL BOTÓN ---
btn.onclick = () => {
    if (!isListening) {
        finalTranscript = '';
        recognition.start();
        isListening = true;

        btn.innerText = 'PULSAR PARA HABLAR 🟥';
        statusText.innerText = "Maleón te escucha atentamente...";
    } else {
        recognition.stop();
        isListening = false;

        btn.innerText = 'PULSAR PARA HABLAR';
        statusText.innerText = "Procesando mensaje...";
    }
};

recognition.onresult = (event) => {
    let interimTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
            finalTranscript += event.results[i][0].transcript;
        } else {
            interimTranscript += event.results[i][0].transcript;
        }
    }
    statusText.innerText = "Diciendo: " + (finalTranscript + interimTranscript);
};

recognition.onend = () => {
    if (!isListening && finalTranscript.trim() !== '') {
        enviarAlBackend(finalTranscript);
    }
};

// --- ENVÍO AL BACKEND Y REPRODUCCIÓN DE AUDIO ---
async function enviarAlBackend(texto) {
    statusText.innerText = "Maleón está pensando...";
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: texto })
        });

        const data = await response.json();

        const textoLimpio = data.reply.replace(/[^\wáéíóúñ\s]/gi, '');

        const audio = new Audio(data.audio_url);

        audio.onplay = () => {
            statusText.innerText = "Maleón respondiendo...";
            animarBocaSincronizada(textoLimpio, audio);
        };

        audio.onended = () => {
            statusText.innerText = "Esperando interacción...";
            mouth.src = "/avatar/mouth_neutral.png";
        };

        audio.play();

    } catch (error) {
        console.error("Error:", error);
        statusText.innerText = "¡Ay mare! Falló la conexión.";
        btn.innerText = 'PULSAR PARA HABLAR';
    }
}
