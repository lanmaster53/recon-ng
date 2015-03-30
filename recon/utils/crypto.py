import aes

def aes_decrypt(ciphertext, key, iv):
    decoded = ciphertext.decode('base64')
    password = aes.decryptData(key, iv.encode('utf-8') + decoded)
    return unicode(password, 'utf-8')
