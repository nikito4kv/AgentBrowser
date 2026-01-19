# Plan: Оптимизация контекста и истории (Bug Fix)

## Phase 1: Implementation [checkpoint: 24ab5c1]
Реализация логики очистки истории в классе Orchestrator или Agent.

- [x] **Task 1: Реализация метода очистки истории** 10c7eee
    - [ ] Добавить метод `_prune_history(history)` в `Agent` (или управлять этим в `Orchestrator`).
    - [ ] Логика: проходить по списку `contents`, и если `part` содержит `inline_data` или `file_data` (изображение) и это не последнее сообщение, удалять его.
    - [ ] Написать тест `tests/test_history_pruning.py`, который создает историю с 3 картинками и проверяет, что после "чистки" осталась одна.
- [x] **Task 2: Интеграция в Main Loop** 10c7eee
- [x] **Task 3: Оптимизация формата скриншотов (JPEG)** 2664982
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Implementation' (Protocol in workflow.md)**
