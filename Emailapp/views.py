from django.shortcuts import render, redirect
from io import BytesIO
from django.contrib import messages
from .forms import CompanyForm, EmailFormatForm, UploadFileForm
from .models import Company, EmailFormat,UserRegister
import pandas as pd
from django.http import HttpResponse
from .forms import UploadFileForm
import openpyxl
import re
from collections import defaultdict
import datetime
from datetime import datetime
from .forms import UploadNotepadForm, UploadFileForm
from unidecode import unidecode

def index(request):
    msg = ''
    userpassword=""
    if request.method == 'POST':
        usermobilenumber = request.POST['txtmobilenumber']
        userpassword = request.POST['txtpassword']
        if UserRegister.objects.filter(mobilenumber=usermobilenumber,password=userpassword).exists():
            data=UserRegister.objects.get(mobilenumber=usermobilenumber,password=userpassword)
            request.session["optmobilenumber"]=request.POST['txtmobilenumber']
            return redirect("add_company")
            msg="Loged in Successfully"
        else:
            msg="Invalid Login Details"
    return render(request, 'index.html', {'msg': msg})

# List of common certifications or titles to exclude from names
EXCLUDED_TITLES = [
    "PMP", "MBA", "CSM", "ITIL", "CSPO", "SFC", "ACP", "SAP Successfactors", "EC implementation", "CTDP",
    "SAFe", "SAFe®", "Six Sigma", "PSPO", "PMI-PBA", "SPOC", "M.Eng", "MA", "B.Eng", "MSc", "CBAP", "CFA", 
    "FRM", "PRINCE2", "SSM", "CISA", "DASSM", "PgMP", "SAMC", "ITIL", "GCPM", "TOGAF", "Prosci", "6σ", "FPC",
    "P.Eng.", "GCPM", "TOGAF", "CAPM", "P.Eng", "PhD", "SCM", "PMP®", "CSPO®", "SAFe SPC", "SAFe®6", "AI certified", 
    "AI", "PMP®", "PSM", "PMI-ACP", "PSM I", "SASM", "SσBB™", "PMP®, PMP®, CSPO®, PMP®, CSM", "BSc", "MGP", "CBAP®",
    "M.Eng", "MS", "SASM", "CBAP®", "M.Eng", "PMI-ACP", "PRINCE2P"
]

def is_human_name(name):
    # Regular expression to allow names with letters, periods, hyphens, apostrophes, and parentheses
    name_pattern = re.compile(r"^[a-zA-ZÀ-ÿ'-.() ]+$")

    # Clean the name by removing titles or certifications
    name_cleaned = name
    for title in EXCLUDED_TITLES:
        name_cleaned = re.sub(rf'\b{title}\b', '', name_cleaned)

    # Remove trailing punctuation like ., ,, -
    name_cleaned = re.sub(r'[,.-]+$', '', name_cleaned).strip()

    # Remove periods from the cleaned name
    name_cleaned = name_cleaned.replace('.', '')

    # Strip extra spaces and check if the name matches the pattern
    name_cleaned = name_cleaned.strip()

    # Split the cleaned name into parts
    name_parts = name_cleaned.split()

    # Ensure that the cleaned name still has at least two valid parts (first name and last name)
    if len(name_parts) >= 2 and name_pattern.match(name_cleaned):
        # Check if each part of the name is valid (alphabetic or allowed punctuation)
        return all(re.match(r"[a-zA-ZÀ-ÿ'-]+", part) for part in name_parts)

    return False

def upload_and_convert(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            # Check if country is selected
            selected_country = request.POST.get('country', '').strip()
            if not selected_country:
                messages.error(request, "Please select a valid country.")
                return render(request, 'upload_and_convert.html', {'form': form})
            
            try:
                # Read uploaded file
                uploaded_file = request.FILES.get('file', None)
                if not uploaded_file:
                    messages.error(request, "No file uploaded. Please upload a valid file.")
                    return render(request, 'upload_and_convert.html', {'form': form})

                try:
                    data = uploaded_file.read().decode('utf-8')
                except UnicodeDecodeError:
                    messages.error(request, "Failed to decode the file. Please upload a valid UTF-8 encoded file.")
                    return render(request, 'upload_and_convert.html', {'form': form})

                # Split data into individual profiles based on the delimiter "Add"
                profiles = data.split("Add")
                profile_list = []
                skipped_profile_list = []  # List for skipped profiles

                for profile in profiles[1:]:  # Skip the first item since it's empty
                    lines = profile.splitlines()

                    # Remove empty lines
                    lines = [line for line in lines if line.strip()]

                    # Improved extraction logic for skipped profiles
                    if len(lines) < 7:
                        skipped_profile_list.append({
                            'Full Name': lines[2] if len(lines) > 2 else "N/A",
                            'Skipped Reason': 'Insufficient data (less than 7 lines)',
                            'Company Name': 'N/A',
                            'First Name': 'N/A',
                            'Last Name': 'N/A',
                            'Country': selected_country,
                            'Designation': 'N/A',
                            'Location': 'N/A',
                            'Industry': 'N/A',
                            'Source': 'LinkedIn',
                            'File Name': f'LinkedIn_{datetime.today().strftime("%Y-%m-%d")}',
                        })
                        continue  # Skip profiles that don't have enough data

                    # Extract Full Name from the 3rd line
                    full_name = lines[2].strip() if len(lines) > 2 else "N/A"

                    # Check if the full_name is likely to be a human name
                    if not is_human_name(full_name):
                        skipped_profile_list.append({
                            'Full Name': full_name,
                            'Skipped Reason': "Non-human name",
                            'Company Name': 'N/A',
                            'First Name': 'N/A',
                            'Last Name': 'N/A',
                            'Country': selected_country,
                            'Designation': 'N/A',
                            'Location': 'N/A',
                            'Industry': 'N/A',
                            'Source': 'LinkedIn',
                            'File Name': f'LinkedIn_{datetime.today().strftime("%Y-%m-%d")}',
                        })
                        continue  # Skip non-human names

                    # Clean the full name (remove titles like PMP, MBA, etc.)
                    full_name = unidecode(full_name)  # Convert non-English characters to English equivalents
                    name_parts = full_name.split()
                    name_parts_cleaned = [part for part in name_parts if part not in EXCLUDED_TITLES]
                    
                    # Extract first and last names
                    first_name = name_parts_cleaned[0].strip() if len(name_parts_cleaned) > 0 else 'N/A'
                    last_name = name_parts_cleaned[-1].strip() if len(name_parts_cleaned) > 1 else 'N/A'

                    # Remove periods and commas from full name, first name, and last name
                    full_name = re.sub(r'[.,]', '', full_name)
                    first_name = re.sub(r'[.,]', '', first_name)
                    last_name = re.sub(r'[.,]', '', last_name)

                    # Extract Designation and Company from the 6th line (splitting by two spaces or unexpected characters)
                    role_company_line = lines[5].strip() if len(lines) > 5 else "N/A"
                    role = company = 'N/A'

                    # Look for patterns like space, comma, or special characters between designation and company
                    if '  ' in role_company_line:
                        parts = role_company_line.split('  ')  # Split by double spaces
                        role = parts[0].strip() if len(parts) > 0 else 'N/A'
                        company = parts[1].strip() if len(parts) > 1 else 'N/A'
                    elif ',' in role_company_line or '|' in role_company_line or '-,-' in role_company_line or '"' in role_company_line:
                        # Handle cases where delimiters are commas, pipe symbols, etc.
                        parts = re.split(r'[ ,|"-,-]', role_company_line)  # Split by space, comma, or special characters
                        role = parts[0].strip() if len(parts) > 0 else 'N/A'
                        company = parts[1].strip() if len(parts) > 1 else 'N/A'
                    elif role_company_line:  # If there's only one part (designation or company)
                        role = role_company_line.strip()  # Treat as role if no clear company part is present

                    # Extract Location from the 7th line
                    location = lines[6].strip() if len(lines) > 6 else "N/A"
                    if not location:
                        location = 'N/A'

                    # If location is still missing or incorrectly extracted, try extracting from next available data
                    if '  ' in location:  # If a space or special character pattern exists, handle accordingly
                        location_parts = re.split(r'[ ,|"-,-]', location)
                        location = location_parts[0].strip() if location_parts else 'N/A'

                    # Set static values for Industry, Source, and File Name
                    industry = ''  # Blank for now, so using N/A
                    source = 'LinkedIn'

                    # Add valid profile to the list
                    profile_list.append({
                        'Company Name': company if company else 'N/A',
                        'First Name': first_name if first_name else 'N/A',
                        'Last Name': last_name if last_name else 'N/A',
                        'Country': selected_country,  # Use the selected country here
                        'Designation': role if role else 'N/A',
                        'Location': location if location else 'N/A',
                        'Industry': industry,
                        'Source': source,
                        'Full Name': full_name if full_name else 'N/A',
                        'File Name': f'LinkedIn_{datetime.today().strftime("%Y-%m-%d")}',
                    })

                # If no valid profiles were found
                if not profile_list and not skipped_profile_list:
                    messages.error(request, "No valid profiles were found in the file.")
                    return render(request, 'upload_and_convert.html', {'form': form})

                # Create a DataFrame from the profile list
                df_valid = pd.DataFrame(profile_list)
                df_skipped = pd.DataFrame(skipped_profile_list)

                # Create the Excel file as a response
                response = HttpResponse(content_type='application/vnd.ms-excel')
                response['Content-Disposition'] = f'attachment; filename="developer_profiles_{datetime.today().strftime("%Y-%m-%d")}.xlsx"'

                # Write valid profiles to the first sheet and skipped profiles to the second sheet
                with pd.ExcelWriter(response, engine='xlsxwriter') as writer:
                    df_valid.to_excel(writer, sheet_name='Valid Profiles', index=False)
                    df_skipped.to_excel(writer, sheet_name='Skipped Profiles', index=False)

                return response

            except Exception as e:
                print(f"Error occurred: {e}")
                messages.error(request, "An error occurred while processing the file. Please try again.")
                return render(request, 'upload_and_convert.html', {'form': form})
        else:
            messages.error(request, "Invalid form submission. Please check the file and try again.")

    else:
        form = UploadFileForm()

    return render(request, 'upload_and_convert.html', {'form': form})
    
# Chunk size (number of rows per chunk)
CHUNK_SIZE = 20000  # You can adjust this as needed

def add_company(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Company added successfully.")
            return redirect('add_company')
    else:
        form = CompanyForm()
    return render(request, 'add_company.html', {'form': form})

def add_email_format(request):
    if request.method == 'POST':
        form = EmailFormatForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Email format added successfully.")
            return redirect('add_email_format')
    else:
        form = EmailFormatForm()
    return render(request, 'add_email_format.html', {'form': form})

def upload_excel(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                # Read the Excel file
                df = pd.read_excel(excel_file)

                # Validate required columns
                required_columns = ['Company Name', 'Domain', 'Email Format', 'Country']
                if not all(column in df.columns for column in required_columns):
                    messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}.")
                    return render(request, 'upload_excel.html', {'form': form})

                # Initialize counters and error tracking lists
                added_companies = 0
                added_email_formats = 0
                skipped_companies = 0
                skipped_email_formats = 0
                duplicates = []
                missing_domains = []
                missing_email_formats = []
                missing_countries = []
                conflicting_formats = []

                # Check for duplicate email formats within the same company in the uploaded file
                grouped_df = df.groupby('Company Name')
                for company_name, group in grouped_df:
                    if group['Email Format'].nunique() > 1:
                        conflicting_formats.append({
                            'Company Name': company_name,
                            'Email Formats': ', '.join(group['Email Format'].unique())
                        })

                # If there are conflicting formats, return the conflicts as a downloadable file
                if conflicting_formats:
                    conflicts_df = pd.DataFrame(conflicting_formats)
                    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=email_format_conflicts.xlsx'
                    conflicts_df.to_excel(response, index=False)
                    messages.error(request, "Multiple email formats found for the same company. Please resolve the conflicts in the Excel file.")
                    return response

                # Iterate over each row in the Excel file
                for index, row in df.iterrows():
                    company_name = str(row['Company Name']).strip()
                    domain_name = str(row['Domain']).strip()
                    email_format = str(row['Email Format']).strip()
                    country = str(row['Country']).strip()

                    # Check for missing company name
                    if not company_name:
                        continue  # Skip rows with missing company names

                    # Check for missing domain
                    if not domain_name:
                        missing_domains.append({
                            'Company Name': company_name,
                            'Domain': 'N/A',
                            'Email Format': email_format if email_format else 'N/A',
                            'Country': country if country else 'N/A'
                        })
                        continue

                    # Check for missing email format
                    if not email_format:
                        missing_email_formats.append({
                            'Company Name': company_name,
                            'Domain': domain_name,
                            'Email Format': 'N/A',
                            'Country': country if country else 'N/A'
                        })
                        continue

                    # Check for missing country
                    if not country:
                        missing_countries.append({
                            'Company Name': company_name,
                            'Domain': domain_name,
                            'Email Format': email_format if email_format else 'N/A',
                            'Country': 'N/A'
                        })
                        continue

                    # Check for duplicates in the database based on name, domain, and country
                    company_exists = Company.objects.filter(name=company_name, domainname=domain_name, country=country).exists()
                    if company_exists:
                        duplicates.append({
                            'Company Name': company_name,
                            'Domain': domain_name,
                            'Email Format': email_format,
                            'Country': country
                        })
                        skipped_companies += 1
                        continue

                    # Create or get the company and email format
                    company, company_created = Company.objects.get_or_create(name=company_name, domainname=domain_name, country=country)
                    if company_created:
                        added_companies += 1

                    email_format_obj, email_format_created = EmailFormat.objects.get_or_create(company=company, format_string=email_format)
                    if email_format_created:
                        added_email_formats += 1
                    else:
                        skipped_email_formats += 1

                # Handle success and errors
                if added_companies or added_email_formats:
                    messages.success(request, f"Upload complete: {added_companies} new companies added, {added_email_formats} new email formats added.")

                # Handle missing and duplicate data issues in a downloadable file
                issues = duplicates + missing_domains + missing_email_formats + missing_countries
                if issues:
                    issues_df = pd.DataFrame(issues)
                    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=upload_issues.xlsx'
                    issues_df.to_excel(response, index=False)
                    return response

                # If any data was skipped, notify the user
                if skipped_companies or skipped_email_formats:
                    messages.info(request, f"{skipped_companies} companies and {skipped_email_formats} email formats were already in the database and were skipped.")

                return redirect('upload_excel')

            except pd.errors.EmptyDataError:
                messages.error(request, "The uploaded Excel file is empty. Please provide a valid file.")
            except pd.errors.ParserError:
                messages.error(request, "Error parsing the Excel file. Ensure it is a valid Excel format.")
            except Exception as e:
                messages.error(request, f"An error occurred while processing the file: {str(e)}")

        else:
            messages.error(request, "Please upload a valid Excel file.")

    else:
        form = UploadFileForm()

    return render(request, 'upload_excel.html', {'form': form})


def generate_emails(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)
                required_columns = ['Company Name', 'First Name', 'Last Name', 'Country']
                if not all(column in df.columns for column in required_columns):
                    messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}.")
                    return render(request, 'generate_emails.html', {'form': form})

                # Exclude rows with numbers in any of the required columns
                df = df[~df[['Company Name', 'First Name', 'Last Name', 'Country']].apply(lambda x: x.astype(str).str.contains('\d')).any(axis=1)]

                generated_emails = []
                missing_companies = []
                missing_format = []
                invalid_data = []
                duplicates = []

                for index, row in df.iterrows():
                    company_name = str(row['Company Name']).strip()
                    first_name = str(row['First Name']).strip()
                    last_name = str(row['Last Name']).strip()
                    country = str(row['Country']).strip()

                    if not company_name or not first_name or not last_name or not country:
                        invalid_data.append({
                            'Company Name': company_name if company_name else 'N/A',
                            'First Name': first_name if first_name else 'N/A',
                            'Last Name': last_name if last_name else 'N/A',
                            'Country': country if country else 'N/A'
                        })
                        generated_emails.append('N/A')
                        continue

                    try:
                        # Filter by both company name and country
                        companies = Company.objects.filter(name=company_name, country=country)

                        if not companies.exists():
                            # Company not found, add to missing_companies
                            missing_companies.append({
                                'Company Name': company_name,
                                'First Name': first_name,
                                'Last Name': last_name,
                                'Country': country
                            })
                            generated_emails.append('N/A')
                            continue

                        # If multiple companies exist, pick the last one or implement custom logic
                        company = companies.last()  # Optionally, add logic to select based on domain, etc.
                        domain = company.domainname
                        email_format = EmailFormat.objects.filter(company=company).last()

                        if not email_format:
                            missing_format.append({
                                'Company Name': company_name,
                                'First Name': first_name,
                                'Last Name': last_name,
                                'Country': country
                            })
                            generated_emails.append('N/A')
                            continue

                        # Generate the email based on the format
                        format_string = email_format.format_string

                        # Safely get initials or handle missing characters
                        first_initial = first_name[0].lower() if first_name else ''
                        last_initial = last_name[0].lower() if last_name else ''

                        # Apply replacements
                        email = format_string.replace("{first_initial}", first_initial)
                        email = email.replace("{last_initial}", last_initial)
                        email = email.replace("{first_name}", first_name.lower())
                        email = email.replace("{last_name}", last_name.lower())
                        email = email.replace("{company}", domain)

                        # Handle middle initial if needed (optional)
                        middle_initial = ""
                        name_parts = first_name.split()
                        if len(name_parts) > 1:
                            middle_initial = name_parts[1][0].lower() if name_parts[1] else ''
                        email = email.replace("{middle_initial}", middle_initial)

                        # Check for duplicates
                        if email in generated_emails:
                            duplicates.append({
                                'Company Name': company_name,
                                'First Name': first_name,
                                'Last Name': last_name,
                                'Generated Email': email,
                                'Country': country
                            })
                            generated_emails.append('N/A')
                            continue

                        generated_emails.append(email)

                    except Company.DoesNotExist:
                        missing_companies.append({
                            'Company Name': company_name,
                            'First Name': first_name,
                            'Last Name': last_name,
                            'Country': country
                        })
                        generated_emails.append('N/A')
                        continue

                # Add the generated emails to the original DataFrame
                df['Generated Email'] = generated_emails

                # Create a BytesIO stream to write the Excel file
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df.to_excel(writer, sheet_name='Generated Emails', index=False)

                    if missing_companies or missing_format or invalid_data or duplicates:
                        issues = missing_companies + missing_format + invalid_data + duplicates
                        issues_df = pd.DataFrame(issues)
                        issues_df.to_excel(writer, sheet_name='Issues', index=False)

                # Set the cursor of the BytesIO stream to the beginning
                output.seek(0)

                # Return the Excel file as a download response
                response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                response['Content-Disposition'] = 'attachment; filename=generated_emails_and_issues.xlsx'
                return response

            except Exception as e:
                messages.error(request, f"An error occurred while processing the file: {str(e)}")
                return render(request, 'generate_emails.html', {'form': form})
        else:
            messages.error(request, "Please upload a valid Excel file.")
    else:
        form = UploadFileForm()
    return render(request, 'generate_emails.html', {'form': form})

def detect_email_format(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            try:
                df = pd.read_excel(excel_file)
                required_columns = ['Company', 'Employee Name', 'Email']
                if not all(column in df.columns for column in required_columns):
                    messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}.")
                    return render(request, 'upload_emails.html', {'form': form})

                # Exclude rows with numbers in Employee Name or Email
                df = df[~df[['Employee Name', 'Email']].apply(lambda x: x.astype(str).str.contains('\d')).any(axis=1)]

                email_patterns = []
                invalid_emails = []

                def get_initials(name):
                    return name[0].lower() if name else ''  # Check if name is not empty

                # Analyze email patterns
                for index, row in df.iterrows():
                    company = str(row.get('Company', '')).strip()
                    employee_name = str(row['Employee Name']).strip()
                    email = str(row['Email']).strip()

                    # Validate email format
                    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
                    if not re.match(email_regex, email):
                        invalid_emails.append({
                            'Company': company,
                            'Employee Name': employee_name,
                            'Email': email,
                            'Detected Email Format': 'Invalid email format'
                        })
                        continue

                    # Split the email and convert to lowercase
                    email_local, domain = email.lower().split('@')

                    # Split the employee name into parts and convert them to lowercase
                    name_parts = employee_name.lower().split()

                    # Initialize variables to avoid "variable not defined" errors
                    first_name = last_name = middle_name = ''
                    first_initial = last_initial = middle_initial = ''

                    # Handle cases with only a first and last name
                    if len(name_parts) == 2:
                        first_name, last_name = name_parts[0], name_parts[1]

                    # Handle cases with a first, middle, and last name
                    elif len(name_parts) == 3:
                        first_name, middle_name, last_name = name_parts

                    # Handle cases with more than three parts (e.g., multiple middle names)
                    elif len(name_parts) > 3:
                        first_name = name_parts[0]
                        last_name = name_parts[-1]
                        middle_name = " ".join(name_parts[1:-1])  # Combine all middle parts

                    # Handle cases with only one part (incomplete name)
                    elif len(name_parts) == 1:
                        first_name = name_parts[0]

                    # Ensure first name and last name are not empty before using their initials
                    if first_name:
                        first_initial = get_initials(first_name)
                    if last_name:
                        last_initial = get_initials(last_name)
                    if middle_name:
                        middle_initial = get_initials(middle_name)

                    # Detect patterns based on employee name and email
                    detected_format = 'Cannot determine format'  # Default if no match found

                    # Adjust the pattern detection logic
                    patterns = {
                        # Exact first_initial + last_name format
                        f"{first_initial}{last_name.lower()}": '{first_initial}{last_name}@{company}',
                        f"{first_name.lower()}.{last_name.lower()}": '{first_name}.{last_name}@{company}',
                        f"{first_name.lower()}_{last_name.lower()}": '{first_name}_{last_name}@{company}',
                        
                        # Add condition to check for middle name only if it exists
                        f"{first_initial}{middle_initial}{last_name.lower()}": '{first_initial}{middle_initial}{last_name}@{company}' if middle_initial else '',
                        f"{first_name.lower()}_{last_initial}": '{first_name}_{last_initial}@{company}',
                        f"{first_name.lower()}.{last_initial}": '{first_name}.{last_initial}@{company}',
                        f"{first_name.lower()}-{last_name.lower()}": '{first_name}-{last_name}@{company}',
                        f"{first_name.lower()}-{last_initial}": '{first_name}-{last_initial}@{company}',
                        f"{first_initial}.{last_name.lower()}": '{first_initial}.{last_name}@{company}',
                        f"{first_initial}_{last_name.lower()}": '{first_initial}_{last_name}@{company}',
                        f"{first_initial}-{last_name.lower()}": '{first_initial}-{last_name}@{company}',
                        f"{first_initial}{last_initial}": '{first_initial}{last_initial}@{company}',
                        f"{first_initial}.{last_initial}": '{first_initial}.{last_initial}@{company}',
                        f"{first_initial}_{last_initial}": '{first_initial}_{last_initial}@{company}',
                        f"{first_initial}-{last_initial}": '{first_initial}-{last_initial}@{company}',
                        f"{last_name.lower()}.{first_name.lower()}": '{last_name}.{first_name}@{company}',
                        f"{last_name.lower()}.{first_initial}": '{last_name}.{first_initial}@{company}',
                        f"{last_name.lower()}_{first_name.lower()}": '{last_name}_{first_name}@{company}',
                        f"{last_name.lower()}-{first_name.lower()}": '{last_name}-{first_name}@{company}',
                        f"{last_name.lower()}_{first_initial}": '{last_name}_{first_initial}@{company}',
                        f"{last_name.lower()}-{first_initial}": '{last_name}-{first_initial}@{company}',
                        f"{last_initial}.{first_name.lower()}": '{last_initial}.{first_name}@{company}',
                        f"{last_initial}_{first_name.lower()}": '{last_initial}_{first_name}@{company}',
                        f"{last_initial}-{first_name.lower()}": '{last_initial}-{first_name}@{company}',
                        f"{last_initial}{first_initial}": '{last_initial}{first_initial}@{company}',
                        f"{last_initial}.{first_initial}": '{last_initial}.{first_initial}@{company}',
                        f"{last_initial}_{first_initial}": '{last_initial}_{first_initial}@{company}',
                        f"{last_initial}-{first_initial}": '{last_initial}-{first_initial}@{company}',
                        f"{first_name.lower()}": '{first_name}@{company}',
                        f"{last_name.lower()}": '{last_name}@{company}',

                        # Commonly used email formats
                        f"{first_name.lower()}{last_name.lower()}": '{first_name}{last_name}@{company}',
                        f"{first_initial}{last_name.lower()}": '{first_initial}{last_name}@{company}',
                        f"{first_name.lower()}.{last_initial}": '{first_name}.{last_initial}@{company}',
                        f"{first_name.lower()}{last_initial}": '{first_name}{last_initial}@{company}',
                        f"{first_name.lower()}{last_initial.lower()}": '{first_name}{last_initial}@{company}',
                        f"{first_name.lower()}{last_name.lower()}": '{first_name}{last_name}@{company}',  # e.g. JohnSmi for John Smith
                        # Ensure middle initials only used when they exist
                        f"{first_initial}{middle_initial}{last_name.lower()}": '{first_initial}{middle_initial}{last_name}@{company}' if middle_initial else '',
                    
                        f"{first_initial}{last_name.lower()}": '{first_initial}{last_name}@{company}',
                        f"{first_name.lower()}.{last_name.lower()}": '{first_name}.{last_name}@{company}',
                        f"{first_name.lower()}_{last_name.lower()}": '{first_name}_{last_name}@{company}',
                        f"{first_initial}{middle_initial}{last_name.lower()}": '{first_initial}{middle_initial}{last_name}@{company}' if middle_initial else '',
                        f"{first_name.lower()}_{last_initial}": '{first_name}_{last_initial}@{company}',
                        f"{first_name.lower()}.{last_initial}": '{first_name}.{last_initial}@{company}',
                        f"{first_name.lower()}-{last_name.lower()}": '{first_name}-{last_name}@{company}',
                        f"{first_initial}.{last_name.lower()}": '{first_initial}.{last_name}@{company}',
                        f"{last_name.lower()}.{first_name.lower()}": '{last_name}.{first_name}@{company}',
                        f"{first_initial}{last_name}": '{first_initial}{last_name}@{company}',

                        # Additional patterns...
                    }

                    if email_local in patterns and patterns[email_local]:
                        detected_format = patterns[email_local]
                    else:
                        detected_format = analyze_complex_format(email_local, first_name, middle_name, last_name)
                        if detected_format == f"{email_local}@{domain}":
                            detected_format = 'Cannot determine format'

                    email_patterns.append({
                        'Company': company,
                        'Employee Name': employee_name,
                        'Email': email,
                        'Detected Email Format': detected_format
                    })

                if invalid_emails:
                    invalid_df = pd.DataFrame(invalid_emails)
                    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=invalid_emails.xlsx'
                    invalid_df.to_excel(response, index=False)
                    return response

                if email_patterns:
                    patterns_df = pd.DataFrame(email_patterns)
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        patterns_df.to_excel(writer, sheet_name='Detected Formats', index=False)

                    output.seek(0)
                    response = HttpResponse(output, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                    response['Content-Disposition'] = 'attachment; filename=email_format_analysis.xlsx'
                    return response

                messages.success(request, "Email format analysis completed.")
                return redirect('detect_email_format')

            except Exception as e:
                messages.error(request, f"An error occurred while processing the file: {str(e)}")
                return render(request, 'upload_emails.html', {'form': form})
        else:
            messages.error(request, "Please upload a valid Excel file.")
    else:
        form = UploadFileForm()
    return render(request, 'upload_emails.html', {'form': form})

def analyze_complex_format(email_local, first_name, middle_name, last_name):
    format_string = email_local
    
    # Replace first name and initials
    if first_name.lower() in email_local:
        format_string = format_string.replace(first_name.lower(), '{first_name}')
    if first_name and first_name[0].lower() in email_local:
        format_string = format_string.replace(first_name[0].lower(), '{first_initial}')

    # Replace middle name and initials if present
    if middle_name:
        if middle_name.lower() in email_local:
            format_string = format_string.replace(middle_name.lower(), '{middle_name}')
        if middle_name and middle_name[0].lower() in email_local:
            format_string = format_string.replace(middle_name[0].lower(), '{middle_initial}')
    
    # Replace last name and initials
    if last_name.lower() in email_local:
        format_string = format_string.replace(last_name.lower(), '{last_name}')
    if last_name and last_name[0].lower() in email_local:
        format_string = format_string.replace(last_name[0].lower(), '{last_initial}')

    if re.search(r'[a-z]', format_string.replace('{first_name}', '').replace('{first_initial}', '')
                                        .replace('{middle_name}', '').replace('{middle_initial}', '')
                                        .replace('{last_name}', '').replace('{last_initial}', '')):
        return 'N/A'
    return format_string + '@{company}'
