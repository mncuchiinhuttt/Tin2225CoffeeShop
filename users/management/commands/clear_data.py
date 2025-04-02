from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Clears all data from the database except user data'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # Disable foreign key checks temporarily
            cursor.execute('SET CONSTRAINTS ALL DEFERRED;')
            
            try:
                tables = [
                    'users_cartitem',
                    'users_orderitem',
                    'users_order',
                    'users_size',
                    'users_menuitem',
                    'users_category'
                ]
                
                for table in tables:
                    self.stdout.write(f'Clearing table {table}...')
                    try:
                        cursor.execute(f'TRUNCATE TABLE {table} CASCADE;')
                        self.stdout.write(self.style.SUCCESS(f'Successfully cleared {table}'))
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f'Error clearing {table}: {str(e)}'))
                        continue
                
                self.stdout.write(self.style.SUCCESS('Successfully cleared all non-user data'))
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
            finally:
                # Re-enable foreign key checks
                cursor.execute('SET CONSTRAINTS ALL IMMEDIATE;') 