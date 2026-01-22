-- 1. Setup Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 2. Create the "Blueprint" Schema
CREATE SCHEMA IF NOT EXISTS template_schema;

-- 3. Define Template Tables (Blueprints for new users)
CREATE TABLE IF NOT EXISTS template_schema.conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS template_schema.messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS template_schema.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'day-to-day',
    priority VARCHAR(20) DEFAULT 'medium',     
    status VARCHAR(20) DEFAULT 'pending',    
    deadline DATE,
    assigned_to_username VARCHAR(50), 
    assigned_by VARCHAR(50) DEFAULT 'Self',    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 4. Define Shared Users Table (In Public Schema)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'employee',
    status VARCHAR(50) DEFAULT 'general', 
    name VARCHAR(255),
    designation VARCHAR(100),
    employee_id VARCHAR(50) UNIQUE,
    last_day DATE,
    managers TEXT[] DEFAULT '{}',
    
    -- IMPORTANT: Stores the user's specific database schema name
    schema_name VARCHAR(100),
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);

-- 5. Insert Initial Users
-- We assign them a 'schema_name' immediately so the backend can create it on startup.
INSERT INTO users (
    username, password_hash, role, status, name, designation, employee_id, last_day, managers, schema_name
) 
VALUES 
    (
        'admin', 
        crypt('admin', gen_salt('bf')), 
        'admin', 
        'general', 
        NULL, 
        NULL, 
        NULL, 
        NULL, 
        '{}',
        'user_admin'
    ),
    (
        'manager1', 
        crypt('manager1', gen_salt('bf')), 
        'manager', 
        'general', 
        'Rajesh Kumar', 
        'Dev Manager', 
        'EMP-123', 
        NULL, 
        ARRAY['EMP-1234'],
        'user_manager1'
    ),
    (
        'manager2', 
        crypt('manager2', gen_salt('bf')), 
        'manager', 
        'general', 
        'Suresh Kumar', 
        'Infra Manager', 
        'EMP-1234', 
        NULL, 
        '{}',
        'user_manager2'
    ),
    (
        'Mastermind-sap', 
        crypt('Mastermind-sap', gen_salt('bf')), 
        'employee', 
        'onboard', 
        'Mastermind-sap', 
        'Frontend Developer', 
        'EMP-763326', 
        '2025-12-29', 
        ARRAY['EMP-123'],
        'user_mastermind_sap'
    )
ON CONFLICT (username) DO UPDATE 
SET schema_name = EXCLUDED.schema_name;
