CREATE TABLE users
(
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    home INTEGER,
    shared INTEGER,
    pass INTEGER,
    passvalue TEXT,
    sge INTEGER,
    maillist INTEGER,
    email INTEGER
);

CREATE TABLE prio
(
    prio_id INTEGER PRIMARY KEY,
    project_name TEXT,
    papers INTEGER,
    prio INTEGER,
    user_id INTEGER REFERENCES users(user_id)
);

CREATE INDEX idx_users_name ON users(username);
