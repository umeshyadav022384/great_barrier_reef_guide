// ============================================
// STATE
// ============================================
let sessionId = localStorage.getItem('sessionId') || generateSessionId();
let isRecording = false;
let mediaRecorder = null;
let audioChunks = [];
let backendUrl = 'http://127.0.0.1:8000';
let isProcessing = false;
let speechRecognition = null;

// ============================================
// DOM REFS
// ============================================
const backgroundLayer = document.getElementById('background-layer');
const locationName = document.getElementById('location-name');
const inventoryText = document.getElementById('inventory-text');
const messagesContainer = document.getElementById('messages-container');
const chipsContainer = document.getElementById('chips-container');
const micButton = document.getElementById('mic-button');
const recordingStatus = document.getElementById('recording-status');
const textInput = document.getElementById('text-input');
const sendButton = document.getElementById('send-button');
const audioPlayer = document.getElementById('audio-player');
const resetBtn = document.getElementById('reset-btn');

// ============================================
// SESSION
// ============================================
function generateSessionId() {
    let id = localStorage.getItem('sessionId');
    if (!id) {
        id = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
        localStorage.setItem('sessionId', id);
    }
    return id;
}

// ============================================
// MESSAGES
// ============================================
function addMessage(text, type = 'bot') {
    console.log('📝 Adding message:', text ? text.substring(0, 30) : 'null');
    if (!text) return;
    
    const div = document.createElement('div');
    div.className = `message ${type}`;

    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = type === 'bot' ? '🤖' : '👤';

    const bubble = document.createElement('div');
    bubble.className = 'bubble';

    const p = document.createElement('p');
    p.textContent = text;

    const time = document.createElement('span');
    time.className = 'time';
    time.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    bubble.appendChild(p);
    bubble.appendChild(time);
    div.appendChild(avatar);
    div.appendChild(bubble);

    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    console.log('✅ Message added, total:', messagesContainer.children.length);
}

function showTyping(show) {
    let indicator = document.getElementById('typing-indicator');
    if (show) {
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'typing-indicator';
            indicator.className = 'typing-indicator active';
            indicator.innerHTML = `
                <div class="avatar">🤖</div>
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
            `;
            messagesContainer.appendChild(indicator);
        }
        indicator.classList.add('active');
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    } else if (indicator) {
        indicator.classList.remove('active');
        setTimeout(() => indicator.remove(), 400);
    }
}

// ============================================
// BROWSER VOICE SUPPORT
// ============================================
function initBrowserVoice() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        console.warn('Browser microphone support is not available.');
        recordingStatus.textContent = '⚠️ Microphone unavailable';
        return false;
    }

    return true;
}

function speakText(text) {
    if (!text || typeof window.speechSynthesis === 'undefined') return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = 'en-US';
    utterance.rate = 1;
    window.speechSynthesis.speak(utterance);
}

function playAudio(audioUrl) {
    if (!audioUrl) return;

    let fullUrl = audioUrl;
    if (audioUrl.startsWith('/')) {
        fullUrl = `${backendUrl}${audioUrl}`;
    }

    audioPlayer.src = fullUrl;
    audioPlayer.load();
    
    setTimeout(() => {
        audioPlayer.play().catch(e => console.log('Audio play:', e.message));
    }, 300);
}

// ============================================
// SEND MESSAGE
// ============================================
async function sendMessage(text = null, audioBase64 = null) {
    if (isProcessing) return;
    isProcessing = true;

    const isVoice = audioBase64 !== null && audioBase64 !== '';

    showTyping(true);
    micButton.disabled = true;
    textInput.disabled = true;
    sendButton.disabled = true;

    try {
        let url = `${backendUrl}/voice-chat?session_id=${sessionId}`;
        if (text) url += `&text=${encodeURIComponent(text)}`;

        console.log('📤 Sending to:', url);

        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ audio_data: audioBase64 || '' })
        });

        if (!response.ok) throw new Error(`HTTP ${response.status}`);

        const data = await response.json();
        console.log('📦 Response:', data);
        
        showTyping(false);
        
        // ✅ CRITICAL: Add bot message
        if (data.text) {
            addMessage(data.text, 'bot');
        } else {
            addMessage('(No response received)', 'bot');
        }
        
        // Update UI
        updateUI(data, isVoice);

    } catch (error) {
        console.error('❌ Error:', error);
        showTyping(false);
        addMessage('❌ Sorry, something went wrong.', 'bot');
    }

    isProcessing = false;
    micButton.disabled = false;
    textInput.disabled = false;
    sendButton.disabled = false;
    textInput.focus();
}

// ============================================
// UPDATE UI
// ============================================
function updateUI(data, isVoice = false) {
    console.log('🔄 Updating UI');

    // Background
    if (data.current_room) {
        const bgImage = `../public/images/${data.current_room}.jpg`;
        backgroundLayer.style.backgroundImage = `url('${bgImage}')`;
        backgroundLayer.style.backgroundSize = 'cover';
        backgroundLayer.style.backgroundPosition = 'center';
    }

    // Location
    if (data.current_room) {
        const locationNames = {
            'dive_boat': 'Expedition Dive Boat',
            'reef_flats': 'Shallow Reef Flats',
            'reef_wall': 'Deep Outer Reef Wall'
        };
        locationName.textContent = locationNames[data.current_room] || data.current_room;
    }

    // Inventory
    if (data.inventory !== undefined) {
        if (data.inventory && data.inventory.length > 0) {
            inventoryText.textContent = data.inventory.join(', ');
            inventoryText.className = 'info-value';
        } else {
            inventoryText.textContent = 'None';
            inventoryText.className = 'info-value empty';
        }
    }

    // Chips
    updateChips(data.context_chips);

    // Audio
    if (data.audio_url && isVoice) {
        setTimeout(() => playAudio(data.audio_url), 400);
    } else if (data.text) {
        setTimeout(() => speakText(data.text), 300);
    }

    // Reset recording status
    recordingStatus.textContent = '🎤 Click mic or press Space to speak';
    micButton.classList.remove('recording');
}

// ============================================
// UPDATE CHIPS
// ============================================
function normalizeChipCommand(chipText) {
    const cleaned = (chipText || '')
        .replace(/[⚓🏝️☀️🔒🌊]/g, '')
        .replace(/\s+/g, ' ')
        .trim();

    const normalized = cleaned.toLowerCase();

    if (normalized.includes('gear locker')) return 'Check the gear locker';
    if (normalized.includes('reef flats') && normalized.includes('go to')) return 'Go to Reef Flats';
    if (normalized.includes('weather')) return 'Check weather conditions';
    if (normalized.includes('dive boat')) return 'Go to Dive Boat';
    if (normalized.includes('deep outer reef wall') || normalized.includes('deep wall') || normalized.includes('reef wall')) return 'Go to Deep Wall';
    if (normalized.includes('clownfish')) return 'Tell me about clownfish';
    if (normalized.includes('sharks')) return 'Tell me about sharks';
    if (normalized.includes('dive limit')) return 'Calculate my dive limit';

    return cleaned;
}

function updateChips(chips) {
    if (!chipsContainer) return;
    
    chipsContainer.innerHTML = '';
    
    const defaultChips = ['⚓ Check Gear Locker', '🏝️ Go to Reef Flats', '☀️ Check Weather'];
    const chipList = (chips && chips.length > 0) ? chips : defaultChips;
    
    chipList.forEach(function(chipText) {
        const btn = document.createElement('button');
        btn.className = 'chip';
        const isLocked = chipText.includes('🔒');
        if (isLocked) {
            btn.classList.add('locked');
        }
        btn.textContent = chipText;
        btn.onclick = function() {
            const command = normalizeChipCommand(chipText);
            addMessage(chipText, 'user');

            if (isLocked) {
                const fallback = chipText.toLowerCase().includes('deep wall')
                    ? 'Check the gear locker to unlock the deep reef wall'
                    : 'That option is not available yet.';
                sendMessage(fallback);
                return;
            }

            sendMessage(command);
        };
        chipsContainer.appendChild(btn);
    });
}

// ============================================
// TEXT INPUT
// ============================================
function handleTextInput() {
    const text = textInput.value.trim();
    if (!text || isProcessing) return;
    addMessage(text, 'user');
    textInput.value = '';
    sendMessage(text);
}

// ============================================
// VOICE RECORDING
// ============================================
async function startRecording() {
    if (isProcessing) return;

    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
        audioChunks = [];

        mediaRecorder.ondataavailable = function(event) {
            if (event.data.size > 0) audioChunks.push(event.data);
        };

        mediaRecorder.onstop = async function() {
            const tracks = stream.getTracks();
            tracks.forEach(function(track) { track.stop(); });

            if (audioChunks.length === 0) {
                recordingStatus.textContent = '⚠️ No audio detected';
                micButton.classList.remove('recording');
                return;
            }

            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            if (audioBlob.size < 300) {
                recordingStatus.textContent = '⚠️ Audio too short. Try speaking a little longer.';
                micButton.classList.remove('recording');
                return;
            }

            recordingStatus.textContent = '🔄 Sending voice message...';
            const reader = new FileReader();
            reader.onloadend = async function() {
                const base64Audio = reader.result.split(',')[1];
                addMessage('🎤 (Voice input)', 'user');
                await sendMessage(null, base64Audio);
            };
            reader.readAsDataURL(audioBlob);
        };

        mediaRecorder.start(1000);
        isRecording = true;
        recordingStatus.textContent = '🔴 Recording... Speak now!';
        micButton.classList.add('recording');

        setTimeout(function() {
            if (mediaRecorder && mediaRecorder.state === 'recording') stopRecording();
        }, 12000);

    } catch (error) {
        console.error('Microphone error:', error);
        recordingStatus.textContent = '❌ Microphone access denied';
        micButton.classList.remove('recording');
        addMessage('⚠️ Microphone access was denied. Please allow microphone access and try again.', 'bot');
    }
}

function stopRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
        isRecording = false;
    } else {
        isRecording = false;
        micButton.classList.remove('recording');
        recordingStatus.textContent = '🎤 Click mic or press Space to speak';
    }
}

// ============================================
// EVENT LISTENERS
// ============================================
micButton.addEventListener('click', function() {
    if (isRecording) stopRecording();
    else startRecording();
});

sendButton.addEventListener('click', handleTextInput);

textInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        e.preventDefault();
        handleTextInput();
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === ' ' && document.activeElement !== textInput && !isProcessing) {
        e.preventDefault();
        micButton.click();
    }
});

resetBtn.addEventListener('click', function() {
    localStorage.removeItem('sessionId');
    sessionId = generateSessionId();
    messagesContainer.innerHTML = '';
    addMessage('🔄 Session reset! Welcome back!', 'bot');
    inventoryText.textContent = 'None';
    inventoryText.className = 'info-value empty';
    locationName.textContent = 'Expedition Dive Boat';
    backgroundLayer.style.backgroundImage = "url('../public/images/dive_boat.jpg')";
    recordingStatus.textContent = '🎤 Click mic or press Space to speak';
    micButton.classList.remove('recording');
    updateChips([]);
});

// ============================================
// INITIALIZE
// ============================================
console.log('🌊 Great Barrier Reef Voice Guide');
console.log('📱 Session ID:', sessionId);

// Add welcome message
addMessage('Welcome aboard! You\'re on the expedition dive boat. The Great Barrier Reef awaits! Check the gear locker or head to the reef flats.', 'bot');

// Initialize chips
updateChips([]);
initBrowserVoice();

async function checkBackend() {
    try {
        const res = await fetch(`${backendUrl}/health`);
        if (res.ok) console.log('✅ Backend is healthy');
        else console.warn('⚠️ Backend health check failed');
    } catch (error) {
        console.warn('⚠️ Backend not reachable on http://localhost:8000');
        addMessage('⚠️ Backend not running. Please start the server.', 'bot');
    }
}
checkBackend();

// Hide loading screen
setTimeout(function() {
    const loading = document.getElementById('loading-screen');
    if (loading) loading.classList.add('hidden');
}, 500);