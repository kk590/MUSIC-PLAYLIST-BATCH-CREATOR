# backup_service.py
import subprocess
from datetime import datetime

class BackupService:
    def backup_postgres(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.sql"
        subprocess.run([
            "pg_dump", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME,
            "-f", f"/backups/{filename}"
        ])
        upload_to_s3(filename)

    def restore(self, backup_key: str):
        download_from_s3(backup_key, "/tmp/restore.sql")
        subprocess.run([
            "psql", "-h", DB_HOST, "-U", DB_USER, "-d", DB_NAME,
            "-f", "/tmp/restore.sql"
        ])
