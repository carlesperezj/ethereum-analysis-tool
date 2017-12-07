import logging
from datetime import datetime

import rlp
from eth_utils import (encode_hex)

from ethereum_stats.statedataset import StateDataset

HEADER_PREFIX = b'h'
BODY_PREFIX = b'b'
BLOCK_HASH_PREFIX = b'H'
LAST_HEADER_KEY = b'LastHeader'
NUM_SUFFIX = b'n'
NUM_LEN_BYTES = 8

date_formats = ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d', '%d/%m/%Y %H:%M:%S', '%d/%m/%Y')


class BlockHeader:
    def __init__(self, blk_hash='', parent_hash='', ommers_hash='',
                 beneficiary='', state_root='', transactions_root='',
                 receipts_root='', logs_bloom='', difficulty=0,
                 number=-1, gas_limit=-1, gas_used=-1, timestamp=0,
                 extra_data='', mix_hash='', nonce=''):
        self.blk_hash = blk_hash
        self.parent_hash = parent_hash
        self.ommers_hash = ommers_hash
        self.beneficiary = beneficiary
        self.state_root = state_root
        self.transactions_root = transactions_root
        self.receipts_root = receipts_root
        self.logs_bloom = logs_bloom
        self.difficulty = difficulty
        self.number = number
        self.gas_limit = gas_limit
        self.gas_used = gas_used
        self.timestamp = timestamp
        self.extra_data = extra_data
        self.mix_hash = mix_hash
        self.nonce = nonce

        logging.info('BlockHeader created\n\tblk_hash %s\n\tparent_hash %s\n\tommers_hash %s\n\tbeneficiary %s'
                     '\n\tstate_root %s\n\ttransactions_root %s \n\treceipts_root %s'
                     '\n\tlogs_bloom %s\n\tdifficulty %i\n\tnumber %i\n\tgas_limit %i\n\tgas_used %i'
                     '\n\ttimestamp %s\n\textra_data %s\n\tmix_hash %s\n\tnonce %s',
                     blk_hash, parent_hash, ommers_hash, beneficiary, state_root, transactions_root, receipts_root,
                     logs_bloom, difficulty, number, gas_limit, gas_used,
                     datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%dT%H:%M:%S %Z'), extra_data, mix_hash, nonce)

    @classmethod
    def from_rlp(cls, blk_hash, rlp_data):
        a = rlp.decode(rlp_data)
        parent_hash = encode_hex(a[0]) if a[0] != b'' else ''
        ommers_hash = encode_hex(a[1]) if a[1] != b'' else ''
        beneficiary = encode_hex(a[2]) if a[2] != b'' else ''
        state_root = encode_hex(a[3]) if a[3] != b'' else ''
        transactions_root = encode_hex(a[4]) if a[4] != b'' else ''
        receipts_root = encode_hex(a[5]) if a[5] != b'' else ''
        logs_bloom = encode_hex(a[6]) if a[6] != b'' else ''
        difficulty = int.from_bytes(a[7], byteorder='big') if a[7] != b'' else -1
        number = int.from_bytes(a[8], byteorder='big') if a[8] != b'' else -1
        gas_limit = int.from_bytes(a[9], byteorder='big') if a[9] != b'' else 0
        gas_used = int.from_bytes(a[10], byteorder='big') if a[10] != b'' else 0
        timestamp = int.from_bytes(a[11], byteorder='big') if a[11] != b'' else 0
        extra_data = encode_hex(a[12]) if a[12] != b'' else ''
        mix_hash = encode_hex(a[13]) if a[13] != b'' else ''
        nonce = encode_hex(a[14]) if a[14] != b'' else ''

        blk_header = cls(blk_hash, parent_hash, ommers_hash,
                         beneficiary, state_root, transactions_root,
                         receipts_root, logs_bloom, difficulty,
                         number, gas_limit, gas_used, timestamp,
                         extra_data, mix_hash, nonce)

        return blk_header

    @staticmethod
    def get_block_header_by_number(db, blk_nbr):
        blk_nbr_big_endian = blk_nbr.to_bytes(NUM_LEN_BYTES, byteorder='big')
        key = HEADER_PREFIX + blk_nbr_big_endian + NUM_SUFFIX
        blk_hash = db.get(key)
        key = HEADER_PREFIX + blk_nbr_big_endian + blk_hash
        header_rlp = db.get(key)
        return BlockHeader.from_rlp(encode_hex(blk_hash), header_rlp)

    @staticmethod
    def get_latest_block_header_number(db):
        key = LAST_HEADER_KEY
        blk_hash = db.get(key)
        key = BLOCK_HASH_PREFIX + blk_hash
        blk_nbr_big_endian = db.get(key)
        return int.from_bytes(blk_nbr_big_endian, byteorder='big')

    @staticmethod
    def get_latest_block_header(db):
        key = LAST_HEADER_KEY
        blk_hash = db.get(key)
        key = BLOCK_HASH_PREFIX + blk_hash
        blk_nbr_big_endian = db.get(key)
        key = HEADER_PREFIX + blk_nbr_big_endian + blk_hash
        header_rlp = db.get(key)
        return BlockHeader.from_rlp(encode_hex(blk_hash), header_rlp)

    @staticmethod
    def get_block_number_by_timestamp(db, timestamp, top):
        last_nbr = BlockHeader.get_latest_block_header(db).number
        first_nbr = 0
        blk_number = first_nbr
        while first_nbr <= last_nbr:
            mid_nbr = (first_nbr + last_nbr) // 2
            mid_timestamp = BlockHeader.get_block_header_by_number(db, mid_nbr).timestamp
            if mid_timestamp < timestamp:
                first_nbr = mid_nbr + 1
            elif mid_timestamp > timestamp:
                last_nbr = mid_nbr - 1
            else:
                blk_number = mid_nbr
                break
        if blk_number == 0:
            # if mid_nbr < last_nbr and top:
            #     blk_number = last_nbr
            # elif mid_nbr < last_nbr and not top:
            #     blk_number = last_nbr + 1
            # elif mid_nbr == last_nbr and top:
            #     blk_number = mid_nbr - 1
            # elif mid_nbr == last_nbr and not top:
            #     blk_number = mid_nbr
            # elif mid_nbr > last_nbr and top:
            #     blk_number = last_nbr - 1
            # elif mid_nbr > last_nbr and not top:
            #     blk_number = last_nbr
            if mid_timestamp < timestamp and top:
                blk_number = mid_nbr
            elif mid_timestamp < timestamp and not top:
                blk_number = mid_nbr + 1
            elif mid_timestamp > timestamp and not top:
                blk_number = mid_nbr
            elif mid_timestamp > timestamp and top:
                blk_number = mid_nbr - 1

        return blk_number


class BlockRange:
    def __init__(self, db, lower_blk_nbr, upper_blk_nbr):
        if lower_blk_nbr > upper_blk_nbr:
            raise ValueError('Lower limit cannot be greater than upper limit')
        self.db = db
        self.lower_blk_nbr = lower_blk_nbr
        self.current_blk_nbr = lower_blk_nbr
        self.upper_blk_nbr = upper_blk_nbr

        logging.info('Block range created from %i to %i', self.lower_blk_nbr, self.upper_blk_nbr)

    @classmethod
    def date_range(cls, db, lower_date, upper_date):
        lower_date_timestamp = None
        upper_date_timestamp = None

        for date_format in date_formats:
            try:
                lower_date_timestamp = datetime.strptime(lower_date, date_format).timestamp()
                break
            except ValueError:
                pass
        if lower_date_timestamp is None:
            raise ValueError('Cannot parse date')

        for date_format in date_formats:
            try:
                upper_date_timestamp = datetime.strptime(upper_date, date_format).timestamp()
                break
            except ValueError:
                pass
        if upper_date_timestamp is None:
            raise ValueError('Cannot parse date')

        lower_blk_nbr = BlockHeader.get_block_number_by_timestamp(db, lower_date_timestamp, False)
        upper_blk_nbr = BlockHeader.get_block_number_by_timestamp(db, upper_date_timestamp, True)
        return BlockRange(db, lower_blk_nbr, upper_blk_nbr)

    @staticmethod
    def get_first_state_in_db(db):
        blk = BlockHeader.get_latest_block_header_number(db)
        state = StateDataset(db, blk.state_root)
        step = -1
        while state.is_in_db:
            blk = BlockHeader.get_block_header_by_number(blk.number + step)
             


    def __iter__(self):
        return self

    def __next__(self):
        if self.current_blk_nbr > self.upper_blk_nbr:
            raise StopIteration
        else:
            self.current_blk_nbr += 1
            return BlockHeader.get_block_header_by_number(self.db, self.current_blk_nbr - 1)
