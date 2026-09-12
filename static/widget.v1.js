(function() {
    'use strict';
    
    // Extract widget ID from script tag
    function getWidgetId() {
        const scripts = document.getElementsByTagName('script');
        for (let i = 0; i < scripts.length; i++) {
            const src = scripts[i].src;
            if (src && src.includes('widget.v1.js')) {
                const url = new URL(src);
                return url.searchParams.get('id');
            }
        }
        return null;
    }
    
    // Generate unique ID for forms
    function generateId() {
        return 'widget-' + Math.random().toString(36).substr(2, 9);
    }
    
    // Create CSS styles
    function createStyles() {
        const style = document.createElement('style');
        style.textContent = `
            .flyrank-widget {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: white;
                border: 1px solid #e1e5e9;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                max-width: 400px;
                margin: 20px;
                position: relative;
            }
            .flyrank-widget h3 {
                margin: 0 0 8px 0;
                color: #333;
                font-size: 18px;
            }
            .flyrank-widget p {
                margin: 0 0 16px 0;
                color: #666;
                font-size: 14px;
                line-height: 1.4;
            }
            .flyrank-widget-form {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .flyrank-widget-field {
                display: flex;
                flex-direction: column;
                gap: 4px;
            }
            .flyrank-widget-label {
                font-size: 14px;
                font-weight: 500;
                color: #333;
            }
            .flyrank-widget-input {
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                font-size: 14px;
                transition: border-color 0.2s;
            }
            .flyrank-widget-input:focus {
                outline: none;
                border-color: #3b82f6;
                box-shadow: 0 0 0 3px rgba(59,130,246,0.1);
            }
            .flyrank-widget-textarea {
                min-height: 80px;
                resize: vertical;
            }
            .flyrank-widget-button {
                background: #3b82f6;
                color: white;
                border: none;
                padding: 10px 16px;
                border-radius: 4px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                transition: background-color 0.2s;
            }
            .flyrank-widget-button:hover {
                background: #2563eb;
            }
            .flyrank-widget-button:disabled {
                background: #9ca3af;
                cursor: not-allowed;
            }
            .flyrank-widget-message {
                padding: 12px;
                border-radius: 4px;
                font-size: 14px;
                margin-top: 12px;
            }
            .flyrank-widget-success {
                background: #dcfce7;
                color: #166534;
                border: 1px solid #bbf7d0;
            }
            .flyrank-widget-error {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
            }
            .flyrank-widget-honeypot {
                position: absolute !important;
                left: -9999px !important;
                width: 1px !important;
                height: 1px !important;
                overflow: hidden !important;
            }
        `;
        document.head.appendChild(style);
    }
    
    // Fetch widget configuration
    async function fetchConfig(widgetId) {
        const response = await fetch(`/widgets/${widgetId}/config`);
        if (!response.ok) {
            throw new Error(`Failed to load widget config: ${response.status}`);
        }
        return response.json();
    }
    
    // Submit form data
    async function submitForm(widgetId, formData, honeypotValue) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        // Add idempotency key
        const idempotencyKey = generateId() + '-' + Date.now();
        headers['Idempotency-Key'] = idempotencyKey;
        
        const response = await fetch('/submissions', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                widget_id: widgetId,
                data: formData,
                hp_field: honeypotValue
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Submission failed');
        }
        
        return response.json();
    }
    
    // Create form field HTML
    function createField(field) {
        const fieldId = generateId();
        const isRequired = field.required ? ' *' : '';
        
        let input;
        if (field.type === 'textarea') {
            input = `<textarea 
                class="flyrank-widget-input flyrank-widget-textarea" 
                id="${fieldId}" 
                name="${field.name}" 
                ${field.required ? 'required' : ''}
                placeholder="${field.label}"></textarea>`;
        } else {
            input = `<input 
                class="flyrank-widget-input" 
                type="${field.type}" 
                id="${fieldId}" 
                name="${field.name}" 
                ${field.required ? 'required' : ''}
                placeholder="${field.label}">`;
        }
        
        return `
            <div class="flyrank-widget-field">
                <label class="flyrank-widget-label" for="${fieldId}">
                    ${field.label}${isRequired}
                </label>
                ${input}
            </div>
        `;
    }
    
    // Create widget HTML
    function createWidget(config) {
        const widgetId = generateId();
        const fields = config.form_fields.map(createField).join('');
        
        return `
            <div class="flyrank-widget" id="${widgetId}">
                <h3>${config.title}</h3>
                ${config.description ? `<p>${config.description}</p>` : ''}
                <form class="flyrank-widget-form" data-widget-id="${config.id}">
                    ${fields}
                    <input type="text" name="hp_field" class="flyrank-widget-honeypot" tabindex="-1" autocomplete="off">
                    <button type="submit" class="flyrank-widget-button">
                        ${config.button_text || 'Submit'}
                    </button>
                </form>
            </div>
        `;
    }
    
    // Show message
    function showMessage(container, message, isError = false) {
        const messageClass = isError ? 'flyrank-widget-error' : 'flyrank-widget-success';
        const messageHtml = `
            <div class="flyrank-widget-message ${messageClass}">
                ${message}
            </div>
        `;
        
        // Remove existing messages
        const existingMessage = container.querySelector('.flyrank-widget-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        
        container.insertAdjacentHTML('beforeend', messageHtml);
    }
    
    // Handle form submission
    function handleFormSubmit(form, widgetId) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const button = form.querySelector('button[type="submit"]');
            const container = form.closest('.flyrank-widget');
            
            // Disable button and show loading
            button.disabled = true;
            button.textContent = 'Submitting...';
            
            try {
                // Collect form data
                const formData = new FormData(form);
                const data = {};
                const honeypotValue = formData.get('hp_field') || '';
                
                for (const [key, value] of formData.entries()) {
                    if (key !== 'hp_field') {
                        data[key] = value;
                    }
                }
                
                // Submit form
                await submitForm(widgetId, data, honeypotValue);
                
                // Show success message
                showMessage(container, 'Thank you! Your submission has been received.');
                
                // Reset form
                form.reset();
                
            } catch (error) {
                console.error('Submission error:', error);
                showMessage(container, error.message || 'Something went wrong. Please try again.', true);
            } finally {
                // Re-enable button
                button.disabled = false;
                button.textContent = form.closest('.flyrank-widget').querySelector('h3').textContent.includes('Submit') ? 
                    'Submit' : 
                    button.getAttribute('data-original-text') || 'Submit';
            }
        });
    }
    
    // Initialize widget
    async function initWidget() {
        try {
            const widgetId = getWidgetId();
            if (!widgetId) {
                console.error('FlyRank Widget: No widget ID found in script URL');
                return;
            }
            
            // Create styles
            createStyles();
            
            // Fetch configuration
            const config = await fetchConfig(widgetId);
            
            // Create and insert widget
            const widgetHtml = createWidget(config);
            
            // Insert widget at script location or at end of body
            const script = document.currentScript || document.querySelector('script[src*="widget.v1.js"]');
            if (script && script.parentNode) {
                script.parentNode.insertAdjacentHTML('afterend', widgetHtml);
            } else {
                document.body.insertAdjacentHTML('beforeend', widgetHtml);
            }
            
            // Setup form submission
            const form = document.querySelector(`form[data-widget-id="${widgetId}"]`);
            if (form) {
                handleFormSubmit(form, widgetId);
                
                // Store original button text
                const button = form.querySelector('button[type="submit"]');
                if (button) {
                    button.setAttribute('data-original-text', button.textContent);
                }
            }
            
        } catch (error) {
            console.error('FlyRank Widget Error:', error);
        }
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initWidget);
    } else {
        initWidget();
    }
    
})();