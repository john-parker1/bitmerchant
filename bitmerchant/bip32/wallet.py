from hashlib import sha256
import string
import random

from pycoin import wallet


def _random_wallet_secret(size=1024, chars=string.printable):
    """Generate a random key for a bitcoin wallet.

    TODO: Verify that this is a good idea.
    """
    return (sha256(''.join(random.choice(chars) for x in xrange(size)))
            .hexdigest())


def create_address(master_pub_key, address_id):
    """Create a new address from a public key.

    Args:
        master_pub_key: A master public key for a wallet generated by
            wallet.Wallet.public_copy()
        address_id: The ID of the user you want to generate an address for.
            Address IDs should be positive integers that can be associated
            with the account that you're creating an address for.

    Creating a new address is useful for merchants because it allows you to
    link a public bitcoin address with a user of your system without exposing
    your private key.

    To create a wallet see `bitmerchant.wallet.Wallet`.

    After backing up the keys, as detailed in Wallet's docs, give the master
    public key of your wallet as a parameter to this method.
    """
    wallet = Wallet.from_public_key(master_pub_key)
    return wallet.subkey(address_id).bitcoin_address()


def new_wallet(key=None):
    """Create a new BIP32 compliant Wallet.

    Args:
        key: The key to use to generate this wallet. It may be a long
            string. Do not use a phrase from a book or song, as that will
            be guessed and is not secure. My advice is to not supply this
            argument and let me generate a new random key for you.

    **WARNING**:

    When creating a new wallet you MUST back up the private key. If
    you don't then any coins sent to your address will be LOST FOREVER.

    You need to save the private key somewhere. It is OK to just write
    it down on a piece of paper! Don't share this key with anyone!

        >>> my_wallet = new_wallet(key='correct horse battery staple')
        >>> private, public = my_wallet.get_keys()
        >>> private  # doctest: +ELLIPSIS
        u'xprv9s21ZrQH143K2mDJW8vDeFwbyDbFv868mM2Zr87rJSTj8q16Unka...'
    """
    key = key or _random_wallet_secret()
    return Wallet.from_master_secret(key)


class Wallet(wallet.Wallet):
    def get_private_key(self):
        """Get the private key for this Wallet.

        DO NOT share this private key with anyone. For maximum security you
        should generate this key on a computer not connected to the internet.
        """
        return self.wallet_key(as_private=True)

    @classmethod
    def from_private_key(cls, key):
        """Load a Wallet from a private key."""
        w = cls.from_wallet_key(key)
        if not w.is_private:
            raise PrivateKeyException("The provided key is not a private key")
        return w

    def get_public_key(self):
        """Get the public key for this wallet.

        A public key for a BIP32 wallet allow you to generate new addresses
        without exposing your private key.
        """
        return self.wallet_key(as_private=False)

    @classmethod
    def from_public_key(cls, key):
        """Load a Wallet from a public key.

        This Wallet will not have the ability to spend coins, but only to
        generate new addresses at which to receive payments.

            >>> wallet = Wallet.from_public_key(
            ... u'xpub661MyMwAqRbcFrpiKz9aNJpRkABRXnfREvQqxxya6cdhyGUtx3eRZS'
            ... u'BGXcQgWLg8yY5dpNY2rjwEE6FbXJdqmL37qfkcBNUtbMQfArn7KRg')
            >>> wallet.is_private
            False
        """
        w = cls.from_wallet_key(key)
        if w.is_private:
            raise PublicKeyException("The provided key is a PRIVATE key!")
        return w

    def get_keys(self):
        """Get the keys necessary to rebuild this Wallet.

        >>> wallet = new_wallet(key='correct horse battery staple')
        >>> private, public = wallet.get_keys()
        >>> private  # doctest: +ELLIPSIS
        u'xprv9s21ZrQH143K2mDJW8vDeFwbyDbFv868mM2Zr87rJSTj8q16Unka...'
        >>> public  # doctest: +ELLIPSIS
        u'xpub661MyMwAqRbcFFHmcATE1PtLXFRkKaoz8ZxAeWXTrmzi1dLF2L4q...'
        """
        private = self.get_private_key()
        public = self.get_public_key()
        return private, public

    def __eq__(self, other):
        eq = (isinstance(other, self.__class__) and
              self.get_keys() == other.get_keys() and
              self.is_private == other.is_private and
              self.public_pair == other.public_pair and
              self.chain_code == other.chain_code and
              self.depth == other.depth and
              self.parent_fingerprint == other.parent_fingerprint and
              self.child_number == other.child_number)

        if self.is_private:
            eq = eq and (
                self.secret_exponent == other.secret_exponent)

        return eq


class PrivateKeyException(Exception):
    """Exception for problems with a private key."""


class PublicKeyException(Exception):
    """Exception for problems with a public key."""
