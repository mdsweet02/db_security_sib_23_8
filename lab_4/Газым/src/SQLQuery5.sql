--2.1
ALTER TABLE dbo.Работники
ALTER COLUMN ФИО NVARCHAR(100)
MASKED WITH (FUNCTION = 'partial(1,"XXXXX",1)');

--2.2
ALTER TABLE dbo.Расчет
DROP CONSTRAINT CK__Расчет__Сумма_за__6B24EA82;

ALTER TABLE dbo.Расчет
ALTER COLUMN Сумма_заказа INT
MASKED WITH (FUNCTION = 'default()');

ALTER TABLE dbo.Расчет
ADD CONSTRAINT CK_Сумма_заказа CHECK (Сумма_заказа > 0);

--2.3
ALTER TABLE dbo.Расчет
DROP CONSTRAINT CK__Расчет__Сумма_об__6C190EBB;

ALTER TABLE dbo.Расчет
ALTER COLUMN Сумма_обслуживания INT
MASKED WITH (FUNCTION = 'default()');

ALTER TABLE dbo.Расчет
ADD CONSTRAINT CK_Сумма_обслуживания CHECK (Сумма_обслуживания > 0);

--2.4
ALTER TABLE dbo.Склад
DROP CONSTRAINT CK__Склад__Цена__5BE2A6F2;

ALTER TABLE dbo.Склад
ALTER COLUMN Цена INT
MASKED WITH (FUNCTION = 'default()');

ALTER TABLE dbo.Склад
ADD CONSTRAINT CK_Цена CHECK (Цена > 0);

--3 --4
CREATE LOGIN TestUser WITH PASSWORD = 'Password123!';
GO

USE Питание_1;
GO

CREATE USER TestUser FOR LOGIN TestUser;
GO

--Доступ
GRANT SELECT ON dbo.Работники TO TestUser;
GRANT SELECT ON dbo.Склад TO TestUser;
GRANT SELECT ON dbo.Расчет TO TestUser;

--5 Проверка
EXECUTE AS USER = 'TestUser';
SELECT * FROM dbo.Работники;
SELECT * FROM dbo.Склад;
SELECT * FROM dbo.Расчет;
REVERT;

--6
USE Питание_1;
GO

REVERT;

GRANT SELECT ON dbo.Работники TO TestUser;
GRANT SELECT ON dbo.Склад TO TestUser;
GRANT SELECT ON dbo.Расчет TO TestUser;
GRANT UNMASK TO TestUser;

--Проверка
EXECUTE AS USER = 'TestUser';
SELECT * FROM dbo.Работники;
SELECT * FROM dbo.Склад;
SELECT * FROM dbo.Расчет;
REVERT;

--7
REVERT
REVOKE UNMASK FROM TestUser;

--8
USE Питание_1
GO

ALTER TABLE dbo.Работники
ALTER COLUMN ФИО DROP MASKED; 
ALTER TABLE dbo.Расчет 
ALTER COLUMN Сумма_заказа DROP MASKED; 
ALTER TABLE dbo.Расчет
ALTER COLUMN Сумма_обслуживания DROP MASKED;
ALTER TABLE dbo.Склад
ALTER COLUMN Цена DROP MASKED;

--9
EXECUTE AS USER = 'TestUser';

SELECT *
FROM dbo.Расчет
WHERE Сумма_заказа > 10000;

REVERT;

EXECUTE AS USER = 'TestUser';

SELECT *
FROM dbo.Работники
WHERE ФИО LIKE 'И%';

REVERT;