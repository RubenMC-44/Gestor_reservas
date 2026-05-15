from django.db import models

# Usamos el modelo User de Django sin extensión adicional.
# Si en el futuro necesitases campos extra (avatar, teléfono...),
# aquí crearías un modelo Profile con OneToOneField a User.
