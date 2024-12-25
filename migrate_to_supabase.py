import json
import os
from datetime import datetime
import uuid
from supabase import create_client, Client

# Supabase credentials
SUPABASE_URL = "https://wcviuqikbxjkrmjecasu.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Indjdml1cWlrYnhqa3JtamVjYXN1Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNTA2NDgwOCwiZXhwIjoyMDUwNjQwODA4fQ.LobS_8PlchtU9zZR52pGX3e9YZgk_VbY3SXz-BxiqiY"

def get_supabase():
    """Initialize Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def migrate_business_parameters():
    """Migrate business parameters to Supabase"""
    try:
        with open('config/business_parameters.json', 'r') as f:
            data = json.load(f)
        
        supabase = get_supabase()
        
        # Check if parameters already exist
        existing = supabase.table('business_parameters').select('*').execute()
        if existing.data:
            # Update existing parameters
            supabase.table('business_parameters').update({
                'efficiency_rate': float(data.get('efficiency_rate', 0.4)),
                'profit_margin_multiplier': float(data.get('profit_margin_multiplier', 0.25)),
                'hourly_rate': float(data.get('hourly_rate', 450.0))
            }).eq('id', existing.data[0]['id']).execute()
        else:
            # Insert new parameters
            supabase.table('business_parameters').insert({
                'efficiency_rate': float(data.get('efficiency_rate', 0.4)),
                'profit_margin_multiplier': float(data.get('profit_margin_multiplier', 0.25)),
                'hourly_rate': float(data.get('hourly_rate', 450.0))
            }).execute()
        print("Business parameters migrated successfully")
    except Exception as e:
        print(f"Error migrating business parameters: {str(e)}")

def migrate_overhead_costs():
    """Migrate overhead costs to Supabase"""
    try:
        with open('config/expenses.json', 'r') as f:
            data = json.load(f)
        
        supabase = get_supabase()
        costs = data.get('overhead_costs', {})
        
        # Check if costs already exist
        existing = supabase.table('overhead_costs').select('*').execute()
        if existing.data:
            # Update existing costs
            supabase.table('overhead_costs').update({
                'rent': float(costs.get('rent', 2000)),
                'utilities': float(costs.get('utilities', 500)),
                'insurance': float(costs.get('insurance', 400)),
                'tools_equipment': float(costs.get('tools_equipment', 500)),
                'vehicle_expenses': float(costs.get('vehicle_expenses', 1500)),
                'marketing': float(costs.get('marketing', 1000)),
                'misc_expenses': float(costs.get('misc_expenses', 300)),
                'employee_wages': float(costs.get('employee_wages', 0))
            }).eq('id', existing.data[0]['id']).execute()
        else:
            # Insert new costs
            supabase.table('overhead_costs').insert({
                'rent': float(costs.get('rent', 2000)),
                'utilities': float(costs.get('utilities', 500)),
                'insurance': float(costs.get('insurance', 400)),
                'tools_equipment': float(costs.get('tools_equipment', 500)),
                'vehicle_expenses': float(costs.get('vehicle_expenses', 1500)),
                'marketing': float(costs.get('marketing', 1000)),
                'misc_expenses': float(costs.get('misc_expenses', 300)),
                'employee_wages': float(costs.get('employee_wages', 0))
            }).execute()
        print("Overhead costs migrated successfully")
    except Exception as e:
        print(f"Error migrating overhead costs: {str(e)}")

def migrate_employees():
    """Migrate employees to Supabase"""
    try:
        with open('config/employees.json', 'r') as f:
            data = json.load(f)
        
        supabase = get_supabase()
        employees = data.get('employees', [])
        
        for employee in employees:
            # Check if employee already exists
            existing = supabase.table('employees').select('*').eq('employee_id', employee['employee_id']).execute()
            if existing.data:
                # Update existing employee
                supabase.table('employees').update({
                    'name': employee['name'],
                    'phone': employee['phone'],
                    'email': employee['email'],
                    'position': employee['position'],
                    'hours_per_week': float(employee['hours_per_week']),
                    'hourly_wage': float(employee['hourly_wage'])
                }).eq('employee_id', employee['employee_id']).execute()
            else:
                # Insert new employee
                supabase.table('employees').insert({
                    'employee_id': employee['employee_id'],
                    'name': employee['name'],
                    'phone': employee['phone'],
                    'email': employee['email'],
                    'position': employee['position'],
                    'hours_per_week': float(employee['hours_per_week']),
                    'hourly_wage': float(employee['hourly_wage'])
                }).execute()
        print("Employees migrated successfully")
    except Exception as e:
        print(f"Error migrating employees: {str(e)}")

def migrate_trucks():
    """Migrate trucks to Supabase"""
    try:
        with open('config/trucks.json', 'r') as f:
            data = json.load(f)
        
        supabase = get_supabase()
        trucks = data.get('trucks', [])
        
        for truck in trucks:
            # Check if truck already exists
            existing = supabase.table('trucks').select('*').eq('truck_id', truck['truck_id']).execute()
            if existing.data:
                # Update existing truck
                supabase.table('trucks').update({
                    'name': truck['name'],
                    'make': truck.get('make'),
                    'model': truck.get('model'),
                    'year': truck.get('year'),
                    'license_plate': truck.get('license_plate'),
                    'employee_ids': truck.get('employee_ids', []),
                    'effective_hours': float(truck.get('effective_hours', 40)),
                    'loan_payment': float(truck.get('loan_payment', 800)),
                    'insurance': float(truck.get('insurance', 200)),
                    'fuel_budget': float(truck.get('fuel_budget', 400)),
                    'maintenance_budget': float(truck.get('maintenance_budget', 100)),
                    'other_expenses': float(truck.get('other_expenses', 0)),
                    'service_area': truck.get('service_area'),
                    'notes': truck.get('notes')
                }).eq('truck_id', truck['truck_id']).execute()
            else:
                # Insert new truck
                supabase.table('trucks').insert({
                    'truck_id': truck['truck_id'],
                    'name': truck['name'],
                    'make': truck.get('make'),
                    'model': truck.get('model'),
                    'year': truck.get('year'),
                    'license_plate': truck.get('license_plate'),
                    'employee_ids': truck.get('employee_ids', []),
                    'effective_hours': float(truck.get('effective_hours', 40)),
                    'loan_payment': float(truck.get('loan_payment', 800)),
                    'insurance': float(truck.get('insurance', 200)),
                    'fuel_budget': float(truck.get('fuel_budget', 400)),
                    'maintenance_budget': float(truck.get('maintenance_budget', 100)),
                    'other_expenses': float(truck.get('other_expenses', 0)),
                    'service_area': truck.get('service_area'),
                    'notes': truck.get('notes')
                }).execute()
        print("Trucks migrated successfully")
    except Exception as e:
        print(f"Error migrating trucks: {str(e)}")

def migrate_customers():
    """Migrate customers to Supabase"""
    try:
        with open('config/customers.json', 'r') as f:
            data = json.load(f)
        
        supabase = get_supabase()
        customers = data.get('customers', [])
        
        for customer in customers:
            # Check if customer already exists
            existing = supabase.table('customers').select('*').eq('customer_id', customer['customer_id']).execute()
            if existing.data:
                # Update existing customer
                supabase.table('customers').update({
                    'name': customer['name'],
                    'address': customer.get('address'),
                    'phone': customer.get('phone'),
                    'email': customer.get('email')
                }).eq('customer_id', customer['customer_id']).execute()
            else:
                # Insert new customer
                supabase.table('customers').insert({
                    'customer_id': customer['customer_id'],
                    'name': customer['name'],
                    'address': customer.get('address'),
                    'phone': customer.get('phone'),
                    'email': customer.get('email')
                }).execute()
        print("Customers migrated successfully")
    except Exception as e:
        print(f"Error migrating customers: {str(e)}")

def main():
    """Main migration function"""
    print("\nStarting data migration to Supabase...")
    
    # Migrate all data
    migrate_business_parameters()
    migrate_overhead_costs()
    migrate_employees()
    migrate_trucks()
    migrate_customers()
    
    print("\nMigration completed!")

if __name__ == '__main__':
    main() 