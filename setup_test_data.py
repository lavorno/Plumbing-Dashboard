from config.supabase import get_supabase
import uuid
from datetime import datetime

def setup_test_data():
    try:
        supabase = get_supabase()
        
        # First, clear existing data
        print("Clearing existing data...")
        # Get all existing trucks and employees
        trucks_result = supabase.table('trucks').select('truck_id').execute()
        employees_result = supabase.table('employees').select('employee_id').execute()
        
        # Delete existing trucks
        if trucks_result.data:
            for truck in trucks_result.data:
                supabase.table('trucks').delete().eq('truck_id', truck['truck_id']).execute()
                print(f"Deleted truck: {truck['truck_id']}")
        
        # Delete existing employees
        if employees_result.data:
            for employee in employees_result.data:
                supabase.table('employees').delete().eq('employee_id', employee['employee_id']).execute()
                print(f"Deleted employee: {employee['employee_id']}")
        
        print("\nCreating test employees...")
        # Create 10 test employees with specific IDs for consistency
        employees = [
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'John Smith',
                'phone': '903-555-0001',
                'email': 'john.smith@example.com',
                'position': 'Master Plumber',
                'hours_per_week': 40,
                'hourly_wage': 45.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Mike Johnson',
                'phone': '903-555-0002',
                'email': 'mike.johnson@example.com',
                'position': 'Journeyman',
                'hours_per_week': 40,
                'hourly_wage': 35.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'David Wilson',
                'phone': '903-555-0003',
                'email': 'david.wilson@example.com',
                'position': 'Master Plumber',
                'hours_per_week': 40,
                'hourly_wage': 48.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Robert Brown',
                'phone': '903-555-0004',
                'email': 'robert.brown@example.com',
                'position': 'Apprentice',
                'hours_per_week': 40,
                'hourly_wage': 25.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'James Davis',
                'phone': '903-555-0005',
                'email': 'james.davis@example.com',
                'position': 'Master Plumber',
                'hours_per_week': 40,
                'hourly_wage': 50.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Thomas Anderson',
                'phone': '903-555-0006',
                'email': 'thomas.anderson@example.com',
                'position': 'Journeyman',
                'hours_per_week': 40,
                'hourly_wage': 32.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Richard Taylor',
                'phone': '903-555-0007',
                'email': 'richard.taylor@example.com',
                'position': 'Master Plumber',
                'hours_per_week': 40,
                'hourly_wage': 47.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Daniel Martinez',
                'phone': '903-555-0008',
                'email': 'daniel.martinez@example.com',
                'position': 'Journeyman',
                'hours_per_week': 40,
                'hourly_wage': 34.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Joseph Garcia',
                'phone': '903-555-0009',
                'email': 'joseph.garcia@example.com',
                'position': 'Master Plumber',
                'hours_per_week': 40,
                'hourly_wage': 46.00,
                'created_at': datetime.now().isoformat()
            },
            {
                'employee_id': str(uuid.uuid4()),
                'name': 'Christopher Lee',
                'phone': '903-555-0010',
                'email': 'christopher.lee@example.com',
                'position': 'Journeyman',
                'hours_per_week': 40,
                'hourly_wage': 33.00,
                'created_at': datetime.now().isoformat()
            }
        ]
        
        # Add employees to database and store their IDs
        employee_ids = []
        for employee in employees:
            result = supabase.table('employees').insert(employee).execute()
            if result.data:
                employee_ids.append(employee['employee_id'])
                print(f"Added employee: {employee['name']} (ID: {employee['employee_id']})")
            else:
                print(f"Failed to add employee: {employee['name']}")
        
        print("\nCreating trucks...")
        # Create 5 trucks with 2 employees each
        trucks = []
        for i in range(5):
            if i*2+1 < len(employee_ids):  # Make sure we have enough employees
                truck = {
                    'truck_id': f"t2-2024-{i+1:02d}",
                    'name': f"Truck #{i+1}",
                    'make': 'Ford',
                    'model': 'Transit-350',
                    'year': '2024',
                    'license_plate': f'TX{1001+i}',
                    'employee_ids': [employee_ids[i*2], employee_ids[i*2+1]],
                    'effective_hours': 80,  # Combined hours of both employees
                    'loan_payment': 800.0,
                    'insurance': 200.0,
                    'fuel_budget': 400.0,
                    'maintenance_budget': 100.0,
                    'other_expenses': 0.0,
                    'service_area': f'Zone {i+1}',
                    'notes': f'Master/Journeyman Team {i+1}',
                    'created_at': datetime.now().isoformat()
                }
                trucks.append(truck)
        
        # Add trucks to database
        for truck in trucks:
            result = supabase.table('trucks').insert(truck).execute()
            if result.data:
                print(f"Added truck: {truck['name']} with employees: {truck['employee_ids']}")
            else:
                print(f"Failed to add truck: {truck['name']}")
        
        print("\nTest data setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up test data: {str(e)}")

if __name__ == '__main__':
    setup_test_data() 