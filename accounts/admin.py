from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

# El UserAdmin por defecto ya registra el modelo User.
# No necesitamos re-registrar nada aquí.
