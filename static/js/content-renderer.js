// Content Rendering Utilities - Code and Math

/**
 * Render code blocks and math formulas in text content
 * @param {string} text - Text containing code/math markup
 * @returns {string} HTML with rendered code and math
 */
function renderContent(text) {
    if (!text) return '';
    
    // Escape HTML to prevent XSS, but we'll selectively unescape for our markup
    const div = document.createElement('div');
    div.textContent = text;
    let escaped = div.innerHTML;
    
    // Convert code blocks first (```) before inline code (`)
    // Code blocks: ```language\ncode```  or just ```code```
    escaped = escaped.replace(/```(\w+)?\n?([\s\S]+?)```/g, function(match, lang, code) {
        const language = lang || 'python';
        // Unescape the code content
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = code;
        const unescapedCode = tempDiv.textContent;
        return `<pre><code class="language-${language}">${unescapedCode}</code></pre>`;
    });
    
    // Convert inline code `code` to <code>code</code>
    escaped = escaped.replace(/`([^`]+)`/g, function(match, code) {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = code;
        const unescapedCode = tempDiv.textContent;
        return `<code>${unescapedCode}</code>`;
    });
    
    // Render math formulas - wrap in spans for later KaTeX rendering
    // Block math first: $$formula$$
    escaped = escaped.replace(/\$\$([\s\S]+?)\$\$/g, '<span class="math-block">$1</span>');
    
    // Inline math: $formula$
    escaped = escaped.replace(/\$([^\$]+)\$/g, '<span class="math-inline">$1</span>');
    
    return escaped;
}

/**
 * Render KaTeX math formulas in the DOM
 * Call this after inserting HTML with math-inline or math-block classes
 */
function renderMath() {
    // Check if KaTeX is loaded
    if (typeof katex === 'undefined') {
        console.warn('KaTeX is not loaded');
        return;
    }
    
    // Inline math
    document.querySelectorAll('.math-inline').forEach(element => {
        if (element.hasAttribute('data-rendered')) return; // Skip if already rendered
        
        try {
            const formula = element.textContent;
            katex.render(formula, element, {
                throwOnError: false,
                displayMode: false
            });
            element.setAttribute('data-rendered', 'true');
        } catch (e) {
            console.error('KaTeX inline error:', e);
            element.classList.add('math-error');
        }
    });
    
    // Block math
    document.querySelectorAll('.math-block').forEach(element => {
        if (element.hasAttribute('data-rendered')) return; // Skip if already rendered
        
        try {
            const formula = element.textContent;
            katex.render(formula, element, {
                throwOnError: false,
                displayMode: true
            });
            element.setAttribute('data-rendered', 'true');
        } catch (e) {
            console.error('KaTeX block error:', e);
            element.classList.add('math-error');
        }
    });
}

/**
 * Highlight code blocks using Prism.js
 * Call this after inserting HTML with code blocks
 */
function highlightCode() {
    if (typeof Prism !== 'undefined') {
        Prism.highlightAll();
    } else if (typeof hljs !== 'undefined') {
        // If using highlight.js instead
        document.querySelectorAll('pre code').forEach((block) => {
            hljs.highlightElement(block);
        });
    }
}

/**
 * Process content: render code and math, then highlight
 * Call this after dynamically adding content to the page
 */
function processContent() {
    highlightCode();
    renderMath();
}
