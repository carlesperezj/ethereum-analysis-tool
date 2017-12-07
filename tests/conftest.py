import logging
import os
import random
import shutil
import time
from datetime import datetime

import pytest
import web3

from ethereum_stats import levelDB
from ethereum_stats.process import DevGethProcessWithLogging

NBR_ACCOUNTS = 30
assert NBR_ACCOUNTS > 3
ACCOUNT_PASSPHRASE = 'the-passphrase'
TESTING_NETWORK = 'testing'
CLIENT_NODE_DIR = '/home/ethereum/eth-private/private'
DB_DIR = CLIENT_NODE_DIR + '/' + TESTING_NETWORK + '/geth/chaindata'
RE_USE_DB = True
LOGGING_LEVEL = logging.WARNING

logging.basicConfig(level=LOGGING_LEVEL)


class PrivateNetwork:
    def __init__(self, client_node, db, w3, coinbase, accounts):
        # def __init__(self, client_node, w3, coinbase, accounts):

        self.client_node = client_node
        self.db = db
        self.w3 = w3
        self.coinbase = coinbase
        self.accounts = accounts

        logging.info('Private network created')

    def transfer_funds(self, to_acc, from_acc, value):
        blk_nbr = -1
        if not self.w3.eth.mining:
            self.w3.miner.start(1)
        txn_hash = self.w3.eth.sendTransaction({'to': to_acc, 'from': from_acc, 'value': value})

        logging.info('Waiting for txn to be added to a block')
        not_yet_in_block = True
        while not_yet_in_block:
            txn = self.w3.eth.getTransaction(txn_hash)
            if txn['blockNumber'] is not None:
                not_yet_in_block = False
                blk_nbr = txn['blockNumber']
                logging.info('Transaction added to block\n\ttxn: %s', '\n\tin block: %i', '\n\tfrom account %s',
                             txn_hash, blk_nbr, txn['from'])
                logging.info('Waiting for block to be canonical')
                not_yet_canonical = True
                while not_yet_canonical:
                    blk2 = self.w3.eth.getBlock('latest')
                    if blk2['number'] > blk_nbr + 6:
                        not_yet_canonical = False
                    else:
                        time.sleep(0.5)
            else:
                time.sleep(0.5)

        self.w3.miner.stop()
        return blk_nbr

    def get_account_balance(self, account, block_number=None):
        if block_number is None:
            balance = self.w3.eth.getBalance(account)
        else:
            balance = self.w3.eth.getBalance(account, block_number)
        return balance

    def get_account_nonce(self, account, block_number=None):
        if block_number is None:
            nonce = self.w3.eth.getTransactionCount(account)
        else:
            nonce = self.w3.eth.getTransactionCount(account, block_number)
        return nonce

    def get_block(self, block_number=None):
        if block_number is None:
            block = self.w3.eth.getBlock('latest')
        else:
            block = self.w3.eth.getBlock(block_number)
        return block

    @staticmethod
    def get_db_dir():
        return DB_DIR

    def get_db(self):
        return self.db


@pytest.fixture(scope='session')
def initial_scenario():
    logging.info('Setting private network for testing')

    if not RE_USE_DB:
        logging.info('Delete previous client node directory')
        if os.path.isdir(CLIENT_NODE_DIR):
            shutil.rmtree(CLIENT_NODE_DIR)

    logging.info('Start the client node')
    client_node = DevGethProcessWithLogging(TESTING_NETWORK, CLIENT_NODE_DIR)
    client_node.start()
    logging.info('Waiting for IPC ready')
    while not client_node.is_ipc_ready:
        client_node.wait_for_ipc(timeout=30)
    logging.info('IPC ready')
    w3 = web3.Web3(web3.Web3.IPCProvider(client_node.ipc_path))
    coinbase = w3.eth.coinbase
    logging.info('Client node started')

    if not RE_USE_DB:
        logging.info('Creating accounts')
        accounts = []
        accounts_balances = []
        for n in range(NBR_ACCOUNTS):
            acc_address = w3.personal.newAccount(ACCOUNT_PASSPHRASE)
            w3.personal.unlockAccount(acc_address, passphrase=ACCOUNT_PASSPHRASE, duration=0)
            accounts.append(acc_address)
            logging.info('%i new acc: %s', n, acc_address)
        logging.info('Accounts created')

        logging.info('Initial transferring funds to accounts')
        txn_hashes = []
        for n in range(NBR_ACCOUNTS):
            value = 10 ** 20 + random.randrange(10000, 100000, 1000)
            txn_hashes.append(w3.eth.sendTransaction({'to': accounts[n],
                                                      'from': w3.eth.coinbase,
                                                      'value': value}))
            accounts_balances.append(value)

        logging.info('Waiting for txns to be added to a block')
        for n in range(NBR_ACCOUNTS):
            not_yet_in_block = True
            txn_hash = txn_hashes[n]
            not_yet_in_block = True
            while not_yet_in_block:
                txn = w3.eth.getTransaction(txn_hash)
                blk_nbr = txn['blockNumber']
                if blk_nbr is not None:
                    not_yet_in_block = False
                    logging.info('Transaction added to block\n\ttxn:', '\n\tblock:', txn_hash, blk_nbr)
                else:
                    time.sleep(0.5)
        for n in range(NBR_ACCOUNTS):
            logging.info('Acc %s has an initial balance of %i', accounts[n], w3.eth.getBalance(accounts[n]))
            assert w3.eth.getBalance(accounts[n]) == accounts_balances[n]
        logging.info('Initial funds to accounts transferred')

        logging.info('Random fund transfers')
        for n in range(NBR_ACCOUNTS * 3):
            to_acc = random.choice(accounts)
            from_acc = random.choice(accounts)
            value = random.randrange(1000, 10000)
            while to_acc == from_acc:
                from_acc = random.choice(accounts)
            txn_hash = w3.eth.sendTransaction({'to': to_acc, 'from': from_acc, 'value': value})
            logging.info('Waiting for txn to be added to a block')
            not_yet_in_block = True
            while not_yet_in_block:
                txn = w3.eth.getTransaction(txn_hash)
                if txn['blockNumber'] is not None:
                    not_yet_in_block = False
                    blk_nbr = txn['blockNumber']
                    logging.info('Transaction added to block\n\ttxn: %s', '\n\tblock: %i\n\tfrom %s',
                                 txn_hash, blk_nbr, txn['from'])
                else:
                    time.sleep(0.5)

        logging.info('Waiting transactions to become canonical')
        not_yet_canonical = True
        blk = w3.eth.getBlock('latest')
        blk_nbr = blk['number']
        while not_yet_canonical:
            blk2 = w3.eth.getBlock('latest')
            if blk2['number'] > blk_nbr + 6:
                not_yet_canonical = False
            else:
                print('.', end='', flush=True)
                time.sleep(0.5)
    else:
        accounts = w3.personal.listAccounts
        accounts.remove(coinbase)
        logging.info('List of accounts\n%s\ncoinbase %s', accounts, coinbase)

    logging.info('Stop mining')
    w3.miner.stop()
    db = levelDB.LevelDB(DB_DIR)

    # print the contents of the database
    # for k, v in db.db.RangeIter():
    #     print(k, encode_hex(v))

    private_network = PrivateNetwork(client_node, db, w3, coinbase, accounts)

    logging.info('Private network for testing ready')
    yield private_network

    logging.info('Tear down')
    if client_node.is_running:
        client_node.stop()
    del db
