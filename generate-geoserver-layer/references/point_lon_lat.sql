SELECT
    a.id AS gid,
    a.name,
    ST_SetSRID(ST_MakePoint(a.longitude, a.latitude), 4326) AS geom
FROM app_monitor_site a
WHERE 1 = 1
  AND a.longitude IS NOT NULL
  AND a.latitude IS NOT NULL
  AND ('%city%' = '' OR a.city = '%city%')
  AND ('%name%' = '' OR a.name LIKE concat('%%', '%name%', '%%'));
