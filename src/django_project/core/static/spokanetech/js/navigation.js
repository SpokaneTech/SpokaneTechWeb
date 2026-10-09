// Keep Bootstrap navigation usable after an existing HTMX page transition.
document.addEventListener('htmx:afterSwap', function (event) {
    if (event.detail.target.id !== 'body_main') return;
    const menu = document.getElementById('navbarNav');
    if (menu.classList.contains('show')) {
        const toggle = document.querySelector('[aria-controls="navbarNav"]');
        toggle.focus();
        bootstrap.Collapse.getOrCreateInstance(menu, {toggle: false}).hide();
    }
});
