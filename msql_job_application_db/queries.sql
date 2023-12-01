-- Adding new entries:

-- Add a new company
INSERT INTO "companies" ("name", "website", "hq_country", "industry", "employee_count", "revenue", "comment")
VALUES ('Company ABC', 'https://company-abc.com', 'USA', 'Consumer goods manufacturing', '500', '30 mio USD per year', 'interesting products, hidden champion');

-- Add a new contact person
INSERT INTO "contact_persons" ("company_id", "family_name", "given_name", "title", "job_title", "linkedin", "comment")
VALUES (1, 'Smith', 'John', 'Mr.', 'HR recruiter', 'https://www.linkedin.com/in/john-smith/', 'met at job fare XY in Taipei on 2023-07-13, plays golf');

-- Add a new vacancy
INSERT INTO "vacancies" ("company_id", "contact_person_id", "job_title", "application_deadline", "location", "salary", "conditions", "comment")
VALUES (1, 1, 'Senior software engineer', '2023-12-31', 'Taipei, Taiwan', '85.000 NTD per month gross', '40h, 15 days annual leave, no remote work possible', 'interesting, but maybe my experience is not enough');

-- Add a new interaction
INSERT INTO "interactions" ("company_id", "contact_person_id", "vacancy_id", "prev_interaction_id", "date", "open", "comment")
VALUES (1, 1, 1, NULL, '2023-11-14', 1, 'applied for this job despite low experience');


-- Searching and finding existing entries:

-- Find all open interactions
SELECT *
FROM "interactions_view"
WHERE "open" = 1;

-- Find all interactions related to a specific company
SELECT *
FROM "interactions_view"
WHERE "name" LIKE '%abc%';

-- Find all interactions related to a specific contact person
SELECT *
FROM "interactions_view"
WHERE "family_name" LIKE '%smith%'
AND "given_name" LIKE '%john%';

-- Find all interactions related to a specific vacancy
SELECT *
FROM "vacancies_view"
WHERE "job_title" LIKE '%software engineer%';

-- Find all vacancies at a specific company
SELECT *
FROM "vacancies_view"
WHERE "name" LIKE '%abc%';

-- Find all vacancies witha specific location
SELECT *
FROM "vacancies_view"
WHERE "location" LIKE '%taipei%';

-- Find all companies with a specific origin (hq_location)
SELECT *
FROM "companies"
WHERE "hq_country" LIKE '%usa%';


-- Updating existing entries:

-- Marking specific interactions as closed
UPDATE "interactions"
SET "open" = 0
WHERE "id" = 1;

-- Updating comment of a specific vacancy
UPDATE "vacancies"
SET "comment" = 'negotiated a better deal! now 20 vacation days'
WHERE "id" = 1;