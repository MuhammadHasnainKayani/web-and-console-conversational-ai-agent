// Select elements
const micButton = document.getElementById("mic-button");
const chatBox = document.getElementById("chat-box");
const audioPlayer = document.getElementById("audio-player");

// Speech Recognition Setup
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.continuous = true;
recognition.interimResults = true;
recognition.lang = "en-US";

// Handle Microphone Button Click
let isRecording = false;
micButton.addEventListener("click", () => {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
});

// Start Recording
function startRecording() {
    isRecording = true;
    micButton.classList.add("recording");
    micButton.innerHTML = "🎙️ Listening...";
    recognition.start();
}

// Stop Recording
function stopRecording() {
    isRecording = false;
    micButton.classList.remove("recording");
    micButton.innerHTML = "🎤 Start Recording";
    recognition.stop();
}

// Process Transcriptions
recognition.onresult = (event) => {
    let transcript = "";
    for (let i = event.resultIndex; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript + " ";
    }
    updateChat(transcript, "user");

    // Simulate AI Response (Replace with backend call)
    setTimeout(() => {
        let botResponse = generateBotResponse(transcript);
        updateChat(botResponse, "bot");
        playTTS(botResponse);
    }, 1000);
};

// Update Chat UI
function updateChat(text, sender) {
    const message = document.createElement("div");
    message.classList.add("message", sender);
    message.innerText = text;
    chatBox.appendChild(message);
    chatBox.scrollTop = chatBox.scrollHeight;
}

// Simulated Bot Response (Replace with AI backend)
function generateBotResponse(userText) {
    if (userText.toLowerCase().includes("price")) {
        return "The price of a medium crown crust pizza is $12.99.";
    }
    return "I'm not sure, but I can check for you!";
}

// Play TTS Response
function playTTS(text) {
    const utterance = new SpeechSynthesisUtterance(text);
    speechSynthesis.speak(utterance);

    // Optional: Update UI when TTS plays
    utterance.onstart = () => micButton.innerHTML = "🔊 Speaking...";
    utterance.onend = () => micButton.innerHTML = "🎤 Start Recording";
}
