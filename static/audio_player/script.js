function previousAudio() {
    // Implement logic for fetching and playing the previous audio
    alert("Go to previous audio book.");
}

function togglePlayPause() {
    const audioPlayer = document.getElementById("custom-audio-player");
    if (audioPlayer.paused) {
        audioPlayer.play();
    } else {
        audioPlayer.pause();
    }
}

function nextAudio() {
    // Implement logic for fetching and playing the next audio
    alert("Go to next audio book.");
}
