from __future__ import print_function

__author__ = 'Viktor Kerkez <alefnula@gmail.com>'
__date__ = '11 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

import os
import random
from tea.utils import six
from tea.system import platform

__all__ = ['CryptError', 'encrypt', 'decrypt']


class CryptError(Exception):
    pass

# key to use for encryption if no other alternative is possible
_key = [213, 21, 199, 11, 17, 227, 18, 7, 114, 184, 27,
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
    'get_key': lambda: _key
}


# Decorators
def encrypter(name):
    """Decorator for registering function as encryptor."""
    def wrapper(func):
        implementations['encryption'][name] = func
        return func
    return wrapper


def decrypter(name):
    """Decorator for registering function as decryptor."""
    def wrapper(func):
        implementations['decryption'][name] = func
        return func
    return wrapper


def keygetter(func):
    """Decorator for registering function for getting the encryption key."""
    implementations['get_key'] = func
    return func


# Helpers
def _generate_key(length=32):
    """Generates list of random number in range 0 to 255 inclusive of specified
    length."""
    return [random.randint(0, 255) for _ in range(length)]


def _to_hex_digest(bts):
    """Converts sequence of bytes to hex digest."""
    return ''.join(['%02x' % x for x in map(ord, bts)])


def _from_hex_digest(digest):
    """Converts hex digest to sequence of bytes."""
    return ''.join([chr(int(digest[x:x + 2], 16))
                    for x in range(0, len(digest), 2)])


# Try to register AES from pycrypt
try:
    from Crypto.Cipher import AES

    def _get_cipher(key):
        """Create AES chiper with provided key."""
        key = ''.join(map(chr, key))
        vector = ''.join(map(chr, _vector))
        return AES.new(key, AES.MODE_CFB, vector)

    @encrypter('aes')
    def _encrypt(data, key):
        """Encrypts data using provided key with AES cipher."""
        return _get_cipher(key).encrypt(data)

    @decrypter('aes')
    def _decrypt(data, key):
        """Decrypts data using provided key with AES cipher."""
        return _get_cipher(key).decrypt(data)
except ImportError:
    pass


if platform.is_only(platform.WINDOWS):
    # if we have win32 installed add native windows crypting
    try:
        import ctypes
        from ctypes import wintypes
        from ctypes import windll

        class DATA_BLOB(ctypes.Structure):
            _fields_ = [
                ('cbData', wintypes.DWORD),
                ('pbData', ctypes.POINTER(ctypes.c_char))
            ]

        def get_data(data_blob):
            cbData = int(data_blob.cbData)
            pbData = data_blob.pbData
            cbuffer = ctypes.c_buffer(cbData)
            ctypes.cdll.msvcrt.memcpy(cbuffer, pbData, cbData)
            windll.kernel32.LocalFree(pbData)  # @UndefinedVariable
            return cbuffer.raw

        CRYPTPROTECT_UI_FORBIDDEN = 0x01

        @encrypter('win')
        def Win32CryptProtectData(data, key=None):
            if isinstance(data, six.text_type):
                data = data.encode('utf-8')
            buffer_in = ctypes.c_buffer(data, len(data))
            blob_in = DATA_BLOB(len(data), buffer_in)
            blob_out = DATA_BLOB()
            CryptProtectData = windll.crypt32.CryptProtectData
            if CryptProtectData(ctypes.byref(blob_in), u'tea-crypt',
                                None, None, None,
                                CRYPTPROTECT_UI_FORBIDDEN,
                                ctypes.byref(blob_out)):
                return get_data(blob_out)
            else:
                return ''

        @decrypter('win')
        def Win32CryptUnprotectData(data, key=None):
            if isinstance(data, six.text_type):
                data = data.encode('utf-8')
            buffer_in = ctypes.c_buffer(data, len(data))
            blob_in = DATA_BLOB(len(data), buffer_in)
            blob_out = DATA_BLOB()
            CryptUnprotectData = windll.crypt32.CryptUnprotectData
            if CryptUnprotectData(ctypes.byref(blob_in),
                                  None, None, None, None,
                                  CRYPTPROTECT_UI_FORBIDDEN,
                                  ctypes.byref(blob_out)):
                return get_data(blob_out)
            else:
                return ''

        #import win32crypt
        #import win32cryptcon
        #@encrypter('win')
        #def _encrypt(data, key=None):
        #    ''' Encrypts data using windows crypt service.
        #        Key is not used.'''
        #    windll.c
        #    return win32crypt.CryptProtectData(
        #        data, 'tea-crypt', None, None, None,
        #        win32cryptcon.CRYPTPROTECT_UI_FORBIDDEN
        #    )
        #
        #@decrypter('win')
        #def _decrypt(data, key=None):
        #    ''' Decrypts data using windows crypt service.
        #        Key is not used.'''
        #    return win32crypt.CryptUnprotectData(
        #        data, None, None, None,
        #        win32cryptcon.CRYPTPROTECT_UI_FORBIDDEN
        #    )[1]
    except ImportError:
        pass

    # if we have win32 installed try add key storage using windows credentials
    try:
        import win32cred
        import pywintypes

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

        # TODO: There is a bug with saving and getting key from vault
        #       probably something with encoding. Sometimes _vault_retrieve
        #       returns numbers higher then 255 (even if they were not stored)
        @keygetter
        def get_key():
            key = _vault_retrieve('tea', 'tea-crypt')
            if key:
                return [ord(k) % 256 for k in key]
            else:
                key = _generate_key()
                _vault_store('tea', 'tea-crypt', ''.join(map(chr, key)))
                return key
    except ImportError:
        pass

elif platform.is_a(platform.DOTNET):
    # ironpython - .net implementation of AES can be used
    # ironpython can be used on mono so check what options are for key storage
    import clr
    clr.AddReference('System.Security')
    from System import Array, Byte
    from System.Text import UTF8Encoding
    from System.IO import MemoryStream
    from System.Security.Cryptography import (RijndaelManaged, CryptoStream,
                                              CryptoStreamMode, ProtectedData,
                                              DataProtectionScope)

    @encrypter('dotnet')
    def _encrypt(text, key):
        """Performs crypting of provided text using AES algorithm.

        If 'digest' is True hex_digest will be returned, otherwise bytes of
        encrypted data will be returned.

        This function is symmetrical with decrypt function.
        """
        utfEncoder = UTF8Encoding()
        bytes_text = utfEncoder.GetBytes(text)
        rm = RijndaelManaged()
        key = Array[Byte](key)
        enc_transform = rm.CreateEncryptor(key, Array[Byte](_vector))
        mem = MemoryStream()

        cs = CryptoStream(mem, enc_transform, CryptoStreamMode.Write)
        cs.Write(bytes_text, 0, len(bytes_text))
        cs.FlushFinalBlock()
        mem.Position = 0
        encrypted = Array.CreateInstance(Byte, mem.Length)
        mem.Read(encrypted, 0, mem.Length)
        cs.Close()

        return ''.join(map(chr, encrypted))

    @decrypter('dotnet')
    def _decrypt(data, key):
        """Performs decrypting of provided encrypted data.
        If 'digest' is True data must be hex digest, otherwise data should be
        encrypted bytes.

        This function is symmetrical with encrypt function.
        """
        data = Array[Byte](map(Byte, map(ord, data)))
        key = Array[Byte](map(Byte, key))
        rm = RijndaelManaged()
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

    # Can't find a way to invoke win32api from ironpython without wrapping it
    # to C# dll and using pInvoke. So, instead of using windows credentials to
    # store a key, key will be stored in file, encrypted with
    # ProtedtedData.Protect.
    @keygetter
    def get_key():
        from tea.system import get_appdata
        from tea.shell import mkdir
        dir_path = os.path.join(get_appdata(), 'Tea')
        key_path = os.path.join(dir_path, 'key.bin')
        if os.path.exists(dir_path) and os.path.exists(key_path):
            with open(key_path, 'rb') as f:
                cr_key = Array[Byte](map(ord, f.read()))
                key = ProtectedData.Unprotect(cr_key, None,
                                              DataProtectionScope.CurrentUser)
                return [int(k, 10) for k in key]
        else:
            mkdir(dir_path)
            key = _generate_key()
            arr_key = Array[Byte](key)
            cr_key = ProtectedData.Protect(arr_key, None,
                                           DataProtectionScope.CurrentUser)
            with open(key_path, 'wb') as f:
                f.write(cr_key)
            return key

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
        key_len = len(key)
        encrypted = []
        for i, c in enumerate(data):
            key_c = key[i % key_len]
            msg_c = ord(c)
            encrypted.append(chr((msg_c + key_c) % 127))
        return ''.join(encrypted)

    @decrypter('simple')
    def _simple_decrypt(data, key):
        key_len = len(key)
        decrypted = []
        for i, c in enumerate(data):
            key_c = key[i % key_len]
            enc_c = ord(c)
            decrypted.append(chr((enc_c - key_c) % 127))
        return ''.join(decrypted)


def get_best_algorithm():
    for alg in algorithms:
        if (alg in implementations['encryption'] and
                alg in implementations['decryption']):
            return alg
    raise CryptError('No crypting algorithms suitable for %s platform' %
                     platform)


# public interface
def encrypt(data, digest=True):
    """Performs encryption of provided data."""
    alg = get_best_algorithm()
    enc = implementations['encryption'][alg](data,
                                             implementations['get_key']())
    return '%s$%s' % (alg, (_to_hex_digest(enc) if digest else enc))


def decrypt(data, digest=True):
    """Decrypts provided data."""
    alg, _, data = data.rpartition('$')
    if not alg:
        return data
    data = _from_hex_digest(data) if digest else data
    try:
        return implementations['decryption'][alg](data,
                                                  implementations['get_key']())
    except KeyError:
        raise CryptError('Can not decrypt key for algorithm: %s' % alg)


def main():
    print(implementations)
    print(implementations['get_key'].__doc__)
    print(implementations['get_key']())
    print(encrypt('password koji ce biti encryptovan'))
    print(decrypt(encrypt('password koji ce biti encryptovan')))


if __name__ == '__main__':
    main()
