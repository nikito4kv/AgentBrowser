# Plan: Улучшение восприятия и устойчивости (Contextual Vision & Recovery)

## Phase 1: Content & Recovery [checkpoint: eff84e9]
Быстрые исправления для стабильности: обрезка контента и обработка сбоев.

- [x] **Task 1: Лимитирование extract_content** 8c8e5c1
    - [ ] Модифицировать `BrowserManager.extract_content` для обрезки текста (макс 10000 символов).
    - [ ] Написать тест на проверку лимита.
- [x] **Task 2: Реализация механизма самовосстановления** 57d51ac
    - [ ] В `main.py` добавить логику обработки пустого ответа.
    - [ ] Реализовать откат истории (`pop`) и повторную попытку с текстом об ошибке.
- [x] **Task: Conductor - User Manual Verification 'Phase 1: Content & Recovery' (Protocol in workflow.md)** 207e564

## Phase 2: Contextual Vision [checkpoint: 207e564]
Улучшение "зрения" агента за счет семантических данных.

- [x] **Task 3: Сбор семантики элементов (JS)** 297d12d
- [x] **Task 4: Передача карты элементов модели** 2cc479e
- [x] **Task 5: Глубокая очистка контекста и обработка API лимитов** 8e21487
- [x] **Task 6: Стабилизация навигации (wait в type_text)** b43b8b5
- [x] **Task: Conductor - User Manual Verification 'Phase 2: Contextual Vision' (Protocol in workflow.md)** 207e564
