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
