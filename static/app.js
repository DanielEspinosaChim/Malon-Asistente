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
let currentAudio = null; // Para controlar el audio actual
let abortController = null; // Para cancelar peticiones fetch pendientes

// --- LÓGICA DE PARPADEO ---
// ... (mismo código de parpadeo)
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
        if (!audio || audio.paused || audio.ended) {
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
    // Si hay audio sonando, lo detenemos
    if (currentAudio) {
        currentAudio.pause();
        currentAudio = null;
        mouth.src = "/avatar/mouth_neutral.png";
    }

    // Si hay una petición al backend pendiente, la cancelamos
    if (abortController) {
        abortController.abort();
        abortController = null;
    }

    if (!isListening) {
        finalTranscript = '';
        try {
            recognition.start();
            isListening = true;
            avatarContainer.classList.add('listening'); // Efecto visual
            btn.innerText = 'PULSAR PARA DETENER 🟥';
            statusText.innerText = "Maleón te escucha atentamente...";
        } catch (e) {
            console.error("Error al iniciar reconocimiento:", e);
        }
    } else {
        recognition.stop();
        isListening = false;
        avatarContainer.classList.remove('listening'); // Quitar efecto visual
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
    avatarContainer.classList.remove('listening'); // Por seguridad
    if (!isListening && finalTranscript.trim() !== '') {
        const textoAEnviar = finalTranscript;
        finalTranscript = ''; // Limpiamos inmediatamente para evitar reenvíos
        
        // Obtenemos la hora actual del usuario
        const ahora = new Date();
        const horaStr = ahora.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
        
        enviarAlBackend(textoAEnviar, horaStr);
    } else if (!isListening) {
        statusText.innerText = "Esperando interacción...";
    }
};

// --- ENVÍO AL BACKEND Y REPRODUCCIÓN DE AUDIO ---
async function enviarAlBackend(texto, hora = null) {
    statusText.innerText = "Maleón está pensando...";
    
    // Creamos un nuevo controlador para esta petición
    abortController = new AbortController();

    try {
        const bodyData = { text: texto };
        if (hora) bodyData.time = hora; // Enviamos la hora

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData),
            signal: abortController.signal
        });

        const data = await response.json();
        abortController = null; // Petición terminada con éxito

        if (!data || !data.reply) {
            throw new Error("Respuesta del servidor incompleta");
        }

        const textoLimpio = data.reply.replace(/[^\wáéíóúñ\s]/gi, '');

        // Detenemos cualquier audio previo por si acaso
        if (currentAudio) currentAudio.pause();
        
        if (data.audio_url) {
            currentAudio = new Audio();
            
            currentAudio.oncanplaythrough = () => {
                currentAudio.play().catch(e => console.error("Error al reproducir:", e));
            };

            currentAudio.onplay = () => {
                statusText.innerHTML = data.reply;
                animarBocaSincronizada(textoLimpio, currentAudio);
            };

            currentAudio.onerror = (e) => {
                console.error("Error cargando audio:", e);
                statusText.innerHTML = data.reply;
            };

            currentAudio.onended = () => {
                statusText.innerText = "Esperando interacción...";
                mouth.src = "/avatar/mouth_neutral.png";
                currentAudio = null;
            };

            currentAudio.src = data.audio_url; // Dispara la carga
        } else {
            // Si no hay audio, solo mostramos el texto
            statusText.innerHTML = data.reply;
            setTimeout(() => {
                if (!currentAudio) statusText.innerText = "Esperando interacción...";
            }, 5000);
        }

    } catch (error) {
        if (error.name === 'AbortError') {
            console.log("Petición cancelada porque el usuario inició otra acción.");
        } else {
            console.error("Error:", error);
            statusText.innerText = "¡Ay mare! Falló la conexión.";
            btn.innerText = 'PULSAR PARA HABLAR';
        }
    } finally {
        abortController = null;
    }
}
