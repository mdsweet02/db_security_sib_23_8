#!/usr/bin/env python3
import getpass
import os
import re
import sys
import time
from dataclasses import dataclass
from textwrap import dedent

from impacket import tds


DEFAULT_AUDIT_NAME = "Audit_UserActions"
DEFAULT_ADMIN_AUDIT_NAME = "Audit_AdminUsers"
DEFAULT_SERVER_SPEC = "Audit_LoginEvents"
DEFAULT_DB_SPEC = "Audit_EmployeeActions"
DEFAULT_DATABASE = "AuditLab"
DEFAULT_AUDIT_PATH = "/var/opt/mssql/log/"
DEFAULT_DEMO_USER = "audit_demo"
KNOWN_SERVER_SPECS = [
    "Audit_LoginEvents",
    "Audit_PermissionChanges",
    "Audit_AdminUsersSpec",
]
KNOWN_DB_SPECS = [
    "Audit_EmployeeActions",
    "Audit_ObjectChanges",
    "Audit_OneTableOnly",
    "Audit_UserOnly",
    "Audit_DeleteUpdateOnly",
    "Audit_AdminActions",
]


class Style:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[96m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"
    WHITE = "\033[97m"

    @classmethod
    def wrap(cls, text: str, *styles: str) -> str:
        return "".join(styles) + text + cls.RESET


@dataclass
class Config:
    host: str
    port: int
    user: str
    password: str
    database: str
    audit_path: str
    audit_name: str
    demo_user: str
    demo_password: str


class SqlAuditApp:
    def __init__(self, config: Config) -> None:
        self.config = config

    def connect(self, database: str | None = None, user: str | None = None, password: str | None = None):
        db = database or self.config.database
        login = user or self.config.user
        secret = password if password is not None else self.config.password

        client = tds.MSSQL(self.config.host, self.config.port, self.config.host)
        client.connect()
        ok = client.login(db, login, secret, "", None, False)
        if not ok:
            messages = self._messages(client)
            client.disconnect()
            raise RuntimeError("\n".join(messages) or f"Login failed for {login}")
        return client

    def _messages(self, client) -> list[str]:
        output = []
        for token_list in client.replies.values():
            for token in token_list:
                if hasattr(token, "fields") and "MsgText" in token.fields:
                    output.append(token["MsgText"].decode("utf-16le"))
        return output

    def execute(self, sql: str, database: str | None = None, user: str | None = None, password: str | None = None):
        sql = dedent(sql).strip()
        client = self.connect(database=database, user=user, password=password)
        try:
            rows = client.sql_query(sql)
            messages = self._messages(client)
            return rows or [], messages
        finally:
            client.disconnect()

    def announce(self, title: str, description: str, sql: str | None = None) -> None:
        print()
        print(Style.wrap("=" * 78, Style.BLUE))
        print(Style.wrap(title, Style.BOLD, Style.CYAN))
        print(Style.wrap(description, Style.DIM, Style.WHITE))
        if sql:
            print(Style.wrap("\nБудет выполнен SQL:", Style.BOLD, Style.YELLOW))
            self.print_sql(sql)
        print(Style.wrap("=" * 78, Style.BLUE))

    @staticmethod
    def print_sql(sql: str) -> None:
        sql = dedent(sql).strip()
        for line in sql.splitlines():
            print(Style.wrap(f"SQL> {line}", Style.MAGENTA))

    @staticmethod
    def _drop_known_server_specs_sql() -> str:
        chunks = []
        for name in KNOWN_SERVER_SPECS:
            chunks.append(
                f"""
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'{name}')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION {name} WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION {name};
END;
""".strip()
            )
        return "\n".join(chunks)

    @staticmethod
    def _drop_known_db_specs_sql() -> str:
        chunks = []
        for name in KNOWN_DB_SPECS:
            chunks.append(
                f"""
IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = N'{name}')
BEGIN
    ALTER DATABASE AUDIT SPECIFICATION {name} WITH (STATE = OFF);
    DROP DATABASE AUDIT SPECIFICATION {name};
END;
""".strip()
            )
        return "\n".join(chunks)

    def _audit_status_sql(self, audit_name: str) -> str:
        return f"""
SELECT name, status_desc, audit_file_path
FROM sys.dm_server_audit_status
WHERE name = '{audit_name}';
"""

    def _get_audit_pattern_for(self, audit_name: str) -> str:
        rows, _ = self.execute(self._audit_status_sql(audit_name), database="master")
        if not rows:
            raise RuntimeError(f"Аудит {audit_name} не найден. Сначала создайте его.")
        path = rows[0]["audit_file_path"]
        return re.sub(r"_0_\\d+\\.sqlaudit$", "_*.sqlaudit", path)

    def prepare_environment(self) -> None:
        sql = f"""
IF DB_ID(N'{DEFAULT_DATABASE}') IS NULL
    CREATE DATABASE {DEFAULT_DATABASE};

USE {DEFAULT_DATABASE};

IF OBJECT_ID(N'dbo.Employees', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Employees
    (
        EmployeeID INT PRIMARY KEY,
        FullName NVARCHAR(100),
        Department NVARCHAR(100),
        Salary INT
    );
END;

IF COL_LENGTH('dbo.Employees', 'NationalID') IS NULL
    ALTER TABLE dbo.Employees
    ADD NationalID NVARCHAR(20) MASKED WITH (FUNCTION = 'partial(0,\"XXXXXX\",4)') NULL;

DELETE FROM dbo.Employees WHERE EmployeeID = 4;

IF OBJECT_ID(N'dbo.TestTable', N'U') IS NOT NULL
    DROP TABLE dbo.TestTable;

USE master;

IF NOT EXISTS (SELECT 1 FROM sys.server_principals WHERE name = N'{self.config.demo_user}')
    CREATE LOGIN [{self.config.demo_user}] WITH PASSWORD = N'{self.config.demo_password}';

USE {DEFAULT_DATABASE};

IF USER_ID(N'{self.config.demo_user}') IS NULL
    CREATE USER [{self.config.demo_user}] FOR LOGIN [{self.config.demo_user}];

GRANT SELECT, INSERT, UPDATE, DELETE, ALTER TO [{self.config.demo_user}];
GRANT UNMASK TO [{self.config.demo_user}];
"""
        sql_seed = """
USE AuditLab;

UPDATE dbo.Employees
SET FullName = N'Иванов Иван',
    Department = N'IT',
    Salary = 800000,
    NationalID = N'990101123456'
WHERE EmployeeID = 1;

IF @@ROWCOUNT = 0
    INSERT INTO dbo.Employees (EmployeeID, FullName, Department, Salary, NationalID)
    VALUES (1, N'Иванов Иван', N'IT', 800000, N'990101123456');

UPDATE dbo.Employees
SET FullName = N'Петров Петр',
    Department = N'Finance',
    Salary = 900000,
    NationalID = N'980202654321'
WHERE EmployeeID = 2;

IF @@ROWCOUNT = 0
    INSERT INTO dbo.Employees (EmployeeID, FullName, Department, Salary, NationalID)
    VALUES (2, N'Петров Петр', N'Finance', 900000, N'980202654321');

UPDATE dbo.Employees
SET FullName = N'Сидоров Алексей',
    Department = N'HR',
    Salary = 650000,
    NationalID = N'970303777888'
WHERE EmployeeID = 3;

IF @@ROWCOUNT = 0
    INSERT INTO dbo.Employees (EmployeeID, FullName, Department, Salary, NationalID)
    VALUES (3, N'Сидоров Алексей', N'HR', 650000, N'970303777888');
"""
        display_sql = (sql + "\n\n" + sql_seed).replace(self.config.demo_password, "<demo_password>")
        self.announce(
            "Подготовка среды",
            "Создаст тестовую базу, таблицу Employees, добавит маскируемое поле NationalID и подготовит demo-пользователя.",
            display_sql,
        )
        rows, messages = self.execute(sql, database="master")
        rows2, messages2 = self.execute(sql_seed, database=DEFAULT_DATABASE)
        self.print_messages(messages + messages2)
        rows.extend(rows2)
        self.print_table(rows, "Результат подготовки")

    def create_server_audit_only(self) -> None:
        sql = f"""
USE master;
{self._drop_known_server_specs_sql()}

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'{self.config.audit_name}')
BEGIN
    ALTER SERVER AUDIT {self.config.audit_name} WITH (STATE = OFF);
    DROP SERVER AUDIT {self.config.audit_name};
END;

CREATE SERVER AUDIT {self.config.audit_name}
TO FILE
(
    FILEPATH = N'{self.config.audit_path}',
    MAXSIZE = 100 MB,
    MAX_ROLLOVER_FILES = 10,
    RESERVE_DISK_SPACE = OFF
)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT {self.config.audit_name} WITH (STATE = ON);

{self._audit_status_sql(self.config.audit_name)}
"""
        self.announce(
            "Часть 1: создание SQL Server Audit",
            "Создаст SERVER AUDIT и сразу покажет, что он находится в состоянии STARTED.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 2")

    def create_server_spec_only(self) -> None:
        sql = f"""
USE master;
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'{DEFAULT_SERVER_SPEC}')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC} WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC};
END;

CREATE SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC}
FOR SERVER AUDIT {self.config.audit_name}
ADD (SUCCESSFUL_LOGIN_GROUP),
ADD (FAILED_LOGIN_GROUP),
ADD (LOGOUT_GROUP)
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.server_audit_specifications
WHERE name = '{DEFAULT_SERVER_SPEC}';
"""
        self.announce(
            "Часть 2: создание Server Audit Specification",
            "Создаст серверную спецификацию для успешных входов, неуспешных входов и выходов.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 3")

    def create_database_spec_only(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
{self._drop_known_db_specs_sql()}

CREATE DATABASE AUDIT SPECIFICATION {DEFAULT_DB_SPEC}
FOR SERVER AUDIT {self.config.audit_name}
ADD (SELECT ON dbo.Employees BY PUBLIC),
ADD (INSERT ON dbo.Employees BY PUBLIC),
ADD (UPDATE ON dbo.Employees BY PUBLIC),
ADD (DELETE ON dbo.Employees BY PUBLIC)
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.database_audit_specifications
WHERE name = '{DEFAULT_DB_SPEC}';
"""
        self.announce(
            "Часть 3: создание Database Audit Specification",
            "Создаст аудит чтения, вставки, изменения и удаления только для таблицы Employees.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 4")

    def setup_lab(self) -> None:
        sql = f"""
IF DB_ID(N'{DEFAULT_DATABASE}') IS NULL
    CREATE DATABASE {DEFAULT_DATABASE};

USE {DEFAULT_DATABASE};

IF OBJECT_ID(N'dbo.Employees', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.Employees
    (
        EmployeeID INT PRIMARY KEY,
        FullName NVARCHAR(100),
        Department NVARCHAR(100),
        Salary INT
    );
END;

DELETE FROM dbo.Employees WHERE EmployeeID = 4;

MERGE dbo.Employees AS target
USING (VALUES
    (1, N'Иванов Иван', N'IT', 800000),
    (2, N'Петров Петр', N'Finance', 900000),
    (3, N'Сидоров Алексей', N'HR', 650000)
) AS src(EmployeeID, FullName, Department, Salary)
ON target.EmployeeID = src.EmployeeID
WHEN MATCHED THEN
    UPDATE SET FullName = src.FullName, Department = src.Department, Salary = src.Salary
WHEN NOT MATCHED THEN
    INSERT (EmployeeID, FullName, Department, Salary)
    VALUES (src.EmployeeID, src.FullName, src.Department, src.Salary);

IF OBJECT_ID(N'dbo.TestTable', N'U') IS NOT NULL
    DROP TABLE dbo.TestTable;

USE master;

IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'{DEFAULT_SERVER_SPEC}')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC} WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC};
END;

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'{self.config.audit_name}')
BEGIN
    ALTER SERVER AUDIT {self.config.audit_name} WITH (STATE = OFF);
    DROP SERVER AUDIT {self.config.audit_name};
END;

CREATE SERVER AUDIT {self.config.audit_name}
TO FILE
(
    FILEPATH = N'{self.config.audit_path}',
    MAXSIZE = 100 MB,
    MAX_ROLLOVER_FILES = 10,
    RESERVE_DISK_SPACE = OFF
)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT {self.config.audit_name} WITH (STATE = ON);

CREATE SERVER AUDIT SPECIFICATION {DEFAULT_SERVER_SPEC}
FOR SERVER AUDIT {self.config.audit_name}
ADD (SUCCESSFUL_LOGIN_GROUP),
ADD (FAILED_LOGIN_GROUP),
ADD (LOGOUT_GROUP),
ADD (SERVER_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_PERMISSION_CHANGE_GROUP)
WITH (STATE = ON);

USE {DEFAULT_DATABASE};

IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = N'{DEFAULT_DB_SPEC}')
BEGIN
    ALTER DATABASE AUDIT SPECIFICATION {DEFAULT_DB_SPEC} WITH (STATE = OFF);
    DROP DATABASE AUDIT SPECIFICATION {DEFAULT_DB_SPEC};
END;

CREATE DATABASE AUDIT SPECIFICATION {DEFAULT_DB_SPEC}
FOR SERVER AUDIT {self.config.audit_name}
ADD (SELECT ON dbo.Employees BY PUBLIC),
ADD (INSERT ON dbo.Employees BY PUBLIC),
ADD (UPDATE ON dbo.Employees BY PUBLIC),
ADD (DELETE ON dbo.Employees BY PUBLIC),
ADD (SCHEMA_OBJECT_CHANGE_GROUP)
WITH (STATE = ON);
"""
        self.announce(
            "Настройка лабораторной",
            "Создаст AuditLab, Employees, SERVER AUDIT и обе спецификации аудита.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Настройка завершена")

    def generate_demo_events(self) -> None:
        sql = """
SELECT * FROM dbo.Employees;

INSERT INTO dbo.Employees (EmployeeID, FullName, Department, Salary)
VALUES (4, N'Касымов Ержан', N'IT', 750000);

UPDATE dbo.Employees
SET Salary = 850000
WHERE EmployeeID = 1;

DELETE FROM dbo.Employees
WHERE EmployeeID = 3;

CREATE TABLE dbo.TestTable (ID INT);
DROP TABLE dbo.TestTable;
"""
        self.announce(
            "Генерация тестовых событий",
            "Выполнит SELECT, INSERT, UPDATE, DELETE, CREATE TABLE и DROP TABLE под demo-пользователем.",
            sql,
        )
        rows, messages = self.execute(
            sql,
            database=DEFAULT_DATABASE,
            user=self.config.demo_user,
            password=self.config.demo_password,
        )
        self.print_messages(messages)
        self.print_table(rows, "События выполнены")
        self._generate_failed_login()

    def _generate_failed_login(self) -> None:
        print(Style.wrap("\nДополнительно создаю одно неуспешное подключение для FAILED_LOGIN_GROUP.", Style.YELLOW))
        client = tds.MSSQL(self.config.host, self.config.port, self.config.host)
        client.connect()
        client.login(DEFAULT_DATABASE, self.config.demo_user, "WrongPassword_123!", "", None, False)
        client.disconnect()
        time.sleep(1)

    def audit_status(self) -> None:
        sql = f"""
SELECT name, status_desc, audit_file_path
FROM sys.dm_server_audit_status
WHERE name = '{self.config.audit_name}';
"""
        self.announce(
            "Статус аудита",
            "Покажет, запущен ли SERVER AUDIT и в какой .sqlaudit файл он пишет.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Статус аудита")

    def revoke_unmask(self) -> None:
        target_user = self.config.demo_user
        if target_user.lower() == "sa":
            target_user = DEFAULT_DEMO_USER
        sql = f"""
USE {DEFAULT_DATABASE};
REVOKE UNMASK FROM [{target_user}];

SELECT permission_name, state_desc
FROM sys.database_permissions p
JOIN sys.database_principals dp
    ON p.grantee_principal_id = dp.principal_id
WHERE dp.name = '{target_user}'
  AND permission_name = 'UNMASK';
"""
        self.announce(
            "Часть 5: отозвать право UNMASK",
            f"Отзовет у пользователя {target_user} право видеть реальные значения маскируемого поля NationalID.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 6")

    def show_recent_records(self) -> None:
        pattern = self.get_audit_pattern()
        sql = f"""
SELECT TOP 20
    event_time,
    CONVERT(varchar(4), action_id) AS action_id,
    succeeded,
    server_principal_name,
    database_name,
    object_name,
    statement,
    client_ip
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
ORDER BY event_time DESC;
"""
        self.announce(
            "Последние события аудита",
            "Считает последние записи из .sqlaudit файла и покажет, кто, что и когда делал.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Последние события аудита")

    def show_delete_events(self) -> None:
        self._show_filtered(
            """
SELECT event_time, server_principal_name, object_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE action_id = 'DL'
ORDER BY event_time DESC;
""",
            "Удаления",
        )

    def suspicious_queries_pack(self) -> None:
        pattern = self.get_audit_pattern()
        blocks = [
            (
                "Подозрительные удаления",
                f"""
SELECT event_time, server_principal_name, object_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE action_id = 'DL'
ORDER BY event_time DESC;
""",
            ),
            (
                "Изменения Salary",
                f"""
SELECT event_time, server_principal_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE statement LIKE '%Salary%'
ORDER BY event_time DESC;
""",
            ),
            (
                "Неуспешные входы",
                f"""
SELECT event_time, server_principal_name, succeeded, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE action_id = 'LGIF'
ORDER BY event_time DESC;
""",
            ),
            (
                "Действия конкретного пользователя",
                f"""
SELECT event_time, CONVERT(varchar(4), action_id) AS action_id, object_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE server_principal_name = '{self.config.demo_user}'
ORDER BY event_time DESC;
""",
            ),
        ]
        print()
        print(Style.wrap("=" * 78, Style.BLUE))
        print(Style.wrap("Часть 6: поиск подозрительных действий", Style.BOLD, Style.CYAN))
        print(Style.wrap("По очереди выполнит четыре запроса, чтобы получить скрины 7-10.", Style.DIM, Style.WHITE))
        print(Style.wrap("=" * 78, Style.BLUE))
        for title, sql in blocks:
            self.print_sql(sql)
            rows, messages = self.execute(sql, database="master")
            self.print_messages(messages)
            self.print_table(rows, title)

    def show_salary_events(self) -> None:
        self._show_filtered(
            """
SELECT event_time, server_principal_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE statement LIKE '%Salary%'
ORDER BY event_time DESC;
""",
            "События по Salary",
        )

    def show_failed_logins(self) -> None:
        self._show_filtered(
            """
SELECT event_time, server_principal_name, succeeded, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE action_id = 'LGIF'
ORDER BY event_time DESC;
""",
            "Неуспешные входы",
        )

    def show_user_events(self, principal_name: str) -> None:
        pattern = self.get_audit_pattern()
        safe_name = principal_name.replace("'", "''")
        sql = f"""
SELECT TOP 20
    event_time,
    CONVERT(varchar(4), action_id) AS action_id,
    object_name,
    statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE server_principal_name = '{safe_name}'
ORDER BY event_time DESC;
"""
        self.announce(
            f"События пользователя {principal_name}",
            "Покажет только те действия, где в аудите фигурирует выбранный логин.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, f"События пользователя {principal_name}")

    def show_employees(self) -> None:
        sql = """
SELECT EmployeeID, FullName, Department, Salary, NationalID
FROM dbo.Employees
ORDER BY EmployeeID;
"""
        self.announce(
            "Текущее содержимое Employees",
            "Покажет записи тестовой таблицы перед или после генерации событий.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Таблица Employees")

    def disable_audit(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
{self._drop_known_db_specs_sql()}

USE master;
{self._drop_known_server_specs_sql()}

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'{self.config.audit_name}')
    ALTER SERVER AUDIT {self.config.audit_name} WITH (STATE = OFF);

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'{DEFAULT_ADMIN_AUDIT_NAME}')
    ALTER SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME} WITH (STATE = OFF);
"""
        self.announce(
            "Отключение аудита",
            "Остановит database audit specification, server audit specification и сам SERVER AUDIT.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Аудит отключен")

    def create_permission_changes_spec(self) -> None:
        sql = f"""
USE master;
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'Audit_PermissionChanges')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION Audit_PermissionChanges WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION Audit_PermissionChanges;
END;

CREATE SERVER AUDIT SPECIFICATION Audit_PermissionChanges
FOR SERVER AUDIT {self.config.audit_name}
ADD (SERVER_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_ROLE_MEMBER_CHANGE_GROUP),
ADD (DATABASE_PERMISSION_CHANGE_GROUP)
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.server_audit_specifications
WHERE name = 'Audit_PermissionChanges';
"""
        self.announce(
            "Часть 7: аудит изменения прав доступа",
            "Создаст отдельную server audit specification для ролей и прав доступа.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 11")

    def create_object_changes_spec(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = N'Audit_ObjectChanges')
BEGIN
    ALTER DATABASE AUDIT SPECIFICATION Audit_ObjectChanges WITH (STATE = OFF);
    DROP DATABASE AUDIT SPECIFICATION Audit_ObjectChanges;
END;

CREATE DATABASE AUDIT SPECIFICATION Audit_ObjectChanges
FOR SERVER AUDIT {self.config.audit_name}
ADD (SCHEMA_OBJECT_CHANGE_GROUP)
WITH (STATE = ON);

CREATE TABLE dbo.TestTable (ID INT);
DROP TABLE dbo.TestTable;

SELECT name, is_state_enabled
FROM sys.database_audit_specifications
WHERE name = 'Audit_ObjectChanges';
"""
        self.announce(
            "Часть 8: аудит создания и удаления объектов",
            "Включит аудит изменения схемы и сразу создаст/удалит TestTable для наглядного результата.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 12")

    def task_one_table_only(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
{self._drop_known_db_specs_sql()}

CREATE DATABASE AUDIT SPECIFICATION Audit_OneTableOnly
FOR SERVER AUDIT {self.config.audit_name}
ADD (SELECT ON dbo.Employees BY PUBLIC),
ADD (INSERT ON dbo.Employees BY PUBLIC),
ADD (UPDATE ON dbo.Employees BY PUBLIC),
ADD (DELETE ON dbo.Employees BY PUBLIC)
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.database_audit_specifications
WHERE name = 'Audit_OneTableOnly';
"""
        self.announce(
            "Задание 1: аудит только одной таблицы",
            "Настроит аудит только для dbo.Employees и покажет включенную спецификацию.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 14")

    def task_specific_user(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
{self._drop_known_db_specs_sql()}

CREATE DATABASE AUDIT SPECIFICATION Audit_UserOnly
FOR SERVER AUDIT {self.config.audit_name}
ADD (SELECT ON dbo.Employees BY [{self.config.demo_user}]),
ADD (INSERT ON dbo.Employees BY [{self.config.demo_user}]),
ADD (UPDATE ON dbo.Employees BY [{self.config.demo_user}]),
ADD (DELETE ON dbo.Employees BY [{self.config.demo_user}])
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.database_audit_specifications
WHERE name = 'Audit_UserOnly';
"""
        self.announce(
            "Задание 2: аудит только для конкретного пользователя",
            f"Настроит аудит операций только для пользователя {self.config.demo_user}.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 15")

    def task_delete_update_only(self) -> None:
        sql = f"""
USE {DEFAULT_DATABASE};
{self._drop_known_db_specs_sql()}

CREATE DATABASE AUDIT SPECIFICATION Audit_DeleteUpdateOnly
FOR SERVER AUDIT {self.config.audit_name}
ADD (UPDATE ON dbo.Employees BY PUBLIC),
ADD (DELETE ON dbo.Employees BY PUBLIC)
WITH (STATE = ON);

SELECT name, is_state_enabled
FROM sys.database_audit_specifications
WHERE name = 'Audit_DeleteUpdateOnly';
"""
        self.announce(
            "Задание 3: аудит только DELETE и UPDATE",
            "Включит аудит только двух наиболее критичных операций изменения данных.",
            sql,
        )
        rows, messages = self.execute(sql, database=DEFAULT_DATABASE)
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 16")

    def task_last_24h(self) -> None:
        pattern = self.get_audit_pattern()
        sql = f"""
SELECT event_time, CONVERT(varchar(4), action_id) AS action_id, server_principal_name, object_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE event_time >= DATEADD(HOUR, -24, SYSUTCDATETIME())
ORDER BY event_time DESC;
"""
        self.announce(
            "Задание 4: все события за последние 24 часа",
            "Отберет только актуальные события последних суток.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 17")

    def task_sensitive_field_actions(self) -> None:
        pattern = self.get_audit_pattern()
        sql = f"""
SELECT event_time, server_principal_name, object_name, statement
FROM sys.fn_get_audit_file('{pattern}', DEFAULT, DEFAULT)
WHERE statement LIKE '%Salary%'
   OR statement LIKE '%NationalID%'
ORDER BY event_time DESC;
"""
        self.announce(
            "Задание 5: действия с чувствительными данными",
            "Покажет запросы, где менялись или читались Salary и NationalID.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 18")

    def task_failed_logins(self) -> None:
        self.announce(
            "Задание 6: все случаи неудачного входа",
            "Выведет только записи FAILED_LOGIN_GROUP.",
            f"""
SELECT event_time, server_principal_name, succeeded, statement
FROM sys.fn_get_audit_file('{self.get_audit_pattern()}', DEFAULT, DEFAULT)
WHERE action_id = 'LGIF'
ORDER BY event_time DESC;
""",
        )
        self.show_failed_logins()

    def task_admin_audit(self) -> None:
        sql = f"""
USE master;
IF EXISTS (SELECT 1 FROM sys.server_audit_specifications WHERE name = N'Audit_AdminUsersSpec')
BEGIN
    ALTER SERVER AUDIT SPECIFICATION Audit_AdminUsersSpec WITH (STATE = OFF);
    DROP SERVER AUDIT SPECIFICATION Audit_AdminUsersSpec;
END;

IF EXISTS (SELECT 1 FROM sys.server_audits WHERE name = N'{DEFAULT_ADMIN_AUDIT_NAME}')
BEGIN
    ALTER SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME} WITH (STATE = OFF);
    DROP SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME};
END;

CREATE SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME}
TO FILE
(
    FILEPATH = N'{self.config.audit_path}',
    MAXSIZE = 50 MB,
    MAX_ROLLOVER_FILES = 5,
    RESERVE_DISK_SPACE = OFF
)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);

ALTER SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME} WITH (STATE = ON);

USE {DEFAULT_DATABASE};
IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = N'Audit_AdminActions')
BEGIN
    ALTER DATABASE AUDIT SPECIFICATION Audit_AdminActions WITH (STATE = OFF);
    DROP DATABASE AUDIT SPECIFICATION Audit_AdminActions;
END;

CREATE DATABASE AUDIT SPECIFICATION Audit_AdminActions
FOR SERVER AUDIT {DEFAULT_ADMIN_AUDIT_NAME}
ADD (SELECT ON dbo.Employees BY [dbo]),
ADD (UPDATE ON dbo.Employees BY [dbo]),
ADD (DELETE ON dbo.Employees BY [dbo])
WITH (STATE = ON);

SELECT name, status_desc, audit_file_path
FROM sys.dm_server_audit_status
WHERE name = '{DEFAULT_ADMIN_AUDIT_NAME}';
"""
        self.announce(
            "Задание 7: отдельный аудит для администраторов",
            "Создаст второй SERVER AUDIT и отдельную db-spec только для действий dbo/администратора.",
            sql,
        )
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, "Рисунок 20")

    def task_permission_changes(self) -> None:
        self.create_permission_changes_spec()

    def task_compare_audit_triggers(self) -> None:
        rows = [
            {
                "SQL Server Audit": "На уровне сервера",
                "Триггеры": "На уровне таблицы",
            },
            {
                "SQL Server Audit": "Лог в файле",
                "Триггеры": "Лог в таблице",
            },
            {
                "SQL Server Audit": "Сложнее отключить",
                "Триггеры": "Можно удалить",
            },
            {
                "SQL Server Audit": "Меньше влияет на производительность",
                "Триггеры": "Может замедлять",
            },
            {
                "SQL Server Audit": "Подходит для безопасности",
                "Триггеры": "Подходит для контроля данных",
            },
        ]
        print()
        print(Style.wrap("=" * 78, Style.BLUE))
        print(Style.wrap("Задание 9: сравнение SQL Server Audit и триггеров", Style.BOLD, Style.CYAN))
        print(Style.wrap("Текстовый экран для готового скриншота сравнения.", Style.DIM, Style.WHITE))
        print(Style.wrap("=" * 78, Style.BLUE))
        self.print_table(rows, "Сравнение")

    def task_critical_events(self) -> None:
        rows = [
            {"Критичное событие": "UPDATE таблицы Клиенты", "Почему важно": "Риск подмены персональных данных и финансовых записей"},
            {"Критичное событие": "DELETE таблицы Заказ", "Почему важно": "Потеря истории операций и спорные транзакции"},
            {"Критичное событие": "Изменение суммы оплаты", "Почему важно": "Прямая финансовая манипуляция"},
            {"Критичное событие": "Изменение ИИН клиента", "Почему важно": "Компрометация идентификационных данных"},
            {"Критичное событие": "Удаление данных работников", "Почему важно": "Сокрытие следов и потеря кадровой информации"},
            {"Критичное событие": "Изменение ролей и прав", "Почему важно": "Эскалация привилегий"},
            {"Критичное событие": "Неудачные входы", "Почему важно": "Признак перебора паролей или атаки"},
            {"Критичное событие": "Изменение цен услуг", "Почему важно": "Риск финансового ущерба компании"},
            {"Критичное событие": "Удаление материалов склада", "Почему важно": "Искажение остатков и учета"},
        ]
        print()
        print(Style.wrap("=" * 78, Style.BLUE))
        print(Style.wrap("Задание 10: наиболее критичные события", Style.BOLD, Style.CYAN))
        print(Style.wrap("Готовый экран со списком критичных событий для скриншота.", Style.DIM, Style.WHITE))
        print(Style.wrap("=" * 78, Style.BLUE))
        self.print_table(rows, "Критичные события")

    def get_audit_pattern(self) -> str:
        rows, _ = self.execute(
            f"""
SELECT audit_file_path
FROM sys.dm_server_audit_status
WHERE name = '{self.config.audit_name}';
""",
            database="master",
        )
        if not rows:
            raise RuntimeError("Аудит не найден. Сначала выполните настройку.")
        path = rows[0]["audit_file_path"]
        return re.sub(r"_0_\\d+\\.sqlaudit$", "_*.sqlaudit", path)

    def _show_filtered(self, template: str, title: str) -> None:
        pattern = self.get_audit_pattern()
        sql = template.format(pattern=pattern)
        descriptions = {
            "Удаления": "Покажет только операции DELETE по зааудированным объектам.",
            "События по Salary": "Покажет команды, где в тексте запроса фигурирует поле Salary.",
            "Неуспешные входы": "Покажет только события FAILED_LOGIN_GROUP.",
        }
        self.announce(title, descriptions.get(title, "Выполнит фильтр по журналу аудита."), sql)
        rows, messages = self.execute(sql, database="master")
        self.print_messages(messages)
        self.print_table(rows, title)

    @staticmethod
    def print_messages(messages: list[str]) -> None:
        if not messages:
            return
        print(Style.wrap("\nСообщения SQL Server:", Style.BOLD, Style.YELLOW))
        for message in messages:
            print(Style.wrap(f"- {message}", Style.YELLOW))

    @staticmethod
    def print_table(rows: list[dict], title: str) -> None:
        print(Style.wrap(f"\n=== {title} ===", Style.BOLD, Style.GREEN))
        if not rows:
            print(Style.wrap("Нет строк.", Style.DIM))
            return

        normalized_rows = []
        for row in rows:
            normalized = {}
            for key, value in row.items():
                if isinstance(value, bytes):
                    try:
                        normalized[key] = value.decode().strip()
                    except Exception:
                        normalized[key] = repr(value)
                else:
                    normalized[key] = value
            normalized_rows.append(normalized)

        headers = list(normalized_rows[0].keys())
        widths = {}
        for header in headers:
            widths[header] = len(header)
        for row in normalized_rows:
            for header in headers:
                value = "" if row.get(header) is None else str(row.get(header))
                widths[header] = min(max(widths[header], len(value)), 80)

        def crop(value: str, width: int) -> str:
            if len(value) <= width:
                return value
            return value[: width - 3] + "..."

        header_line = " | ".join(header.ljust(widths[header]) for header in headers)
        sep_line = "-+-".join("-" * widths[header] for header in headers)
        print(Style.wrap(header_line, Style.BOLD, Style.WHITE))
        print(Style.wrap(sep_line, Style.BLUE))
        for row in normalized_rows:
            line = " | ".join(
                crop("" if row.get(header) is None else str(row.get(header)), widths[header]).ljust(widths[header])
                for header in headers
            )
            print(line)


def prompt(text: str, default: str | None = None, secret: bool = False) -> str:
    suffix = f" [{default}]" if default else ""
    message = f"{text}{suffix}: "
    try:
        if secret:
            value = getpass.getpass(message)
        else:
            value = input(message).strip()
    except EOFError:
        return default or ""
    return value or (default or "")


def load_config() -> Config:
    host = os.getenv("MSSQL_HOST", "127.0.0.1")
    port = int(os.getenv("MSSQL_PORT", "1433"))
    user = os.getenv("MSSQL_USER", "sa")
    password = os.getenv("MSSQL_PASSWORD", "")
    database = os.getenv("MSSQL_DATABASE", "master")
    audit_path = os.getenv("MSSQL_AUDIT_PATH", DEFAULT_AUDIT_PATH)
    audit_name = os.getenv("MSSQL_AUDIT_NAME", DEFAULT_AUDIT_NAME)
    demo_user = os.getenv("MSSQL_DEMO_USER", DEFAULT_DEMO_USER)
    demo_password = os.getenv("MSSQL_DEMO_PASSWORD", password)

    print(Style.wrap("SQL Server Audit Lab Console", Style.BOLD, Style.CYAN))
    print(Style.wrap("Параметры подключения. Enter оставляет значение по умолчанию.\n", Style.DIM, Style.WHITE))
    host = prompt("Host", host)
    port = int(prompt("Port", str(port)))
    user = prompt("User", user)
    if not password:
        password = prompt("Password", secret=True)
    else:
        override = prompt("Password override", "", secret=True)
        if override:
            password = override
    database = prompt("Default database", database)
    audit_path = prompt("Audit path", audit_path)
    demo_user = prompt("Demo user for audited actions", demo_user)
    if not demo_password:
        demo_password = prompt("Demo user password", secret=True)
    else:
        override_demo = prompt("Demo user password override", "", secret=True)
        if override_demo:
            demo_password = override_demo

    return Config(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        audit_path=audit_path,
        audit_name=audit_name,
        demo_user=demo_user,
        demo_password=demo_password,
    )


def show_menu() -> None:
    print()
    print(Style.wrap("╔══════════════════════════════════════════════════════════════════════╗", Style.BLUE))
    print(Style.wrap("║                    SQL Server Audit Lab Console                    ║", Style.BOLD, Style.CYAN))
    print(Style.wrap("╠══════════════════════════════════════════════════════════════════════╣", Style.BLUE))
    print(Style.wrap("║  1  Рис.1  Подготовка среды                                        ║", Style.WHITE))
    print(Style.wrap("║  2  Рис.2  Создание SQL Server Audit                               ║", Style.WHITE))
    print(Style.wrap("║  3  Рис.3  Server Audit Specification                              ║", Style.WHITE))
    print(Style.wrap("║  4  Рис.4  Database Audit Specification                            ║", Style.WHITE))
    print(Style.wrap("║  5  Рис.5  Генерация событий                                       ║", Style.WHITE))
    print(Style.wrap("║  6  Рис.6  Отозвать право UNMASK                                   ║", Style.WHITE))
    print(Style.wrap("║  7  Рис.7-10 Поиск подозрительных действий                         ║", Style.WHITE))
    print(Style.wrap("║  8  Рис.11 Аудит изменения прав доступа                            ║", Style.WHITE))
    print(Style.wrap("║  9  Рис.12 Аудит создания и удаления объектов                      ║", Style.WHITE))
    print(Style.wrap("║ 10  Рис.13 Отключение аудита                                       ║", Style.WHITE))
    print(Style.wrap("║ 11  Рис.14 Задание 1: аудит одной таблицы                          ║", Style.WHITE))
    print(Style.wrap("║ 12  Рис.15 Задание 2: аудит конкретного пользователя               ║", Style.WHITE))
    print(Style.wrap("║ 13  Рис.16 Задание 3: только DELETE и UPDATE                       ║", Style.WHITE))
    print(Style.wrap("║ 14  Рис.17 Задание 4: события за 24 часа                           ║", Style.WHITE))
    print(Style.wrap("║ 15  Рис.18 Задание 5: действия с чувствительными данными           ║", Style.WHITE))
    print(Style.wrap("║ 16  Рис.19 Задание 6: неуспешные входы                             ║", Style.WHITE))
    print(Style.wrap("║ 17  Рис.20 Задание 7: отдельный аудит для админов                  ║", Style.WHITE))
    print(Style.wrap("║ 18  Рис.21 Задание 8: аудит ролей и прав                           ║", Style.WHITE))
    print(Style.wrap("║ 19  Задание 9: сравнение Audit и триггеров                         ║", Style.WHITE))
    print(Style.wrap("║ 20  Задание 10: критичные события                                  ║", Style.WHITE))
    print(Style.wrap("║ 21  Показать Employees                                             ║", Style.WHITE))
    print(Style.wrap("║ 22  Последние события аудита                                       ║", Style.WHITE))
    print(Style.wrap("║ 23  Найти действия пользователя                                    ║", Style.WHITE))
    print(Style.wrap("║  0  Выход                                                          ║", Style.WHITE))
    print(Style.wrap("╚══════════════════════════════════════════════════════════════════════╝", Style.BLUE))


def main() -> int:
    try:
        config = load_config()
        app = SqlAuditApp(config)
    except KeyboardInterrupt:
        print(Style.wrap("\nОтменено.", Style.RED))
        return 1

    actions = {
        "1": app.prepare_environment,
        "2": app.create_server_audit_only,
        "3": app.create_server_spec_only,
        "4": app.create_database_spec_only,
        "5": app.generate_demo_events,
        "6": app.revoke_unmask,
        "7": app.suspicious_queries_pack,
        "8": app.create_permission_changes_spec,
        "9": app.create_object_changes_spec,
        "10": app.disable_audit,
        "11": app.task_one_table_only,
        "12": app.task_specific_user,
        "13": app.task_delete_update_only,
        "14": app.task_last_24h,
        "15": app.task_sensitive_field_actions,
        "16": app.task_failed_logins,
        "17": app.task_admin_audit,
        "18": app.task_permission_changes,
        "19": app.task_compare_audit_triggers,
        "20": app.task_critical_events,
        "21": app.show_employees,
        "22": app.show_recent_records,
    }

    while True:
        show_menu()
        try:
            choice = input("\nВыбор: ").strip()
            if choice == "0":
                return 0
            if choice == "23":
                principal_name = input("Имя пользователя: ").strip()
                app.show_user_events(principal_name)
                continue
            action = actions.get(choice)
            if not action:
                print(Style.wrap("Неизвестный пункт меню.\n", Style.RED))
                continue
            action()
            print()
        except KeyboardInterrupt:
            print(Style.wrap("\nОперация прервана.\n", Style.RED))
        except EOFError:
            print(Style.wrap("\nВыход.", Style.DIM))
            return 0
        except Exception as exc:
            print(Style.wrap(f"\nОшибка: {exc}\n", Style.RED))


if __name__ == "__main__":
    sys.exit(main())
