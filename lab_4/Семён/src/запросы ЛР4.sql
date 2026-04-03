-- Задание 1 и 2
ALTER TABLE Работники
ALTER COLUMN ФИО
ADD MASKED WITH (FUNCTION = 'partial(1,"****",1)');
GO

ALTER TABLE Клиенты
ALTER COLUMN ФИО
ADD MASKED WITH (FUNCTION = 'partial(1,"****",1)');
GO

ALTER TABLE Клиенты
ALTER COLUMN Адрес_проживания
ADD MASKED WITH (FUNCTION = 'default()');
GO

ALTER TABLE Клиенты
ALTER COLUMN Телефон
ADD MASKED WITH (FUNCTION = 'partial(0,"*******",2)');
GO

ALTER TABLE Клиенты
ALTER COLUMN ИИН_Клиента
ADD MASKED WITH (FUNCTION = 'partial(0,"********",2)');
GO

ALTER TABLE Оплата
ALTER COLUMN Сумма
ADD MASKED WITH (FUNCTION = 'random(1000,50000)');
GO

ALTER TABLE Заказ
ALTER COLUMN Номер_ТС
ADD MASKED WITH (FUNCTION = 'partial(0,"***",3)');
GO

ALTER TABLE Заказ
ALTER COLUMN Описание_ТС 
ADD MASKED WITH (FUNCTION = 'default()');
GO

ALTER TABLE Заказ
ALTER COLUMN ИИН_Клиента
ADD MASKED WITH (FUNCTION = 'partial(0,"********",2)');
GO

ALTER TABLE Оплата
ALTER COLUMN ИИН_Клиента
ADD MASKED WITH (FUNCTION = 'partial(0,"********",2)');
GO

--Задание 4

CREATE LOGIN User_NoMask 
WITH PASSWORD = 'Password123!';
GO

CREATE USER User_NoMask FOR LOGIN User_NoMask;
GO

GRANT SELECT ON Клиенты TO User_NoMask;
GRANT SELECT ON Заказ TO User_NoMask;
GRANT SELECT ON Оплата TO User_NoMask;
GRANT SELECT ON Работники TO User_NoMask;
GO

-- Задание 3 и 5
SELECT * FROM Клиенты;
SELECT * FROM Заказ;
SELECT * FROM Оплата;
SELECT * FROM Работники;

-- Задание 6
GRANT UNMASK TO User_NoMask;
GO
SELECT * FROM Клиенты;
SELECT * FROM Заказ;
SELECT * FROM Оплата;
SELECT * FROM Работники;

-- Задание 7
REVOKE UNMASK TO User_NoMask;
GO
SELECT * FROM Клиенты;

-- Задание 8
ALTER TABLE Клиенты
ALTER COLUMN ФИО
DROP MASKED;
GO

ALTER TABLE Клиенты
ALTER COLUMN Телефон
DROP MASKED;
GO

-- Задание 9
SELECT ФИО FROM Клиенты;

SELECT * FROM Клиенты WHERE ИИН_Клиента = '811308890124';

SELECT * FROM Клиенты WHERE ФИО Like 'Кас%';

SELECT * FROM Оплата WHERE сумма BETWEEN 1000 AND 50000;
