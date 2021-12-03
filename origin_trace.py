"""
    File name: origin_trace.py
    Author: The Ancient Kraken
"""
import requests
import base64
import networkx as nx
from pyvis.network import Network
import random
from typing import Tuple
import sys
import json
import click

###############################################################################
# Requires Blockfrost API Key.
with open("blockfrost_api.key", "r") as read_content: API_KEY = read_content.read().splitlines()[0]
headers    = { 'Project_id': API_KEY}
mainnet    = "https://cardano-mainnet.blockfrost.io/api/v0/"
testnet    = "https://cardano-testnet.blockfrost.io/api/v0/"
###############################################################################


def get(endpoint:str) -> dict:
    """
    Return the json reponse from an endpoint.
    """
    response = requests.get(endpoint, headers=headers).json()
    return response


def all_transactions(asset:str, mainnet_flag:bool=True) -> list:
    """
    Create a list of all the transactions for a given asset.
    """
    page = 1
    trx = []
    # Query each page until nothing returns.
    while True:
        if mainnet_flag is True:
            response = get(mainnet + 'assets/{}/transactions?page={}'.format(asset, page))
        else:
            response = get(testnet + 'assets/{}/transactions?page={}'.format(asset, page))
        try:
            response['error']
            click.echo(click.style('Error: Check The Input Options.', fg='red'))
            sys.exit()
        except TypeError:
            pass
        if response == []:
            break
        for obj in response:
            tx_hash = obj['tx_hash']
            trx.append(tx_hash)
        page += 1
    return trx


def txhash_to_address(trx_hashes:list, asset:str, mainnet_flag:bool=True) -> dict:
    """
    Create a dictionary of transaction hashes and addresses from a list of 
    every transaction of some asset.
    """
    addresses = {}
    # Loop each tx hash from all the transactions
    for trx in trx_hashes:
        if mainnet_flag is True:
            response_utxos = get(mainnet + 'txs/{}/utxos'.format(trx))
        else:
            response_utxos = get(testnet + 'txs/{}/utxos'.format(trx))
        # Loop all the outputs from each UTxO of each transaction.
        for outputs in response_utxos['outputs']:
            # Loop the amounts
            for amt in outputs['amount']:
                if amt['unit'] == asset:
                    # Check if stake address is available.
                    if mainnet_flag is True:
                        response_address = get(mainnet + 'addresses/{}'.format(outputs['address']))['stake_address']
                    else:
                        response_address = get(testnet + 'addresses/{}'.format(outputs['address']))['stake_address']
                    if response_address is None:
                        response_address = outputs['address']
                    addresses[trx] = response_address
    return addresses


def build_graph(addresses:dict, script_address:str,) -> nx.classes.digraph.DiGraph:
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
        # Other nodes
        if counter > 0:
            if addresses[tx_hash] != script_address:
                G.add_node(counter, address=addresses[tx_hash], label=str(counter), title=addresses[tx_hash], color=selected_color)
                if G.nodes[counter-1]['label'] == 'Contract':
                    G.add_node(counter, label='Wallet')
            else:
                # A specific address to uniquely label.
                G.add_node(counter-1, label='Wallet')
                G.add_node(counter, address=addresses[tx_hash], label='Contract', title=addresses[tx_hash], color=selected_color)
            # Add edge only if there exists one.
            G.add_edge(counter-1, counter, trxHash=tx_hash, title=tx_hash)
        counter += 1
    return G


def track_asset(policy_id:str, asset_name:str, script_address:str="", mainnet_flag:bool=True) -> Tuple[nx.classes.digraph.DiGraph, dict]:
    """
    Track an asset by its policy and asset name from origin to present wallet.
    Provide a smart contract address to mark a specific wallet.
    """
    asset = policy_id + base64.b16encode(bytes(asset_name.encode('utf-8'))).decode('utf-8').lower()
    trx_hashes = all_transactions(asset, mainnet_flag)
    addresses = txhash_to_address(trx_hashes, asset, mainnet_flag)
    G = build_graph(addresses, script_address)
    return G, addresses


def find_node(G:nx.classes.digraph.DiGraph, val:int) -> bool:
    """
    Return True if a vertex exists within G else False.
    """
    return any([node for node in G.nodes(data=True) if node[0] == val])


def analyze_trajectory(G:nx.classes.digraph.DiGraph) -> nx.classes.digraph.DiGraph:
    """
    Analyze the NFT trajectory for withdraws and sales.
    """
    for node in G.nodes(data=True):
        (n, data) = node
        if data['label'] == 'Contract' and find_node(G, n+1) is True:
            a = G.nodes(data=True)[n-1]['address']
            b = G.nodes(data=True)[n+1]['address']
            if a == b:
                G.add_edge(n-1, n+1, trxHash="Withdraw", title="Withdraw", label="Withdraw", color="#000000", alpha=0.54)
            else:
                G.add_edge(n-1, n+1, trxHash="Sold", title="Sold", label="Sold", color="#000000", alpha=0.54)
    return G


def print_address_data(addresses:list) -> None:
    """
    Print addresses data to console.
    """
    number_of_wallets = len(list(set(addresses.values())))
    click.echo(click.style(f'{number_of_wallets} Unique Wallet', fg='magenta'))

    printed = []
    for txhash in addresses:
        if addresses[txhash] in printed:
            click.echo(click.style(f'Tx Hash: {txhash}', fg='cyan'))
        else:
            click.echo(click.style(f'\nAddress: {addresses[txhash]}', fg='white'))
            click.echo(click.style(f'Tx Hash: {txhash}', fg='cyan'))
            printed.append(addresses[txhash])


def save_address_data(addresses:dict) -> None:
    """
    JSON dump the address dictionary into a file.
    """
    with open('cnft_history.json', 'w+') as outfile:
        json.dump(addresses, outfile, indent=2)


@click.command()
@click.option('--policy_id',      prompt='The policy id of the NFT.',                                   help='Required')
@click.option('--asset_name',     prompt='The asset name of the NFT.',                                  help='Required')
@click.option('--script_address', default="addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk", help='Optional')
@click.option('--print_flag',     default=False,                                                        help='Optional')
@click.option('--save_flag',      default=True,                                                         help='Optional')
@click.option('--mainnet_flag',   default=True,                                                         help='Optional')
def create_html_page(policy_id:str, asset_name:str, script_address:str="addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk", print_flag:bool=False, save_flag:bool=True, mainnet_flag:bool=True) -> None:
    """
    Use track asset to provide information to create a html file of the direct graph. By 
    default the function prints the address data to the console.
    """
    click.echo(click.style('\nTracking Asset', fg='blue'))

    G, addresses = track_asset(policy_id, asset_name, script_address, mainnet_flag)
    G = analyze_trajectory(G)
    click.echo(click.style('Creating HTML page', fg='blue'))
    nt = Network('100%', '100%', heading=policy_id+'.'+asset_name, directed=True)
    nt.from_nx(G)
    if print_flag is True:
        click.echo(click.style('Opening HTML page', fg='yellow'))
        print_address_data(addresses)
        nt.show('nx.html')
    elif save_flag is True:
        click.echo(click.style('Saving html page.', fg='yellow'))
        save_address_data(addresses)
        nt.save_graph('nx.html')
    else:
        click.echo(click.style('Error: No flag is set.', fg='red'))
        sys.exit()
    click.echo(click.style('\nComplete!\n', fg='green'))


if __name__ == '__main__':
    create_html_page()
