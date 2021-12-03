import unittest
import origin_trace as trace

"""
get(endpoint:str) -> dict
"""
class TestGetMethod(unittest.TestCase):

    def test_no_url(self):
        self.assertEqual(trace.get(''), {})
    
    def test_wrong_url(self):
        self.assertEqual(trace.get('https://www.logicalmechanism.io/'), {})
    
    def test_correct_url(self):
        self.assertEqual(trace.get('https://cardano-mainnet.blockfrost.io/api/v0/')['url'], 'https://blockfrost.io/')
    
    def test_number_url(self):
        self.assertEqual(trace.get(1), {})

"""
con_cat(policy_id:str, asset_name:str) -> str
"""
class TestConcatMethod(unittest.TestCase):

    def test_no_strings(self):
        self.assertEqual(trace.con_cat('', ''), '')
    
    def test_simple_string(self):
        self.assertEqual(trace.con_cat('', 'myassetname'), '6d7961737365746e616d65')
    
    def test_numbers(self):
        self.assertEqual(trace.con_cat(1,2), '132')
    
    def test_numbers(self):
        self.assertEqual(trace.con_cat('hello',''), 'hello')

"""
all_transactions(asset:str, mainnet_flag:bool=True) -> list
"""
class TestAllTransactionsMethod(unittest.TestCase):

    def test_no_asset(self):
        self.assertEqual(trace.all_transactions(''), [])
    
    def test_no_asset(self):
        self.assertEqual(trace.all_transactions(123), [])
    
    def test_good_asset(self):
        asset = trace.con_cat('eb25239ff383cba6f76699f88c6d4441179cf9bfea27b214ee461fd6','HappyFaceTunnel')
        outcome = ['567fa04abe944eb6b0b418681e0ced5f4b0be1be264dd8065018a3f0967f8e68','815f7621e14060df0be24e090ddb9738bca9542377a9bad265c3f73348228f6e']
        self.assertEqual(trace.all_transactions(asset), outcome)
    
    def test_good_asset_bad_flag(self):
        asset = trace.con_cat('eb25239ff383cba6f76699f88c6d4441179cf9bfea27b214ee461fd6','HappyFaceTunnel')
        self.assertEqual(trace.all_transactions(asset, False), [])

"""
txhash_to_address(trx_hashes:list, asset:str, mainnet_flag:bool=True) -> dict
"""
class TestTxHashToAddressMethod(unittest.TestCase):
    
    def test_no_asset(self):
        self.assertEqual(trace.txhash_to_address([], ''), {})
    
    def test_no_asset(self):
        self.assertEqual(trace.txhash_to_address([], 123), {})
        self.assertEqual(trace.txhash_to_address(123, ''), {})
    
    def test_correct_inputs(self):
        asset = trace.con_cat('eb25239ff383cba6f76699f88c6d4441179cf9bfea27b214ee461fd6','HappyFaceTunnel')
        tx_hashes = ['567fa04abe944eb6b0b418681e0ced5f4b0be1be264dd8065018a3f0967f8e68','815f7621e14060df0be24e090ddb9738bca9542377a9bad265c3f73348228f6e']
        outcome =  {'567fa04abe944eb6b0b418681e0ced5f4b0be1be264dd8065018a3f0967f8e68': 'addr1vy356vnymrzy27kkh4se0znrpr4jgqmay2n0xutglcnfnac85efw4','815f7621e14060df0be24e090ddb9738bca9542377a9bad265c3f73348228f6e': 'addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk'}
        self.assertEqual(trace.txhash_to_address(tx_hashes, asset), outcome)

"""
build_graph(addresses:dict, script_address:str,) -> nx.classes.digraph.DiGraph
"""
class TestBuildGraphMethod(unittest.TestCase):
    
    def test_no_addresses(self):
        # return empty graph
        self.assertEqual(trace.build_graph({}, '').number_of_nodes(), 0)
    
    def test_wrong_addresses_type(self):
        # return empty graph
        self.assertEqual(trace.build_graph([], '').number_of_nodes(), 0)
    
    def test_no_contract(self):
        outcome =  {'567fa04abe944eb6b0b418681e0ced5f4b0be1be264dd8065018a3f0967f8e68': 'addr1vy356vnymrzy27kkh4se0znrpr4jgqmay2n0xutglcnfnac85efw4','815f7621e14060df0be24e090ddb9738bca9542377a9bad265c3f73348228f6e': 'addr1wyl5fauf4m4thqze74kvxk8efcj4n7qjx005v33ympj7uwsscprfk'}
        self.assertEqual(trace.build_graph(outcome, '').number_of_nodes(), 2)

"""
find_node(G:nx.classes.digraph.DiGraph, val:int) -> bool
"""
class TestFindNodeMethod(unittest.TestCase):

    def test_no_graph_input(self):
        # return empty graph
        self.assertEqual(trace.find_node({}, 'a'), False)
    
    def test_bad_val_input(self):
        # return empty graph
        G = trace.build_graph({}, '')
        self.assertEqual(trace.find_node(G, 'a'), False)
    
    def test_correct_inputs(self):
        # return empty graph
        G = trace.build_graph({}, '')
        G.add_node(0)
        self.assertEqual(trace.find_node(G, 0), True)
    
    def test_correct_inputs_wrong_nodee(self):
        # return empty graph
        G = trace.build_graph({}, '')
        G.add_node(0)
        self.assertEqual(trace.find_node(G, 1), False)


"""
track_asset(policy_id:str, asset_name:str, script_address:str="", mainnet_flag:bool=True) -> Tuple[nx.classes.digraph.DiGraph, dict]
"""
class TestTrackAssetMethod(unittest.TestCase):
    
    def test_no_graph_input(self):
        # return empty graph
        G = trace.build_graph({}, '')
        self.assertEqual(trace.track_asset('','')[0].number_of_nodes(), 0)
        self.assertEqual(trace.track_asset('','')[1], {})
    
    def test_correct_inputs(self):
        policy_id, asset_name = ('eb25239ff383cba6f76699f88c6d4441179cf9bfea27b214ee461fd6','HappyFaceTunnel')

        self.assertEqual(trace.track_asset(policy_id, asset_name)[0].number_of_nodes(), 2)


"""
select_colors(number:int) -> list
"""
class TestSelectColorsMethod(unittest.TestCase):

    def test_bad_inputs(self):
        self.assertEqual(trace.select_colors('test'), [])
    
    def test_good_inputs(self):
        self.assertEqual(trace.select_colors(2), ['#1f77b4', '#ff7f0e'])
    
    def test_large_inputs(self):
        self.assertEqual(len(trace.select_colors(25)), 25)


if __name__ == '__main__':
    unittest.main()