from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
from datetime import datetime
import sqlite3
import uuid
import os
import json

app = Flask(__name__)

def format_currency(amount):
    """Format a number as currency with commas and 2 decimal places"""
    return "{:,.2f}".format(float(amount))

def format_number(number):
    """Format a number with commas"""
    return "{:,}".format(float(number))

class PlumbingBusiness:
    def __init__(self):
        # Default business parameters
        self.overhead_costs = {
            'rent': 2000,
            'utilities': 500,
            'insurance': 1000,
            'tools_equipment': 500,
            'vehicle_expenses': 800,
            'marketing': 400,
            'misc_expenses': 300,
            'employee_wages': 0
        }
        self.efficiency_rate = 0.55
        self.profit_margin_multiplier = 0.7
        self.locked_hourly_rate = None  # New field for locked rate
        
    def calculate_billable_hours(self):
        """Calculate billable hours using truck data and efficiency rate"""
        total_hours = calculate_total_billable_hours()
        billable_hours = total_hours * self.efficiency_rate
        return round(billable_hours)
    
    def calculate_cost_per_billable_hour(self):
        """Calculate cost per billable hour"""
        total_expenses = sum(self.overhead_costs.values())
        billable_hours = self.calculate_billable_hours()
        if billable_hours > 0:
            cost_per_hour = total_expenses / billable_hours
            return round(cost_per_hour, 2)
        return 0
    
    def calculate_hourly_rate(self):
        """Calculate final hourly rate"""
        if self.locked_hourly_rate is not None:
            return self.locked_hourly_rate
        
        cost_per_hour = self.calculate_cost_per_billable_hour()
        if self.profit_margin_multiplier > 0:
            hourly_rate = cost_per_hour / self.profit_margin_multiplier
            return round(hourly_rate, 2)
        return 0

    def calculate_recommended_hourly_rate(self):
        """Calculate recommended hourly rate regardless of lock"""
        cost_per_hour = self.calculate_cost_per_billable_hour()
        if self.profit_margin_multiplier > 0:
            hourly_rate = cost_per_hour / self.profit_margin_multiplier
            return round(hourly_rate, 2)
        return 0

    def calculate_financial_metrics(self):
        self.overhead_costs['employee_wages'] = calculate_total_employee_expenses()
        total_expenses = sum(self.overhead_costs.values())
        available_hours = calculate_total_billable_hours()
        billable_hours = self.calculate_billable_hours()
        cost_per_hour = self.calculate_cost_per_billable_hour()
        hourly_rate = self.calculate_hourly_rate()
        recommended_rate = self.calculate_recommended_hourly_rate()
        
        monthly_revenue = hourly_rate * billable_hours
        yearly_revenue = monthly_revenue * 12
        
        # Keep profit calculation consistent regardless of lock status
        monthly_profit = monthly_revenue - total_expenses
        yearly_profit = monthly_profit * 12
        
        return {
            'total_expenses': format_currency(total_expenses),
            'available_hours': format_number(available_hours),
            'billable_hours': format_number(billable_hours),
            'cost_per_hour': format_currency(cost_per_hour),
            'hourly_rate': format_currency(hourly_rate),
            'recommended_rate': format_currency(recommended_rate),
            'is_rate_locked': self.locked_hourly_rate is not None,
            'monthly_revenue_potential': format_currency(monthly_revenue),
            'yearly_revenue_potential': format_currency(yearly_revenue),
            'monthly_profit': format_currency(monthly_profit),
            'yearly_profit': format_currency(yearly_profit)
        }

class Job:
    def __init__(self, customer_id, description, estimated_hours, status="pending"):
        self.job_id = str(uuid.uuid4())
        self.customer_id = customer_id
        self.description = description
        self.estimated_hours = estimated_hours
        self.status = status
        self.created_at = datetime.now()
        self.completed_at = None

class Customer:
    def __init__(self, name, address, phone, email):
        self.customer_id = str(uuid.uuid4())
        self.name = name
        self.address = address
        self.phone = phone
        self.email = email
        self.created_at = datetime.now()

class Employee:
    def __init__(self, name, phone, email, position, hours_per_week=40, hourly_wage=25.0):
        self.employee_id = str(uuid.uuid4())
        self.name = name
        self.phone = phone
        self.email = email
        self.position = position
        self.hours_per_week = hours_per_week
        self.hourly_wage = hourly_wage
        self.created_at = datetime.now()

plumbing_business = PlumbingBusiness()

def calculate_total_employee_expenses():
    """Calculate total employee expenses based on truck assignments and effective hours"""
    try:
        trucks = load_trucks_from_json()
        employees = load_employees_from_json()
        total_monthly_wages = 0

        # Create a map of employee IDs to their wage info
        employee_wages = {emp['employee_id']: {
            'hourly_wage': emp['hourly_wage'],
            'hours_per_week': emp['hours_per_week']
        } for emp in employees}

        # Calculate wages based on truck assignments
        for truck in trucks:
            truck_employees = truck.get('employee_ids', [])
            # Calculate total wages for this truck's employees
            for emp_id in truck_employees:
                if emp_id in employee_wages:
                    emp_info = employee_wages[emp_id]
                    # Use the employee's full hours for wage calculation
                    total_monthly_wages += (emp_info['hours_per_week'] * emp_info['hourly_wage'] * 4)

        return total_monthly_wages
    except Exception as e:
        print(f"Error calculating employee expenses: {str(e)}")
        return 0

def calculate_total_billable_hours():
    """Calculate total available hours from all trucks"""
    try:
        trucks = load_trucks_from_json()
        total_hours = 0

        for truck in trucks:
            # Use effective hours if set, otherwise calculate from employees
            if truck.get('effective_hours'):
                total_hours += truck['effective_hours']
            else:
                # If no effective hours set, use sum of employee hours
                employees = [emp for emp in load_employees_from_json() 
                           if emp['employee_id'] in truck.get('employee_ids', [])]
                truck_hours = sum(emp['hours_per_week'] for emp in employees)
                total_hours += truck_hours

        return total_hours * 4  # Convert to monthly hours
    except Exception as e:
        print(f"Error calculating total hours: {str(e)}")
        return 0

def update_employee_wages_in_settings():
    """Update the expenses.json file with current employee wages"""
    try:
        # Calculate total employee wages
        total_wages = calculate_total_employee_expenses()
        
        # Load current settings
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
        
        # Update employee wages in overhead costs
        if 'overhead_costs' not in settings:
            settings['overhead_costs'] = {}
        settings['overhead_costs']['employee_wages'] = total_wages
        
        # Save updated settings
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        # Update the plumbing business object
        plumbing_business.overhead_costs['employee_wages'] = total_wages
        
    except Exception as e:
        print(f"Error updating employee wages in settings: {str(e)}")

def init_db():
    conn = sqlite3.connect('plumbing.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS customers
                 (customer_id TEXT PRIMARY KEY, name TEXT, address TEXT, 
                  phone TEXT, email TEXT, created_at TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS jobs
                 (job_id TEXT PRIMARY KEY, customer_id TEXT, description TEXT,
                  estimated_hours REAL, status TEXT, created_at TIMESTAMP,
                  completed_at TIMESTAMP,
                  FOREIGN KEY (customer_id) REFERENCES customers (customer_id))''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (employee_id TEXT PRIMARY KEY, name TEXT, phone TEXT,
                  email TEXT, position TEXT, hours_per_week REAL,
                  hourly_wage REAL, created_at TIMESTAMP)''')
    conn.commit()
    conn.close()

def load_saved_settings():
    try:
        # Create config directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # First try to load business parameters if they exist
        if os.path.exists('config/business_parameters.json'):
            with open('config/business_parameters.json', 'r') as f:
                business_params = json.load(f)
                plumbing_business.efficiency_rate = business_params.get('efficiency_rate', 0.55)
                plumbing_business.profit_margin_multiplier = business_params.get('profit_margin_multiplier', 0.7)
                # Don't set locked_hourly_rate here - let it be controlled only by the lock button
                
        # Then load other settings from expenses.json
        if os.path.exists('config/expenses.json'):
            with open('config/expenses.json', 'r') as f:
                settings = json.load(f)
                
                # Load overhead costs
                if 'overhead_costs' in settings:
                    plumbing_business.overhead_costs = settings['overhead_costs']
                
                # Load lock status from business parameters
                if 'business_parameters' in settings:
                    plumbing_business.locked_hourly_rate = settings['business_parameters'].get('locked_hourly_rate')
        else:
            # Create default settings if file doesn't exist
            settings = {
                'overhead_costs': plumbing_business.overhead_costs,
                'business_parameters': {
                    'efficiency_rate': plumbing_business.efficiency_rate,
                    'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                    'locked_hourly_rate': None  # Always start unlocked
                }
            }
            with open('config/expenses.json', 'w') as f:
                json.dump(settings, f, indent=4)
        
        # Update employee wages from database
        total_wages = calculate_total_employee_expenses()
        plumbing_business.overhead_costs['employee_wages'] = total_wages
        
    except Exception as e:
        print(f"Error loading settings: {str(e)}")
        # If there's any error, ensure we have a valid settings file
        settings = {
            'overhead_costs': plumbing_business.overhead_costs,
            'business_parameters': {
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                'locked_hourly_rate': None  # Always start unlocked
            }
        }
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)

def save_customers_to_json(customers_data):
    """Save customers directly to JSON file"""
    os.makedirs('config', exist_ok=True)
    with open('config/customers.json', 'w') as f:
        json.dump({'customers': customers_data}, f, indent=4)

def save_employees_to_json(employees_data):
    """Save employees directly to JSON file"""
    os.makedirs('config', exist_ok=True)
    with open('config/employees.json', 'w') as f:
        json.dump({'employees': employees_data}, f, indent=4)

def load_customers_from_json():
    """Load customers from JSON file"""
    try:
        with open('config/customers.json', 'r') as f:
            data = json.load(f)
            return data.get('customers', [])
    except FileNotFoundError:
        save_customers_to_json([])  # Create empty customers file
        return []

def load_employees_from_json():
    """Load employees from JSON file"""
    try:
        with open('config/employees.json', 'r') as f:
            data = json.load(f)
            return data.get('employees', [])
    except FileNotFoundError:
        save_employees_to_json([])  # Create empty employees file
        return []

def load_trucks_from_json():
    """Load trucks from JSON file"""
    try:
        with open('config/trucks.json', 'r') as f:
            data = json.load(f)
            return data.get('trucks', [])
    except FileNotFoundError:
        save_trucks_to_json([])  # Create empty trucks file
        return []

def save_trucks_to_json(trucks_data):
    """Save trucks directly to JSON file"""
    os.makedirs('config', exist_ok=True)
    with open('config/trucks.json', 'w') as f:
        json.dump({'trucks': trucks_data}, f, indent=4)

def calculate_total_vehicle_expenses():
    """Calculate total vehicle expenses from all trucks"""
    try:
        trucks = load_trucks_from_json()
        total_expenses = 0

        for truck in trucks:
            # Sum all truck-related expenses
            truck_expenses = (
                float(truck.get('loan_payment', 0)) +
                float(truck.get('insurance', 0)) +
                float(truck.get('fuel_budget', 0)) +
                float(truck.get('maintenance_budget', 0)) +
                float(truck.get('other_expenses', 0))
            )
            total_expenses += truck_expenses

        return total_expenses
    except Exception as e:
        print(f"Error calculating vehicle expenses: {str(e)}")
        return 0

def update_vehicle_expenses_in_settings():
    """Update the vehicle expenses in settings.json with the total from trucks"""
    try:
        total_vehicle_expenses = calculate_total_vehicle_expenses()
        
        # Load current settings
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
        
        # Update vehicle expenses
        if 'overhead_costs' not in settings:
            settings['overhead_costs'] = {}
        settings['overhead_costs']['vehicle_expenses'] = total_vehicle_expenses
        
        # Save updated settings
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        # Update the plumbing business object
        plumbing_business.overhead_costs['vehicle_expenses'] = total_vehicle_expenses
        
    except Exception as e:
        print(f"Error updating vehicle expenses in settings: {str(e)}")

def calculate_truck_metrics(truck, efficiency_rate, hourly_rate):
    """Calculate all metrics for a truck"""
    # Calculate total available hours
    weekly_hours = truck.get('effective_hours', 0) or sum(float(emp.get('hours_per_week', 0)) for emp in truck.get('employees', []))
    monthly_hours = weekly_hours * 4
    
    # Apply efficiency rate to get billable hours
    monthly_billable_hours = monthly_hours * efficiency_rate
    
    # Calculate crew wages
    crew_wages = sum(
        float(emp.get('hourly_wage', 0)) * float(emp.get('hours_per_week', 0)) * 4
        for emp in truck.get('employees', [])
    )
    
    # Calculate vehicle expenses
    vehicle_expenses = (
        float(truck.get('loan_payment', 0)) +
        float(truck.get('insurance', 0)) +
        float(truck.get('fuel_budget', 0)) +
        float(truck.get('maintenance_budget', 0)) +
        float(truck.get('other_expenses', 0))
    )
    
    # Calculate total expenses
    total_monthly_expenses = crew_wages + vehicle_expenses
    
    # Calculate revenue and profit based on billable hours
    monthly_revenue = monthly_billable_hours * hourly_rate
    monthly_profit = monthly_revenue - total_monthly_expenses
    
    return {
        'weekly_hours': weekly_hours,
        'monthly_hours': monthly_hours,
        'monthly_billable_hours': monthly_billable_hours,
        'monthly_revenue': monthly_revenue,
        'vehicle_expenses': vehicle_expenses,
        'crew_wages': crew_wages,
        'total_monthly_expenses': total_monthly_expenses,
        'monthly_profit': monthly_profit
    }

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/settings')
def settings():
    return render_template('monthly_expenses.html')

@app.route('/business_parameters')
def business_parameters():
    return render_template('business_parameters.html')

@app.route('/update_settings', methods=['POST'])
def update_settings():
    data = request.json
    
    # Update the business object with new values
    plumbing_business.overhead_costs = data['overhead_costs']
    
    # Load current settings to preserve business parameters
    try:
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        settings = {
            'overhead_costs': {},
            'business_parameters': {
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier
            }
        }
    
    # Update only the overhead costs
    settings['overhead_costs'] = plumbing_business.overhead_costs
    
    # Save to file
    os.makedirs('config', exist_ok=True)
    with open('config/expenses.json', 'w') as f:
        json.dump(settings, f, indent=4)
    
    return jsonify({'success': True})

@app.route('/get_settings')
def get_settings():
    try:
        # Create config directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # Try to load existing settings
        if os.path.exists('config/expenses.json'):
            with open('config/expenses.json', 'r') as f:
                settings = json.load(f)
        else:
            # If file doesn't exist, create it with default values
            settings = {
                'overhead_costs': plumbing_business.overhead_costs,
                'business_parameters': {
                    'efficiency_rate': plumbing_business.efficiency_rate,
                    'profit_margin_multiplier': plumbing_business.profit_margin_multiplier
                }
            }
            # Save the default settings
            with open('config/expenses.json', 'w') as f:
                json.dump(settings, f, indent=4)
        
        # Ensure overhead_costs exists in settings
        if 'overhead_costs' not in settings:
            settings['overhead_costs'] = plumbing_business.overhead_costs
        
        # Update employee wages
        total_wages = calculate_total_employee_expenses()
        settings['overhead_costs']['employee_wages'] = total_wages
        
        # Save the updated settings
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        return jsonify(settings)
        
    except Exception as e:
        print(f"Error in get_settings: {str(e)}")
        # Return default values if there's an error
        default_settings = {
            'overhead_costs': {
                'rent': 2000,
                'utilities': 500,
                'insurance': 1000,
                'tools_equipment': 500,
                'vehicle_expenses': 800,
                'marketing': 400,
                'misc_expenses': 300,
                'employee_wages': calculate_total_employee_expenses()
            },
            'business_parameters': {
                'efficiency_rate': 0.55,
                'profit_margin_multiplier': 0.7
            }
        }
        
        # Try to save the default settings
        try:
            with open('config/expenses.json', 'w') as f:
                json.dump(default_settings, f, indent=4)
        except Exception as write_error:
            print(f"Error saving default settings: {str(write_error)}")
        
        return jsonify(default_settings)

@app.route('/get_dashboard_data')
def get_dashboard_data():
    conn = sqlite3.connect('plumbing.db')
    c = conn.cursor()
    
    # Get recent jobs
    c.execute('''SELECT j.*, c.name FROM jobs j
                 JOIN customers c ON j.customer_id = c.customer_id
                 ORDER BY j.created_at DESC LIMIT 5''')
    recent_jobs = c.fetchall()
    
    # Get job statistics
    c.execute('''SELECT status, COUNT(*) FROM jobs GROUP BY status''')
    job_stats = dict(c.fetchall())
    
    conn.close()
    
    # Calculate raw metrics first
    metrics_raw = plumbing_business.calculate_financial_metrics()
    
    # Format overhead costs for display
    formatted_overhead = {k: format_currency(v) for k, v in plumbing_business.overhead_costs.items()}
    
    return jsonify({
        'recent_jobs': recent_jobs,
        'job_stats': job_stats,
        'metrics': metrics_raw,
        'overhead_costs': plumbing_business.overhead_costs,  # Keep raw values for chart
        'business_parameters': {
            'available_hours': calculate_total_billable_hours(),
            'efficiency_rate': plumbing_business.efficiency_rate,
            'profit_margin_multiplier': plumbing_business.profit_margin_multiplier
        }
    })

@app.route('/customers')
def customers():
    return render_template('customers.html')

@app.route('/get_customers')
def get_customers():
    customers = load_customers_from_json()
    return jsonify({'customers': customers})

@app.route('/add_customer', methods=['POST'])
def add_customer():
    data = request.json
    customer = {
        'customer_id': str(uuid.uuid4()),
        'name': data['name'],
        'address': data['address'],
        'phone': data['phone'],
        'email': data['email'],
        'created_at': datetime.now().isoformat()
    }
    
    customers = load_customers_from_json()
    customers.append(customer)
    save_customers_to_json(customers)
    
    return jsonify({'success': True, 'customer_id': customer['customer_id']})

@app.route('/update_customer/<customer_id>', methods=['PUT'])
def update_customer(customer_id):
    data = request.json
    customers = load_customers_from_json()
    
    for customer in customers:
        if customer['customer_id'] == customer_id:
            customer.update({
                'name': data['name'],
                'address': data['address'],
                'phone': data['phone'],
                'email': data['email']
            })
            break
    
    save_customers_to_json(customers)
    return jsonify({'success': True})

@app.route('/delete_customer/<customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    customers = load_customers_from_json()
    customers = [c for c in customers if c['customer_id'] != customer_id]
    save_customers_to_json(customers)
    return jsonify({'success': True})

@app.route('/employees')
def employees():
    return render_template('employees.html')

@app.route('/get_employees')
def get_employees():
    employees = load_employees_from_json()
    return jsonify({'employees': employees})

@app.route('/add_employee', methods=['POST'])
def add_employee():
    data = request.json
    employee = {
        'employee_id': str(uuid.uuid4()),
        'name': data['name'],
        'phone': data['phone'],
        'email': data['email'],
        'position': data['position'],
        'hours_per_week': float(data.get('hours_per_week', 40)),
        'hourly_wage': float(data.get('hourly_wage', 25.0)),
        'created_at': datetime.now().isoformat()
    }
    
    employees = load_employees_from_json()
    employees.append(employee)
    save_employees_to_json(employees)
    
    # Update the expenses.json file with new employee wages
    update_employee_wages_in_settings()
    
    return jsonify({'success': True, 'employee_id': employee['employee_id']})

@app.route('/get_employee/<employee_id>')
def get_employee(employee_id):
    employees = load_employees_from_json()
    employee = next((e for e in employees if e['employee_id'] == employee_id), None)
    
    if employee:
        return jsonify(employee)
    return jsonify({'error': 'Employee not found'}), 404

@app.route('/update_employee/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.json
    employees = load_employees_from_json()
    
    for employee in employees:
        if employee['employee_id'] == employee_id:
            employee.update({
                'name': data['name'],
                'phone': data['phone'],
                'email': data['email'],
                'position': data['position'],
                'hours_per_week': float(data['hours_per_week']),
                'hourly_wage': float(data['hourly_wage'])
            })
            break
    
    save_employees_to_json(employees)
    update_employee_wages_in_settings()
    
    return jsonify({'success': True})

@app.route('/delete_employee/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    employees = load_employees_from_json()
    employees = [e for e in employees if e['employee_id'] != employee_id]
    save_employees_to_json(employees)
    update_employee_wages_in_settings()
    return jsonify({'success': True})

@app.route('/trucks')
def trucks():
    return render_template('trucks.html')

@app.route('/get_trucks')
def get_trucks():
    try:
        trucks = load_trucks_from_json()
        employees = load_employees_from_json()
        
        # Create a map of employee IDs to employee details
        employee_map = {emp['employee_id']: emp for emp in employees}
        
        # Get current business parameters
        efficiency_rate = plumbing_business.efficiency_rate
        hourly_rate = plumbing_business.calculate_hourly_rate()
        
        # Process each truck
        for truck in trucks:
            # Add employee details
            truck['employees'] = []
            for emp_id in truck.get('employee_ids', []):
                if emp_id in employee_map:
                    truck['employees'].append(employee_map[emp_id])
            
            # Calculate metrics
            truck['metrics'] = calculate_truck_metrics(truck, efficiency_rate, hourly_rate)
        
        return jsonify({
            'trucks': trucks,
            'business_parameters': {
                'efficiency_rate': efficiency_rate,
                'hourly_rate': hourly_rate,
                'profit_margin': 1 - plumbing_business.profit_margin_multiplier
            }
        })
    except Exception as e:
        print(f"Error getting trucks: {str(e)}")
        return jsonify({'trucks': []})

@app.route('/get_truck/<truck_id>')
def get_truck(truck_id):
    trucks = load_trucks_from_json()
    truck = next((t for t in trucks if t['truck_id'] == truck_id), None)
    
    if truck:
        employees = load_employees_from_json()
        truck['employees'] = [emp for emp in employees if emp['employee_id'] in truck.get('employee_ids', [])]
        return jsonify(truck)
    return jsonify({'error': 'Truck not found'}), 404

@app.route('/add_truck', methods=['POST'])
def add_truck():
    data = request.json
    truck = {
        'truck_id': str(uuid.uuid4()),
        'name': data['name'],
        'make': data.get('make', ''),
        'model': data.get('model', ''),
        'year': data.get('year', ''),
        'license_plate': data.get('license_plate', ''),
        'loan_payment': float(data.get('loan_payment', 0)),
        'insurance': float(data.get('insurance', 0)),
        'fuel_budget': float(data.get('fuel_budget', 0)),
        'maintenance_budget': float(data.get('maintenance_budget', 0)),
        'other_expenses': float(data.get('other_expenses', 0)),
        'employee_ids': data.get('employee_ids', []),
        'effective_hours': float(data.get('effective_hours', 0)) if data.get('effective_hours') else 0,
        'service_area': data.get('service_area', ''),
        'notes': data.get('notes', ''),
        'created_at': datetime.now().isoformat()
    }
    
    trucks = load_trucks_from_json()
    trucks.append(truck)
    save_trucks_to_json(trucks)
    
    # Update vehicle expenses in settings
    update_vehicle_expenses_in_settings()
    
    return jsonify({'success': True, 'truck_id': truck['truck_id']})

@app.route('/update_truck/<truck_id>', methods=['PUT'])
def update_truck(truck_id):
    try:
        data = request.json
        trucks = load_trucks_from_json()
        
        # Find the truck to update
        truck_found = False
        for truck in trucks:
            if truck['truck_id'] == truck_id:
                truck_found = True
                # Helper function to safely convert to float
                def safe_float(value, default=0):
                    if value is None or (isinstance(value, str) and value.strip() == ''):
                        return default
                    return float(value)
                
                truck.update({
                    'name': data['name'],
                    'make': data.get('make', ''),
                    'model': data.get('model', ''),
                    'year': data.get('year', ''),
                    'license_plate': data.get('license_plate', ''),
                    'loan_payment': safe_float(data.get('loan_payment')),
                    'insurance': safe_float(data.get('insurance')),
                    'fuel_budget': safe_float(data.get('fuel_budget')),
                    'maintenance_budget': safe_float(data.get('maintenance_budget')),
                    'other_expenses': safe_float(data.get('other_expenses')),
                    'employee_ids': data.get('employee_ids', []),
                    'effective_hours': safe_float(data.get('effective_hours'), None),
                    'service_area': data.get('service_area', ''),
                    'notes': data.get('notes', '')
                })
                break
        
        if not truck_found:
            return jsonify({'success': False, 'error': 'Truck not found'}), 404
        
        save_trucks_to_json(trucks)
        
        # Update vehicle expenses in settings
        update_vehicle_expenses_in_settings()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating truck: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/delete_truck/<truck_id>', methods=['DELETE'])
def delete_truck(truck_id):
    trucks = load_trucks_from_json()
    trucks = [t for t in trucks if t['truck_id'] != truck_id]
    save_trucks_to_json(trucks)
    
    # Update vehicle expenses in settings
    update_vehicle_expenses_in_settings()
    
    return jsonify({'success': True})

@app.route('/debug')
def debug():
    return render_template('debug.html')

@app.route('/update_business_parameters', methods=['POST'])
def update_business_parameters():
    try:
        data = request.json
        
        # Update the business object
        plumbing_business.efficiency_rate = float(data.get('efficiency_rate', 0.55))
        plumbing_business.profit_margin_multiplier = 1 - (float(data.get('profit_margin', 30)) / 100)
        
        # Load current settings
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
        
        # Update business parameters
        settings['business_parameters'] = {
            'efficiency_rate': plumbing_business.efficiency_rate,
            'profit_margin_multiplier': plumbing_business.profit_margin_multiplier
        }
        
        # Save to file
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating business parameters: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/update_business_parameter', methods=['POST'])
def update_business_parameter():
    try:
        data = request.json
        parameter = data['parameter']
        value = float(data['value'])
        
        # Load current settings
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
        
        # Update the parameter in settings
        settings['business_parameters'][parameter] = value
        
        # Update the plumbing business object
        if parameter == 'efficiency_rate':
            plumbing_business.efficiency_rate = value
        elif parameter == 'profit_margin_multiplier':
            plumbing_business.profit_margin_multiplier = value
        elif parameter == 'hourly_rate':
            # Don't update locked_hourly_rate here - that should only happen in toggle_hourly_rate_lock
            pass
        
        # Save the updated settings
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        # Save to business_parameters.json as well
        with open('config/business_parameters.json', 'w') as f:
            json.dump({
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                'hourly_rate': value if parameter == 'hourly_rate' else settings['business_parameters'].get('hourly_rate', 125)
            }, f, indent=4)
        
        # Recalculate all metrics
        metrics = plumbing_business.calculate_financial_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'business_parameters': {
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier
            }
        })
    except Exception as e:
        print(f"Error updating business parameter: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/toggle_hourly_rate_lock', methods=['POST'])
def toggle_hourly_rate_lock():
    try:
        data = request.json
        action = data.get('action')  # 'lock' or 'unlock'
        rate = data.get('rate') if action == 'lock' else None
        
        # Load current settings
        with open('config/expenses.json', 'r') as f:
            settings = json.load(f)
        
        # Update the locked rate
        if 'business_parameters' not in settings:
            settings['business_parameters'] = {}
        
        settings['business_parameters']['locked_hourly_rate'] = rate
        plumbing_business.locked_hourly_rate = rate
        
        # Save to file
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        # Recalculate metrics
        metrics = plumbing_business.calculate_financial_metrics()
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        print(f"Error toggling hourly rate lock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_business_parameters', methods=['POST'])
def save_business_parameters():
    try:
        parameters = request.json
        
        # Create config directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # Save to business_parameters.json
        with open('config/business_parameters.json', 'w') as f:
            json.dump(parameters, f, indent=4)
            
        # Also update the business object
        plumbing_business.efficiency_rate = parameters.get('efficiency_rate', 0.55)
        plumbing_business.profit_margin_multiplier = parameters.get('profit_margin_multiplier', 0.7)
        plumbing_business.locked_hourly_rate = parameters.get('hourly_rate')
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error saving business parameters: {str(e)}")  # Server-side log
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_business_parameters', methods=['GET'])
def get_business_parameters():
    try:
        # Try to read existing parameters
        if os.path.exists('config/business_parameters.json'):
            with open('config/business_parameters.json', 'r') as f:
                parameters = json.load(f)
        else:
            # Return current values from business object
            parameters = {
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                'hourly_rate': plumbing_business.locked_hourly_rate or 125
            }
        
        return jsonify({'success': True, 'parameters': parameters})
    except Exception as e:
        print(f"Error loading business parameters: {str(e)}")  # Server-side log
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    # Initialize empty JSON files if they don't exist
    if not os.path.exists('config/customers.json'):
        save_customers_to_json([])
    if not os.path.exists('config/employees.json'):
        save_employees_to_json([])
    if not os.path.exists('config/trucks.json'):
        save_trucks_to_json([])
    load_saved_settings()
    app.run(debug=True)