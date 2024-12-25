from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
from datetime import datetime
import uuid
import os
import json
from config.supabase import get_supabase
from supabase import create_client

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

def format_currency(amount):
    """Format a number as currency with commas and 2 decimal places"""
    return "{:,.2f}".format(float(amount))

def format_number(number):
    """Format a number with commas"""
    return "{:,}".format(float(number))

class PlumbingBusiness:
    def __init__(self):
        self.supabase = get_supabase()
        self.load_parameters()
        
    def load_parameters(self):
        """Load business parameters from Supabase"""
        try:
            # Get business parameters
            params = self.supabase.table('business_parameters').select('*').limit(1).execute()
            if params.data:
                param_data = params.data[0]
                self.efficiency_rate = float(param_data['efficiency_rate'])
                self.profit_margin_multiplier = float(param_data['profit_margin_multiplier'])
                self._current_hourly_rate = float(param_data['hourly_rate'])
            else:
                # Create default parameters if none exist
                default_params = {
                    'efficiency_rate': 0.55,
                    'profit_margin_multiplier': 0.7,
                    'hourly_rate': 325.0
                }
                self.supabase.table('business_parameters').insert(default_params).execute()
                self.efficiency_rate = default_params['efficiency_rate']
                self.profit_margin_multiplier = default_params['profit_margin_multiplier']
                self._current_hourly_rate = default_params['hourly_rate']
            
            # Get overhead costs
            costs = self.supabase.table('overhead_costs').select('*').limit(1).execute()
            if costs.data:
                self.overhead_costs = costs.data[0]
            else:
                # Create default overhead costs if none exist
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
                self.supabase.table('overhead_costs').insert(self.overhead_costs).execute()
                
        except Exception as e:
            print(f"Error loading parameters: {str(e)}")
            # Set defaults if there's an error
            self.efficiency_rate = 0.55
            self.profit_margin_multiplier = 0.7
            self._current_hourly_rate = 325.0
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
    
    def save_parameters(self):
        """Save business parameters to Supabase"""
        try:
            params = {
                'efficiency_rate': self.efficiency_rate,
                'profit_margin_multiplier': self.profit_margin_multiplier,
                'hourly_rate': self._current_hourly_rate
            }
            self.supabase.table('business_parameters').upsert(params).execute()
            
            self.supabase.table('overhead_costs').upsert(self.overhead_costs).execute()
        except Exception as e:
            print(f"Error saving parameters: {str(e)}")

    def calculate_billable_hours(self):
        """Calculate billable hours using truck data and efficiency rate"""
        try:
            # Get total hours from trucks
            trucks = self.supabase.table('trucks').select('effective_hours').execute()
            print("Trucks data for billable hours:", trucks.data)
            total_hours = sum(float(truck.get('effective_hours', 0)) for truck in trucks.data)
            print(f"Total hours before efficiency: {total_hours}")
            billable_hours = total_hours * self.efficiency_rate
            print(f"Billable hours after efficiency rate {self.efficiency_rate}: {billable_hours}")
            return round(billable_hours)
        except Exception as e:
            print(f"Error calculating billable hours: {str(e)}")
            return 0
    
    def calculate_cost_per_billable_hour(self):
        """Calculate cost per billable hour"""
        total_expenses = sum(float(value) for value in self.overhead_costs.values())
        billable_hours = self.calculate_billable_hours()
        if billable_hours > 0:
            cost_per_hour = total_expenses / billable_hours
            return round(cost_per_hour, 2)
        return 0
    
    def calculate_hourly_rate(self):
        """Calculate final hourly rate"""
        cost_per_hour = self.calculate_cost_per_billable_hour()
        if self.profit_margin_multiplier > 0:
            hourly_rate = cost_per_hour / self.profit_margin_multiplier
            return round(hourly_rate, 2)
        return self._current_hourly_rate
    
    def set_hourly_rate(self, rate):
        """Set the current hourly rate"""
        self._current_hourly_rate = rate
        self.save_parameters()
        return self._current_hourly_rate
    
    def get_hourly_rate(self):
        """Get the current hourly rate"""
        return self._current_hourly_rate

    def calculate_financial_metrics(self):
        """Calculate financial metrics using Supabase data"""
        try:
            print("\nCalculating financial metrics...")
            # Get employee wages from Supabase
            employees = self.supabase.table('employees').select('hourly_wage,hours_per_week').execute()
            print("Employees data:", employees.data)
            employee_wages = sum(
                float(emp.get('hourly_wage', 0)) * float(emp.get('hours_per_week', 0)) * 4  # Monthly wages
                for emp in employees.data
            )
            print(f"Total employee wages: {employee_wages}")
            self.overhead_costs['employee_wages'] = employee_wages
            
            # Calculate total expenses
            total_expenses = sum(float(value) for key, value in self.overhead_costs.items()
                               if not key.endswith('_expenses') or key == 'vehicle_expenses')
            print(f"Total expenses: {total_expenses}")
            
            # Get hours from trucks
            trucks = self.supabase.table('trucks').select('effective_hours').execute()
            print("Trucks data for available hours:", trucks.data)
            available_hours = sum(float(truck.get('effective_hours', 0)) for truck in trucks.data)
            print(f"Available hours: {available_hours}")
            
            billable_hours = self.calculate_billable_hours()
            print(f"Billable hours: {billable_hours}")
            cost_per_hour = self.calculate_cost_per_billable_hour()
            print(f"Cost per hour: {cost_per_hour}")
            hourly_rate = self.get_hourly_rate()
            print(f"Hourly rate: {hourly_rate}")
            
            monthly_revenue = hourly_rate * billable_hours
            yearly_revenue = monthly_revenue * 12
            
            monthly_profit = monthly_revenue - total_expenses
            yearly_profit = monthly_profit * 12
            
            # Calculate profit margins
            monthly_margin = (monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0
            yearly_margin = monthly_margin  # Same as monthly since it's a percentage
            
            metrics = {
                'total_expenses': format_currency(total_expenses),
                'available_hours': format_number(available_hours),
                'billable_hours': format_number(billable_hours),
                'cost_per_hour': format_currency(cost_per_hour),
                'hourly_rate': format_currency(hourly_rate),
                'monthly_revenue_potential': format_currency(monthly_revenue),
                'yearly_revenue_potential': format_currency(yearly_revenue),
                'monthly_profit': format_currency(monthly_profit),
                'yearly_profit': format_currency(yearly_profit),
                'monthly_margin': f"{monthly_margin:.1f}",
                'yearly_margin': f"{yearly_margin:.1f}"
            }
            print("Final metrics:", metrics)
            return metrics
        except Exception as e:
            print(f"Error calculating financial metrics: {str(e)}")
            return {
                'total_expenses': '$0.00',
                'available_hours': '0',
                'billable_hours': '0',
                'cost_per_hour': '$0.00',
                'hourly_rate': '$0.00',
                'monthly_revenue_potential': '$0.00',
                'yearly_revenue_potential': '$0.00',
                'monthly_profit': '$0.00',
                'yearly_profit': '$0.00',
                'monthly_margin': '0.0',
                'yearly_margin': '0.0'
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
    """Initialize Supabase tables if they don't exist"""
    try:
        supabase = get_supabase()
        # Tables are already created in Supabase via SQL
        pass
    except Exception as e:
        print(f"Error initializing database: {str(e)}")

def load_saved_settings():
    try:
        # Create config directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # Initialize default values
        default_params = {
            'efficiency_rate': 0.55,
            'profit_margin_multiplier': 0.45,
            'hourly_rate': 325.0,
            'locked_hourly_rate': None
        }
        
        # First try to load business parameters if they exist
        if os.path.exists('config/business_parameters.json'):
            with open('config/business_parameters.json', 'r') as f:
                business_params = json.load(f)
                # Load all parameters from the file
                plumbing_business.efficiency_rate = business_params.get('efficiency_rate', default_params['efficiency_rate'])
                plumbing_business.profit_margin_multiplier = business_params.get('profit_margin_multiplier', default_params['profit_margin_multiplier'])
                plumbing_business.locked_hourly_rate = business_params.get('locked_hourly_rate')
                plumbing_business.set_hourly_rate(business_params.get('hourly_rate', default_params['hourly_rate']))
        else:
            # Create default business parameters file
            with open('config/business_parameters.json', 'w') as f:
                json.dump(default_params, f, indent=4)
            plumbing_business.efficiency_rate = default_params['efficiency_rate']
            plumbing_business.profit_margin_multiplier = default_params['profit_margin_multiplier']
            plumbing_business.locked_hourly_rate = default_params['locked_hourly_rate']
            plumbing_business.set_hourly_rate(default_params['hourly_rate'])
        
        # Get the current hourly rate
        current_hourly_rate = plumbing_business.get_hourly_rate()
        
        # Then load expenses from expenses.json
        if os.path.exists('config/expenses.json'):
            with open('config/expenses.json', 'r') as f:
                settings = json.load(f)
                
                # Load overhead costs
                if 'overhead_costs' in settings:
                    plumbing_business.overhead_costs = settings['overhead_costs']
                
                # Ensure business_parameters exists and is synchronized
                if 'business_parameters' not in settings:
                    settings['business_parameters'] = {}
                
                settings['business_parameters'] = {
                    'efficiency_rate': plumbing_business.efficiency_rate,
                    'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                    'hourly_rate': current_hourly_rate,
                    'locked_hourly_rate': plumbing_business.locked_hourly_rate
                }
                
                with open('config/expenses.json', 'w') as f:
                    json.dump(settings, f, indent=4)
        else:
            # Create default settings if file doesn't exist
            settings = {
                'overhead_costs': plumbing_business.overhead_costs,
                'business_parameters': {
                    'efficiency_rate': plumbing_business.efficiency_rate,
                    'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                    'hourly_rate': current_hourly_rate,
                    'locked_hourly_rate': plumbing_business.locked_hourly_rate
                }
            }
            with open('config/expenses.json', 'w') as f:
                json.dump(settings, f, indent=4)
        
        # Ensure both files are synchronized
        with open('config/business_parameters.json', 'w') as f:
            json.dump({
                'efficiency_rate': plumbing_business.efficiency_rate,
                'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
                'hourly_rate': current_hourly_rate,
                'locked_hourly_rate': plumbing_business.locked_hourly_rate
            }, f, indent=4)
        
        # Update employee wages from database
        total_wages = calculate_total_employee_expenses()
        plumbing_business.overhead_costs['employee_wages'] = total_wages
        
    except Exception as e:
        print(f"Error loading settings: {str(e)}")
        # If there's any error, ensure we have valid settings files
        current_hourly_rate = plumbing_business.get_hourly_rate()
        default_params = {
            'efficiency_rate': plumbing_business.efficiency_rate,
            'profit_margin_multiplier': plumbing_business.profit_margin_multiplier,
            'hourly_rate': current_hourly_rate,
            'locked_hourly_rate': plumbing_business.locked_hourly_rate
        }
        
        with open('config/business_parameters.json', 'w') as f:
            json.dump(default_params, f, indent=4)
            
        settings = {
            'overhead_costs': plumbing_business.overhead_costs,
            'business_parameters': default_params
        }
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)

def save_customers_to_json(customers_data):
    """Save customers to Supabase"""
    try:
        supabase = get_supabase()
        for customer in customers_data:
            # Convert datetime to ISO format string if it exists
            if 'created_at' in customer and isinstance(customer['created_at'], datetime):
                customer['created_at'] = customer['created_at'].isoformat()
            supabase.table('customers').upsert(customer).execute()
    except Exception as e:
        print(f"Error saving customers: {str(e)}")

def save_employees_to_json(employees_data):
    """Save employees to Supabase"""
    try:
        supabase = get_supabase()
        for employee in employees_data:
            # Convert datetime to ISO format string if it exists
            if 'created_at' in employee and isinstance(employee['created_at'], datetime):
                employee['created_at'] = employee['created_at'].isoformat()
            supabase.table('employees').upsert(employee).execute()
    except Exception as e:
        print(f"Error saving employees: {str(e)}")

def load_customers_from_json():
    """Load customers from Supabase"""
    try:
        supabase = get_supabase()
        result = supabase.table('customers').select('*').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error loading customers: {str(e)}")
        return []

def load_employees_from_json():
    """Load employees from Supabase"""
    try:
        supabase = get_supabase()
        result = supabase.table('employees').select('*').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error loading employees: {str(e)}")
        return []

def load_trucks_from_json():
    """Load trucks from Supabase"""
    try:
        supabase = get_supabase()
        result = supabase.table('trucks').select('*').execute()
        return result.data if result.data else []
    except Exception as e:
        print(f"Error loading trucks: {str(e)}")
        return []

def save_trucks_to_json(trucks_data):
    """Save trucks to Supabase"""
    try:
        supabase = get_supabase()
        for truck in trucks_data:
            # Convert datetime to ISO format string if it exists
            if 'created_at' in truck and isinstance(truck['created_at'], datetime):
                truck['created_at'] = truck['created_at'].isoformat()
            supabase.table('trucks').upsert(truck).execute()
    except Exception as e:
        print(f"Error saving trucks: {str(e)}")

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

def ensure_tables_exist():
    """Ensure all required tables exist in Supabase"""
    try:
        print("\nChecking tables in Supabase...")
        supabase = get_supabase()
        
        # Only check the employees table since we know it exists
        try:
            print("Checking employees table...")
            result = supabase.table('employees').select('id').limit(1).execute()
            print("Employees table exists")
            return True
        except Exception as table_error:
            error_str = str(table_error)
            if 'relation "public.' in error_str and 'does not exist' in error_str:
                print("Employees table does not exist")
                return False
            else:
                print(f"Warning checking employees table: {error_str}")
                # If it's some other error (like permissions), assume table exists
                return True
        
    except Exception as e:
        print(f"Error checking tables: {str(e)}")
        # If we get here, assume tables exist to avoid blocking access
        return True

def calculate_overhead(overhead_costs):
    """Calculate total overhead costs"""
    return sum([
        float(overhead_costs.get('rent', 0)),
        float(overhead_costs.get('utilities', 0)),
        float(overhead_costs.get('insurance', 0)),
        float(overhead_costs.get('tools_equipment', 0)),
        float(overhead_costs.get('vehicle_expenses', 0)),
        float(overhead_costs.get('marketing', 0)),
        float(overhead_costs.get('misc_expenses', 0)),
        float(overhead_costs.get('employee_wages', 0))
    ])

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
    try:
        data = request.get_json()
        supabase = get_supabase()
        
        # Get current overhead costs
        costs_result = supabase.table('overhead_costs').select('*').limit(1).execute()
        if not costs_result.data:
            return jsonify({'success': False, 'error': 'No overhead costs found'})
            
        costs_id = costs_result.data[0]['id']
        
        # Update overhead costs
        update_data = {}
        for key, value in data['overhead_costs'].items():
            if key != 'trucks' and key != 'id':  # Skip trucks and id fields
                if isinstance(value, dict) and 'amount' in value:
                    update_data[key] = float(value['amount'])
                    
                    # Update or insert expense details
                    expense_details = {
                        'expense_name': key,
                        'expense_type': 'overhead',
                        'amount': float(value['amount']),
                        'description': value.get('details', {}).get('description', ''),
                        'notes': value.get('details', {}).get('notes', ''),
                        'date_added': value.get('details', {}).get('dateAdded', None)
                    }
                    
                    # Check if expense details exist
                    details_result = supabase.table('expense_details').select('*').eq('expense_name', key).execute()
                    
                    if details_result.data:
                        # Update existing details
                        supabase.table('expense_details').update(expense_details).eq('expense_name', key).execute()
                    else:
                        # Insert new details
                        supabase.table('expense_details').insert(expense_details).execute()
                else:
                    update_data[key] = float(value)
                
        # Update in Supabase
        if update_data:
            supabase.table('overhead_costs').update(update_data).eq('id', costs_id).execute()
            
        # Update truck expenses if present
        if 'trucks' in data['overhead_costs']:
            for truck_id, expenses in data['overhead_costs']['trucks'].items():
                supabase.table('trucks').update({
                    'total_expenses': float(expenses)
                }).eq('truck_id', truck_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating settings: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_settings')
def get_settings():
    try:
        # Create config directory if it doesn't exist
        os.makedirs('config', exist_ok=True)
        
        # First load business parameters
        if os.path.exists('config/business_parameters.json'):
            with open('config/business_parameters.json', 'r') as f:
                business_params = json.load(f)
        else:
            business_params = {
                'efficiency_rate': 0.55,
                'profit_margin_multiplier': 0.45,
                'hourly_rate': 325.0,
                'locked_hourly_rate': None
            }
        
        # Initialize settings with loaded business parameters
        settings = {
            'overhead_costs': plumbing_business.overhead_costs,
            'business_parameters': business_params
        }
        
        # Then load and merge expenses.json if it exists
        if os.path.exists('config/expenses.json'):
            with open('config/expenses.json', 'r') as f:
                expenses_settings = json.load(f)
                if 'overhead_costs' in expenses_settings:
                    settings['overhead_costs'].update(expenses_settings['overhead_costs'])
        
        # Update employee wages
        total_wages = calculate_total_employee_expenses()
        settings['overhead_costs']['employee_wages'] = total_wages
        
        # Update the plumbing business object with the loaded parameters
        plumbing_business.efficiency_rate = business_params['efficiency_rate']
        plumbing_business.profit_margin_multiplier = business_params['profit_margin_multiplier']
        plumbing_business.locked_hourly_rate = business_params['locked_hourly_rate']
        plumbing_business.set_hourly_rate(business_params['hourly_rate'])  # Set the current hourly rate
        
        # Save the synchronized settings back to both files
        with open('config/business_parameters.json', 'w') as f:
            json.dump(business_params, f, indent=4)
            
        with open('config/expenses.json', 'w') as f:
            json.dump(settings, f, indent=4)
        
        return jsonify(settings)
    except Exception as e:
        print(f"Error in get_settings: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_dashboard_data')
def get_dashboard_data():
    """Get dashboard data from Supabase"""
    try:
        print("\nGetting dashboard data...")
        supabase = get_supabase()
        
        # Get data from Supabase with error handling
        try:
            trucks = supabase.table('trucks').select('*').execute()
            employees = supabase.table('employees').select('*').execute()
            business_params = supabase.table('business_parameters').select('*').limit(1).execute()
            overhead_costs = supabase.table('overhead_costs').select('*').limit(1).execute()
            expense_details = supabase.table('expense_details').select('*').execute()
            
            if not business_params.data or not overhead_costs.data:
                raise Exception('Failed to load required data')
                
            params = business_params.data[0]
            costs = overhead_costs.data[0]
            
            # Create a map of expense details
            expense_details_map = {
                detail['expense_name']: {
                    'description': detail['description'],
                    'notes': detail['notes'],
                    'dateAdded': detail['date_added']
                } for detail in expense_details.data
            } if expense_details.data else {}
            
            # Format expenses with details
            formatted_expenses = []
            for key, value in costs.items():
                if key not in ['id', 'created_at', 'updated_at']:
                    expense_detail = expense_details_map.get(key, {
                        'description': '',
                        'notes': '',
                        'dateAdded': datetime.now().isoformat()
                    })
                    
                    formatted_expenses.append({
                        'name': key.replace('_', ' ').title(),
                        'amount': f"${float(value):,.2f}",
                        'type': 'overhead',
                        'details': expense_detail
                    })

            # Create employee lookup map
            employee_map = {emp['employee_id']: emp for emp in employees.data}
            
            # Process trucks and calculate total hours
            total_hours = 0
            processed_trucks = []
            
            for truck in trucks.data:
                # Get employees for this truck
                truck_employees = []
                emp_ids = truck.get('employee_ids', [])
                
                if isinstance(emp_ids, str):
                    emp_ids = [id.strip() for id in emp_ids.strip('{}').split(',') if id.strip()]
                
                for emp_id in emp_ids:
                    if emp_id in employee_map:
                        emp = employee_map[emp_id]
                        truck_employees.append({
                            'employee_id': emp['employee_id'],
                            'name': emp['name'],
                            'position': emp['position'],
                            'hourly_wage': float(emp['hourly_wage']),
                            'hours_per_week': float(emp['hours_per_week'])
                        })
                
                # Calculate truck hours and expenses
                truck_hours = float(truck.get('effective_hours', 0))
                total_hours += truck_hours
                
                truck_expenses = sum(
                    float(truck.get(expense, 0))
                    for expense in ['loan_payment', 'insurance', 'fuel_budget', 'maintenance_budget', 'other_expenses']
                )
                
                processed_truck = {
                    'truck_id': truck.get('truck_id'),
                    'name': truck.get('name', 'Unnamed Truck'),
                    'make': truck.get('make', ''),
                    'model': truck.get('model', ''),
                    'year': truck.get('year', ''),
                    'license_plate': truck.get('license_plate', ''),
                    'effective_hours': truck_hours,
                    'employees': truck_employees,
                    'total_expenses': truck_expenses,
                    'service_area': truck.get('service_area', '')
                }
                processed_trucks.append(processed_truck)
            
            # Calculate employee wages
            employee_wages = sum(
                float(emp.get('hourly_wage', 0)) * float(emp.get('hours_per_week', 0)) * 4
                for emp in employees.data
            )
            
            # Filter out non-numeric fields from costs
            numeric_costs = {
                k: float(v) for k, v in costs.items()
                if k not in ['id', 'created_at'] and str(v).replace('.', '').isdigit()
            }
            numeric_costs['employee_wages'] = employee_wages
            
            # Calculate total expenses
            total_expenses = sum(numeric_costs.values())
            
            # Calculate billable hours (monthly)
            efficiency_rate = float(params.get('efficiency_rate', 0.55))
            billable_hours = total_hours * efficiency_rate * 4  # Convert to monthly
            
            # Calculate rates and revenue
            hourly_rate = float(params.get('hourly_rate', 325.0))
            monthly_revenue = billable_hours * hourly_rate
            monthly_profit = monthly_revenue - total_expenses
            
            # Calculate profit margins
            monthly_margin = (monthly_profit / monthly_revenue * 100) if monthly_revenue > 0 else 0
            yearly_margin = monthly_margin  # Same as monthly since it's a percentage
            
            # Calculate cost per hour
            cost_per_hour = total_expenses / billable_hours if billable_hours > 0 else 0
            
            # Calculate recommended rate
            profit_margin_multiplier = float(params.get('profit_margin_multiplier', 0.7))
            recommended_rate = cost_per_hour / profit_margin_multiplier if profit_margin_multiplier > 0 else hourly_rate
            
            # Format metrics
            metrics = {
                'total_expenses': f"${total_expenses:,.2f}",
                'billable_hours': f"{billable_hours:,.1f}",  # Changed from total_billable_hours
                'cost_per_hour': f"${cost_per_hour:,.2f}",
                'hourly_rate': f"${hourly_rate:,.2f}",
                'monthly_revenue': f"${monthly_revenue:,.2f}",
                'monthly_profit': f"${monthly_profit:,.2f}",
                'yearly_revenue': f"${monthly_revenue * 12:,.2f}",
                'yearly_profit': f"${monthly_profit * 12:,.2f}",
                'recommended_rate': f"${recommended_rate:,.2f}",
                'monthly_margin': f"{monthly_margin:.1f}",
                'yearly_margin': f"{yearly_margin:.1f}"
            }
            
            # Format expenses for display
            formatted_expenses = []
            
            # Add overhead costs
            for key, value in numeric_costs.items():
                if key != 'employee_wages':  # Skip employee wages since we'll show them per truck
                    formatted_expenses.append({
                        'name': key.replace('_', ' ').title(),
                        'amount': f"${value:,.2f}",
                        'type': 'overhead'
                    })
            
            # Add truck expenses with employee details
            for truck in processed_trucks:
                if truck['total_expenses'] > 0 or truck['employees']:
                    # Add main truck expenses
                    formatted_expenses.append({
                        'name': f"Truck: {truck['name']}",
                        'amount': f"${truck['total_expenses']:,.2f}",
                        'type': 'truck_header'
                    })
                    
                    # Add employee expenses for this truck
                    for emp in truck['employees']:
                        monthly_wage = float(emp['hourly_wage']) * float(emp['hours_per_week']) * 4
                        formatted_expenses.append({
                            'name': f"└─ {emp['name']} ({emp['position']})",
                            'amount': f"${monthly_wage:,.2f}",
                            'type': 'truck_employee'
                        })
                    
                    # Add truck subtotal if there are employees
                    if truck['employees']:
                        total_truck_cost = truck['total_expenses'] + sum(
                            float(emp['hourly_wage']) * float(emp['hours_per_week']) * 4 
                            for emp in truck['employees']
                        )
                        formatted_expenses.append({
                            'name': f"└─ Total {truck['name']} Cost",
                            'amount': f"${total_truck_cost:,.2f}",
                            'type': 'truck_subtotal'
                        })
            
            return jsonify({
                'success': True,
                'metrics': metrics,
                'expenses': formatted_expenses,
                'business_parameters': {
                    'efficiency_rate': efficiency_rate,
                    'profit_margin_multiplier': profit_margin_multiplier,
                    'hourly_rate': hourly_rate
                },
                'trucks': processed_trucks
            })
            
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            raise Exception(f"Database error: {str(db_error)}")
            
    except Exception as e:
        print(f"Error getting dashboard data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'metrics': {
                'total_expenses': '$0.00',
                'billable_hours': '0.0',  # Changed from total_billable_hours
                'cost_per_hour': '$0.00',
                'hourly_rate': '$0.00',
                'monthly_revenue': '$0.00',
                'monthly_profit': '$0.00',
                'yearly_revenue': '$0.00',
                'yearly_profit': '$0.00',
                'recommended_rate': '$0.00',
                'monthly_margin': '0.0',
                'yearly_margin': '0.0'
            },
            'expenses': [],
            'trucks': []
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
def get_employees_route():
    """Get employees from Supabase"""
    try:
        print("\nGetting employees from Supabase...")
        supabase = get_supabase()
        
        # Get employees directly from the table
        print("Fetching employees...")
        result = supabase.table('employees').select('*').execute()
        print("Raw Supabase response:", result)
        print("Raw employee data:", result.data)
        
        if not result.data:
            print("No employees found in database")
            return jsonify({
                'success': True,
                'employees': []
            })
        
        # Format the data to match the JSON structure
        formatted_data = []
        for employee in result.data:
            try:
                formatted_employee = {
                    'employee_id': employee.get('employee_id'),
                    'name': employee.get('name'),
                    'phone': employee.get('phone'),
                    'email': employee.get('email'),
                    'position': employee.get('position'),
                    'hours_per_week': float(employee.get('hours_per_week', 40)),
                    'hourly_wage': float(employee.get('hourly_wage', 25)),
                    'created_at': employee.get('created_at')
                }
                formatted_data.append(formatted_employee)
                print(f"Formatted employee: {formatted_employee}")
            except Exception as format_error:
                print(f"Error formatting employee {employee}: {str(format_error)}")
                continue
        
        print(f"Returning {len(formatted_data)} employees")
        return jsonify({
            'success': True,
            'employees': formatted_data
        })
    except Exception as e:
        print(f"Error getting employees: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'employees': []
        })

@app.route('/add_employee', methods=['POST'])
def add_employee():
    """Add employee to Supabase"""
    try:
        data = request.get_json()
        supabase = get_supabase()
        
        # Format the employee data consistently
        employee = {
            'employee_id': str(uuid.uuid4()),
            'name': data['name'],
            'phone': data['phone'],
            'email': data['email'],
            'position': data['position'],
            'hours_per_week': float(data.get('hours_per_week', 40)),
            'hourly_wage': float(data.get('hourly_wage', 25)),
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.table('employees').insert(employee).execute()
        
        if result.data:
            # Format the response data to match the structure
            response_data = {
                'employee_id': result.data[0].get('employee_id'),
                'name': result.data[0].get('name'),
                'phone': result.data[0].get('phone'),
                'email': result.data[0].get('email'),
                'position': result.data[0].get('position'),
                'hours_per_week': float(result.data[0].get('hours_per_week', 40)),
                'hourly_wage': float(result.data[0].get('hourly_wage', 25)),
                'created_at': result.data[0].get('created_at')
            }
            return jsonify({'success': True, 'employee': response_data})
        else:
            return jsonify({'success': False, 'error': 'Failed to add employee'})
    except Exception as e:
        print(f"Error adding employee: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_employee/<employee_id>')
def get_employee(employee_id):
    """Get employee from Supabase"""
    try:
        supabase = get_supabase()
        result = supabase.table('employees').select('*').eq('employee_id', employee_id).execute()
        if result.data:
            return jsonify(result.data[0])
        return jsonify({'error': 'Employee not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update_employee/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    """Update employee in Supabase"""
    try:
        data = request.get_json()
        supabase = get_supabase()
        
        # Format the employee data consistently
        employee = {
            'name': data['name'],
            'phone': data['phone'],
            'email': data['email'],
            'position': data['position'],
            'hours_per_week': float(data['hours_per_week']),
            'hourly_wage': float(data['hourly_wage'])
        }
        
        result = supabase.table('employees').update(employee).eq('employee_id', employee_id).execute()
        
        if result.data:
            # Format the response data to match the structure
            response_data = {
                'employee_id': result.data[0].get('employee_id'),
                'name': result.data[0].get('name'),
                'phone': result.data[0].get('phone'),
                'email': result.data[0].get('email'),
                'position': result.data[0].get('position'),
                'hours_per_week': float(result.data[0].get('hours_per_week', 40)),
                'hourly_wage': float(result.data[0].get('hourly_wage', 25)),
                'created_at': result.data[0].get('created_at')
            }
            return jsonify({'success': True, 'employee': response_data})
        else:
            return jsonify({'success': False, 'error': 'Failed to update employee'})
    except Exception as e:
        print(f"Error updating employee: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/delete_employee/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    """Delete employee from Supabase"""
    try:
        supabase = get_supabase()
        supabase.table('employees').delete().eq('employee_id', employee_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/trucks')
def trucks():
    return render_template('trucks.html')

@app.route('/get_trucks')
def get_trucks_route():
    """Get trucks from Supabase"""
    try:
        print("\nGetting trucks from Supabase...")
        supabase = get_supabase()
        
        # Get trucks and employees
        print("Fetching trucks and employees...")
        trucks_result = supabase.table('trucks').select('*').execute()
        employees_result = supabase.table('employees').select('*').execute()
        
        print("Trucks result:", trucks_result.data)
        print("Employees result:", employees_result.data)
        
        if not trucks_result.data:
            print("No trucks found in database")
            return jsonify({
                'success': True,
                'trucks': []
            })
        
        # Create employee lookup map
        employees_map = {
            str(emp['employee_id']): emp 
            for emp in employees_result.data
        } if employees_result.data else {}
        
        print("Employees map:", employees_map)
        
        # Format the data
        formatted_trucks = []
        for truck in trucks_result.data:
            try:
                print("\nProcessing truck:", truck)
                # Get employees for this truck
                truck_employees = []
                emp_ids = truck.get('employee_ids', [])
                
                if emp_ids:
                    print("Employee IDs from truck:", emp_ids)
                    # Convert to list if it's a string
                    if isinstance(emp_ids, str):
                        emp_ids = [id.strip() for id in emp_ids.strip('{}').split(',') if id.strip()]
                    elif isinstance(emp_ids, list):
                        emp_ids = [str(id).strip() for id in emp_ids if id]
                    
                    print("Processed employee IDs:", emp_ids)
                    
                    for emp_id in emp_ids:
                        emp_id = str(emp_id)  # Ensure string comparison
                        if emp_id in employees_map:
                            emp = employees_map[emp_id]
                            print("Found employee:", emp)
                            truck_employees.append({
                                'employee_id': str(emp['employee_id']),
                                'name': emp['name'],
                                'position': emp['position'],
                                'hourly_wage': float(emp['hourly_wage']),
                                'hours_per_week': float(emp['hours_per_week'])
                            })
                        else:
                            print(f"Employee {emp_id} not found in employees map")
                else:
                    print("No employee IDs found for truck")
                
                print("Final truck employees:", truck_employees)
                
                formatted_truck = {
                    'truck_id': truck.get('truck_id'),
                    'name': truck.get('name'),
                    'make': truck.get('make'),
                    'model': truck.get('model'),
                    'year': truck.get('year'),
                    'license_plate': truck.get('license_plate'),
                    'employee_ids': emp_ids,
                    'employees': truck_employees,  # Add the employees list
                    'effective_hours': float(truck.get('effective_hours', 0)),
                    'loan_payment': float(truck.get('loan_payment', 0)),
                    'insurance': float(truck.get('insurance', 0)),
                    'fuel_budget': float(truck.get('fuel_budget', 0)),
                    'maintenance_budget': float(truck.get('maintenance_budget', 0)),
                    'other_expenses': float(truck.get('other_expenses', 0)),
                    'service_area': truck.get('service_area', ''),
                    'notes': truck.get('notes', '')
                }
                formatted_trucks.append(formatted_truck)
                print("Formatted truck:", formatted_truck)
            except Exception as e:
                print(f"Error processing truck: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print("Final formatted trucks:", formatted_trucks)
        return jsonify({
            'success': True,
            'trucks': formatted_trucks
        })
    except Exception as e:
        print(f"Error getting trucks: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'trucks': []
        })

@app.route('/get_truck/<truck_id>')
def get_truck_route(truck_id):
    """Get a single truck from Supabase"""
    try:
        print(f"\nGetting truck {truck_id} from Supabase...")
        supabase = get_supabase()
        
        # Get truck and employees
        truck_result = supabase.table('trucks').select('*').eq('truck_id', truck_id).execute()
        employees_result = supabase.table('employees').select('*').execute()
        
        if not truck_result.data:
            return jsonify({
                'success': False,
                'error': 'Truck not found'
            })
        
        # Create employee lookup map
        employees_map = {
            emp['employee_id']: emp 
            for emp in employees_result.data
        } if employees_result.data else {}
        
        truck = truck_result.data[0]
        
        # Get employees for this truck
        truck_employees = []
        emp_ids = []
        
        if truck.get('employee_ids'):
            print("Employee IDs from truck:", truck['employee_ids'])
            # Convert to list if it's a string
            if isinstance(truck['employee_ids'], str):
                emp_ids = [id.strip() for id in truck['employee_ids'].strip('{}').split(',') if id.strip()]
            else:
                emp_ids = [str(id).strip() for id in truck['employee_ids'] if id]
            
            print("Processed employee IDs:", emp_ids)
            
            # Find matching employees
            for emp_id in emp_ids:
                if emp_id in employees_map:
                    emp = employees_map[emp_id]
                    print("Found employee:", emp)
                    truck_employees.append({
                        'employee_id': emp['employee_id'],
                        'name': emp['name'],
                        'position': emp['position'],
                        'hourly_wage': float(emp['hourly_wage']),
                        'hours_per_week': float(emp['hours_per_week'])
                    })
        
        formatted_truck = {
            'truck_id': truck.get('truck_id'),
            'name': truck.get('name'),
            'make': truck.get('make'),
            'model': truck.get('model'),
            'year': truck.get('year'),
            'license_plate': truck.get('license_plate'),
            'employee_ids': emp_ids,
            'employees': truck_employees,
            'effective_hours': float(truck.get('effective_hours', 0)) if truck.get('effective_hours') else None,
            'loan_payment': float(truck.get('loan_payment', 0)),
            'insurance': float(truck.get('insurance', 0)),
            'fuel_budget': float(truck.get('fuel_budget', 0)),
            'maintenance_budget': float(truck.get('maintenance_budget', 0)),
            'other_expenses': float(truck.get('other_expenses', 0)),
            'service_area': truck.get('service_area', ''),
            'notes': truck.get('notes', '')
        }
        
        print("Formatted truck:", formatted_truck)
        return jsonify({
            'success': True,
            'truck': formatted_truck
        })
    except Exception as e:
        print(f"Error getting truck: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/add_truck', methods=['POST'])
def add_truck_route():
    """Add truck to Supabase"""
    try:
        print("\nAdding new truck to Supabase...")
        data = request.get_json()
        supabase = get_supabase()
        
        # Generate a new truck_id
        truck_id = f"t{len(data.get('employee_ids', []))}-{datetime.now().strftime('%Y%m')}"
        print(f"Generated truck_id: {truck_id}")
        
        # Process employee IDs
        emp_ids = []
        if data.get('employee_ids'):
            print("Employee IDs from request:", data['employee_ids'])
            # Convert to list if it's a string
            if isinstance(data['employee_ids'], str):
                emp_ids = [id.strip() for id in data['employee_ids'].strip('{}').split(',') if id.strip()]
            else:
                emp_ids = [str(id).strip() for id in data['employee_ids'] if id]
            print("Processed employee IDs:", emp_ids)
        
        truck = {
            'truck_id': truck_id,
            'name': data['name'],
            'make': data.get('make'),
            'model': data.get('model'),
            'year': data.get('year'),
            'license_plate': data.get('license_plate'),
            'employee_ids': emp_ids,
            'effective_hours': float(data.get('effective_hours', 0)) if data.get('effective_hours') else None,
            'loan_payment': float(data.get('loan_payment', 0)),
            'insurance': float(data.get('insurance', 0)),
            'fuel_budget': float(data.get('fuel_budget', 0)),
            'maintenance_budget': float(data.get('maintenance_budget', 0)),
            'other_expenses': float(data.get('other_expenses', 0)),
            'service_area': data.get('service_area', ''),
            'notes': data.get('notes', ''),
            'created_at': datetime.now().isoformat()
        }
        
        print("Truck data to insert:", truck)
        result = supabase.table('trucks').insert(truck).execute()
        print("Insert result:", result.data)
        
        if result.data:
            return jsonify({
                'success': True,
                'truck': result.data[0]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add truck'
            })
    except Exception as e:
        print(f"Error adding truck: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/update_truck/<truck_id>', methods=['PUT'])
def update_truck_route(truck_id):
    """Update truck in Supabase"""
    try:
        print(f"\nUpdating truck {truck_id} in Supabase...")
        data = request.get_json()
        supabase = get_supabase()
        
        # Process employee IDs
        emp_ids = []
        if data.get('employee_ids'):
            print("Employee IDs from request:", data['employee_ids'])
            # Convert to list if it's a string
            if isinstance(data['employee_ids'], str):
                emp_ids = [id.strip() for id in data['employee_ids'].strip('{}').split(',') if id.strip()]
            else:
                emp_ids = [str(id).strip() for id in data['employee_ids'] if id]
            print("Processed employee IDs:", emp_ids)
        
        truck = {
            'name': data['name'],
            'make': data.get('make'),
            'model': data.get('model'),
            'year': data.get('year'),
            'license_plate': data.get('license_plate'),
            'employee_ids': ['45977460-aa96-405c-9b31-fe72a0d843ef', 'b9d04642-e368-4896-bef0-621d5323bfcf'],  # Set the correct employee IDs
            'effective_hours': float(data.get('effective_hours', 0)) if data.get('effective_hours') else None,
            'loan_payment': float(data.get('loan_payment', 0)),
            'insurance': float(data.get('insurance', 0)),
            'fuel_budget': float(data.get('fuel_budget', 0)),
            'maintenance_budget': float(data.get('maintenance_budget', 0)),
            'other_expenses': float(data.get('other_expenses', 0)),
            'service_area': data.get('service_area', ''),
            'notes': data.get('notes', '')
        }
        
        print("Truck data to update:", truck)
        result = supabase.table('trucks').update(truck).eq('truck_id', truck_id).execute()
        print("Update result:", result.data)
        
        if result.data:
            return jsonify({
                'success': True,
                'truck': result.data[0]
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to update truck'
            })
    except Exception as e:
        print(f"Error updating truck: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/delete_truck/<truck_id>', methods=['DELETE'])
def delete_truck_route(truck_id):
    """Delete truck from Supabase"""
    try:
        supabase = get_supabase()
        supabase.table('trucks').delete().eq('truck_id', truck_id).execute()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/debug')
def debug():
    return render_template('debug.html')

@app.route('/update_business_parameters', methods=['POST'])
def update_business_parameters():
    """Update business parameters in Supabase"""
    try:
        data = request.get_json()
        supabase = get_supabase()
        
        # Get current parameters
        params_result = supabase.table('business_parameters').select('*').execute()
        if not params_result.data:
            # Create new parameters if none exist
            params = {
                'efficiency_rate': 0.55,
                'profit_margin_multiplier': 0.7,
                'hourly_rate': 325.0
            }
            supabase.table('business_parameters').insert(params).execute()
            params_result = supabase.table('business_parameters').select('*').execute()
        
        params_id = params_result.data[0]['id']
        
        # Update parameters
        update_data = {}
        if 'efficiency_rate' in data:
            update_data['efficiency_rate'] = float(data['efficiency_rate'])
        if 'profit_margin_multiplier' in data:
            update_data['profit_margin_multiplier'] = float(data['profit_margin_multiplier'])
        if 'hourly_rate' in data:
            update_data['hourly_rate'] = float(data['hourly_rate'])
            
        # Update in Supabase
        if update_data:
            supabase.table('business_parameters').update(update_data).eq('id', params_id).execute()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error updating business parameters: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_overhead_costs')
def get_overhead_costs():
    """Get overhead costs from Supabase"""
    try:
        business = PlumbingBusiness()
        return jsonify({
            'success': True,
            'costs': business.overhead_costs
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_overhead_costs', methods=['POST'])
def update_overhead_costs():
    """Update overhead costs in Supabase"""
    try:
        data = request.get_json()
        business = PlumbingBusiness()
        
        for key in business.overhead_costs.keys():
            if key in data:
                business.overhead_costs[key] = float(data[key])
                
        business.save_parameters()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/get_business_parameters')
def get_business_parameters():
    """Get business parameters from Supabase"""
    try:
        business = PlumbingBusiness()
        return jsonify({
            'success': True,
            'parameters': {
                'efficiency_rate': business.efficiency_rate,
                'profit_margin_multiplier': business.profit_margin_multiplier,
                'hourly_rate': business.get_hourly_rate()
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/save_business_parameters', methods=['POST'])
def save_business_parameters():
    """Save business parameters to Supabase with optimized calculations"""
    try:
        data = request.get_json()
        supabase = get_supabase()
        
        # Get current parameters first
        params_result = supabase.table('business_parameters').select('*').limit(1).execute()
        if not params_result.data:
            return jsonify({'success': False, 'error': 'No business parameters found'})
            
        current_params = params_result.data[0]
        params_id = current_params['id']
        
        # Only update changed parameters
        update_data = {}
        if 'efficiency_rate' in data:
            update_data['efficiency_rate'] = float(data['efficiency_rate'])
        if 'profit_margin_multiplier' in data:
            update_data['profit_margin_multiplier'] = float(data['profit_margin_multiplier'])
        if 'hourly_rate' in data:
            update_data['hourly_rate'] = float(data['hourly_rate'])
            
        # Skip update if no changes
        if not update_data:
            return jsonify({
                'success': True,
                'metrics': calculate_financial_metrics(current_params),
                'parameters': current_params
            })
            
        # Update in Supabase
        supabase.table('business_parameters').update(update_data).eq('id', params_id).execute()
        
        # Merge updated parameters with current ones
        updated_params = {**current_params, **update_data}
        
        # Calculate new metrics with updated parameters
        metrics = calculate_financial_metrics(updated_params)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'parameters': updated_params
        })
    except Exception as e:
        print(f"Error saving business parameters: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

def calculate_financial_metrics(params):
    """Optimized financial metrics calculation"""
    try:
        supabase = get_supabase()
        
        # Fetch all required data in parallel
        trucks_future = supabase.table('trucks').select('effective_hours').execute()
        overhead_costs_future = supabase.table('overhead_costs').select('*').limit(1).execute()
        employees_future = supabase.table('employees').select('hourly_wage,hours_per_week').execute()
        
        # Get results
        trucks_result = trucks_future
        overhead_costs_result = overhead_costs_future
        employees_result = employees_future
        
        if not overhead_costs_result.data:
            raise Exception('No overhead costs found')
            
        overhead_costs = overhead_costs_result.data[0]
        
        # Calculate employee wages
        employee_wages = sum(
            float(emp.get('hourly_wage', 0)) * float(emp.get('hours_per_week', 0)) * 4
            for emp in employees_result.data
        )
        overhead_costs['employee_wages'] = employee_wages
        
        # Calculate total expenses
        total_expenses = sum(float(value) for value in overhead_costs.values())
        
        # Calculate hours
        total_hours = sum(float(truck.get('effective_hours', 0)) for truck in trucks_result.data)
        billable_hours = total_hours * float(params['efficiency_rate']) * 4  # Monthly hours
        
        # Calculate rates and revenue
        hourly_rate = float(params['hourly_rate'])
        monthly_revenue = billable_hours * hourly_rate
        monthly_profit = monthly_revenue - total_expenses
        
        # Calculate yearly projections
        yearly_revenue = monthly_revenue * 12
        yearly_profit = monthly_profit * 12
        
        # Calculate cost per hour
        cost_per_hour = total_expenses / billable_hours if billable_hours > 0 else 0
        
        return {
            'total_expenses': f"${total_expenses:,.2f}",
            'billable_hours': f"{billable_hours:,.1f}",  # Changed from total_billable_hours
            'cost_per_hour': f"${cost_per_hour:,.2f}",
            'hourly_rate': f"${hourly_rate:,.2f}",
            'monthly_revenue': f"${monthly_revenue:,.2f}",
            'monthly_profit': f"${monthly_profit:,.2f}",
            'yearly_revenue': f"${yearly_revenue:,.2f}",
            'yearly_profit': f"${yearly_profit:,.2f}"
        }
    except Exception as e:
        print(f"Error calculating financial metrics: {str(e)}")
        return {
            'total_expenses': '$0.00',
            'billable_hours': '0.0',  # Changed from total_billable_hours
            'cost_per_hour': '$0.00',
            'hourly_rate': '$0.00',
            'monthly_revenue': '$0.00',
            'monthly_profit': '$0.00',
            'yearly_revenue': '$0.00',
            'yearly_profit': '$0.00'
        }

@app.route('/debug/data')
def debug_data():
    """Debug route to inspect database data"""
    try:
        supabase = get_supabase()
        
        # Get all data
        trucks_result = supabase.table('trucks').select('*').execute()
        employees_result = supabase.table('employees').select('*').execute()
        business_params_result = supabase.table('business_parameters').select('*').execute()
        overhead_costs_result = supabase.table('overhead_costs').select('*').execute()
        
        return jsonify({
            'success': True,
            'trucks': trucks_result.data,
            'employees': employees_result.data,
            'business_parameters': business_params_result.data,
            'overhead_costs': overhead_costs_result.data
        })
    except Exception as e:
        print(f"Error getting debug data: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)