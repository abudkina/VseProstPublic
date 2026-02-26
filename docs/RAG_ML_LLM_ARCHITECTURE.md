# RAG, ML, LMM и смежные компоненты VseProst

Полное описание того, как устроены поиск, рекомендации, генерация изображений и зарезервированные настройки (Ollama).

---

## 1. Обзор компонентов

| Компонент | Назначение | Где используется |
|-----------|------------|-------------------|
| **RAG** | Семантический и гибридный поиск по проблемам/решениям | Поиск в API проблем и решений |
| **ML (embeddings)** | Векторизация текста, похожие сущности, рекомендации | Рекомендации, RAG-поиск |
| **LMM (CLIP)** | Поиск по изображениям и текст↔картинка | Режим `multimodal` поиска |
| **OpenAI API** | Генерация изображений (DALL-E 2/3) | Создание картинок для проблем/решений |
| **Ollama** | Локальный LLM (в коде не используется) | Только переменные в `.env` |

---

## 2. RAG (Retrieval-Augmented Generation)

В проекте RAG используется **только как retrieval**: поиск релевантных записей по запросу. Генерация текста LLM по найденным документам не реализована.

### 2.1 Режимы поиска (`search_mode`)

Единая точка входа — `logic/rag_search.py` → `search_with_rag()`.

| Режим | Описание | Реализация |
|-------|----------|-------------|
| `text` | Только текстовый поиск | SQL `LIKE` по `name` и `describe` (problem/solution) |
| `semantic` | Только семантика | Вектор запроса + косинусное сходство с `Embedding` в БД |
| `hybrid` | Текст + семантика (по умолчанию) | `hybrid_search()`: текст (вес 0.3) + семантика (0.7), объединение и сортировка |
| `multimodal` | Текст или картинка как запрос | CLIP: текст/изображение → вектор, сравнение с векторами картинок сущностей |

Режим передаётся в API через query-параметр `search_mode` (по умолчанию `hybrid`). Вызов идёт из:

- `logic/problem.py` — список проблем с фильтром по поиску
- `logic/solution.py` — список решений с фильтром по поиску

### 2.2 Поток данных RAG

1. Пользователь вводит запрос `search` в API проблем/решений.
2. Вызывается `search_with_rag(query=search, entity_type='problem'|'solution', search_mode=...)`.
3. В зависимости от режима:
   - **text**: выборка по `LIKE`, возврат списка `(id, 1.0)`.
   - **semantic**: запрос векторизуется той же моделью, что и сущности (`paraphrase-multilingual-MiniLM-L12-v2`), сравнение с векторами из таблицы `embedding`, порог `min_similarity=0.3`, возврат `(entity_id, score)`.
   - **hybrid**: отдельно текстовые совпадения и `semantic_search()`, объединение с весами 0.3/0.7, сортировка по комбинированному score.
   - **multimodal**: если запрос — текст, CLIP даёт текстовый вектор; если запрос — изображение, — вектор картинки; сравнение с векторами изображений сущностей (только сущности с заполненным `image`), при недоступности CLIP — fallback на `semantic_search`.
4. По списку `(entity_id, score)` строится итоговая выборка (фильтр `Problem.id.in_(rag_ids)` или аналог для решений). При пустом RAG используется fallback на текстовый `LIKE`.

### 2.3 Важные параметры

- **limit**: максимум результатов (в API передаётся `limit * 2` для последующей фильтрации).
- **exclude_ids**: ID, которые нужно исключить из выдачи.
- **min_similarity**: порог сходства в семантике (например 0.2 в hybrid, 0.3 в semantic).

---

## 3. ML: embeddings и рекомендации

### 3.1 Модель и библиотека

- **Библиотека**: `sentence-transformers` (`SentenceTransformer`).
- **Модель**: `paraphrase-multilingual-MiniLM-L12-v2` (Hugging Face).
  - Размерность вектора: **384** (константа `EMBEDDING_DIMENSION` в `logic/constants.py`).
  - Поддержка русского языка, размер модели ~420 MB.
- Загрузка один раз при первом обращении, хранится в глобальной переменной в `logic/recommendations.py` (`get_model()`).

### 3.2 Таблица Embedding (БД)

Таблица `embedding` (`logic/model.py`, класс `Embedding`):

| Поле | Тип | Описание |
|------|-----|----------|
| id | PK | Первичный ключ |
| entity_type | string | `'problem'` или `'solution'` |
| entity_id | int | ID записи в `problem` или `solution` |
| embedding_vector | JSON | Массив float (длина 384) |
| text_content | text | Исходный текст, по которому построен вектор |
| model_name | string | Имя модели (по умолчанию в коде — та же MiniLM) |
| created_date, modified_date | datetime | Время создания/обновления |

Уникальность: одна запись на пару `(entity_type, entity_id)`.

### 3.3 Когда создаётся embedding

- При первом запросе «похожих» или при семантическом поиске: если для сущности ещё нет вектора, он создаётся в `create_embedding()`.
- Текст для векторизации:
  - **problem**: `name` + `describe` + имена связанных `hashtags`.
  - **solution**: `name` + `describe`.
- Массовое создание: `batch_create_embeddings(entity_type, entity_ids=None, batch_size=10)` — для всех или выбранных problem/solution.

### 3.4 Косинусное сходство

В `logic/recommendations.py`: `cosine_similarity(vec1, vec2)` — обычная формула по numpy. Используется и в RAG (сравнение запроса с векторами), и в рекомендациях (сравнение векторов сущностей между собой).

### 3.5 Рекомендации для пользователя

- **Источник данных**: таблица `user_activity` (типы: `create`, `search`, `favorite`, `view`), сущности — problem/solution.
- **Функция**: `get_user_recommendations(user_id, entity_type, limit=20)` в `logic/recommendations.py`.
- Логика:
  - Берётся активность за последние 30 дней.
  - По каждой «взаимодействованной» сущности (до 10) вызывается `find_similar_entities()` (по косинусному сходству векторов из `Embedding`), порог сходства 0.3.
  - Если есть поисковые запросы, последний запрос векторизуется той же моделью и сравнивается со всеми embedding данного `entity_type`; сходство > 0.3 добавляет сущность в рекомендации.
- Константы в `logic/constants.py`: `RECOMMENDATION_DAYS_LOOKBACK = 30`, `RECOMMENDATION_SIMILARITY_THRESHOLD = 0.3`.

### 3.6 Отслеживание активности и User Knowledge

- При действиях пользователя вызывается `track_user_activity(user_id, activity_type, entity_type, entity_id, search_query)` — пишет в `user_activity`.
- После этого может вызываться `trigger_knowledge_update(user_id)` из `logic/user_knowledge.py`: обновляется профиль «персональных знаний» (таблица `user_knowledge`: топ категорий, хэштегов, топиков, поисковых слов, счётчики просмотров/избранного). Обновление не чаще раза в час (если не `force_update`).

---

## 4. LMM: мультимодальный поиск (CLIP)

### 4.1 Модель и назначение

- **Модель**: `openai/clip-vit-base-patch32` (Hugging Face `transformers`: `CLIPModel`, `CLIPProcessor`).
- **Назначение**: поиск по тексту или по изображению — запрос и картинки сущностей переводятся в общее векторное пространство, релевантность считается косинусным сходством.

### 4.2 Условия использования

- Нужны установленные `torch` и `transformers`; при их отсутствии в RAG выставляется `CLIP_AVAILABLE = False`, мультимодальный поиск недоступен (fallback на семантический по тексту).
- Устройство: `cuda` при наличии GPU, иначе `cpu`.
- В мультимодальном поиске участвуют только сущности (problem/solution) с заполненным полем `image` (и не дефолтным путём). Для каждой такой сущности изображение загружается с диска, прогоняется через CLIP, результат сравнивается с вектором запроса (текст или картинка).

### 4.3 Где вызывается

Режим `search_mode='multimodal'` в `search_with_rag()` → `multimodal_search()`. Если CLIP недоступен или сущностей с картинками нет, используется обычный семантический поиск по тексту.

---

## 5. Генерация изображений (OpenAI API, не LLM-чат)

Генерация картинок к проблемам/решениям идёт через **OpenAI-совместимый API** (DALL-E), не через текстовый LLM.

### 5.1 Конфигурация

- В `config.py`: `OPENAI_API_KEY`, `OPENAI_API_URL` (например `https://api.proxyapi.ru/openai/v1`).
- В `.env` задаются те же переменные.

### 5.2 Логика

- Файл: `logic/utils/image_search.py`, функция `generate_image_with_openai()`.
- Промпт: название сущности (`name`) + до 15 слов из описания (`description`), обрезка по лимиту символов (1000 для DALL-E 2, 4000 для DALL-E 3).
- Модели: `dall-e-2` (по умолчанию) или `dall-e-3`; размеры задаются в параметрах (например 256x256 для DALL-E 2).
- Ответ (base64 или URL) сохраняется: загрузка в Yandex Object Storage, в ответ возвращается публичная ссылка; при недоступности хранилища — fallback в локальную папку `uploads`.

Использование: API создания/редактирования проблем и решений (например `logic/image_generation.py` и эндпоинты генерации изображений), когда пользователь запрашивает автогенерацию картинки по названию/описанию.

---

## 6. Ollama (зарезервировано)

В `.env` есть переменные:

- `PREFER_LOCAL_LLM=false`
- `OLLAMA_BASE_URL=http://localhost:11434`
- `OLLAMA_MODEL=llama3`

В коде приложения эти переменные **нигде не читаются и не используются**. То есть локальный LLM (Ollama) в текущей реализации не подключён: ни для RAG-генерации ответов, ни для чата, ни для других функций. Настройки зарезервированы под возможное будущее использование (например, локальная генерация текста поверх RAG).

---

## 7. Зависимости (requirements.txt)

- **ML/RAG**: `sentence-transformers`, `numpy`, `transformers`, `torch`.
- **LMM (CLIP)**: те же `transformers`, `torch` (отдельного пакета для CLIP нет).
- **Генерация изображений**: `openai` (клиент для OpenAI-совместимого API).

---

## 8. Схема потока данных (кратко)

```
Пользовательский поиск (API problem/solution)
    → search_with_rag(search_mode= hybrid | text | semantic | multimodal)
        → text:     SQL LIKE
        → semantic: get_model().encode(query) → сравнение с Embedding.embedding_vector
        → hybrid:   text + semantic, веса 0.3 / 0.7
        → multimodal: CLIP(query) vs CLIP(images сущностей) или fallback semantic
    → список (entity_id, score) → фильтрация выборки

Рекомендации
    → user_activity (последние 30 дней)
    → find_similar_entities() по Embedding + cosine_similarity
    → + векторизация последнего search_query и сравнение с embedding
    → get_user_recommendations() возвращает список entity_id

Новая/обновлённая problem/solution
    → при необходимости create_embedding() (sentence-transformers)
    → запись в таблицу embedding

Генерация изображения
    → OpenAI API (DALL-E 2/3) по name + description
    → загрузка в Yandex Storage → ссылка в поле image
```

---

## 9. Константы и конфиг (сводка)

| Константа / переменная | Значение / место | Назначение |
|------------------------|------------------|------------|
| `DEFAULT_EMBEDDING_MODEL` | `paraphrase-multilingual-MiniLM-L12-v2` | Модель эмбеддингов (constants.py и recommendations.py) |
| `EMBEDDING_DIMENSION` | 384 | Размерность вектора |
| `RECOMMENDATION_DAYS_LOOKBACK` | 30 | Дней активности для рекомендаций |
| `RECOMMENDATION_SIMILARITY_THRESHOLD` | 0.3 | Минимальное сходство для рекомендации |
| `OPENAI_API_KEY`, `OPENAI_API_URL` | config / .env | Генерация изображений |
| `PREFER_LOCAL_LLM`, `OLLAMA_*` | только .env | Не используются в коде (Ollama зарезервирован) |

Если понадобится, можно вынести модель эмбеддингов или пороги в переменные окружения и описать их в этом же документе.
