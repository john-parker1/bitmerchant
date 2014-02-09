import base64
import binascii
from mock import patch
from unittest import TestCase

from bitmerchant.wallet.keys import BitcoinTestnetKeyConstants
from bitmerchant.wallet.keys import PrivateKey
from bitmerchant.wallet.keys import PublicKey
from bitmerchant.wallet.keys import WIFKey


class _TestPrivateKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.key = PrivateKey(
            "0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D")


class _TestPublicKeyBase(TestCase):
    def setUp(self):
        # This private key chosen from the bitcoin docs:
        # https://en.bitcoin.it/wiki/Wallet_import_format
        self.private_key = PrivateKey(
            "0C28FCA386C7A227600B2FE50B7CAE11EC86D3BF1FBE471BE89827E19D72AA1D")
        self.public_key = PublicKey(
            "04"
            "50863AD64A87AE8A2FE83C1AF1A8403CB53F53E486D8511DAD8A04887E5B2352"
            "2CD470243453A299FA9E77237716103ABC11A1DF38855ED6F2EE187E9C582BA6")


class TestPrivateKey(_TestPrivateKeyBase):
    def test_raw_key_b64(self):
        key = self.key.key
        b64_key = base64.b64encode(key)
        self.assertEqual(PrivateKey(b64_key), self.key)

    def test_raw_key_hex(self):
        key = self.key.key
        self.assertEqual(PrivateKey(key), self.key)

    def test_raw_key_hex_bytes(self):
        key = binascii.unhexlify(self.key.key)
        self.assertEqual(PrivateKey(key), self.key)


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
            WIFKey.IncompatibleNetworkException, PrivateKey.from_wif,
            self.key.export_to_wif(), BitcoinTestnetKeyConstants)

    def test_import_wif_network(self):
        # Make a wif for bitcoin testnet:
        testnet_key = PrivateKey(
            raw_key=self.key.key, constants=BitcoinTestnetKeyConstants)
        testnet_wif = testnet_key.export_to_wif()
        key = PrivateKey.from_wif(testnet_wif, BitcoinTestnetKeyConstants)
        self.assertEqual(testnet_key, key)

    def test_bad_checksum(self):
        with patch('bitmerchant.wallet.keys.WIFKey._wif_checksum',
                   return_value=binascii.unhexlify('FFFFFFFF')):
            wif = self.key.export_to_wif()
        self.assertRaises(WIFKey.ChecksumException, PrivateKey.from_wif, wif)


class TestPublicKey(_TestPublicKeyBase):
    def test_address(self):
        expected_address = "16UwLL9Risc3QfPqBUvKofHmBQ7wMtjvM"
        actual_address = self.public_key.to_address()
        self.assertEqual(expected_address, actual_address)
