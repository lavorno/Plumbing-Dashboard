from config.supabase import get_supabase

def update_truck():
    try:
        supabase = get_supabase()
        
        # Update truck with correct employee IDs
        truck_data = {
            'employee_ids': ['45977460-aa96-405c-9b31-fe72a0d843ef', 'b9d04642-e368-4896-bef0-621d5323bfcf']
        }
        
        result = supabase.table('trucks').update(truck_data).eq('truck_id', 't1-2024-01').execute()
        print("Update successful:", result.data)
        
    except Exception as e:
        print("Error updating truck:", str(e))

if __name__ == '__main__':
    update_truck() 