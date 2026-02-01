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
    active_repos TEXT[] DEFAULT '{}',

    -- Stores the user's specific database schema name
    schema_name VARCHAR(100),

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);


CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);


-- 5. Insert Initial Users
INSERT INTO users (
    username, password_hash, role, status, name, designation, employee_id, last_day, managers, active_repos, schema_name
) 
VALUES 
    -- 1. System Admin
    (
        'admin', 
        crypt('admin', gen_salt('bf')), 
        'admin', 
        'general', 
        'System Admin', 
        'Super User', 
        'ADMIN-001', 
        NULL, 
        '{}',
        '{}',
        'user_admin'
    ),

    -- 2. Senior Manager (The Boss)
    (
        'manager1', 
        crypt('manager1', gen_salt('bf')), 
        'manager', 
        'general', 
        'Manager One', 
        'Senior Manager', 
        'MGR-001', 
        NULL, 
        '{}',
        '{}',
        'user_manager1'
    ),

    -- 3. Team Lead (Reports to Manager1)
    (
        'manager2', 
        crypt('manager2', gen_salt('bf')), 
        'manager', 
        'general', 
        'Manager Two', 
        'Team Lead', 
        'MGR-002', 
        NULL, 
        ARRAY['MGR-001'], -- Reports to Manager One
        '{}',
        'user_manager2'
    ),

    -- 4. Frontend Developer (Reports to Manager2)
    (
        'dev1', 
        crypt('dev1', gen_salt('bf')), 
        'employee', 
        'onboard', 
        'Developer One', 
        'Frontend Developer', 
        'DEV-001', 
        '2025-12-29', 
        ARRAY['MGR-002'], 
        ARRAY['CCExtractor/taskwarrior-flutter'],
        'user_dev1'
    ),

    -- 5. Backend Developer (Reports to Manager2)
    (
        'dev2', 
        crypt('dev2', gen_salt('bf')), 
        'employee', 
        'offboard', 
        'Developer Two', 
        'Backend Developer', 
        'DEV-002', 
        '2026-01-26', 
        ARRAY['MGR-002'], 
        ARRAY['torvalds/test-tlb'],
        'user_dev2'
    ),

    -- 6. QA Tester (Reports to Manager2)
    (
        'qa1', 
        crypt('qa1', gen_salt('bf')), 
        'employee', 
        'onboard', 
        'QA One', 
        'Quality Engineer', 
        'QA-001', 
        NULL, 
        ARRAY['MGR-002'], 
        ARRAY['CCExtractor/taskwarrior-flutter'],
        'user_qa1'
    )
ON CONFLICT (username) DO UPDATE 
SET 
    schema_name = EXCLUDED.schema_name,
    active_repos = EXCLUDED.active_repos,
    managers = EXCLUDED.managers,
    last_day = EXCLUDED.last_day,
    status = EXCLUDED.status,
    password_hash = EXCLUDED.password_hash;


-- 6. Function to Clone Schema for New Users
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

    -- Clone messages table structure
    EXECUTE format(
        'CREATE TABLE %I.messages (LIKE %I.messages INCLUDING DEFAULTS INCLUDING CONSTRAINTS INCLUDING INDEXES)',
        dest_schema, source_schema
    );

    -- Create sequence for messages.id
    EXECUTE format('CREATE SEQUENCE %I.messages_id_seq', dest_schema);

    -- Set the sequence as default
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
SELECT clone_schema_for_user('template_schema', 'user_dev1');
SELECT clone_schema_for_user('template_schema', 'user_dev2');
SELECT clone_schema_for_user('template_schema', 'user_qa1');