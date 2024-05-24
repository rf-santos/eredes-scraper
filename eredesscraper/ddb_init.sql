CREATE SEQUENCE IF NOT EXISTS id_seq;

CREATE TABLE IF NOT EXISTS workflowrequests (
    id INTEGER PRIMARY KEY DEFAULT nextval('id_seq'),
    task_id UUID UNIQUE NOT NULL,
    workflow VARCHAR,
    db VARCHAR[],
    month INTEGER,
    year INTEGER,
    delta BOOL,
    download BOOL,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS taskstatus (
    task_id UUID PRIMARY KEY REFERENCES workflowrequests(task_id),
    status VARCHAR,
    file BLOB,
    created TIMESTAMP,
    updated TIMESTAMP
);