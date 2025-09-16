from django.contrib import admin
# Import specific models to avoid NameError
from .models import ChatGroup, GroupMessage
# Register your models here.

admin.site.register(ChatGroup)
admin.site.register(GroupMessage)