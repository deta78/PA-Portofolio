const siteHeader = document.getElementById('siteHeader');
const menuToggle = document.getElementById('menuToggle');
const navMenu = document.getElementById('navMenu');
const navLinks = document.querySelectorAll('.nav-link');
const revealItems = document.querySelectorAll('.reveal');

function toggleHeaderStyle() {
  siteHeader.classList.toggle('scrolled', window.scrollY > 40);
}

function setActiveNav() {
  const sections = document.querySelectorAll('section[id]');
  const currentPosition = window.scrollY + 140;
  sections.forEach((section) => {
    const top = section.offsetTop;
    const height = section.offsetHeight;
    const id = section.getAttribute('id');
    if (currentPosition >= top && currentPosition < top + height) {
      navLinks.forEach((link) => {
        link.classList.toggle('active', link.getAttribute('href') === `#${id}`);
      });
    }
  });
}

window.addEventListener('scroll', () => {
  toggleHeaderStyle();
  setActiveNav();
});

menuToggle.addEventListener('click', () => {
  const isOpen = navMenu.classList.toggle('active');
  menuToggle.classList.toggle('active', isOpen);
});

navLinks.forEach((link) => {
  link.addEventListener('click', () => {
    navMenu.classList.remove('active');
    menuToggle.classList.remove('active');
  });
});

const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add('visible');
  });
}, { threshold: .15 });

revealItems.forEach((item) => revealObserver.observe(item));
toggleHeaderStyle();
setActiveNav();


document.querySelectorAll('.flash').forEach((flash) => {
  setTimeout(() => {
    flash.classList.add('fade-out');
    setTimeout(() => flash.remove(), 400);
  }, 3500);
});
