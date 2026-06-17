# Data Engineer Technical Challenge

## 1. Problemas detectados

Durante la revisión de la solución original se identificaron los siguientes riesgos:

### CI/CD

* Credencial GCP expuesta directamente en el pipeline.
* Despliegue a un único ambiente.
* Ausencia de validaciones previas antes del despliegue.

### Airflow

* Uso de XCom para transportar grandes volúmenes de información.
* Ejecución de consultas BigQuery durante la carga del DAG (Top-Level Code).
* Inserción de registros utilizando procesamiento fila a fila.

### BigQuery

* MERGE ejecutado sobre una tabla histórica particionada con alto volumen de datos.
* Riesgo de incremento significativo en costos por lecturas innecesarias.
* Falta de estrategia para manejar datos tardíos (Late Arriving Data).

---

## 2. Solución CI/CD

Se implementó una estrategia de despliegue separada para ambientes Dev y Prod.

Principales mejoras:

* Validación de sintaxis del DAG antes de cualquier despliegue.
* Uso de variables protegidas para las credenciales GCP.
* Separación de buckets por ambiente.
* Despliegue manual para Producción.

---

## 3. Solución Airflow

El DAG fue rediseñado para que Airflow actúe únicamente como orquestador.

Mejoras implementadas:

* Eliminación de XCom para cargas masivas.
* Eliminación de consultas ejecutadas durante la carga del DAG.
* Uso de macros nativas de Airflow mediante `{{ ds }}`.
* Flujo idempotente basado en fecha de ejecución.

---

## 4. Optimización BigQuery

La principal optimización fue reducir el alcance del MERGE.

Se calcula dinámicamente la fecha mínima y máxima presente en staging y posteriormente se limita el procesamiento únicamente a las particiones afectadas.

Beneficios:

* Menor volumen de lectura.
* Menor costo computacional.
* Mejor rendimiento de ejecución.

---

## 5. Manejo de Late Arriving Data

La solución considera registros que pueden llegar varios días después de su fecha real de ocurrencia.

El procedimiento obtiene automáticamente el rango de fechas presente en staging y actualiza únicamente las particiones involucradas.

De esta forma, si llegan registros con fechas de días anteriores, estos son incorporados sin necesidad de reprocesar la totalidad del histórico.

---

## 6. Data Quality Gate

Se incorporó una validación previa a la ejecución del Stored Procedure.

Reglas implementadas:

* id_venta no puede ser nulo.
* monto no puede ser negativo.

Si se detectan registros inválidos:

* Los registros son enviados a la tabla `staging.ventas_cuarentena`.
* El proceso se detiene inmediatamente.
* El Stored Procedure no es ejecutado.

Esto evita contaminar la capa final con información incorrecta.

---

## 7. Evolución del Esquema

Para absorber cambios provenientes de los sistemas origen se recomienda:

* Mantener una capa Staging desacoplada de la capa analítica.
* Incorporar validaciones automáticas de esquema.
* Utilizar versionamiento de estructuras.
* Permitir la incorporación de nuevas columnas sin afectar procesos existentes.

Ante cambios de tipo de dato, se recomienda realizar conversiones controladas dentro de la capa de transformación antes de llegar al modelo final.

---

## 8. Gobierno de Datos (PII)

Para proteger información sensible como email o teléfono se propone utilizar capacidades nativas de GCP:

* IAM para control de acceso.
* Policy Tags de BigQuery.
* Column Level Security.
* Data Catalog para clasificación de información sensible.

Con este enfoque, analistas junior pueden visualizar únicamente información anonimizada mientras perfiles gerenciales mantienen acceso a los datos completos según sus permisos.

---

## 9. Mejoras Futuras

* Incorporar monitoreo y alertamiento.
* Implementar pruebas automáticas de calidad de datos.
* Incorporar observabilidad de costos en BigQuery.
* Integrar métricas operacionales del pipeline.
