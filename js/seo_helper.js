// seo_helper.js
/**
 * SEO Helper - управление динамическими мета-тегами и хлебными крошками
 */

class SEOHelper {
    constructor() {
        this.baseUrl = window.location.origin;
    }

    /**
     * Обновляет meta-теги страницы динамически
     * @param {Object} metadata - объект с мета-данными
     */
    updateMetaTags(metadata) {
        const {
            title,
            description,
            keywords,
            canonical,
            ogTitle,
            ogDescription,
            ogImage,
            ogUrl,
            twitterTitle,
            twitterDescription,
            twitterImage,
            robots
        } = metadata;

        // Обновляем title
        if (title) {
            document.title = title;
            this._updateMetaTag('property', 'og:title', ogTitle || title);
            this._updateMetaTag('name', 'twitter:title', twitterTitle || title);
        }

        // Обновляем description
        if (description) {
            this._updateMetaTag('name', 'description', description);
            this._updateMetaTag('property', 'og:description', ogDescription || description);
            this._updateMetaTag('name', 'twitter:description', twitterDescription || description);
        }

        // Обновляем keywords
        if (keywords) {
            this._updateMetaTag('name', 'keywords', keywords);
        }

        // Обновляем canonical URL
        if (canonical) {
            this._updateCanonical(canonical);
        }

        // Обновляем Open Graph теги
        if (ogUrl) {
            this._updateMetaTag('property', 'og:url', ogUrl);
        }

        if (ogImage) {
            this._updateMetaTag('property', 'og:image', ogImage);
            this._updateMetaTag('name', 'twitter:image', twitterImage || ogImage);
        }

        // Обновляем robots мета-тег
        if (robots) {
            this._updateMetaTag('name', 'robots', robots);
        }

        // Отправляем событие для Google Analytics
        if (window.gtag) {
            gtag('event', 'page_view', {
                'page_title': title,
                'page_path': window.location.pathname
            });
        }

        // Отправляем событие для Яндекс.Метрики
        if (window.ym) {
            ym(106548955, 'hit', window.location.href, {
                title: title,
                referrer: document.referrer
            });
        }
    }

    /**
     * Обновляет или создает meta-тег
     * @private
     */
    _updateMetaTag(attribute, attributeValue, content) {
        let tag = document.querySelector(`meta[${attribute}="${attributeValue}"]`);
        
        if (!tag) {
            tag = document.createElement('meta');
            tag.setAttribute(attribute, attributeValue);
            document.head.appendChild(tag);
        }
        
        tag.setAttribute('content', content);
    }

    /**
     * Обновляет canonical URL
     * @private
     */
    _updateCanonical(canonicalUrl) {
        let link = document.querySelector('link[rel="canonical"]');
        
        if (!link) {
            link = document.createElement('link');
            link.setAttribute('rel', 'canonical');
            document.head.appendChild(link);
        }
        
        link.setAttribute('href', canonicalUrl);
    }

    /**
     * Обновляет Structured Data (JSON-LD)
     * @param {Object} schema - объект JSON-LD схемы
     * @param {string} id - ID для уникальности (опционально)
     */
    updateStructuredData(schema, id = 'seo-schema') {
        // Удаляем старую схему если есть
        const existingScript = document.getElementById(id);
        if (existingScript) {
            existingScript.remove();
        }

        // Создаем новую схему
        const script = document.createElement('script');
        script.type = 'application/ld+json';
        script.id = id;
        script.textContent = JSON.stringify(schema);
        document.head.appendChild(script);
    }

    /**
     * Создает и отображает хлебные крошки (breadcrumbs)
     * @param {Array<{name: string, url: string}>} items - элементы навигации
     * @param {string} containerId - ID контейнера для вставки
     */
    createBreadcrumbs(items, containerId = 'breadcrumbs') {
        let container = document.getElementById(containerId);
        
        if (!container) {
            container = document.createElement('nav');
            container.id = containerId;
            container.className = 'breadcrumbs';
            
            // Вставляем после header или в начало main
            const header = document.querySelector('header');
            const main = document.querySelector('main');
            
            if (header) {
                header.parentNode.insertBefore(container, header.nextSibling);
            } else if (main) {
                main.parentNode.insertBefore(container, main);
            } else {
                document.body.insertBefore(container, document.body.firstChild);
            }
        }

        // Очищаем контейнер
        container.innerHTML = '';

        // Добавляем Structured Data для breadcrumbs
        const breadcrumbSchema = {
            '@context': 'https://schema.org',
            '@type': 'BreadcrumbList',
            'itemListElement': items.map((item, index) => ({
                '@type': 'ListItem',
                'position': index + 1,
                'name': item.name,
                'item': this._normalizeUrl(item.url)
            }))
        };
        
        this.updateStructuredData(breadcrumbSchema, 'breadcrumb-schema');

        // Создаем HTML для хлебных крошек
        const nav = document.createElement('nav');
        nav.setAttribute('aria-label', 'breadcrumbs');
        nav.setAttribute('itemscope', '');
        nav.setAttribute('itemtype', 'https://schema.org/BreadcrumbList');

        items.forEach((item, index) => {
            const li = document.createElement('li');
            li.setAttribute('itemprop', 'itemListElement');
            li.setAttribute('itemscope', '');
            li.setAttribute('itemtype', 'https://schema.org/ListItem');

            if (index < items.length - 1) {
                // Не последний элемент
                const a = document.createElement('a');
                a.href = item.url;
                a.setAttribute('itemprop', 'item');
                a.textContent = item.name;
                
                li.appendChild(a);
                
                const span = document.createElement('span');
                span.className = 'separator';
                span.textContent = ' / ';
                
                container.appendChild(li);
                container.appendChild(span);
            } else {
                // Последний элемент
                li.className = 'current';
                li.setAttribute('itemprop', 'name');
                li.textContent = item.name;
                
                container.appendChild(li);
            }

            // Добавляем позицию для Structured Data
            const position = document.createElement('meta');
            position.setAttribute('itemprop', 'position');
            position.setAttribute('content', (index + 1).toString());
            li.appendChild(position);
        });

        container.appendChild(nav);
    }

    /**
     * Генерирует SEO-friendly URL slug
     * @param {string} text - текст для преобразования
     * @returns {string} - преобразованный slug
     */
    static generateSlug(text) {
        return text
            .toLowerCase()
            .trim()
            .replace(/[^\w\s-]/g, '') // Удаляем специальные символы
            .replace(/\s+/g, '-') // Заменяем пробелы на дефисы
            .replace(/-+/g, '-') // Заменяем множественные дефисы на один
            .replace(/^-+|-+$/g, ''); // Удаляем дефисы в начале и конце
    }

    /**
     * Нормализует URL
     * @private
     */
    _normalizeUrl(url) {
        if (url.startsWith('http')) {
            return url;
        }
        return this.baseUrl + (url.startsWith('/') ? url : '/' + url);
    }

    /**
     * Проверяет, индексируется ли страница
     * @returns {boolean}
     */
    isIndexable() {
        const robots = document.querySelector('meta[name="robots"]');
        if (!robots) return true;
        
        const content = robots.getAttribute('content');
        return content && content.includes('index');
    }

    /**
     * Добавляет rel="nofollow" для внешних ссылок
     */
    markExternalLinks() {
        const links = document.querySelectorAll('a[href^="http"]');
        const currentDomain = window.location.hostname;
        
        links.forEach(link => {
            const linkDomain = new URL(link.href).hostname;
            if (linkDomain !== currentDomain) {
                link.setAttribute('rel', 'nofollow noopener noreferrer');
                link.setAttribute('target', '_blank');
            }
        });
    }

    /**
     * Оптимизирует изображения для SEO
     */
    optimizeImages() {
        const images = document.querySelectorAll('img');
        images.forEach((img, index) => {
            // Добавляем alt текст если его нет
            if (!img.alt) {
                img.alt = `Изображение ${index + 1}`;
            }
            
            // Добавляем loading="lazy" для оптимизации производительности
            if (!img.loading) {
                img.loading = 'lazy';
            }
        });
    }

    /**
     * Уведомляет поисковики об обновлении страницы
     */
    notifySearchEngines() {
        // Проверяем Support для navigator.sendBeacon
        if (navigator.sendBeacon) {
            // Google
            navigator.sendBeacon(
                'https://www.google.com/ping?sitemap=' + 
                encodeURIComponent(this.baseUrl + '/sitemap.xml')
            );
            
            // Яндекс
            navigator.sendBeacon(
                'https://ping.yandex.ru/ping?' +
                'sitemap=' + encodeURIComponent(this.baseUrl + '/sitemap.xml')
            );
        }
    }
}

// Экспортируем для использования в других модулях
export default SEOHelper;
