CREATE OR REPLACE PROCEDURE `mi_proyecto.staging.sp_transform_ventas`(
    fecha_proceso DATE
)
BEGIN

DECLARE fecha_min DATE;
DECLARE fecha_max DATE;

SET fecha_min = (
    SELECT MIN(PARSE_DATE('%Y-%m-%d', fecha))
    FROM `mi_proyecto.staging.ventas_raw`
);

SET fecha_max = (
    SELECT MAX(PARSE_DATE('%Y-%m-%d', fecha))
    FROM `mi_proyecto.staging.ventas_raw`
);

MERGE `mi_proyecto.data_warehouse.reporte_ventas_consumo` T
USING (

    SELECT
        id_venta,
        monto * 1.19 AS monto_con_impuesto,
        PARSE_DATE('%Y-%m-%d', fecha) AS fecha_vta
    FROM `mi_proyecto.staging.ventas_raw`

) S
ON T.id_venta = S.id_venta
AND T.fecha BETWEEN fecha_min AND fecha_max

WHEN MATCHED THEN
UPDATE SET
    T.monto_con_impuesto = S.monto_con_impuesto

WHEN NOT MATCHED THEN
INSERT (
    id_venta,
    monto_con_impuesto,
    fecha
)
VALUES (
    S.id_venta,
    S.monto_con_impuesto,
    S.fecha_vta
);

TRUNCATE TABLE `mi_proyecto.staging.ventas_raw`;

END;