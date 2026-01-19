# Plan: Расширение инструментов навигации (Smart Navigation & Scraping)

## Phase 1: Navigation Tools Implementation [checkpoint: 933740a]
Реализация базовых инструментов навигации в BrowserManager и Agent.

- [x] **Task 1: Реализация методов навигации в BrowserManager** 2701abf
    - [ ] Добавить методы `navigate`, `go_back`, `go_forward`, `reload` в `BrowserManager`.
    - [ ] Написать тесты для проверки навигации (переход, назад, вперед).
- [x] **Task 2: Обновление Agent Tools и System Prompt** 0a3c786
    - [ ] Добавить новые инструменты в схему `get_tools` класса `Agent`.
    - [ ] Обновить системный промпт инструкциями по выбору между поиском и навигацией.
    - [ ] Написать тест, где агент должен выбрать `navigate` для запроса с URL.
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Navigation Tools Implementation' (Protocol in workflow.md)**

## Phase 2: Content Scraping Implementation [checkpoint: 6fb0288]
Реализация инструмента для чтения содержимого страницы.

- [x] **Task 3: Реализация extract_content** 9e50ce8
    - [ ] Установить библиотеку `markdownify` (или аналог).
    - [ ] Реализовать метод `extract_content` в `BrowserManager`, который возвращает текст страницы в Markdown.
    - [ ] Написать тест: открыть страницу с текстом и проверить, что метод возвращает корректный контент.
- [x] **Task 4: Интеграция с Agent и Main** 055fd60
    - [ ] Добавить инструмент `extract_content` в `Agent`.
    - [ ] Добавить обработку нового инструмента в `main.py` (`execute_tool`).
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Content Scraping Implementation' (Protocol in workflow.md)**
