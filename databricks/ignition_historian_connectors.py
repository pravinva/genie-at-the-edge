"""
Different Ways to Connect to Ignition Historian from Databricks
Comparison of JDBC vs SQL Connectors vs Native Options
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *
import dlt

# ==============================================================================
# OPTION 1: JDBC (Traditional - What We've Been Using)
# ==============================================================================

def connect_via_jdbc():
    """
    Traditional JDBC connection
    Pros: Universal, works with any database
    Cons: Single connection bottleneck, no pushdown optimization
    """

    historian_df = spark.read \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://ignition-db:5432/historian") \
        .option("user", "ignition_user") \
        .option("password", "your_password") \
        .option("dbtable", "sqlt_data_1_2024_01") \
        .option("numPartitions", 4) \
        .option("fetchsize", 10000) \
        .load()

    return historian_df

# ==============================================================================
# OPTION 2: PostgreSQL Native Connector (Recommended for Ignition)
# ==============================================================================

def connect_via_postgresql_connector():
    """
    Native PostgreSQL connector with better performance
    Pros: Optimized for PostgreSQL, better parallelism, predicate pushdown
    Cons: PostgreSQL specific
    """

    # First, install in cluster: postgresql-42.2.18.jar

    historian_df = spark.read \
        .format("postgresql") \
        .option("host", "ignition-db") \
        .option("port", "5432") \
        .option("database", "historian") \
        .option("user", "ignition_user") \
        .option("password", spark.conf.get("spark.postgres.password")) \
        .option("query", """
            SELECT
                tagpath,
                t_stamp,
                floatvalue,
                AVG(floatvalue) OVER (
                    PARTITION BY tagpath
                    ORDER BY t_stamp
                    ROWS BETWEEN 10080 PRECEDING AND CURRENT ROW
                ) as baseline_7d
            FROM sqlt_data_1_2024_01
            WHERE t_stamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
              AND tagpath IN ('HAUL-001/temperature', 'HAUL-001/vibration')
        """) \
        .option("partitionColumn", "t_stamp") \
        .option("lowerBound", "2024-01-01") \
        .option("upperBound", "2024-02-26") \
        .option("numPartitions", 10) \
        .load()

    return historian_df

# ==============================================================================
# OPTION 3: Databricks SQL Connector (Federated Query)
# ==============================================================================

def connect_via_databricks_sql_federation():
    """
    Use Databricks SQL to create federated connection
    Pros: Managed by Databricks, automatic optimization, caching
    Cons: Requires Unity Catalog
    """

    # First, create connection in Unity Catalog
    spark.sql("""
        CREATE CONNECTION IF NOT EXISTS ignition_historian
        TYPE postgresql
        OPTIONS (
            host 'ignition-db',
            port '5432',
            user 'ignition_user',
            password SECRET('ignition_password', 'password_scope')
        )
    """)

    # Create foreign catalog
    spark.sql("""
        CREATE FOREIGN CATALOG IF NOT EXISTS ignition_catalog
        USING CONNECTION ignition_historian
        OPTIONS (database 'historian')
    """)

    # Now query directly with SQL!
    historian_df = spark.sql("""
        SELECT
            tagpath,
            t_stamp,
            floatvalue,
            -- Databricks SQL handles window functions!
            AVG(floatvalue) OVER (
                PARTITION BY tagpath
                ORDER BY t_stamp
                RANGE BETWEEN INTERVAL 7 DAYS PRECEDING AND CURRENT ROW
            ) as baseline_7d,
            -- Even complex analytics
            PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY floatvalue)
                OVER (PARTITION BY tagpath) as p95_value
        FROM ignition_catalog.historian.sqlt_data_1_2024_01
        WHERE t_stamp > CURRENT_TIMESTAMP - INTERVAL '30 days'
    """)

    return historian_df

# ==============================================================================
# OPTION 4: Delta Live Tables with SQL Sources
# ==============================================================================

@dlt.table(
    name="historian_baselines_live",
    comment="Live connection to Ignition historian using SQL"
)
def historian_baselines_sql():
    """
    DLT can directly read from external SQL databases
    Pros: Automatic incremental processing, built-in CDC support
    Cons: Requires DLT pipeline
    """

    # Method A: Direct SQL query
    return spark.sql("""
        SELECT * FROM postgresql.`ignition-db:5432`.historian.sqlt_data_1_2024_01
        WHERE t_stamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
    """)

@dlt.table(name="historian_incremental")
@dlt.incremental(
    source="postgresql.`ignition-db:5432`.historian.sqlt_data_1_2024_01",
    keys=["tagpath", "t_stamp"],
    sequence_by="t_stamp"
)
def historian_incremental():
    """
    Incremental loading from Ignition historian
    Only processes new data since last run
    """
    return dlt.read("postgresql.`ignition-db:5432`.historian.sqlt_data_1_2024_01")

# ==============================================================================
# OPTION 5: Lakehouse Federation (Best for Production)
# ==============================================================================

def setup_lakehouse_federation():
    """
    Best practice: Create external tables pointing to Ignition
    Pros: Best performance, supports streaming, automatic stats
    """

    # Create external table
    spark.sql("""
        CREATE TABLE IF NOT EXISTS ignition_historian_external
        USING org.apache.spark.sql.jdbc
        OPTIONS (
            url 'jdbc:postgresql://ignition-db:5432/historian',
            dbtable 'sqlt_data_1_2024_01',
            user 'ignition_user',
            password SECRET('ignition_password', 'password_scope'),
            -- Performance optimizations
            numPartitions '10',
            partitionColumn 't_stamp',
            lowerBound '2024-01-01',
            upperBound '2024-12-31',
            fetchSize '10000',
            batchsize '10000',
            isolationLevel 'READ_UNCOMMITTED',
            pushDownPredicate 'true',
            pushDownAggregate 'true'
        )
    """)

    # Create materialized view for common queries
    spark.sql("""
        CREATE MATERIALIZED VIEW IF NOT EXISTS historian_baselines
        PARTITIONED BY (date)
        AS
        SELECT
            DATE(t_stamp) as date,
            tagpath as equipment_sensor,
            AVG(floatvalue) as daily_avg,
            MIN(floatvalue) as daily_min,
            MAX(floatvalue) as daily_max,
            STDDEV(floatvalue) as daily_stddev,
            PERCENTILE_CONT(0.05) as p5,
            PERCENTILE_CONT(0.95) as p95,
            COUNT(*) as reading_count
        FROM ignition_historian_external
        WHERE t_stamp > CURRENT_DATE - 90
        GROUP BY DATE(t_stamp), tagpath
    """)

    # Refresh materialized view (schedule this)
    spark.sql("REFRESH MATERIALIZED VIEW historian_baselines")

# ==============================================================================
# OPTION 6: Python Database Connectors (For Simple Cases)
# ==============================================================================

def connect_via_python_psycopg2():
    """
    Direct Python connection for small data or metadata queries
    Pros: Simple, fast for small queries
    Cons: Not distributed, runs on driver only
    """

    import psycopg2
    import pandas as pd

    conn = psycopg2.connect(
        host="ignition-db",
        database="historian",
        user="ignition_user",
        password="your_password"
    )

    # Small query for metadata or config
    query = """
        SELECT DISTINCT tagpath, datatype, min(t_stamp), max(t_stamp)
        FROM sqlt_data_1_2024_01
        GROUP BY tagpath, datatype
    """

    df_pandas = pd.read_sql(query, conn)
    df_spark = spark.createDataFrame(df_pandas)

    conn.close()
    return df_spark

# ==============================================================================
# PERFORMANCE COMPARISON
# ==============================================================================

def performance_comparison():
    """
    Compare different connection methods
    """

    import time

    # Test query
    test_query = """
        SELECT COUNT(*), AVG(floatvalue), MAX(floatvalue)
        FROM sqlt_data_1_2024_01
        WHERE t_stamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
    """

    methods = {
        "JDBC": connect_via_jdbc,
        "PostgreSQL Connector": connect_via_postgresql_connector,
        "SQL Federation": connect_via_databricks_sql_federation,
        "Python (psycopg2)": connect_via_python_psycopg2
    }

    results = {}
    for name, method in methods.items():
        start = time.time()
        try:
            df = method()
            count = df.count()
            elapsed = time.time() - start
            results[name] = {
                "time": elapsed,
                "rows": count,
                "rows_per_sec": count / elapsed
            }
        except Exception as e:
            results[name] = {"error": str(e)}

    return results

# ==============================================================================
# RECOMMENDED PRODUCTION ARCHITECTURE
# ==============================================================================

def production_architecture():
    """
    Recommended setup for production
    """

    # 1. Create federated connection for batch queries
    spark.sql("""
        CREATE OR REPLACE TABLE ignition_historian_federated
        USING postgresql
        OPTIONS (
            host 'ignition-db',
            port '5432',
            database 'historian',
            user SECRET('ignition_user', 'credentials'),
            password SECRET('ignition_password', 'credentials'),
            numPartitions '20',
            fetchsize '50000'
        )
    """)

    # 2. Create streaming table for real-time
    spark.sql("""
        CREATE OR REPLACE STREAMING TABLE sensor_stream_realtime
        AS
        SELECT * FROM cloud_files(
            '/mnt/ignition/streaming',
            'json',
            map('cloudFiles.inferColumnTypes', 'true')
        )
    """)

    # 3. Create hybrid view combining both
    spark.sql("""
        CREATE OR REPLACE VIEW sensor_data_enriched AS
        -- Real-time data
        WITH realtime AS (
            SELECT
                equipment_id,
                sensor_name,
                sensor_value,
                timestamp
            FROM sensor_stream_realtime
            WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour'
        ),
        -- Historical context
        historical AS (
            SELECT
                tagpath as equipment_sensor,
                AVG(floatvalue) as baseline_7d,
                STDDEV(floatvalue) as stddev_7d,
                PERCENTILE_CONT(0.95) as p95_30d
            FROM ignition_historian_federated
            WHERE t_stamp > CURRENT_DATE - 30
            GROUP BY tagpath
        )
        -- Join real-time with historical
        SELECT
            r.*,
            h.baseline_7d,
            h.stddev_7d,
            h.p95_30d,
            (r.sensor_value - h.baseline_7d) / h.stddev_7d as z_score
        FROM realtime r
        LEFT JOIN historical h
            ON CONCAT(r.equipment_id, '/', r.sensor_name) = h.equipment_sensor
    """)

    print("Production architecture created successfully!")

# ==============================================================================
# WHICH OPTION TO CHOOSE?
# ==============================================================================

"""
RECOMMENDATION MATRIX:

1. Small Scale / POC:
   → Python psycopg2 for simple queries
   → JDBC with fetchsize tuning

2. Medium Scale (Our Current Demo):
   → PostgreSQL native connector
   → Materialized views for baselines
   → Direct SQL queries in DLT

3. Large Scale Production:
   → Lakehouse Federation with Unity Catalog
   → External tables with partitioning
   → Materialized views with scheduled refresh
   → Streaming for real-time + Federation for batch

4. Enterprise Scale:
   → Delta Sharing from Ignition
   → CDC from PostgreSQL to Delta
   → Photon-accelerated queries
   → Z-order optimization on time + equipment

PERFORMANCE TIPS:
- Always use partitionColumn for large tables
- Set appropriate fetchsize (10000-50000)
- Use broadcast joins for small dimension tables
- Create indexes in Ignition PostgreSQL on (tagpath, t_stamp)
- Use column pruning - only SELECT needed columns
- Consider caching frequently used baselines
"""