CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255) UNIQUE NOT NULL,
    user_id VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    title TEXT,
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS messages (
    id BIGSERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    tokens_used INTEGER DEFAULT 0,
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX idx_messages_conversation_time ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_conversations_session ON conversations(session_id);
CREATE INDEX idx_conversations_user ON conversations(user_id);

CREATE INDEX IF NOT EXISTS idx_messages_role_user
ON messages(conversation_id, created_at DESC)
WHERE role = 'user';

CREATE INDEX IF NOT EXISTS idx_messages_role
ON messages(role);

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
    
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_employee_id ON users(employee_id);

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(50) DEFAULT 'day-to-day',
    priority VARCHAR(20) DEFAULT 'medium',     
    status VARCHAR(20) DEFAULT 'pending',    
    deadline DATE,
    
    assigned_to_username VARCHAR(50) REFERENCES users(username) ON DELETE CASCADE,
    assigned_by VARCHAR(50) DEFAULT 'Self',    
    
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to_username);

INSERT INTO users (
    username, password_hash, role, status, name, designation, employee_id, last_day, managers
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
        '{}'
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
        ARRAY['EMP-1234'] 
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
        '{}'
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
        ARRAY['EMP-123']
    )
ON CONFLICT (username) DO NOTHING;

INSERT INTO tasks (
    title, description, category, priority, status, deadline, assigned_to_username, assigned_by
)
VALUES 
    (
        'Complete project documentation', 
        'Document the current project structure and API endpoints', 
        'day-to-day', 
        'high', 
        'pending', 
        '2025-01-20', 
        'Mastermind-sap', 
        'Rajesh Kumar'
    ),
    (
        'Review code changes', 
        'Review and provide feedback on recent pull requests', 
        'day-to-day', 
        'medium', 
        'in-progress', 
        '2025-01-18', 
        'Mastermind-sap', 
        'Rajesh Kumar'
    ),
    
    (
        'Update personal development plan', 
        'Review and update my personal development goals for Q1', 
        'day-to-day', 
        'low', 
        'pending', 
        NULL, 
        'Mastermind-sap', 
        'Self'
    ),
    (
        'Learn new framework features', 
        'Study the latest updates in the framework we are using', 
        'day-to-day', 
        'medium', 
        'in-progress', 
        '2025-01-25', 
        'Mastermind-sap', 
        'Self'
    );