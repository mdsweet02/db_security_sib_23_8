CREATE DATABASE lab4;
GO

USE lab4;
GO
---
CREATE TABLE Clients
(
    ClientID INT PRIMARY KEY,
    FullName NVARCHAR(100),

    Phone NVARCHAR(20) 
    MASKED WITH (FUNCTION = 'partial(0,"XXXXXXX",4)'),

    Email NVARCHAR(100) 
    MASKED WITH (FUNCTION = 'email()'),

    Salary INT 
    MASKED WITH (FUNCTION = 'default()'),

    Age INT 
    MASKED WITH (FUNCTION = 'random(18,60)')
);

INSERT INTO Clients VALUES
(1, 'Жанбырбай Алмас', '+77011234567', 'almas@gmail.com', 850000, 21),
(2, 'Иванов Иван', '+77025556677', 'ivanov@mail.kz', 650000, 30),
(3, 'Петров Петр', '+77037778899', 'petrov@yandex.ru', 1200000, 40);

SELECT * FROM Clients;
---
CREATE LOGIN TestUser_Almas WITH PASSWORD = 'Password123!';
GO
CREATE USER TestUser_Almas FOR LOGIN TestUser_Almas;
GO
GRANT SELECT ON Clients TO TestUser_Almas;

EXECUTE AS USER = 'TestUser_Almas';
SELECT * FROM Clients;
REVERT;
---
GRANT UNMASK TO TestUser_Almas;

EXECUTE AS USER = 'TestUser_Almas';
SELECT * FROM Clients;
REVERT;
---
REVOKE UNMASK FROM TestUser_Almas;

EXECUTE AS USER = 'TestUser_Almas';
SELECT * FROM Clients;
REVERT;
---
CREATE TABLE Employees
(
    EmployeeID INT PRIMARY KEY,
    FullName NVARCHAR(100),
    Phone NVARCHAR(20),
    Email NVARCHAR(100),
    Salary INT
);

INSERT INTO Employees VALUES
(1, 'Ибраев Нурлан', '+77018889900', 'ibraev@mail.kz', 700000),
(2, 'Касымов Ержан', '+77017776655', 'kasymov@gmail.com', 900000),
(3, 'Жакимов Алмас', '+77018889900', 'almas@mail.kz', 650000);
(4, 'Жумабаев Акежан', '+77018884564', 'akezhan@mail.kz', 1100000);

Select * from Employees;
---
ALTER TABLE Employees
ALTER COLUMN Phone NVARCHAR(20)
MASKED WITH (FUNCTION = 'partial(0,"XXXXXXX",4)');

ALTER TABLE Employees
ALTER COLUMN Email NVARCHAR(100)
MASKED WITH (FUNCTION = 'email()');

ALTER TABLE Employees
ALTER COLUMN Salary INT
MASKED WITH (FUNCTION = 'default()');
---
ALTER TABLE Employees
ALTER COLUMN Phone DROP MASKED;

ALTER TABLE Employees
ALTER COLUMN Email DROP MASKED;

ALTER TABLE Employees
ALTER COLUMN Salary DROP MASKED;
---
EXECUTE AS USER = 'TestUser_Almas';
SELECT * FROM Employees
WHERE Email LIKE 'almas%';

REVERT;
---
EXECUTE AS USER = 'TestUser_Almas';

SELECT * FROM Employees
WHERE Salary > 1000000;

REVERT;