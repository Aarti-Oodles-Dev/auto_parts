#!/bin/bash
# ============================================================
# STEP 2: AutoCare SQL files import karo
# D1 se run karo:
#   cd ~/Desktop/Asian-Autos/frappe-bench/apps/auto_parts
#   bash auto_parts/scripts/02_import_sql_files.sh
# ============================================================
# SQL zip files teri machine pe kahan hain? wahan ka path daal
SQL_DIR="${1:-/home/aarti-kumari/Downloads}"

echo "Enter MySQL root password:"
read -s MYSQL_PASS

echo ""
echo "SQL files directory: $SQL_DIR"
echo ""

import_sql() {
    local DB=$1
    local ZIP_PATTERN=$2
    local ZIP_FILE=$(ls ${SQL_DIR}/${ZIP_PATTERN} 2>/dev/null | head -1)

    if [ -z "$ZIP_FILE" ]; then
        echo "  [SKIP] $ZIP_PATTERN not found in $SQL_DIR"
        return
    fi

    echo "=== Importing: $DB from $ZIP_FILE ==="
    unzip -p "$ZIP_FILE" | mysql -h db -u root -p${MYSQL_PASS} "$DB"
    if [ $? -eq 0 ]; then
        echo "  DONE: $DB imported!"
    else
        echo "  ERROR: $DB import failed!"
    fi
    echo ""
}

import_sql "autocare_vcdb"  "AutoCare_VCdb_NA_LDPS_enUS_MySQL_*.zip"
import_sql "autocare_pcdb"  "AutoCare_PCdb_enUS_MySQL_*.zip"
import_sql "autocare_padb"  "AutoCare_PAdb_enUS_MySQL_*.zip"
import_sql "autocare_pcadb" "AutoCare_PCAdb_enUS_MySQL_*.zip"
import_sql "autocare_qdb"   "AutoCare_Qdb_enUS_MySQL_*.zip"

echo "=== SQL imports complete! ==="
echo "Now run step 3 - Brands JSON import"