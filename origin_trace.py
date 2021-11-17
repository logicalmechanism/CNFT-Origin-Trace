import requests
import base64
import networkx as nx
from pyvis.network import Network
import random
from typing import Tuple

###############################################################################
# Requires Blockfrost API Key.
with open("blockfrost_api.key", "r") as read_content: API_KEY = read_content.read().splitlines()[0]
# Store the blockfrost api key inside blockfrost_api.key.
headers = {'Project_id': API_KEY}
###############################################################################

def get(endpoint: str) -> dict:
    """
    Return the json reponse from an endpoint.
    """
    response = requests.get(endpoint, headers=headers).json()
    return response


def all_transactions(asset: str) -> list:
    """
    Create a list of all the transactions for a given asset.
    """
    page = 1
    trx = []
    # Query each page until nothing returns.
    while True:
        response = get('https://cardano-mainnet.blockfrost.io/api/v0/assets/{}/transactions?page={}'.format(asset, page))
        if response == []:
            break
        for obj in response:
            tx_hash = obj['tx_hash']
            trx.append(tx_hash)
        page += 1
    return trx


def txhash_to_address(trx_hashes: list, asset:str) -> dict:
    """
    Create a dictionary of transaction hashes and addresses from a list of 
    every transaction of some asset.
    """
    addresses = {}
    # Loop each tx hash from all the transactions
    for trx in trx_hashes:
        response_utxos = get('https://cardano-mainnet.blockfrost.io/api/v0/txs/{}/utxos'.format(trx))
        # Loop all the outputs from each UTxO of each transaction.
        for outputs in response_utxos['outputs']:
            # Loop the amounts
            for amt in outputs['amount']:
                if amt['unit'] == asset:
                    # Check if stake address is available.
                    response_address = get('https://cardano-mainnet.blockfrost.io/api/v0/addresses/{}'.format(outputs['address']))['stake_address']
                    if response_address is None:
                        response_address = outputs['address']
                    addresses[trx] = response_address
    return addresses


def build_graph(addresses: dict, smart_contract_address: str) -> nx.classes.digraph.DiGraph:
    """
    Builds a directed graph from the dictionary of transaction hashes and
    addresses, using the smart contract address to pinpoint a specific
    wallet during the trace.
    """
    G = nx.DiGraph()
    counter = 0
    unique_addresses = list(set(addresses.values()))
    # Randomly generate a list of colors with size len(unique addresses).
    list_of_colors = ["#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)]) for j in range(len(unique_addresses))]
    # Loop all the transaction hashes from the addresses.
    for tx_hash in addresses:
        nodes = [x for x,y in G.nodes(data=True) if y['address'] == addresses[tx_hash]] # Correct node count.
        index = unique_addresses.index(addresses[tx_hash])
        selected_color = list_of_colors[index]
        # Check if the next wallet is new and there are wallets to go map.
        if len(nodes) > 0 and counter-1 in nodes:
            continue
        # Start the graph at the Origin
        if counter == 0:
            G.add_node(counter, address=addresses[tx_hash], label='Origin', title=addresses[tx_hash], color=selected_color)
        if counter > 0:
            if addresses[tx_hash] != smart_contract_address:
                G.add_node(counter, address=addresses[tx_hash], label=str(counter), title=addresses[tx_hash], color=selected_color)
            else:
                # A specific address to uniquely label.
                G.add_node(counter, address=addresses[tx_hash], label='Contract', title=addresses[tx_hash], color=selected_color)
            # Add edge only if there exists one.
            G.add_edge(counter-1, counter, trxHash=tx_hash, title=tx_hash)
        counter += 1
    return G


def track_asset(policy_id: str, asset_name:str, smart_contract_address:str="") -> Tuple[nx.classes.digraph.DiGraph, dict]:
    """
    Track an asset by its policy and asset name from origin to present wallet.
    Provide a smart contract address to mark a specific wallet.
    """
    asset = policy_id + base64.b16encode(bytes(asset_name.encode('utf-8'))).decode('utf-8').lower()
    trx_hashes = all_transactions(asset)
    addresses = txhash_to_address(trx_hashes, asset)
    G = build_graph(addresses, smart_contract_address)
    return G, addresses


def print_address_data(addresses: list):
    """
    Print addresses data to console.
    """
    print(len(list(set(addresses.values()))), 'Unique Wallet')
    printed = []
    for txhash in addresses:
        if addresses[txhash] in printed:
            print('Tx Hash:', txhash)
        else:
            print('\nAddress:', addresses[txhash])
            print('Tx Hash:', txhash)
            printed.append(addresses[txhash])


def create_html_page(policy_id: str, asset_name:str, smart_contract_address:str="", print_flag:bool=True):
    """
    Use track asset to provide information to create a html file of the direct graph. By 
    default the function prints the address data to the console.
    """
    G, addresses = track_asset(policy_id, asset_name, smart_contract_address)
    if print_flag is True:
        print_address_data(addresses)
    nt = Network('100%', '100%', heading=policy_id+'.'+asset_name, directed=True)
    nt.from_nx(G)
    nt.show('nx.html')


if __name__ == "__main__":
    policy_id = "8634f3bf5cd864c4b661ff25789ae0154b34084d431c222d242bc39c"
    asset_name = "DEADTRAILLOGIC11"
    smart_contract_address = "addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk"
    create_html_page(policy_id, asset_name, smart_contract_address)
