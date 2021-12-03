# CNFT-Origin-Trace

A python script to perform an origin trace on a cnft.

![alt text](nx_html_image.png)

## What is this graph?

This is a directed graph where each node is a unique wallet and each colored edge is a transaction going between unique wallets. The darker edges represent either a withdraw and sell action and do not represent NFT movement. Each color used in the graph is defined by the amount of unique wallets. If two or more nodes have colors that are equal then its the same wallet.

### Requirements

- [Python](https://www.python.org/downloads/)
- [Click](https://github.com/pallets/click/)
- [PyVis](https://github.com/WestHealth/pyvis)
- [NetworkX](https://github.com/networkx/networkx)

This file requires a mainnet or testnet [BlockFrost](https://blockfrost.io/) api key. Place the api key into a file called blockfrost_api.key inside the CNFT-Origin-Trace folder.

Use the requirements.txt file to install the python requirements with the pip command below.

```bash
pip install -r requirements.txt
```

## How to use

The file is designed to be imported and ran from the terminal. 

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
    mainnet_flag = True
)
```

If print is set to true, it will display the information inside the terminal and attempt to open nx.html in the default internet browser. 

If save is set to true then it will just save the nx.html file to the local folder and it will save all the addresses and transactions into a json file, cnft_history.json.

Set mainet_flag to False for testnet tracing.

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
    --mainnet_flag True
```

A help menu also exists.

```
python origin_trace.py --help

Usage: origin_trace.py [OPTIONS]

  Use track asset to provide information to create a html file of the direct
  graph. By  default the function prints the address data to the console.

Options:
  --policy_id TEXT        Required
  --asset_name TEXT       Required
  --script_address TEXT   Optional
  --print_flag BOOLEAN    Optional
  --save_flag BOOLEAN     Optional
  --mainnet_flag BOOLEAN  Optional
  --help                  Show this message and exit.
```
