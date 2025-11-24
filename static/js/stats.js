// Statistics page functionality

let currentDays = 7;

document.addEventListener('DOMContentLoaded', function() {
    // Setup time range buttons
    const rangeBtns = document.querySelectorAll('.range-btn');
    rangeBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active from all buttons
            rangeBtns.forEach(b => b.classList.remove('active'));
            // Add active to clicked button
            this.classList.add('active');
            
            // Update current days
            currentDays = parseInt(this.dataset.days);
            
            // Reload charts with new range
            loadReviewData(currentDays);
        });
    });
    
    // Load initial data
    loadReviewData(currentDays);
});

function loadReviewData(days) {
    fetch(`/api/stats/review-history?days=${days}`)
        .then(response => response.json())
        .then(data => {
            createAccuracyChart(data.accuracy, days);
        })
        .catch(error => {
            console.error('Error loading review data:', error);
        });
}

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

function createReviewChart(reviewData, days) {
    const canvas = document.getElementById('reviewChart');
    if (!canvas || !reviewData || reviewData.length === 0) return;
    
    // Update period label
    document.getElementById('chart-period').textContent = `(Last ${days} Days)`;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data - fill in missing dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    const allDates = [];
    const dateMap = new Map();
    
    // Create map of existing data
    reviewData.forEach(d => {
        dateMap.set(d.date, d.count);
    });
    
    // Fill in all dates
    const dataPoints = [];
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        allDates.push(`${d.getMonth() + 1}/${d.getDate()}`);
        dataPoints.push(dateMap.get(dateStr) || 0);
    }
    
    const maxValue = Math.max(...dataPoints, 10);
    
    // Setup canvas
    const theme = document.documentElement.getAttribute('data-theme');
    const isDark = theme === 'dark';
    
    canvas.width = canvas.parentElement.offsetWidth - 40;
    canvas.height = 300;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 60, left: 60 };
    const barWidth = (width - padding.left - padding.right) / dataPoints.length;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw grid lines
    ctx.strokeStyle = isDark ? '#404040' : '#e0e0e0';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
        const value = (maxValue / 5) * i;
        const y = height - padding.bottom - ((value / maxValue) * (height - padding.top - padding.bottom));
        
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
        
        // Y-axis labels
        ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(Math.round(value), padding.left - 10, y + 4);
    }
    
    // Draw bars
    dataPoints.forEach((value, index) => {
        const barHeight = ((value / maxValue) * (height - padding.top - padding.bottom));
        const x = padding.left + (index * barWidth);
        const y = height - padding.bottom - barHeight;
        
        // Bar
        ctx.fillStyle = isDark ? '#4CAF50' : '#2196F3';
        ctx.fillRect(x + 2, y, barWidth - 4, barHeight);
    });
    
    // Draw x-axis labels (show fewer labels for readability)
    ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    
    const labelInterval = Math.ceil(dataPoints.length / 10);
    for (let i = 0; i < allDates.length; i += labelInterval) {
        const x = padding.left + (i * barWidth) + (barWidth / 2);
        ctx.fillText(allDates[i], x, height - padding.bottom + 20);
    }
    
    // Draw axes
    ctx.strokeStyle = isDark ? '#666666' : '#cccccc';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();
}

function createAccuracyChart(accuracyData, days) {
    const canvas = document.getElementById('accuracyChart');
    if (!canvas || !accuracyData || accuracyData.length === 0) return;
    
    // Update period label
    document.getElementById('accuracy-period').textContent = `(Last ${days} Days)`;
    
    const ctx = canvas.getContext('2d');
    
    // Prepare data - fill in missing dates
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(startDate.getDate() - days);
    
    const allDates = [];
    const dateMap = new Map();
    
    // Create map of existing data
    accuracyData.forEach(d => {
        dateMap.set(d.date, d.accuracy);
    });
    
    // Fill in all dates
    const dataPoints = [];
    for (let d = new Date(startDate); d <= endDate; d.setDate(d.getDate() + 1)) {
        const dateStr = d.toISOString().split('T')[0];
        allDates.push(`${d.getMonth() + 1}/${d.getDate()}`);
        const accuracy = dateMap.get(dateStr);
        dataPoints.push(accuracy !== undefined ? accuracy : null);
    }
    
    // Setup canvas
    const theme = document.documentElement.getAttribute('data-theme');
    const isDark = theme === 'dark';
    
    canvas.width = canvas.parentElement.offsetWidth - 40;
    canvas.height = 300;
    
    const width = canvas.width;
    const height = canvas.height;
    const padding = { top: 40, right: 20, bottom: 60, left: 60 };
    
    const graphWidth = width - padding.left - padding.right;
    const graphHeight = height - padding.top - padding.bottom;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw grid lines
    ctx.strokeStyle = isDark ? '#404040' : '#e0e0e0';
    ctx.lineWidth = 1;
    
    for (let i = 0; i <= 5; i++) {
        const value = i * 20; // 0, 20, 40, 60, 80, 100
        const y = height - padding.bottom - ((value / 100) * graphHeight);
        
        ctx.beginPath();
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
        ctx.stroke();
        
        // Y-axis labels
        ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
        ctx.font = '12px Inter, sans-serif';
        ctx.textAlign = 'right';
        ctx.fillText(value + '%', padding.left - 10, y + 4);
    }
    
    // Draw line chart
    ctx.strokeStyle = isDark ? '#66BB6A' : '#4CAF50';
    ctx.lineWidth = 3;
    ctx.beginPath();
    
    let firstPoint = true;
    dataPoints.forEach((value, index) => {
        if (value !== null) {
            const x = padding.left + (index / (dataPoints.length - 1)) * graphWidth;
            const y = height - padding.bottom - ((value / 100) * graphHeight);
            
            if (firstPoint) {
                ctx.moveTo(x, y);
                firstPoint = false;
            } else {
                ctx.lineTo(x, y);
            }
            
            // Draw point
            ctx.fillStyle = isDark ? '#66BB6A' : '#4CAF50';
            ctx.beginPath();
            ctx.arc(x, y, 4, 0, 2 * Math.PI);
            ctx.fill();
        }
    });
    ctx.stroke();
    
    // Draw x-axis labels
    ctx.fillStyle = isDark ? '#b0b0b0' : '#757575';
    ctx.font = '11px Inter, sans-serif';
    ctx.textAlign = 'center';
    
    const labelInterval = Math.ceil(dataPoints.length / 10);
    for (let i = 0; i < allDates.length; i += labelInterval) {
        const x = padding.left + (i / (dataPoints.length - 1)) * graphWidth;
        ctx.fillText(allDates[i], x, height - padding.bottom + 20);
    }
    
    // Draw axes
    ctx.strokeStyle = isDark ? '#666666' : '#cccccc';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(padding.left, padding.top);
    ctx.lineTo(padding.left, height - padding.bottom);
    ctx.lineTo(width - padding.right, height - padding.bottom);
    ctx.stroke();
}

// Redraw charts on theme change
const observer = new MutationObserver(function(mutations) {
    mutations.forEach(function(mutation) {
        if (mutation.attributeName === 'data-theme') {
            loadReviewData(currentDays);
        }
    });
});

observer.observe(document.documentElement, {
    attributes: true
});
