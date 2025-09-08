# serializers.py
from rest_framework import serializers
from .models import Company, EmailFormat, UserRegister

class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'domainname', 'country']

class EmailFormatSerializer(serializers.ModelSerializer):
    company_name = serializers.SerializerMethodField()  # <-- add this

    class Meta:
        model = EmailFormat
        fields = ['id', 'company', 'company_name', 'format_string', 'date']  # include company_name

    def get_company_name(self, obj):
        return obj.company.name
    
class UserRegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserRegister
        fields = ['id', 'fullname', 'mobilenumber', 'designation']
