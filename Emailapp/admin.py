from django.contrib import admin
from .models import Company, EmailFormat

class EmailFormatInline(admin.TabularInline):
    model = EmailFormat
    extra = 1

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'domainname','country')
    inlines = [EmailFormatInline]

@admin.register(EmailFormat)
class EmailFormatAdmin(admin.ModelAdmin):
    list_display = ('company', 'format_string')



