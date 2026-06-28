document.querySelectorAll('.flash').forEach((flash) => {
  setTimeout(() => {
    flash.classList.add('fade-out');
    setTimeout(() => flash.remove(), 400);
  }, 3200);
});


const passwordInput = document.getElementById('passwordInput');
const togglePassword = document.getElementById('togglePassword');

if (passwordInput && togglePassword) {
  togglePassword.addEventListener('click', () => {
    const isHidden = passwordInput.type === 'password';
    passwordInput.type = isHidden ? 'text' : 'password';
    togglePassword.textContent = isHidden ? '🙈' : '👁';
    togglePassword.setAttribute('aria-label', isHidden ? 'Sembunyikan password' : 'Tampilkan password');
  });
}
