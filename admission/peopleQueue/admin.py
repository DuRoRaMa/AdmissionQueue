from django.contrib import admin

from .models import *

# Register your models here.
admin.site.register(Talon)
admin.site.register(TalonLog)
admin.site.register(TalonPurposes)
admin.site.register(OperatorLocation)
admin.site.register(OperatorSettings)
admin.site.register(OperatorQueue)
