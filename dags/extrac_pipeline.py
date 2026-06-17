from datetime import datetime

from airflow import DAG
from airflow.providers.google.cloud.operators.bigquery import BigQueryInsertJobOperator


PROJECT_ID = "mi_proyecto"
STAGING_TABLE = f"{PROJECT_ID}.staging.ventas_raw"
CUARENTENA_TABLE = f"{PROJECT_ID}.staging.ventas_cuarentena"
SP_NAME = f"{PROJECT_ID}.staging.sp_transform_ventas"


default_args = {
    "start_date": datetime(2026, 1, 1),
    "retries": 1,
}


with DAG(
    dag_id="pipeline_ventas_consumo",
    default_args=default_args,
    schedule_interval="@daily",
    catchup=False,
    tags=["ventas", "bigquery", "composer"],
) as dag:

    cargar_staging = BigQueryInsertJobOperator(
        task_id="cargar_staging",
        configuration={
            "query": {
                "query": """
                    -- En un caso real esta carga vendría desde la BD origen
                    -- hacia BigQuery usando extracción por ventana diaria.
                    INSERT INTO `mi_proyecto.staging.ventas_raw`
                    SELECT
                        id_venta,
                        monto,
                        fecha
                    FROM `mi_proyecto.staging.ventas_raw_tmp`
                    WHERE DATE(PARSE_DATE('%Y-%m-%d', fecha)) = DATE('{{ ds }}')
                """,
                "useLegacySql": False,
            }
        },
    )

    mover_registros_malos = BigQueryInsertJobOperator(
        task_id="mover_registros_malos",
        configuration={
            "query": {
                "query": """
                    INSERT INTO `mi_proyecto.staging.ventas_cuarentena`
                    SELECT
                        *,
                        CURRENT_TIMESTAMP() AS fecha_auditoria,
                        '{{ ds }}' AS fecha_proceso
                    FROM `mi_proyecto.staging.ventas_raw`
                    WHERE DATE(PARSE_DATE('%Y-%m-%d', fecha)) = DATE('{{ ds }}')
                      AND (
                        id_venta IS NULL
                        OR monto < 0
                      )
                """,
                "useLegacySql": False,
            }
        },
    )

    validar_calidad = BigQueryInsertJobOperator(
        task_id="validar_calidad",
        configuration={
            "query": {
                "query": """
                    SELECT
                      CASE
                        WHEN COUNT(1) > 0 THEN
                          ERROR('Existen registros invalidos en staging')
                        ELSE
                          'OK'
                      END AS resultado
                    FROM `mi_proyecto.staging.ventas_raw`
                    WHERE DATE(PARSE_DATE('%Y-%m-%d', fecha)) = DATE('{{ ds }}')
                      AND (
                        id_venta IS NULL
                        OR monto < 0
                      )
                """,
                "useLegacySql": False,
            }
        },
    )

    ejecutar_sp = BigQueryInsertJobOperator(
        task_id="ejecutar_sp",
        configuration={
            "query": {
                "query": """
                    CALL `mi_proyecto.staging.sp_transform_ventas`(
                        DATE('{{ ds }}')
                    );
                """,
                "useLegacySql": False,
            }
        },
    )

    cargar_staging >> mover_registros_malos >> validar_calidad >> ejecutar_sp