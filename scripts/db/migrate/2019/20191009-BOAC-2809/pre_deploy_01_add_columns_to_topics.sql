BEGIN;

ALTER TABLE topics ADD COLUMN available_in_notes BOOLEAN;
ALTER TABLE topics ADD COLUMN available_in_appointments BOOLEAN;

UPDATE topics
SET available_in_notes = TRUE, available_in_appointments = FALSE;

ALTER TABLE ONLY topics ALTER COLUMN available_in_notes SET NOT NULL;
ALTER TABLE ONLY topics ALTER COLUMN available_in_appointments SET NOT NULL;

UPDATE topics
SET available_in_appointments = TRUE
WHERE topic in ('Advising Holds', 'Internship', 'Change of College', 'Concurrent Enrollment', 'Course Add', 'Course Drop', 'Double Major', 'Degree Check', 'Excess Units', 'Other', 'Probation', 'Readmission', 'Retroactive Add', 'Retroactive Drop', 'Retroactive Unit Change', 'Retroactive Withdrawal', 'Withdrawal', 'Other');

INSERT INTO topics (topic, created_at, available_in_notes, available_in_appointments) VALUES
  ('Appeal Procedures', now(), FALSE, TRUE),
  ('Career Planning', now(), FALSE, TRUE),
  ('Crisis Advising', now(), FALSE, TRUE),
  ('Graduate Advising', now(), FALSE, TRUE),
  ('Student/Faculty mediation', now(), FALSE, TRUE);

COMMIT;
