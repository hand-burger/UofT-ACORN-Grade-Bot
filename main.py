import sys
import time
import smtplib
PYTHON2 = (sys.version_info[0] < 3)
import re
import requests
import getpass
if PYTHON2:
    import urllib
else:
    import urllib.parse as urllib

# You can fill this information in to avoid typing.
# However I don't recommend it.
UTORID_USERNAME = ''
UTORID_PASSWORD = ''

EMAIL_USERNAME = ''
EMAIL_PASSWORD = ''

URLS = {
 'acorn': 'http://acorn.utoronto.ca/',
 'acorn_spACS': 'https://acorn.utoronto.ca/spACS',
 'complete_academic_history': 'https://acorn.utoronto.ca/sws/rest/' +
                              'history/academic/complete',
 'logout': 'https://acorn.utoronto.ca/sws/auth/logout'
}

def perform_SSO(username, password):

    session = requests.session()

    acorn_redirect_to_auth = session.get(URLS['acorn'])

    sso_url = acorn_redirect_to_auth.url

    payload, headers = prepare_login_form_data(acorn_redirect_to_auth.text,
                                             username, password)

    login_redirect_to_loggedin = session.post(sso_url,
                                            headers=headers, data=payload)

    if "Authentication Failed" in login_redirect_to_loggedin.text:
        print("ERROR: Are your credentials correct?")
        exit(1)

    form_inputs = extract_form_data(login_redirect_to_loggedin.text)
    SSO_idp_redirect_to_acorn = session.post(URLS['acorn_spACS'],
                                              data=form_inputs)

    if "ACORN Unavailable" in SSO_idp_redirect_to_acorn.text:
        print("ERROR: ACORN is unavailable.")
        exit(1)

    return session

def prepare_login_form_data(login_markup, user, pw):
    form_data = extract_form_data(login_markup)
    form_inputs = {}
    form_inputs.update(form_data)
    form_inputs['j_username'] = user
    form_inputs['j_password'] = pw
    form_inputs['_eventId_proceed'] = ''
    payload = urllib.urlencode(form_inputs)
    headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
    return payload, headers

def extract_form_data(raw_markup):
    form_regex = '<input type=hidden name=([^\ ]*) value=([^>]*)'
    raw_markup = raw_markup.replace('"', '')
    pattern = re.compile(form_regex)
    matches = pattern.findall(raw_markup)
    form_data = {}
    for form_input in matches:
        form_data[str(form_input[0])] = str(form_input[1])
    return form_data

def retrieve_complete_academic_history(session):
    complete_history = session.get(URLS['complete_academic_history'])
    marks_regex = '<div.*?courses blok.*?>([^<]*)</div>'
    pattern = re.compile(marks_regex)
    all_marks = pattern.findall(complete_history.text)

    gpa_regex = '<div.*?gpa-listing.*?>([^<]*)</div>'
    pattern = re.compile(gpa_regex)
    all_gpas = pattern.findall(complete_history.text)
    return all_marks, all_gpas

def logout(session):
    response = session.get(URLS['logout'])
    return 'You have logged out of ACORN' in response.text

if __name__ == '__main__':
    if not UTORID_USERNAME or not UTORID_PASSWORD \
        or not EMAIL_PASSWORD or not EMAIL_USERNAME:
        if PYTHON2:
            input_method = raw_input
        else:
            input_method = input
        UTORID_USERNAME = input_method("Please enter your UTORid: ")
        UTORID_PASSWORD = getpass.getpass("Please enter your password: ")
        email = input_method("Would you like email notifications (y/n): ")
        if email == 'y':
            print("NOTE: Email notifications require additional setup.")
            EMAIL_USERNAME = input_method("Please enter your email: ")
            EMAIL_PASSWORD = getpass.getpass("Please enter your password: ")

    print('Processing...\n')


    try:
        authed_session = perform_SSO(UTORID_USERNAME, UTORID_PASSWORD)
        marks, gpas = retrieve_complete_academic_history(authed_session)
    except requests.exceptions.RequestException as exception:
        print(exception)
        print('\nAre you connected to the internet?')
        exit(1)

    if email == 'y':
        print('Starting email server...\n')
        try:
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        except: 
            print('Server failed to start. Did you enter the correct password?\n')
            print('If you\'re using gmail, make sure you\'re using an App Password.')


    for semester in marks:
        print(semester)
    print('\n')
    for semester in gpas:
        print(semester)

    # Save the marks to compare
    first_marks = marks

    # Repeatedly Perform SSO
    while first_marks == marks:
        logout(authed_session)
        try: 
            authed_session = perform_SSO(UTORID_USERNAME, UTORID_PASSWORD)
            marks, gpas = retrieve_complete_academic_history(authed_session)
        except requests.exceptions.RequestException as exception:
            print(exception)
            print('\nAre you connected to the internet?')
            exit(1)
        print('No change detected, checking again in 10 minutes.')
        time.sleep(600)  # Check every 10 minutes

    print('Change Detected!')
    try:
        SUBJECT = 'Change detected in Academic History!'
        TEXT = 'Check ACORN: https://acorn.utoronto.ca/'
        message = 'Subject: {}\n\n{}'.format(SUBJECT, TEXT)
        server.sendmail(EMAIL_USERNAME, EMAIL_USERNAME, message)
    except:
        print('Failed to send email. Did you enter the correct password?\n')

    print('\n')

    if logout(authed_session):
        print('Logged out!')
    else:
        print('Logout unsuccessful')

    server.quit()
