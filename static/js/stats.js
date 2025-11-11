// Statistics page functionality

document.addEventListener('DOMContentLoaded', function() {
    if (typeof reviewData !== 'undefined' && reviewData.length > 0) {
        createReviewChart();
    }
});

function createReviewChart() {
    const canvas = document.getElementById('reviewChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data
    const labels = reviewData.map(d => {
        const date = new Date(d.date);
        return `${date.getMonth() + 1}/${date.getDate()}`;
    });
    const data = reviewData.map(d => d.count);
    
    const maxValue = Math.max(...data, 10);
    const height = canvas.height;
    const width = canvas.width;
    const barWidth = width / labels.length;
    const padding = 40;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw bars
    data.forEach((value, index) => {
        const barHeight = ((value / maxValue) * (height - padding * 2));
        const x = index * barWidth;
        const y = height - padding - barHeight;
        
        // Bar
        const theme = document.documentElement.getAttribute('data-theme');
        ctx.fillStyle = theme === 'dark' ? '#4CAF50' : '#2196F3';
        ctx.fillRect(x + 5, y, barWidth - 10, barHeight);
        
        // Value label
        ctx.fillStyle = theme === 'dark' ? '#ffffff' : '#333333';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(value, x + barWidth / 2, y - 5);
        
        // Date label
        ctx.fillText(labels[index], x + barWidth / 2, height - 10);
    });
    
    // Y-axis
    ctx.strokeStyle = theme === 'dark' ? '#666666' : '#cccccc';
    ctx.beginPath();
    ctx.moveTo(padding - 10, padding);
    ctx.lineTo(padding - 10, height - padding);
    ctx.stroke();
}

// Redraw chart on theme change
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'data-theme') {
            if (typeof reviewData !== 'undefined' && reviewData.length > 0) {
                createReviewChart();
            }
        }
    });
});

observer.observe(document.documentElement, {
    attributes: true
});
