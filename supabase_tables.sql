-- Create updated_at function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create business_parameters table
DROP TABLE IF EXISTS business_parameters CASCADE;
CREATE TABLE IF NOT EXISTS business_parameters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    efficiency_rate DECIMAL NOT NULL DEFAULT 0.55,
    profit_margin_multiplier DECIMAL NOT NULL DEFAULT 0.7,
    hourly_rate DECIMAL NOT NULL DEFAULT 325.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create overhead_costs table
DROP TABLE IF EXISTS overhead_costs CASCADE;
CREATE TABLE IF NOT EXISTS overhead_costs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rent DECIMAL NOT NULL DEFAULT 2000,
    utilities DECIMAL NOT NULL DEFAULT 500,
    insurance DECIMAL NOT NULL DEFAULT 1000,
    tools_equipment DECIMAL NOT NULL DEFAULT 500,
    vehicle_expenses DECIMAL NOT NULL DEFAULT 800,
    marketing DECIMAL NOT NULL DEFAULT 400,
    misc_expenses DECIMAL NOT NULL DEFAULT 300,
    employee_wages DECIMAL NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create expense_details table
DROP TABLE IF EXISTS expense_details CASCADE;
CREATE TABLE IF NOT EXISTS expense_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    expense_name TEXT NOT NULL,
    expense_type TEXT NOT NULL,
    amount DECIMAL NOT NULL DEFAULT 0,
    description TEXT,
    notes TEXT,
    date_added TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employees table
DROP TABLE IF EXISTS employees CASCADE;
CREATE TABLE IF NOT EXISTS employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    phone TEXT,
    email TEXT,
    position TEXT,
    hours_per_week DECIMAL DEFAULT 40,
    hourly_wage DECIMAL DEFAULT 25.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trucks table
DROP TABLE IF EXISTS trucks CASCADE;
CREATE TABLE IF NOT EXISTS trucks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    truck_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    make TEXT,
    model TEXT,
    year TEXT,
    license_plate TEXT,
    employee_ids TEXT[],
    status TEXT DEFAULT 'active',
    hours_worked DECIMAL DEFAULT 0,
    loan_payment DECIMAL DEFAULT 0,
    insurance DECIMAL DEFAULT 0,
    fuel_budget DECIMAL DEFAULT 0,
    maintenance_budget DECIMAL DEFAULT 0,
    other_expenses DECIMAL DEFAULT 0,
    effective_hours DECIMAL DEFAULT 0,
    service_area TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create customers table
DROP TABLE IF EXISTS customers CASCADE;
CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    address TEXT,
    phone TEXT,
    email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create jobs table
DROP TABLE IF EXISTS jobs CASCADE;
CREATE TABLE IF NOT EXISTS jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(id),
    status TEXT DEFAULT 'pending',
    description TEXT,
    scheduled_date TIMESTAMP WITH TIME ZONE,
    completed_date TIMESTAMP WITH TIME ZONE,
    amount DECIMAL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Drop existing triggers if they exist
DROP TRIGGER IF EXISTS update_business_parameters_updated_at ON business_parameters;
DROP TRIGGER IF EXISTS update_overhead_costs_updated_at ON overhead_costs;
DROP TRIGGER IF EXISTS update_employees_updated_at ON employees;
DROP TRIGGER IF EXISTS update_trucks_updated_at ON trucks;
DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
DROP TRIGGER IF EXISTS update_expense_details_updated_at ON expense_details;

-- Add updated_at triggers
CREATE TRIGGER update_business_parameters_updated_at
    BEFORE UPDATE ON business_parameters
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_overhead_costs_updated_at
    BEFORE UPDATE ON overhead_costs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employees_updated_at
    BEFORE UPDATE ON employees
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_trucks_updated_at
    BEFORE UPDATE ON trucks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_expense_details_updated_at
    BEFORE UPDATE ON expense_details
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Enable Row Level Security but allow all operations for now
ALTER TABLE business_parameters ENABLE ROW LEVEL SECURITY;
ALTER TABLE overhead_costs ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE trucks ENABLE ROW LEVEL SECURITY;
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE expense_details ENABLE ROW LEVEL SECURITY;

-- Create policies to allow all operations (you can restrict these later)
DROP POLICY IF EXISTS "Allow all" ON business_parameters;
DROP POLICY IF EXISTS "Allow all" ON overhead_costs;
DROP POLICY IF EXISTS "Allow all" ON employees;
DROP POLICY IF EXISTS "Allow all" ON trucks;
DROP POLICY IF EXISTS "Allow all" ON customers;
DROP POLICY IF EXISTS "Allow all" ON jobs;
DROP POLICY IF EXISTS "Allow all" ON expense_details;

CREATE POLICY "Allow all" ON business_parameters FOR ALL USING (true);
CREATE POLICY "Allow all" ON overhead_costs FOR ALL USING (true);
CREATE POLICY "Allow all" ON employees FOR ALL USING (true);
CREATE POLICY "Allow all" ON trucks FOR ALL USING (true);
CREATE POLICY "Allow all" ON customers FOR ALL USING (true);
CREATE POLICY "Allow all" ON jobs FOR ALL USING (true);
CREATE POLICY "Allow all" ON expense_details FOR ALL USING (true);