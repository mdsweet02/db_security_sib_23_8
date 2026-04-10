-- Часть 0
CREATE DATABASE AuditLab;
GO
USE AuditLab;
GO
CREATE TABLE Employees
(
 EmployeeID INT PRIMARY KEY,
 FullName NVARCHAR(100),
 Department NVARCHAR(100),
 Salary INT
);
INSERT INTO Employees
VALUES
(1, 'Иванов Иван', 'IT', 800000),
(2, 'Петров Петр', 'Finance', 900000),
(3, 'Сидоров Алексей', 'HR', 650000);

-- Часть 1
USE master;
GO
CREATE SERVER AUDIT Audit_UserActions
TO FILE
(
 FILEPATH = 'C:\SQLAudit\',
 MAXSIZE = 100 MB,
 MAX_ROLLOVER_FILES = 10,
 RESERVE_DISK_SPACE = OFF
);
GO
ALTER SERVER AUDIT Audit_UserActions
WITH (STATE = ON);
GO

-- Часть 2 
CREATE SERVER AUDIT SPECIFICATION Audit_LoginEvents
FOR SERVER AUDIT Audit_UserActions
ADD (SUCCESSFUL_LOGIN_GROUP),
ADD (FAILED_LOGIN_GROUP),
ADD (LOGOUT_GROUP)
WITH (STATE = ON);
GO

-- Часть 3
USE AuditLab;
GO
CREATE DATABASE AUDIT SPECIFICATION Audit_EmployeeActions
FOR SERVER AUDIT Audit_UserActions
ADD (SELECT ON dbo.Employees BY PUBLIC),
ADD (INSERT ON dbo.Employees BY PUBLIC),
ADD (UPDATE ON dbo.Employees BY PUBLIC),
ADD (DELETE ON dbo.Employees BY PUBLIC)
WITH (STATE = ON);
GO

-- Часть 4
SELECT * FROM Employees;
GO
INSERT INTO Employees
VALUES
(4, 'Касымов Ержан', 'IT', 750000);
GO
UPDATE Employees
SET Salary = 850000
WHERE EmployeeID = 1;
GO
DELETE FROM Employees
WHERE EmployeeID = 3;
GO

-- Часть 5
SELECT *
FROM sys.fn_get_audit_file
(
 'C:\SQLAudit\*',
 DEFAULT,
 DEFAULT
);

-- Часть 6
SELECT event_time,
 server_principal_name,
 object_name,
 statement
FROM sys.fn_get_audit_file
(
 'C:\SQLAudit\*',
 DEFAULT,
 DEFAULT
)
WHERE action_id = 'DL';

SELECT event_time,
 server_principal_name,
 statement
FROM sys.fn_get_audit_file
(
 'C:\SQLAudit\*',
 DEFAULT,
 DEFAULT
)
WHERE statement LIKE '%Salary%';

SELECT event_time,
 server_principal_name,
 succeeded,
 statement
FROM sys.fn_get_audit_file
(
 'C:\SQLAudit\*',
 DEFAULT,
 DEFAULT
)
WHERE action_id = 'LGIF';

SELECT event_time,
 action_id,
 object_name,
 statement
FROM sys.fn_get_audit_file
(
 'C:\SQLAudit\*',
 DEFAULT,
 DEFAULT
)
WHERE server_principal_name = 'TestUser';

-- Часть 7
USE master;
GO
CREATE SERVER AUDIT SPECIFICATION Audit_PermissionChanges
FOR SERVER AUDIT Audit_UserActions
ADD (SERVER_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_PERMISSION_CHANGE_GROUP)
WITH (STATE = ON);
GO

-- Часть 8
USE AuditLab;
GO
CREATE DATABASE AUDIT SPECIFICATION Audit_ObjectChanges
FOR SERVER AUDIT Audit_UserActions
ADD (SCHEMA_OBJECT_CHANGE_GROUP)
WITH (STATE = ON);
GO
CREATE TABLE TestTable
(
 ID INT
);
DROP TABLE TestTable;

-- Часть 9
USE AuditLab;
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_EmployeeActions
WITH (STATE = OFF);
USE MASTER;
GO
ALTER SERVER AUDIT SPECIFICATION Audit_LoginEvents
WITH (STATE = OFF);
ALTER SERVER AUDIT Audit_UserActions
WITH (STATE = OFF);

-- Задание 1
CREATE SERVER AUDIT Audit_Table
TO FILE (FILEPATH = 'C:\SQLAudit\');
GO
ALTER SERVER AUDIT Audit_Table
WITH (STATE = ON);
GO

USE Станция_технического_обслуживания_автомобилей;
GO
CREATE DATABASE AUDIT SPECIFICATION Audit_Table_Spec
FOR SERVER AUDIT Audit_Table
ADD (SELECT, INSERT, UPDATE, DELETE
     ON dbo.Заказ BY PUBLIC);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = ON);
GO
-- Задание 2
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = OFF);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
ADD (SELECT, INSERT, UPDATE, DELETE
     ON dbo.Заказ BY User_NoMask);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = ON);
GO

-- Задание 3
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = OFF);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
ADD (UPDATE ON dbo.Заказ BY PUBLIC),
ADD (DELETE ON dbo.Заказ BY PUBLIC);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = ON);
GO

-- Задание 4
SELECT *
FROM sys.fn_get_audit_file('C:\SQLAudit\*.sqlaudit', DEFAULT, DEFAULT)
WHERE event_time >= DATEADD(HOUR,-24,GETDATE());

-- Задание 5
SELECT *
FROM sys.fn_get_audit_file('C:\SQLAudit\*.sqlaudit', DEFAULT, DEFAULT)
WHERE statement LIKE '%ИИН%'
   OR statement LIKE '%сумма%'
   OR statement LIKE '%UPDATE%';

-- Задание 6
SELECT *
FROM sys.fn_get_audit_file('C:\SQLAudit\*.sqlaudit', DEFAULT, DEFAULT)
WHERE action_id = 'LGIF';

-- Задание 7
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = OFF);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
ADD (SELECT, INSERT, UPDATE, DELETE
     ON DATABASE::Станция_технического_обслуживания_автомобилей BY dbo);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = ON);
GO

-- Задание 8
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = OFF);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_PERMISSION_CHANGE_GROUP);
GO
ALTER DATABASE AUDIT SPECIFICATION Audit_Table_Spec
WITH (STATE = ON);
GO