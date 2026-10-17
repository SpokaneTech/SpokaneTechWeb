// Enhance native horizontal scrolling without changing card links or requiring a library.
(function () {
    function updateCarousel(track) {
        const controls = track.closest('section').querySelector('.st-carousel-controls');
        const maximum = track.scrollWidth - track.clientWidth;
        controls.hidden = maximum <= 1;
        controls.querySelector('[data-carousel-scroll="-1"]').disabled = track.scrollLeft <= 1;
        controls.querySelector('[data-carousel-scroll="1"]').disabled = track.scrollLeft >= maximum - 1;
    }

    function updateAll() {
        document.querySelectorAll('[data-carousel]').forEach(updateCarousel);
    }

    function cardStep(track) {
        return track.querySelector('.st-group-card, .st-event-card, .st-blog-card').getBoundingClientRect().width
            + parseFloat(getComputedStyle(track).columnGap);
    }

    function scrollOptions(left) {
        return {left: left, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'};
    }

    document.addEventListener('click', function (event) {
        const button = event.target.closest('[data-carousel-scroll]');
        if (!button) return;
        const track = document.getElementById(button.getAttribute('aria-controls'));
        const step = cardStep(track);
        const visibleCards = Math.max(1, Math.floor(track.clientWidth / step));
        track.scrollBy(scrollOptions(Number(button.dataset.carouselScroll) * visibleCards * step));
    });

    document.addEventListener('keydown', function (event) {
        const track = event.target;
        if (!track.matches('[data-carousel]')) return;
        if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') {
            event.preventDefault();
            track.scrollBy(scrollOptions((event.key === 'ArrowLeft' ? -1 : 1) * cardStep(track)));
        } else if (event.key === 'Home' || event.key === 'End') {
            event.preventDefault();
            track.scrollTo(scrollOptions(event.key === 'Home' ? 0 : track.scrollWidth));
        }
    });

    document.addEventListener('scroll', function (event) {
        if (event.target instanceof Element && event.target.matches('[data-carousel]')) {
            updateCarousel(event.target);
        }
    }, true);
    document.addEventListener('htmx:load', updateAll);
    document.addEventListener('htmx:historyRestore', updateAll);
    window.addEventListener('resize', updateAll);
    window.addEventListener('pageshow', updateAll);
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', updateAll);
    } else {
        updateAll();
    }
})();
