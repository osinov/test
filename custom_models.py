from django.db import models

class CustomMoneyField(models.CharField):
    def db_type(self, connection):
        return 'money'
