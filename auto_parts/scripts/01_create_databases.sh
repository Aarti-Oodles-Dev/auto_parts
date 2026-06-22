#!/bin/bash
# ============================================================
# STEP 1: Purani DB drop karo + Naye 6 AutoCare Databases banao
# D1 se run karo:
#   cd ~/Desktop/Asian-Autos/frappe-bench/apps/auto_parts
#   bash auto_parts/scripts/01_drop_and_create_databases.sh
# ============================================================

echo "MySQL root password enter karo:"
read -s MYSQL_PASS
MYSQL_CMD="mysql -h db -u root -p${MYSQL_PASS}"

echo ""
echo "=== Purani autocare_master DB drop ho rahi hai... ==="
mysql -h db -u root -p${MYSQL_PASS} -e "DROP DATABASE IF EXISTS autocare_master;"

echo "=== 6 naye AutoCare databases create ho rahe hain... ==="
mysql -h db -u root -p${MYSQL_PASS} -e "
CREATE DATABASE IF NOT EXISTS autocare_vcdb  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS autocare_pcdb  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS autocare_padb  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS autocare_pcadb CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS autocare_qdb   CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS autocare_brands CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
GRANT SELECT ON autocare_vcdb.*   TO '_b91c46a6a05c36aa'@'%';
GRANT SELECT ON autocare_pcdb.*   TO '_b91c46a6a05c36aa'@'%';
GRANT SELECT ON autocare_padb.*   TO '_b91c46a6a05c36aa'@'%';
GRANT SELECT ON autocare_pcadb.*  TO '_b91c46a6a05c36aa'@'%';
GRANT SELECT ON autocare_qdb.*    TO '_b91c46a6a05c36aa'@'%';
GRANT SELECT ON autocare_brands.* TO '_b91c46a6a05c36aa'@'%';
FLUSH PRIVILEGES;
SHOW DATABASES LIKE 'autocare_%';
"

echo ""
echo "=== DONE! 6 databases ready. Ab Step 2 run karo ==="