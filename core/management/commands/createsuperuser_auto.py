from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Automatically create a superuser if none exists."

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="vominhlong").exists():
            User.objects.create_superuser(
                username="vominhlong",
                email="vominhlongbentre@gmail.com",
                password="Vominhlong1212@"
            )
            self.stdout.write(self.style.SUCCESS("Superuser created"))
        else:
            self.stdout.write("Superuser already exists")
