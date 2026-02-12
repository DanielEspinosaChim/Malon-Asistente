const btn = document.getElementById('btn-hablar'); 
const mouth = document.getElementById('mouth-img');
const eyes = document.getElementById('eyes-img');
const avatarContainer = document.getElementById('avatar-container');
const chatHistory = document.getElementById('chat-history');
let sessionId = crypto.randomUUID();

// --- LÓGICA DE HISTORIAL ---
function addMessageToHistory(text, sender) {
    const msgDiv = document.createElement('div');
    msgDiv.classList.add('message');
    msgDiv.classList.add(sender === 'user' ? 'user-message' : 'bot-message');
    msgDiv.innerHTML = text; // innerHTML para soportar enlaces de reportes
    chatHistory.appendChild(msgDiv);
    
    // Auto-scroll al final
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showInterimUserMessage(text) {
    let tempBubble = document.getElementById('temp-user-bubble');
    if (!tempBubble) {
        tempBubble = document.createElement('div');
        tempBubble.id = 'temp-user-bubble';
        tempBubble.classList.add('message', 'user-message');
        tempBubble.style.opacity = '0.6'; // Apariencia de borrador
        tempBubble.style.fontStyle = 'italic';
        chatHistory.appendChild(tempBubble);
    }
    tempBubble.innerText = text;
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeInterimUserMessage() {
    const tempBubble = document.getElementById('temp-user-bubble');
    if (tempBubble) tempBubble.remove();
}

function showTypingIndicator() {
    const typingDiv = document.createElement('div');
    typingDiv.id = 'typing-indicator-container';
    typingDiv.classList.add('message', 'bot-message');
    typingDiv.innerHTML = `
        <div class="typing-indicator">
            <span></span>
            <span></span>
            <span></span>
        </div>
    `;
    chatHistory.appendChild(typingDiv);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typing-indicator-container');
    if (indicator) indicator.remove();
}

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
        } catch (e) {
            console.error("Error al iniciar reconocimiento:", e);
        }
    } else {
        recognition.stop();
        isListening = false;
        avatarContainer.classList.remove('listening'); // Quitar efecto visual
        btn.innerText = 'PULSAR PARA HABLAR';
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
    // Mostrar lo que se está diciendo en tiempo real
    if (finalTranscript || interimTranscript) {
        showInterimUserMessage(finalTranscript + interimTranscript);
    }
};

recognition.onend = () => {
    avatarContainer.classList.remove('listening'); // Por seguridad
    
    // Quitamos la burbuja temporal
    removeInterimUserMessage();

    if (!isListening && finalTranscript.trim() !== '') {
        const textoAEnviar = finalTranscript;
        finalTranscript = ''; // Limpiamos inmediatamente para evitar reenvíos
        
        // Agregar al historial visual (ya fijo)
        addMessageToHistory(textoAEnviar, 'user');

        // Obtenemos la hora actual del usuario
        const ahora = new Date();
        const horaStr = ahora.toLocaleTimeString('es-MX', { hour: '2-digit', minute: '2-digit' });
        
        enviarAlBackend(textoAEnviar, horaStr);
    }
};

// --- ENVÍO AL BACKEND Y REPRODUCCIÓN DE AUDIO ---
async function enviarAlBackend(texto, hora = null) {
    
    // Mostramos indicador de escritura
    showTypingIndicator();

    // Creamos un nuevo controlador para esta petición
    abortController = new AbortController();

    try {
        const bodyData = {
            text: texto,
            session_id: sessionId
        };

        if (hora) bodyData.time = hora;

        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyData),
            signal: abortController.signal
        });

        const data = await response.json();
        abortController = null; // Petición terminada con éxito

        // Quitamos el indicador de escritura
        removeTypingIndicator();

        if (!data || !data.reply) {
            throw new Error("Respuesta del servidor incompleta");
        }

        // Agregar al historial visual
        addMessageToHistory(data.reply, 'bot');

        const textoLimpio = data.reply.replace(/[^\wáéíóúñ\s]/gi, '');

        // Detenemos cualquier audio previo por si acaso
        if (currentAudio) currentAudio.pause();
        
        if (data.audio_url) {
            currentAudio = new Audio();
            
            currentAudio.oncanplaythrough = () => {
                currentAudio.play().catch(e => console.error("Error al reproducir:", e));
            };

            currentAudio.onplay = () => {
                animarBocaSincronizada(textoLimpio, currentAudio);
            };

            currentAudio.onerror = (e) => {
                console.error("Error cargando audio:", e);
            };

            currentAudio.onended = () => {
                mouth.src = "/avatar/mouth_neutral.png";
                currentAudio = null;
            };

            currentAudio.src = data.audio_url; // Dispara la carga
        }

    } catch (error) {
        removeTypingIndicator();
        if (error.name === 'AbortError') {
            console.log("Petición cancelada porque el usuario inició otra acción.");
        } else {
            console.error("Error:", error);
            btn.innerText = 'PULSAR PARA HABLAR';
        }
    } finally {
        abortController = null;
    }
}