--3
create database TestDB

CREATE TABLE Product
(
    ProductID INT IDENTITY(1,1) PRIMARY KEY,
    Name NVARCHAR(100),
    ListPrice MONEY
);

BACKUP DATABASE TestDB TO DISK =  'C:\Student\Test\AW.bak'
--4
INSERT INTO Product (Name, ListPrice)
VALUES ('Test Product', 100);
--5
ALTER DATABASE TestDB
SET RECOVERY FULL;
BACKUP LOG TestDB TO DISK = 'C:\Student\Test\AW1.trn'
--6
INSERT INTO Product (Name, ListPrice)
VALUES ('Second Product', 200);
--7
BACKUP DATABASE TestDB TO DISK =  'C:\Student\Test\AWDIFF1.bak'  WITH DIFFERENTIAL
--8
UPDATE Product
SET ListPrice = 150
WHERE ProductID = 1;
--9
BACKUP LOG TestDB TO DISK = 'C:\Student\Test\AW2.TRN'
--8.2
INSERT INTO Product (Name, ListPrice)
VALUES ('New Product', 250);

--3.2
create database TestDBExample
--3.3
USE TestDBExample;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongPassword123!';
GO
--3.4
CREATE CERTIFICATE MyCert
WITH SUBJECT = 'Certificate for encrypting backups';
GO
--3.5
BACKUP MASTER KEY
TO FILE = 'C:\Student\Database\MasterKey.bak'
ENCRYPTION BY PASSWORD = 'AnotherStrongPassword123!';
GO

BACKUP CERTIFICATE MyCert
TO FILE = 'C:\Student\Database\MyCert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\Student\Database\MyCert_PrivateKey.pvk',
    ENCRYPTION BY PASSWORD = 'AnotherStrongPassword123!'
);
GO
--3.6
BACKUP DATABASE TestDBExample
TO DISK = 'C:\Student\Database\TestDBExample_Backup.bak'
WITH 
    ENCRYPTION (
        ALGORITHM = AES_256,
        SERVER CERTIFICATE = MyCert
    ),
    INIT;
GO

--4.1
USE master;
GO
DROP MASTER KEY;
GO
--4.2
DROP CERTIFICATE MyCert;
GO
--4.3
DROP DATABASE TestDBExample;
GO
--4.4
RESTORE DATABASE TestDBExample
FROM DISK = 'C:\Student\Database\TestDBExample_Backup.bak';
GO
--4.5
Сообщение 33111, уровень 16, состояние 3, строка 84
Не удается найти сервер сертификат с отпечатком "0xD7B9D46BEB1BA1DD58B7714D006764C0462D303D".
Сообщение 3013, уровень 16, состояние 1, строка 84
RESTORE DATABASE прервано с ошибкой.

Объяснение:
Резервная копия была зашифрована сертификатом MyCert и защищена мастер-ключом.
После удаления сертификата и мастер-ключа SQL Server не имеет возможности расшифровать резервную копию.
Без восстановления этих объектов БД восстановить невозможно.
--5.1
USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD = 'StrongPassword123!';
GO
--5.2
CREATE CERTIFICATE MyCert
FROM FILE = 'C:\Student\Database\MyCert.cer'
WITH PRIVATE KEY (
    FILE = 'C:\Student\Database\MyCert_PrivateKey.pvk',
    DECRYPTION BY PASSWORD = 'AnotherStrongPassword123!'
);
GO
--5.3
RESTORE DATABASE TestDBExample
FROM DISK = 'C:\Student\Database\TestDBExample_Backup.bak'
WITH REPLACE; -- Заменяет БД, если она существует
GO