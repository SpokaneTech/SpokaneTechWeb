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

// Keep Bootstrap's dialog element connected when HTMX loads modal content.
document.addEventListener('htmx:beforeSwap', function (event) {
    const wrapper = event.detail.target;
    if (wrapper.id !== 'modal_wrapper' || !event.detail.shouldSwap) return;
    const current = wrapper.querySelector('.modal-dialog');
    const response = new DOMParser().parseFromString(event.detail.serverResponse, 'text/html');
    const incoming = response.querySelector('.modal-dialog');
    if (!current || !incoming) return;
    current.className = incoming.className;
    event.detail.target = current;
    event.detail.serverResponse = incoming.innerHTML;
});

// Wrap Tab at the dialog boundaries, including after dynamic content swaps.
document.addEventListener('keydown', function (event) {
    if (event.key !== 'Tab') return;
    const modal = event.target.closest('.st-modal.show');
    if (!modal) return;
    const controls = Array.from(modal.querySelectorAll('a[href], button, input, select, textarea, [tabindex]'))
        .filter(function (element) {
            return element.tabIndex >= 0 && !element.matches(':disabled') && element.getClientRects().length
                && getComputedStyle(element).visibility !== 'hidden';
        });
    if (!controls.length) return;
    const first = controls[0];
    const last = controls[controls.length - 1];
    if (event.shiftKey && (event.target === first || event.target === modal)) {
        event.preventDefault();
        last.focus();
    } else if (!event.shiftKey && event.target === last) {
        event.preventDefault();
        first.focus();
    }
});
