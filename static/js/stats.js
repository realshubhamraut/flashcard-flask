// Statistics page functionality

document.addEventListener('DOMContentLoaded', function() {
    if (typeof reviewData !== 'undefined' && reviewData.length > 0) {
        createReviewChart();
    }
    
    // Load retention chart
    loadRetentionChart();
});

function loadRetentionChart() {
    fetch('/api/retention-data')
        .then(response => response.json())
        .then(data => {
            createRetentionChart(data);
        })
        .catch(error => {
            console.error('Error loading retention data:', error);
        });
}

function createRetentionChart(data) {
    const canvas = document.getElementById('retentionChart');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Filter historical data to only include non-null values
    const historicalData = data.historical.filter(d => d.retention !== null);
    
    // Combine historical and prediction data
    const allDates = [
        ...historicalData.map(d => d.date),
        ...data.predictions.map(d => d.date)
    ];
    
    const historicalRetention = [
        ...historicalData.map(d => d.retention),
        ...new Array(data.predictions.length).fill(null)
    ];
    
    const predictedRetention = [
        ...new Array(historicalData.length).fill(null),
        historicalData.length > 0 ? historicalData[historicalData.length - 1].retention : null,
        ...data.predictions.map(d => d.predicted_retention)
    ];
    
    const theme = document.documentElement.getAttribute('data-theme');
    const isDark = theme === 'dark';
    
    // Clear and setup canvas
    canvas.width = canvas.parentElement.offsetWidth - 40;
    canvas.height = 350;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 40, bottom: 60, left: 60 };
    
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Find min/max for y-axis (retention %)
    const allValues = [
        ...historicalRetention.filter(v => v !== null),
        ...predictedRetention.filter(v => v !== null)
    ];
    const minRetention = Math.max(0, Math.min(...allValues) - 10);
    const maxRetention = Math.min(100, Math.max(...allValues) + 10);
    
    // Helper functions
    const xScale = (index) => padding.left + (index / (allDates.length - 1)) * graphWidth;
    const yScale = (value) => padding.top + graphHeight - ((value - minRetention) / (maxRetention - minRetention)) * graphHeight;
    
    // Draw grid lines
    ctx.strokeStyle = isDark ? '#404040' : '#e0e0e0';
    ctx.lineWidth = 1;
    
    // Horizontal grid lines (retention %)
    for (let i = 0; i <= 5; i++) {
        const value = minRetention + (maxRetention - minRetention) * (i / 5);
        const y = yScale(value);
        
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
        
        // Y-axis labels
        ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(value) + '%', padding.left - 10, y + 4);
    }
    
    // Draw axes
    ctx.strokeStyle = isDark ? '#666666' : '#cccccc';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();
    
    // Draw historical data line
    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    let firstPoint = true;
    historicalRetention.forEach((value, index) => {
        if (value !== null) {
            const x = xScale(index);
            const y = yScale(value);
            
            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    ctx.stroke();
    
    // Draw prediction line (dashed)
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 3;
    ctx.setLineDash([5, 5]);
    ctx.beginPath();
    
    firstPoint = true;
    predictedRetention.forEach((value, index) => {
        if (value !== null) {
            const x = xScale(index);
            const y = yScale(value);
            
            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
        }
    });
    ctx.stroke();
    ctx.setLineDash([]);
    
    // Draw date labels (every 15 days)
    ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    
    for (let i = 0; i < allDates.length; i += 15) {
        const date = new Date(allDates[i]);
        const label = `${date.getMonth() + 1}/${date.getDate()}`;
        const x = xScale(i);
        
        ctx.fillText(label, x, height - padding.bottom + 20);
    }
    
    // Add "Today" marker
    const todayIndex = historicalData.length - 1;
    if (todayIndex >= 0) {
        const x = xScale(todayIndex);
        
        ctx.strokeStyle = isDark ? '#FFA726' : '#FF9800';
        ctx.lineWidth = 2;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(x, padding.top);
        ctx.lineTo(x, height - padding.bottom);
        ctx.stroke();
        ctx.setLineDash([]);
        
        ctx.fillStyle = isDark ? '#FFA726' : '#FF9800';
        ctx.font = 'bold 11px Inter, sans-serif';
        ctx.fillText('Today', x, padding.top - 10);
    }
    
    // Add average retention text
    if (data.avg_retention) {
        ctx.fillStyle = isDark ? '#e0e0e0' : '#212121';
        ctx.font = 'bold 13px Inter, sans-serif';
        ctx.textAlign = 'left';
        ctx.fillText(`Average Retention: ${data.avg_retention}%`, padding.left, padding.top - 15);
    }
}

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

// Redraw charts on theme change
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'data-theme') {
            if (typeof reviewData !== 'undefined' && reviewData.length > 0) {
                createReviewChart();
            }
            // Reload retention chart
            loadRetentionChart();
        }
    });
});

observer.observe(document.documentElement, {
    attributes: true
});
