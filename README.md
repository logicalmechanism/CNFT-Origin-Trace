# CNFT-Origin-Trace

A python script to perform an origin trace on a CNFT.

![alt text](nx_html_image.png)

## What is this graph?

This is a directed graph where each node is a unique wallet and each edge is a transaction going between unique wallets. The black edges represent an action on the smart contract and do not represent NFT movement. The number of colors used in the graph is defined by the amount of unique wallets. If two or more nodes have the same color then its the same wallet. The graph starts at the Origin node with the minting transaction and follows the NFT as it moves throughout the blockchain.

### Requirements

- [Python](https://www.python.org/downloads/)
- [Click](https://github.com/pallets/click/)
- [PyVis](https://github.com/WestHealth/pyvis)
- [NetworkX](https://github.com/networkx/networkx)
- [Requests](https://github.com/psf/requests)
- [Matplotlib](https://github.com/matplotlib/matplotlib)

This file requires a mainnet or testnet Blockfrost API key. Please visit [BlockFrost](https://blockfrost.io/) and create a free api key. The api key can be exported into an environment variable called BLOCKFROST_API_KEY or the api key can be placed into a file called blockfrost_api.key inside the CNFT-Origin-Trace folder.

```bash
export BLOCKFROST_API_KEY="Blockfrost API Key Here"
```

```
CNFT-Origin-Trace/
  > origin_trace.py
  > blockfrost_api.key
```

## How to use

The file is designed to be imported and ran from the terminal. Please refer to the [importing section](#importing) or the [command line section](#command-line).

### Importing

If you are importing origin trace then you can use the create html page function like below.

```py
from origin_trace import create_html_page
policy_id              = "8634f3bf5cd864c4b661ff25789ae0154b34084d431c222d242bc39c"
asset_name             = "DEADTRAILLOGIC11"
smart_contract_address = "addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk"
create_html_page(
    policy_id,
    asset_name,
    smart_contract_address,
    print_flag   = False,
    save_flag    = True,
    mainnet_flag = True,
    actions      = "('Withdraw', 'Sold')"
)
```

If print_flag is set to true then it will display the information inside the terminal and attempt to open nx.html in the default internet browser. 

If save_flag is set to true then it will save the graph to the nx.html file and it will save all the addresses and transaction hashes into the cnft_history.json file.

Set mainet_flag to False for testnet origin tracing.

### Command line

This file can also be used directly from the terminal. It will prompt you to enter the policy id and asset name.

```bash
python origin_trace.py

# The policy id of the NFT.: 8634f3bf5cd864c4b661ff25789ae0154b34084d431c222d242bc39c
# The asset name of the NFT.: DEADTRAILLOGIC11
```

Each option can be manually added to the function call.
```
python origin_trace.py \
    --policy_id 8634f3bf5cd864c4b661ff25789ae0154b34084d431c222d242bc39c \
    --asset_name DEADTRAILLOGIC11 \
    --script_address addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk \
    --print_flag False \
    --save_flag True \
    --mainnet_flag True \
    --actions "('Withdraw', 'Sold')"
```

A help menu also exists.

```bash
python origin_trace.py --help

Usage: origin_trace.py [OPTIONS]

  Creates a html file of a direct graph representing the activity of the
  policy_id.asset_name NFT.

Options:
  --policy_id TEXT        Required
  --asset_name TEXT       Required
  --script_address TEXT   Optional
  --print_flag BOOLEAN    Optional  [default: False]
  --save_flag BOOLEAN     Optional  [default: True]
  --mainnet_flag BOOLEAN  Optional  [default: True]
  --actions TEXT          Optional  [default: ('Withdraw', 'Sold')]
  --help                  Show this message and exit.
```

## Testing

Unit tests for ```origin_trace.py``` are located in the test.py file.
