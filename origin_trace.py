"""
File name   : origin_trace.py
Testing     : test.py
Author      : The Ancient Kraken
Description : A python script to perform an origin trace on a CNFT.
"""
import requests
import base64
import networkx as nx
from pyvis.network import Network
import random
from typing import Tuple
import json
import click
import matplotlib.colors as mcolors
import ast

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

    try:
        response = requests.get(endpoint, headers=headers).json()
    except (requests.exceptions.MissingSchema, json.decoder.JSONDecodeError):
        response = {}
    return response


def all_transactions(asset:str, mainnet_flag:bool=True) -> list:
    """
    Create a list of all the transactions for a given asset.
    """
    
    page = 1
    trx = []
    
    # Query each page until nothing returns.
    while True:
        endpoint = 'assets/{}/transactions?page={}'.format(asset, page)
        if mainnet_flag is True:
            response = get(mainnet + endpoint)
        else:
            response = get(testnet + endpoint)
        
        # Any error should return an empty list.
        try:
            response['error']
            click.echo(click.style('Error: Invalid Inputs', fg='red'))
            return []
        except TypeError:
            pass
        
        # The last page will be empty.
        if response == []:
            break
        
        # Append the hash and increment the page.
        for obj in response:
            trx.append(obj['tx_hash'])
        page += 1
    return trx


def txhash_to_address(trx_hashes:list, asset:str, mainnet_flag:bool=True) -> dict:
    """
    Create a dictionary of transaction hashes and addresses from a list of 
    every transaction of some asset.
    """
    
    # This function requries a list of hashes to work.
    if not isinstance(trx_hashes, list):
        return {}
    asset = str(asset)
    addresses = {}
    
    # Loop each tx hash from all the transactions
    for trx in trx_hashes:
        endpoint = 'txs/{}/utxos'.format(trx)
        if mainnet_flag is True:
            response_utxos = get(mainnet + endpoint)
        else:
            response_utxos = get(testnet + endpoint)
        
        # Loop all the outputs from each UTxO of each transaction.
        for outputs in response_utxos['outputs']:
            
            # Loop the amounts
            for amt in outputs['amount']:
                if amt['unit'] == asset:
                    endpoint2 = 'addresses/{}'.format(outputs['address'])
                    
                    # Check if stake address is available.
                    if mainnet_flag is True:
                        response_address = get(mainnet + endpoint2)['stake_address']
                    else:
                        response_address = get(testnet + endpoint2)['stake_address']
                    
                    # Use the wallet address if a stake address doesn't exist.
                    if response_address is None:
                        response_address = outputs['address']
                    addresses[trx] = response_address
    return addresses


def select_colors(number:int) -> list:
    """
    Select N unique colors that are distingishable.
    """

    # The number must be an int.
    try:
        number = int(number)
    except ValueError:
        return []
    
    # Use the tableau colors for low values of number
    tc = mcolors.TABLEAU_COLORS
    full_color_list = list(tc.values())
    if number <= len(full_color_list):
        colors = full_color_list[:number]
    else:
        # If more than 10 colors are required then just randomly generate the colors and hope for the best.
        colors = ["#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)]) for j in range(number)]
    return colors


def build_graph(addresses:dict, script_address:str,) -> nx.classes.digraph.DiGraph:
    """
    Builds a directed graph from the dictionary of transaction hashes and
    addresses, using the smart contract address to pinpoint a specific
    wallet during the trace.
    """
    
    # A empty graph.
    G = nx.DiGraph()
    
    # This function requires addresses to be a dict.
    if not isinstance(addresses, dict):
        return G
    
    script_address = str(script_address)
    counter = 0
    unique_addresses = list(set(addresses.values()))
    
    # Randomly generate a list of colors
    list_of_colors = select_colors(len(unique_addresses))
    
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


def con_cat(policy_id:str, asset_name:str) -> str:
    """
    Return the concatenation of the policy id and the hex encoded asset name.
    """
    
    policy_id  = str(policy_id)
    asset_name = str(asset_name)
    asset = policy_id + base64.b16encode(bytes(asset_name.encode('utf-8'))).decode('utf-8').lower()
    return asset


def track_asset(policy_id:str, asset_name:str, script_address:str="", mainnet_flag:bool=True) -> Tuple[nx.classes.digraph.DiGraph, dict]:
    """
    Track an asset by its policy and asset name from origin to present wallet.
    Provide a smart contract address to mark a specific wallet.
    """
    
    G = nx.DiGraph()
    asset = con_cat(policy_id, asset_name)
    
    trx_hashes = all_transactions(asset, mainnet_flag)
    if trx_hashes == []:
        return G, {}
    
    addresses = txhash_to_address(trx_hashes, asset, mainnet_flag)
    if addresses == {}:
        return G, {}
    
    G = build_graph(addresses, script_address)
    return G, addresses


def find_node(G:nx.classes.digraph.DiGraph, val:int) -> bool:
    """
    Return True if a vertex exists within G else False.
    """
    
    if not isinstance(G, nx.classes.digraph.DiGraph):
        return False
    
    try:
        val = int(val)
    except ValueError:
        return False
    
    return any([node for node in G.nodes(data=True) if node[0] == val])


def analyze_trajectory(G:nx.classes.digraph.DiGraph, actions:Tuple[str, str]=('Withdraw', 'Sold')) -> nx.classes.digraph.DiGraph:
    """
    Analyze the NFT trajectory for withdraws and sales.
    """
    
    action_1 = actions[0]
    action_2 = actions[1]
    
    # Loop every node.
    for node in G.nodes(data=True):
        (n, data) = node
        
        # Find the Contract label and draw actions.
        if data['label'] == 'Contract' and find_node(G, n+1) is True:
            a = G.nodes(data=True)[n-1]['address']
            b = G.nodes(data=True)[n+1]['address']
            if a == b:
                G.add_edge(n-1, n+1, trxHash=action_1, title=action_1, label=action_1, color="#000000", alpha=0.54)
            else:
                G.add_edge(n-1, n+1, trxHash=action_2, title=action_2, label=action_2, color="#000000", alpha=0.54)
    return G


def print_address_data(addresses:list, script_address: str) -> None:
    """
    Print addresses data to console.
    """
    
    number_of_wallets = len(list(set(addresses.values())))
    click.echo(click.style(f'{number_of_wallets} Unique Wallets', fg='magenta'))

    printed = []
    for txhash in addresses:
        if addresses[txhash] in printed:
            click.echo(click.style(f'Tx Hash: {txhash}', fg='cyan'))
        else:
            if addresses[txhash] == script_address:
                click.echo(click.style(f'\nAddress: {addresses[txhash]}', fg='yellow'))
            else:
                click.echo(click.style(f'\nAddress: {addresses[txhash]}', fg='white'))
            click.echo(click.style(f'Tx Hash: {txhash}', fg='cyan'))
            printed.append(addresses[txhash])


def save_address_data(addresses:dict) -> None:
    """
    JSON dump the address dictionary into a file.
    """
    
    # If adddress is a dict then attempt to dump to file.
    if isinstance(addresses, dict):
        with open('cnft_history.json', 'w+') as outfile:
            json.dump(addresses, outfile, indent=2)


@click.command()
@click.option('--policy_id',      prompt='The policy id of the NFT.',                                   help='Required')
@click.option('--asset_name',     prompt='The asset name of the NFT.',                                  help='Required')
@click.option('--script_address', default="addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk", help='Optional')
@click.option('--print_flag',     default=False,                                                        help='Optional', show_default=True)
@click.option('--save_flag',      default=True,                                                         help='Optional', show_default=True)
@click.option('--mainnet_flag',   default=True,                                                         help='Optional', show_default=True)
@click.option('--actions',        default="('Withdraw', 'Sold')",                                       help='Optional', show_default=True)
def create_html_page(policy_id:str, asset_name:str, script_address:str="addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk", print_flag:bool=False, save_flag:bool=True, mainnet_flag:bool=True, actions:Tuple[str, str]=('Withdraw', 'Sold')) -> None:
    """
    Use track asset to provide information to create a html file of the direct graph. By 
    default the function prints the address data to the console.
    """
    
    # Track asset
    click.echo(click.style('\nTracking Asset', fg='blue'))
    actions = ast.literal_eval(actions)
    G, addresses = track_asset(policy_id, asset_name, script_address, mainnet_flag)
    G = analyze_trajectory(G, actions)
    
    # Create html page
    click.echo(click.style('Creating HTML page', fg='blue'))
    nt = Network('100%', '100%', heading=policy_id+'.'+asset_name, directed=True)
    nt.from_nx(G)
    
    # Flag Checking
    if print_flag is True:
        click.echo(click.style('Opening HTML page', fg='yellow'))
        print_address_data(addresses, script_address)
        nt.show('nx.html')
    elif save_flag is True:
        click.echo(click.style('Saving html page.', fg='yellow'))
        save_address_data(addresses)
        nt.save_graph('nx.html')
    else:
        click.echo(click.style('Error: No Flag Is Set.', fg='red'))
    # Complete
    click.echo(click.style('\nComplete!\n', fg='green'))


if __name__ == '__main__':
    create_html_page()