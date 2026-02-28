EXEC sp_helpsrvrole 

EXEC sp_addlogin 'TempUser','123'

EXEC sp_helplogins 

EXEC sp_addsrvrolemember 'TempUser', 'securityadmin' 

EXEC sp_helprole

EXEC sp_helprolemember 'db_owner'

EXEC sp_adduser 'TempUser', 'MyFirstUser'

EXEC sp_helpuser

EXEC sp_addrolemember 'db_datareader', 'MyFirstUser'
---6 Задание---
CREATE DATABASE Stud_Almas

USE master;
CREATE LOGIN TestUser WITH PASSWORD = 'TestUser'
CREATE LOGIN Andy WITH PASSWORD = 'Andy'
GO
USE Stud_Almas; 
GO
CREATE USER TestUser FOR LOGIN TestUser;
GO
CREATE TABLE dbo.ROUTE (
    RouteID INT PRIMARY KEY IDENTITY(1,1),
    RouteName NVARCHAR(100) NOT NULL,
    Distance FLOAT,
    Description NVARCHAR(MAX)
);
GO
GRANT SELECT, UPDATE ON dbo.ROUTE TO TestUser;
GO
---
USE Stud_Almas; 
GO
CREATE USER Andy FOR LOGIN Andy;
GO
GRANT SELECT (RouteID, RouteName) ON dbo.ROUTE TO Andy;
GO
---7,8 задание---
EXEC sp_droprolemember 'db_datareader', 'MyFirstUser'
EXEC sp_dropuser 'MyFirstUser'
EXEC sp_dropsrvrolemember 'TempUser', 'securityadmin'
EXEC sp_droplogin 'TempUser'

---Самостоятельная работа---
USE master;
GO
CREATE DATABASE StoreDB;
GO
USE StoreDB;
GO
CREATE TABLE dbo.Products (
    ProductID INT PRIMARY KEY IDENTITY(1,1), 
    ProductName NVARCHAR(100) NOT NULL,     
    Category NVARCHAR(50),                   
    Price DECIMAL(10, 2) NOT NULL,          
    StockQuantity INT DEFAULT 0,            
    CratedDate DATETIME DEFAULT GETDATE()
);
GO
---Cоздание логинов---
USE master;
GO
CREATE LOGIN ManagerLogin WITH PASSWORD = 'ManagerPass123', DEFAULT_DATABASE = StoreDB;
CREATE LOGIN AnalystLogin WITH PASSWORD = 'AnalystPass123', DEFAULT_DATABASE = StoreDB;
CREATE LOGIN RestrictedLogin WITH PASSWORD = 'RestrictedPass123', DEFAULT_DATABASE = StoreDB;
GO
---Создание пользователей---
USE StoreDB;
GO
CREATE USER ManagerUser FOR LOGIN ManagerLogin;
CREATE USER AnalystUser FOR LOGIN AnalystLogin;
CREATE USER RestrictedUser FOR LOGIN RestrictedLogin;
GO
---Создание ролей---
USE StoreDB;
GO
CREATE ROLE ProductManagerRole;
CREATE ROLE LimitedViewerRole;
GO
GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.Products TO ProductManagerRole;
GRANT SELECT (ProductID, ProductName, Price) ON dbo.Products TO LimitedViewerRole;
GO
---Добавление права доступа---
ALTER ROLE ProductManagerRole ADD MEMBER ManagerUser;
ALTER ROLE LimitedViewerRole ADD MEMBER RestrictedUser;
ALTER ROLE db_datareader ADD MEMBER AnalystUser;
GO

---Проверка---
USE StoreDB;
GO
SELECT name, type_desc 
FROM sys.database_principals 
WHERE name IN ('ManagerUser', 'AnalystUser', 'RestrictedUser');
GO

USE master;
GO
SELECT name, default_database_name 
FROM sys.sql_logins 
WHERE name IN ('ManagerLogin', 'AnalystLogin', 'RestrictedLogin');
GO  