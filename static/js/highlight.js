// Use highlight.js library for Python syntax highlighting
document.addEventListener('DOMContentLoaded', function() {
    highlightCode();
});

function highlightCode() {
    // Use highlight.js library to highlight all code blocks
    const codeBlocks = document.querySelectorAll('.code-block code');
    
    codeBlocks.forEach(block => {
        if (block.classList.contains('highlighted')) return;
        
        // Use highlight.js library
        if (typeof hljs !== 'undefined') {
            hljs.highlightElement(block);
        }
        
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
