import hashlib
from Crypto.PublicKey import RSA

# CRYPTO settings
HASH_ALG = 'sha256'
SIG_ALG = 'RSA-SHA256'


def hashe(s, encoding='hex'):
    return hashlib.new(HASH_ALG, s.encode()).hexdigest()


def generateKeypair():
    key = RSA.generate(1024)
    return {
        'public': key.publickey().export_key(format='PEM'),
        'private': key.export_key(format='PEM')
    }


def sign(privKey, msg):
    signer = RSA.import_key(privKey)
    string = (msg if isinstance(msg, str) else str(msg))
    return signer.sign(string.encode(), '')


def verifySignature(pubKey, msg, sig):
    verifier = RSA.import_key(pubKey)
    string = (msg if isinstance(msg, str) else str(msg))
    return verifier.verify(string.encode(), sig)


def calcAddress(key):
    addr = hashe(str(key), 'base64')
    # print(f"Generating address {addr} from {key}")
    return addr


def addressMatchesKey(addr, pubKey):
    return addr == calcAddress(pubKey.decode())
