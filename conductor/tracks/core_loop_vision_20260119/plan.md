# Plan: Разработка ядра автономного агента (Core Loop & Vision)

## Phase 1: Environment Setup & Browser Initialization [checkpoint: cf9d970]
Инициализация проекта, настройка зависимостей и базового управления браузером.

- [x] **Task 1: Настройка проекта с использованием `uv`** 0117a6f
    - [ ] Создать `pyproject.toml` и установить зависимости: `playwright`, `google-genai`, `pillow`, `python-dotenv`, `rich`, `pytest`, `pytest-cov`.
    - [ ] Настроить `.env` для `GEMINI_API_KEY`.
- [x] **Task 2: Реализация базового контроллера браузера** 880b422
    - [ ] Написать тесты для инициализации Playwright и открытия страницы.
    - [ ] Реализовать класс `BrowserManager` для управления сессией и навигацией.
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Environment Setup & Browser Initialization' (Protocol in workflow.md)**

## Phase 2: Visual Annotator (Set-of-Mark)
Реализация системы разметки страницы для того, чтобы ИИ мог «видеть» элементы.

- [x] **Task 3: JS-скрипт для поиска и разметки элементов** 2145ba1
    - [ ] Написать тесты для проверки нахождения интерактивных элементов на тестовой HTML-странице.
    - [ ] Реализовать JS-скрипт, который помечает элементы атрибутом `data-agent-id` и рисует визуальные метки.
- [x] **Task 4: Снятие скриншотов с разметкой** 90e3dcf
    - [ ] Написать тесты для захвата скриншота и проверки наличия на нем визуальных меток.
    - [ ] Реализовать метод в `BrowserManager` для получения скриншота с активной разметкой.
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Visual Annotator (Set-of-Mark)' (Protocol in workflow.md)**

## Phase 3: Action Layer (Basic Tools Implementation)
Реализация инструментов взаимодействия с браузером, которые будет вызывать ИИ.

- [ ] **Task 5: Реализация инструмента `click_element`**
    - [ ] Написать тесты для клика по элементу через его ID в разметке.
    - [ ] Реализовать логику поиска элемента по `data-agent-id` и выполнения клика.
- [ ] **Task 6: Реализация инструмента `type_text`**
    - [ ] Написать тесты для ввода текста в поле ввода по его ID.
    - [ ] Реализовать логику ввода текста с предварительной очисткой поля.
- [ ] **Task 7: Реализация инструментов `scroll` и `wait`**
    - [ ] Написать тесты для прокрутки страницы и ожидания появления элементов.
    - [ ] Реализовать функции прокрутки и ожидания.
- [ ] **Task: Conductor - User Manual Verification 'Phase 3: Action Layer (Basic Tools Implementation)' (Protocol in workflow.md)**

## Phase 4: Logic Layer & Integration
Интеграция с Gemini 2.0 Flash и запуск основного цикла работы агента.

- [ ] **Task 8: Интеграция с `google-genai` SDK**
    - [ ] Написать тесты для мокированного вызова API Gemini.
    - [ ] Реализовать класс `Agent` для взаимодействия с моделью, включая системный промпт и передачу скриншотов.
- [ ] **Task 9: Реализация Core Loop (Observe-Think-Act)**
    - [ ] Написать интеграционный тест для выполнения простой задачи (например, «загугли что-то»).
    - [ ] Реализовать цикл, который объединяет навигацию, разметку, анализ модели и выполнение действий.
- [ ] **Task 10: Обработка ошибок и Retry-механизм**
    - [ ] Написать тесты для имитации ошибок Playwright.
    - [ ] Реализовать логику повторных попыток и запрос помощи у пользователя.
- [ ] **Task: Conductor - User Manual Verification 'Phase 4: Logic Layer & Integration' (Protocol in workflow.md)**
