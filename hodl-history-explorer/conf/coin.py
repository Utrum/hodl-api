from bitcoin.core import CoreMainParams
class CoinParams(CoreMainParams):
    MESSAGE_START = b'\x24\xe9\x27\x64'
    DEFAULT_PORT = 7770
    RPC_PORT = 7771
    CONF_FILE = "/Users/patrickhennis/Desktop/utrum/hodl-api/hodl-history-explorer/conf/OOT.conf"
    EXPLORER = "https://explorer.utrum.io"
    DNS_SEEDS = (('seeds.komodoplatform.com', 'static.kolo.supernet.org'))
    BASE58_PREFIXES = {'PUBKEY_ADDR': 60,
                       'SCRIPT_ADDR': 85,
                       'SECRET_KEY': 188}
