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

// Load and display dashboard data
function loadDashboardData() {
    fetch('/get_dashboard_data')
        .then(response => response.json())
        .then(data => {
            // Update metrics
            document.getElementById('billable-hours').textContent = data.metrics.billable_hours;
            document.getElementById('hourly-rate').textContent = data.metrics.hourly_rate.replace('$', '');
            document.getElementById('cost-per-hour').textContent = data.metrics.cost_per_hour.replace('$', '');
            document.getElementById('total-expenses').textContent = data.metrics.total_expenses.replace('$', '');
            document.getElementById('monthly-revenue').textContent = data.metrics.monthly_revenue_potential.replace('$', '');
            document.getElementById('monthly-profit').textContent = data.metrics.monthly_profit.replace('$', '');
            document.getElementById('yearly-revenue').textContent = data.metrics.yearly_revenue_potential.replace('$', '');
            document.getElementById('yearly-profit').textContent = data.metrics.yearly_profit.replace('$', '');

            // Calculate and update margins
            const monthlyRevenue = parseFloat(data.metrics.monthly_revenue_potential.replace(/[$,]/g, ''));
            const monthlyProfit = parseFloat(data.metrics.monthly_profit.replace(/[$,]/g, ''));
            const yearlyRevenue = parseFloat(data.metrics.yearly_revenue_potential.replace(/[$,]/g, ''));
            const yearlyProfit = parseFloat(data.metrics.yearly_profit.replace(/[$,]/g, ''));

            const monthlyMargin = monthlyRevenue ? ((monthlyProfit / monthlyRevenue) * 100).toFixed(1) : '0.0';
            const yearlyMargin = yearlyRevenue ? ((yearlyProfit / yearlyRevenue) * 100).toFixed(1) : '0.0';

            document.getElementById('monthly-margin').textContent = monthlyMargin;
            document.getElementById('yearly-margin').textContent = yearlyMargin;

            // Update expenses list
            const expensesList = document.getElementById('expenses-list');
            if (expensesList) {
                expensesList.innerHTML = '';
                
                // Add overhead expenses header
                expensesList.innerHTML += `
                    <tr class="expense-header">
                        <td colspan="2"><strong>Overhead Expenses</strong></td>
                    </tr>
                `;

                // Add overhead expenses
                let overhead = {...data.overhead_costs};
                delete overhead.vehicle_expenses;
                delete overhead.employee_wages;

                let totalOverheadExpenses = 0;
                Object.entries(overhead).forEach(([key, value]) => {
                    if (!key.toLowerCase().includes('vehicle') && !key.toLowerCase().includes('truck')) {
                        const formattedKey = key.replace(/_/g, ' ')
                            .split(' ')
                            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                            .join(' ');
                        const expenseValue = parseFloat(value) || 0;
                        totalOverheadExpenses += expenseValue;
                        
                        expensesList.innerHTML += `
                            <tr class="overhead-expense">
                                <td>${formattedKey}</td>
                                <td class="text-end">${formatCurrency(expenseValue)}</td>
                            </tr>
                        `;
                    }
                });

                // Add overhead expenses subtotal
                expensesList.innerHTML += `
                    <tr class="expense-subtotal">
                        <td>Total Overhead Expenses</td>
                        <td class="text-end">${formatCurrency(totalOverheadExpenses)}</td>
                    </tr>
                `;

                // Add truck expenses header
                expensesList.innerHTML += `
                    <tr class="expense-header">
                        <td colspan="2"><strong>Vehicle Expenses</strong></td>
                    </tr>
                `;

                // Add truck expenses
                let totalTruckExpenses = 0;
                data.trucks.forEach(truck => {
                    const truckExpenses = (
                        parseFloat(truck.loan_payment || 0) +
                        parseFloat(truck.insurance || 0) +
                        parseFloat(truck.fuel_budget || 0) +
                        parseFloat(truck.maintenance_budget || 0) +
                        parseFloat(truck.other_expenses || 0)
                    );
                    totalTruckExpenses += truckExpenses;

                    expensesList.innerHTML += `
                        <tr class="truck-expense-item">
                            <td>
                                <div>${truck.name}</div>
                                <small class="text-muted">Loan, Insurance, Fuel, Maintenance</small>
                            </td>
                            <td class="text-end">${formatCurrency(truckExpenses)}</td>
                        </tr>
                    `;
                });

                // Add truck expenses subtotal
                expensesList.innerHTML += `
                    <tr class="expense-subtotal">
                        <td>Total Vehicle Expenses</td>
                        <td class="text-end">${formatCurrency(totalTruckExpenses)}</td>
                    </tr>
                `;

                // Add employee wages if they exist
                const employeeWages = parseFloat(data.overhead_costs.employee_wages) || 0;
                if (employeeWages > 0 || data.employees.length > 0) {
                    expensesList.innerHTML += `
                        <tr class="expense-header">
                            <td colspan="2"><strong>Employee Wages</strong></td>
                        </tr>
                    `;

                    // Add individual employee breakdown
                    data.employees.forEach(employee => {
                        const monthlyWage = parseFloat(employee.hourly_wage) * parseFloat(employee.hours_per_week) * 4; // 4 weeks per month
                        expensesList.innerHTML += `
                            <tr class="truck-expense-item">
                                <td>
                                    <div>${employee.name}</div>
                                    <small class="text-muted">${employee.position} - ${employee.hours_per_week}hrs/week @ $${employee.hourly_wage}/hr</small>
                                </td>
                                <td class="text-end">${formatCurrency(monthlyWage)}</td>
                            </tr>
                        `;
                    });

                    expensesList.innerHTML += `
                        <tr class="expense-subtotal">
                            <td>Total Employee Wages</td>
                            <td class="text-end">${formatCurrency(employeeWages)}</td>
                        </tr>
                    `;
                }

                // Add total expenses
                const totalExpenses = totalOverheadExpenses + totalTruckExpenses + employeeWages;
                document.getElementById('expenses-total-value').textContent = formatCurrency(totalExpenses);
            }

            // Update trucks overview
            const trucksOverview = document.getElementById('trucks-overview');
            if (trucksOverview) {
                trucksOverview.innerHTML = '';
                data.trucks.forEach(truck => {
                    const truckCard = document.createElement('div');
                    truckCard.className = 'truck-card';
                    
                    // Find employees assigned to this truck
                    const truckEmployees = truck.employees || [];
                    
                    truckCard.innerHTML = `
                        <div class="truck-header">
                            <h6>${truck.name}</h6>
                            <span class="status ${truck.status}">${truck.status}</span>
                        </div>
                        <div class="truck-details">
                            <div class="detail-item">
                                <span class="label">Hours:</span>
                                <span class="value">${truck.effective_hours} hrs/week</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Area:</span>
                                <span class="value">${truck.service_area || 'N/A'}</span>
                            </div>
                            <div class="detail-item">
                                <span class="label">Team:</span>
                                <span class="value">${truckEmployees.length > 0 ? truckEmployees.map(emp => emp.name).join(', ') : 'No team members assigned'}</span>
                            </div>
                        </div>
                    `;
                    trucksOverview.appendChild(truckCard);
                });
            }

            // Update truck summary
            document.getElementById('total-employees').textContent = `${data.truck_summary.total_employees} employees`;
            document.getElementById('total-hours').textContent = `${data.truck_summary.total_weekly_hours} hrs`;
            document.getElementById('total-truck-expenses').textContent = formatCurrency(data.truck_summary.total_monthly_expenses);

            // Update business parameters
            const efficiencySlider = document.getElementById('efficiency-rate-input');
            if (efficiencySlider) {
                const efficiencyRate = data.business_parameters.efficiency_rate * 100;
                efficiencySlider.value = efficiencyRate;
                efficiencySlider.nextElementSibling.textContent = efficiencyRate.toFixed(0) + '%';
            }

            const profitMarginSlider = document.getElementById('profit-margin-input');
            if (profitMarginSlider) {
                const profitMargin = data.business_parameters.profit_margin_multiplier * 100;
                profitMarginSlider.value = profitMargin;
                profitMarginSlider.nextElementSibling.textContent = profitMargin.toFixed(0) + '%';
            }
        })
        .catch(error => console.error('Error loading dashboard data:', error));
}

function formatCurrency(amount) {
    return `$${parseFloat(amount).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    
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

    // Refresh dashboard data every 30 seconds
    setInterval(loadDashboardData, 30000);
});

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