// Enhance server-rendered event sections; both remain available without scripts.
(function () {
    function selectTab(container, activeTab) {
        container.querySelectorAll('[data-event-tab]').forEach(function (tab) {
            const selected = tab === activeTab;
            tab.setAttribute('aria-selected', String(selected));
            tab.tabIndex = selected ? 0 : -1;
            const panel = document.getElementById(tab.getAttribute('aria-controls'));
            panel.hidden = !selected;
        });
    }

    function initialize() {
        document.querySelectorAll('[data-event-tabs]').forEach(function (container) {
            const tabs = container.querySelectorAll('[data-event-tab]');
            const tablist = container.querySelector('.st-group-event-tabs');
            tablist.setAttribute('role', 'tablist');
            tablist.hidden = false;
            tabs.forEach(function (tab) {
                tab.setAttribute('role', 'tab');
                const panel = document.getElementById(tab.getAttribute('aria-controls'));
                panel.setAttribute('role', 'tabpanel');
                panel.setAttribute('aria-labelledby', tab.id);
                panel.tabIndex = 0;
            });
            selectTab(container, container.querySelector('[aria-selected="true"]') || tabs[0]);
        });
    }

    document.addEventListener('click', function (event) {
        const tab = event.target.closest('[data-event-tab]');
        if (tab) selectTab(tab.closest('[data-event-tabs]'), tab);
    });
    document.addEventListener('keydown', function (event) {
        const tab = event.target.closest('[data-event-tab]');
        if (!tab || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const container = tab.closest('[data-event-tabs]');
        const tabs = Array.from(container.querySelectorAll('[data-event-tab]'));
        const index = tabs.indexOf(tab);
        const nextIndex = event.key === 'Home' ? 0 : event.key === 'End' ? tabs.length - 1 :
            (index + (event.key === 'ArrowRight' ? 1 : -1) + tabs.length) % tabs.length;
        selectTab(container, tabs[nextIndex]);
        tabs[nextIndex].focus();
    });
    document.addEventListener('htmx:afterSwap', initialize);
    document.addEventListener('htmx:historyRestore', initialize);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})();
