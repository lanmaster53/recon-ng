import time
import hmac
import hashlib
import urllib
import base64
import aes


def build_payload(payload, method, key, secret):
    timestamp = int(time.time())
    payload['ts'] = timestamp
    payload['key'] = key
    msg = '%s%s%s%s' % (key, timestamp, method, secret)
    hm = hmac.new(secret, msg, hashlib.sha1)
    payload['hmac'] = hm.hexdigest() 
    return payload

def decrypt(ciphertext, key, iv):
    decoded = base64.b64decode(ciphertext)
    return aes.decryptData(key, str(iv) + decoded)

def guard(num):
    ans = raw_input('This operation will use %d API queries. Do you want to continue? [Y/N]: ' % (num))
    if ans.upper() != 'Y': return False
    return True
