
const themeToggle = document.getElementById('theme-toggle');
const themeIcon = document.querySelector('.theme-icon');

// Check for saved theme preference or default to 'light'
const currentTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', currentTheme);
updateThemeIcon(currentTheme);

if (themeToggle) {
    themeToggle.addEventListener('click', function() {
        let theme = document.documentElement.getAttribute('data-theme');
        let newTheme = theme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeIcon(newTheme);
    });
}

// Mobile menu toggle
const mobileToggle = document.getElementById('mobile-menu-toggle');
const navLinks = document.querySelector('.nav-links');
if (mobileToggle && navLinks) {
    mobileToggle.addEventListener('click', function() {
        navLinks.classList.toggle('open');
    });
}

function updateThemeIcon(theme) {
    if (themeIcon) {
        themeIcon.textContent = theme === 'dark' ? '☀️' : '🌙';
    }
}

// Flash message auto-dismiss
document.addEventListener('DOMContentLoaded', function() {
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
});
