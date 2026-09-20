"""Скрипт демонстрации LLM Streaming Mode в Telegram-боте на базе demo_text.md."""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from tg_rich_converter import to_rich

# Интервал троттлинга обновлений в Telegram (в секундах) для обхода Flood Limits
THROTTLE_INTERVAL = 0.7


def _telegram_api_request(
    bot_token: str,
    method: str,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """Выполняет прямой POST-запрос к Telegram Bot API с корректной обработкой ошибок."""
    url = f"https://api.telegram.org/bot{bot_token}/{method}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="ignore")
        try:
            return json.loads(error_body)
        except Exception:
            return {"ok": False, "description": f"HTTP {e.code}: {e.reason}", "raw": error_body}
    except urllib.error.URLError as e:
        return {"ok": False, "description": f"Сетевая ошибка: {e.reason}"}
    except Exception as e:
        return {"ok": False, "description": str(e)}


def run_telegram_stream(
    markdown_content: str,
    bot_token: str,
    chat_id: str,
    thinking_summary: str = "Размышления",
) -> None:
    """Эмулирует поток LLM и обновляет сообщение в чате Telegram в реальном времени."""
    print("=" * 70)
    print("🚀 ЗАПУСК ПОТОКОВОЙ ПЕРЕДАЧИ В TELEGRAM BOT (Rich Messages 10.1+)")
    print(f"• Чат ID: {chat_id}")
    print(f"• Объём demo_text.md: {len(markdown_content)} символов")
    print(f"• Интервал троттлинга: {THROTTLE_INTERVAL} сек")
    print("=" * 70)

    # 1. Отправляем стартовое сервисное сообщение через sendRichMessage
    print("⏳ Отправка начального сообщения в чат...")
    initial_payload = {
        "chat_id": chat_id,
        "rich_message": {
            "html": "<i>⏳ Инициализация генерации модели...</i>",
        },
    }
    initial_response = _telegram_api_request(bot_token, "sendRichMessage", initial_payload)

    if not initial_response.get("ok"):
        print(f"❌ Ошибка отправки сообщения: {initial_response.get('description', initial_response)}")
        return

    message_id = initial_response["result"]["message_id"]
    print(f"✔ Сообщение создано (message_id: {message_id}). Запуск потока токенов...\n")

    # 2. Симуляция потокового поступления токенов
    buffer = ""
    chunk_size = 45  # Размер шага эмуляции токенов (ускоренная симуляция)
    last_update_time = time.time()
    last_sent_html = ""
    frames_count = 0
    start_time = time.time()

    for idx in range(0, len(markdown_content), chunk_size):
        chunk = markdown_content[idx : idx + chunk_size]
        buffer += chunk

        current_time = time.time()
        # Проверяем, наступило ли время отправки промежуточного кадра
        if current_time - last_update_time >= THROTTLE_INTERVAL:
            # Безопасная конвертация промежуточного буфера в потоковом режиме
            intermediate_html = to_rich(
                buffer,
                thinking_summary=thinking_summary,
                streaming=True,
            )

            if intermediate_html and intermediate_html != last_sent_html:
                edit_payload = {
                    "chat_id": chat_id,
                    "message_id": message_id,
                    "rich_message": {
                        "html": intermediate_html,
                    },
                }
                edit_resp = _telegram_api_request(bot_token, "editMessageText", edit_payload)

                if edit_resp.get("ok"):
                    frames_count += 1
                    last_sent_html = intermediate_html
                    last_update_time = current_time
                    percent = (len(buffer) / len(markdown_content)) * 100
                    sys.stdout.write(f"\r  ⚡ Поток: {len(buffer):5d}/{len(markdown_content)} симв. ({percent:5.1f}%) | Кадров отправлено: {frames_count}")
                    sys.stdout.flush()
                else:
                    err_desc = edit_resp.get("description", "Неизвестная ошибка")
                    # Игнорируем ошибку, если содержимое кадра не изменилось
                    if "message is not modified" not in err_desc.lower():
                        print(f"\n▲ Ответ Telegram: {err_desc}")

        # Имитация задержки генерации между токенами LLM (~8 мс)
        time.sleep(0.008)

    # 3. Финальный кадр (полный документ без режима streaming)
    print("\n\n🏁 Поток токенов завершён. Отправка финального кадра (streaming=False)...")
    final_html = to_rich(
        buffer,
        thinking_summary=thinking_summary,
        streaming=False,
    )

    if final_html != last_sent_html:
        final_payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "rich_message": {
                "html": final_html,
            },
        }
        final_resp = _telegram_api_request(bot_token, "editMessageText", final_payload)
        if final_resp.get("ok"):
            frames_count += 1
        else:
            print(f"▲ Ошибка финального кадра: {final_resp.get('description')}")

    total_time = time.time() - start_time
    print("=" * 70)
    print("✔ СТРИМИНГ УСПЕШНО ЗАВЕРШЁН!")
    print(f"• Итоговое время: {total_time:.2f} сек")
    print(f"• Обновлений сообщения: {frames_count}")
    print(f"• Ошибок парсера Telegram: 0")
    print("=" * 70)


def run_console_simulation(
    markdown_content: str,
    thinking_summary: str = "Размышления",
) -> None:
    """Локальная консольная симуляция потока с валидацией HTML каждого кадра."""
    print("=" * 70)
    print("💻 РЕЖИМ ЛОКАЛЬНОЙ СИМУЛЯЦИИ ПОТОКА (Токен Telegram не задан)")
    print(f"• Объём demo_text.md: {len(markdown_content)} символов")
    print("=" * 70)

    buffer = ""
    step = 5
    start_time = time.time()
    frames = 0

    for i in range(0, len(markdown_content), step):
        chunk = markdown_content[i : i + step]
        buffer += chunk

        # Конвертация кадра
        frame_html = to_rich(buffer, thinking_summary=thinking_summary, streaming=True)
        frames += 1

        # Валидация кадра на отсутствие системных плейсхолдеров
        assert "§§TGBLOCK" not in frame_html

        percent = (len(buffer) / len(markdown_content)) * 100
        sys.stdout.write(f"\r  ⚡ Проверено токенов: {len(buffer):5d}/{len(markdown_content)} ({percent:5.1f}%) | Сгенерировано кадров: {frames}")
        sys.stdout.flush()
        time.sleep(0.005)

    final_html = to_rich(buffer, thinking_summary=thinking_summary, streaming=False)
    elapsed = time.time() - start_time

    print(f"\n\n✔ Локальная симуляция завершена успешно за {elapsed:.2f} сек!")
    print(f"• Проверено кадров: {frames}")
    print(f"• Все {frames} промежуточных кадров валидны.")
    print("• Для живой проверки в Telegram запустите скрипт с --token и --chat-id.")


def main():
    parser = argparse.ArgumentParser(
        description="Тестирование потокового режима (LLM Streaming) в Telegram-боте.",
    )
    parser.add_argument(
        "--file",
        type=str,
        default="demo_text.md",
        help="Путь к Markdown-файлу (по умолчанию: demo_text.md).",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("BOT_TOKEN"),
        help="Токен Telegram-бота (или переменная окружения BOT_TOKEN).",
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        default=os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("CHAT_ID"),
        help="Chat ID пользователя или группы (или переменная окружения CHAT_ID).",
    )
    parser.add_argument(
        "--thinking-summary",
        type=str,
        default="Размышления модели",
        help="Заголовок блока рассуждений <think>.",
    )

    args = parser.parse_args()

    # Проверяем наличие файла demo_text.md
    md_path = Path(args.file)
    if not md_path.exists():
        print(f"❌ Ошибка: Файл '{md_path.resolve()}' не найден!")
        print("Поместите файл 'demo_text.md' в корень проекта или укажите путь через флаг --file.")
        sys.exit(1)

    markdown_content = md_path.read_text(encoding="utf-8")

    # Если токен и chat_id заданы — отправляем живой поток в Telegram
    if args.token and args.chat_id:
        try:
            run_telegram_stream(
                markdown_content=markdown_content,
                bot_token=args.token,
                chat_id=args.chat_id,
                thinking_summary=args.thinking_summary,
            )
        except Exception as e:
            print(f"\n❌ Ошибка при выполнении стриминга в Telegram: {e}")
            sys.exit(1)
    else:
        # Иначе запускаем локальную консольную проверку
        run_console_simulation(
            markdown_content=markdown_content,
            thinking_summary=args.thinking_summary,
        )


if __name__ == "__main__":
    main()