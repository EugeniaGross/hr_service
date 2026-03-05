document.addEventListener('DOMContentLoaded', function() {
    const tabLink = document.querySelector('a[href="#general"]');
    if (tabLink) {
        tabLink.textContent = 'Основное';
    }
});