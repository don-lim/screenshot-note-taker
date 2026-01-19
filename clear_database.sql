-- Clear all data from database tables
\c image_search_db;

-- Truncate all tables (CASCADE handles foreign key dependencies)
TRUNCATE TABLE text_embedding CASCADE;
TRUNCATE TABLE ocr_results CASCADE;
TRUNCATE TABLE images CASCADE;

-- Verify tables are empty
SELECT 'images' as table_name, COUNT(*) as record_count FROM images
UNION ALL
SELECT 'ocr_results', COUNT(*) FROM ocr_results
UNION ALL
SELECT 'text_embedding', COUNT(*) FROM text_embedding;
