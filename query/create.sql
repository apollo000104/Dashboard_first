CREATE TABLE IF NOT EXISTS "TO" (
    "ID" VARCHAR(255) PRIMARY KEY,
    "Заявка ТО" VARCHAR(255),
    Клієнт VARCHAR(255),
    "Держ. номер" VARCHAR(10),
    Авто VARCHAR(255),
    "Дата відкриття" TIMESTAMP,
    "Дата закриття" TIMESTAMP,
    "Проведення ЗН" TIMESTAMP,
    "Дата початку робіт" TIMESTAMP,
    "Дата закінчення робіт" TIMESTAMP,
    Нормогодини FLOAT,
    Категорія VARCHAR(255),
    Менеджер VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS "CTO" (
    "ID" VARCHAR(255) PRIMARY KEY,
    "Заявка ТО" VARCHAR(255),
    "Створення запис на СТО" TIMESTAMP,
    "Плановий заїзд" TIMESTAMP,
    "Планове закінчення" TIMESTAMP
);

CREATE TABLE IF NOT EXISTS phones (
    "Enterprise" VARCHAR(255),
    "EnterpriseCode" VARCHAR(255),
    "user" VARCHAR(255),
    "reportDate" TIMESTAMP,
    "callDate" TIMESTAMP,
    "client" VARCHAR(255),
    "phone" VARCHAR(20),
    "employee" VARCHAR(255),
    "status" VARCHAR(255),
    "phoneRecived" VARCHAR(255),
    "phoneManager" VARCHAR(255),
    "note" TEXT,
    "phoneEnterprise" VARCHAR(255),
    "department" VARCHAR(255),
    "group" VARCHAR(255),
    "advertisingSource" VARCHAR(255),
    "record" VARCHAR(255),
    "callType" VARCHAR(255),
    "callTime" VARCHAR(20),
    "tellTime" VARCHAR(20)
);


CREATE TABLE IF NOT EXISTS traffic (
    "Период" TIMESTAMP,
    "ГосударственныйНомер" VARCHAR(255),
    "ДатаНачала" TIMESTAMP,
    "ДатаОкончания" TIMESTAMP,
    "Документ" VARCHAR(255),
    "Клиент" VARCHAR(255),
    "Авто" VARCHAR(255),
    "Направление" VARCHAR(255),
    "ИдентификаторЗаезда" VARCHAR(255),
    "ИдентификаторКамеры" VARCHAR(255),
    "ИдентификаторЗоны1" VARCHAR(255),
    "ИдентификаторЗоны2" VARCHAR(255),
    "ДатаЗакрытия" TIMESTAMP,
    "Количество" INTEGER,
    "КоличествоФакт" INTEGER,
    "Примечание" VARCHAR(255)
);

-- CREATE TABLE IF NOT EXISTS detailed (
--     "ПІБ" VARCHAR(255),
--     "Телефон" VARCHAR(255),
--     "Держ. номер" VARCHAR(10),
--     "Марка і модель" VARCHAR(255),
--     "Вхідний дзвінок" TIMESTAMP,
--     "Втрачений дзвінок" TIMESTAMP,
--     "Створення запис на СТО" TIMESTAMP,
--     "Створення ЗН" TIMESTAMP,
--     "Плановий заїзд" TIMESTAMP,
--     "Заїзд на парковку" TIMESTAMP,
--     "Заїзд в зону сервісу" TIMESTAMP,
--     "Виїзд з зони сервісу" TIMESTAMP,
--     "Закриття ЗН" TIMESTAMP,
--     "Виїзд з території" TIMESTAMP,
--     "Проведення ЗН" TIMESTAMP,
--     "Кінець роботи" TIMESTAMP,
--     "Початок роботи" TIMESTAMP,
--     "Кількість закритих нормогодин в ЗН" FLOAT
-- );

CREATE TABLE IF NOT EXISTS stages(
  "ПІБ" VARCHAR(255),
  "Телефон" VARCHAR(255),
  "Держ. номер" VARCHAR(255),
  "Марка і модель" VARCHAR(255),
  "Вхідний дзвінок" TIMESTAMP,
  "Втрачений дзвінок" TIMESTAMP,
  "Створення запис на СТО" TIMESTAMP,
  "Створення ЗН" TIMESTAMP,
  "Плановий заїзд" TIMESTAMP,
  "Проведення ЗН" TIMESTAMP,
  "Дата початку робіт" TIMESTAMP,
  "Заїзд на парковку" TIMESTAMP,
  "Заїзд в зону сервісу" TIMESTAMP,
  "Виїзд з зони сервісу" TIMESTAMP,
  "Дата закінчення робіт" TIMESTAMP,
  "Планове закінчення" TIMESTAMP,
  "Закриття ЗН" TIMESTAMP,
  "Виїзд з території" TIMESTAMP,
  "Нормогодини" FLOAT,
  "Категорія" VARCHAR(255),
  "Менеджер" VARCHAR(255),
  "Заявка ТО" VARCHAR(255),
  "Запис" BOOLEAN
);

