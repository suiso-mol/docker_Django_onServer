from django.contrib import admin

from .models import Server
from .models import Package
from .models import Content

admin.site.register(Server)
admin.site.register(Package)
admin.site.register(Content)
