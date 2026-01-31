-- Задание 2
sp_helpsrvrole;

-- Задание 3
sp_addlogin 'TempUser', 'Password!'
sp_helplogins;

sp_addsrvrolemember TempUser, securityadmin

-- Задание 4
USE Тест;

sp_helprole;

sp_helprolemember db_owner

-- Задание 5
sp_adduser TempUser, MyFirstUser;

sp_helpuser;

sp_addrolemember db_datareader, MyFirstUser;
GO
sp_helpuser

-- Задание 6
GRANT select, update on Тест.Заказ to MyFirstUser;

sp_addlogin 'AndyUser', 'andy';
GO
sp_adduser AndyUser, Andy;
GRANT select on товары (название_товара, Цена) to Andy;Э

-- Задание 8
sp_droprolemember db_datareader, MyFirstUser;
go
sp_helpuser;

sp_dropuser MyFirstUser
go
sp_helpuser

sp_dropsrvrolemember TempUser, securityadmin;

sp_droplogin TempUser
go
sp_helplogins;

-- Самостоятельная работа
USE master;
GO
CREATE LOGIN login_read
WITH PASSWORD = 'Read1234',
DEFAULT_DATABASE = Станция_технического_обслуживания_автомобилей;
CREATE LOGIN login_edit
WITH PASSWORD = 'Edit1234',
DEFAULT_DATABASE = Станция_технического_обслуживания_автомобилей;
CREATE LOGIN login_limited
WITH PASSWORD = 'Limit1234',
DEFAULT_DATABASE = Станция_технического_обслуживания_автомобилей;
GO
sp_helplogins;

USE Станция_технического_обслуживания_автомобилей;
GO
CREATE USER user_read FOR LOGIN login_read;
CREATE USER user_edit FOR LOGIN login_edit;
CREATE USER user_limited FOR LOGIN login_limited;
GO
sp_helpuser

CREATE ROLE role_read_only;
CREATE ROLE role_edit_data;
CREATE ROLE role_limited_access;
GO
ALTER ROLE role_read_only ADD MEMBER user_read;
ALTER ROLE role_edit_data ADD MEMBER user_edit;
ALTER ROLE role_limited_access ADD MEMBER user_limited;
GO
sp_helpuser

GRANT SELECT TO role_read_only;
GO
GRANT SELECT, INSERT, UPDATE, DELETE
ON Заказ TO role_edit_data;
GRANT SELECT, INSERT, UPDATE, DELETE
ON Заказ_услуги TO role_edit_data;
GO
GRANT SELECT TO role_limited_access;
DENY SELECT ON dbo.Клиенты TO role_limited_access;
GO

SELECT name, default_database_name
FROM sys.sql_logins
WHERE name LIKE 'login_%';

SELECT r.name AS RoleName, m.name AS MemberName FROM sys.database_role_members
JOIN sys.database_principals r
  ON sys.database_role_members.role_principal_id = r.principal_id
JOIN sys.database_principals m
  ON sys.database_role_members.member_principal_id = m.principal_id;

-- Проверка

SELECT * FROM Заказ;

INSERT INTO Заказ (Номер_заказа, ИИН_Клиента, дата, Марка_ТС, Номер_ТС, Описание_ТС, Начало_выполнения, Конец_выполнения)
VALUES ('Z000022', '79151001226', '2026-01-23', 22, 'KZ012TUV35', 'Ремонт', '2025-06-21', '2025-06-23');

INSERT INTO Заказ (Номер_заказа, ИИН_Клиента, дата, Марка_ТС, Номер_ТС, Описание_ТС, Начало_выполнения, Конец_выполнения)
VALUES ('Z000025', '791510012346', '2025-02-20', 20, 'KZ012TUV35', 'Ремонт электропроводки', '2025-02-21', '2025-02-23');
SELECT * FROM Заказ;

SELECT * FROM Склад;

SELECT * FROM Склад;

SELECT * FROM Клиенты;