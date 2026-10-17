// Metadata travels with the content so history restoration cannot reuse another page's title.
(function () {
    'use strict';
    let current = null;
    let lastManualLocation = null;
    function updateTag(selector, attribute, key, value) {
        let node = document.head.querySelector(selector);
        if (!node) {
            node = document.createElement(key === 'canonical' ? 'link' : 'meta');
            if (key === 'canonical') node.rel = 'canonical';
            else node.setAttribute(attribute, key);
            document.head.appendChild(node);
        }
        node.setAttribute(key === 'canonical' ? 'href' : 'content', value);
    }
    function applyMetadata() {
        const state = document.querySelector('#body_main [data-st-page-metadata]');
        if (!state) return;
        try { current = JSON.parse(state.textContent); } catch (_) { return; }
        document.title = current.title;
        updateTag('meta[name="description"]', 'name', 'description', current.description);
        updateTag('meta[name="robots"]', 'name', 'robots', current.robots);
        if (current.public) {
            updateTag('link[rel="canonical"]', 'rel', 'canonical', current.canonical);
            const og = {title: current.title, description: current.description, url: current.canonical, image: current.image, 'image:alt': current.image_alt};
            Object.entries(og).forEach(([key, value]) => updateTag('meta[property="og:' + key + '"]', 'property', 'og:' + key, value));
            const twitter = {title: current.title, description: current.description, image: current.image, 'image:alt': current.image_alt};
            Object.entries(twitter).forEach(([key, value]) => updateTag('meta[name="twitter:' + key + '"]', 'name', 'twitter:' + key, value));
        } else {
            document.head.querySelectorAll('link[rel="canonical"], meta[property^="og:"], meta[name^="twitter:"]').forEach(node => node.remove());
        }
        document.head.querySelectorAll('[data-st-schema]').forEach(node => node.remove());
        if (current.structured_data.length) {
            const schema = document.createElement('script');
            schema.type = 'application/ld+json';
            schema.setAttribute('data-st-schema', '');
            schema.textContent = JSON.stringify(current.structured_data);
            document.head.appendChild(schema);
        }
    }
    function pageView() {
        if (!current) return;
        // Compare the actual navigation path; opening/dismissing a modal is not a page view.
        const location = window.location.origin + window.location.pathname + window.location.search;
        if (lastManualLocation === location) return;
        lastManualLocation = location;
        if (!current.public || !current.manual_page_views || typeof window.gtag !== 'function') return;
        const safeLocation = new URL(current.canonical);
        const parameters = new URLSearchParams(window.location.search);
        ['utm_source', 'utm_medium', 'utm_campaign', 'utm_content', 'utm_term'].forEach(key => {
            const value = parameters.get(key);
            if (value && /^[a-z0-9_-]{1,100}$/i.test(value)) safeLocation.searchParams.set(key, value);
        });
        window.gtag('event', 'page_view', {page_title: current.title, page_location: safeLocation.href});
    }
    document.addEventListener('DOMContentLoaded', function () { applyMetadata(); pageView(); });
    document.addEventListener('htmx:afterSwap', function (event) {
        if (event.detail.target.id !== 'body_main') return;
        applyMetadata();
    });
    document.addEventListener('htmx:afterSettle', function (event) {
        if (event.detail.target.id === 'body_main') pageView();
    });
    // Some HTMX versions push the URL after afterSettle; count only once it changes.
    ['htmx:pushedIntoHistory', 'htmx:replacedInHistory'].forEach(function (name) {
        document.addEventListener(name, function () { applyMetadata(); pageView(); });
    });
    document.addEventListener('htmx:historyRestore', function () { applyMetadata(); pageView(); });
    document.addEventListener('click', async function (event) {
        const share = event.target.closest('[data-share-link]');
        if (share && current) {
            try {
                await navigator.clipboard.writeText(current.canonical);
                share.parentElement.querySelector('[role="status"]').textContent = 'Link copied.';
            } catch (_) {
                window.prompt('Copy this link:', current.canonical);
            }
            if (typeof window.gtag === 'function') window.gtag('event', 'share_click', {page_path: new URL(current.canonical).pathname});
        }
        const link = event.target.closest('a[href]');
        if (!link || !current || !current.public || typeof window.gtag !== 'function') return;
        const destination = new URL(link.href, window.location.href);
        const allowed = new Set(['rsvp_click', 'community_link_click']);
        let action = link.dataset.trackEvent;
        if (!action && ['discord.gg', 'discord.com'].includes(destination.hostname)) action = 'community_link_click';
        if (!allowed.has(action)) return;
        const data = {page_path: new URL(current.canonical).pathname, link_domain: destination.hostname};
        if (/^\d+$/.test(link.dataset.eventId || '')) data.event_id = link.dataset.eventId;
        window.gtag('event', action, data);
    });
}());
