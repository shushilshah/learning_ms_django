from django.contrib.auth import get_user_model
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lms_system.settings")
django.setup()


User = get_user_model()

# Set these from environment variables
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

if not User.objects.filter(username=ADMIN_USERNAME).exists():
    print(f"Creating superuser {ADMIN_USERNAME}")
    User.objects.create_superuser(
        username=ADMIN_USERNAME,
        email=ADMIN_EMAIL,
        password=ADMIN_PASSWORD
    )
else:
    print(f"Superuser {ADMIN_USERNAME} already exists")
