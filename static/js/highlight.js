// Simple Python syntax highlighting
document.addEventListener('DOMContentLoaded', function() {
    highlightCode();
});

function highlightCode() {
    const codeBlocks = document.querySelectorAll('.code-block code');
    
    codeBlocks.forEach(block => {
        if (block.classList.contains('highlighted')) return;
        
        let code = block.textContent;
        
        // Python keywords
        const keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'in', 'is', 'not', 
                         'and', 'or', 'return', 'import', 'from', 'as', 'with', 'try', 'except', 
                         'finally', 'raise', 'assert', 'pass', 'break', 'continue', 'yield', 
                         'lambda', 'None', 'True', 'False', 'async', 'await'];
        
        // Python built-ins
        const builtins = ['print', 'len', 'range', 'str', 'int', 'float', 'list', 'dict', 'set', 
                         'tuple', 'type', 'isinstance', 'open', 'input', 'map', 'filter', 'sum',
                         'min', 'max', 'sorted', 'enumerate', 'zip', 'any', 'all'];
        
        // Escape HTML
        code = code.replace(/&/g, '&amp;')
                   .replace(/</g, '&lt;')
                   .replace(/>/g, '&gt;');
        
        // Highlight comments (must be first to avoid conflicts)
        code = code.replace(/(#.*$)/gm, '<span class="comment">$1</span>');
        
        // Highlight strings
        code = code.replace(/(['"]{3}[\s\S]*?['"]{3})/g, '<span class="string">$1</span>'); // Triple quotes
        code = code.replace(/(['"])((?:\\.|(?!\1).)*?)\1/g, '<span class="string">$1$2$1</span>'); // Single/double quotes
        
        // Highlight numbers
        code = code.replace(/\b(\d+\.?\d*)\b/g, '<span class="number">$1</span>');
        
        // Highlight keywords
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b(${keyword})\\b`, 'g');
            code = code.replace(regex, '<span class="keyword">$1</span>');
        });
        
        // Highlight built-in functions
        builtins.forEach(builtin => {
            const regex = new RegExp(`\\b(${builtin})(?=\\()`, 'g');
            code = code.replace(regex, '<span class="builtin">$1</span>');
        });
        
        // Highlight function definitions
        code = code.replace(/\b(def)\s+(\w+)/g, '<span class="keyword">$1</span> <span class="function">$2</span>');
        
        // Highlight class definitions
        code = code.replace(/\b(class)\s+(\w+)/g, '<span class="keyword">$1</span> <span class="function">$2</span>');
        
        block.innerHTML = code;
        block.classList.add('highlighted');
    });
}

// Re-highlight when new content is added
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length) {
            highlightCode();
        }
    });
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});
