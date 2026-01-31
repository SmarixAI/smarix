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
    conversation_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb,
    CONSTRAINT fk_conversation 
        FOREIGN KEY (conversation_id) 
        REFERENCES template_schema.conversations(id) 
        ON DELETE CASCADE
);

-- Add index for better query performance
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id 
    ON template_schema.messages(conversation_id);

CREATE INDEX IF NOT EXISTS idx_messages_created_at 
    ON template_schema.messages(created_at);


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


-- 6. Function to Clone Schema for New Users
-- This function will be called when creating user schemas
CREATE OR REPLACE FUNCTION clone_schema_for_user(source_schema TEXT, dest_schema TEXT)
RETURNS VOID AS $$
DECLARE
    object RECORD;
BEGIN
    -- Create new schema
    EXECUTE format('CREATE SCHEMA IF NOT EXISTS %I', dest_schema);

    -- Clone conversations table
    EXECUTE format(
        'CREATE TABLE %I.conversations (LIKE %I.conversations INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)',
        dest_schema, source_schema
    );

    -- Clone messages table structure (without sequences yet)
    EXECUTE format(
        'CREATE TABLE %I.messages (LIKE %I.messages INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)',
        dest_schema, source_schema
    );

    -- Create sequence for messages.id
    EXECUTE format('CREATE SEQUENCE %I.messages_id_seq', dest_schema);

    -- Set the sequence as default for messages.id
    EXECUTE format(
        'ALTER TABLE %I.messages ALTER COLUMN id SET DEFAULT nextval(%L)',
        dest_schema,
        dest_schema || '.messages_id_seq'
    );

    -- Set sequence ownership
    EXECUTE format(
        'ALTER SEQUENCE %I.messages_id_seq OWNED BY %I.messages.id',
        dest_schema, dest_schema
    );

    -- Add foreign key constraint
    EXECUTE format(
        'ALTER TABLE %I.messages DROP CONSTRAINT IF EXISTS fk_conversation',
        dest_schema
    );

    EXECUTE format(
        'ALTER TABLE %I.messages ADD CONSTRAINT fk_conversation FOREIGN KEY (conversation_id) REFERENCES %I.conversations(id) ON DELETE CASCADE',
        dest_schema, dest_schema
    );

    -- Clone tasks table
    EXECUTE format(
        'CREATE TABLE %I.tasks (LIKE %I.tasks INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)',
        dest_schema, source_schema
    );

    -- Recreate indexes
    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON %I.messages(conversation_id)',
        dest_schema
    );

    EXECUTE format(
        'CREATE INDEX IF NOT EXISTS idx_messages_created_at ON %I.messages(created_at)',
        dest_schema
    );

    RAISE NOTICE 'Schema % cloned successfully from %', dest_schema, source_schema;
END;
$$ LANGUAGE plpgsql;


-- 7. Create schemas for initial users
SELECT clone_schema_for_user('template_schema', 'user_admin');
SELECT clone_schema_for_user('template_schema', 'user_manager1');
SELECT clone_schema_for_user('template_schema', 'user_manager2');
SELECT clone_schema_for_user('template_schema', 'user_mastermind_sap');