"""Скрипт для стресс-тестирования конвертера и генерации локального preview.html."""

from pathlib import Path

from tg_rich_converter import save_preview

COMPLEX_MARKDOWN = r"""
<think>
1. Задача: провести анализ квантового состояния и оператора эволюции.
2. Проверим условие унитарности: $U^\dagger U = I$.
3. Построим матрицу оператора Гамильтона $\hat{H}$ и решим характеристическое уравнение $\det(H - \lambda I) = 0$.
4. Скрытый диагностический параметр: ||DIAG_STATE_VECT_0x99||.
</think>

# Квантовый гармонический осциллятор и анализ матриц

В квантовой механике эволюция вектора состояния $|\psi(t)\rangle$ во времени описывается нестационарным уравнением Шрёдингера:

$$i\hbar \frac{\partial}{\partial t} |\psi(t)\rangle = \hat{H} |\psi(t)\rangle$$

Где оператор Гамильтона $\hat{H}$ для одномерной частицы имеет канонический вид:

$$\hat{H} = -\frac{\hbar^2}{2m} \frac{d^2}{dx^2} + \frac{1}{2} m \omega^2 x^2$$

---

## 1. Свойства квантовых состояний

* Нормировка волновой функции: интеграл вероятности строго равен единице:
$$\int_{-\infty}^{+\infty} |\psi(x)|^2 \, dx = \sqrt{\frac{\pi}{\alpha}} \cdot \sqrt{\frac{\alpha}{\pi}} = 1$$
* Основное состояние: $|0\rangle = \left(\frac{m\omega}{\pi\hbar}\right)^{1/4} e^{-\frac{m\omega}{2\hbar}x^2}$.
* Принцип суперпозиции: состояние $|\Psi\rangle = \frac{1}{\sqrt{2}}(|0\rangle + |1\rangle)$ демонстрирует ==квантовое превосходство== при интерференции.
* Наблюдаемая величина: модуль отклонения $|x| \ge 0$ всегда неотрицателен.

> **Важное замечание:**
> Эволюция замкнутой квантовой системы является ++строго унитарной++.
> Использование ~~классического приближения~~ в данном масштабе недопустимо.

---

## 2. Сравнительный анализ операторов

В таблице ниже приведены операторы, их матрицы и свойства (проверка экранирования пайпов `\|` и математики в ячейках):

| Оператор | Матричный вид | Собственные числа | Статус \| Режим |
|:---------|:-------------:|------------------:|:---------------|
| Паули $\sigma_x$ | $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ | $\lambda = \pm 1$ | Активен \| Базовый |
| Паули $\sigma_z$ | $\begin{pmatrix} 1 & 0 \\ 0 & -1 \end{pmatrix}$ | $\lambda = \pm 1$ | Активен \| Проекция |
| Адамар $H$ | $\frac{1}{\sqrt{2}}\begin{pmatrix} 1 & 1 \\ 1 & -1 \end{pmatrix}$ | $\lambda \in \{-1, 1\}$ | Фазовый \| $H^2 = I$ |

---

## 3. Программная реализация на Python

Для численного расчёта спектра оператора используем модуль `numpy`:

```python
import numpy as np

def compute_pauli_eigen():
    # Матрица Паули sigma_x
    sigma_x = np.array([[0, 1], [1, 0]], dtype=complex)
    eigenvalues, eigenvectors = np.linalg.eig(sigma_x)
    
    # Проверка: det(A) == prod(eigenvalues)
    assert np.isclose(np.linalg.det(sigma_x), -1.0)
    return eigenvalues

print("Собственные значения:", compute_pauli_eigen())
```

Ключ верификации квантового канала: ||QUANTUM_ENTANGLED_KEY_999||.
"""


def main():
    output_path = Path("preview.html")
    save_preview(
        text=COMPLEX_MARKDOWN,
        file_path=output_path,
        title="Telegram Rich HTML — Комплексный стресс-тест",
        thinking_summary="Цепочка квантовых рассуждений",
    )
    print(f"Успешно сгенерирован файл: {output_path.resolve()}")
    print("Откройте 'preview.html' в браузере, чтобы оценить рендеринг!")


if __name__ == "__main__":
    main()
