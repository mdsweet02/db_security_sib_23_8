USE master;
GO

CREATE LOGIN Admin_Pitanie
WITH PASSWORD = 'Admin123!',
DEFAULT_DATABASE = Питание_1;
GO
CREATE LOGIN Manager_Pitanie
WITH PASSWORD = 'Manager123!',
DEFAULT_DATABASE = Питание_1;
GO
CREATE LOGIN Viewer_Pitanie
WITH PASSWORD = 'Viewer123!',
DEFAULT_DATABASE = Питание_1;
GO

Проверка
SELECT name, default_database_name
FROM sys.sql_logins
WHERE name LIKE '%Pitanie%';

user
USE Питание_1;
GO

CREATE USER AdminUser FOR LOGIN Admin_Pitanie;
CREATE USER ManagerUser FOR LOGIN Manager_Pitanie;
CREATE USER ViewerUser FOR LOGIN Viewer_Pitanie;
GO

Проверка
SELECT name, type_desc
FROM sys.database_principals
WHERE name LIKE '%User';

Роли
CREATE ROLE role_admin;
CREATE ROLE role_manager;
CREATE ROLE role_viewer;
GO

Полный доступ
GRANT SELECT, INSERT, UPDATE, DELETE ON SCHEMA::dbo TO role_admin;

Менеджер (работа с заказами и расчетами)
GRANT SELECT, INSERT, UPDATE
ON Заказ TO role_manager;
GRANT SELECT, INSERT, UPDATE
ON Расчет TO role_manager;
GRANT SELECT
ON Меню TO role_manager;

Только просмотр (ограниченный доступ)
GRANT SELECT
ON Продукт TO role_viewer;
GRANT SELECT
ON Блюда TO role_viewer;
GRANT SELECT
ON Меню TO role_viewer;
DENY SELECT ON Расчет TO role_viewer;

НАЗНАЧЕНИЕ РОЛЕЙ ПОЛЬЗОВАТЕЛЯМ
ALTER ROLE role_admin ADD MEMBER AdminUser;
ALTER ROLE role_manager ADD MEMBER ManagerUser;
ALTER ROLE role_viewer ADD MEMBER ViewerUser;
GO

Проверка
SELECT dp1.name AS RoleName,
       dp2.name AS UserName
FROM sys.database_role_members drm
JOIN sys.database_principals dp1
  ON drm.role_principal_id = dp1.principal_id
JOIN sys.database_principals dp2
  ON drm.member_principal_id = dp2.principal_id;