CREATE TABLE IF NOT EXISTS workflowrequests (
    id INTEGER,
    task_id UUID NOT NULL,
    workflow VARCHAR,
    db VARCHAR,
    month INTEGER,
    year INTEGER,
    delta INTEGER,
    download INTEGER,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id)
);

CREATE TABLE IF NOT EXISTS taskstatus (
    id INTEGER,
    task_id UUID NOT NULL,
    status VARCHAR,
    file BLOB,
    created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(id)
);