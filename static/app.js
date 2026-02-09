const btn = document.getElementById('btn-hablar'); 
const mouth = document.getElementById('mouth-img');
const eyes = document.getElementById('eyes-img');
const statusText = document.getElementById('status');
const avatarContainer = document.getElementById('avatar-container');

// --- RECONOCIMIENTO DE VOZ (STT) ---
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'es-MX';
recognition.continuous = true;      // Mantenemos abierto hasta que el usuario decida
recognition.interimResults = true;  // Permite ver resultados parciales

let isListening = false;
let finalTranscript = '';

function parpadear() {
    // Usamos la imagen eyes_closed.png que trajo el Git
    eyes.style.opacity = "1";
    setTimeout(() => { eyes.style.opacity = "0"; }, 150);
    setTimeout(parpadear, Math.random() * 4000 + 2000);
}
parpadear();

// --- MAPEO DE BOCAS (Para las nuevas imágenes del Git) ---
const mouthMap = { 
    'a': 'A', 'á': 'A', 'e': 'E', 'é': 'E', 'i': 'I', 'í': 'I',
    'o': 'O', 'ó': 'O', 'u': 'O', 'ú': 'O',
    'f': 'F_V', 'v': 'F_V', 'm': 'M_P_B', 'p': 'M_P_B', 'b': 'M_P_B',
    'n': 'N_D', 'd': 'N_D', 'l': 'N_D', 't': 'N_D', 's': 'N_D', 'r': 'N_D'
};

/**
 * Limpia el formato Markdown para que la síntesis de voz no lea los símbolos
 */
function cleanMarkdown(text) {
    return text
        .replace(/(\*\*|__)(.*?)\1/g, '$2')          // Negritas
        .replace(/(\*|_)(.*?)\1/g, '$2')             // Cursivas
        .replace(/#+\s?(.*)/g, '$1')                 // Títulos (#)
        .replace(/`{1,3}(.*?)`{1,3}/g, '$1')         // Código (backticks)
        .replace(/\[(.*?)\]\(.*?\)/g, '$1')          // Enlaces [texto](url) -> texto
        .replace(/(\r\n|\n|\r)/gm, " ")               // Saltos de línea por espacios
        .trim();
}

// --- ANIMACIÓN SINCRONIZADA CON EL AUDIO REAL ---
function animarBocaSincronizada(texto, audio) {
    let currentLetter = 0;
    const interval = setInterval(() => {
        // Si el audio se detiene o termina, volvemos a neutral
        if (audio.paused || audio.ended) {
            mouth.src = "/avatar/mouth_neutral.png";
            clearInterval(interval);
            return;
        }

        const char = texto[currentLetter]?.toLowerCase();
        // Cambiamos la imagen de la boca según la letra
        const mouthSuffix = mouthMap[char] || 'neutral';
        mouth.src = `/avatar/mouth_${mouthSuffix}.png`;
        
        currentLetter = (currentLetter + 1) % texto.length;
    }, 75); // 75ms es el tiempo ideal para la velocidad 0.85 que pusimos
}

// --- MANEJO DEL BOTÓN ---
btn.onclick = () => {
    if (!isListening) {
        // --- PRIMER CLIC: INICIAR ---
        if (synthesis.speaking) synthesis.cancel(); // Silenciar si estaba hablando
        
        finalTranscript = '';
        recognition.start();
        isListening = true;
        
        btn.innerText = 'Escuchando... 🟥';
        btn.classList.add('active'); // Por si quieres darle estilo CSS
        statusText.innerText = "Maleón te escucha atentamente...";
    } else {
        recognition.stop();
        isListening = false;
        
        btn.innerText = 'PULSAR PARA HABLAR';
        btn.classList.remove('active');
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

        const utterance = new SpeechSynthesisUtterance(data.reply);
        utterance.lang = 'es-MX';
        
        utterance.onstart = () => {
            statusText.innerText = "Maleón respondiendo...";
            animarBocaSincronizada(textoLimpio);
        };

        utterance.onend = () => {
            statusText.innerText = "Esperando interacción...";
            mouth.src = "/avatar/mouth_neutral.png";
        };

        // 4. ¡A darle! Reproducimos el audio de Google
        audio.play();

    } catch (error) {
        console.error("Error:", error);
        statusText.innerText = "Error de conexión.";
        btn.innerText = 'PULSAR PARA HABLAR';
    }
}