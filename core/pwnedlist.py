import time
import hmac
import hashlib
import urllib
import base64
from Crypto.Cipher import AES

def build_payload(payload, method, key, secret):
    timestamp = int(time.time())
    payload['ts'] = timestamp
    payload['key'] = key
    msg = "%s%s%s%s" % (key, timestamp, method, secret)
    hm = hmac.new(secret, msg, hashlib.sha1)
    payload['hmac'] = hm.hexdigest() 
    return payload

def decrypt(plain, key, iv):
    AES.key_size=128
    crypt_object=AES.new(key=key,mode=AES.MODE_CBC,IV=iv)
    decoded=base64.b64decode(plain) # your ecrypted and encoded text goes here
    decrypted=crypt_object.decrypt(decoded)
    return decrypted

def guard(num):
    ans = raw_input('This operation will use %d API queries. Do you want to continue? [Y/N]: ' % (num))
    if ans.upper() != 'Y': return False
    return True