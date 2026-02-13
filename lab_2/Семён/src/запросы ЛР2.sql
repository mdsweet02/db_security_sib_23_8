-- Задание 1

-- Сохранение БД в .bak файл
BACKUP DATABASE TestDB TO DISK = 'C:\Student\test\AW.bak';

-- Добавление изменений в БД
Use TestDB;
INSERT INTO Работники VALUES (44444, 'Михаил', 'Кассир', 3443455)
Select *  from Работники;

-- Сохранение транзациий
BACKUP LOG TestDB TO DISK = 'C:\Student\test\AW1.trn';

-- Добавление еще изменений в БД
Use TestDB;
INSERT INTO Работники VALUES (34457, 'Лариса', 'Кассир', 3443455)
Select *  from Работники;

-- Создание разностной резервной копии
BACKUP DATABASE TestDB TO DISK =  'C:\Student\test\AWDIFF1.bak' WITH DIFFERENTIAL;

-- Добавление и еще изменений в БД
Use TestDB;
INSERT INTO Работники VALUES (36455, 'Оксана', 'Кассир', 3443455)
Select *  from Работники;

-- Сохранение транзациий
BACKUP LOG TestDB TO DISK = 'C:\Student\test\AW2.trn';

-- Задание 2

-- Проверка БД
Select *  from Работники;
BACKUP DATABASE TestDBExample
TO DISK = 'C:\Student\db\TestDBExample_Encrypted.bak'
WITH
    ENCRYPTION (
        ALGORITHM = AES_256,
        SERVER CERTIFICATE = MyCert
    ),
    INIT;
GO

-- Задание 3

-- Создание БД TestDBExample
CREATE DATABASE TestDBExample;
GO

-- Создание Мастер-ключа
USE TestDBExample;
GO
CREATE MASTER KEY
ENCRYPTION BY PASSWORD = 'MASTER_KEY_IS_SAFE123!';
GO

-- Создание сертификата MyCert
CREATE CERTIFICATE MyCert
WITH SUBJECT = 'Certificate for TestDBExample backup encryption';
GO

-- Резервная копия мастер-ключа и сертификата
BACKUP MASTER KEY
TO FILE = 'C:\Student\db\TestDBExample_masterkey.key'
ENCRYPTION BY PASSWORD = 'SafePassword_1234!';
GO
BACKUP CERTIFICATE MyCert
TO FILE = 'C:\Student\db\MyCert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\Student\db\MyCert_PrivateKey.pvk',
    ENCRYPTION BY PASSWORD = 'SafePassword_123!'
);
GO

-- Резервная копия БД (не работает в экспресс версии)
BACKUP DATABASE TestDBExample
TO DISK = 'C:\Student\db\TestDBExample_Encrypted.bak'
WITH
    ENCRYPTION (
        ALGORITHM = AES_256,
        SERVER CERTIFICATE = MyCert
    ),
    INIT;
GO

-- Резервная копия
BACKUP DATABASE TestDBExample
TO DISK = 'C:\Student\db\TestDBExample_Encrypted.bak'
GO

-- Задание 4

-- Удаление сертификата
USE TestDBExample;
GO
DROP CERTIFICATE MyCert;
GO

-- Удаление мастер-ключа
DROP MASTER KEY;
GO

-- Удаление БД
USE master;
GO
DROP DATABASE TestDBExample;
GO

-- Восстановление зашифрованного БД с файла 

-- Задание 5

-- Создание мастер-ключа
USE master;
GO
CREATE MASTER KEY
ENCRYPTION BY PASSWORD = 'StrongPassword_123!';
GO

-- Восстановление сертификата
CREATE CERTIFICATE MyCert
FROM FILE = 'C:\Student\db\MyCert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\Student\db\MyCert_PrivateKey.pvk',
    DECRYPTION BY PASSWORD = 'SafePassword_123!'
);
GO

-- Восстановление БД
RESTORE DATABASE TestDBExample
FROM DISK = 'C:\Student\db\TestDBExample_Encrypted.bak'
WITH REPLACE;
GO