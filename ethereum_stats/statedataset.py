import logging
import warnings

import numpy as np
import pandas as pd
import rlp
from eth_utils import (encode_hex, to_canonical_address, decode_hex)
from ethereum import utils
from ethereum.trie import Trie

BLANK_ROOT = encode_hex(utils.sha3rlp(b''))
BLANK_CODE = encode_hex(utils.sha3(b''))
BLANK_RLP = rlp.encode(b'')
ACCOUNT_LENGTH = 42


class Account:
    def __init__(self, address, nonce=0, balance=0, storage_root=BLANK_ROOT, contract_code=BLANK_CODE,
                 is_in_db=False, is_address_in_db=False):
        """
        :type nonce: int
        :type address: str
        :type balance: int
        :type storage_root: str
        :type contract_code: str
        :type is_in_db: bool
        """
        self.address = address
        self.nonce = nonce
        self.balance = balance
        self.storage_root = storage_root
        self.contract_code = contract_code
        self.is_address_in_db = is_address_in_db
        self.is_in_db = is_in_db
        logging.info('New account instance \n\taddress: %s \n\tnonce: %i\n\tbalance: %i\n\tstorageRoot: '
                     '%s\n\tcontractCode: %s',
                     address, nonce, balance, storage_root, contract_code)

    @classmethod
    def from_trie(cls, db, k, rlp_data):
        try:
            address = encode_hex(db.get(b'secure-key-' + k))
            key_in_db = True
        except KeyError:
            address = encode_hex(k)
            key_in_db = False
            logging.info('secure-key- %s not found', k)
        rlp_fields = rlp.decode(rlp_data)
        nonce = int.from_bytes(rlp_fields[0], byteorder='big') if rlp_fields[0] != b'' else 0
        balance = int.from_bytes(rlp_fields[1], byteorder='big') if rlp_fields[1] != b'' else 0
        storage_root = encode_hex(rlp_fields[2])
        contract_code = encode_hex(rlp_fields[3])
        account = cls(address, nonce, balance, storage_root, contract_code, True, key_in_db)
        return account

    @classmethod
    def not_found(cls, address):
        warnings.warn('\n\tAccount %s not found', address)
        return cls(address=address, is_in_db=False)

    @property
    def is_contract(self):
        return self.contract_code != BLANK_CODE

    def code_size(self, db):
        if self.is_contract:
            try:
                code = db.get(decode_hex(self.contract_code))
                size = len(code)
            except KeyError:
                size = 0
                logging.warning('contract code key %s not in database', self.contract_code)

        else:
            size = 0
        return size

    def storage_size(self, db):
        size = 0

        if self.is_contract:
            try:
                storage_trie = Trie(db, decode_hex(self.storage_root))
            except KeyError:
                logging.warning('storage root %s not in database', self.storage_root)
                return size

            try:
                trie_dict = storage_trie.to_dict()
            except KeyError:
                logging.warning('storage root %s integrity error in database', self.storage_root)
                return size

            size = len(trie_dict)

        return size


class StateDataset:
    def __init__(self, db, state_root):
        self.db = db
        if isinstance(state_root, str):
            self.state_root = decode_hex(state_root)
        else:
            self.state_root = state_root

        try:
            self.trie = Trie(db, self.state_root)
            self.is_in_db = True
        except KeyError:
            self.state_root = None
            self.is_in_db = False
            logging.warning('State root %s not in database', self.state_root)

        logging.info('State created')

    def to_dict(self):
        state_dict = dict()
        for k in self.trie:
            try:
                acc = Account.from_trie(self.db, k, self.trie[k])
            except KeyError:
                logging.error('value in trie for %s not found', k)
            state_dict[acc.address] = (acc.nonce, acc.balance, acc.storage_root, acc.contract_code,
                                       acc.is_address_in_db)
        return state_dict

    def to_panda_dataframe(self):
        trie_dict = self.trie.to_dict()
        size = len(trie_dict)
        dtype = [('sha3_account', np.str, ACCOUNT_LENGTH), ('account', np.str, ACCOUNT_LENGTH), ('nonce', np.float),
                 ('balance', np.float),
                 ('is_contract', np.bool), ('code_size', np.float), ('storage_size', np.float), ('key_in_db', np.bool)]
        arr = np.zeros(size, dtype=dtype)
        i = 0
        for k in self.trie:
            try:
                account = Account.from_trie(self.db, k, self.trie[k])
            except KeyError:
                logging.error('value in trie for %s not found', k)
                continue
            arr[i] = (encode_hex(k), account.address, account.nonce, account.balance, account.is_contract,
                      account.code_size(self.db), account.storage_size(self.db), account.is_address_in_db)
            i += 1
        df = pd.DataFrame.from_records(arr, index='sha3_account')

        return df

    def get_account(self, address):
        key = utils.sha3(to_canonical_address(address))
        try:
            rlp_data = self.trie.get(key)
            acc = Account.from_trie(self.db, key, rlp_data)
        except KeyError:
            acc = Account.notFound(address)
        return acc

