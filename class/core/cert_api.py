# coding:utf-8

import re
import fcntl
import datetime
import binascii
import hashlib
import base64
import json
import time
import os
import sys
import argparse

if os.path.exists('/home/slemp/server/panel'):
    os.chdir('/home/slemp/server/panel')

import slemp

try:
    import OpenSSL
except:
    slemp.execShell("pip install pyopenssl")
    import OpenSSL


def echoErr(msg):
    writeLog("\033[31m=" * 65)
    writeLog("|-Error：{}\033[0m".format(msg))
    exit()


def writeLog(log_str, mode="ab+"):
    if __name__ == "__main__":
        print(log_str)
        return
    _log_file = 'logs/letsencrypt.log'
    f = open(_log_file, mode)
    log_str += "\n"
    f.write(log_str.encode('utf-8'))
    f.close()
    return True


class cert_api:
    __debug = False
    __user_agent = "SLEMP-Panel"
    __apis = None
    __url = None
    __replay_nonce = None
    __acme_timeout = 30
    __max_check_num = 5
    __wait_time = 5
    __bits = 2048
    __digest = "sha256"
    __verify = False
    __config = {}
    __dns_class = None
    __auto_wildcard = False
    __mod_index = {True: "Staging", False: "Production"}
    __save_path = 'data/letsencrypt'
    __cfg_file = 'data/letsencrypt.json'

    def __init__(self):
        self.__user_agent = 'SLEMP-Panel:' + slemp.getRandomString(8)
        self.__save_path = slemp.getServerDir() + '/web_conf/letsencrypt'
        if not os.path.exists(self.__save_path):
            os.makedirs(self.__save_path)
        if self.__debug:
            self.__url = 'https://acme-staging-v02.api.letsencrypt.org/directory'
        else:
            self.__url = 'https://acme-v02.api.letsencrypt.org/directory'
        self.__config = self.readConfig()

    def D(self, name, val):
        if self.__debug:
            print('---------{} start--------'.format(name))
            print(val)
            print('---------{} end--------'.format(name))

    def readConfig(self):
        if not os.path.exists(self.__cfg_file):
            self.__config['orders'] = {}
            self.__config['account'] = {}
            self.__config['apis'] = {}
            self.__config['email'] = slemp.M('users').where(
                'id=?', (1,)).getField('email')
            if self.__config['email'] in ['dentix.id@gmail.com']:
                self.__config['email'] = None
            self.saveConfig()
            return self.__config
        tmp_config = slemp.readFile(self.__cfg_file)
        if not tmp_config:
            return self.__config
        try:
            self.__config = json.loads(tmp_config)
        except:
            self.saveConfig()
            return self.__config
        return self.__config

    def saveConfig(self):
        fp = open(self.__cfg_file, 'w+')
        fcntl.flock(fp, fcntl.LOCK_EX)
        fp.write(json.dumps(self.__config))
        fcntl.flock(fp, fcntl.LOCK_UN)
        fp.close()
        return True

    def createCertCron(self):
        try:
            import crontab_api
            api = crontab_api.crontab_api()

            echo = slemp.md5(slemp.md5('panel_renew_lets_cron'))
            cron_id = slemp.M('crontab').where('echo=?', (echo,)).getField('id')

            cron_path = slemp.getServerDir() + '/cron'
            if not os.path.exists(cron_path):
                slemp.execShell('mkdir -p ' + cron_path)

            shell = 'python3 -u {}/class/core/cert_api.py --renew=1'.format(
                slemp.getRunDir())

            logs_file = cron_path + '/' + echo + '.log'

            cmd = '''#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

dst_dir=%s
logs_file=%s
cd $dst_dir

if [ -f bin/activate ];then
    source bin/activate
fi

''' % (slemp.getRunDir(), logs_file)
            cmd += 'echo "★【`date +"%Y-%m-%d %H:%M:%S"`】 STSRT★" >> $logs_file' + "\n"
            cmd += 'echo ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>" >> $logs_file' + "\n"
            cmd += 'cd $dst_dir && ' + shell + ' >> $logs_file 2>&1' + "\n"
            cmd += 'echo "【`date +"%Y-%m-%d %H:%M:%S"`】 END★" >> $logs_file' + "\n"
            cmd += 'echo "<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<" >> $logs_file' + "\n"

            file = cron_path + '/' + echo

            if type(cron_id) != int:

                slemp.writeFile(file, cmd)
                slemp.execShell('chmod 750 ' + file)

                info = {}
                info['type'] = 'day'
                info['minute'] = '10'
                info['hour'] = '0'
                shell_cron, rinfo, name = api.getCrondCycle(info)
                shell_cron += ' ' + cron_path + '/' + echo + \
                    ' >> ' + logs_file + ' 2>&1'

                api.writeShell(shell_cron)

                insert_id = slemp.M('crontab').add('name,type,where1,where_hour,where_minute,echo,addtime,status,save,backup_to,stype,sname,sbody,urladdress', (
                    "[Do not delete] Renew Let's Encrypt certificate", 'day', '', '0', '10', echo, time.strftime('%Y-%m-%d %X', time.localtime()), '1', '', 'localhost', 'toShell', '', cmd, ''))

                if insert_id > 0:
                    print('Create certificate auto-renewal task successfully!')
            else:
                slemp.writeFile(file, cmd)
                slemp.execShell('chmod 750 ' + file)
                slemp.M('crontab').where('id=?', (cron_id)).save('sbody', (cmd,))
        except Exception as e:
            print(slemp.getTracebackInfo())

    def getApis(self):
        if not self.__apis:
            api_index = self.__mod_index[self.__debug]
            if not 'apis' in self.__config:
                self.__config['apis'] = {}

            if api_index in self.__config['apis']:
                if 'expires' in self.__config['apis'][api_index] and 'directory' in self.__config['apis'][api_index]:
                    if time.time() < self.__config['apis'][api_index]['expires']:
                        self.__apis = self.__config[
                            'apis'][api_index]['directory']
                        return self.__apis

            try:
                res = slemp.httpGet(self.__url)
                result = json.loads(res)
                self.__apis = {}
                self.__apis['newAccount'] = result['newAccount']
                self.__apis['newNonce'] = result['newNonce']
                self.__apis['newOrder'] = result['newOrder']
                self.__apis['revokeCert'] = result['revokeCert']
                self.__apis['keyChange'] = result['keyChange']

                self.__config['apis'][api_index] = {}
                self.__config['apis'][api_index]['directory'] = self.__apis
                self.__config['apis'][api_index]['expires'] = time.time() + \
                    86400
                self.saveConfig()
            except Exception as e:
                raise Exception(
                    'The service is closed due to maintenance or an internal error occurs, check <a href="https://letsencrypt.status.io/" target="_blank" class="btlink">https://letsencrypt.status.io/</ a> for more details.')
        return self.__apis

    def stringfyItems(self, payload):
        if isinstance(payload, str):
            return payload

        for k, v in payload.items():
            if isinstance(k, bytes):
                k = k.decode("utf-8")
            if isinstance(v, bytes):
                v = v.decode("utf-8")
            payload[k] = v
        return payload

    def formatDomains(self, domains):
        if type(domains) != list:
            return []
        if self.__auto_wildcard:
            domains = self.autoWildcard(domains)
        wildcard = []
        tmp_domains = []
        for domain in domains:
            domain = domain.strip()
            if domain in tmp_domains:
                continue
            f_index = domain.find("*.")
            if f_index not in [-1, 0]:
                continue
            if f_index == 0:
                wildcard.append(domain.replace(
                    "*", r"^[\w-]+").replace(".", r"\."))
            tmp_domains.append(domain)

        apply_domains = tmp_domains[:]
        for domain in tmp_domains:
            for w in wildcard:
                if re.match(w, domain):
                    apply_domains.pop(domain)

        return apply_domains

    def calculateSafeBase64(self, un_encoded_data):
        if sys.version_info[0] == 3:
            if isinstance(un_encoded_data, str):
                un_encoded_data = un_encoded_data.encode("utf8")
        r = base64.urlsafe_b64encode(un_encoded_data).rstrip(b"=")
        return r.decode("utf8")

    def createKey(self, key_type=OpenSSL.crypto.TYPE_RSA):
        key = OpenSSL.crypto.PKey()
        key.generate_key(key_type, self.__bits)
        private_key = OpenSSL.crypto.dump_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, key)
        return private_key

    def getAccountKey(self):
        if not 'account' in self.__config:
            self.__config['account'] = {}
        k = self.__mod_index[self.__debug]
        if not k in self.__config['account']:
            self.__config['account'][k] = {}

        if not 'key' in self.__config['account'][k]:
            self.__config['account'][k]['key'] = self.createKey()
            if type(self.__config['account'][k]['key']) == bytes:
                self.__config['account'][k]['key'] = self.__config[
                    'account'][k]['key'].decode()
            self.saveConfig()
        return self.__config['account'][k]['key']

    def register(self, existing=False):
        if not 'email' in self.__config:
            self.__config['email'] = 'dentix.id@gmail.com'
        if existing:
            payload = {"onlyReturnExisting": True}
        elif self.__config['email']:
            payload = {
                "termsOfServiceAgreed": True,
                "contact": ["mailto:{0}".format(self.__config['email'])],
            }
        else:
            payload = {"termsOfServiceAgreed": True}

        res = self.acmeRequest(url=self.__apis['newAccount'], payload=payload)

        if res.status not in [201, 200, 409]:
            raise Exception("Failed to register ACME account: {}".format(res.json()))
        kid = res.headers["Location"]
        return kid

    def getKid(self, force=False):
        if not 'account' in self.__config:
            self.__config['account'] = {}
        k = self.__mod_index[self.__debug]
        if not k in self.__config['account']:
            self.__config['account'][k] = {}

        if not 'kid' in self.__config['account'][k]:
            self.__config['account'][k]['kid'] = self.register()
            self.saveConfig()
            time.sleep(3)
            self.__config = self.readConfig()
        return self.__config['account'][k]['kid']

    def requestsGet(self, url, timeout):
        try:
            import urllib.request
            import ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass

            headers = {"User-Agent": self.__user_agent}
            req = urllib.request.Request(url=url, headers=headers)
            req = urllib.request.urlopen(url, timeout=timeout)
            return req
        except Exception as ex:
            raise Exception("requestsGet: {}".format(str(ex)))

    def requestsPost(self, url, data, timeout):
        try:
            import urllib.request
            import ssl
            try:
                ssl._create_default_https_context = ssl._create_unverified_context
            except:
                pass

            headers = {"User-Agent": self.__user_agent}
            headers.update({"Content-Type": "application/jose+json"})
            data = bytes(data, encoding="utf8")
            req = urllib.request.Request(
                url, data, headers=headers, method='POST')
            response = urllib.request.urlopen(req, timeout=timeout)
            return response
        except Exception as ex:

            #self.getError()
            raise Exception("requestsPost: {}".format(self.getError(str(ex))))

    def getRequestJson(self, response):
        try:
            data = response.read().decode('utf-8')
            return json.loads(data)
        except Exception as ex:
            raise Exception("getRequestJson: {}".format(str(ex)))

    def getNonce(self, force=False):
        if not self.__replay_nonce or force:
            try:
                response = self.requestsGet(
                    self.__apis['newNonce'], timeout=self.__acme_timeout)
                self.__replay_nonce = response.headers["replay-nonce"]
            except Exception as e:
                raise Exception("Failed to get random number: {}".format(str(e)))

        return self.__replay_nonce

    def getAcmeHeader(self, url):
        nonce = self.getNonce()

        header = {"alg": "RS256", "nonce": nonce, "url": url}
        if url in [self.__apis['newAccount'], 'GET_THUMBPRINT']:
            from cryptography.hazmat.backends import default_backend
            from cryptography.hazmat.primitives import serialization
            private_key = serialization.load_pem_private_key(
                self.getAccountKey().encode(),
                password=None,
                backend=default_backend(),
            )
            public_key_public_numbers = private_key.public_key().public_numbers()

            exponent = "{0:x}".format(public_key_public_numbers.e)
            exponent = "0{0}".format(exponent) if len(
                exponent) % 2 else exponent
            modulus = "{0:x}".format(public_key_public_numbers.n)
            jwk = {
                "kty": "RSA",
                "e": self.calculateSafeBase64(binascii.unhexlify(exponent)),
                "n": self.calculateSafeBase64(binascii.unhexlify(modulus)),
            }
            header["jwk"] = jwk
        else:
            header["kid"] = self.getKid()
        return header

    def signMessage(self, message):
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.getAccountKey().encode())
        return OpenSSL.crypto.sign(pk, message.encode("utf8"), self.__digest)

    def getSiteRunPathByid(self, site_id):
        if slemp.M('sites').where('id=?', (site_id,)).count() >= 1:
            site_path = slemp.M('sites').where('id=?', site_id).getField('path')
            if not site_path:
                return None
            if not os.path.exists(site_path):
                return None
            args = slemp.dict_obj()
            args.id = site_id
            import panelSite
            run_path = panelSite.panelSite().GetRunPath(args)
            if run_path in ['/']:
                run_path = ''
            if run_path:
                if run_path[0] == '/':
                    run_path = run_path[1:]
            site_run_path = os.path.join(site_path, run_path)
            if not os.path.exists(site_run_path):
                return site_path
            return site_run_path
        else:
            return False

    def getSiteRunPath(self, domains):
        site_id = 0
        for domain in domains:
            site_id = slemp.M('domain').where("name=?", domain).getField('pid')
            if site_id:
                break

        if not site_id:
            return None
        return self.getSiteRunPathByid(site_id)

    def clearAuthFile(self, index):
        if not self.__config['orders'][index]['auth_type'] in ['http', 'tls']:
            return True
        acme_path = '{}/.well-known/acme-challenge'.format(
            self.__config['orders'][index]['auth_to'])
        writeLog("|-Verify directory：{}".format(acme_path))
        if os.path.exists(acme_path):
            slemp.execShell("rm -f {}/*".format(acme_path))

        acme_path = slemp.getServerDir() + '/stop/.well-known/acme-challenge'
        if os.path.exists(acme_path):
            slemp.execShell("rm -f {}/*".format(acme_path))

    def getAuthType(self, index):
        if not index in self.__config['orders']:
            raise Exception('The specified order does not exist!')
        s_type = 'http-01'
        if 'auth_type' in self.__config['orders'][index]:
            if self.__config['orders'][index]['auth_type'] == 'dns':
                s_type = 'dns-01'
            elif self.__config['orders'][index]['auth_type'] == 'tls':
                s_type = 'tls-alpn-01'
            else:
                s_type = 'http-01'
        return s_type

    def getIdentifierAuth(self, index, url, auth_info):
        s_type = self.getAuthType(index)
        writeLog("|-Authentication type：{}".format(s_type))
        domain = auth_info['identifier']['value']
        wildcard = False

        if 'wildcard' in auth_info:
            wildcard = auth_info['wildcard']
        if wildcard:
            domain = "*." + domain

        for auth in auth_info['challenges']:
            if auth['type'] != s_type:
                continue
            identifier_auth = {
                "domain": domain,
                "url": url,
                "wildcard": wildcard,
                "token": auth['token'],
                "dns_challenge_url": auth['url'],
            }
            return identifier_auth
        return None

    def getKeyauthorization(self, token):
        acme_header_jwk_json = json.dumps(
            self.getAcmeHeader("GET_THUMBPRINT")["jwk"], sort_keys=True, separators=(",", ":")
        )
        acme_thumbprint = self.calculateSafeBase64(
            hashlib.sha256(acme_header_jwk_json.encode("utf8")).digest()
        )
        acme_keyauthorization = "{0}.{1}".format(token, acme_thumbprint)
        base64_of_acme_keyauthorization = self.calculateSafeBase64(
            hashlib.sha256(acme_keyauthorization.encode("utf8")).digest()
        )

        return acme_keyauthorization, base64_of_acme_keyauthorization

    def writeAuthFile(self, auth_to, token, acme_keyauthorization):
        try:
            # self.D('writeAuthFile', auth_to)
            acme_path = '{}/.well-known/acme-challenge'.format(auth_to)
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                slemp.setOwn(acme_path, 'www')
            wellknown_path = '{}/{}'.format(acme_path, token)
            slemp.writeFile(wellknown_path, acme_keyauthorization)
            slemp.setOwn(wellknown_path, 'www')

            acme_path = slemp.getServerDir() + '/stop/.well-known/acme-challenge'
            if not os.path.exists(acme_path):
                os.makedirs(acme_path)
                slemp.setOwn(acme_path, 'www')
            wellknown_path = '{}/{}'.format(acme_path, token)
            slemp.writeFile(wellknown_path, acme_keyauthorization)
            slemp.setOwn(wellknown_path, 'www')
            return True
        except:
            err = slemp.getTracebackInfo()
            raise Exception("Failed to write verification file: {}".format(err))

    def setAuthInfo(self, identifier_auth):

        if identifier_auth['auth_to'] == 'dns':
            return None

        if identifier_auth['type'] in ['http', 'tls']:
            self.writeAuthFile(identifier_auth['auth_to'], identifier_auth[
                               'token'], identifier_auth['acme_keyauthorization'])

    def getAuths(self, index):
        if not index in self.__config['orders']:
            raise Exception('The specified order does not exist!')

        if 'auths' in self.__config['orders'][index]:
            if time.time() < self.__config['orders'][index]['auths'][0]['expires']:
                return self.__config['orders'][index]['auths']
        if self.__config['orders'][index]['auth_type'] != 'dns':
            site_run_path = self.getSiteRunPath(
                self.__config['orders'][index]['domains'])
            if site_run_path:
                self.__config['orders'][index]['auth_to'] = site_run_path

        self.clearAuthFile(index)

        auths = []
        for auth_url in self.__config['orders'][index]['authorizations']:
            res = self.acmeRequest(auth_url, "")
            if res.status not in [200, 201]:
                raise Exception("Failed to obtain authorization: {}".format(res.json()))

            s_body = self.getRequestJson(res)
            if 'status' in s_body:
                if s_body['status'] in ['invalid']:
                    raise Exception("Invalid order, this order is currently in a verification failure state!")
                if s_body['status'] in ['valid']:
                    continue

            s_body['expires'] = self.utcToTime(s_body['expires'])
            identifier_auth = self.getIdentifierAuth(index, auth_url, s_body)
            if not identifier_auth:
                raise Exception("Authentication information construction failed!{}")

            acme_keyauthorization, auth_value = self.getKeyauthorization(identifier_auth[
                                                                         'token'])
            identifier_auth['acme_keyauthorization'] = acme_keyauthorization
            identifier_auth['auth_value'] = auth_value
            identifier_auth['expires'] = s_body['expires']
            identifier_auth['auth_to'] = self.__config[
                'orders'][index]['auth_to']
            identifier_auth['type'] = self.__config[
                'orders'][index]['auth_type']

            # print(identifier_auth)
            self.setAuthInfo(identifier_auth)
            auths.append(identifier_auth)
        self.__config['orders'][index]['auths'] = auths
        self.saveConfig()
        return auths

    def updateReplayNonce(self, res):
        replay_nonce = res.headers.get('replay-nonce')
        if replay_nonce:
            self.__replay_nonce = replay_nonce

    def acmeRequest(self, url, payload):
        headers = {"User-Agent": self.__user_agent}
        payload = self.stringfyItems(payload)

        if payload == "":
            payload64 = payload
        else:
            payload64 = self.calculateSafeBase64(json.dumps(payload))
        protected = self.getAcmeHeader(url)
        protected64 = self.calculateSafeBase64(json.dumps(protected))
        signature = self.signMessage(
            message="{0}.{1}".format(protected64, payload64))  # bytes
        signature64 = self.calculateSafeBase64(signature)  # str
        data = json.dumps({
            "protected": protected64,
            "payload": payload64,
            "signature": signature64
        })

        headers.update({"Content-Type": "application/jose+json"})
        response = self.requestsPost(
            url, data=data, timeout=self.__acme_timeout)
        self.updateReplayNonce(response)
        return response

    def utcToTime(self, utc_string):
        try:
            utc_string = utc_string.split('.')[0]
            utc_date = datetime.datetime.strptime(
                utc_string, "%Y-%m-%dT%H:%M:%S")
            return int(time.mktime(utc_date.timetuple())) + (3600 * 8)
        except:
            return int(time.time() + 86400 * 7)

    def saveOrder(self, order_object, index):
        if not 'orders' in self.__config:
            self.__config['orders'] = {}
        renew = False
        if not index:
            index = slemp.md5(json.dumps(order_object['identifiers']))
        else:
            renew = True
            order_object['certificate_url'] = self.__config[
                'orders'][index]['certificate_url']
            order_object['save_path'] = self.__config[
                'orders'][index]['save_path']

        order_object['expires'] = self.utcToTime(order_object['expires'])
        self.__config['orders'][index] = order_object
        self.__config['orders'][index]['index'] = index
        if not renew:
            self.__config['orders'][index]['create_time'] = int(time.time())
            self.__config['orders'][index]['renew_time'] = 0
        self.saveConfig()
        return index

    def getError(self, error):
        if error.find("Max checks allowed") >= 0:
            return "The CA cannot verify your domain name, please check whether the domain name resolution is correct, or wait for 5-10 minutes and try again."
        elif error.find("Max retries exceeded with") >= 0 or error.find('status_code=0 ') != -1:
            return "CA server connection timed out, please try again later."
        elif error.find("The domain name belongs") >= 0:
            return "The domain name does not belong to this DNS service provider, please ensure that the domain name is filled in correctly."
        elif error.find('login token ID is invalid') >= 0:
            return 'DNS server connection failed, please check if the key is correct.'
        elif error.find('Error getting validation data') != -1:
            return 'Data validation failed, the CA could not get the correct verification code from the verification connection.'
        elif "too many certificates already issued for exact set of domains" in error:
            return 'Issuance failed, the domain name %s has exceeded the weekly re-issuance limit!' % re.findall("exact set of domains: (.+):", error)
        elif "Error creating new account :: too many registrations for this IP" in error:
            return 'Issuance failed, the current server IP has reached the limit of creating 10 accounts every 3 hours.'
        elif "DNS problem: NXDOMAIN looking up A for" in error:
            return 'The verification failed, the domain name was not resolved, or the resolution did not take effect!'
        elif "Invalid response from" in error:
            return 'Verification failed, domain name resolution error or verification URL cannot be accessed!'
        elif error.find('TLS Web Server Authentication') != -1:
            return "Failed to connect to CA server, please try again later."
        elif error.find('Name does not end in a public suffix') != -1:
            return "The domain name %s is not supported, please check whether the domain name is correct!" % re.findall("Cannot issue for \"(.+)\":", error)
        elif error.find('No valid IP addresses found for') != -1:
            return "The domain name %s did not find a resolution record, please check whether the resolution of the domain name is valid!" % re.findall("No valid IP addresses found for (.+)", error)
        elif error.find('No TXT record found at') != -1:
            return "No valid TXT resolution record was found in the domain name %s, please check whether the TXT record is resolved correctly, if it is applied by DNSAPI, please try again in 10 minutes!" % re.findall("No TXT record found at (.+)", error)
        elif error.find('Incorrect TXT record') != -1:
            return "An incorrect TXT record was found on %s: %s, please check whether the TXT resolution is correct, if it is applied through DNSAPI, please try again in 10 minutes!" % (re.findall("found at (.+)", error), re.findall("Incorrect TXT record \"(.+)\"", error))
        elif error.find('Domain not under you or your user') != -1:
            return "This domain name does not exist under this dnspod account, adding and parsing failed!"
        elif error.find('SERVFAIL looking up TXT for') != -1:
            return "No valid TXT resolution record was found in the domain name %s, please check whether the TXT record is resolved correctly, if it is applied by DNSAPI, please try again in 10 minutes!" % re.findall("looking up TXT for (.+)", error)
        elif error.find('Timeout during connect') != -1:
            return "The connection timed out, and the CA server cannot access your website!"
        elif error.find("DNS problem: SERVFAIL looking up CAA for") != -1:
            return "The domain name %s is currently required to verify the CAA record, please manually resolve the CAA record, or try to apply again after 1 hour!" % re.findall("looking up CAA for (.+)", error)
        elif error.find("Read timed out.") != -1:
            return "The verification timed out. Please check whether the domain name is resolved correctly. If it is resolved correctly, the connection between the server and Let'sEncrypt may be abnormal. Please try again later!"
        elif error.find('Cannot issue for') != -1:
            return "Unable to issue a certificate for {}, cannot directly apply for a wildcard certificate with a domain name suffix!".format(re.findall(r'for\s+"(.+)"', error))
        elif error.find('too many failed authorizations recently'):
            return 'This account has failed orders more than 5 times within 1 hour, please wait 1 hour and try again!'
        elif error.find("Error creating new order") != -1:
            return "Order creation failed, please try again later!"
        elif error.find("Too Many Requests") != -1:
            return "More than 5 verification failures within 1 hour, the application is temporarily banned, please try again later!"
        elif error.find('HTTP Error 400: Bad Request') != -1:
            return "CA server denies access, please try again later!"
        elif error.find('Temporary failure in name resolution') != -1:
            return 'The server DNS is faulty, and the domain name cannot be resolved, please use the Linux toolbox to check the dns configuration'
        elif error.find('Too Many Requests') != -1:
            return 'There are too many requests for this domain name, please try again after 3 hours'
        else:
            return error

    def createOrder(self, domains, auth_type, auth_to, index=None):
        domains = self.formatDomains(domains)
        if not domains:
            raise Exception("At least one domain name is required")
        identifiers = []
        for domain_name in domains:
            identifiers.append({"type": 'dns', "value": domain_name})
        payload = {"identifiers": identifiers}

        res = self.acmeRequest(self.__apis['newOrder'], payload)
        if not res.status in [201]:
            e_body = self.getRequestJson(res)
            if 'type' in e_body:
                if e_body['type'].find('error:badNonce') != -1:
                    self.getNonce(force=True)
                    res = self.acmeRequest(self.__apis['newOrder'], payload)

                if e_body['detail'].find('KeyID header contained an invalid account URL') != -1:
                    k = self._mod_index[self.__debug]
                    del(self.__config['account'][k])
                    self.getKid()
                    self.getNonce(force=True)
                    res = self.acmeRequest(self.__apis['newOrder'], payload)
            if not res.status in [201]:
                a_auth = e_body

                ret_title = self.getError(str(a_auth))
                raise StopIteration("{0} >>>> {1}".format(
                    ret_title, json.dumps(a_auth)))

        s_json = self.getRequestJson(res)
        s_json['auth_type'] = auth_type
        s_json['domains'] = domains
        s_json['auth_to'] = auth_to
        index = self.saveOrder(s_json, index)
        return index

    def checkAuthStatus(self, url, desired_status=None):

        desired_status = desired_status or ["pending", "valid", "invalid"]
        number_of_checks = 0
        rdata = None
        while True:
            if desired_status == ['valid', 'invalid']:
                writeLog("|-Verification result of {} query..".format(number_of_checks + 1))
                time.sleep(self.__wait_time)
            check_authorization_status_response = self.acmeRequest(url, "")
            a_auth = rdata = self.getRequestJson(
                check_authorization_status_response)
            authorization_status = a_auth["status"]
            number_of_checks += 1
            if authorization_status in desired_status:
                if authorization_status == "invalid":
                    writeLog("|-Verification failed!")
                    try:
                        if 'error' in a_auth['challenges'][0]:
                            ret_title = a_auth['challenges'][
                                0]['error']['detail']
                        elif 'error' in a_auth['challenges'][1]:
                            ret_title = a_auth['challenges'][
                                1]['error']['detail']
                        elif 'error' in a_auth['challenges'][2]:
                            ret_title = a_auth['challenges'][
                                2]['error']['detail']
                        else:
                            ret_title = str(a_auth)
                        ret_title = self.getError(ret_title)
                    except:
                        ret_title = str(a_auth)
                    raise StopIteration("{0} >>>> {1}".format(
                        ret_title, json.dumps(a_auth)))
                break

            if number_of_checks == self.__max_check_num:
                raise StopIteration(
                    "Error: Authentication has been attempted {0} times. The maximum number of authentications is {1}. The authentication interval is {2} seconds.".format(
                        number_of_checks,
                        self.__max_check_num,
                        self.__wait_time
                    )
                )
        if desired_status == ['valid', 'invalid']:
            writeLog("|-Verification successful!")
        return rdata

    def respondToChallenge(self, auth):
        payload = {"keyAuthorization": "{0}".format(
            auth['acme_keyauthorization'])}
        respond_to_challenge_response = self.acmeRequest(
            auth['dns_challenge_url'], payload)
        return respond_to_challenge_response

    def checkDns(self, domain, value, s_type='TXT'):
        writeLog(
            "|-Try to verify DNS records locally, domain name: {}, type: {} record value: {}".format(domain, s_type, value))
        time.sleep(10)
        n = 0
        while n < 20:
            n += 1
            try:
                import dns.resolver
                ns = dns.resolver.query(domain, s_type)
                for j in ns.response.answer:
                    for i in j.items:
                        txt_value = i.to_text().replace('"', '').strip()
                        writeLog("|-Validation value for {}th time: {}".format(n, txt_value))
                        if txt_value == value:
                            write_log("|-Local authentication succeeded!")
                            return True
            except:
                try:
                    import dns.resolver
                except:
                    return False
            time.sleep(3)
        writeLog("|-Local authentication failed!")
        return True

    def authDomain(self, index):
        if not index in self.__config['orders']:
            raise Exception('The specified order does not exist!')

        for auth in self.__config['orders'][index]['auths']:
            res = self.checkAuthStatus(auth['url'])
            if res['status'] == 'pending':
                if auth['type'] == 'dns':
                    self.checkDns(
                        "_acme-challenge.{}".format(
                            auth['domain'].replace('*.', '')),
                        auth['auth_value'],
                        "TXT"
                    )
                self.respondToChallenge(auth)

        for i in range(len(self.__config['orders'][index]['auths'])):
            self.checkAuthStatus(self.__config['orders'][index]['auths'][i]['url'], [
                'valid', 'invalid'])
            self.__config['orders'][index]['status'] = 'valid'

    def getAltNames(self, index):
        domain_name = self.__config['orders'][index]['domains'][0]
        domain_alt_names = []
        if len(self.__config['orders'][index]['domains']) > 1:
            domain_alt_names = self.__config['orders'][index]['domains'][1:]
        return domain_name, domain_alt_names

    def createCsr(self, index):
        if 'csr' in self.__config['orders'][index]:
            return self.__config['orders']['csr']
        domain_name, domain_alt_names = self.getAltNames(index)
        X509Req = OpenSSL.crypto.X509Req()
        X509Req.get_subject().CN = domain_name
        if domain_alt_names:
            SAN = "DNS:{0}, ".format(domain_name).encode("utf8") + ", ".join(
                "DNS:" + i for i in domain_alt_names
            ).encode("utf8")
        else:
            SAN = "DNS:{0}".format(domain_name).encode("utf8")

        X509Req.add_extensions(
            [
                OpenSSL.crypto.X509Extension(
                    "subjectAltName".encode("utf8"), critical=False, value=SAN
                )
            ]
        )
        pk = OpenSSL.crypto.load_privatekey(
            OpenSSL.crypto.FILETYPE_PEM, self.createCertificateKey(
                index).encode()
        )
        X509Req.set_pubkey(pk)
        X509Req.set_version(2)
        X509Req.sign(pk, self.__digest)
        return OpenSSL.crypto.dump_certificate_request(OpenSSL.crypto.FILETYPE_ASN1, X509Req)

    def createCertificateKey(self, index):
        if 'private_key' in self.__config['orders'][index]:
            return self.__config['orders'][index]['private_key']
        private_key = self.createKey()
        if type(private_key) == bytes:
            private_key = private_key.decode()
        self.__config['orders'][index]['private_key'] = private_key
        self.saveConfig()
        return private_key

    def sendCsr(self, index):
        csr = self.createCsr(index)
        payload = {"csr": self.calculateSafeBase64(csr)}
        send_csr_response = self.acmeRequest(
            url=self.__config['orders'][index]['finalize'], payload=payload)
        send_csr_response_json = self.getRequestJson(send_csr_response)
        if send_csr_response.status not in [200, 201]:
            raise ValueError(
                "Error: Sending CSR: Response status {status_code}, Response value: {response}".format(
                    status_code=send_csr_response.status,
                    response=send_csr_response_json,
                )
            )
        certificate_url = send_csr_response_json["certificate"]
        self.__config['orders'][index]['certificate_url'] = certificate_url
        self.saveConfig()
        return certificate_url

    def strfDate(self, sdate):
        return time.strftime('%Y-%m-%d', time.strptime(sdate, '%Y%m%d%H%M%S'))

    def dumpDer(self, cert_path):
        cert = OpenSSL.crypto.load_certificate(
            OpenSSL.crypto.FILETYPE_PEM, slemp.readFile(cert_path + '/cert.csr'))
        return OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_ASN1, cert)

    def dumpPkcs12(self, key_pem=None, cert_pem=None, ca_pem=None, friendly_name=None):
        p12 = OpenSSL.crypto.PKCS12()
        if cert_pem:
            p12.set_certificate(OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cert_pem.encode()))
        if key_pem:
            p12.set_privatekey(OpenSSL.crypto.load_privatekey(
                OpenSSL.crypto.FILETYPE_PEM, key_pem.encode()))
        if ca_pem:
            p12.set_ca_certificates((OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, ca_pem.encode()),))
        if friendly_name:
            p12.set_friendlyname(friendly_name.encode())
        return p12.export()

    def splitCaData(self, cert):
        sp_key = '-----END CERTIFICATE-----\n'
        datas = cert.split(sp_key)
        return {"cert": datas[0] + sp_key, "root": sp_key.join(datas[1:])}

    def getCertInit(self, pem_file):
        if not os.path.exists(pem_file):
            return None
        try:
            result = {}
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, slemp.readFile(pem_file))
            issuer = x509.get_issuer()
            result['issuer'] = ''
            if hasattr(issuer, 'CN'):
                result['issuer'] = issuer.CN
            if not result['issuer']:
                is_key = [b'0', '0']
                issue_comp = issuer.get_components()
                if len(issue_comp) == 1:
                    is_key = [b'CN', 'CN']
                for iss in issue_comp:
                    if iss[0] in is_key:
                        result['issuer'] = iss[1].decode()
                        break
            result['notAfter'] = self.strfDate(
                bytes.decode(x509.get_notAfter())[:-1])

            result['notBefore'] = self.strfDate(
                bytes.decode(x509.get_notBefore())[:-1])

            result['dns'] = []
            for i in range(x509.get_extension_count()):
                s_name = x509.get_extension(i)
                if s_name.get_short_name() in [b'subjectAltName', 'subjectAltName']:
                    s_dns = str(s_name).split(',')
                    for d in s_dns:
                        result['dns'].append(d.split(':')[1])
            subject = x509.get_subject().get_components()

            if len(subject) == 1:
                result['subject'] = subject[0][1].decode()
            else:
                result['subject'] = result['dns'][0]
            return result
        except:
            return None

    def subAllCert(self, key_file, pem_file):
        cert_init = self.getCertInit(pem_file)
        paths = ['/home/slemp/server/panel/data/letsencrypt']
        is_panel = False
        for path in paths:
            if not os.path.exists(path):
                continue
            for p_name in os.listdir(path):
                to_path = path + '/' + p_name
                to_pem_file = to_path + '/fullchain.pem'
                to_key_file = to_path + '/privkey.pem'
                to_info = to_path + '/info.json'

                if not os.path.exists(to_pem_file):
                    if not p_name in ['ssl']:
                        continue
                    to_pem_file = to_path + '/certificate.pem'
                    to_key_file = to_path + '/privateKey.pem'
                    if not os.path.exists(to_pem_file):
                        continue
                    if path == paths[-1]:
                        is_panel = True

                to_cert_init = self.getCertInit(to_pem_file)

                try:
                    if to_cert_init['issuer'] != cert_init['issuer'] and to_cert_init['issuer'].find("Let's Encrypt") == -1 and to_cert_init['issuer'] != 'R3':
                        continue
                except:
                    continue

                if to_cert_init['notAfter'] > cert_init['notAfter']:
                    continue

                if len(to_cert_init['dns']) != len(cert_init['dns']):
                    continue
                is_copy = True
                for domain in to_cert_init['dns']:
                    if not domain in cert_init['dns']:
                        is_copy = False
                if not is_copy:
                    continue

                slemp.writeFile(to_pem_file, slemp.readFile(pem_file, 'rb'), 'wb')
                slemp.writeFile(to_key_file, slemp.readFile(key_file, 'rb'), 'wb')
                slemp.writeFile(to_info, json.dumps(cert_init))
                writeLog("|-It is detected that the certificate under {} overlaps with the certificate applied for this time, and the expiration time is earlier, it has been replaced with a new certificate!".format(to_path))
        slemp.restartWeb()

    def saveCert(self, cert, index):
        try:
            domain_name = self.__config['orders'][index]['domains'][0]
            path = self.__config['orders'][index]['save_path']
            if not os.path.exists(path):
                os.makedirs(path, 384)

            key_file = path + "/privkey.pem"
            pem_file = path + "/fullchain.pem"
            slemp.writeFile(key_file, cert['private_key'])
            slemp.writeFile(pem_file, cert['cert'] + cert['root'])
            slemp.writeFile(path + "/cert.csr", cert['cert'])
            slemp.writeFile(path + "/root_cert.csr", cert['root'])

            pfx_buffer = self.dumpPkcs12(
                cert['private_key'], cert['cert'] + cert['root'], cert['root'], domain_name)
            slemp.writeFile(path + "/fullchain.pfx", pfx_buffer, 'wb+')

            ps = '''Document Description：
privkey.pem     certificate private key
fullchain.pem   certificate in PEM format containing the certificate chain (nginx/apache)
root_cert.csr   root certificate
cert.csr        domain name certificate
fullchain.pfx   certificate format for IIS

How to use in SLEMP panel：
privkey.pem         Paste into the key input box
fullchain.pem       Paste into the certificate input box
'''
            slemp.writeFile(path + '/readme.txt', ps)
            self.subAllCert(key_file, pem_file)
        except:
            writeLog(slemp.getTracebackInfo())

    def getCertTimeout(self, cret_data):
        try:
            x509 = OpenSSL.crypto.load_certificate(
                OpenSSL.crypto.FILETYPE_PEM, cret_data)
            cert_timeout = bytes.decode(x509.get_notAfter())[:-1]
            return int(time.mktime(time.strptime(cert_timeout, '%Y%m%d%H%M%S')))
        except:
            return int(time.time() + (86400 * 90))

    def downloadCert(self, index):
        res = self.acmeRequest(
            self.__config['orders'][index]['certificate_url'], "")

        pem_certificate = res.read().decode('utf-8')
        if res.status not in [200, 201]:
            raise Exception("Failed to download certificate: {}".format(json.loads(pem_certificate)))

        cert = self.splitCaData(pem_certificate)
        cert['cert_timeout'] = self.getCertTimeout(cert['cert'])
        cert['private_key'] = self.__config['orders'][index]['private_key']
        cert['domains'] = self.__config['orders'][index]['domains']
        del(self.__config['orders'][index]['private_key'])
        del(self.__config['orders'][index]['auths'])
        del(self.__config['orders'][index]['expires'])
        del(self.__config['orders'][index]['authorizations'])
        del(self.__config['orders'][index]['finalize'])
        del(self.__config['orders'][index]['identifiers'])
        if 'cert' in self.__config['orders'][index]:
            del(self.__config['orders'][index]['cert'])
        self.__config['orders'][index]['status'] = 'valid'
        self.__config['orders'][index]['cert_timeout'] = cert['cert_timeout']
        domain_name = self.__config['orders'][index]['domains'][0]
        self.__config['orders'][index]['save_path'] = '{}/{}'.format(
            self.__save_path, domain_name)
        cert['save_path'] = self.__config['orders'][index]['save_path']
        self.saveConfig()
        self.saveCert(cert, index)
        return cert

    def applyCert(self, domains, auth_type='http', auth_to='Dns_com|None|None', args={}):
        writeLog("", "wb+")
        try:
            self.getApis()
            index = None
            if 'index' in args and args.index:
                index = args.index
            if not index:
                writeLog("|-Creating order..")
                index = self.createOrder(domains, auth_type, auth_to)
                writeLog("|-Obtaining verification information..")
                self.getAuths(index)
                if auth_to == 'dns' and len(self.__config['orders'][index]['auths']) > 0:
                    return self.__config['orders'][index]
            writeLog("|-Verifying domain name..")
            self.authDomain(index)

            writeLog("|-Sending CSR..")
            self.sendCsr(index)

            writeLog("|-Downloading certificate..")
            cert = self.downloadCert(index)

            self.saveConfig()
            cert['status'] = True
            cert['msg'] = 'Successful application!'
            writeLog("|-The application is successful and is being deployed to the site..")

            self.clearAuthFile(index)

            if os.path.exists(auth_to):
                slemp.execShell("rm -rf {}/.well-known".format(auth_to))
            return cert
        except Exception as ex:
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                writeLog(slemp.getTracebackInfo())

            cert = {}
            cert['status'] = False
            cert['msg'] = msg
            return cert

    def extractZone(self, domain_name):
        top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn', '.gov.cn', '.gs.cn',
                           '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn', '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn',
                           '.jl.cn', '.js.cn', '.jx.cn', '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn',
                           '.my.id', '.com.ac', '.com.ad', '.com.ae', '.com.af', '.com.ag', '.com.ai', '.com.al', '.com.am',
                           '.com.an', '.com.ao', '.com.aq', '.com.ar', '.com.as', '.com.as', '.com.at', '.com.au', '.com.aw',
                           '.com.az', '.com.ba', '.com.bb', '.com.bd', '.com.be', '.com.bf', '.com.bg', '.com.bh', '.com.bi',
                           '.com.bj', '.com.bm', '.com.bn', '.com.bo', '.com.br', '.com.bs', '.com.bt', '.com.bv', '.com.bw',
                           '.com.by', '.com.bz', '.com.ca', '.com.ca', '.com.cc', '.com.cd', '.com.cf', '.com.cg', '.com.ch',
                           '.com.ci', '.com.ck', '.com.cl', '.com.cm', '.com.cn', '.com.co', '.com.cq', '.com.cr', '.com.cu',
                           '.com.cv', '.com.cx', '.com.cy', '.com.cz', '.com.de', '.com.dj', '.com.dk', '.com.dm', '.com.do',
                           '.com.dz', '.com.ec', '.com.ee', '.com.eg', '.com.eh', '.com.es', '.com.et', '.com.eu', '.com.ev',
                           '.com.fi', '.com.fj', '.com.fk', '.com.fm', '.com.fo', '.com.fr', '.com.ga', '.com.gb', '.com.gd',
                           '.com.ge', '.com.gf', '.com.gh', '.com.gi', '.com.gl', '.com.gm', '.com.gn', '.com.gp', '.com.gr',
                           '.com.gt', '.com.gu', '.com.gw', '.com.gy', '.com.hm', '.com.hn', '.com.hr', '.com.ht', '.com.hu',
                           '.com.id', '.com.id', '.com.ie', '.com.il', '.com.il', '.com.in', '.com.io', '.com.iq', '.com.ir',
                           '.com.is', '.com.it', '.com.jm', '.com.jo', '.com.jp', '.com.ke', '.com.kg', '.com.kh', '.com.ki',
                           '.com.km', '.com.kn', '.com.kp', '.com.kr', '.com.kw', '.com.ky', '.com.kz', '.com.la', '.com.lb',
                           '.com.lc', '.com.li', '.com.lk', '.com.lr', '.com.ls', '.com.lt', '.com.lu', '.com.lv', '.com.ly',
                           '.com.ma', '.com.mc', '.com.md', '.com.me', '.com.mg', '.com.mh', '.com.ml', '.com.mm', '.com.mn',
                           '.com.mo', '.com.mp', '.com.mq', '.com.mr', '.com.ms', '.com.mt', '.com.mv', '.com.mw', '.com.mx',
                           '.com.my', '.com.mz', '.com.na', '.com.nc', '.com.ne', '.com.nf', '.com.ng', '.com.ni', '.com.nl',
                           '.com.no', '.com.np', '.com.nr', '.com.nr', '.com.nt', '.com.nu', '.com.nz', '.com.om', '.com.pa',
                           '.com.pe', '.com.pf', '.com.pg', '.com.ph', '.com.pk', '.com.pl', '.com.pm', '.com.pn', '.com.pr',
                           '.com.pt', '.com.pw', '.com.py', '.com.qa', '.com.re', '.com.ro', '.com.rs', '.com.ru', '.com.rw',
                           '.com.sa', '.com.sb', '.com.sc', '.com.sd', '.com.se', '.com.sg', '.com.sh', '.com.si', '.com.sj',
                           '.com.sk', '.com.sl', '.com.sm', '.com.sn', '.com.so', '.com.sr', '.com.st', '.com.su', '.com.sy',
                           '.com.sz', '.com.tc', '.com.td', '.com.tf', '.com.tg', '.com.th', '.com.tj', '.com.tk', '.com.tl',
                           '.com.tm', '.com.tn', '.com.to', '.com.tp', '.com.tr', '.com.tt', '.com.tv', '.com.tw', '.com.tz',
                           '.com.ua', '.com.ug', '.com.uk', '.com.uk', '.com.us', '.com.uy', '.com.uz', '.com.va', '.com.vc',
                           '.com.ve', '.com.vg', '.com.vn', '.com.vu', '.com.wf', '.com.ws', '.com.ye', '.com.za', '.com.zm',
                           '.com.zw', '.mil.cn', '.qh.cn', '.sc.cn', '.sd.cn', '.sh.cn', '.sx.cn', '.tj.cn', '.tw.cn', '.tw.cn',
                           '.xj.cn', '.xz.cn', '.yn.cn', '.zj.cn', '.bj.cn', '.edu.kg'
                           ]
        old_domain_name = domain_name
        top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        new_top_domain = "." + top_domain.replace(".", "")
        is_tow_top = False
        if top_domain in top_domain_list:
            is_tow_top = True
            domain_name = domain_name[:-len(top_domain)] + new_top_domain

        if domain_name.count(".") > 1:
            zone, middle, last = domain_name.rsplit(".", 2)
            if is_tow_top:
                last = top_domain[1:]
            root = ".".join([middle, last])
        else:
            zone = ""
            root = old_domain_name
        return root, zone

    def getSslUsedSite(self, save_path):
        pkey_file = '{}/privkey.pem'.format(save_path)
        pkey = slemp.readFile(pkey_file)
        if not pkey:
            return False
        cert_paths = 'vhost/cert'
        import panelSite
        args = slemp.dict_obj()
        args.siteName = ''
        for c_name in os.listdir(cert_paths):
            skey_file = '{}/{}/privkey.pem'.format(cert_paths, c_name)
            skey = slemp.readFile(skey_file)
            if not skey:
                continue
            if skey == pkey:
                args.siteName = c_name
                run_path = panelSite.panelSite().GetRunPath(args)
                if not run_path:
                    continue
                sitePath = slemp.M('sites').where(
                    'name=?', c_name).getField('path')
                if not sitePath:
                    continue
                to_path = "{}/{}".format(sitePath, run_path)
                return to_path
        return False

    def renewCertOther(self):
        cert_path = "{}/vhost/cert".format(slemp.getRunDir())
        if not os.path.exists(cert_path):
            return
        new_time = time.time() + (86400 * 30)
        n = 0
        if not 'orders' in self.__config:
            self.__config['orders'] = {}
        import panelSite
        siteObj = panelSite.panelSite()
        args = slemp.dict_obj()
        for siteName in os.listdir(cert_path):
            try:
                cert_file = '{}/{}/fullchain.pem'.format(cert_path, siteName)
                if not os.path.exists(cert_file):
                    continue
                siteInfo = slemp.M('sites').where('name=?', siteName).find()
                if not siteInfo:
                    continue
                cert_init = self.getCertInit(cert_file)
                if not cert_init:
                    continue
                end_time = time.mktime(time.strptime(
                    cert_init['notAfter'], '%Y-%m-%d'))
                if end_time > new_time:
                    continue
                try:
                    if not cert_init['issuer'] in ['R3', "Let's Encrypt"] and cert_init['issuer'].find("Let's Encrypt") == -1:
                        continue
                except:
                    continue

                if isinstance(cert_init['dns'], str):
                    cert_init['dns'] = [cert_init['dns']]
                index = self.getIndex(cert_init['dns'])
                if index in self.__config['orders'].keys():
                    continue

                n += 1
                writeLog(
                    "|-Renewing additional certificate {}, domain name: {}..".format(n, cert_init['subject']))
                writeLog("|-Creating order..")
                args.id = siteInfo['id']
                runPath = siteObj.GetRunPath(args)
                if runPath and not runPath in ['/']:
                    path = siteInfo['path'] + '/' + runPath
                else:
                    path = siteInfo['path']
            except:
                writeLog("|-[{}] renewal failed".format(siteName))

    # external API - START ----------------------------------------------------------
    def getHostConf(self, siteName):
        return slemp.getServerDir() + '/web_conf/nginx/vhost/' + siteName + '.conf'

    def getSitePath(self, siteName):
        file = self.getHostConf(siteName)
        if os.path.exists(file):
            conf = slemp.readFile(file)
            rep = '\s*root\s*(.+);'
            path = re.search(rep, conf).groups()[0]
            return path
        return ''

    def applyCertApi(self, args):
        '''
        Apply for a certificate - api
        '''
        return self.applyCert(args['domains'], args['auth_type'], args['auth_to'])
    # external API - END ----------------------------------------------------------

    def getSiteNameByDomains(self, domains):
        sql = slemp.M('domain')
        site_sql = slemp.M('sites')
        siteName = None
        for domain in domains:
            pid = sql.where('name=?', domain).getField('pid')
            if pid:
                siteName = site_sql.where('id=?', pid).getField('name')
                break
        return siteName

    def renewCertTo(self, domains, auth_type, auth_to, index=None):
        site_name = None
        cert = {}

        import site_api
        api = site_api.site_api()
        if os.path.exists(auth_to):
            if slemp.M('sites').where('path=?', auth_to).count() == 1:
                site_id = m.M('sites').where('path=?', auth_to).getField('id')
                site_name = m.M('sites').where(
                    'path=?', auth_to).getField('name')

                rdata = api.getSiteRunPath(site_id)
                runPath = rdata['runPath']
                if runPath and not runPath in ['/']:
                    path = auth_to + '/' + runPath
                    if os.path.exists(path):
                        auth_to = path.replace('//', '/')

            else:
                site_name = self.getSiteNameByDomains(domains)
        is_rep = api.httpToHttps(site_name)
        try:
            index = self.createOrder(
                domains,
                auth_type,
                auth_to.replace('//', '/'),
                index
            )

            writeLog("|-Obtaining verification information..")
            self.getAuths(index)
            writeLog("|-Verifying domain name..")
            self.authDomain(index)
            writeLog("|-Sending CSR..")
            self.sendCsr(index)
            writeLog("|-Downloading certificate..")
            cert = self.downloadCert(index)
            self.__config['orders'][index]['renew_time'] = int(time.time())

            self.__config['orders'][index]['retry_count'] = 0
            self.__config['orders'][index]['next_retry_time'] = 0

            self.saveConfig()
            cert['status'] = True
            cert['msg'] = 'Successfully renewed!'
            writeLog("|-Successfully renewed!")
        except Exception as e:
            if str(e).find('429') > -1:
                msg = 'At least 7 more days to renew!'
                writeLog("|-" + msg)
                return slemp.returnJson(False, msg)

            if str(e).find('Please try again later') == -1:
                if index:
                    self.__config['orders'][index][
                        'next_retry_time'] = int(time.time() + (86400 * 2))
                    if not 'retry_count' in self.__config['orders'][index].keys():
                        self.__config['orders'][index]['retry_count'] = 1
                    self.__config['orders'][index]['retry_count'] += 1
                    self.saveConfig()
            msg = str(e).split('>>>>')[0]
            writeLog("|-" + msg)
            return slemp.returnJson(False, msg)
        finally:
            is_rep_decode = json.loads(is_rep)
            if is_rep_decode['status']:
                api.closeToHttps(site_name)
        writeLog("-" * 70)
        return cert

    def renewCert(self, index):
        writeLog("", "wb+")
        # self.D('renew_cert', index)
        try:
            order_index = []
            if index:
                if type(index) != str:
                    index = index.index
                if not index in self.__config['orders']:
                    raise Exception("The specified order number does not exist and cannot be renewed!")
                order_index.append(index)
            else:
                start_time = time.time() + (30 * 86400)
                # print(self.__config)
                if not 'orders' in self.__config:
                    self.__config['orders'] = {}

                for i in self.__config['orders'].keys():
                    # print(self.__config['orders'][i])
                    if not 'save_path' in self.__config['orders'][i]:
                        continue

                    if 'cert' in self.__config['orders'][i]:
                        self.__config['orders'][i]['cert_timeout'] = self.__config[
                            'orders'][i]['cert']['cert_timeout']

                    if not 'cert_timeout' in self.__config['orders'][i]:
                        self.__config['orders'][i][
                            'cert_timeout'] = int(time.time())

                    if self.__config['orders'][i]['cert_timeout'] > start_time:
                        writeLog(
                            "|-Domain name skipped this time: {}, not expired!".format(self.__config['orders'][i]['domains'][0]))
                        continue

                    if self.__config['orders'][i]['auth_to'].find('|') == -1 and self.__config['orders'][i]['auth_to'].find('/') != -1:
                        if not os.path.exists(self.__config['orders'][i]['auth_to']):
                            auth_to = self.getSslUsedSite(
                                self.__config['orders'][i]['save_path'])
                            if not auth_to:
                                continue

                            for domain in self.__config['orders'][i]['domains']:
                                if domain.find('*') != -1:
                                    break
                                if not slemp.M('domain').where("name=?", (domain,)).count() and not slemp.M('binding').where("domain=?", domain).count():
                                    auth_to = None
                                    writeLog(
                                        "|-Skip deleted domains: {}".format(self.__config['orders'][i]['domains']))
                            if not auth_to:
                                continue

                            self.__config['orders'][i]['auth_to'] = auth_to

                    if 'next_retry_time' in self.__config['orders'][i]:
                        timeout = self.__config['orders'][i][
                            'next_retry_time'] - int(time.time())
                        if timeout > 0:
                            writeLog('|-The domain name is skipped this time: {}, because the last renewal failed, you need to wait {} hours before trying again'.format(
                                self.__config['orders'][i]['domains'], int(timeout / 60 / 60)))
                            continue

                    if 'retry_count' in self.__config['orders'][i]:
                        if self.__config['orders'][i]['retry_count'] >= 5:
                            writeLog('|-The domain name is skipped this time: {}, and this certificate will not be renewed due to 5 consecutive renewal failures (you can try to manually renew this certificate, and the number of errors will be reset after success)'.format(
                                self.__config['orders'][i]['domains']))
                            continue

                    order_index.append(i)
                if not order_index:
                    writeLog("|-No SSL certificate that expires within 30 days was found, trying to find other renewable certificates!")
                    # self.getApis()
                    # self.renewCertOther()
                    writeLog("|-All tasks have been processed!")
                    return
            writeLog("|-A total of {} certificates need to be renewed".format(len(order_index)))

            n = 0
            self.getApis()
            cert = None
            for index in order_index:
                n += 1
                writeLog("|-Renewing number {}, domain name: {}..".format(n,
                                                        self.__config['orders'][index]['domains']))
                writeLog("|-Creating order..")
                cert = self.renewCertTo(self.__config['orders'][index]['domains'], self.__config[
                    'orders'][index]['auth_type'], self.__config['orders'][index]['auth_to'], index)
                self.clearAuthFile(index)
            return cert
        except Exception as ex:
            ex = str(ex)
            if ex.find(">>>>") != -1:
                msg = ex.split(">>>>")
                msg[1] = json.loads(msg[1])
            else:
                msg = ex
                writeLog(slemp.getTracebackInfo())
            return slemp.returnJson(False, msg)

    def revokeOrder(self, index):
        if not index in self.__config['orders']:
            raise Exception("The specified order does not exist!")
        cert_path = self.__config['orders'][index]['save_path']
        if not os.path.exists(cert_path):
            raise Exception("No available certificates were found for the specified order!")
        cert = self.dumpDer(cert_path)
        if not cert:
            raise Exception("Certificate read failed!")
        payload = {
            "certificate": self.calculateSafeBase64(cert),
            "reason": 4
        }

        self.getApis()
        res = self.acmeRequest(self.__apis['revokeCert'], payload)
        if res.status in [200, 201]:
            if os.path.exists(cert_path):
                slemp.execShell("rm -rf {}".format(cert_path))
            del(self.__config['orders'][index])
            self.saveConfig()
            return slemp.returnJson(True, "Certificate revocation successful!")
        return res.json()

    def do(self, args):
        cert = None
        try:
            if not args.index:
                if not args.domains:
                    echoErr("Please specify the domain name to apply for the certificate in the --domain parameter, separated by commas (,)")
                if not args.auth_type in ['http', 'tls']:
                    echoErr("Please specify the correct authentication type in the --type parameter, http")

                auth_to = ''
                if args.auth_type in ['http', 'tls']:
                    if not args.path:
                        echoErr("Please specify the website root directory in the --path parameter!")
                    if not os.path.exists(args.path):
                        echoErr("The specified website root directory does not exist, please check: {}".format(args.path))
                    auth_to = args.path
                else:
                    echoErr("Only file verification is supported!")
                    exit()

                domains = args.domains.strip().split(',')
                cert = self.applyCert(
                    domains, auth_type=args.auth_type, auth_to=auth_to, args=args)
            else:
                cert = self.applyCert([], auth_type='dns',
                                      auth_to='dns', index=args.index)
        except Exception as e:
            writeLog("|-{}".format(slemp.getTracebackInfo()))
            exit()

        if not cert:
            exit()

        # print(cert)
        if not cert['status']:
            writeLog('|-' + cert['msg'][0])
            exit()
        writeLog("=" * 65)
        writeLog("|-Certificate obtained successfully!")
        writeLog("=" * 65)
        writeLog("Certificate expiration time: {}".format(
            slemp.formatDate(times=cert['cert_timeout'])))
        writeLog("The certificate is saved in: {}/".format(cert['save_path']))


# exp:
if __name__ == "__main__":
    p = argparse.ArgumentParser(usage="Necessary parameters: --domain domain name list, multiple separated by commas!")
    p.add_argument('--domain', default=None,
                   help="Please specify the domain name to apply for a certificate", dest="domains")
    p.add_argument('--type', default=None, help="Please specify verification type", dest="auth_type")
    p.add_argument('--path', default=None, help="Please specify the website root directory", dest="path")
    p.add_argument('--index', default=None, help="Specify order index", dest="index")
    p.add_argument('--renew', default=None, help="Certificate renewal", dest="renew")
    p.add_argument('--revoke', default=None, help="Revocation certificate", dest="revoke")

    args = p.parse_args()
    cr = cert_api()

    if args.revoke:
        if not args.index:
            echoErr("Please pass in the index of the order to be revoked in the --index parameter")
        result = cr.revokeOrder(args.index)
        writeLog(result)
        exit()

    if args.renew:
        cr.renewCert(args.index)
        exit()

    cr.do(args)
