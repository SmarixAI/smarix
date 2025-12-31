CREATE INDEX IF NOT EXISTS idx_messages_role_user
ON messages(conversation_id, created_at DESC)
WHERE role = 'user';

CREATE INDEX IF NOT EXISTS idx_messages_role
ON messages(role);

SELECT
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexname::regclass)) as size
FROM pg_indexes
WHERE tablename IN ('messages', 'conversations')
ORDER BY tablename, indexname;