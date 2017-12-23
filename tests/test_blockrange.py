from datetime import datetime
import random

from pytest import raises

from ethereum_stats.blockrange import BlockHeader, BlockRange

NBR_RANDOM_TESTS = 5


def compare_blk_hdrs(w3_blk, blk):
    assert blk.blk_hash == w3_blk['hash']
    assert blk.parent_hash == w3_blk['parentHash']
    assert blk.ommers_hash == w3_blk['sha3Uncles']
    assert blk.beneficiary == w3_blk['miner']
    assert blk.state_root == w3_blk['stateRoot']
    assert blk.transactions_root == w3_blk['transactionsRoot']
    assert blk.receipts_root == w3_blk['receiptsRoot']
    assert blk.logs_bloom == w3_blk['logsBloom']
    assert blk.difficulty == w3_blk['difficulty']
    assert blk.number == w3_blk['number']
    assert blk.gas_limit == w3_blk['gasLimit']
    assert blk.gas_used == w3_blk['gasUsed']
    assert blk.timestamp == w3_blk['timestamp']
    assert blk.extra_data == w3_blk['extraData']
    assert blk.mix_hash == w3_blk['mixHash']
    assert blk.nonce == w3_blk['nonce']


def test_get_latest_block_header_number(initial_scenario):
    w3_latest_block = initial_scenario.get_block()
    assert w3_latest_block['number'] == BlockHeader.get_latest_block_header_number(initial_scenario.get_db())


def test_get_block_number_by_timestamp(initial_scenario):
    test_db = initial_scenario.get_db()
    latest_block_nbr = BlockHeader.get_latest_block_header_number(test_db)
    nbr_test = 0
    while nbr_test < NBR_RANDOM_TESTS:
        test_blk_nbr = random.randrange(2, latest_block_nbr)
        test_blk = BlockHeader.get_block_header_by_number(test_db, test_blk_nbr)
        test_blk_ts = test_blk.timestamp
        test_blk_plus_nbr = test_blk_nbr + 1
        test_blk_plus = BlockHeader.get_block_header_by_number(test_db, test_blk_plus_nbr)
        test_blk_plus_ts = test_blk_plus.timestamp
        test_blk_minus_nbr = test_blk_nbr - 1
        test_blk_minus = BlockHeader.get_block_header_by_number(test_db, test_blk_minus_nbr)
        test_blk_minus_ts = test_blk_minus.timestamp
        # on private network blocks can be created less than one second apart, unreasonable in other networks.
        if (test_blk_ts - test_blk_minus_ts) < 2 or (test_blk_plus_ts - test_blk_ts) < 2:
            continue
        test_ts = (test_blk_ts + test_blk_plus_ts) // 2
        # test ts is upper limit of range, thus we expect to find the block to the 'left'
        assert test_blk_nbr == BlockHeader.get_block_number_by_timestamp(test_db, test_ts, True)
        # test ts is lower limit of range, thus we expect to find the block to the 'right'
        assert test_blk_plus_nbr == BlockHeader.get_block_number_by_timestamp(test_db, test_ts, False)
        test_ts = (test_blk_minus_ts + test_blk_ts) // 2
        # test ts is lower limit of range, thus we expect to find the block to the 'right'
        assert test_blk_nbr == BlockHeader.get_block_number_by_timestamp(test_db, test_ts, False)
        # test ts is upper limit of range, thus we expect to find the block to the 'left'
        assert test_blk_minus_nbr == BlockHeader.get_block_number_by_timestamp(test_db, test_ts, True)
        nbr_test += 1


def test_get_latest_block_header(initial_scenario):
    w3_latest_block = initial_scenario.get_block()
    latest_block = BlockHeader.get_latest_block_header(initial_scenario.get_db())
    compare_blk_hdrs(w3_latest_block, latest_block)


def test_block_header(initial_scenario):
    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_block_with_txn = False
        while not is_block_with_txn:
            w3_blk = initial_scenario.get_block(random.randrange(1, latest_block_nbr))
            if len(w3_blk['transactions']) > 0:
                is_block_with_txn = True
        blk = BlockHeader.get_block_header_by_number(initial_scenario.get_db(), w3_blk['number'])
        compare_blk_hdrs(w3_blk, blk)


def test_block_range(initial_scenario):
    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_proper_range = False
        while not is_proper_range:
            lower = random.randrange(1, latest_block_nbr)
            upper = random.randrange(1, latest_block_nbr)
            if upper > lower:
                is_proper_range = True
        for blk in BlockRange(initial_scenario.get_db(), lower, upper):
            w3_blk = initial_scenario.get_block(blk.number)
            compare_blk_hdrs(w3_blk, blk)
        with raises(ValueError, message='Lower limit cannot be greater than upper limit'):
            BlockRange(initial_scenario.get_db(), upper, lower)


def test_date_range(initial_scenario):
    test_db = initial_scenario.get_db()
    with raises(ValueError, message='Cannot parse date'):
        BlockRange.date_range(test_db, '2017/11/3', '2017/11/4')
    with raises(ValueError, message='Lower limit cannot be greater than upper limit'):
        BlockRange.date_range(test_db, '2017-11-5', '2017-11-4')

    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_proper_range = False
        while not is_proper_range:
            lower = random.randrange(1, latest_block_nbr)
            upper = random.randrange(1, latest_block_nbr)
            if upper > lower:
                is_proper_range = True
        w3_blk_lower = initial_scenario.get_block(lower)
        w3_ts_lower = w3_blk_lower['timestamp']
        lower_date = datetime.utcfromtimestamp(w3_ts_lower).strftime('%Y-%m-%dT%H:%M:%S')
        w3_blk_upper = initial_scenario.get_block(upper)
        w3_ts_upper = w3_blk_upper['timestamp']
        upper_date = datetime.utcfromtimestamp(w3_ts_upper).strftime('%Y-%m-%dT%H:%M:%S')
        date_range = BlockRange.date_range(test_db, lower_date, upper_date)
        assert date_range.upper_blk_nbr >= date_range.lower_blk_nbr
        # private network only run one day, this test will fail
        # lower_date = datetime.utcfromtimestamp(w3_ts_lower).strftime('%Y-%m-%d')
        # upper_date = datetime.utcfromtimestamp(w3_ts_upper).strftime('%Y-%m-%d')
        # date_range = BlockRange.date_range(test_db, lower_date, upper_date)
        # assert date_range.upper_blk_nbr >= date_range.lower_blk_nbr
        lower_date = datetime.utcfromtimestamp(w3_ts_lower).strftime('%d/%m/%Y %H:%M:%S')
        upper_date = datetime.utcfromtimestamp(w3_ts_upper).strftime('%d/%m/%Y %H:%M:%S')
        date_range = BlockRange.date_range(test_db, lower_date, upper_date)
        assert date_range.upper_blk_nbr >= date_range.lower_blk_nbr
        # private network only run one day, this test will fail
        # lower_date = datetime.utcfromtimestamp(w3_ts_lower).strftime('%d/%m/%Y')
        # upper_date = datetime.utcfromtimestamp(w3_ts_upper).strftime('%d/%m/%Y')
        # date_range = BlockRange.date_range(test_db, lower_date, upper_date)
        # assert date_range.upper_blk_nbr >= date_range.lower_blk_nbr
