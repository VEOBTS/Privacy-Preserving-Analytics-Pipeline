import os
import json
import phe.paillier as paillier
from dotenv import load_dotenv

load_dotenv()

KEY_FILE_PATH = os.getenv('KEY_FILE_PATH', './keys/paillier_keys.json')

# These variables hold the loaded keys
_public_key = None
_private_key = None


def _ensure_key_dir():
    """Create the keys directory if it does not exist."""
    key_dir = os.path.dirname(KEY_FILE_PATH)
    if key_dir and not os.path.exists(key_dir):
        os.makedirs(key_dir, exist_ok=True)


def load_or_generate_keys():
    """
    Called once when the server starts.
    Loads the keypair from disk if it exists.
    Generates and saves a new keypair if it does not.
    """
    global _public_key, _private_key

    _ensure_key_dir()

    if os.path.exists(KEY_FILE_PATH):
        print(f'Loading Paillier keys from {KEY_FILE_PATH}')
        with open(KEY_FILE_PATH, 'r') as f:
            data = json.load(f)
        pub_data = data['public_key']
        priv_data = data['private_key']
        _public_key = paillier.PaillierPublicKey(n=int(pub_data['n']))
        _private_key = paillier.PaillierPrivateKey(
            _public_key,
            p=int(priv_data['p']),
            q=int(priv_data['q'])
        )
    else:
        print('Generating new Paillier keypair (this may take a few seconds)...')
        # key_size=2048 is the minimum secure size
        _public_key, _private_key = paillier.generate_paillier_keypair(n_length=2048)
        data = {
            'public_key': {'n': str(_public_key.n)},
            'private_key': {
                'p': str(_private_key.p),
                'q': str(_private_key.q)
            }
        }
        with open(KEY_FILE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print(f'Keypair saved to {KEY_FILE_PATH}')


def get_public_key() -> paillier.PaillierPublicKey:
    """Returns the loaded public key. Call load_or_generate_keys() first."""
    if _public_key is None:
        raise RuntimeError('Keys not loaded. Call load_or_generate_keys() first.')
    return _public_key


def get_private_key() -> paillier.PaillierPrivateKey:
    """Returns the loaded private key. Used only by the aggregator."""
    if _private_key is None:
        raise RuntimeError('Keys not loaded. Call load_or_generate_keys() first.')
    return _private_key


def encrypt_integer(value: int) -> str:
    """Encrypts an integer and returns the ciphertext as a string."""
    pub = get_public_key()
    encrypted = pub.encrypt(value)
    return str(encrypted.ciphertext())


def decrypt_aggregate(ciphertext_str: str) -> float:
    """Decrypts a single aggregate ciphertext string to a float."""
    pub = get_public_key()
    priv = get_private_key()
    # Recreate the EncryptedNumber object from the stored ciphertext string
    enc_num = paillier.EncryptedNumber(pub, int(ciphertext_str))
    return priv.decrypt(enc_num)


def add_encrypted_numbers(ciphertext_list: list[str]) -> str:
    """
    Homomorphically adds a list of ciphertexts.
    Returns the resulting aggregate ciphertext as a string.
    This uses Paillier's additive property: Enc(a) + Enc(b) decrypts to (a + b).
    """
    if not ciphertext_list:
        return None

    pub = get_public_key()

    # Start with the first ciphertext
    current = paillier.EncryptedNumber(pub, int(ciphertext_list[0]))

    # Add each remaining ciphertext to the running total
    for ct_str in ciphertext_list[1:]:
        next_enc = paillier.EncryptedNumber(pub, int(ct_str))
        current = current + next_enc  # phe library overloads the + operator

    return str(current.ciphertext())