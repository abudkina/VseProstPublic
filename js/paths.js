/**
 * URL-хелперы для GitHub Pages и локального Flask.
 */
(function () {
    'use strict';

    var cfg = window.SITE_CONFIG || {};

    function inHtmlDir() {
        return /\/html\//.test(location.pathname);
    }

    function problemUrl(id) {
        if (cfg.isStaticMode) {
            return (inHtmlDir() ? '' : 'html/') + 'problem.html?id=' + id;
        }
        return '/problem/' + id;
    }

    function solutionUrl(id) {
        if (cfg.isStaticMode) {
            return (inHtmlDir() ? '' : 'html/') + 'solution.html?id=' + id;
        }
        return '/solution/' + id;
    }

    window.PATHS = {
        problem: problemUrl,
        solution: solutionUrl,
        home: function () {
            return /\/html\//.test(location.pathname) ? '../' : './';
        }
    };
})();
