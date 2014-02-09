from base64 import b64decode
import binascii
from hashlib import sha256

import base58


class BitcoinKeyConstants(object):
    NAME = "Bitcoin Main Net"
    PRIVATE_KEY_BYTE_PREFIX = 0x80  # = int(128) --> "5"


class BitcoinTestnetKeyConstants(object):
    NAME = "Bitcoin Test Net"
    PRIVATE_KEY_BYTE_PREFIX = 0xEF  # = int(239) --> "9"


class Key(object):
    def __init__(self, raw_key, constants):
        """Construct a Key.

        :param raw_key: The raw hex-encoded key
        :type raw_key: Hex string
        """
        self.raw_key = raw_key.upper()
        self.constants = constants

    def __eq__(self, other):
        return (self.raw_key == other.raw_key and
                self.constants == other.constants and
                type(self) == type(other))


class WIFKey(object):
    """Methods for dealing with WIF keys

    WIF is Wallet Import Format. It is a base58 encoded checksummed key.
    See https://en.bitcoin.it/wiki/Wallet_import_format for a full description.
    """
    @classmethod
    def _wif_checksum(cls, key_bytes):
        """Checksum an extended key.

        :param key_bytes: A byte array of an extended key
        :type key_bytes: A byte array, eg binascii.unhexlify('DEADBEEF')
        """
        # Double SHA256 the key
        hashed_extended_key_bytes = \
            sha256(sha256(key_bytes).digest()).digest()
        # The first four bytes of the hash is the checksum
        checksum_bytes = hashed_extended_key_bytes[:4]
        return checksum_bytes

    def export_to_wif(self):
        """Export a key to WIF."""
        # First add the network byte, creating the "extended key"
        network_hex_chars = binascii.hexlify(
            chr(self.constants.PRIVATE_KEY_BYTE_PREFIX))
        extended_key_hex = network_hex_chars + self.raw_key
        extended_key_bytes = binascii.unhexlify(extended_key_hex)
        # Get the checksum
        checksum_bytes = self._wif_checksum(extended_key_bytes)
        # Append the checksum to the extended key
        checksummed_extended_key_bytes = extended_key_bytes + checksum_bytes
        # And return the base58-encoded result
        return base58.b58encode(checksummed_extended_key_bytes)

    @classmethod
    def from_wif(cls, wif, constants=BitcoinKeyConstants):
        """Import a key in WIF format."""
        # Decode the base58 key into bytes
        checksummed_extended_key_bytes = base58.b58decode(wif)

        # Verify we're on the right network
        network_bytes = checksummed_extended_key_bytes[0]
        if (ord(network_bytes) != constants.PRIVATE_KEY_BYTE_PREFIX):
            raise cls.IncompatibleNetworkException(
                "Incorrect network. {net_name} expects a byte prefix of "
                "{expected_prefix}, but you supplied {given_prefix}".format(
                    net_name=constants.NAME,
                    expected_prefix=constants.PRIVATE_KEY_BYTE_PREFIX,
                    given_prefix=ord(network_bytes)))

        # The checksum of the given wif-key is the last 4 bytes
        checksum_bytes, extended_key_bytes = (
            checksummed_extended_key_bytes[-4:],
            checksummed_extended_key_bytes[:-4])
        # Verify the checksum
        calc_checksum_bytes = cls._wif_checksum(extended_key_bytes)
        if checksum_bytes != calc_checksum_bytes:
            raise cls.ChecksumException("%s != %s" % (
                binascii.hexlify(checksum_bytes),
                binascii.hexlify(calc_checksum_bytes)))

        # Drop the network bytes
        extended_key_bytes = extended_key_bytes[1:]
        # And we should finally have a valid key
        return cls(binascii.hexlify(extended_key_bytes), constants)

    class IncompatibleNetworkException(Exception):
        pass

    class ChecksumException(Exception):
        pass


class PrivateKey(Key, Base64KeyParser, WIFKey):
    def __init__(self, raw_key, constants=BitcoinKeyConstants):
        super(PrivateKey, self).__init__(raw_key, constants)


class KeyParseError(Exception):
    pass
