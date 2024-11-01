function previousAudio() {
    // Logic for previous audio book
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
    // Logic for next audio book
    alert("Go to next audio book.");
}
