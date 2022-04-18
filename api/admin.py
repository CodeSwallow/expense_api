from django.contrib import admin
from api.models import Account, Expense, Payment
# Register your models here.


admin.site.register(Account)
admin.site.register(Expense)
admin.site.register(Payment)

