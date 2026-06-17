# Data Engineer Technical Challenge

## 1. Problemas detectados

Durante la revisión de la solución original se identificaron los siguientes riesgos:

### CI/CD

* Credencial GCP se encuentra expuesta directamente en el pipiline
* Despliegue solo fue realizado a un unico ambiente
* No se realizaron validaciones antes del despliegue

### Airflow

* Se uso Xcom para transportar grandes volumenes de informacion
* se detectaron consultas Bigquery durante la carga del DAG
* Inserción de registros utilizando procesamiento fila a fila.

### BigQuery

* Se utilizo MERGE sobre una tabla historica particionada con altos vol de datos
* Se detectó un alto costo por lecturas innecesarias
* Falta de estrategia para manejar datos tardíos (Late Arriving Data).

---

## 2. Solución CI/CD

Se implementó una estrategia de despliegue separada para ambientes Dev y Prod.

Principales mejoras:

* Se hizo una validacion de la sintaxis  del DAG antes de un despliegue
* Se usaron variables protegidas para las credenciales de GCP
* Se separaron los buckets por ambiente
* Se hizo un despliegue manual para Produccion

---

## 3. Solución Airflow

El DAG fue rediseñado para que Airflow actúe únicamente como orquestador.

Mejoras implementadas:

* Se elimina XCom para las cargas masivas
* Se eliminan las consultas ejecutadas durante la carga DAG
* Se usaron macros nativas de Airflow mediante `{{ ds }}`.
* Se hizo un flujo idemponente en base a las fechas de ejecucion

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
