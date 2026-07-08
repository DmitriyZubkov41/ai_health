CREATE TABLE lab_analiz (
    "Дата" DATE,
    "Лаборатория" VARCHAR(50),
    "Витамин D" NUMERIC(5,2),
    "Витамин B-12" NUMERIC(5,2),
    "Белок C-реактивный" NUMERIC(5,2),
    "Ревматоидный фактор" NUMERIC(5,2),
    "Группа крови" VARCHAR(20),
    "Резус принадлежности" VARCHAR(20),
    "Аланинаминотрансфераза (АлАТ)" NUMERIC(5,2),
    "Аспартатаминотрансфераза (ФсАт)" NUMERIC(5,2),
    "Фосфатаза щелочная" NUMERIC(5,2),
    "Лактатдегидрогеназа (ЛДГ)" NUMERIC(5,2),
    "Амилаза" NUMERIC(5,2),
    "Липаза" NUMERIC(5,2),
    "Гамма-глутамилтрансфераза (ГГТ)" NUMERIC(5,2),
    "Альфафетопротеин (АФП)" NUMERIC(5,2),
    "ПСА общий" NUMERIC(5,2),
    "ПСА свободный" NUMERIC(5,2),
    "Пролактин" NUMERIC(5,2),
    "Исследование Янус-киназы Jak2" VARCHAR(50),
    "Холестерин общий" NUMERIC(5,2),
    "Гомоцистеин" NUMERIC(5,2),
    "Фолиевая кислота" NUMERIC(5,2),
    "Исследование кала на гельминты" VARCHAR(300),
    "Кальпротектин" NUMERIC(5,2),
    "Копрограмма" TEXT
);

DROP TABLE IF EXISTS metrics;

CREATE TABLE metrics (
    Дата Date,
    Время Time,
    "Верхнее давление" numeric(10,1),
    "Нижнее давление" numeric(10,1),
    Пульс numeric(10,1),
    Сахар numeric(10,1),
    Температура numeric(10,1),
    Вес numeric(10,1),  -- если есть
    Примечание VARCHAR(300)
);

ALTER TABLE lab_analiz 
RENAME COLUMN "Аланинаминотрансфераза (АлАТ)" TO "Аланинаминотрансфераза_(АлАТ)";

CREATE TABLE lab_oak (
    data DATE,
    laboratoria VARCHAR(50),
    leykotsity NUMERIC(5,2),
    neytrofily_abs NUMERIC(5,2),
    neytrofily_procent NUMERIC(5,2),
    neytrofily_palochkoyad_procent NUMERIC(5,2),
    neytrofily_segmentoyad NUMERIC(5,2),
    neytrofily_segmentoyad_procent NUMERIC(5,2),
    limfotsity_procent NUMERIC(5,2),
    monotsity_procent NUMERIC(5,2),
    monotsity_abs NUMERIC(5,2),
    eozinofily_procent NUMERIC(5,2),
    eozinofily_abs NUMERIC(5,2),
    bazofily_procent NUMERIC(5,2),
    bazofily_abs NUMERIC(5,2),
    eritrotsity NUMERIC(5,2),
    gipohromnye_eritrotsity NUMERIC(5,2),
    gemoglobin NUMERIC(5,2),
    gematokrit NUMERIC(5,2),
    gematokrit_procent NUMERIC(5,2),
    sredniy_obem_eritrotsitov NUMERIC(5,2),
    mch NUMERIC(5,2),
    mchc NUMERIC(5,2),
    rdw_cw NUMERIC(5,2),
    rdw_sd NUMERIC(5,2),
    normotsity_abs VARCHAR(50),
    trombotsitokrit_procent NUMERIC(5,2),
    trombotsity NUMERIC(5,2),
    mpv NUMERIC(5,2),
    shirina_raspredeleniya_trombotsitov NUMERIC(5,2),
    shirina_raspr_trombotsitov_procent NUMERIC(5,2),
    pdw NUMERIC(5,2),
    soe_panchenkov NUMERIC(5,2),
    procent_krupnyh_trombotsitov NUMERIC(5,2),
    normoblasty NUMERIC(5,2),
    normoblasty_procent NUMERIC(5,2)
);

CREATE TABLE chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,      -- Идентификатор сессии (пользователя)
    role VARCHAR(20) NOT NULL,             -- 'user', 'assistant', 'system', 'function'
    content TEXT,                          -- Текст сообщения
    function_call JSONB,                   -- Данные о вызове функции (если есть)
    function_name VARCHAR(50),             -- Имя вызванной функции
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);