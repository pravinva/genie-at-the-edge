#!/usr/bin/env bash
set -euo pipefail

# This script captures the current reproducible commands and platform constraints.
# Workspace profile defaults to DEFAULT; export DATABRICKS_CONFIG_PROFILE to override.

PROFILE="${DATABRICKS_CONFIG_PROFILE:-DEFAULT}"
INSTANCE_NAME="${INSTANCE_NAME:-pravin-ignition}"
MANAGED_CATALOG="${MANAGED_CATALOG:-pravin_ignition_managed}"
LOGICAL_DB="${LOGICAL_DB:-historian}"

echo "Using profile: ${PROFILE}"
echo "Ensuring Lakebase instance exists: ${INSTANCE_NAME}"

databricks -p "${PROFILE}" database get-database-instance "${INSTANCE_NAME}" -o json \
  || databricks -p "${PROFILE}" database create-database-instance "${INSTANCE_NAME}" --capacity CU_1 --enable-pg-native-login --no-wait -o json

echo "Ensuring managed database catalog exists: ${MANAGED_CATALOG}"
databricks -p "${PROFILE}" database get-database-catalog "${MANAGED_CATALOG}" -o json \
  || databricks -p "${PROFILE}" database create-database-catalog "${MANAGED_CATALOG}" "${INSTANCE_NAME}" "${LOGICAL_DB}" --create-database-if-not-exists -o json

cat <<'EOF'

IMPORTANT CONSTRAINTS OBSERVED (current platform behavior):
1) UC schema creation is NOT allowed inside CATALOG_MANAGED_POSTGRESQL:
   databricks schemas create <schema> <managed_catalog>  -> fails.

2) create-database-table currently supports only STANDARD catalogs:
   databricks database create-database-table ... in managed catalog -> fails.

3) Practical pattern right now:
   - Keep analytics/Zerobus targets in standard UC catalog (e.g. field_engineering.*),
   - Keep operational historian/serving tables in Lakebase Postgres (historian DB),
   - Use synced tables / Reverse ETL where needed for lakehouse -> lakebase activation.

EOF
