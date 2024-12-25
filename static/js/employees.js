// Load and display employees
function loadEmployees() {
    console.log('Loading employees...');
    fetch('/get_employees')
        .then(response => response.json())
        .then(data => {
            console.log('Employees data:', data);
            if (data.success) {
                const employeeTableBody = document.getElementById('employeeTableBody');
                employeeTableBody.innerHTML = '';
                
                data.employees.forEach(employee => {
                    const monthlyWage = employee.hourly_wage * employee.hours_per_week * 4;
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${employee.name}</td>
                        <td>${employee.phone}</td>
                        <td>${employee.email}</td>
                        <td>${employee.position}</td>
                        <td>${employee.hours_per_week}</td>
                        <td>$${employee.hourly_wage.toFixed(2)}</td>
                        <td>$${monthlyWage.toFixed(2)}</td>
                        <td class="text-end">
                            <div class="action-buttons">
                                <button class="btn btn-sm btn-outline-primary" onclick="editEmployee('${employee.employee_id}')">
                                    <i class="fas fa-edit"></i>
                                </button>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteEmployee('${employee.employee_id}')">
                                    <i class="fas fa-trash"></i>
                                </button>
                            </div>
                        </td>
                    `;
                    employeeTableBody.appendChild(row);
                });
            } else {
                console.error('Error loading employees:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Add new employee
function addEmployee(event) {
    event.preventDefault();
    const formData = new FormData(event.target);
    const employeeData = Object.fromEntries(formData.entries());
    
    fetch('/add_employee', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(employeeData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('employeeModal'));
            modal.hide();
            loadEmployees();
        } else {
            console.error('Error adding employee:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Edit employee
function editEmployee(employeeId) {
    fetch(`/get_employee/${employeeId}`)
        .then(response => response.json())
        .then(employee => {
            document.getElementById('employeeId').value = employee.employee_id;
            document.getElementById('employeeName').value = employee.name;
            document.getElementById('employeePhone').value = employee.phone;
            document.getElementById('employeeEmail').value = employee.email;
            document.getElementById('employeePosition').value = employee.position;
            document.getElementById('employeeHours').value = employee.hours_per_week;
            document.getElementById('employeeWage').value = employee.hourly_wage;
            
            const modal = new bootstrap.Modal(document.getElementById('employeeModal'));
            modal.show();
        })
        .catch(error => {
            console.error('Error:', error);
        });
}

// Delete employee
function deleteEmployee(employeeId) {
    if (confirm('Are you sure you want to delete this employee?')) {
        fetch(`/delete_employee/${employeeId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                loadEmployees();
            } else {
                console.error('Error deleting employee:', data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    }
}

// Show add employee modal
function showAddEmployeeModal() {
    document.getElementById('employeeForm').reset();
    document.getElementById('employeeId').value = '';
    const modal = new bootstrap.Modal(document.getElementById('employeeModal'));
    modal.show();
}

// Sort employees
function sortEmployees(by) {
    const tbody = document.getElementById('employeeTableBody');
    const rows = Array.from(tbody.getElementsByTagName('tr'));
    
    rows.sort((a, b) => {
        if (by === 'name') {
            const nameA = a.cells[0].textContent.toLowerCase();
            const nameB = b.cells[0].textContent.toLowerCase();
            return nameA.localeCompare(nameB);
        } else if (by === 'date') {
            // Sort by the hidden created_at value
            const dateA = new Date(a.dataset.createdAt);
            const dateB = new Date(b.dataset.createdAt);
            return dateB - dateA;
        }
    });
    
    rows.forEach(row => tbody.appendChild(row));
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadEmployees();
    
    // Set up form submission handler
    const form = document.getElementById('employeeForm');
    form.addEventListener('submit', addEmployee);
}); 