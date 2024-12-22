function saveBusinessParameters(parameters = null, preserveLockState = true) {
    // If no parameters provided, get them from the form
    if (!parameters) {
        parameters = {
            efficiency_rate: parseFloat(document.getElementById('efficiency_rate').value),
            profit_margin_multiplier: parseFloat(document.getElementById('profit_margin_multiplier').value),
            hourly_rate: parseFloat(document.getElementById('hourly_rate').value),
        };
    }
    
    // Add preserve_lock_state parameter
    parameters.preserve_lock_state = preserveLockState;

    fetch('/save_business_parameters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(parameters)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update UI with new metrics
            if (data.metrics) {
                updateMetricsDisplay(data.metrics);
            }
            
            // Update form fields with saved parameters
            if (data.parameters) {
                Object.entries(data.parameters).forEach(([key, value]) => {
                    const input = document.getElementById(key);
                    if (input) {
                        input.value = value;
                    }
                });
            }
            
            // Show success message
            showNotification('Parameters saved successfully', 'success');
        } else {
            showNotification('Error saving parameters: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error saving parameters', 'error');
    });
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.textContent = message;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Remove after 3 seconds
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

function updateMetricsDisplay(metrics) {
    Object.entries(metrics).forEach(([key, value]) => {
        const element = document.getElementById(key);
        if (element) {
            if (typeof value === 'number') {
                element.textContent = value.toFixed(2);
            } else {
                element.textContent = value;
            }
        }
    });
}

// Load and display business parameters
function loadBusinessParameters() {
    fetch('/get_business_parameters')
        .then(response => response.json())
        .then(data => {
            if (data.success && data.parameters) {
                const params = data.parameters;
                
                // Update sliders
                const efficiencySlider = document.getElementById('efficiency-rate-input');
                if (efficiencySlider) {
                    efficiencySlider.value = (params.efficiency_rate * 100).toFixed(0);
                    efficiencySlider.nextElementSibling.textContent = efficiencySlider.value + '%';
                }
                
                const profitMarginSlider = document.getElementById('profit-margin-input');
                if (profitMarginSlider) {
                    profitMarginSlider.value = (params.profit_margin_multiplier * 100).toFixed(0);
                    profitMarginSlider.nextElementSibling.textContent = profitMarginSlider.value + '%';
                }
                
                const hourlyRateSlider = document.getElementById('hourlyRateSlider');
                if (hourlyRateSlider) {
                    hourlyRateSlider.value = params.hourly_rate;
                    hourlyRateSlider.nextElementSibling.querySelector('.param-display').textContent = '$' + params.hourly_rate;
                }
                
                // Update display values
                document.getElementById('hourly-rate').textContent = params.hourly_rate.toFixed(2);
                document.getElementById('recommended-rate').textContent = params.hourly_rate.toFixed(2);
            }
        })
        .catch(error => console.error('Error loading parameters:', error));
}

// Handle slider input (live update)
function handleSliderInput(slider, paramName, valueTransform) {
    const value = valueTransform ? valueTransform(parseFloat(slider.value)) : parseFloat(slider.value);
    const displayValue = paramName === 'hourly_rate' ? '$' + value : (slider.value + '%');
    slider.nextElementSibling.textContent = displayValue;
}

// Handle slider release (save changes)
function handleSliderRelease(slider, paramName, valueTransform) {
    const value = valueTransform ? valueTransform(parseFloat(slider.value)) : parseFloat(slider.value);
    const parameters = {
        [paramName]: value
    };
    saveBusinessParameters(parameters);
}

// Handle hourly rate slider
function handleHourlyRateSlider(slider) {
    const value = parseFloat(slider.value);
    slider.nextElementSibling.querySelector('.param-display').textContent = '$' + value;
    document.getElementById('hourly-rate').textContent = value.toFixed(2);
}

function handleHourlyRateRelease(slider) {
    const value = parseFloat(slider.value);
    saveBusinessParameters({
        hourly_rate: value
    });
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadBusinessParameters();
    
    // Add rate lock button functionality
    const rateLockBtn = document.getElementById('rate-lock-btn');
    if (rateLockBtn) {
        rateLockBtn.addEventListener('click', function() {
            const isLocked = this.querySelector('i').classList.contains('fa-lock');
            this.querySelector('i').classList.toggle('fa-lock');
            this.querySelector('i').classList.toggle('fa-lock-open');
            
            // Save the current hourly rate when locking/unlocking
            const currentRate = parseFloat(document.getElementById('hourly-rate').textContent);
            saveBusinessParameters({
                hourly_rate: currentRate
            }, !isLocked); // preserve lock state is opposite of current state
        });
    }
}); 