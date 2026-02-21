from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'SQLite veritabanını optimize eder'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('🔧 VACUUM işlemi başlıyor...')
            cursor.execute('VACUUM;')
            
            self.stdout.write('🔧 ANALYZE işlemi başlıyor...')
            cursor.execute('ANALYZE;')
            
            self.stdout.write('🔧 REINDEX işlemi başlıyor...')
            cursor.execute('REINDEX;')
        
        self.stdout.write(self.style.SUCCESS('✅ Veritabanı optimize edildi!'))