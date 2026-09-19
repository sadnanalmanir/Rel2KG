-- MySQL 8.4 — campus library
-- borrower_email / author.email overlap with PostgreSQL employee.email

USE library;

CREATE TABLE author (
    id         INT AUTO_INCREMENT PRIMARY KEY,
    full_name  VARCHAR(128) NOT NULL,
    email      VARCHAR(128) NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE book (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    isbn            VARCHAR(20) NOT NULL UNIQUE,
    title           VARCHAR(255) NOT NULL,
    published_year  INT NULL,
    author_id       INT NOT NULL,
    CONSTRAINT fk_book_author FOREIGN KEY (author_id) REFERENCES author (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE loan (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    borrower_email  VARCHAR(128) NOT NULL,
    book_id         INT NOT NULL,
    loaned_on       DATE NOT NULL,
    returned_on     DATE NULL,
    CONSTRAINT fk_loan_book FOREIGN KEY (book_id) REFERENCES book (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO author (id, full_name, email) VALUES
    (1, 'Ada Lovelace',      'ada@campus.example'),
    (2, 'Donald Knuth',      'donald@campus.example'),
    (3, 'Tim Berners-Lee',   'timbl@w3.example'),
    (4, 'Edgar F. Codd',     'ted@rdbms.example');

INSERT INTO book (id, isbn, title, published_year, author_id) VALUES
    (1, '978-0-000-00001', 'Notes on the Analytical Engine',           1843, 1),
    (2, '978-0-201-89683', 'The Art of Computer Programming, Vol. 1',  1968, 2),
    (3, '978-0-06-251587', 'Weaving the Web',                          1999, 3),
    (4, '978-0-000-00070', 'A Relational Model of Data',               1970, 4);

INSERT INTO loan (id, borrower_email, book_id, loaned_on, returned_on) VALUES
    (1, 'ada@campus.example',    2, '2026-02-01', '2026-02-20'),
    (2, 'alan@campus.example',   4, '2026-03-03', NULL),
    (3, 'grace@campus.example',  3, '2026-01-12', '2026-01-28'),
    (4, 'edsger@campus.example', 1, '2026-03-10', NULL);
