from django.urls import path
from .views import index,upload_excel, generate_emails, add_company, add_email_format, detect_email_format,upload_and_convert
from .views import company_list ,emailformat_list,user_list,dashboard_insights
urlpatterns = [
    #Below are API endpoints
    path('api/companies/', company_list, name='company-list'),
    path('api/emailformats/', emailformat_list, name='emailformat-list'),
    path('api/users/', user_list, name='user-list'),
    path('api/dashboard-insights/', dashboard_insights, name='dashboard-insights'),
    

    path('',index, name='index'),
    path('upload/',upload_and_convert, name='upload_and_convert'),
    path('upload_excel', upload_excel, name='upload_excel'),
    path('generate-emails/', generate_emails, name='generate_emails'),
    path('add-company/', add_company, name='add_company'),
    path('', add_email_format, name='add_email_format'),
    path('detect-email-format/', detect_email_format, name='detect_email_format')
]
