SELECT 
    d.driverId,
    d.forename || ' '|| d.surname AS driver_name,
    COUNT(*) AS entries,
    SUM(CASE WHEN r.positionOrder = 1 THEN 1 ELSE 0 END) AS wins,
    ROUND(SUM(CASE WHEN r.positionOrder = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS win_rate
FROM 
    drivers d 
    JOIN results r on d.driverId = r.driverId
GROUP BY 
    d.driverId, d.forename, d.surname
HAVING 
    COUNT(*) >= 50
ORDER BY
    win_rate DESC
LIMIT 10;
