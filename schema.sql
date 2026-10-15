-- Student intake schema.
-- netid is stored normalized: lowercased, with a trailing @nyu.edu removed.
-- school year and intro-programming background are lookup tables (one-to-many).
-- tools and availability are many-to-many, split out of semicolon-separated cells.
-- interests stays free text on students.

CREATE TABLE school_years (
    school_year_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label          text NOT NULL UNIQUE
);

CREATE TABLE intro_programming (
    intro_programming_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code                 text NOT NULL UNIQUE
);

CREATE TABLE tools (
    tool_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name    text NOT NULL UNIQUE
);

CREATE TABLE availability_slots (
    slot_id integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    label   text NOT NULL UNIQUE
);

CREATE TABLE students (
    student_id            integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    netid                 text NOT NULL UNIQUE,
    name                  text NOT NULL,
    school_year_id        integer NOT NULL REFERENCES school_years (school_year_id),
    intro_programming_id  integer NOT NULL REFERENCES intro_programming (intro_programming_id),
    skill_programming     smallint NOT NULL CHECK (skill_programming BETWEEN 1 AND 5),
    skill_data_stats      smallint NOT NULL CHECK (skill_data_stats BETWEEN 1 AND 5),
    skill_frontend_design smallint NOT NULL CHECK (skill_frontend_design BETWEEN 1 AND 5),
    skill_business_pitch  smallint NOT NULL CHECK (skill_business_pitch BETWEEN 1 AND 5),
    working_style         text NOT NULL,
    interests             text NOT NULL,
    semester_goal         text NOT NULL,
    submitted_at          timestamptz NOT NULL
);

CREATE TABLE student_tools (
    student_id integer NOT NULL REFERENCES students (student_id),
    tool_id    integer NOT NULL REFERENCES tools (tool_id),
    PRIMARY KEY (student_id, tool_id)
);

CREATE TABLE student_availability (
    student_id integer NOT NULL REFERENCES students (student_id),
    slot_id    integer NOT NULL REFERENCES availability_slots (slot_id),
    PRIMARY KEY (student_id, slot_id)
);
