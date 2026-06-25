/**
 * Статический API для GitHub Pages — перехват fetch без бэкенда.
 * Подключать сразу после site-config.js.
 */
(function () {
    'use strict';

    if (!window.SITE_CONFIG || !window.SITE_CONFIG.isStaticMode) {
        return;
    }

    var basePath = window.SITE_CONFIG.basePath || '';
    var dataUrl = 'data/site.json';
    var dataPromise = null;
    var favKey = 'vseprost_static_favorites';
    var cartKey = 'vseprost_static_cart';

    function loadData() {
        if (!dataPromise) {
            dataPromise = fetch(dataUrl, { cache: 'no-store' })
                .then(function (r) {
                    if (!r.ok) throw new Error('Не удалось загрузить data/site.json');
                    return r.json();
                });
        }
        return dataPromise;
    }

    function jsonResponse(body, status) {
        return new Response(JSON.stringify(body), {
            status: status || 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    function parseApiPath(url) {
        try {
            var u = new URL(url, window.location.origin);
            var path = u.pathname;
            var apiIdx = path.indexOf('/api');
            if (apiIdx === -1) return null;
            return {
                path: path.slice(apiIdx + 4) || '/',
                search: u.searchParams
            };
        } catch (e) {
            return null;
        }
    }

    function getFavorites() {
        try {
            return JSON.parse(localStorage.getItem(favKey) || '{"problems":[],"solutions":[]}');
        } catch (e) {
            return { problems: [], solutions: [] };
        }
    }

    function saveFavorites(f) {
        localStorage.setItem(favKey, JSON.stringify(f));
    }

    function getCart() {
        try {
            return JSON.parse(localStorage.getItem(cartKey) || '[]');
        } catch (e) {
            return [];
        }
    }

    function saveCart(items) {
        localStorage.setItem(cartKey, JSON.stringify(items));
    }

    function filterProblems(list, params) {
        var search = (params.get('search') || '').trim().toLowerCase();
        var category = params.get('category');
        var topic = params.get('topic');
        var hashtags = params.get('hashtags');
        var sort = params.get('sort') || 'default';
        var limit = parseInt(params.get('limit') || '20', 10);
        var offset = parseInt(params.get('offset') || '0', 10);
        var fav = getFavorites();

        var out = list.filter(function (p) {
            if (search && !(p.Name || '').toLowerCase().includes(search) &&
                !(p.Describe || '').toLowerCase().includes(search)) {
                return false;
            }
            if (category && String(p.Category) !== String(category)) return false;
            if (topic && String(p.Topic) !== String(topic)) return false;
            if (hashtags) {
                var ids = hashtags.split(',').map(function (x) { return parseInt(x, 10); });
                var pIds = (p.Hashtags || []).map(function (h) { return h.ID; });
                if (!ids.every(function (id) { return pIds.indexOf(id) !== -1; })) return false;
            }
            return true;
        });

        if (sort === 'popular') {
            out.sort(function (a, b) { return (b.Show || 0) - (a.Show || 0); });
        } else if (sort === 'new') {
            out.sort(function (a, b) { return (b.ID || 0) - (a.ID || 0); });
        }

        out = out.map(function (p) {
            var copy = Object.assign({}, p);
            copy.IsFavourite = fav.problems.indexOf(p.ID) !== -1;
            return copy;
        });

        var slice = out.slice(offset, offset + limit);
        var hasFilters = !!(search || category || topic || hashtags);
        if (hasFilters) {
            return { problems: slice, hasMore: offset + limit < out.length };
        }
        return { list: slice, hasMore: offset + limit < out.length, raw: out };
    }

    function filterSolutions(list, params) {
        var search = (params.get('search') || '').trim().toLowerCase();
        var category = params.get('category');
        var hashtags = params.get('hashtags');
        var limit = parseInt(params.get('limit') || '20', 10);
        var offset = parseInt(params.get('offset') || '0', 10);
        var fav = getFavorites();

        var out = list.filter(function (s) {
            if (search && !(s.Name || '').toLowerCase().includes(search) &&
                !(s.Describe || '').toLowerCase().includes(search)) {
                return false;
            }
            if (category) {
                var probs = s.Problems || [];
                if (!probs.some(function (p) { return String(p.ID) === String(category); })) {
                    return false;
                }
            }
            return true;
        });

        out = out.map(function (s) {
            var copy = Object.assign({}, s);
            copy.IsFavourite = fav.solutions.indexOf(s.ID) !== -1;
            return copy;
        });

        var slice = out.slice(offset, offset + limit);
        return { solutions: slice, hasMore: offset + limit < out.length };
    }

    function handleApi(url, init) {
        var parsed = parseApiPath(url);
        if (!parsed) return null;

        var method = ((init && init.method) || 'GET').toUpperCase();
        var path = parsed.path.replace(/\/$/, '') || '/';
        var params = parsed.search;

        return loadData().then(function (data) {
            var fav = getFavorites();
            var cart = getCart();

            if (method === 'GET' && path === '/categories') {
                return jsonResponse(data.categories);
            }
            if (method === 'GET' && path === '/topics') {
                return jsonResponse(data.topics);
            }
            if (method === 'GET' && path === '/hashtags') {
                var q = (params.get('q') || '').trim().toLowerCase();
                if (q.length < 2) return jsonResponse([]);
                var tags = data.hashtags.filter(function (h) {
                    return (h.Name || '').toLowerCase().indexOf(q) !== -1;
                }).slice(0, 20);
                return jsonResponse(tags);
            }
            if (method === 'GET' && path === '/problems') {
                var pf = filterProblems(data.problems, params);
                if (pf.problems) return jsonResponse(pf);
                if (params.toString()) return jsonResponse({ problems: pf.list });
                return jsonResponse(pf.list);
            }
            if (method === 'GET' && path === '/problems/favorites') {
                var ids = fav.problems;
                var items = data.problems.filter(function (p) { return ids.indexOf(p.ID) !== -1; });
                return jsonResponse({ problems: items });
            }
            if (method === 'GET' && path === '/solutions') {
                return jsonResponse(filterSolutions(data.solutions, params));
            }
            if (method === 'GET' && path === '/solutions/favorites') {
                var sids = fav.solutions;
                var sitems = data.solutions.filter(function (s) { return sids.indexOf(s.ID) !== -1; });
                return jsonResponse({ solutions: sitems });
            }
            if (method === 'GET' && path === '/cart/count') {
                return jsonResponse({ count: cart.length });
            }
            if (method === 'GET' && path === '/notifications/count') {
                return jsonResponse({ count: 0 });
            }
            if (method === 'GET' && path === '/cart') {
                var cartItems = cart.map(function (id) {
                    var s = data.solutions.find(function (x) { return x.ID === id; });
                    return s ? { SolutionID: id, Image: s.Image, Name: s.Name, Price: s.Price } : null;
                }).filter(Boolean);
                return jsonResponse(cartItems);
            }

            var problemMatch = path.match(/^\/problems\/(\d+)$/);
            if (method === 'GET' && problemMatch) {
                var pd = data.problems_detail[problemMatch[1]];
                if (!pd) return jsonResponse({ error: 'Не найдено' }, 404);
                var prob = Object.assign({}, pd.problem);
                prob.IsFavourite = fav.problems.indexOf(prob.ID) !== -1;
                return jsonResponse({ problem: prob });
            }

            var solutionMatch = path.match(/^\/solutions\/(\d+)$/);
            if (method === 'GET' && solutionMatch) {
                var sd = data.solutions_detail[solutionMatch[1]];
                if (!sd) return jsonResponse({ error: 'Не найдено' }, 404);
                var sol = Object.assign({}, sd.solution);
                sol.IsFavourite = fav.solutions.indexOf(sol.ID) !== -1;
                return jsonResponse({ solution: sol });
            }

            var problemToggleMatch = path.match(/^\/problems\/(\d+)\/toggle-favourite$/);
            if (method === 'POST' && problemToggleMatch) {
                var ptid = parseInt(problemToggleMatch[1], 10);
                var ptidx = fav.problems.indexOf(ptid);
                if (ptidx === -1) fav.problems.push(ptid); else fav.problems.splice(ptidx, 1);
                saveFavorites(fav);
                return jsonResponse({ is_favourite: ptidx === -1 });
            }

            var solutionToggleMatch = path.match(/^\/solutions\/(\d+)\/toggle-favourite$/);
            if (method === 'POST' && solutionToggleMatch) {
                var stid = parseInt(solutionToggleMatch[1], 10);
                var stidx = fav.solutions.indexOf(stid);
                if (stidx === -1) fav.solutions.push(stid); else fav.solutions.splice(stidx, 1);
                saveFavorites(fav);
                return jsonResponse({ is_favourite: stidx === -1 });
            }

            if (method === 'POST' && path.match(/^\/cart\/\d+$/)) {
                var cid = parseInt(path.split('/').pop(), 10);
                var cidx = cart.indexOf(cid);
                if (cidx === -1) cart.push(cid); else cart.splice(cidx, 1);
                saveCart(cart);
                return jsonResponse({ success: true, in_cart: cidx === -1 });
            }

            if (method === 'GET' && path.match(/^\/cart\/\d+$/)) {
                var checkId = parseInt(path.split('/').pop(), 10);
                return jsonResponse({ in_cart: cart.indexOf(checkId) !== -1 });
            }

            if (path === '/login' || path === '/register' || path === '/validate-token' ||
                path === '/refreshToken' || path === '/forgot-password' || path === '/reset-password') {
                return jsonResponse({
                    message: 'Авторизация недоступна в демо на GitHub Pages. Запустите проект локально с Flask.'
                }, 401);
            }

            if (method === 'GET') {
                return jsonResponse([], 200);
            }

            return jsonResponse({ message: 'Недоступно в статическом режиме' }, 403);
        });
    }

    var originalFetch = window.fetch.bind(window);
    window.fetch = function (input, init) {
        var url = typeof input === 'string' ? input : (input && input.url) || '';
        if (url.indexOf('/api') !== -1) {
            var handled = handleApi(url, init);
            if (handled) return handled;
        }
        return originalFetch(input, init);
    };

    window.STATIC_API = { loadData: loadData, getFavorites: getFavorites, getCart: getCart };
})();
