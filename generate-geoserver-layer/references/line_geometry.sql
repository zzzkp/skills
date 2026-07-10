SELECT
    a.id AS gid,
    a.name,
    ST_Transform(a.road_geom, 4326) AS geom
FROM app_road_segment a
WHERE 1 = 1
  AND a.road_geom IS NOT NULL
  AND ('%city%' = '' OR a.city = '%city%')
  AND ('%name%' = '' OR a.name LIKE concat('%%', '%name%', '%%'));
