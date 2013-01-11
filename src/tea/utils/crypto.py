__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '11 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

__key = '\xe5\xb9\x13A0\xb0\x0bkat\xea\xb7\x08D\xee3'
__iv  = '\xdbU\x8b5\x08B\xe6\xbe\x8eS\xfe\x04\x7f\xe0\xb6\xd0'

try:
    from Cryptor.Cipher import AES
    
    def encrypt(data):
        cipher = AES.new(__key, AES.MODE_CFB, __iv)
        return cipher.encrypt(data)
    
    def decrypt(data):
        cipher = AES.new(__key, AES.MODE_CFB, __iv)
        return cipher.decrypt(data)

except ImportError:

    __key = __key + __iv

    def encrypt(data):
        key_len  = len(__key)
        encryped = []
        for i, c in enumerate(data):
            key_c = ord(__key[i % key_len])
            msg_c = ord(c)
            encryped.append(chr((msg_c + key_c) % 127))
        return ''.join(encryped)

    def decrypt(data):
        key_len   = len(__key)
        decrypted = []
        for i, c in enumerate(data):
            key_c = ord(__key[i % key_len])
            enc_c = ord(c)
            decrypted.append(chr((enc_c - key_c) % 127))
        return ''.join(decrypted)
