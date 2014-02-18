import binascii
from unittest import TestCase

import base58

from bitmerchant.wallet.network import BitcoinTestNet
from bitmerchant.wallet.keys import ChecksumException
from bitmerchant.wallet.keys import IncompatibleNetworkException
from bitmerchant.wallet.keys import KeyParseError  # TODO test this
from bitmerchant.wallet.keys import PrivateKey
from bitmerchant.wallet.keys import ExtendedPrivateKey
from bitmerchant.wallet.keys import PublicKey
from bitmerchant.wallet.utils import long_to_hex


class _TestPrivateKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.expected_key = \
            "0c28fca386c7a227600b2fe50b7cae11ec86d3bf1fbe471be89827e19d72aa1d"
        self.key = PrivateKey(long(self.expected_key, 16))


class _TestPublicKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.expected_private_key = \
            "18e14a7b6a307f426a94f8114701e7c8e774e7f9a47e2c2035db29a206321725"
        self.private_key = PrivateKey(long(self.expected_private_key, 16))
        self.public_key = PublicKey.from_hex_key(
            "04"
            "50863ad64a87ae8a2fe83c1af1a8403cb53f53e486d8511dad8a04887e5b2352"
            "2cd470243453a299fa9e77237716103abc11a1df38855ed6f2ee187e9c582ba6")


class TestPrivateKey(_TestPrivateKeyBase):
    def test_raw_key_hex(self):
        exp = self.key.private_exponent
        self.assertEqual(PrivateKey(exp), self.key)

    def test_raw_key_hex_bytes(self):
        key = binascii.unhexlify(self.key.key)
        self.assertEqual(PrivateKey.from_hex_key(key), self.key)

    def test_from_master_password(self):
        password = "correct horse battery staple"
        expected_wif = "5KJvsngHeMpm884wtkJNzQGaCErckhHJBGFsvd3VyK5qMZXj3hS"
        expected_pub_address = "1JwSSubhmg6iPtRjtyqhUYYH7bZg3Lfy1T"

        key = PrivateKey.from_master_password(password)
        self.assertEqual(key.export_to_wif(), expected_wif)
        self.assertEqual(
            key.get_public_key().to_address(), expected_pub_address)


class TestWIF(_TestPrivateKeyBase):
    def setUp(self):
        super(TestWIF, self).setUp()
        self.expected_wif = \
            '5HueCGU8rMjxEXxiPuD5BDku4MkFqeZyd4dZ1jvhTVqvbTLvyTJ'

    def test_export_to_wif(self):
        self.assertEqual(
            self.key.export_to_wif(),
            self.expected_wif)

    def test_import_wif(self):
        key = PrivateKey.from_wif(self.expected_wif)
        self.assertEqual(key, self.key)

    def test_import_wif_invalid_network(self):
        self.assertRaises(
            IncompatibleNetworkException, PrivateKey.from_wif,
            self.key.export_to_wif(), BitcoinTestNet)

    def test_import_wif_network(self):
        # Make a wif for bitcoin testnet:
        testnet_key = PrivateKey(
            self.key.private_exponent, network=BitcoinTestNet)
        testnet_wif = testnet_key.export_to_wif()
        # We should be able to load it properly
        key = PrivateKey.from_wif(testnet_wif, BitcoinTestNet)
        self.assertEqual(testnet_key, key)

    def test_bad_checksum(self):
        wif = self.key.export_to_wif()
        bad_checksum = base58.b58encode(binascii.unhexlify('FFFFFFFF'))
        wif = wif[:-8] + bad_checksum
        self.assertRaises(ChecksumException, PrivateKey.from_wif, wif)


class TestPublicKey(_TestPublicKeyBase):
    def test_leading_zeros(self):
        # This zero-leading x coordinate generated by:
        # pvk = '18E14A7B6A307F426A94F8114701E7C8E774E7F9A47E2C2035DB29A206321725'  # nopep8
        # pubkey = Public_key(SECP256k1.generator, SECP256k1.generator * long(pvk, 16))  # nopep8
        # for i in range(1, 10000):
        # x = (pubkey.point * i).x()
        # k = keys.long_to_hex(x, 64)
        # if k.startswith('0'):
        #     print i
        #     break
        expected_key = (
            "04"
            "02cbfd5410fd04973c096a4275bf75070955ebd689f316a6fbd449980ba7b756"
            "c559764e5c367c03e002751aaf4ef8ec40fe97cda9b2d3f14fdd4cd244e8fcd2")
        public_key = PublicKey.from_hex_key(expected_key)
        self.assertEqual(public_key.key, expected_key)

    def test_address(self):
        expected_address = "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM"
        actual_address = self.public_key.to_address()
        self.assertEqual(expected_address, actual_address)

    def test_private_to_public(self):
        self.assertEqual(
            self.private_key.get_public_key(),
            self.public_key)

    def test_unhexlified_key(self):
        key_bytes = binascii.unhexlify(self.public_key.key)
        self.assertEqual(
            PublicKey.from_hex_key(key_bytes),
            self.public_key)

    def test_bad_key(self):
        self.assertRaises(KeyParseError, PublicKey.from_hex_key, 'badkey')

    def test_bad_network_key(self):
        key = self.public_key.key
        # Change the network constant
        key = "00" + key[2:]
        self.assertRaises(IncompatibleNetworkException,
                          PublicKey.from_hex_key, key)


class TestExtendedPrivateKey(TestCase):
    def setUp(self):
        self.expected_key = (
            "0488ade4"  # BitcoinMainNet version
            "00"  # depth
            "00000000"  # parent fingerprint
            "00000000"  # child_number
            # chain_code
            "873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508"
            "00"  # key identifier
            # private exponent
            "e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35")
        self.master_key = ExtendedPrivateKey.from_hex_key(self.expected_key)

    def test_serialize_master_key(self):
        self.assertEqual(self.expected_key, self.master_key.serialize())

    def test_from_master_secret(self):
        secret = binascii.unhexlify('000102030405060708090a0b0c0d0e0f')
        self.assertEqual(ExtendedPrivateKey.from_master_secret(secret),
                         self.master_key)

    def test_invalid_network_prefix(self):
        pass

    def test_invalid_key_data_prefix(self):
        pass

    def test_invalid_fingerprint(self):
        pass

    def test_identifier(self):
        pass

    def test_fingerprint(self):
        pass


class TestExtendedPrivateKeyVectors(TestCase):
    def setUp(self):
        self.master_key = ExtendedPrivateKey.from_master_secret(
            binascii.unhexlify('000102030405060708090a0b0c0d0e0f'))

    def _test_vector(self, key, id_hex, fingerprint, address,
                     secret_key_hex, secret_key_wif,
                     pubkey_hex, chaincode_hex,
                     pubkey_serialized_hex, pubkey_base58,
                     private_serialized_hex, private_base58,
                     ):
        self.assertEqual(key.identifier, id_hex)
        self.assertEqual(key.fingerprint, fingerprint)
        self.assertEqual(key.get_public_key().to_address(),
                         address)

        self.assertEqual(key.key, secret_key_hex)
        self.assertEqual(key.export_to_wif(), secret_key_wif)

        self.assertEqual(key.get_public_key().key, pubkey_hex)
        self.assertEqual(key.chain_code, chaincode_hex)

        self.assertEqual(
            key.get_public_key().serialize(),
            pubkey_serialized_hex)
        self.assertEqual(
            key.get_public_key().serialize_b58(), pubkey_base58)
        self.assertEqual(key.serialize(), private_serialized_hex)
        self.assertEqual(key.serialize_b58(), private_base58)

    def test_m(self):
        """[Chain m]"""
        id_hex = '3442193e1bb70916e914552172cd4e2dbc9df811'
        fingerprint = '0x3442193e'
        address = '15mKKb2eos1hWa6tisdPwwDC1a5J1y9nma'

        secret_key_hex = \
            'e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35'
        secret_key_wif = 'L52XzL2cMkHxqxBXRyEpnPQZGUs3uKiL3R11XbAdHigRzDozKZeW'

        pubkey_hex = (
            '03'
            '39a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2')

        chaincode_hex = \
            '873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508'

        pubkey_serialized_hex = (
            '0488b21e000000000000000000'
            '873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508'
            '03'
            '39a36013301597daef41fbe593a02cc513d0b55527ec2df1050e2e8ff49c85c2')
        pubkey_base58 = (
            'xpub661MyMwAqRbcFtXgS5sYJABqqG9YLmC4Q1Rdap9gSE8NqtwybGhePY2gZ29E'
            'SFjqJoCu1Rupje8YtGqsefD265TMg7usUDFdp6W1EGMcet8')
        private_serialized_hex = (
            '0488ade4000000000000000000'
            '873dff81c02f525623fd1fe5167eac3a55a049de3d314bb42ee227ffed37d508'
            '00'
            'e8f32e723decf4051aefac8e2c93c9c5b214313817cdb01a1494b917c8436b35')
        private_base58 = (
            'xprv9s21ZrQH143K3QTDL4LXw2F7HEK3wJUD2nW2nRk4stbPy6cq3jPPqjiChkVv'
            'vNKmPGJxWUtg6LnF5kejMRNNU3TGtRBeJgk33yuGBxrMPHi')
        self._test_vector(
            self.master_key, id_hex, fingerprint, address,
            secret_key_hex, secret_key_wif,
            pubkey_hex, chaincode_hex,
            pubkey_serialized_hex, pubkey_base58,
            private_serialized_hex, private_base58)

    def test_m_0p(self):
        key = (
            "0488ade4013442193e80000000"
            "47fdacbd0f1097043b78c63c20c34ef4ed9a111d980047ad16282c7ae6236141"
            "00"
            "edb2e14f9ee77d26dd93b4ecede8d16ed408ce149b6cd80b0715a2d911a0afea")
        pk = ExtendedPrivateKey.from_hex_key(key)
        self.assertEqual(pk.serialize(), key)
        self.assertEqual(pk.parent_fingerprint,
                         self.master_key.fingerprint.replace("0x", ""))
        self.assertEqual(pk.child_number, long_to_hex(long(0x80000000), 8))

    def test_m_0p_1(self):
        key = (
            "0488ade4025c1bd64800000001"
            "2a7857631386ba23dacac34180dd1983734e444fdbf774041578e9b6adb37c19"
            "00"
            "3c6cb8d0f6a264c91ea8b5030fadaa8e538b020f0a387421a12de9319dc93368")
        pk = ExtendedPrivateKey.from_hex_key(key)
        self.assertEqual(pk.serialize(), key)
        self.assertEqual(pk.child_number, long_to_hex(1, 8))

    def test_m_0p_1_2p(self):
        key = (
            "0488ade403bef5a2f980000002"
            "04466b9cc8e161e966409ca52986c584f07e9dc81f735db683c3ff6ec7b1503f"
            "00"
            "cbce0d719ecf7431d88e6a89fa1483e02e35092af60c042b1df2ff59fa424dca")
        pk = ExtendedPrivateKey.from_hex_key(key)
        self.assertEqual(pk.serialize(), key)
        self.assertEqual(pk.child_number, long_to_hex(long(0x80000000 + 2), 8))
