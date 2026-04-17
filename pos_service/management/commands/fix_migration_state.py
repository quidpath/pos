"""
Management command to fix migration state inconsistencies.
This command helps resolve issues where Django migrations are out of sync with the actual database schema.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Fix migration state inconsistencies by marking migrations as applied'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Check if the problematic columns exist in the database
        with connection.cursor() as cursor:
            # Check if drafted_at column exists
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'pos_posorder' 
                AND column_name IN ('drafted_at', 'posted_at', 'posted_by', 'invoice_id', 'is_invoiced', 'invoiced_at', 'invoiced_by')
            """)
            existing_columns = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"Existing columns in pos_posorder: {existing_columns}")
            
            # Check migration state
            cursor.execute("""
                SELECT name FROM django_migrations 
                WHERE app = 'pos' 
                ORDER BY name
            """)
            applied_migrations = [row[0] for row in cursor.fetchall()]
            
            self.stdout.write(f"Applied migrations: {applied_migrations}")
            
            # If columns exist but migration 0006 is not marked as applied, mark it as applied
            required_columns = ['drafted_at', 'posted_at', 'posted_by', 'invoice_id', 'is_invoiced', 'invoiced_at', 'invoiced_by']
            all_columns_exist = all(col in existing_columns for col in required_columns)
            
            if all_columns_exist:
                self.stdout.write(self.style.SUCCESS('All required columns exist in the database'))
                
                # Check if we need to mark migration 0006 as applied
                if '0006_ensure_schema_consistency' not in applied_migrations:
                    if not dry_run:
                        cursor.execute("""
                            INSERT INTO django_migrations (app, name, applied) 
                            VALUES ('pos', '0006_ensure_schema_consistency', NOW())
                            ON CONFLICT (app, name) DO NOTHING
                        """)
                        self.stdout.write(self.style.SUCCESS('Marked migration 0006_ensure_schema_consistency as applied'))
                    else:
                        self.stdout.write(self.style.WARNING('Would mark migration 0006_ensure_schema_consistency as applied'))
                else:
                    self.stdout.write(self.style.SUCCESS('Migration 0006_ensure_schema_consistency already marked as applied'))
            else:
                missing_columns = [col for col in required_columns if col not in existing_columns]
                self.stdout.write(self.style.ERROR(f'Missing columns: {missing_columns}'))
                self.stdout.write(self.style.ERROR('Database schema is incomplete. Run migrations normally.'))
                
        self.stdout.write(self.style.SUCCESS('Migration state check completed'))