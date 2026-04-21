import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db.migrations.recorder import MigrationRecorder

def mark_migration_as_applied():
    try:
        recorder = MigrationRecorder.Migration.objects.using('default')
        recorder.create(
            app='cocktail',
            name='0003_combo_adjust_tables',
        )
        print("Migration marked as applied successfully!")
    except Exception as e:
        print(f"Migration might already be applied: {e}")

if __name__ == "__main__":
    mark_migration_as_applied()