from django.db import models
import datetime
class Company(models.Model):
    name = models.CharField(max_length=255)
    domainname = models.CharField(max_length=255)
    country = models.CharField(max_length=100)
    date = models.DateField(default=datetime.date.today)
    softdelete=models.IntegerField(default=0)

    class Meta:
        unique_together = ('name', 'domainname', 'country')

    def __str__(self):
        return f"{self.name} ({self.domainname}, {self.country})"



class EmailFormat(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    format_string = models.CharField(max_length=255)
    date = models.DateField(default=datetime.date.today)
    softdelete=models.IntegerField(default=0)


    def __str__(self):
        return f"{self.company.name} - {self.format_string}"
