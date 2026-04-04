import os
import json
import time
import requests
import asyncio
import concurrent.futures
import aiohttp
from flask import Flask, jsonify, request, Response
from byte import encrypt_api, Encrypt_ID
from visit_count_pb2 import Info
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ==========================================
# গেম এবং ভিজিট কনফিগারেশন
# ==========================================
CLIENT_VERSION = "1.120.1"
CLIENT_VERSION_CODE = "2019119621"
UNITY_VERSION = "2018.4.11f1"
RELEASE_VERSION = "OB52"
MSDK_VERSION = "5.5.2P3"
USER_AGENT_MODEL = "ASUS_Z01QD"
ANDROID_OS_VERSION = "Android 10"

VISITS_PER_TOKEN = 1000
# ==========================================

app = Flask(__name__)

# =========================================================
# 🌐 ROOT ROUTE: API GUIDE & DEVELOPER CREDIT
# =========================================================
@app.route('/', methods=['GET'])
def index():
    guide_data = {
        "Developer": "Riduanul Islam",
        "TelegramBot": "https://t.me/RiduanFFBot",
        "TelegramChannel": "https://t.me/RiduanOfficialBD",
        "Project": "Free Fire Profile Visit API",
        "Message": "Welcome to Profile Visit API",
        "API_Usage_Guide": {
            "API_Format": {
                "Send_Visits": "/[Server_Name]/[Player_UID]"
            },
            "Examples": {
                "BD_Server": "/BD/1234567890",
                "IND_Server": "/IND/9876543210"
            }
        }
    }
    return Response(json.dumps(guide_data, sort_keys=False), mimetype='application/json'), 200

# =========================================================
# 🔐 AUTO LOGIN & TOKEN GENERATOR MANAGER
# =========================================================

LOGIN_HEX_KEY = "32656534343831396539623435393838343531343130363762323831363231383734643064356437616639643866376530306331653534373135623764316533"
LOGIN_CLIENT_KEY = bytes.fromhex(LOGIN_HEX_KEY)

# ৫ ঘণ্টা = 5 * 60 * 60 = 18000 সেকেন্ড
TOKEN_REFRESH_INTERVAL = 18000 
# Vercel এ শুধুমাত্র /tmp ডিরেক্টরিতে রাইট পারমিশন থাকে
TOKEN_CACHE_FILE = "/tmp/tokens_cache.json"

REGION_LANG = {
    "ME": "ar", "IND": "hi", "ID": "id", "VN": "vi", "TH": "th", 
    "BD": "bn", "PK": "ur", "TW": "zh", "CIS": "ru", "SAC": "es", 
    "BR": "pt", "SG": "en", "NA": "en"
}

def perform_login(uid, password, region):
    """Logs in to Garena Guest Account to retrieve Access Token via UID & Password"""
    try:
        ua_login = f"GarenaMSDK/{MSDK_VERSION}({USER_AGENT_MODEL};{ANDROID_OS_VERSION};en;US;)"
        url_grant = "https://100067.connect.garena.com/oauth/guest/token/grant"
        headers_grant = {
            "User-Agent": ua_login, 
            "Content-Type": "application/x-www-form-urlencoded"
        }
        body_grant = {
            "uid": uid, 
            "password": password, 
            "response_type": "token", 
            "client_type": "2", 
            "client_secret": LOGIN_CLIENT_KEY, 
            "client_id": "100067"
        }
        
        resp_grant = requests.post(url_grant, headers=headers_grant, data=body_grant, timeout=10, verify=False)
        data_grant = resp_grant.json()

        if 'access_token' not in data_grant:
            return None
            
        access_token, open_id = data_grant['access_token'], data_grant['open_id']

        if region in ["ME", "TH"]: 
            url_login = "https://loginbp.common.ggbluefox.com/MajorLogin"
            host = "loginbp.common.ggbluefox.com"
        else: 
            url_login = "https://loginbp.ggblueshark.com/MajorLogin"
            host = "loginbp.ggblueshark.com"
            
        lang = REGION_LANG.get(region, "en")
        
        binary_head = b'\x1a\x132025-08-30 05:19:21"\tfree fire(\x01:\x081.120.13B2Android OS 9 / API-28 (PI/rel.cjw.20220518.114133)J\x08HandheldR\nATM MobilsZ\x04WIFI`\xb6\nh\xee\x05r\x03300z\x1fARMv7 VFPv3 NEON VMH | 2400 | 2\x80\x01\xc9\x0f\x8a\x01\x0fAdreno (TM) 640\x92\x01\rOpenGL ES 3.2\x9a\x01+Google|dfa4ab4b-9dc4-454e-8065-e70c733fa53f\xa2\x01\x0e105.235.139.91\xaa\x01\x02'
        binary_tail = b'\xb2\x01 1d8ec0240ede109973f3321b9354b44d\xba\x01\x014\xc2\x01\x08Handheld\xca\x01\x10Asus ASUS_I005DA\xea\x01@afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390\xf0\x01\x01\xca\x02\nATM Mobils\xd2\x02\x04WIFI\xca\x03 7428b253defc164018c604a1ebbfebdf\xe0\x03\xa8\x81\x02\xe8\x03\xf6\xe5\x01\xf0\x03\xaf\x13\xf8\x03\x84\x07\x80\x04\xe7\xf0\x01\x88\x04\xa8\x81\x02\x90\x04\xe7\xf0\x01\x98\x04\xa8\x81\x02\xc8\x04\x01\xd2\x04=/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/lib/arm\xe0\x04\x01\xea\x04_2087f61c19f57f2af4e7feff0b24d9d9|/data/app/com.dts.freefireth-PdeDnOilCSFn37p1AH_FLg==/base.apk\xf0\x04\x03\xf8\x04\x01\x8a\x05\x0232\x9a\x05\n2019119621\xb2\x05\tOpenGLES2\xb8\x05\xff\x7f\xc0\x05\x04\xe0\x05\xf3F\xea\x05\x07android\xf2\x05pKqsHT5ZLWrYljNb5Vqh//yFRlaPHSO9NWSQsVvOmdhEEn7W+VHNUK+Q+fduA3ptNrGB0Ll0LRz3WW0jOwesLj6aiU7sZ40p8BfUE/FI/jzSTwRe2\xf8\x05\xfb\xe4\x06\x88\x06\x01\x90\x06\x01\x9a\x06\x014\xa2\x06\x014\xb2\x06"GQ@O\x00\x0e^\x00D\x06UA\x0ePM\r\x13hZ\x07T\x06\x0cm\\V\x0ejYV;\x0bU5'
        
        full_payload = binary_head + lang.encode("ascii") + binary_tail
        temp_data = full_payload.replace(b'afcfbf13334be42036e4f742c80b956344bed760ac91b3aff9b607a610ab4390', access_token.encode())
        temp_data = temp_data.replace(b'1d8ec0240ede109973f3321b9354b44d', open_id.encode())
        
        final_body = bytes.fromhex(encrypt_api(temp_data.hex()))
        
        headers_login = {
            "User-Agent": f"Dalvik/2.1.0 (Linux; U; {ANDROID_OS_VERSION}; {USER_AGENT_MODEL} Build/PI)", 
            "Content-Type": "application/x-www-form-urlencoded", 
            "Host": host, 
            "X-GA": "v1 1", 
            "ReleaseVersion": RELEASE_VERSION
        }
        
        resp_login = requests.post(url_login, headers=headers_login, data=final_body, verify=False, timeout=15)
        
        if "eyJ" in resp_login.text:
            token = resp_login.text[resp_login.text.find("eyJ"):]
            end = token.find(".", token.find(".") + 1)
            final_token = token[:end + 44] if end != -1 else token
            return final_token
        return None
    except Exception:
        return None

class AccountManager:
    def __init__(self):
        self.accounts_cache = {}
        self.server_lists = {}
        self.load_token_cache_from_file()

    def load_token_cache_from_file(self):
        """Loads cached tokens from the JSON file."""
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    self.accounts_cache = json.load(f)
            except Exception:
                pass

    def save_token_cache_to_file(self):
        """Saves current tokens to the JSON file."""
        try:
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump(self.accounts_cache, f, indent=4)
        except Exception:
            pass

    def load_accounts(self, server_name="BD"):
        if server_name == "IND": fname = "Accounts.ind.json"
        elif server_name in ["BR", "US", "SAC", "NA"]: fname = "Accounts.br.json"
        else: fname = "Accounts.bd.json"

        try:
            if not os.path.exists(fname):
                return 0
                
            with open(fname, "r") as f:
                data = json.load(f)
                self.server_lists[server_name] = []
                for acc in data:
                    uid = str(acc.get("uid"))
                    pwd = acc.get("password")
                    if uid and pwd:
                        if uid not in self.accounts_cache:
                            self.accounts_cache[uid] = {"password": pwd, "token": None, "token_time": 0}
                        self.server_lists[server_name].append(uid)
            return len(self.server_lists[server_name])
        except Exception:
            return 0

    def generate_token_for_uid(self, uid, region):
        """Helper function for threading to login a single account."""
        account = self.accounts_cache.get(uid)
        if not account: return
        
        new_token = perform_login(uid, account["password"], region)
        if new_token:
            self.accounts_cache[uid]["token"] = new_token
            self.accounts_cache[uid]["token_time"] = time.time()

    def generate_tokens_for_uids(self, uids, server_name):
        """Generates tokens for specific accounts concurrently."""
        if not uids: return
        # স্পিড বাড়ানোর জন্য max_workers 100 করা হয়েছে
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            futures = [executor.submit(self.generate_token_for_uid, uid, server_name) for uid in uids]
            concurrent.futures.wait(futures)
        self.save_token_cache_to_file()

    def get_valid_tokens_batch(self, server_name):
        """Returns a list of valid tokens, generates on the fly if expired."""
        uids = self.server_lists.get(server_name, [])
        if not uids:
            self.load_accounts(server_name)
            uids = self.server_lists.get(server_name, [])
        
        valid_tokens = []
        expired_uids = []
        current_time = time.time()
        
        for uid in uids:
            account = self.accounts_cache.get(uid)
            if account and account.get("token"):
                if current_time - account.get("token_time", 0) < TOKEN_REFRESH_INTERVAL:
                    valid_tokens.append(account["token"])
                else:
                    expired_uids.append(uid)
            else:
                expired_uids.append(uid)
                
        # যদি মেয়াদ উত্তীর্ণ বা নতুন অ্যাকাউন্ট থাকে, দ্রুত জেনারেট করে নিবে
        if expired_uids:
            self.generate_tokens_for_uids(expired_uids, server_name)
            for uid in expired_uids:
                acc = self.accounts_cache.get(uid)
                if acc and acc.get("token"):
                    valid_tokens.append(acc["token"])
                    
        return valid_tokens

acc_manager = AccountManager()

# =========================================================
# API & VISIT LOGIC
# =========================================================

def get_url(server_name):
    if server_name == "IND":
        return "https://client.ind.freefiremobile.com/GetPlayerPersonalShow"
    elif server_name in {"BR", "US", "SAC", "NA"}:
        return "https://client.us.freefiremobile.com/GetPlayerPersonalShow"
    else:
        return "https://clientbp.ggblueshark.com/GetPlayerPersonalShow"

def parse_protobuf_response(response_data):
    try:
        info = Info()
        info.ParseFromString(response_data)
        
        player_data = {
            "uid": info.AccountInfo.UID if info.AccountInfo.UID else 0,
            "nickname": info.AccountInfo.PlayerNickname if info.AccountInfo.PlayerNickname else "",
            "likes": info.AccountInfo.Likes if info.AccountInfo.Likes else 0,
            "region": info.AccountInfo.PlayerRegion if info.AccountInfo.PlayerRegion else "",
            "level": info.AccountInfo.Levels if info.AccountInfo.Levels else 0
        }
        return player_data
    except Exception:
        return None

async def visit(session, url, token, uid, data):
    headers = {
        "ReleaseVersion": RELEASE_VERSION,
        "X-GA": "v1 1",
        "Authorization": f"Bearer {token}",
        "Host": url.replace("https://", "").split("/")[0],
        "User-Agent": f"Dalvik/2.1.0 (Linux; U; {ANDROID_OS_VERSION}; {USER_AGENT_MODEL} Build/QKQ1.190825.002)"
    }
    try:
        async with session.post(url, headers=headers, data=data, ssl=False) as resp:
            if resp.status == 200:
                response_data = await resp.read()
                return True, response_data
            else:
                return False, None
    except Exception:
        return False, None

async def process_visits(tokens, uid, server_name, target_requests):
    url = get_url(server_name)
    connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
    
    # স্পিড বাড়ানোর জন্য কনকারেন্সি লিমিট 2000 করা হয়েছে
    sem = asyncio.Semaphore(2000) 
    
    total_success = 0
    player_info = None

    async with aiohttp.ClientSession(connector=connector) as session:
        encrypted = encrypt_api("08" + Encrypt_ID(str(uid)) + "1801")
        data = bytes.fromhex(encrypted)

        async def sem_visit(token):
            async with sem:
                return await visit(session, url, token, uid, data)

        tasks = [
            asyncio.create_task(sem_visit(tokens[i % len(tokens)]))
            for i in range(target_requests)
        ]
        
        results = await asyncio.gather(*tasks)
        
        for success, response in results:
            if success:
                total_success += 1
                if player_info is None and response is not None:
                    player_info = parse_protobuf_response(response)

    return total_success, target_requests, player_info

@app.route('/<string:server>/<int:uid>', methods=['GET'])
def send_visits(server, uid):
    server = server.upper()
    
    tokens = acc_manager.get_valid_tokens_batch(server)

    if not tokens:
        return jsonify({"error": "❌ No valid tokens could be generated. Check accounts."}), 500

    total_accounts = len(tokens)
    target_requests = total_accounts * VISITS_PER_TOKEN 

    total_success, total_sent, player_info = asyncio.run(
        process_visits(tokens, uid, server, target_requests)
    )

    if player_info:
        response_data = {
            "Developer": "Riduanul Islam",
            "TelegramBot": "https://t.me/RiduanFFBot",
            "TelegramChannel": "https://t.me/RiduanOfficialBD",
            "nickname": player_info.get("nickname", ""),
            "uid": player_info.get("uid", 0),
            "level": player_info.get("level", 0),
            "likes": player_info.get("likes", 0),
            "region": player_info.get("region", ""),
            "target_requested": target_requests,
            "success": total_success,
            "fail": total_sent - total_success,
            "total_accounts_used": total_accounts            
        }
        return Response(json.dumps(response_data, sort_keys=False), mimetype='application/json'), 200
    else:
        return jsonify({"error": "Could not decode player information. Check UID or token validity."}), 500

if __name__ == "__main__":
    acc_manager.load_accounts("BD") 
    app.run(host="0.0.0.0", port=5090)
