const btn = document.getElementById('btn-hablar'); 
const mouth = document.getElementById('mouth-img');
const eyes = document.getElementById('eyes-img');
const statusText = document.getElementById('status');
const avatarContainer = document.getElementById('avatar-container');

// Configuración de Voz
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
const synthesis = window.speechSynthesis;
recognition.lang = 'es-MX';
recognition.continuous = true;      
recognition.interimResults = true;  

let isListening = false;
let finalTranscript = '';

// Lógica de Parpadeo
function parpadear() {
    eyes.style.opacity = "1";
    setTimeout(() => { eyes.style.opacity = "0"; }, 150);
    setTimeout(parpadear, Math.random() * 4000 + 2000);
}
parpadear();

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

function animarBocaSincronizada(texto) {
    let currentLetter = 0;
    const interval = setInterval(() => {
        if (!synthesis.speaking) {
            mouth.src = "/avatar/mouth_neutral.png";
            clearInterval(interval);
            return;
        }
        const char = texto[currentLetter]?.toLowerCase();
        mouth.src = `/avatar/mouth_${mouthMap[char] || 'neutral'}.png`;
        currentLetter = (currentLetter + 1) % texto.length;
    }, 80);
}

// MANEJO DEL BOTÓN (TOGGLE)
btn.onclick = () => {
    if (!isListening) {
        if (synthesis.speaking) synthesis.cancel();
        
        finalTranscript = '';
        recognition.start();
        isListening = true;
        
        btn.innerText = 'Escuchando... 🟥';
        btn.classList.add('active'); 
        avatarContainer.classList.add('active');
        statusText.innerText = "Maleón te escucha atentamente...";
    } else {
        recognition.stop();
        isListening = false;
        
        btn.innerText = 'Pulsar para hablar';
        btn.classList.remove('active');
        avatarContainer.classList.remove('active');
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

async function enviarAlBackend(texto) {
    statusText.innerText = "Maleón está pensando...";
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: texto })
        });
        
        const data = await response.json();
        
        // --- LIMPIEZA DE MARKDOWN PARA VOZ ---
        const textoParaVoz = cleanMarkdown(data.reply);
        
        // Limpiamos emojis y caracteres raros para la animación de la boca
        const textoParaBoca = textoParaVoz.replace(/[^\wáéíóúñ\s]/gi, '');

        const utterance = new SpeechSynthesisUtterance(textoParaVoz);
        utterance.lang = 'es-MX';
        
        utterance.onstart = () => {
            statusText.innerText = data.reply; // Mostramos el texto original (con Markdown si lo tiene)
            animarBocaSincronizada(textoParaBoca);
        };

        utterance.onend = () => {
            statusText.innerText = "Listo para conversar";
            mouth.src = "/avatar/mouth_neutral.png";
        };
        
        synthesis.speak(utterance);
    } catch (error) {
        console.error("Error:", error);
        statusText.innerText = "Error de conexión.";
        btn.innerText = 'Pulsar para hablar';
    }
}