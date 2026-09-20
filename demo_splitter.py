"""Скрипт стресс-тестирования нарезки сверхдлинного документа."""

from pathlib import Path

from tg_rich_converter import save_preview, split_rich_message


def main():
    print("=" * 75)
    print("СТРЕСС-ТЕСТИРОВАНИЕ SMART MESSAGE SPLITTER")
    print("=" * 75)

    md_file = Path("demo_text.md")
    if not md_file.exists():
        print(f"Ошибка: Файл {md_file.name} не найден! Создайте его в корне проекта.")
        return

    base_markdown = md_file.read_text(encoding="utf-8")
    print(f"Базовый документ '{md_file.name}' загружен: {len(base_markdown)} символов.")

    # Создаем масштабный документ объемом свыше 60 000 символов
    massive_markdown = (base_markdown + "\n\n---\n\n") * 6
    total_len = len(massive_markdown)
    print(f"Сформирован масштабированный документ: {total_len} символов.")

    # --------------------------------------------------------------------------
    # ТЕСТ 1: ОФИЦИАЛЬНЫЙ ЛИМИТ TELEGRAM RICH MESSAGES (32 768 символов)
    # --------------------------------------------------------------------------
    rich_limit = 32768
    print(f"\n{'=' * 30} ТЕСТ 1: RICH MESSAGES (лимит {rich_limit}) {'=' * 30}")

    rich_chunks = split_rich_message(
        massive_markdown,
        max_length=rich_limit,
        is_markdown=True,
        thinking_summary="Квантовые рассуждения модели",
    )

    print(f"Результат: документ {total_len} симв. разделён на {len(rich_chunks)} сообщения:")
    for idx, chunk in enumerate(rich_chunks, 1):
        chunk_len = len(chunk)
        print(f"  -> Часть {idx}: {chunk_len:5d} / {rich_limit} симв. (запас: {rich_limit - chunk_len} симв.)")
        assert chunk_len <= rich_limit, f"Часть {idx} превысила лимит {rich_limit}!"

        out_file = Path(f"preview_rich_chunk_{idx}.html")
        save_preview(
            chunk,
            file_path=out_file,
            is_markdown=False,
            title=f"Telegram Rich Preview (32k) — Часть {idx}",
        )
        print(f"     Сохранён HTML: {out_file.name}")

    # --------------------------------------------------------------------------
    # ТЕСТ 2: КЛАССИЧЕСКИЙ ЛИМИТ TELEGRAM (4 096 символов)
    # --------------------------------------------------------------------------
    classic_limit = 4096
    print(f"\n{'=' * 30} ТЕСТ 2: CLASSIC MESSAGES (лимит {classic_limit}) {'=' * 30}")

    classic_chunks = split_rich_message(
        base_markdown,
        max_length=classic_limit,
        is_markdown=True,
        thinking_summary="Квантовые рассуждения модели",
    )

    print(f"Результат: базовый документ разделён на {len(classic_chunks)} сообщений:")
    for idx, chunk in enumerate(classic_chunks, 1):
        chunk_len = len(chunk)
        print(f"  -> Часть {idx}: {chunk_len:5d} / {classic_limit} симв.")
        assert chunk_len <= classic_limit, f"Часть {idx} превысила лимит {classic_limit}!"

        out_file = Path(f"preview_classic_chunk_{idx}.html")
        save_preview(
            chunk,
            file_path=out_file,
            is_markdown=False,
            title=f"Telegram Classic Preview (4k) — Часть {idx}",
        )
        print(f"     Сохранён HTML: {out_file.name}")

    # --------------------------------------------------------------------------
    # ПРОВЕРКА ЦЕЛОСТНОСТИ И БАЛАНСА ТЕГОВ
    # --------------------------------------------------------------------------
    print(f"\n{'=' * 30} ПРОВЕРКА ЦЕЛОСТНОСТИ СТРУКТУРЫ {'=' * 30}")
    for name, chunk_list in [("Rich (32k)", rich_chunks), ("Classic (4k)", classic_chunks)]:
        broken_math = False
        broken_code = False
        for chunk in chunk_list:
            if chunk.count("<tg-math>") != chunk.count("</tg-math>"):
                broken_math = True
            if chunk.count("<tg-math-block>") != chunk.count("</tg-math-block>"):
                broken_math = True
            if chunk.count("<pre>") != chunk.count("</pre>"):
                broken_code = True

        print(f"Режим {name:12s}: Формулы целы = {not broken_math} | Блоки кода сбалансированы = {not broken_code}")

    print("\n" + "=" * 75)
    print("СТРЕСС-ТЕСТ ЗАВЕРШЁН УСПЕШНО!")
    print("Откройте 'preview_rich_chunk_1.html' в браузере для проверки.")
    print("=" * 75)


if __name__ == "__main__":
    main()