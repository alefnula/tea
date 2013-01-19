__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '11 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import random
from tea.system import platform

__all__ = ['CryptError', 'encrypt', 'decrypt']

class CryptError(Exception): pass

# TODO - remove one of the keys
__key = '\xe5\xb9\x13A0\xb0\x0bkat\xea\xb7\x08D\xee3'
__iv  = '\xdbU\x8b5\x08B\xe6\xbe\x8eS\xfe\x04\x7f\xe0\xb6\xd0'

# key to use for encryption if no other alternative is possible
_key    = [213, 21, 199, 11, 17, 227, 18, 7, 114, 184, 27, 
           162, 37, 112, 222, 209, 241, 24, 175, 144, 173, 
           53, 196, 29, 124, 26, 17, 218, 131, 236, 53, 209]

# initialization vector for algorithms that requires is
_vector = [16, 63, 1, 111, 23, 3, 113, 119, 21, 
           121, 31, 112, 44, 32, 114, 255]

# list of supported encryption algorithms in priority order
algorithms = ('aes', 'dotnet', 'win', 'simple')

# Map of implemented encryption algorithms
# Encryption and decryption holds dict of algorithm name to function that
# implements algorithm. 
# Every function that implements encryption or decryption must receive data to
# process and a key to process it with.
# encryptior and decryption decorators can be used to register implementations.
implementations = {
    'encryption': {},
    'decryption': {},
}

def encrypter(name):
    ''' Decorator for registering function as encryptor. '''
    def wrapper(func):
        implementations['encryption'][name] = func
        return func
    return wrapper

def decrypter(name):
    ''' Decorator for registering function as decryptor.'''
    def wrapper(func):
        implementations['decryption'][name] = func
        return func
    return wrapper

def generate_key(length=32):
    ''' Generates list of random number in range 0 to 255 inclusive of specified length.'''
    return [random.randint(0, 255) for i in xrange(length)] #@UnusedVariable

def _to_hex_digest(bts):
    ''' Converts sequence of bytes to hex digest.'''
    return ''.join(map(lambda x: '%02x' % x, map(ord, bts)))

def _from_hex_digest(digest):
    ''' Converts hex digest to sequence of bytes.'''
    return ''.join([chr(int(digest[x:x+2], 16)) for x in xrange(0, len(digest), 2)])

# if we have pycrypt it is out best choice
try:
    from Cryptor.Cipher import AES
    
    def _get_cipher(key):
        ''' Create AES chiper with provided key.'''
        key = ''.join(map(chr, key))
        vector = ''.join(map(chr, _vector))
        return AES.new(key, AES.MODE_CFB, vector)
    
    @encrypter('aes')
    def _encrypt(data, key):
        ''' Encrypts data using provided key with AES cipher.'''
        return _get_cipher(key).encrypt(data)
    
    @decrypter('aes')
    def _decrypt(data, key):
        ''' Decrypts data using provided key with AES cipher.'''
        return _get_cipher(key).decrypt(data)
    
except ImportError:
    pass

if platform.is_only(platform.WINDOWS):
    # if we have win32 installed add native windows crypting
    try:
        import win32crypt
        
        # win crypt constants
        CRYPTPROTECT_UI_FORBIDEN       = 0x01
        CRYPTPROTECT_LOCAL_MACHINE     = 0x04
        CRYPTPROTECT_CRED_SYNC         = 0x08
        CRYPTPROTECT_AUDIT             = 0x10
        CRYPTPROTECT_NO_RECOVERY       = 0x20
        CRYPTPROTECT_VERIFY_PROTECTION = 0x40
        CRYPTPROTECT_CRED_REGENERATE   = 0x80
        
        @encrypter('win')
        def _encrypt(data, key=None): #key is not used in this encryption
            ''' Encrypts data using windows crypt service. 
                Key is not used.'''
            return win32crypt.CryptProtectData(data, 'tea-crypt', 
                                               None, None, None, 
                                               CRYPTPROTECT_UI_FORBIDEN)
            
        @decrypter('win')
        def _decrypt(data, key=None): #key is not used in this decryption
            ''' Decrypts data using windows crypt service.
                Key is not used.'''
            return win32crypt.CryptUnprotectData(data, 
                                                 None, None, None, 
                                                 CRYPTPROTECT_UI_FORBIDEN)[1]
    except ImportError:
        pass
    
    # if we have win32 installed try add key storage using windows credentials
    try:
        import win32cred, pywintypes
        def _vault_store(service, ident, secret):
            target = '%(ident)s@%(service)s' % vars()
            credential = dict(Type=win32cred.CRED_TYPE_GENERIC, 
                              TargetName=target, 
                              UserName=ident, 
                              CredentialBlob=secret, 
                              Comment='Stored using tea-crypt', 
                              Persist=win32cred.CRED_PERSIST_ENTERPRISE)
            win32cred.CredWrite(credential, 0)
        
        def _vault_retrieve(service, ident):
            target = '%(ident)s@%(service)s' % vars()
            try:
                res = win32cred.CredRead(Type=win32cred.CRED_TYPE_GENERIC, 
                                         TargetName=target)
            except pywintypes.error as e:
                if e.winerror == 1168 and e.funcname == 'CredRead':
                    return None
                raise
            return res['CredentialBlob'].decode('utf-16')
        
        def _vault_delete(service, ident):
            target = '%(ident)s@%(service)s' % vars()
            win32cred.CredDelete(Type=win32cred.CRED_TYPE_GENERIC, 
                                 TargetName=target)
            
        def get_key():
            key = _vault_retrieve('tea', 'tea-crypt')
            if key:
                return map(ord, key)
            else:
                key = generate_key()
                _vault_store('tea', 'tea-crypt', ''.join(map(chr, key)))
                return key
    except ImportError:
        pass
    
elif platform.is_a(platform.DOTNET):
    # ironpython - .net implementation of AES can be used 
    # ironpython can be used on mono so check what options are for key storage
    from System import Array, Byte
    from System.Text import UTF8Encoding
    from System.IO import MemoryStream
    from System.Security.Cryptography import RijndaelManaged, CryptoStream, CryptoStreamMode
    
    @encrypter('dotnet')
    def _encrypt(text, key):
        '''
        Performs crypting of provided text using AES algorithm.
        If 'digest' is True hex_digest will be returned, otherwise bytes of encrypted
        data will be returned.
        
        This function is simetrical with decrypt function.
        '''
        utfEncoder    = UTF8Encoding()
        bytes         = utfEncoder.GetBytes(text)
        rm            = RijndaelManaged()
        key           = Array[Byte](key)
        enc_transform = rm.CreateEncryptor(key, Array[Byte](_vector))
        mem           = MemoryStream()
        
        cs = CryptoStream(mem, enc_transform, CryptoStreamMode.Write)
        cs.Write(bytes, 0, len(bytes))
        cs.FlushFinalBlock()
        mem.Position = 0
        encrypted = Array.CreateInstance(Byte, mem.Length)
        mem.Read(encrypted, 0, mem.Length)
        cs.Close()
        
        return ''.join(map(chr, encrypted)) 
    
    @decrypter('dotnet')
    def _decrypt(data, key):
        '''
        Performs decrypting of provided encrypted data. 
        If 'digest' is True data must be hex digest, otherwise data should be
        encrtypted bytes.
        
        This function is simetrical with encrypt function.
        '''
        data = Array[Byte](map(Byte, map(ord, data)))
        key  = Array[Byte](map(Byte, key))
        rm   = RijndaelManaged()
        dec_transform = rm.CreateDecryptor(key, Array[Byte](_vector))
        
        mem = MemoryStream()
        cs = CryptoStream(mem, dec_transform, CryptoStreamMode.Write)
        cs.Write(data, 0, data.Length)
        cs.FlushFinalBlock()
            
        mem.Position = 0
        decrypted = Array.CreateInstance(Byte, mem.Length)
        mem.Read(decrypted, 0, decrypted.Length)
            
        cs.Close()
        utfEncoder = UTF8Encoding()
        return utfEncoder.GetString(decrypted)
    
    # Can't find a way to invoke win32api from ironpython witout wrapping it 
    # to C# dll and using pInvoke. So, for now using windows credentials
    # storage for storing key can not be easely done. 
    
elif platform.is_a(platform.POSIX):
    # some kind of posix OS - more detail check is needed
    pass
elif platform.is_a(platform.DARWIN):
    # macOS - dunno what to do here
    pass
else:
    # this is default cipher - not very secure, but at least password will not 
    # be in plain text format.
    @encrypter('simple')
    def _simple_encrypt(data, key):
        key_len  = len(key)
        encrypted = []
        for i, c in enumerate(data):
            key_c = key[i % key_len]
            msg_c = ord(c)
            encrypted.append(chr((msg_c + key_c) % 127))
        return ''.join(encrypted)
        
    @decrypter('simple')
    def _simple_decrypt(data, key):
        key_len   = len(key)
        decrypted = []
        for i, c in enumerate(data):
            key_c = key[i % key_len]
            enc_c = ord(c)
            decrypted.append(chr((enc_c - key_c) % 127))
        return ''.join(decrypted)
    
# if there is no get_key method fallback to default
try:
    get_key
except NameError:
    def get_key():
        return _key

def get_best_algorithm():
    for alg in algorithms:
        if (implementations['encryption'].has_key(alg) and
            implementations['decryption'].has_key(alg)):
            return alg
    raise CryptError('No crypting algorithms sutable for %s platform' % platform)


# public interface
def encrypt(data, digest=True):
    ''' Performs encryption of provided data.'''
    alg = get_best_algorithm()
    enc = implementations['encryption'][alg](data, get_key())
    return '%s$%s' % (alg, (_to_hex_digest(enc) if digest else enc))

def decrypt(data, digest=True):
    ''' Decrypts provided data.'''
    alg, _, data = data.rpartition('$')
    data = _from_hex_digest(data) if digest else data
    try:
        return implementations['decryption'][alg](data, get_key())
    except KeyError:
        raise CryptError('Can not decrypt key for algorithm: %s' % alg)


    
def main():
#    print platform.get_all_names()
#    print get_best_algorithm()
#    print implementations
    print get_key()
    print encrypt('password koji ce biti encryptovan')
    print decrypt(encrypt('password koji ce biti encryptovan'))

    
if __name__ == '__main__':
    main()