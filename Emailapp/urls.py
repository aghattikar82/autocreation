from django.urls import path
from .views import upload_excel, generate_emails, add_company, add_email_format, detect_email_format,upload_and_convert

urlpatterns = [
    path('upload/',upload_and_convert, name='upload_and_convert'),
    path('', upload_excel, name='upload_excel'),
    path('generate-emails/', generate_emails, name='generate_emails'),
    path('add-company/', add_company, name='add_company'),
    path('', add_email_format, name='add_email_format'),
    path('detect-email-format/', detect_email_format, name='detect_email_format')
]
