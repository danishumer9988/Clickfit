import os
import sys
from django.core.wsgi import get_wsgi_application

# Add project path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Correct settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clickfit.settings")

application = get_wsgi_application()

# 👇 Vercel "app" name expect karta hai
app = application
