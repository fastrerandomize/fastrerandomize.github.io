(() => {
  const audio = document.getElementById('kernels-audio');
  if (!audio) return;
  const panel = audio.closest('.audio-panel');
  const speed = document.getElementById('audio-speed');
  const status = document.getElementById('audio-status');
  let pendingStart = null;

  const clearStatus = () => {
    status.textContent = '';
    status.hidden = true;
  };
  const showError = () => {
    status.textContent = 'Use the audio controls to play, or download the MP3. The transcript is also available below.';
    status.hidden = false;
  };
  const seek = () => {
    if (pendingStart === null || audio.readyState < 1) return;
    audio.currentTime = Math.max(0, Math.min(pendingStart, audio.duration));
    pendingStart = null;
  };

  speed.closest('label').hidden = false;
  speed.addEventListener('change', () => {
    audio.playbackRate = Number(speed.value);
  });
  audio.addEventListener('loadedmetadata', seek);
  audio.addEventListener('error', showError);
  audio.addEventListener('playing', clearStatus);

  panel.querySelectorAll('[data-audio-start]').forEach(button => {
    button.hidden = false;
    button.addEventListener('click', () => {
      clearStatus();
      pendingStart = Number(button.dataset.audioStart);
      seek();
      // Call play in the click handler so mobile browsers retain the user gesture.
      audio.play().catch(showError);
    });
  });
})();
