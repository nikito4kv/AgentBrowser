# Plan: Улучшение восприятия и устойчивости (Contextual Vision & Recovery)

## Phase 1: Content & Recovery [checkpoint: eff84e9]
Быстрые исправления для стабильности: обрезка контента и обработка сбоев.

- [x] **Task 1: Лимитирование extract_content** 8c8e5c1
    - [ ] Модифицировать `BrowserManager.extract_content` для обрезки текста (макс 10000 символов).
    - [ ] Написать тест на проверку лимита.
- [x] **Task 2: Реализация механизма самовосстановления** 57d51ac
    - [ ] В `main.py` добавить логику обработки пустого ответа.
    - [ ] Реализовать откат истории (`pop`) и повторную попытку с текстом об ошибке.
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Content & Recovery' (Protocol in workflow.md)**

## Phase 2: Contextual Vision
Улучшение "зрения" агента за счет семантических данных.

- [ ] **Task 3: Сбор семантики элементов (JS)**
    - [ ] Обновить `annotate.js`: собирать `tagName`, `innerText`, `placeholder`, `aria-label`, `title`.
    - [ ] Возвращать этот Map из JS в Python.
- [ ] **Task 4: Передача карты элементов модели**
    - [ ] Обновить `BrowserManager.capture_annotated_screenshot` (или создать новый метод), чтобы он возвращал и картинку, и текст (карту элементов).
    - [ ] Обновить `main.py`: добавлять карту элементов в промпт модели.
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: Contextual Vision' (Protocol in workflow.md)**
