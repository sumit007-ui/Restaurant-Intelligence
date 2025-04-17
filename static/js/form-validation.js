// Form validation script

document.addEventListener('DOMContentLoaded', function() {
    // Custom form validation
    const forms = document.querySelectorAll('.needs-validation');
    
    // Loop over each form and prevent submission if not valid
    Array.from(forms).forEach(function(form) {
      form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        
        form.classList.add('was-validated');
      }, false);
    });
    
    // Dish form file input preview
    const imageInput = document.getElementById('image');
    const imagePreview = document.getElementById('image-preview');
    
    if (imageInput && imagePreview) {
      imageInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
          const reader = new FileReader();
          reader.onload = function(e) {
            imagePreview.src = e.target.result;
            imagePreview.style.display = 'block';
          };
          reader.readAsDataURL(file);
        }
      });
    }
    
    // Password confirmation validation
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');
    
    if (password && confirmPassword) {
      confirmPassword.addEventListener('input', function() {
        if (password.value !== confirmPassword.value) {
          confirmPassword.setCustomValidity('Passwords do not match');
        } else {
          confirmPassword.setCustomValidity('');
        }
      });
      
      password.addEventListener('input', function() {
        if (confirmPassword.value) {
          if (password.value !== confirmPassword.value) {
            confirmPassword.setCustomValidity('Passwords do not match');
          } else {
            confirmPassword.setCustomValidity('');
          }
        }
      });
    }
    
    // Daily data form - date validation (no future dates)
    const dateInput = document.getElementById('date');
    if (dateInput) {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      
      dateInput.addEventListener('input', function() {
        const selectedDate = new Date(this.value);
        if (selectedDate > today) {
          this.setCustomValidity('Date cannot be in the future');
        } else {
          this.setCustomValidity('');
        }
      });
      
      // Set max date to today
      const year = today.getFullYear();
      const month = String(today.getMonth() + 1).padStart(2, '0');
      const day = String(today.getDate()).padStart(2, '0');
      dateInput.max = `${year}-${month}-${day}`;
    }
    
    // Price validation (positive numbers only)
    const priceInput = document.getElementById('price');
    if (priceInput) {
      priceInput.addEventListener('input', function() {
        const price = parseFloat(this.value);
        if (price <= 0) {
          this.setCustomValidity('Price must be greater than zero');
        } else {
          this.setCustomValidity('');
        }
      });
    }
    
    // Quantity validation (non-negative numbers only)
    const quantitySoldInput = document.getElementById('quantity_sold');
    const quantityWastedInput = document.getElementById('quantity_wasted');
    
    if (quantitySoldInput) {
      quantitySoldInput.addEventListener('input', function() {
        const quantity = parseInt(this.value);
        if (quantity < 0) {
          this.setCustomValidity('Quantity cannot be negative');
        } else {
          this.setCustomValidity('');
        }
      });
    }
    
    if (quantityWastedInput) {
      quantityWastedInput.addEventListener('input', function() {
        const quantity = parseInt(this.value);
        if (quantity < 0) {
          this.setCustomValidity('Quantity cannot be negative');
        } else {
          this.setCustomValidity('');
        }
      });
    }
    
    // Add dish form validation
    const nameInput = document.getElementById('name');
    if (nameInput) {
      nameInput.addEventListener('input', function() {
        if (this.value.trim() === '') {
          this.setCustomValidity('Dish name cannot be empty');
        } else {
          this.setCustomValidity('');
        }
      });
    }
    
    // Email validation
    const emailInput = document.getElementById('email');
    if (emailInput) {
      emailInput.addEventListener('input', function() {
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailPattern.test(this.value)) {
          this.setCustomValidity('Please enter a valid email address');
        } else {
          this.setCustomValidity('');
        }
      });
    }
  });
  