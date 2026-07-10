SELECT
    a.id AS gid,
    a.name,
    ST_SetSRID(ST_GeomFromGeoJSON(a.boundary_geojson), 4326) AS geom
FROM app_scene_manage_scene a
WHERE 1 = 1
  AND a.boundary_geojson IS NOT NULL
  AND a.boundary_geojson <> ''
  AND ('%city%' = '' OR a.city = '%city%')
  AND ('%area%' = '' OR a.area = '%area%')
  AND ('%name%' = '' OR a.name LIKE concat('%%', '%name%', '%%'));
