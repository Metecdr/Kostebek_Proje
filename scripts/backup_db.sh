#!/bin/bash
# Köstebek YKS - Gece Veritabanı Yedekleme Scripti
# Crontab: 0 0 * * * /home/kostebek/Köstebek_Projesi/scripts/backup_db.sh
# Her gece 00:00'da çalışır, son 7 günü tutar

# Ayarlar
DB_NAME="kostebekyks"
DB_USER="kostebekuser"
BACKUP_DIR="/home/kostebek/backups"
DATE=$(date +%Y-%m-%d_%H-%M)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql.gz"
LOG_FILE="$BACKUP_DIR/backup.log"
RETENTION_DAYS=7

# Backup dizinini oluştur
mkdir -p "$BACKUP_DIR"

# Yedekleme başlangıcı
echo "[$(date '+%Y-%m-%d %H:%M:%S')] Yedekleme başlıyor..." >> "$LOG_FILE"

# PostgreSQL dump (sıkıştırılmış)
PGPASSWORD="Kostebek2024" pg_dump -U "$DB_USER" -h localhost "$DB_NAME" | gzip > "$BACKUP_FILE"

# Başarı kontrolü
if [ $? -eq 0 ]; then
    FILESIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Yedekleme başarılı: $BACKUP_FILE ($FILESIZE)" >> "$LOG_FILE"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ❌ Yedekleme BAŞARISIZ!" >> "$LOG_FILE"
    exit 1
fi

# Eski yedekleri sil (7 günden eski)
DELETED=$(find "$BACKUP_DIR" -name "${DB_NAME}_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🗑️ $DELETED eski yedek silindi (${RETENTION_DAYS}+ gün)" >> "$LOG_FILE"
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Yedekleme tamamlandı." >> "$LOG_FILE"
echo "---" >> "$LOG_FILE"
