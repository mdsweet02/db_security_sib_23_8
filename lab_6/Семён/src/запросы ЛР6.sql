-- Задание 4
ALTER ROLE [role_read_only] DROP MEMBER [user_read]
ALTER ROLE [role_edit_data] DROP MEMBER [user_edit]
ALTER ROLE [role_edit_data] DROP MEMBER [User_NoMask]
ALTER ROLE [role_limited_access] DROP MEMBER [user_limited]

ALTER DATABASE [Станция_технического_обслуживания_автомобилей] SET AUTO_CLOSE OFF

USE master;
GO
CREATE MASTER KEY ENCRYPTION BY PASSWORD= '<Shatsk1y>';
GO
CREATE CERTIFICATE StationServerCert
    WITH SUBJECT = 'Semyon';
GO
USE Станция_технического_обслуживания_автомобилей;
GO
CREATE DATABASE ENCRYPTION KEY WITH ALGORITHM = AES_256
    ENCRYPTION BY SERVER CERTIFICATE MyServerCert;
GO
ALTER DATABASE Станция_технического_обслуживания_автомобилей
    SET ENCRYPTION ON;
GO

-- Задание 6
ALTER DATABASE [Станция_технического_обслуживания_автомобилей] SET AUTO_CLOSE ON