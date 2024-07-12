import requests
import json
from time import monotonic, sleep
import names
from random import randint, sample, shuffle
import string
import re

MAIL_DOMAIN = "txcct.com"
FIREBASE_API_KEY = 'AIzaSyA9dhp5-AKka4EtVGO_JBG7bM8mplA0WlE'
FIREBASE_URL = 'https://www.googleapis.com/identitytoolkit/v3/relyingparty'

def tempmail():
    first_name = names.get_first_name()
    last_name = names.get_last_name()
    if randint(0, 1) == 0:
        return f"{first_name}.{last_name}{randint(0, 9999)}@{MAIL_DOMAIN}".lower()
    return f"{first_name}{randint(0, 9999)}@{MAIL_DOMAIN}".lower()

def temppass():
    lower = string.ascii_lowercase
    upper = string.ascii_uppercase
    num = string.digits
    symbols = string.punctuation

    temp = sample(upper, randint(1, 2))
    temp += sample(lower, randint(8, 10))
    temp += sample(num, randint(1, 3))
    temp += sample(symbols, 1) + ["#"]

    shuffle(temp)
    return "".join(temp)

def get_confirmation_link(mail: str):
    mail_user = mail.split("@")[0]
    http_get_url = f"https://www.1secmail.com/api/v1/?action=getMessages&login={mail_user}&domain={MAIL_DOMAIN}"

    latest_mail_id = None
    t0 = monotonic()
    while not latest_mail_id:
        response = requests.get(http_get_url).json()
        if response:
            for email in response:
                if email["from"] == "noreply@workshop-simsimi.firebaseapp.com":
                    latest_mail_id = email["id"]
                    break
        else:
            sleep(1)
            if monotonic() - t0 > 60:
                raise Exception("Email not received in time")

    if not latest_mail_id:
        raise Exception("No email from noreply@workshop-simsimi.firebaseapp.com found")

    http_get_url_single = (
        f"https://www.1secmail.com/api/v1/?action=readMessage&login={mail_user}&domain={MAIL_DOMAIN}&id={latest_mail_id}"
    )
    mail_content = requests.get(http_get_url_single).json()["textBody"]

    urls = re.findall(r"https?://[^\s]+", mail_content)
    if len(urls) != 1:
        raise Exception("Invalid number of confirmation links found")

    confirmation_url = urls[0]
    
    confirmation_response = requests.get(confirmation_url)
    if confirmation_response.status_code == 200:
        oobCode = confirmation_url.split("oobCode=")[1].split("&")[0]
        
        set_account_info_url = f'{FIREBASE_URL}/setAccountInfo?key={FIREBASE_API_KEY}'
        payload = {"oobCode": oobCode}
        set_account_info_response = requests.post(set_account_info_url, json=payload)
        if set_account_info_response.status_code == 200:
            return True
        else:
            print(f"Gagal mengirim permintaan tautan konfirmasi. Status code: {set_account_info_response.status_code}")
            print(set_account_info_response.text)
    else:
        print(f"Failed to click the confirmation link. Status code: {confirmation_response.status_code}")

def create_account():
    print('creating...')
    email = tempmail()
    password = temppass()
    firebase_signup_url = f'{FIREBASE_URL}/signupNewUser?key={FIREBASE_API_KEY}'
    firebase_login_url = f'{FIREBASE_URL}/verifyPassword?key={FIREBASE_API_KEY}'

    signup_data = {
        'email': email,
        'password': password,
        'returnSecureToken': True
    }

    headers = {
        'Content-Type': 'application/json',
        'Origin': 'https://workshop.simsimi.com',
        'Referer': 'https://workshop.simsimi.com/en/login'
    }

    response_signup = requests.post(firebase_signup_url, json=signup_data, headers=headers)

    if response_signup.status_code == 200:
        response_data = response_signup.json()
        id_token = response_data.get('idToken')
        if id_token:
            firebase_get_account_info_url = f'{FIREBASE_URL}/getAccountInfo?key={FIREBASE_API_KEY}'
            account_info_data = {'idToken': id_token}

            response_account_info = requests.post(firebase_get_account_info_url, json=account_info_data, headers=headers)
            
            if response_account_info.status_code == 200:
                response_json = response_account_info.json()
                
                uuid = response_json['users'][0]['localId']
                
                firebase_send_oob_code_url = f'{FIREBASE_URL}/getOobConfirmationCode?key={FIREBASE_API_KEY}'
                oob_data = {
                    'requestType': 'VERIFY_EMAIL',
                    'idToken': id_token
                }
                response_oob_code = requests.post(firebase_send_oob_code_url, json=oob_data, headers=headers)
                
                if response_oob_code.status_code == 200:
                    confirmation_url = get_confirmation_link(email)
                    if confirmation_url:
                        login_data = {
                            'email': email,
                            'password': password,
                            'returnSecureToken': True
                        }
                        login_datafirst = {
                            'uuid': uuid,
                            'email': email
                        }
                        af = requests.post("https://workshop.simsimi.com/api/user", json=login_datafirst, headers=headers)
                        login_response = requests.post(firebase_login_url, json=login_data, headers=headers)
                        
                        if login_response.status_code == 200:
                            id_token = login_response.json().get('idToken')
                            if id_token:
                                set_name = names.get_first_name() + str(randint(100, 999))
                                set_comp = "crut" + str(randint(100, 999))
                                suid = str(uuid)
                                setup_data = {
                                    "uuid": suid,
                                    "username": set_name,
                                    "mailing": 0,
                                    "company": set_comp,
                                    "country": "dz",
                                    "industryCategory": "ic_professional",
                                    "organizationSize": "os_999",
                                    "jobRole": "jr_sales",
                                    "devSkill": "",
                                    "platform": "",
                                    "botDescription": ""
                                }

                                setup_headers = {
                                    'authority': 'workshop.simsimi.com',
                                    'Content-Type': 'application/json',
                                    'Origin': 'https://workshop.simsimi.com',
                                    'Referer': 'https://workshop.simsimi.com/en/settings'
                                }
                                sleep(10)
                                setup_response = requests.put('https://workshop.simsimi.com/api/user', json=setup_data, headers=setup_headers)
                                if setup_response.status_code == 200:
                                    response_data = setup_response.json()
                                    sleep(10)
                                    res = requests.get(f"https://workshop.simsimi.com/api/project?uuid={uuid}")
                                    if res.status_code == 200:
                                        data = res.json()
                                        api_key = data[0]['apiKey']
                                        puid = data[0]['puid']
                                        put_url = 'https://workshop.simsimi.com/api/project/enable'
                                        data = {'puid': puid}
                                        response = requests.put(put_url, json=data)

                                        if response:
                                            print(f'Done(active):\napiKey: {api_key},\nemail: {email},\npassword: {password}')

                                    else:
                                        print(f"GET request failed with status code: {res.status_code}")
                                        print(res.text)
                                else:
                                    print(f"Gagal mengatur akun. Status code: {setup_response.status_code}")

                            else:
                                print(f"Gagal login. Status code: {login_response.status_code}")
                        else:
                            print(f'Gagal mengirim permintaan tautan konfirmasi. Status code: {response_oob_code.status_code}')
                            print(response_oob_code.text)
                    else:
                        print(f'Gagal mendapatkan informasi akun. Status code: {response_account_info.status_code}')
                        print(response_account_info.text)
                else:
                    print(f'Gagal mendapatkan informasi akun. Status code: {response_account_info.status_code}')
                    print(response_account_info.text)
            else:
                print('Token tidak ditemukan dalam respons registrasi.')
        else:
            print('Token tidak ditemukan dalam respons registrasi.')
    else:
        print(f'Registrasi gagal dengan status code: {response_signup.status_code}')
        print(response_signup.text)


create_account()
