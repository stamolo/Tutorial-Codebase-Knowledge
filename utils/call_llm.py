import os
import json
import logging
import requests
from datetime import datetime
from google import genai

# ================== Настройка логирования ==================
log_directory = os.getenv("LOG_DIR", "logs")
os.makedirs(log_directory, exist_ok=True)
log_file = os.path.join(
    log_directory, f"llm_calls_{datetime.now().strftime('%Y%m%d')}.log"
)

logger = logging.getLogger("llm_logger")
logger.setLevel(logging.INFO)
logger.propagate = False  # Не поднимать логи в корневой логгер
file_handler = logging.FileHandler(log_file, encoding="utf-8")
file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(file_handler)

# Файл для кеша ответов
cache_file = "llm_cache.json"


def call_llm(prompt: str, use_cache: bool = True) -> str:
    """
    Универсальная обёртка над LLM: если задан OPENROUTER_API_KEY — уходит запрос
    в OpenRouter.ai, иначе — в Google Gemini через google-genai.
    Результаты при use_cache=True сохраняются локально в JSON-файле.
    """
    logger.info(f"PROMPT: {prompt}")

    # --- попытка взять из кеша ---
    if use_cache:
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                logger.warning("Не удалось загрузить кеш, начинаем с пустого")
        if prompt in cache:
            logger.info(f"RESPONSE (cache): {cache[prompt]}")
            return cache[prompt]

    # --- если есть ключ OpenRouter — используем OpenRouter.ai ---
    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if openrouter_key:
        model = os.getenv("OPENROUTER_MODEL", "google/gemma-3-27b-it")
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
            # при желании:
            # "HTTP-Referer": os.getenv("REFERER_URL", ""),
            # "X-Title": os.getenv("SITE_TITLE", ""),
        }
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
        try:
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"OpenRouter API error: {e}")
            raise

        data = resp.json()
        response_text = data["choices"][0]["message"]["content"]
        logger.info(f"RESPONSE (OpenRouter): {response_text}")

    else:
        # --- по умолчанию: Google Gemini через genai.Client ---
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", ""))
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-pro-exp-03-25")
        response = client.models.generate_content(model=model, contents=[prompt])
        response_text = response.text
        logger.info(f"RESPONSE (Gemini): {response_text}")

    # --- записываем в кеш ---
    if use_cache:
        cache = {}
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache = json.load(f)
            except Exception:
                pass
        cache[prompt] = response_text
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f)
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")

    return response_text


if __name__ == "__main__":
    test_prompt = "Hello, how are you?"
    print("Making call without cache...")
    r1 = call_llm(test_prompt, use_cache=False)
    print(f"Response: {r1}")
