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

    function assetUrl(path) {
        if (!path) return '';
        var p = String(path).replace(/\\/g, '/').trim();
        if (/^https?:\/\//i.test(p)) return p;
        if (p.startsWith('/')) p = p.slice(1);
        return (inHtmlDir() ? '../' : '') + p;
    }

    window.PATHS = {
        problem: problemUrl,
        solution: solutionUrl,
        asset: assetUrl,
        home: function () {
            return inHtmlDir() ? '../' : './';
        }
    };
    window.assetUrl = assetUrl;

    window.normalizeImageSrc = function (raw, fallback) {
        fallback = fallback || 'assets/images/Screenshot_4-ww78noDj9-transformed.png';
        var imageSrc = (raw || '').replace(/\\/g, '/').trim();
        if (!imageSrc || imageSrc === '../images/default.png') return assetUrl(fallback);
        if (/^https?:\/\//i.test(imageSrc)) return imageSrc;
        if (imageSrc.startsWith('../images/')) imageSrc = 'assets/images/' + imageSrc.slice(13);
        else if (imageSrc.startsWith('../assets/')) imageSrc = imageSrc.slice(3);
        else if (imageSrc.startsWith('/')) imageSrc = imageSrc.slice(1);
        return assetUrl(imageSrc);
    };
})();
