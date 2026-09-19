-- PostgreSQL 16 — campus HR (system of record for people)
-- Linking key used by the other databases: employee.email

CREATE TABLE department (
    id    SMALLSERIAL PRIMARY KEY,
    code  TEXT NOT NULL UNIQUE,
    name  TEXT NOT NULL
);

CREATE TABLE employee (
    id             SERIAL PRIMARY KEY,
    given_name     TEXT NOT NULL,
    family_name    TEXT NOT NULL,
    email          TEXT NOT NULL UNIQUE,
    department_id  SMALLINT NOT NULL REFERENCES department (id),
    hired_on       DATE NOT NULL
);

INSERT INTO department (id, code, name) VALUES
    (1, 'CS',   'Computer Science'),
    (2, 'MATH', 'Mathematics'),
    (3, 'LIB',  'Library');

INSERT INTO employee (id, given_name, family_name, email, department_id, hired_on) VALUES
    (1, 'Ada',    'Lovelace',  'ada@campus.example',    1, '2018-03-01'),
    (2, 'Alan',   'Turing',    'alan@campus.example',   1, '2019-09-15'),
    (3, 'Grace',  'Hopper',    'grace@campus.example',  1, '2017-01-10'),
    (4, 'Donald', 'Knuth',     'donald@campus.example', 2, '2015-08-20'),
    (5, 'Edsger', 'Dijkstra',  'edsger@campus.example', 1, '2016-04-12');

SELECT setval('department_id_seq', (SELECT MAX(id) FROM department));
SELECT setval('employee_id_seq',   (SELECT MAX(id) FROM employee));
