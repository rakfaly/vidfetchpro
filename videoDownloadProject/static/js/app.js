const root = document.documentElement;
const themeToggle = document.getElementById('themeToggle');
const themeLabel = document.querySelector('.theme-label');

const setTheme = (mode) => {
  if (mode === 'dark') {
    root.classList.add('dark');
    if (themeLabel) {
      themeLabel.textContent = 'Light';
    }
    localStorage.setItem('theme', 'dark');
  } else {
    root.classList.remove('dark');
    if (themeLabel) {
      themeLabel.textContent = 'Dark';
    }
    localStorage.setItem('theme', 'light');
  }
};

const savedTheme = localStorage.getItem('theme');
setTheme(savedTheme === 'dark' ? 'dark' : 'light');

if (themeToggle) {
  themeToggle.addEventListener('click', () => {
    const isDark = root.classList.contains('dark');
    setTheme(isDark ? 'light' : 'dark');
  });
}

const progressBar = document.querySelector('[data-progress]');
const progressText = document.querySelector('[data-progress-text]');
const elapsedText = document.querySelector('[data-elapsed]');
const etaText = document.querySelector('[data-eta]');

if (progressBar && progressText && elapsedText && etaText) {
  let progress = 65;
  let elapsed = 138;
  let eta = 34;

  const tick = () => {
    progress = Math.min(progress + 0.4, 100);
    elapsed += 1;
    eta = Math.max(0, Math.round(eta - 0.3));

    progressBar.style.width = `${progress}%`;
    progressText.textContent = `${Math.round(progress)}%`;

    const elapsedMin = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const elapsedSec = String(elapsed % 60).padStart(2, '0');
    elapsedText.textContent = `${elapsedMin}:${elapsedSec}`;

    const etaMin = String(Math.floor(eta / 60)).padStart(2, '0');
    const etaSec = String(eta % 60).padStart(2, '0');
    etaText.textContent = `${etaMin}:${etaSec}`;
  };

  setInterval(tick, 1200);
}
