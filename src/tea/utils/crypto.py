__author__    = 'Viktor Kerkez <alefnula@gmail.com>'
__date__      = '11 January 2013'
__copyright__ = 'Copyright (c) 2013 Viktor Kerkez'

from tea.system import platform

# TODO - remove one of the keys
__key = '\xe5\xb9\x13A0\xb0\x0bkat\xea\xb7\x08D\xee3'
__iv  = '\xdbU\x8b5\x08B\xe6\xbe\x8eS\xfe\x04\x7f\xe0\xb6\xd0'

_key    = [213, 21, 199, 11, 17, 227, 18, 7, 114, 184, 27, 
           162, 37, 112, 222, 209, 241, 24, 175, 144, 173, 
           53, 196, 29, 124, 26, 17, 218, 131, 236, 53, 209]
_vector = [16, 63, 1, 111, 23, 3, 113, 119, 21, 
           121, 31, 112, 44, 32, 114, 255]

#if platform.is_a(platform.DOTNET):
#    import clr
#    import System
#    import System.Security.Cryptography

if platform.is_a(platform.DOTNET):
    from System import Array, Byte
    from System.Text import UTF8Encoding
    from System.IO import MemoryStream
    from System.Security.Cryptography import RijndaelManaged, CryptoStream, CryptoStreamMode
    
    _key = Array[Byte](_key)
    _vector = Array[Byte](_vector)
    
    def encrypt(text, digest=True):
        '''
        Performs crypting of provided text using AES algorithm.
        If 'digest' is True hex_digest will be returned, otherwise bytes of encrypted
        data will be returned.
        
        This function is simetrical with decrypt function.
        '''
        utfEncoder    = UTF8Encoding()
        bytes         = utfEncoder.GetBytes(text)
        rm            = RijndaelManaged()
        enc_transform = rm.CreateEncryptor(_key, _vector)
        mem           = MemoryStream()
        
        cs = CryptoStream(mem, enc_transform, CryptoStreamMode.Write)
        cs.Write(bytes, 0, len(bytes))
        cs.FlushFinalBlock()
        mem.Position = 0
        encrypted = Array.CreateInstance(Byte, mem.Length)
        mem.Read(encrypted, 0, mem.Length)
        cs.Close()
            
        l = map(int, encrypted)
        return _to_hex_digest(l) if digest else _to_bytes(l)
        if digest:
            return _to_hex_digest(map(int, encrypted))
        else:
            return _to_bytes(map(int, encrypted))
    
    def decrypt(data, digest=True):
        '''
        Performs decrypting of provided encrypted data. 
        If 'digest' is True data must be hex digest, otherwise data should be
        encrtypted bytes.
        
        This function is simetrical with encrypt function.
        '''
        data = Array[Byte](map(Byte, _from_hex_digest(data) if digest else _from_bytes(data)))
            
        rm = RijndaelManaged()
        dec_transform = rm.CreateDecryptor(_key, _vector)
        
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
    
else:
    try:
        from Cryptor.Cipher import AES
        
        def encrypt(data, digest=True):
            cipher = AES.new(__key, AES.MODE_CFB, __iv)
            return cipher.encrypt(data)
        
        def decrypt(data, digest=True):
            cipher = AES.new(__key, AES.MODE_CFB, __iv)
            return cipher.decrypt(data)
    
    except ImportError:
    
        __key = __key + __iv
    
        def encrypt(data, digest=True):
            key_len  = len(__key)
            encryped = []
            for i, c in enumerate(data):
                key_c = ord(__key[i % key_len])
                msg_c = ord(c)
                encryped.append(chr((msg_c + key_c) % 127))
            return ''.join(encryped)
    
        def decrypt(data, digest=True):
            key_len   = len(__key)
            decrypted = []
            for i, c in enumerate(data):
                key_c = ord(__key[i % key_len])
                enc_c = ord(c)
                decrypted.append(chr((enc_c - key_c) % 127))
            return ''.join(decrypted)


def _to_bytes(lst):
    return ''.join(map(chr, lst))
    
def _from_bytes(bts):
    return [ord(b) for b in bts]
    
def _to_hex_digest(encrypted):
    return ''.join(map(lambda x: '%02x' % x, encrypted))
    
def _from_hex_digest(digest):
    return [int(digest[x:x+2], 16) for x in xrange(0, len(digest), 2)]

    