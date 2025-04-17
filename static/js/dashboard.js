// Dashboard.js - Handles dashboard interactivity with luxury animations

document.addEventListener('DOMContentLoaded', function() {
    // Initialize AOS animation library
    AOS.init({
      duration: 800,
      easing: 'ease',
      once: true
    });
    
    // Toggle sidebar with elegant animation
    const toggleSidebarBtn = document.getElementById('toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const mainContent = document.querySelector('.main-content');
    const sidebarOverlay = document.querySelector('.sidebar-overlay');
  
    if (toggleSidebarBtn) {
      toggleSidebarBtn.addEventListener('click', function() {
        sidebar.classList.toggle('show');
        
        // Handle overlay for mobile
        if (window.innerWidth < 768) {
          if (!sidebarOverlay) {
            const overlay = document.createElement('div');
            overlay.classList.add('sidebar-overlay');
            document.body.appendChild(overlay);
            
            overlay.addEventListener('click', function() {
              sidebar.classList.remove('show');
              this.remove();
            });
          }
        }
      });
    }
  
    // Initialize Bootstrap tooltips & popovers for premium feel
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  
    // Initialize Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
      return new bootstrap.Popover(popoverTriggerEl);
    });
  
    // Active link highlighting
    const currentLocation = window.location.pathname;
    const sidebarLinks = document.querySelectorAll('.sidebar-link');
    
    sidebarLinks.forEach(link => {
      const linkPath = link.getAttribute('href');
      if (currentLocation === linkPath) {
        link.classList.add('active');
      }
    });
  
    // Load dashboard data
    if (document.getElementById('salesByDayChart') || document.getElementById('salesByCategoryChart')) {
      fetchDashboardData();
    }
  
    // Handle date range picker for reports if available
    const dateRangePicker = document.getElementById('reportDateRange');
    if (dateRangePicker) {
      const start = moment().subtract(29, 'days');
      const end = moment();
  
      function cb(start, end) {
        dateRangePicker.innerHTML = start.format('MMM D, YYYY') + ' - ' + end.format('MMM D, YYYY');
      }
  
      $(dateRangePicker).daterangepicker({
        startDate: start,
        endDate: end,
        ranges: {
          'Today': [moment(), moment()],
          'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
          'Last 7 Days': [moment().subtract(6, 'days'), moment()],
          'Last 30 Days': [moment().subtract(29, 'days'), moment()],
          'This Month': [moment().startOf('month'), moment().endOf('month')],
          'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        }
      }, cb);
  
      cb(start, end);
    }
  
    // Display toast notifications
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
      const category = message.dataset.category;
      const text = message.textContent;
      
      // Create and show toast
      showToast(category, text);
      
      // Remove the element to prevent duplication
      message.remove();
    });
  });
  
  // Function to fetch dashboard data from API
  function fetchDashboardData() {
    fetch('/api/dashboard-data')
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        // Render charts with the data
        renderSalesByDayChart(data.salesByDay);
        renderSalesByCategoryChart(data.salesByCategory);
      })
      .catch(error => {
        console.error('Error fetching dashboard data:', error);
        showToast('error', 'Failed to load dashboard data');
      });
  }
  
  // Show toast notification
  function showToast(category, message) {
    const toastContainer = document.querySelector('.toast-container');
    
    // Create container if it doesn't exist
    if (!toastContainer) {
      const container = document.createElement('div');
      container.classList.add('toast-container');
      document.body.appendChild(container);
    }
    
    // Map category to icon and color
    const iconMap = {
      'success': 'check-circle',
      'error': 'x-circle',
      'danger': 'x-circle',
      'warning': 'alert-triangle',
      'info': 'info'
    };
    
    const titleMap = {
      'success': 'Success',
      'error': 'Error',
      'danger': 'Error',
      'warning': 'Warning',
      'info': 'Information'
    };
    
    // Default to info if category not found
    const icon = iconMap[category] || 'info';
    const title = titleMap[category] || 'Information';
    
    // Create toast element
    const toast = document.createElement('div');
    toast.classList.add('toast', `toast-${category}`);
    toast.innerHTML = `
      <div class="toast-icon">
        <i data-feather="${icon}"></i>
      </div>
      <div class="toast-content">
        <div class="toast-title">${title}</div>
        <div class="toast-message">${message}</div>
      </div>
      <button class="toast-close" onclick="this.parentElement.remove()">
        <i data-feather="x"></i>
      </button>
    `;
    
    // Add to container
    document.querySelector('.toast-container').appendChild(toast);
    
    // Initialize Feather icons
    if (window.feather) {
      feather.replace();
    }
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
      toast.remove();
    }, 5000);
  }
  
  // Fetch dish predictions for a specific dish, day, and time
  function fetchDishPrediction(dishId, day, time) {
    const url = `/api/dish-predictions/${dishId}?day=${day}&time=${time}`;
    
    fetch(url)
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        // Update prediction display
        updatePredictionDisplay(data);
      })
      .catch(error => {
        console.error('Error fetching dish prediction:', error);
        showToast('error', 'Failed to load prediction data');
      });
  }
  
  // Update the prediction display with the received data
  function updatePredictionDisplay(data) {
    const predictionContainer = document.getElementById('prediction-container');
    if (!predictionContainer) return;
    
    const predictionClass = `prediction-${data.sales_prediction}`;
    const wasteClass = `prediction-${data.waste_prediction}`;
    
    predictionContainer.innerHTML = `
      <div class="card">
        <div class="card-header">
          <h5 class="card-title">Prediction for ${data.dish_name}</h5>
          <p class="text-muted">${data.day_name}, ${data.time_of_day}</p>
        </div>
        <div class="card-body">
          <div class="row">
            <div class="col-md-6">
              <div class="prediction-item">
                <h6>Sales Prediction</h6>
                <span class="badge ${predictionClass}">${data.sales_prediction.toUpperCase()}</span>
                <div class="progress mt-2">
                  <div class="progress-bar bg-${data.sales_prediction === 'high' ? 'success' : (data.sales_prediction === 'moderate' ? 'warning' : 'danger')}" 
                       style="width: ${data.sales_confidence}%" 
                       aria-valuenow="${data.sales_confidence}" 
                       aria-valuemin="0" 
                       aria-valuemax="100"></div>
                </div>
                <small class="text-muted">${Math.round(data.sales_confidence)}% confidence</small>
              </div>
            </div>
            <div class="col-md-6">
              <div class="prediction-item">
                <h6>Waste Prediction</h6>
                <span class="badge ${wasteClass}">${data.waste_prediction.toUpperCase()}</span>
                <div class="progress mt-2">
                  <div class="progress-bar bg-${data.waste_prediction === 'low' ? 'success' : (data.waste_prediction === 'moderate' ? 'warning' : 'danger')}" 
                       style="width: ${data.waste_confidence}%" 
                       aria-valuenow="${data.waste_confidence}" 
                       aria-valuemin="0" 
                       aria-valuemax="100"></div>
                </div>
                <small class="text-muted">${Math.round(data.waste_confidence)}% confidence</small>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  