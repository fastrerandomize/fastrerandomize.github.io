(() => {
  const audio = document.getElementById('kernels-audio');
  if (!audio) return;
  const speed = document.getElementById('audio-speed');
  const status = document.getElementById('audio-status');

  const clearStatus = () => {
    status.textContent = '';
    status.hidden = true;
  };
  const showError = () => {
    status.textContent = 'Use the audio controls to play, or download the MP3.';
    status.hidden = false;
  };

  speed.closest('label').hidden = false;
  speed.addEventListener('change', () => {
    audio.playbackRate = Number(speed.value);
  });
  audio.addEventListener('error', showError);
  audio.addEventListener('playing', clearStatus);
})();
