// Chart.js integration for crime statistics visualizations

// Function to create a bar chart for monthly crime trend
function createMonthlyTrendChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Crimes',
                data: data,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                title: {
                    display: true,
                    text: 'Monthly Crime Trend'
                }
            }
        }
    });
}

// Function to create a pie chart for crime types distribution
function createCrimeTypesChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(255, 99, 132, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(153, 102, 255, 0.7)',
                    'rgba(255, 159, 64, 0.7)',
                    'rgba(199, 199, 199, 0.7)',
                    'rgba(83, 102, 255, 0.7)',
                    'rgba(40, 159, 64, 0.7)',
                    'rgba(210, 199, 199, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 99, 132, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(255, 206, 86, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(153, 102, 255, 1)',
                    'rgba(255, 159, 64, 1)',
                    'rgba(199, 199, 199, 1)',
                    'rgba(83, 102, 255, 1)',
                    'rgba(40, 159, 64, 1)',
                    'rgba(210, 199, 199, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                },
                title: {
                    display: true,
                    text: 'Crime Types Distribution'
                }
            }
        }
    });
}

// Function to create a horizontal bar chart for crime locations
function createLocationChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Number of Crimes',
                data: data,
                backgroundColor: 'rgba(75, 192, 192, 0.5)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }]
        },
        options: {
            indexAxis: 'y',
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: {
                    beginAtZero: true,
                    ticks: {
                        precision: 0
                    }
                }
            },
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Crime Hotspots (Top 10 Locations)'
                }
            }
        }
    });
}

// Function to create a doughnut chart for crime status
function createStatusChart(ctx, labels, data) {
    return new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels.map(label => label.charAt(0).toUpperCase() + label.slice(1)),
            datasets: [{
                data: data,
                backgroundColor: [
                    'rgba(255, 206, 86, 0.7)',
                    'rgba(54, 162, 235, 0.7)',
                    'rgba(75, 192, 192, 0.7)',
                    'rgba(255, 99, 132, 0.7)'
                ],
                borderColor: [
                    'rgba(255, 206, 86, 1)',
                    'rgba(54, 162, 235, 1)',
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                },
                title: {
                    display: true,
                    text: 'Crime Status Distribution'
                }
            }
        }
    });
}

// Initialize dashboard charts when the DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if the elements exist before creating charts
    const monthlyTrendCtx = document.getElementById('monthlyTrendChart');
    const crimeTypesCtx = document.getElementById('crimeTypesChart');
    const locationChartCtx = document.getElementById('locationChart');
    const statusChartCtx = document.getElementById('statusChart');
    
    // Monthly trend chart
    if (monthlyTrendCtx) {
        const labels = JSON.parse(monthlyTrendCtx.getAttribute('data-labels'));
        const data = JSON.parse(monthlyTrendCtx.getAttribute('data-values'));
        createMonthlyTrendChart(monthlyTrendCtx, labels, data);
    }
    
    // Crime types pie chart
    if (crimeTypesCtx) {
        const labels = JSON.parse(crimeTypesCtx.getAttribute('data-labels'));
        const data = JSON.parse(crimeTypesCtx.getAttribute('data-values'));
        createCrimeTypesChart(crimeTypesCtx, labels, data);
    }
    
    // Crime locations chart
    if (locationChartCtx) {
        const labels = JSON.parse(locationChartCtx.getAttribute('data-labels'));
        const data = JSON.parse(locationChartCtx.getAttribute('data-values'));
        createLocationChart(locationChartCtx, labels, data);
    }
    
    // Crime status chart
    if (statusChartCtx) {
        const labels = JSON.parse(statusChartCtx.getAttribute('data-labels'));
        const data = JSON.parse(statusChartCtx.getAttribute('data-values'));
        createStatusChart(statusChartCtx, labels, data);
    }
});
