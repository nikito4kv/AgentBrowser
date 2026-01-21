/*
 * Modifications Copyright (c) 2025 Anthropic, PBC
 * Modified from original Microsoft Playwright source
 * Original Microsoft Playwright source licensed under Apache License 2.0
 * See CHANGELOG.md for details
 */

// Script for interacting with elements by their reference IDs

(function(elementRef) {
    try {
        // Get element from reference map
        let targetElement = null;
        
        if (window.__claudeElementMap && window.__claudeElementMap[elementRef]) {
            const weakRef = window.__claudeElementMap[elementRef];
            targetElement = weakRef.deref() || null;
            
            if (!targetElement || !document.contains(targetElement)) {
                // Element has been removed from DOM
                delete window.__claudeElementMap[elementRef];
                targetElement = null;
            }
        }
        
        if (!targetElement) {
            return {
                success: false,
                action: 'get_element',
                message: `No element found with reference: "${elementRef}". The element may have been removed from the page.`
            };
        }
        
        // Scroll element into view if needed
        targetElement.scrollIntoView({ behavior: 'instant', block: 'center', inline: 'center' });
        
        // Force a layout/paint to ensure the element is properly positioned after scroll
        targetElement.offsetHeight;
        
        // Get element coordinates
        const rect = targetElement.getBoundingClientRect();
        const clickX = rect.left + rect.width / 2;
        const clickY = rect.top + rect.height / 2;

        // Check for occlusion
        const topElement = document.elementFromPoint(clickX, clickY);
        let isOccluded = false;
        let occludedBy = null;

        if (topElement && topElement !== targetElement && !targetElement.contains(topElement)) {
            // If the element at the click point is not the target and not a descendant of the target,
            // check if the target is a descendant of the top element (sometimes legitimate, like clicking a label wrapping an input)
            // But usually, if we want to click X, and Y is on top, and Y is not X's child, X is covered.
            
            // Allow pointer-events: none pass-through logic simulation? 
            // elementFromPoint already handles pointer-events.
            
            isOccluded = true;
            occludedBy = topElement.tagName.toLowerCase() + 
                (topElement.id ? '#' + topElement.id : '') +
                (topElement.className ? '.' + topElement.className.split(' ').filter(c => c).join('.') : '');
        }
        
        // Build element info string
        const elementInfo = targetElement.tagName.toLowerCase() + 
            (targetElement.id ? '#' + targetElement.id : '') +
            (targetElement.className ? '.' + targetElement.className.split(' ').filter(c => c).join('.') : '');
        
        // Get additional element properties
        const elementType = targetElement.getAttribute('type') || '';
        const elementRole = targetElement.getAttribute('role') || '';
        const elementAriaLabel = targetElement.getAttribute('aria-label') || '';
        const elementText = targetElement.textContent ? targetElement.textContent.substring(0, 100) : '';
        
        return {
            success: true,
            coordinates: [clickX, clickY],
            elementInfo: elementInfo,
            elementRef: elementRef,
            rect: {
                left: rect.left,
                top: rect.top,
                right: rect.right,
                bottom: rect.bottom,
                width: rect.width,
                height: rect.height
            },
            attributes: {
                type: elementType,
                role: elementRole,
                ariaLabel: elementAriaLabel,
                text: elementText
            },
            isOccluded: isOccluded,
            occludedBy: occludedBy,
            isVisible: rect.width > 0 && rect.height > 0,
            isInteractable: !targetElement.disabled && 
                           targetElement.style.display !== 'none' &&
                           targetElement.style.visibility !== 'hidden'
        };
    } catch (error) {
        return {
            success: false,
            action: 'get_element',
            message: 'Error finding element by reference: ' + (error.message || 'Unknown error')
        };
    }
})