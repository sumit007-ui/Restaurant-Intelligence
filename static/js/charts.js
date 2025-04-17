// Charts.js - Advanced visualization with elegant animations

// Render Sales by Day of Week Chart
function renderSalesByDayChart(data) {
    const ctx = document.getElementById('salesByDayChart');
    if (!ctx) return;
  
    // Destroy existing chart if it exists
    if (window.salesByDayChart && typeof window.salesByDayChart.destroy === 'function') {
      window.salesByDayChart.destroy();
    } else {
      window.salesByDayChart = null;
    }
  
    const dayColors = [
      'rgba(123, 84, 39, 0.8)',
      'rgba(224, 159, 62, 0.8)',
      'rgba(93, 162, 113, 0.8)',
      'rgba(78, 76, 170, 0.8)',
      'rgba(211, 93, 110, 0.8)',
      'rgba(245, 150, 40, 0.8)',
      'rgba(137, 123, 200, 0.8)'
    ];
  
    window.salesByDayChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.labels || [],
        datasets: [{
          label: 'Sales by Day of Week',
          data: data.values || [],
          backgroundColor: dayColors,
          borderColor: dayColors.map(color => color.replace('0.8', '1')),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.dataset.label || '';
                if (label) {
                  label += ': ';
                }
                label += context.parsed.y + ' units';
                return label;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              precision: 0
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }
  
  // Render Sales by Category Chart
  function renderSalesByCategoryChart(data) {
    const ctx = document.getElementById('salesByCategoryChart');
    if (!ctx) return;
  
    // Destroy existing chart if it exists
    if (window.salesByCategoryChart && typeof window.salesByCategoryChart.destroy === 'function') {
      window.salesByCategoryChart.destroy();
    } else {
      window.salesByCategoryChart = null;
    }
  
    const categoryColors = [
      'rgba(123, 84, 39, 0.8)',
      'rgba(224, 159, 62, 0.8)',
      'rgba(93, 162, 113, 0.8)',
      'rgba(78, 76, 170, 0.8)',
      'rgba(211, 93, 110, 0.8)'
    ];
  
    window.salesByCategoryChart = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels: data.labels || [],
        datasets: [{
          data: data.values || [],
          backgroundColor: categoryColors,
          borderColor: categoryColors.map(color => color.replace('0.8', '1')),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              padding: 20,
              boxWidth: 10
            }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const value = context.raw;
                const percentage = ((value / total) * 100).toFixed(1);
                return `${context.label}: ${value} units (${percentage}%)`;
              }
            }
          }
        },
        cutout: '70%'
      }
    });
  }
  
  // Render Daily Trend Chart
  function renderDailyTrendChart(data) {
    const ctx = document.getElementById('dailyTrendChart');
    if (!ctx) return;
  
    // Parse data from JSON string if needed
    let chartData = data;
    if (typeof data === 'string') {
      try {
        chartData = JSON.parse(data);
      } catch (e) {
        console.error('Error parsing chart data:', e);
        return;
      }
    }
  
    // Destroy existing chart if it exists
    if (window.dailyTrendChart && typeof window.dailyTrendChart.destroy === 'function') {
      window.dailyTrendChart.destroy();
    } else {
      window.dailyTrendChart = null;
    }
  
    // Extract dates and values
    const dates = chartData.map(item => item.date);
    const values = chartData.map(item => item.total_sold);
  
    window.dailyTrendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: dates,
        datasets: [{
          label: 'Daily Sales',
          data: values,
          backgroundColor: 'rgba(123, 84, 39, 0.1)',
          borderColor: 'rgba(123, 84, 39, 0.8)',
          tension: 0.4,
          fill: true,
          pointBackgroundColor: 'rgba(123, 84, 39, 1)',
          pointRadius: 4,
          pointHoverRadius: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          },
          tooltip: {
            mode: 'index',
            intersect: false,
            callbacks: {
              label: function(context) {
                return `Sales: ${context.parsed.y} units`;
              }
            }
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              precision: 0
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }
  
  // Render Dish Performance Chart
  function renderDishPerformanceChart(dishId, salesData, wasteData) {
    const ctx = document.getElementById(`dishPerformanceChart-${dishId}`);
    if (!ctx) return;
  
    // Destroy existing chart if it exists
    if (window[`dishPerformanceChart-${dishId}`] && typeof window[`dishPerformanceChart-${dishId}`].destroy === 'function') {
      window[`dishPerformanceChart-${dishId}`].destroy();
    } else {
      window[`dishPerformanceChart-${dishId}`] = null;
    }
  
    window[`dishPerformanceChart-${dishId}`] = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: salesData.map(item => item.day),
        datasets: [
          {
            label: 'Average Sales',
            data: salesData.map(item => item.avg_sales),
            backgroundColor: 'rgba(93, 162, 113, 0.8)',
            borderColor: 'rgba(93, 162, 113, 1)',
            borderWidth: 1,
            order: 1
          },
          {
            label: 'Average Waste',
            data: wasteData.map(item => item.avg_waste),
            backgroundColor: 'rgba(211, 93, 110, 0.8)',
            borderColor: 'rgba(211, 93, 110, 1)',
            borderWidth: 1,
            order: 2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'top'
          },
          tooltip: {
            mode: 'index',
            intersect: false
          }
        },
        scales: {
          y: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            }
          },
          x: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }
  
  // Render Top Selling Dishes Chart
  function renderTopSellingChart(data) {
    const ctx = document.getElementById('topSellingChart');
    if (!ctx) return;
  
    // Destroy existing chart if it exists
    if (window.topSellingChart && typeof window.topSellingChart.destroy === 'function') {
      window.topSellingChart.destroy();
    } else {
      window.topSellingChart = null;
    }
  
    // Generate colors for each dish
    const dishColors = data.map((_, index) => {
      const hue = (index * 45) % 360;
      return `hsla(${hue}, 70%, 50%, 0.8)`;
    });
  
    window.topSellingChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(item => item.name),
        datasets: [{
          label: 'Units Sold',
          data: data.map(item => item.total_sold),
          backgroundColor: dishColors,
          borderColor: dishColors.map(color => color.replace('0.8', '1')),
          borderWidth: 1
        }]
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false
          }
        },
        scales: {
          x: {
            beginAtZero: true,
            grid: {
              color: 'rgba(0, 0, 0, 0.05)'
            },
            ticks: {
              precision: 0
            }
          },
          y: {
            grid: {
              display: false
            }
          }
        }
      }
    });
  }
  
  // Initialize charts when document is ready
  document.addEventListener('DOMContentLoaded', function() {
    // Initialize trending chart if data exists
    const dailyTrendElement = document.getElementById('dailyTrendChart');
    if (dailyTrendElement && dailyTrendElement.dataset.chartData) {
      renderDailyTrendChart(dailyTrendElement.dataset.chartData);
    }
    
    // Initialize top selling chart if data exists
    const topSellingElement = document.getElementById('topSellingChart');
    if (topSellingElement && topSellingElement.dataset.chartData) {
      renderTopSellingChart(JSON.parse(topSellingElement.dataset.chartData));
    }
    
    // Initialize dish performance charts
    document.querySelectorAll('[id^="dishPerformanceChart-"]').forEach(chart => {
      const dishId = chart.id.split('-')[1];
      const salesData = JSON.parse(chart.dataset.salesData || '[]');
      const wasteData = JSON.parse(chart.dataset.wasteData || '[]');
      renderDishPerformanceChart(dishId, salesData, wasteData);
    });
  });
  