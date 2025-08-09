from web3 import Web3
from web3.exceptions import TransactionNotFound
from solcx import compile_source, install_solc, set_solc_version
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import init, Fore, Style
from dotenv import load_dotenv
import asyncio, random, json, re, os

init(autoreset=True)
load_dotenv()

class Colors:
    RESET = Style.RESET_ALL
    BOLD = Style.BRIGHT
    GREEN = Fore.GREEN
    YELLOW = Fore.YELLOW
    RED = Fore.RED
    CYAN = Fore.CYAN
    MAGENTA = Fore.MAGENTA
    WHITE = Fore.WHITE
    BRIGHT_GREEN = Fore.LIGHTGREEN_EX
    BRIGHT_MAGENTA = Fore.LIGHTMAGENTA_EX
    BRIGHT_WHITE = Fore.LIGHTWHITE_EX
    BRIGHT_BLACK = Fore.LIGHTBLACK_EX

class Logger:
    @staticmethod
    def log(label, symbol, msg, color):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"{Colors.BRIGHT_BLACK}[{timestamp}]{Colors.RESET} {color}[{symbol}] {msg}{Colors.RESET}")

    @staticmethod
    def info(msg): Logger.log("INFO", "✓", msg, Colors.GREEN)
    @staticmethod
    def warn(msg): Logger.log("WARN", "!", msg, Colors.YELLOW)
    @staticmethod
    def error(msg): Logger.log("ERR", "✗", msg, Colors.RED)
    @staticmethod
    def success(msg): Logger.log("OK", "+", msg, Colors.GREEN)
    @staticmethod
    def loading(msg): Logger.log("LOAD", "⟳", msg, Colors.CYAN)
    @staticmethod
    def step(msg): Logger.log("STEP", "➤", msg, Colors.WHITE)
    @staticmethod
    def action(msg): Logger.log("ACTION", "↪️", msg, Colors.CYAN)
    @staticmethod
    def actionSuccess(msg): Logger.log("ACTION", "✅", msg, Colors.GREEN)

logger = Logger()

install_solc('0.8.20')
set_solc_version('0.8.20')

class Helios:
    def __init__(self) -> None:
        self.BASE_API = "https://testnet-api.helioschain.network/api"
        self.RPC_URL = "https://testnet1.helioschainlabs.org/"
        self.HLS_CONTRACT_ADDRESS = "0xD4949664cD82660AaE99bEdc034a0deA8A0bd517"
        self.WETH_CONTRACT_ADDRESS = "0x80b5a32E4F032B2a058b4F29EC95EEfEEB87aDcd"
        self.WBNB_CONTRACT_ADDRESS = "0xd567B3d7B8FE3C79a1AD8dA978812cfC4Fa05e75"
        self.BRIDGE_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000900"
        self.DELEGATE_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000800"
        self.REWARDS_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000801"
        self.PROPOSAL_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000805"
        self.CHRONOS_ROUTER_ADDRESS = "0x0000000000000000000000000000000000000830"
        self.DEST_TOKENS = [
            { "Ticker": "Sepolia", "ChainId": 11155111 },
            { "Ticker": "BSC Testnet", "ChainId": 97 }
        ]
        self.VALIDATATORS = [
            {"Moniker": "Helios-Peer", "Contract Address": "0x72a9B3509B19D9Dbc2E0Df71c4A6451e8a3DD705"},
            {"Moniker": "Helios-Unity", "Contract Address": "0x7e62c5e7Eba41fC8c25e605749C476C0236e0604"},
            {"Moniker": "Helios-Supra", "Contract Address": "0xa75a393FF3D17eA7D9c9105d5459769EA3EAEf8D"},
            {"Moniker": "Helios-Inter", "Contract Address": "0x882f8A95409C127f0dE7BA83b4Dfa0096C3D8D79"}
        ]
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"decimals","stateMutability":"view","inputs":[],"outputs":[{"name":"","type":"uint8"}]},
            {"type":"function","name":"allowance","stateMutability":"view","inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"outputs":[{"name":"","type":"uint256"}]},
            {"type":"function","name":"approve","stateMutability":"nonpayable","inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"outputs":[{"name":"","type":"bool"}]}
        ]''')
        self.HELIOS_CONTRACT_ABI = [
            {
                "name": "sendToChain",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "name": "chainId", "type": "uint64", "internalType": "uint64" },
                    { "name": "destAddress", "type": "string", "internalType": "string" },
                    { "name": "contractAddress", "type": "address", "internalType": "address" },
                    { "name": "amount", "type": "uint256", "internalType": "uint256" },
                    { "name": "bridgeFee", "type": "uint256", "internalType": "uint256" }
                ],
                "outputs": [
                    { "name": "success", "type": "bool", "internalType": "bool" }
                ]
            },
            {
                "name": "delegate",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "delegatorAddress", "type": "address" },
                    { "internalType": "address", "name": "validatorAddress", "type": "address" },
                    { "internalType": "uint256", "name": "amount", "type": "uint256" },
                    { "internalType": "string", "name": "denom", "type": "string" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "name": "claimRewards",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "delegatorAddress", "type": "address" },
                    { "internalType": "uint32", "name": "maxRetrieve", "type": "uint32" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "type": "function",
                "name": "hyperionProposal",
                "stateMutability": "payable",
                "inputs": [
                    { "internalType": "string", "name": "title", "type": "string" },
                    { "internalType": "string", "name": "description", "type": "string" },
                    { "internalType": "string", "name": "msg", "type": "string" },
                    { "internalType": "uint256", "name": "initialDepositAmount", "type": "uint256" }
                ],
                "outputs": [
                    { "internalType": "uint64", "name": "proposalId", "type": "uint64" }
                ]
            },
            {
                "name": "vote",
                "type": "function",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "voter", "type": "address" },
                    { "internalType": "uint64", "name": "proposalId", "type": "uint64" },
                    { "internalType": "enum VoteOption", "name": "option", "type": "uint8" },
                    { "internalType": "string", "name": "metadata", "type": "string" }
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" }
                ]
            },
            {
                "type": "function",
                "name": "createCron",
                "stateMutability": "nonpayable",
                "inputs": [
                    { "internalType": "address", "name": "contractAddress", "type": "address" },
                    { "internalType": "string", "name": "abi", "type": "string" },
                    { "internalType": "string", "name": "methodName", "type": "string" },
                    { "internalType": "string[]", "name": "params", "type": "string[]" },
                    { "internalType": "uint64", "name": "frequency", "type": "uint64" },
                    { "internalType": "uint64", "name": "expirationBlock", "type": "uint64" },
                    { "internalType": "uint64", "name": "gasLimit", "type": "uint64" },
                    { "internalType": "uint256", "name": "maxGasPrice", "type": "uint256" },
                    { "internalType": "uint256", "name": "amountToDeposit", "type": "uint256" },
                ],
                "outputs": [
                    { "internalType": "bool", "name": "success", "type": "bool" },
                ]
            }
        ]
        self.PAGE_URL = "https://testnet.helioschain.network"
        self.SITE_KEY = "0x4AAAAAABhz7Yc1no53_eWA"
        self.CAPTCHA_KEY = None
        self.BASE_HEADERS = {}
        self.PORTAL_HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.used_nonce = {}
        self.bridge_count = 0
        self.bridge_amount = 0
        self.delegate_count = 0
        self.hls_delegate_amount = 0
        self.weth_delegate_amount = 0
        self.wbnb_delegate_amount = 0
        self.create_proposal = False
        self.proposal_title = None
        self.proposal_description = None
        self.proposal_deposit = 0
        self.vote_count = 0
        self.deploy_count = 0
        self.cron_count = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def welcome(self):
        now = datetime.now()
        print(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}")
        print("  ╔══════════════════════════════════════╗")
        print("  ║           HELIOS  B O T           ║")
        print("  ║                                    ║")
        print(f"  ║      {Colors.YELLOW}{now.strftime('%H:%M:%S %d.%m.%Y')}{Colors.BRIGHT_GREEN}            ║")
        print("  ║                                    ║")
        print("  ║      Helios TESTNET AUTOMATION      ║")
        print(f"  ║   {Colors.BRIGHT_WHITE}ZonaAirdrop{Colors.BRIGHT_GREEN}  |  t.me/ZonaAirdr0p  ║")
        print("  ╚══════════════════════════════════════╝")
        print(f"{Colors.RESET}")

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        try:
            with open("accounts.txt", 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            if not accounts:
                logger.error("No Accounts Found.")
                return None

            logger.info(
                f"Accounts Total  : {len(accounts)}"
            )

            return accounts
        except Exception as e:
            logger.error(f"Failed To Load Accounts: {e}")
            return None
    
    def load_2captcha_key(self):
        try:
            with open("2captcha_key.txt", 'r') as file:
                captcha_key = file.read().strip()
            return captcha_key
        except Exception as e:
            return None
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                if not os.path.exists(filename):
                    logger.error(f"File {filename} Not Found.")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies and use_proxy_choice == 1:
                logger.error(f"No Proxies Found.")
                return

            logger.info(
                f"Proxies Total  : {len(self.proxies)}"
            )
        
        except Exception as e:
            logger.error(f"Failed To Load Proxies: {e}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def build_proxy_config(self, proxy=None):
        if not proxy:
            return None, None, None

        if proxy.startswith("socks"):
            connector = ProxyConnector.from_url(proxy)
            return connector, None, None

        elif proxy.startswith("http"):
            match = re.match(r"http://(.*?):(.*?)@(.*)", proxy)
            if match:
                username, password, host_port = match.groups()
                clean_url = f"http://{host_port}"
                auth = BasicAuth(username, password)
                return None, clean_url, auth
            else:
                return None, proxy, None

        raise Exception("Unsupported Proxy Type.")
    
    def generate_address(self, account: str):
        try:
            account = Account.from_key(account)
            address = account.address
            
            return address
        except Exception as e:
            logger.error(f"Generate Address Failed - {str(e)}")
            return None
        
    def generate_payload(self, account: str, address: str):
        try:
            message = f"Welcome to Helios! Please sign this message to verify your wallet ownership.\n\nWallet: {address}"
            encoded_message = encode_defunct(text=message)
            signed_message = Account.sign_message(encoded_message, private_key=account)
            signature = to_hex(signed_message.signature)

            payload = {
                "wallet": address,
                "signature": signature
            }

            return payload
        except Exception as e:
            logger.error(f"Generate Req Payload Failed - {str(e)}")
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    def generate_random_asset(self):
        asset = random.choice([
            self.HLS_CONTRACT_ADDRESS,
            self.WETH_CONTRACT_ADDRESS,
            self.WBNB_CONTRACT_ADDRESS
        ])

        if asset == self.HLS_CONTRACT_ADDRESS:
            denom = "ahelios"
            ticker = "HLS"
            amount = self.hls_delegate_amount
        elif asset == self.WETH_CONTRACT_ADDRESS:
            denom = "hyperion-11155111-0x7b79995e5f793A07Bc00c21412e50Ecae098E7f9"
            ticker = "WETH"
            amount = self.weth_delegate_amount
        else:
            denom = "hyperion-97-0xC689BF5a007F44410676109f8aa8E3562da1c9Ba"
            ticker = "WBNB"
            amount = self.wbnb_delegate_amount

        return asset, ticker, denom, amount
        
    def generate_raw_token(self):
        numbers = random.randint(0, 99999)
        token_name = f"Token{numbers}"
        token_symbol = f"T{numbers}"
        raw_supply = random.randint(1000, 1_000_000)
        total_supply = raw_supply * (10 ** 18)

        return token_name, token_symbol, raw_supply, total_supply
        
    async def get_web3_with_check(self, address: str, use_proxy: bool):
        retries = 3
        timeout = 60
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            connector, proxy_url, auth = self.build_proxy_config(proxy)
            if connector:
                request_kwargs["connector"] = connector
            elif proxy_url:
                request_kwargs["proxy"] = proxy_url
                if auth:
                    request_kwargs["proxy_headers"] = {"Proxy-Authorization": auth.encode()}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                logger.warn(f"Failed to connect to RPC ({attempt + 1}/{retries}): {str(e)}")
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                else:
                    raise Exception(f"Failed to Connect to RPC After {retries} Retries: {str(e)}")
            
    async def send_raw_transaction_with_retries(self, account, web3, tx, retries=5):
        for attempt in range(retries):
            try:
                signed_tx = web3.eth.account.sign_transaction(tx, account)
                raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
                tx_hash = web3.to_hex(raw_tx)
                return tx_hash
            except TransactionNotFound:
                pass
            except Exception as e:
                logger.warn(f"[Attempt {attempt + 1}] Send TX Error: {str(e)}")
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Hash Not Found After Maximum Retries")

    async def wait_for_receipt_with_retries(self, web3, tx_hash, retries=5):
        for attempt in range(retries):
            try:
                receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
                return receipt
            except TransactionNotFound:
                pass
            except Exception as e:
                logger.warn(f"[Attempt {attempt + 1}] Wait for Receipt Error: {str(e)}")
            await asyncio.sleep(2 ** attempt)
        raise Exception("Transaction Receipt Not Found After Maximum Retries")
        
    async def get_token_balance(self, address: str, contract_address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
            balance = token_contract.functions.balanceOf(address).call()
            decimals = token_contract.functions.decimals().call()

            token_balance = balance / (10 ** decimals)

            return token_balance
        except Exception as e:
            logger.error(str(e))
            return None
    
    async def approving_token(self, account: str, address: str, spender_address: str, contract_address: str, estimated_fees: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            spender = web3.to_checksum_address(spender_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
            decimals = token_contract.functions.decimals().call()

            amount_to_wei = int(self.bridge_amount * (10 ** decimals)) + estimated_fees

            allowance = token_contract.functions.allowance(address, spender).call()
            if allowance < amount_to_wei:
                approve_data = token_contract.functions.approve(spender, amount_to_wei)

                latest_block = web3.eth.get_block("latest")
                base_fee = latest_block.get("baseFeePerGas", 0)
                max_priority_fee = web3.to_wei(1.111, "gwei")
                max_fee = base_fee + max_priority_fee

                approve_tx = approve_data.build_transaction({
                    "from": address,
                    "gas": 1500000,
                    "maxFeePerGas": int(max_fee),
                    "maxPriorityFeePerGas": int(max_priority_fee),
                    "nonce": self.used_nonce[address],
                    "chainId": web3.eth.chain_id,
                })

                tx_hash = await self.send_raw_transaction_with_retries(account, web3, approve_tx)
                receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
                block_number = receipt.blockNumber
                self.used_nonce[address] += 1
                
                explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
                
                logger.success(f"Approve Success")
                logger.info(f"Block: {block_number}")
                logger.info(f"Tx Hash: {tx_hash}")
                logger.info(f"Explorer: {explorer}")
                await asyncio.sleep(10)
            
            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")

    async def perform_bridge(self, account: str, address: str, dest_chain_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            bridge_amount = web3.to_wei(self.bridge_amount, "ether")
            estimated_fees = int(0.5 * (10 ** 18))

            await self.approving_token(account, address, self.BRIDGE_ROUTER_ADDRESS, self.HLS_CONTRACT_ADDRESS, estimated_fees, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.BRIDGE_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            bridge_data = token_contract.functions.sendToChain(
                dest_chain_id, address, self.HLS_CONTRACT_ADDRESS, bridge_amount, estimated_fees
            )

            estimated_gas = bridge_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = max_priority_fee

            bridge_tx = bridge_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, bridge_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            logger.error(str(e))
            return None, None
        
    async def perform_delegate(self, account: str, address: str, contract_address: str, denom: str, delegate_amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.DELEGATE_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)
            amount = web3.to_wei(delegate_amount, "ether")
            
            delegate_data = token_contract.functions.delegate(address, contract_address, amount, denom)

            estimated_gas = delegate_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            delegate_tx = delegate_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, delegate_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            logger.error(str(e))
            return None, None
        
    async def perform_claim_rewards(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.REWARDS_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)
            claim_data = token_contract.functions.claimRewards(address, 10)

            estimated_gas = claim_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            claim_tx = claim_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, claim_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            logger.error(str(e))
            return None, None
        
    async def perform_create_proposal(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            msg = json.dumps({
                "@type": "/helios.hyperion.v1.MsgUpdateOutTxTimeout",
                "signer": address,
                "chain_id": random.choice([11155111, 97]),
                "target_batch_timeout": 3600000,
                "target_outgoing_tx_timeout": 3600000
            })
            amount_to_wei = web3.to_wei(self.proposal_deposit, "ether")
            
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.PROPOSAL_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)
            proposal_data = token_contract.functions.hyperionProposal(
                self.proposal_title, self.proposal_description, msg, amount_to_wei
            )

            estimated_gas = proposal_data.estimate_gas({"from": address, "value": amount_to_wei})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            proposal_tx = proposal_data.build_transaction({
                "from": address,
                "value": amount_to_wei,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, proposal_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            logger.error(str(e))
            return None, None
        
    async def perform_vote(self, account: str, address: str, proposal_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.PROPOSAL_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)
            
            options = ["Yes", "No", "Abstain", "NoWithVeto"]
            vote_option = random.choice(options)
            option_id = options.index(vote_option)
            
            vote_data = token_contract.functions.vote(
                address, proposal_id, option_id, "Vote from Helios Bot"
            )

            estimated_gas = vote_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            vote_tx = vote_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, vote_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1

            return tx_hash, block_number
        except Exception as e:
            logger.error(str(e))
            return None, None
    
    async def deploy_contract(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_name, token_symbol, raw_supply, total_supply = self.generate_raw_token()

            contract_source_code = f'''
            // SPDX-License-Identifier: MIT
            pragma solidity ^0.8.20;

            import "https://github.com/OpenZeppelin/openzeppelin-contracts/blob/master/contracts/token/ERC20/ERC20.sol";

            contract {token_name} is ERC20 {{
                constructor() ERC20("{token_name}", "{token_symbol}") {{
                    _mint(msg.sender, {total_supply});
                }}
            }}
            '''
            
            compiled_sol = compile_source(contract_source_code)
            contract_interface = compiled_sol.get(f'<stdin>:{token_name}')
            
            Contract = web3.eth.contract(abi=contract_interface['abi'], bytecode=contract_interface['bin'])

            latest_block = web3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas", 0)
            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = base_fee + max_priority_fee

            constructor_tx = Contract.constructor().build_transaction({
                "from": address,
                "gas": 1500000,
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id,
            })
            
            tx_hash = await self.send_raw_transaction_with_retries(account, web3, constructor_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1
            contract_address = receipt.contractAddress

            return tx_hash, block_number, contract_address, token_name, token_symbol
        except Exception as e:
            logger.error(str(e))
            return None, None, None, None, None

    async def perform_create_cron(self, account: str, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            contract_address = input(f"{Colors.BRIGHT_MAGENTA}Input Contract Address To Create Cron: {Colors.RESET}")
            if not contract_address.startswith("0x"):
                logger.error("Invalid Contract Address. Aborting.")
                return None, None
            
            abi_input = input(f"{Colors.BRIGHT_MAGENTA}Input Contract ABI (JSON string): {Colors.RESET}")
            try:
                json.loads(abi_input)
            except json.JSONDecodeError:
                logger.error("Invalid ABI format. Please provide a valid JSON string. Aborting.")
                return None, None
            
            method_name = input(f"{Colors.BRIGHT_MAGENTA}Input Method Name: {Colors.RESET}")
            if not method_name:
                logger.error("Invalid Method Name. Aborting.")
                return None, None
            
            params_input = input(f"{Colors.BRIGHT_MAGENTA}Input Parameters (e.g., 'param1,param2' or leave empty for no params): {Colors.RESET}")
            params = [p.strip() for p in params_input.split(',')] if params_input else []
            
            frequency = int(input(f"{Colors.BRIGHT_MAGENTA}Input Frequency in blocks: {Colors.RESET}"))
            expiration_block = int(input(f"{Colors.BRIGHT_MAGENTA}Input Expiration Block: {Colors.RESET}"))
            gas_limit = int(input(f"{Colors.BRIGHT_MAGENTA}Input Gas Limit: {Colors.RESET}"))
            max_gas_price_gwei = float(input(f"{Colors.BRIGHT_MAGENTA}Input Max Gas Price (in Gwei): {Colors.RESET}"))
            max_gas_price_wei = web3.to_wei(max_gas_price_gwei, "gwei")
            amount_to_deposit = float(input(f"{Colors.BRIGHT_MAGENTA}Input Amount To Deposit (in Ether): {Colors.RESET}"))
            amount_to_deposit_wei = web3.to_wei(amount_to_deposit, "ether")

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.CHRONOS_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)
            
            cron_data = token_contract.functions.createCron(
                web3.to_checksum_address(contract_address),
                abi_input,
                method_name,
                params,
                frequency,
                expiration_block,
                gas_limit,
                max_gas_price_wei,
                amount_to_deposit_wei
            )

            estimated_gas = cron_data.estimate_gas({"from": address})
            max_priority_fee = web3.to_wei(2.5, "gwei")
            max_fee = web3.to_wei(4.5, "gwei")

            cron_tx = cron_data.build_transaction({
                "from": address,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, cron_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            block_number = receipt.blockNumber
            self.used_nonce[address] += 1
            
            return tx_hash, block_number
        except Exception as e:
            logger.error(f"Error creating cron job: {str(e)}")
            return None, None

    async def main(self):
        try:
            self.clear_terminal()
            self.welcome()
            accounts = self.load_accounts()
            if not accounts:
                return

            use_proxy_choice = int(input(f"{Colors.BRIGHT_MAGENTA}Use Proxy? (1. Yes / 2. No) : {Colors.RESET}"))
            if use_proxy_choice == 1:
                await self.load_proxies(use_proxy_choice=use_proxy_choice)

            for account in accounts:
                address = self.generate_address(account)
                if address not in self.used_nonce:
                    web3_conn = await self.get_web3_with_check(address, use_proxy_choice == 1)
                    if web3_conn:
                        self.used_nonce[address] = await asyncio.to_thread(web3_conn.eth.get_transaction_count, address)
                    else:
                        logger.error(f"Could not get nonce for account {self.mask_account(account)}. Skipping.")
                        continue

            while True:
                self.clear_terminal()
                self.welcome()
                print(f"""
{Colors.CYAN+Style.BRIGHT}
    1. Run Bridge
    2. Run Delegate
    3. Run Claim Rewards
    4. Run Create Proposal
    5. Run Vote Proposal
    6. Run Deploy Contract
    7. Run Create Cron (Deploy CHRONOS)
    8. Run All Features
    0. Exit
{Style.RESET_ALL}
                """)
                choice = input(f"{Colors.BRIGHT_MAGENTA}Pilih Opsi: {Colors.RESET}")

                if choice == "1":
                    self.bridge_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many bridge transactions? : {Colors.RESET}"))
                    self.bridge_amount = float(input(f"{Colors.BRIGHT_MAGENTA}Amount to bridge: {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Bridge for account: {self.mask_account(account)}")
                        for _ in range(self.bridge_count):
                            logger.action("Performing Bridge Transaction...")
                            dest_chain = random.choice(self.DEST_TOKENS)
                            tx_hash, block_number = await self.perform_bridge(account, address, dest_chain["ChainId"], use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Bridge Success to {dest_chain['Ticker']} at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Bridge Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                        
                elif choice == "2":
                    self.delegate_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many delegate transactions? : {Colors.RESET}"))
                    self.hls_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}HLS amount to delegate: {Colors.RESET}"))
                    self.weth_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}WETH amount to delegate: {Colors.RESET}"))
                    self.wbnb_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}WBNB amount to delegate: {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Delegate for account: {self.mask_account(account)}")
                        for _ in range(self.delegate_count):
                            logger.action("Performing Delegate Transaction...")
                            validator = random.choice(self.VALIDATATORS)
                            contract_address, ticker, denom, amount = self.generate_random_asset()
                            tx_hash, block_number = await self.perform_delegate(account, address, validator["Contract Address"], denom, amount, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Delegate {amount} {ticker} to {validator['Moniker']} Success at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Delegate Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "3":
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Claim Rewards for account: {self.mask_account(account)}")
                        logger.action("Performing Claim Rewards Transaction...")
                        tx_hash, block_number = await self.perform_claim_rewards(account, address, use_proxy_choice == 1)
                        if tx_hash:
                            logger.actionSuccess(f"Claim Rewards Success at block: {block_number}")
                            logger.info(f"Tx Hash: {tx_hash}")
                        else:
                            logger.error(f"Claim Rewards Failed for account {self.mask_account(account)}")
                        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "4":
                    self.create_proposal = bool(input(f"{Colors.BRIGHT_MAGENTA}Create a proposal? (y/n) : {Colors.RESET}").lower() == 'y')
                    if self.create_proposal:
                        self.proposal_title = input(f"{Colors.BRIGHT_MAGENTA}Proposal Title: {Colors.RESET}")
                        self.proposal_description = input(f"{Colors.BRIGHT_MAGENTA}Proposal Description: {Colors.RESET}")
                        self.proposal_deposit = float(input(f"{Colors.BRIGHT_MAGENTA}Proposal Initial Deposit (in Ether): {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Create Proposal for account: {self.mask_account(account)}")
                        if self.create_proposal:
                            logger.action("Performing Create Proposal Transaction...")
                            tx_hash, block_number = await self.perform_create_proposal(account, address, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Create Proposal Success at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Create Proposal Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                        
                elif choice == "5":
                    self.vote_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many vote transactions? : {Colors.RESET}"))
                    proposal_id = int(input(f"{Colors.BRIGHT_MAGENTA}Input Proposal ID to Vote: {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Vote Proposal for account: {self.mask_account(account)}")
                        for _ in range(self.vote_count):
                            logger.action("Performing Vote Transaction...")
                            tx_hash, block_number = await self.perform_vote(account, address, proposal_id, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Vote Success on proposal {proposal_id} at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Vote Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "6":
                    self.deploy_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many contract deployments? : {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address: continue
                        logger.step(f"Starting Deploy Contract for account: {self.mask_account(account)}")
                        for _ in range(self.deploy_count):
                            logger.action("Performing Deploy Contract Transaction...")
                            tx_hash, block_number, contract_address, token_name, token_symbol = await self.deploy_contract(account, address, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Deploy Contract {token_name} ({token_symbol}) Success at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                                logger.info(f"Contract Address: {contract_address}")
                            else:
                                logger.error(f"Deploy Contract Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "7":
                    self.cron_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many cron jobs? : {Colors.RESET}"))
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address:
                            continue
                        logger.step(f"Starting CHRONOS (Create Cron) for account: {self.mask_account(account)}")
                        for _ in range(self.cron_count):
                            logger.action("Performing Create Cron Transaction...")
                            tx_hash, block_number = await self.perform_create_cron(account, address, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Create Cron Success at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Create Cron Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "8":
                    self.bridge_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many bridge transactions? : {Colors.RESET}"))
                    self.bridge_amount = float(input(f"{Colors.BRIGHT_MAGENTA}Amount to bridge: {Colors.RESET}"))
                    self.delegate_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many delegate transactions? : {Colors.RESET}"))
                    self.hls_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}HLS amount to delegate: {Colors.RESET}"))
                    self.weth_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}WETH amount to delegate: {Colors.RESET}"))
                    self.wbnb_delegate_amount = float(input(f"{Colors.BRIGHT_MAGENTA}WBNB amount to delegate: {Colors.RESET}"))
                    self.create_proposal = bool(input(f"{Colors.BRIGHT_MAGENTA}Create a proposal? (y/n) : {Colors.RESET}").lower() == 'y')
                    if self.create_proposal:
                        self.proposal_title = input(f"{Colors.BRIGHT_MAGENTA}Proposal Title: {Colors.RESET}")
                        self.proposal_description = input(f"{Colors.BRIGHT_MAGENTA}Proposal Description: {Colors.RESET}")
                        self.proposal_deposit = float(input(f"{Colors.BRIGHT_MAGENTA}Proposal Initial Deposit: {Colors.RESET}"))
                    self.vote_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many vote transactions? : {Colors.RESET}"))
                    self.deploy_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many contract deployments? : {Colors.RESET}"))
                    self.cron_count = int(input(f"{Colors.BRIGHT_MAGENTA}How many cron jobs? : {Colors.RESET}"))
                    self.min_delay = int(input(f"{Colors.BRIGHT_MAGENTA}Min Delay (seconds): {Colors.RESET}"))
                    self.max_delay = int(input(f"{Colors.BRIGHT_MAGENTA}Max Delay (seconds): {Colors.RESET}"))
                    
                    for account in accounts:
                        address = self.generate_address(account)
                        if not address:
                            continue
                        logger.step(f"Starting all features for account: {self.mask_account(account)}")

                        if self.bridge_count > 0:
                            for _ in range(self.bridge_count):
                                logger.action("Performing Bridge Transaction...")
                                dest_chain = random.choice(self.DEST_TOKENS)
                                tx_hash, block_number = await self.perform_bridge(account, address, dest_chain["ChainId"], use_proxy_choice == 1)
                                if tx_hash:
                                    logger.actionSuccess(f"Bridge Success to {dest_chain['Ticker']} at block: {block_number}")
                                    logger.info(f"Tx Hash: {tx_hash}")
                                else:
                                    logger.error(f"Bridge Failed for account {self.mask_account(account)}")
                                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                        
                        if self.delegate_count > 0:
                            for _ in range(self.delegate_count):
                                logger.action("Performing Delegate Transaction...")
                                validator = random.choice(self.VALIDATATORS)
                                contract_address, ticker, denom, amount = self.generate_random_asset()
                                tx_hash, block_number = await self.perform_delegate(account, address, validator["Contract Address"], denom, amount, use_proxy_choice == 1)
                                if tx_hash:
                                    logger.actionSuccess(f"Delegate {amount} {ticker} to {validator['Moniker']} Success at block: {block_number}")
                                    logger.info(f"Tx Hash: {tx_hash}")
                                else:
                                    logger.error(f"Delegate Failed for account {self.mask_account(account)}")
                                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                        logger.action("Performing Claim Rewards Transaction...")
                        tx_hash, block_number = await self.perform_claim_rewards(account, address, use_proxy_choice == 1)
                        if tx_hash:
                            logger.actionSuccess(f"Claim Rewards Success at block: {block_number}")
                            logger.info(f"Tx Hash: {tx_hash}")
                        else:
                            logger.error(f"Claim Rewards Failed for account {self.mask_account(account)}")
                        await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))
                        
                        if self.create_proposal:
                            logger.action("Performing Create Proposal Transaction...")
                            tx_hash, block_number = await self.perform_create_proposal(account, address, use_proxy_choice == 1)
                            if tx_hash:
                                logger.actionSuccess(f"Create Proposal Success at block: {block_number}")
                                logger.info(f"Tx Hash: {tx_hash}")
                            else:
                                logger.error(f"Create Proposal Failed for account {self.mask_account(account)}")
                            await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                        if self.vote_count > 0:
                            for _ in range(self.vote_count):
                                logger.action("Performing Vote Transaction...")
                                proposal_id = int(input(f"{Colors.BRIGHT_MAGENTA}Input Proposal ID to Vote: {Colors.RESET}"))
                                tx_hash, block_number = await self.perform_vote(account, address, proposal_id, use_proxy_choice == 1)
                                if tx_hash:
                                    logger.actionSuccess(f"Vote Success on proposal {proposal_id} at block: {block_number}")
                                    logger.info(f"Tx Hash: {tx_hash}")
                                else:
                                    logger.error(f"Vote Failed for account {self.mask_account(account)}")
                                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                        if self.deploy_count > 0:
                            for _ in range(self.deploy_count):
                                logger.action("Performing Deploy Contract Transaction...")
                                tx_hash, block_number, contract_address, token_name, token_symbol = await self.deploy_contract(account, address, use_proxy_choice == 1)
                                if tx_hash:
                                    logger.actionSuccess(f"Deploy Contract {token_name} ({token_symbol}) Success at block: {block_number}")
                                    logger.info(f"Tx Hash: {tx_hash}")
                                    logger.info(f"Contract Address: {contract_address}")
                                else:
                                    logger.error(f"Deploy Contract Failed for account {self.mask_account(account)}")
                                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                        if self.cron_count > 0:
                            for _ in range(self.cron_count):
                                logger.action("Performing Create Cron (CHRONOS) Transaction...")
                                tx_hash, block_number = await self.perform_create_cron(account, address, use_proxy_choice == 1)
                                if tx_hash:
                                    logger.actionSuccess(f"Create Cron Success at block: {block_number}")
                                    logger.info(f"Tx Hash: {tx_hash}")
                                else:
                                    logger.error(f"Create Cron Failed for account {self.mask_account(account)}")
                                await asyncio.sleep(random.uniform(self.min_delay, self.max_delay))

                elif choice == "0":
                    break
                else:
                    logger.warn("Invalid option. Please choose again.")
            
            logger.info(f"All Accounts Have Been Processed.")
            seconds = 24 * 60 * 60
            while seconds > 0:
                formatted_time = self.format_seconds(seconds)
                print(
                    f"{Fore.CYAN + Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                    f"{Fore.CYAN + Style.BRIGHT} ]{Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                    f"{Fore.BLUE + Style.BRIGHT}All All Task Completeed.{Style.RESET_ALL}",
                    end="\r"
                )
                await asyncio.sleep(1)
                seconds -= 1

        except FileNotFoundError:
            logger.error(f"File 'accounts.txt' Not Found.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e

if __name__ == '__main__':
    try:
        bot = Helios()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%H:%M:%S')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Helios - BOT{Style.RESET_ALL}"
        )
