# Plan: Внедрение планирования и памяти (Reasoning & Memory)

## Phase 1: Logic & Tools Implementation [checkpoint: f96be1c]
Реализация структур данных для плана и памяти, а также соответствующих инструментов.

- [x] **Task 1: Структуры данных и методы в Agent** cd8f560
    - [ ] Добавить в класс `Agent` поля `self.plan` и `self.memory`.
    - [ ] Реализовать методы `update_plan` и `save_memory`.
    - [ ] Написать тесты на обновление состояния.
- [x] **Task 2: Интеграция инструментов в get_tools** cd8f560
    - [ ] Добавить определения `update_plan` и `save_memory` в `get_tools`.
    - [ ] Обновить `execute_tool` в `main.py` для обработки этих вызовов.
- [ ] **Task: Conductor - User Manual Verification 'Phase 1: Logic & Tools Implementation' (Protocol in workflow.md)**

## Phase 2: System Prompt & Integration
Обновление системного промпта для использования новых возможностей и интеграция в основной цикл.

- [ ] **Task 3: Обновление системного промпта**
    - [ ] Модифицировать `system_instruction` в `Agent`, чтобы он включал динамические секции "Current Plan" и "Memory".
    - [ ] Метод `think` должен подставлять актуальные значения этих секций перед отправкой.
- [ ] **Task 4: Верификация на сложном сценарии**
    - [ ] Создать скрипт верификации, эмулирующий многошаговую задачу (или запустить вручную).
    - [ ] Убедиться, что агент создает план и следует ему.
- [ ] **Task: Conductor - User Manual Verification 'Phase 2: System Prompt & Integration' (Protocol in workflow.md)**
