-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Drop all existing tables to ensure clean state
DROP TABLE IF EXISTS public.jobs CASCADE;
DROP TABLE IF EXISTS public.trucks CASCADE;
DROP TABLE IF EXISTS public.customers CASCADE;
DROP TABLE IF EXISTS public.employees CASCADE;
DROP TABLE IF EXISTS public.overhead_costs CASCADE;
DROP TABLE IF EXISTS public.business_parameters CASCADE;

-- Create business_parameters table
CREATE TABLE IF NOT EXISTS business_parameters (
    id SERIAL PRIMARY KEY,
    efficiency_rate DECIMAL NOT NULL DEFAULT 0.4,
    profit_margin_multiplier DECIMAL NOT NULL DEFAULT 0.25,
    hourly_rate DECIMAL NOT NULL DEFAULT 450.0,
    locked_hourly_rate DECIMAL DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create overhead_costs table
CREATE TABLE IF NOT EXISTS overhead_costs (
    id SERIAL PRIMARY KEY,
    rent DECIMAL NOT NULL DEFAULT 2000,
    utilities DECIMAL NOT NULL DEFAULT 500,
    insurance DECIMAL NOT NULL DEFAULT 400,
    tools_equipment DECIMAL NOT NULL DEFAULT 500,
    vehicle_expenses DECIMAL NOT NULL DEFAULT 1500,
    marketing DECIMAL NOT NULL DEFAULT 1000,
    misc_expenses DECIMAL NOT NULL DEFAULT 300,
    employee_wages DECIMAL NOT NULL DEFAULT 0,
    pierce_brothers_truck_expenses DECIMAL NOT NULL DEFAULT 1500,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    id SERIAL PRIMARY KEY,
    employee_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    phone VARCHAR(20),
    email VARCHAR(255),
    position VARCHAR(100),
    hours_per_week DECIMAL NOT NULL DEFAULT 40,
    hourly_wage DECIMAL NOT NULL DEFAULT 35,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create trucks table
CREATE TABLE IF NOT EXISTS trucks (
    id SERIAL PRIMARY KEY,
    truck_id VARCHAR(50) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    year VARCHAR(4),
    license_plate VARCHAR(20),
    employee_ids UUID[] DEFAULT '{}',
    effective_hours DECIMAL NOT NULL DEFAULT 40,
    loan_payment DECIMAL NOT NULL DEFAULT 800,
    insurance DECIMAL NOT NULL DEFAULT 200,
    fuel_budget DECIMAL NOT NULL DEFAULT 400,
    maintenance_budget DECIMAL NOT NULL DEFAULT 100,
    other_expenses DECIMAL NOT NULL DEFAULT 0,
    service_area VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create customers table
CREATE TABLE IF NOT EXISTS customers (
    id SERIAL PRIMARY KEY,
    customer_id UUID NOT NULL UNIQUE DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    address TEXT,
    phone VARCHAR(20),
    email VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create function to update timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updating timestamps
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

-- Create jobs table (depends on customers)
CREATE TABLE public.jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID UNIQUE DEFAULT uuid_generate_v4(),
    customer_id UUID REFERENCES customers(customer_id),
    description TEXT,
    estimated_hours NUMERIC(10,2),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);