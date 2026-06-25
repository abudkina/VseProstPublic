/**
 * Конфиг для GitHub Pages: base path, статический режим без бэкенда.
 * Подключать первым скриптом в <head> (до CSS).
 */
(function () {
    'use strict';

    var staticRoots = {
        css: 1, js: 1, html: 1, assets: 1, fonts: 1, data: 1,
        uploads: 1, problem: 1, solution: 1, api: 1
    };

    var host = location.hostname;
    var isGitHubPages = host.endsWith('github.io');
    var isLocal = host === 'localhost' || host === '127.0.0.1';
    var basePath = '';

    if (isGitHubPages) {
        var parts = location.pathname.split('/').filter(Boolean);
        if (parts.length && !staticRoots[parts[0]]) {
            basePath = '/' + parts[0];
        }
        if (basePath) {
            var baseEl = document.createElement('base');
            baseEl.href = basePath + '/';
            document.head.insertBefore(baseEl, document.head.firstChild);
        }
    }

    window.SITE_CONFIG = {
        basePath: basePath,
        isGitHubPages: isGitHubPages,
        isStaticMode: isGitHubPages,
        isLocal: isLocal,
        siteUrl: isGitHubPages
            ? ('https://' + host + basePath)
            : location.origin,
        apiOrigin: location.origin
    };
})();
