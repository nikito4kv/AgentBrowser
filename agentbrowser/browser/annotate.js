(function() {
    // Удаляем старые метки, если они есть
    const oldLabels = document.querySelectorAll('.agent-browser-label');
    oldLabels.forEach(l => l.remove());

    const interactiveSelectors = [
        'a', 'button', 'input', 'textarea', 'select',
        '[role="button"]', '[role="link"]', '[role="checkbox"]', '[role="menuitem"]'
    ];

    const elements = document.querySelectorAll(interactiveSelectors.join(','));
    let count = 0;
    const elementData = [];

    elements.forEach(el => {
        // Проверка видимости
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        if (rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none') {
            count++;
            el.setAttribute('data-agent-id', count);

            // Собираем метаданные
            elementData.push({
                id: count,
                tagName: el.tagName,
                text: el.innerText ? el.innerText.trim().substring(0, 50) : "",
                ariaLabel: el.getAttribute('aria-label') || "",
                placeholder: el.getAttribute('placeholder') || "",
                title: el.getAttribute('title') || "",
                role: el.getAttribute('role') || ""
            });

            // Создаем визуальную метку
            const label = document.createElement('div');
            label.className = 'agent-browser-label';
            label.innerText = count;
            label.style.position = 'absolute';
            label.style.top = (rect.top + window.scrollY) + 'px';
            label.style.left = (rect.left + window.scrollX) + 'px';
            label.style.backgroundColor = 'red';
            label.style.color = 'white';
            label.style.fontSize = '12px';
            label.style.fontWeight = 'bold';
            label.style.padding = '2px 5px';
            label.style.borderRadius = '3px';
            label.style.zIndex = '1000000';
            label.style.pointerEvents = 'none';

            document.body.appendChild(label);
        }
    });
    return elementData;
})();
