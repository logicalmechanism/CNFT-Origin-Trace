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
from sys import exit
import os


###############################################################################
#
# Requires Blockfrost API Key.
#
# Check env var then file.
try:
    API_KEY = os.environ['BLOCKFROST_API_KEY']
    headers = { 'Project_id': API_KEY}
    click.echo(click.style('\nThe Blockfrost api key is in the environment variables.', fg='green'))
except KeyError:
    click.echo(click.style('\nThe script did not find the Blockfrost api key in environment variables.', fg='yellow'))
    # Check if the key is inside the blockfrost_api.key file.
    try:
        with open("blockfrost_api.key", "r") as read_content: API_KEY = read_content.read().splitlines()[0]
        headers = { 'Project_id': API_KEY}
        click.echo(click.style('\nThe Blockfrost api key is in the blockfrost_api.key file.', fg='green'))
    except FileNotFoundError:
        click.echo(click.style('\nThe script did not find a blockfrost_api.key file to be inside the base directory.', fg='red'))
        exit(1)
    except IndexError:
        click.echo(click.style('\nThe script expects the api key to be placed inside the blockfrost_api.key file.', fg='red'))
        exit(1)
    
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
            click.echo(click.style(f'Error: {response["message"]}', fg='red'))
            return []
        except TypeError:
            pass
        
        # The last page will be an empty list.
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


def random_colors(amount:int) -> list:
    """
    Create an amount of random colors inside a list.
    """
    return ["#"+''.join([random.choice('ABCDEF0123456789') for i in range(6)]) for j in range(amount)]


def select_colors(number:int) -> list:
    """
    Select N unique colors that are distingishable else reeturn an empty list.
    """

    # The number must be an int.
    try:
        number = int(number)
    except ValueError:
        return []
    
    # Use the tableau colors for less than 11 colors.
    tc = mcolors.TABLEAU_COLORS
    full_color_list = list(tc.values())
    if number <= len(full_color_list):
        colors = full_color_list[:number]
    else:
        # If more than 10 colors are required then just randomly generate the colors and hope for the best.
        additional = number-len(full_color_list)
        colors = full_color_list + random_colors(additional)
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


def ascii_to_hex(string:str) -> str:
    """
    Convert an ascii string into hex
    """
    return base64.b16encode(bytes(string.encode('utf-8'))).decode('utf-8').lower()


def con_cat(policy_id:str, asset_name:str) -> str:
    """
    Return the concatenation of the policy id and the hex encoded asset name.
    """
    
    policy_id  = str(policy_id)
    asset_name = str(asset_name)
    asset = policy_id + ascii_to_hex(asset_name)
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
    Analyze the NFT trajectory.

    This currently applies a binary action to the smart contract. It defaults to Withdraws and Sold.
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
                G.add_edge(n-1, n+1, trxHash=action_1, title=action_1, label=action_1, color="#000000", alpha=0.4)
            else:
                G.add_edge(n-1, n+1, trxHash=action_2, title=action_2, label=action_2, color="#000000", alpha=0.4)
    return G


def print_address_data(addresses:list, script_address: str) -> None:
    """
    Print addresses data to console.
    """
    
    number_of_wallets = len(list(set(addresses.values())))
    click.echo(click.style(f'\n{number_of_wallets} Unique Wallets', fg='magenta'))

    # Print only new data to the console.
    printed = []
    for txhash in addresses:
        if addresses[txhash] in printed:
            click.echo(click.style(f'Tx Hash: {txhash}', fg='bright_magenta'))
        else:
            if addresses[txhash] == script_address:
                click.echo(click.style(f'\nScript: {addresses[txhash]}', fg='bright_yellow'))
            else:
                click.echo(click.style(f'\nAddress: {addresses[txhash]}', fg='bright_white'))
            click.echo(click.style(f'Tx Hash: {txhash}', fg='bright_magenta'))
            printed.append(addresses[txhash])


def save_address_data(addresses:dict) -> None:
    """
    JSON dump the address dictionary into a file.
    """
    
    # If adddress is a dict then attempt to dump to file.
    if isinstance(addresses, dict):
        with open('cnft_history.json', 'w+') as outfile:
            json.dump(addresses, outfile, indent=2)


###############################################################################


@click.command()
@click.option('--policy_id',      prompt='\nThe policy id of the NFT.',                                 help='Required')
@click.option('--asset_name',     prompt='The asset name of the NFT.',                                  help='Required')
@click.option('--script_address', default="addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk", help='Optional')
@click.option('--print_flag',     default=False,                                                        help='Optional', show_default=True)
@click.option('--save_flag',      default=True,                                                         help='Optional', show_default=True)
@click.option('--mainnet_flag',   default=True,                                                         help='Optional', show_default=True)
@click.option('--actions',        default="('Withdraw', 'Sold')",                                       help='Optional', show_default=True)
def create_html_page(policy_id:str, asset_name:str, script_address:str="", print_flag:bool=False, save_flag:bool=True, mainnet_flag:bool=True, actions:Tuple[str, str]=('Withdraw', 'Sold')) -> None:
    """
    Creates a html file of a direct graph representing the activity of the policy_id.asset_name NFT.
    """
    if print_flag is False and save_flag is False:
        click.echo(click.style('Error: The Print And Save Flags Are False.', fg='red'))
        exit(1)
    # Track asset
    click.echo(click.style('\nTracking Asset..', fg='blue'))
    actions = ast.literal_eval(actions)
    G, addresses = track_asset(policy_id, asset_name, script_address, mainnet_flag)
    if addresses == {}:
        exit(1)
    G = analyze_trajectory(G, actions)
    
    # Create html page
    click.echo(click.style('Creating HTML Page..', fg='blue'))
    nt = Network('100%', '100%', heading=policy_id+'.'+asset_name, directed=True)
    nt.from_nx(G)
    
    # Flag Checking
    if print_flag is True:
        print_address_data(addresses, script_address)
        click.echo(click.style('Opening HTML Page..', fg='cyan'))
        nt.show('nx.html')
    
    if save_flag is True:
        save_address_data(addresses)
        click.echo(click.style('Saving HTML Page..', fg='cyan'))
        nt.save_graph('nx.html')
    
    # Complete
    click.echo(click.style('\nComplete!\n', fg='green'))


if __name__ == '__main__':
    create_html_page()