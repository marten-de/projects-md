-- This table holds all company related details.
CREATE TABLE "companies" (
    "id" INTEGER,
    "name" TEXT NOT NULL,
    "website" TEXT,
    "hq_country" TEXT NOT NULL,
    "industry" TEXT NOT NULL,
    "employee_count" INTEGER,
    "revenue" TEXT,
    "comment" TEXT,
    PRIMARY KEY("id")
);

-- This table holds details about all contact persons.
CREATE TABLE "contact_persons" (
    "id" INTEGER,
    "company_id" INTEGER,
    "family_name" TEXT NOT NULL,
    "given_name" TEXT,
    "title" TEXT NOT NULL,
    "job_title" TEXT,
    "linkedin" TEXT,
    "comment" TEXT,
    PRIMARY KEY("id")
    FOREIGN KEY("company_id") REFERENCES "companies"("id")
);

-- This table holds all vacanciy related details.
CREATE TABLE "vacancies" (
    "id" INTEGER,
    "company_id" INTEGER,
    "contact_person_id" INTEGER,
    "job_title" TEXT NOT NULL,
    "application_deadline" TEXT,
    "location" TEXT NOT NULL,
    "salary" TEXT,
    "conditions" TEXT,
    "comment" TEXT,
    PRIMARY KEY("id")
    FOREIGN KEY("company_id") REFERENCES "companies"("id"),
    FOREIGN KEY("contact_person_id") REFERENCES "contact_persons"("id")
);

-- This table holds all interactions between the applicant and any company.
CREATE TABLE "interactions" (
    "id" INTEGER,
    "company_id" INTEGER,
    "contact_person_id" INTEGER,
    "vacancy_id" INTEGER,
    "prev_interaction_id" INTEGER,
    "date" TEXT NOT NULL,
    "open" BOOLEAN NOT NULL,
    "comment" TEXT,
    PRIMARY KEY("id")
    FOREIGN KEY("company_id") REFERENCES "companies"("id"),
    FOREIGN KEY("contact_person_id") REFERENCES "contact_persons"("id"),
    FOREIGN KEY("vacancy_id") REFERENCES "vacancies"("id"),
    FOREIGN KEY("prev_interaction_id") REFERENCES "interactions"("id")
);


-- These indexes are created with common searches (see queries.sql) in mind.
CREATE INDEX "company_name_index" ON "companies" ("name");
CREATE INDEX "contact_person_name_index" ON "contact_persons" ("family_name", "given_name");
CREATE INDEX "job_title_index" ON "vacancies" ("job_title");


-- These views make the common searches much shorter.
CREATE VIEW "interactions_view" AS
SELECT "interactions"."id", "companies"."name","contact_persons"."title", "contact_persons"."family_name", "contact_persons"."given_name", "vacancies"."job_title", "prev_interaction_id", "date", "interactions"."open", "interactions"."comment"
FROM "interactions"
JOIN "companies"
ON "companies"."id" = "interactions"."company_id"
JOIN "contact_persons"
ON "contact_persons"."id" = "interactions"."contact_person_id"
JOIN "vacancies"
ON "vacancies"."id" = "interactions"."vacancy_id";

CREATE VIEW "vacancies_view" AS
SELECT "vacancies"."id", "companies"."name","contact_persons"."title", "contact_persons"."family_name", "contact_persons"."given_name", "vacancies"."job_title", "application_deadline", "location", "salary", "conditions", "vacancies"."comment"
FROM "vacancies"
JOIN "companies"
ON "companies"."id" = "vacancies"."company_id"
JOIN "contact_persons"
ON "contact_persons"."id" = "vacancies"."contact_person_id";