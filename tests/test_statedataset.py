import logging
import random

from eth_utils import decode_hex

from ethereum_stats.statedataset import StateDataset

NBR_RANDOM_TESTS = 5


def test_account_balance_on_nth_block(initial_scenario):
    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_block_with_txn = False
        while not is_block_with_txn:
            n_blk = initial_scenario.get_block(random.randrange(1, latest_block_nbr))
            if len(n_blk['transactions']) > 0:
                is_block_with_txn = True
        n_blk_nbr = n_blk['number']
        to_account = random.choice(initial_scenario.accounts)
        to_account_balance = initial_scenario.get_account_balance(to_account, n_blk_nbr)
        logging.info('w3 balance %i acc: %s on blk: %i', to_account_balance, to_account, n_blk_nbr)
        db = initial_scenario.get_db()
        state = StateDataset(db, decode_hex(n_blk.stateRoot))
        state_dict = state.to_dict()
        assert to_account_balance == state_dict[to_account][1]


def test_account_balance_on_latest(initial_scenario):
    for n in range(NBR_RANDOM_TESTS):
        to_account = random.choice(initial_scenario.accounts)
        to_account_balance = initial_scenario.get_account_balance(to_account)
        logging.info('w3 balance %i on acc: %s on latest blk', to_account_balance, to_account)
        block = initial_scenario.get_block()
        db = initial_scenario.get_db()
        state = StateDataset(db, block.stateRoot)
        state_dict = state.to_dict()
        assert to_account_balance == state_dict[to_account][1]


def test_account_nonce_on_nth_block(initial_scenario):
    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_block_with_txn = False
        while not is_block_with_txn:
            n_blk = initial_scenario.get_block(random.randrange(1, latest_block_nbr))
            if len(n_blk['transactions']) > 0:
                is_block_with_txn = True
        n_blk_nbr = n_blk['number']
        to_account = random.choice(initial_scenario.accounts)
        to_account_nonce = initial_scenario.get_account_nonce(to_account, n_blk_nbr)
        logging.info('w3 nonce %i on acc: %s on blk: %i', to_account_nonce, to_account, n_blk_nbr)
        db = initial_scenario.get_db()
        state = StateDataset(db, decode_hex(n_blk.stateRoot))
        state_dict = state.to_dict()
        assert to_account_nonce == state_dict[to_account][0]


def test_account_nonce_on_latest(initial_scenario):
    block = initial_scenario.get_block()
    db = initial_scenario.get_db()
    state = StateDataset(db, decode_hex(block.stateRoot))
    state_dict = state.to_dict()
    for n in range(NBR_RANDOM_TESTS):
        to_account = random.choice(initial_scenario.accounts)
        to_account_nonce = initial_scenario.get_account_nonce(to_account)
        logging.info('w3 nonce %i  on acc: %s on latest blk', to_account_nonce, to_account)

        assert to_account_nonce == state_dict[to_account][0]


def test_get_account(initial_scenario):
    latest_block = initial_scenario.get_block()
    latest_block_nbr = latest_block['number']
    for n in range(NBR_RANDOM_TESTS):
        is_block_with_txn = False
        while not is_block_with_txn:
            n_blk = initial_scenario.get_block(random.randrange(1, latest_block_nbr))
            if len(n_blk['transactions']) > 0:
                is_block_with_txn = True
        n_blk_nbr = n_blk['number']
        to_account = random.choice(initial_scenario.accounts)
        to_account_nonce = initial_scenario.get_account_nonce(to_account, n_blk_nbr)
        logging.info('w3 nonce %i on acc: %s  on blk: %i', to_account_nonce, to_account, n_blk_nbr)
        db = initial_scenario.get_db()
        state = StateDataset(db, decode_hex(n_blk.stateRoot))
        account = state.get_account(to_account)
        assert to_account_nonce == account.nonce


def test_to_panda_dataset(initial_scenario):
    latest_block = initial_scenario.get_block()
    db = initial_scenario.get_db()
    state = StateDataset(db, decode_hex(latest_block.stateRoot))
    df = state.to_panda_dataframe()
    logging.info('Panda dataset\n%s', df.describe())


def test_account_contract_size_on_latest(initial_scenario):
    block = initial_scenario.get_block()
    db = initial_scenario.get_db()
    state = StateDataset(db, decode_hex(block.stateRoot))
    contract_address = initial_scenario.contract_address
    contract_size = initial_scenario.get_account_code_size(contract_address)
    logging.info('w3 code size %i  on acc: %s on latest blk', contract_address, contract_size)
    contract = state.get_account(contract_address)
    assert contract_size == contract.contract_code_size
