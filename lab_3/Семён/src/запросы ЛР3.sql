-- Задание 1
>sqlcmd -S localhost\SQLEXPRESS –U login_read -P Read1234 -d Станция_технического_обслуживания_автомобилей
1>SELECT * FROM Заказ
2>GO

-- Задание 2
>sqlcmd -S localhost\SQLEXPRESS -U login_read -P Read1234 -d "Станция_технического_обслуживания_автомобилей" -Q "SET NOCOUNT ON; SELECT * FROM Заказ;" -s ";" -W -o C:\test\db.txt -u

-- Задание 3
>sqlcmd -S "localhost\SQLEXPRESS" -U login_read -P Read1234 -d "Станция_технического_обслуживания_автомобилей" -i "C:\test\task_3.sql" -o "C:\test\db.txt" -s ";" -u
 
-- Задание 4
--Экспорт
>sqlcmd -S localhost\SQLEXPRESS -U login_read -P Read1234 -d "Станция_технического_обслуживания_автомобилей" -Q "SET NOCOUNT ON; SELECT * FROM Склад;" -s ";" -W -o C:\test\sklad.csv -u

--Импорт
USE [TestDB];
GO
CREATE TABLE Склад
(
    Код_детали INT PRIMARY KEY,
    Наименование NVARCHAR(100),
    Тип NVARCHAR(50),
    Ед_измерения NVARCHAR(20),
    Цена DECIMAL(10,4),
    Колво INT
);
GO
BULK INSERT Склад
FROM 'C:\test\sklad.csv'
WITH
(
    FIRSTROW = 3,
    FIELDTERMINATOR = ';',
    ROWTERMINATOR = '\n',
	DATAFILETYPE = 'widechar',
	ERRORFILE = 'C:\test\bulk_errors_utf16.txt',
	TABLOCK
);
GO