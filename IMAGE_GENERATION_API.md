# API генерации изображений через OpenAI DALL-E

## Описание

API для генерации изображений с использованием OpenAI DALL-E (DALL-E 2 или DALL-E 3) с автоматической загрузкой в Yandex Object Storage.

## Endpoints

### POST `/api/generate-image`

Генерация изображения по текстовому описанию.

**Требования:**
- Авторизация через JWT токен (заголовок `Authorization: Bearer <token>`)

**Тело запроса (JSON):**

```json
{
  "prompt": "красивый закат над морем",  // обязательное поле
  "description": "в стиле импрессионизма",  // опционально
  "model": "dall-e-2",  // опционально: "dall-e-2" или "dall-e-3", по умолчанию "dall-e-2"
  "size": "256x256",  // опционально, зависит от модели
  "response_format": "b64_json"  // опционально: "b64_json" или "url", по умолчанию "b64_json"
}
```

**Параметры:**

- `prompt` (обязательное) - текстовое описание изображения (1-4000 символов)
- `description` (опциональное) - дополнительное описание (1-4000 символов)
- `model` (опциональное) - модель генерации:
  - `dall-e-2` - более экономичная, быстрая (по умолчанию)
  - `dall-e-3` - более качественная, лучшая детализация
- `size` (опциональное) - размер изображения:
  - Для DALL-E 2: `256x256`, `512x512`, `1024x1024` (по умолчанию `256x256`)
  - Для DALL-E 3: `1024x1024`, `1792x1024`, `1024x1792` (по умолчанию `1024x1024`)
- `response_format` (опциональное) - формат ответа:
  - `b64_json` - base64-кодированные данные (по умолчанию)
  - `url` - URL временной ссылки на изображение

**Успешный ответ (200):**

```json
{
  "success": true,
  "image_url": "https://storage.yandexcloud.net/bucket-name/generated-images/abc123.png",
  "prompt": "красивый закат над морем",
  "model": "dall-e-2",
  "size": "256x256"
}
```

**Ошибки:**

- `400` - Неверные параметры запроса
- `401` - Не авторизован
- `500` - Ошибка генерации или загрузки изображения

### GET `/api/generate-image/info`

Получение информации о доступных моделях и параметрах генерации.

**Ответ (200):**

```json
{
  "models": {
    "dall-e-2": {
      "name": "DALL-E 2",
      "description": "Более экономичная модель, быстрая генерация",
      "sizes": ["256x256", "512x512", "1024x1024"],
      "max_prompt_length": 1000,
      "response_formats": ["b64_json", "url"]
    },
    "dall-e-3": {
      "name": "DALL-E 3",
      "description": "Более качественная модель, лучшая детализация",
      "sizes": ["1024x1024", "1792x1024", "1024x1792"],
      "max_prompt_length": 4000,
      "response_formats": ["b64_json", "url"],
      "quality_options": ["standard", "hd"]
    }
  },
  "defaults": {
    "model": "dall-e-2",
    "size": "256x256",
    "response_format": "b64_json"
  }
}
```

## Примеры использования

### JavaScript (Fetch API)

```javascript
// Генерация изображения
async function generateImage(prompt, description = null) {
  const response = await fetch('http://localhost:8080/api/generate-image', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${yourJwtToken}`
    },
    body: JSON.stringify({
      prompt: prompt,
      description: description,
      model: 'dall-e-2',
      size: '512x512'
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.error || 'Ошибка генерации изображения');
  }
  
  const data = await response.json();
  return data.image_url;
}

// Использование
generateImage('красивый закат над морем', 'в стиле импрессионизма')
  .then(imageUrl => {
    console.log('Изображение сгенерировано:', imageUrl);
    // Используйте imageUrl для отображения изображения
  })
  .catch(error => {
    console.error('Ошибка:', error);
  });
```

### Python (requests)

```python
import requests

def generate_image(prompt, description=None, token=None):
    url = 'http://localhost:8080/api/generate-image'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    data = {
        'prompt': prompt,
        'description': description,
        'model': 'dall-e-2',
        'size': '512x512'
    }
    
    response = requests.post(url, json=data, headers=headers)
    response.raise_for_status()
    
    return response.json()['image_url']

# Использование
image_url = generate_image(
    'красивый закат над морем',
    description='в стиле импрессионизма',
    token='your_jwt_token'
)
print(f'Изображение: {image_url}')
```

## Настройка

### Переменные окружения (.env)

```env
# OpenAI API
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_URL=https://api.proxyapi.ru/openai/v1  # или https://api.openai.com/v1

# Yandex Object Storage
YANDEX_STORAGE_ACCESS_KEY=your_access_key
YANDEX_STORAGE_SECRET_KEY=your_secret_key
YANDEX_STORAGE_BUCKET=your_bucket_name
YANDEX_STORAGE_ENDPOINT=https://storage.yandexcloud.net
YANDEX_STORAGE_REGION=ru-central1
```

## Особенности

1. **Автоматическая загрузка в Yandex Storage**: Все сгенерированные изображения автоматически загружаются в Yandex Object Storage и возвращается публичная ссылка.

2. **Fallback механизм**: Если Yandex Storage недоступен, изображение сохраняется локально в папку `uploads/`.

3. **Логирование**: Все операции логируются для отладки и мониторинга.

4. **Валидация**: Все входные данные валидируются перед отправкой в API OpenAI.

5. **Безопасность**: Требуется JWT авторизация для всех запросов на генерацию изображений.

## Стоимость

- **DALL-E 2**: 
  - 256x256: ~$0.016 за изображение
  - 512x512: ~$0.018 за изображение
  - 1024x1024: ~$0.020 за изображение

- **DALL-E 3**:
  - Standard quality: ~$0.040 за изображение
  - HD quality: ~$0.080 за изображение

*Цены могут изменяться. Актуальные цены смотрите на сайте OpenAI.*
