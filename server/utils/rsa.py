

import base64

from Crypto import Random
from Crypto.Cipher import PKCS1_v1_5
from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA


def encrypt_pkcs1_oaep(public_key, raw_data):
    with open(public_key, 'r') as pub_file:
        pub_key = RSA.importKey(pub_file.read())

    cipher = PKCS1_OAEP.new(pub_key)
    ciphertext = cipher.encrypt(raw_data)
    encoded_data = base64.b64encode(ciphertext)

    return encoded_data


def decrypt_pkcs1_oaep(private_key, encoded_data):
    encrypted_data = base64.b64decode(encoded_data)

    with open(private_key, 'r') as pvt_file:
        pvt_key = RSA.importKey(pvt_file.read())

    cipher = PKCS1_OAEP.new(pvt_key)
    raw_data = cipher.decrypt(encrypted_data)

    return raw_data


def encrypt_pkcs1_v1_5(public_key, raw_data):
    with open(public_key, 'r') as pub_file:
        pub_key = RSA.importKey(pub_file.read())

    h = SHA.new(raw_data)

    cipher = PKCS1_v1_5.new(pub_key)
    ciphertext = cipher.encrypt(raw_data + h.digest())
    encoded_data = base64.b64encode(ciphertext)

    return encoded_data


def decrypt_pkcs1_v1_5(private_key, encoded_data):
    encrypted_data = base64.b64decode(encoded_data)

    with open(private_key, 'r') as pvt_file:
        pvt_key = RSA.importKey(pvt_file.read())

    dsize = SHA.digest_size
    sentinel = Random.new().read(15 + dsize)

    cipher = PKCS1_v1_5.new(pvt_key)
    raw_data = cipher.decrypt(encrypted_data, sentinel)
    
    return raw_data
