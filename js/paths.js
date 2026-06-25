/**
 * URL-хелперы для GitHub Pages и локального Flask.
 */
(function () {
    'use strict';

    var cfg = window.SITE_CONFIG || {};

    function problemUrl(id) {
        if (cfg.isStaticMode) {
            return (cfg.basePath || '') + '/html/problem.html?id=' + id;
        }
        return '/problem/' + id;
    }

    function solutionUrl(id) {
        if (cfg.isStaticMode) {
            return (cfg.basePath || '') + '/html/solution.html?id=' + id;
        }
        return '/solution/' + id;
    }

    window.PATHS = {
        problem: problemUrl,
        solution: solutionUrl,
        home: function () { return (cfg.basePath || '') + '/'; }
    };
})();
