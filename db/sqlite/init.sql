-- SQLite — campus registrar
-- Cross-source identifier: enrollment.student_email
-- Seed size: course 4, enrollment 6

PRAGMA foreign_keys = ON;

BEGIN;

CREATE TABLE IF NOT EXISTS course (
    id       INTEGER PRIMARY KEY,
    code     TEXT NOT NULL UNIQUE,
    title    TEXT NOT NULL,
    credits  INTEGER NOT NULL CHECK (credits > 0)
);

CREATE TABLE IF NOT EXISTS enrollment (
    id             INTEGER PRIMARY KEY,
    student_email  TEXT NOT NULL,
    course_id      INTEGER NOT NULL,
    term           TEXT NOT NULL,
    grade          TEXT,
    UNIQUE (student_email, course_id, term),
    FOREIGN KEY (course_id) REFERENCES course (id)
);

CREATE INDEX IF NOT EXISTS enrollment_student_email
    ON enrollment (student_email);

INSERT OR IGNORE INTO course (id, code, title, credits) VALUES
    (1, 'SEMWEB101', 'Introduction to the Semantic Web', 6),
    (2, 'DB201',     'Relational Databases',             6),
    (3, 'MATH101',   'Discrete Mathematics',             5),
    (4, 'AI301',     'Knowledge Representation',         6);

INSERT OR IGNORE INTO enrollment (id, student_email, course_id, term, grade) VALUES
    (1, 'ada@campus.example',    1, '2026S', 'A'),
    (2, 'alan@campus.example',   2, '2026S', 'A'),
    (3, 'grace@campus.example',  1, '2026S', 'B'),
    (4, 'donald@campus.example', 3, '2025F', 'A'),
    (5, 'edsger@campus.example', 4, '2026S', 'A'),
    (6, 'alan@campus.example',   1, '2026S', 'B');

COMMIT;
