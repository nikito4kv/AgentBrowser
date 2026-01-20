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
- [x] **Task: Conductor - User Manual Verification 'Phase 1: Logic & Tools Implementation' (Protocol in workflow.md)**

## Phase 2: System Prompt & Integration [checkpoint: 07603f0]
Обновление системного промпта для использования новых возможностей и интеграция в основной цикл.

- [x] **Task 3: Обновление системного промпта** c381581
    - [ ] Модифицировать `system_instruction` в `Agent`, чтобы он включал динамические секции "Current Plan" и "Memory".
    - [ ] Метод `think` должен подставлять актуальные значения этих секций перед отправкой.
- [x] **Task 4: Верификация на сложном сценарии** c381581
    - [ ] Создать скрипт верификации, эмулирующий многошаговую задачу (или запустить вручную).
    - [ ] Убедиться, что агент создает план и следует ему.
- [x] **Task: Conductor - User Manual Verification 'Phase 2: System Prompt & Integration' (Protocol in workflow.md)**

## Phase 3: Cognitive Refinement [checkpoint: 1bb9f35]
Улучшение качества принятия решений через Chain-of-Thought, семантическую привязку и самокоррекцию.

- [x] **Task 5: Chain-of-Thought (CoT) Implementation** cd8f560
    - [x] Обновить системный промпт: обязать агента выводить блок `THOUGHT` перед вызовом инструментов.
    - [x] Описать структуру мыслительного процесса: Observation -> Analysis -> Plan -> Action.
- [x] **Task 6: Самокоррекция и проверка состояния** 1bb9f35
    - [x] Добавить в промпт инструкции по проверке успешности предыдущего действия (сравнение состояний).
    - [x] Реализовать логику "если скриншот не изменился после клика -> попробовать другой селектор или wait".
- [x] **Task 7: Тестирование на реальном кейсе (GitHub Search)** 1bb9f35
    - [x] Создать скрипт для запуска сценария "Найти самый популярный репо на GitHub".
    - [x] Отладить промпт и логику на основе логов выполнения.
- [x] **Task: Conductor - User Manual Verification 'Phase 3: Cognitive Refinement' (Protocol in workflow.md)** 1bb9f35
