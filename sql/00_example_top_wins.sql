-- Example query: the 10 drivers with the most career race wins.
-- A "win" = finishing 1st, which in this dataset is results.positionOrder = 1.
--
-- Run it with:
--   .\.venv\Scripts\python.exe etl\query.py sql\00_example_top_wins.sql

SELECT
    d.forename || ' ' || d.surname AS driver,
    COUNT(*)                       AS wins
FROM results r
JOIN drivers d ON d.driverId = r.driverId
WHERE r.positionOrder = 1
GROUP BY r.driverId
ORDER BY wins DESC
LIMIT 10;
