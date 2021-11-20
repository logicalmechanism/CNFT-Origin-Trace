# CNFT-Origin-Trace

A python script to perform an origin trace on a cnft.

## How to use

To create an html page use the create_html_page function.

```py
create_html_page(policy_id: str, asset_name:str, smart_contract_address:str="", print_flag:bool=True)
```

This will produce and attempt to open a file called nx.html in the local directory.

### Example

Directly from the terminal:

```bash
python origin_trace.py 8634f3bf5cd864c4b661ff25789ae0154b34084d431c222d242bc39c DEADTRAILLOGIC11
```

### What this graphs shows

This returns a directed graph where each node is a unique wallet and each edge is a transaction going between unique wallets. Each color is defined by the amount of unique wallets so if the colors are equal then its the same wallet.

