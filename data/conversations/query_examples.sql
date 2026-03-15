-- Sessions/messages by source agent
SELECT agent, COUNT(*) AS sessions
FROM sessions
GROUP BY agent
ORDER BY sessions DESC;

SELECT agent, COUNT(*) AS messages
FROM messages
GROUP BY agent
ORDER BY messages DESC;

-- Time coverage by agent
SELECT agent, MIN(ts) AS first_ts, MAX(ts) AS last_ts
FROM messages
GROUP BY agent
ORDER BY agent;

-- Find discussions about specific topics (FTS)
SELECT session_id, agent, ts, substr(text, 1, 180) AS snippet
FROM messages_fts
JOIN messages ON messages_fts.rowid = messages.id
WHERE messages_fts MATCH 'daytona OR variance OR oracle OR mcp'
ORDER BY ts DESC
LIMIT 100;

-- Top sessions by tool-call intensity
SELECT agent, session_id, tool_calls, msg_count, started_at, last_at
FROM sessions
ORDER BY tool_calls DESC
LIMIT 100;
