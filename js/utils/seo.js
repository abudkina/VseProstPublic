/**
 * SEO Utility Functions
 * Функции для динамического обновления SEO мета-тегов и структурированных данных
 */

/**
 * Обновляет SEO мета-теги на странице
 * @param {Object} options - Объект с данными для SEO
 * @param {string} options.title - Заголовок страницы
 * @param {string} options.description - Описание страницы
 * @param {string} options.image - URL изображения для Open Graph
 * @param {string} options.url - Канонический URL
 * @param {string} options.type - Тип контента (article, website)
 */
export function updateSEOMetaTags(options) {
    const {
        title,
        description,
        image,
        url,
        type = 'article'
    } = options;

    const baseUrl = window.location.origin;
    const fullUrl = url ? (url.startsWith('http') ? url : `${baseUrl}${url}`) : window.location.href;
    const fullImage = image ? (image.startsWith('http') ? image : `${baseUrl}${image}`) : `${baseUrl}/assets/og-image.png`;

    // Обновляем title
    if (title) {
        document.title = title;
        updateMetaTag('property', 'og:title', title);
        updateMetaTag('name', 'twitter:title', title);
    }

    // Обновляем description
    if (description) {
        updateMetaTag('name', 'description', description);
        updateMetaTag('property', 'og:description', description);
        updateMetaTag('name', 'twitter:description', description);
    }

    // Обновляем URL
    if (url) {
        updateMetaTag('rel', 'canonical', fullUrl);
        updateMetaTag('property', 'og:url', fullUrl);
        updateMetaTag('name', 'twitter:url', fullUrl);
    }

    // Обновляем изображение
    if (image) {
        updateMetaTag('property', 'og:image', fullImage);
        updateMetaTag('name', 'twitter:image', fullImage);
    }

    // Обновляем тип
    updateMetaTag('property', 'og:type', type);
}

/**
 * Обновляет или создает мета-тег
 * @param {string} attribute - Атрибут для поиска (name, property, rel)
 * @param {string} value - Значение атрибута
 * @param {string} content - Содержимое мета-тега
 */
function updateMetaTag(attribute, value, content) {
    let meta = document.querySelector(`meta[${attribute}="${value}"]`);
    
    if (!meta) {
        meta = document.createElement('meta');
        meta.setAttribute(attribute, value);
        document.head.appendChild(meta);
    }
    
    meta.setAttribute('content', content);
}

/**
 * Добавляет структурированные данные (JSON-LD) на страницу
 * @param {Object} structuredData - Объект со структурированными данными
 */
export function addStructuredData(structuredData) {
    // Удаляем существующие структурированные данные с таким же типом
    const existingScript = document.querySelector(`script[type="application/ld+json"][data-seo="true"]`);
    if (existingScript) {
        existingScript.remove();
    }

    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.setAttribute('data-seo', 'true');
    script.textContent = JSON.stringify(structuredData, null, 2);
    document.head.appendChild(script);
}

/**
 * Создает структурированные данные для проблемы (Question)
 * @param {Object} problem - Объект проблемы
 * @returns {Object} Структурированные данные в формате JSON-LD
 */
export function createProblemStructuredData(problem) {
    const baseUrl = window.location.origin;
    const problemUrl = `${baseUrl}/html/problem.html?id=${problem.ID}`;
    const imageUrl = problem.Image 
        ? (problem.Image.startsWith('http') ? problem.Image : `${baseUrl}${problem.Image}`)
        : `${baseUrl}/assets/og-image.png`;

    return {
        "@context": "https://schema.org",
        "@type": "Question",
        "name": problem.Name,
        "text": problem.Description || problem.Name,
        "dateCreated": problem.CreatedDate || new Date().toISOString(),
        "dateModified": problem.ModifiedDate || problem.CreatedDate || new Date().toISOString(),
        "author": {
            "@type": "Person",
            "name": problem.Creator?.User || "Пользователь"
        },
        "upvoteCount": problem.Favourite || 0,
        "answerCount": problem.Solutions?.length || 0,
        "image": imageUrl,
        "url": problemUrl
    };
}

/**
 * Создает структурированные данные для решения (Answer)
 * @param {Object} solution - Объект решения
 * @returns {Object} Структурированные данные в формате JSON-LD
 */
export function createSolutionStructuredData(solution) {
    const baseUrl = window.location.origin;
    const solutionUrl = `${baseUrl}/html/solution.html?id=${solution.ID}`;
    const imageUrl = solution.Image 
        ? (solution.Image.startsWith('http') ? solution.Image : `${baseUrl}${solution.Image}`)
        : `${baseUrl}/assets/og-image.png`;

    return {
        "@context": "https://schema.org",
        "@type": "Answer",
        "name": solution.Name,
        "text": solution.Details || solution.Name,
        "dateCreated": solution.CreatedDate || new Date().toISOString(),
        "dateModified": solution.ModifiedDate || solution.CreatedDate || new Date().toISOString(),
        "author": {
            "@type": "Person",
            "name": solution.Creator?.User || "Пользователь"
        },
        "upvoteCount": solution.Favourite || 0,
        "image": imageUrl,
        "url": solutionUrl,
        "aggregateRating": solution.Rating ? {
            "@type": "AggregateRating",
            "ratingValue": solution.Rating,
            "ratingCount": solution.RatingCount || 1
        } : undefined
    };
}

/**
 * Создает структурированные данные для списка (ItemList)
 * @param {Array} items - Массив элементов
 * @param {string} name - Название списка
 * @returns {Object} Структурированные данные в формате JSON-LD
 */
export function createItemListStructuredData(items, name) {
    const baseUrl = window.location.origin;
    
    return {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": name,
        "numberOfItems": items.length,
        "itemListElement": items.map((item, index) => ({
            "@type": "ListItem",
            "position": index + 1,
            "name": item.Name || item.name,
            "url": item.URL || `${baseUrl}${item.url}`
        }))
    };
}
