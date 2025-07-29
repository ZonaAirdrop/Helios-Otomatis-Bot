from web3 import Web3
from web3.exceptions import TransactionNotFound
from eth_utils import to_hex
from eth_account import Account
from eth_account.messages import encode_defunct
from aiohttp import ClientResponseError, ClientSession, ClientTimeout, BasicAuth
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import init, Fore, Style
import asyncio, random, json, re, os, time, pytz

init(autoreset=True)

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
    BLUE = Fore.BLUE

class Logger:
    @staticmethod
    def log(label, symbol, msg, color):
        timestamp = datetime.now().astimezone(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S")
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

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

async def display_welcome_screen():
    clear_console()
    now = datetime.now()
    print(f"{Colors.BRIGHT_GREEN}{Colors.BOLD}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║         HELIOS   B O T            ║")
    print("  ║                                      ║")
    print(f"  ║      {Colors.YELLOW}{now.strftime('%H:%M:%S %d.%m.%Y')}{Colors.BRIGHT_GREEN}          ║")
    print("  ║                                      ║")
    print("  ║      Helios TESTNET AUTOMATION        ║")
    print(f"  ║   {Colors.BRIGHT_WHITE}ZonaAirdrop{Colors.BRIGHT_GREEN}  |  t.me/ZonaAirdr0p   ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{Colors.RESET}")
    await asyncio.sleep(1)


class Helios:
    def __init__(self) -> None:
        self.BASE_API = "https://testnet-api.helioschain.network/api"
        self.RPC_URL = "https://testnet1.helioschainlabs.org/"
        self.HELIOS_CONTRACT_ADDRESS = "0xD4949664cD82660AaE99bEdc034a0deA8A0bd517"
        self.BRIDGE_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000900"
        self.DELEGATE_CONTRACT_ADDRESS = "0x0000000000000000000000000000000000000800"
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
        
        self.SOLARI_BASE_API = "https://api.solariswap.finance/v1"
        self.WETH_CONTRACT_ADDRESS = "0x80b5a32E4F032B2a058b4F29EC95EEfEEB87aDcd"
        self.WBNB_CONTRACT_ADDRESS = "0xd567B3d7B8FE3C79a1AD8dA978812cfC4Fa05e75"
        self.SWAP_ROUTER_ADDRESS = "0xe80Ee0F963E9F636035B36bb1a40d0609f437C45"
        
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
            }
        ]
        
        self.SOLARISWAP_CONTRACT_ABI = [
            {
                "type": "function",
                "name": "exactInputSingle",
                "stateMutability": "payable",
                "inputs": [
                    {
                        "components": [
                            { "internalType": "address", "name": "tokenIn", "type": "address" }, 
                            { "internalType": "address", "name": "tokenOut", "type": "address" }, 
                            { "internalType": "uint24", "name": "fee", "type": "uint24" }, 
                            { "internalType": "address", "name": "recipient", "type": "address" }, 
                            { "internalType": "uint256", "name": "deadline", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountIn", "type": "uint256" }, 
                            { "internalType": "uint256", "name": "amountOutMinimum", "type": "uint256" }, 
                            { "internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160" }
                        ],
                        "internalType": "struct ISwapRouter.ExactInputSingleParams",
                        "name": "params",
                        "type": "tuple"
                    }
                ],
                "outputs": [
                    { "internalType": "uint256", "name": "amountOut", "type": "uint256" }
                ]
            }
        ]
        
        self.PAGE_URL = "https://testnet.helioschain.network"
        self.SITE_KEY = "0x4AAAAAABhz7Yc1no53_eWA"
        self.CAPTCHA_KEY = None
        self.HEADERS = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.access_tokens = {}
        self.used_nonce = {}
        
        self.bridge_count = 0
        self.bridge_amount = 0
        self.delegate_count = 0
        self.delegate_amount = 0
        self.swap_count = 0
        self.helios_amount = 0
        self.weth_amount = 0
        self.wbnb_amount = 0
        
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        clear_console()

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_2captcha_key(self):
        try:
            with open("2captcha_key.txt", 'r') as file:
                captcha_key = file.read().strip()
            return captcha_key
        except Exception as e:
            logger.error(f"Failed to load 2Captcha key: {e}")
            return None
    
    async def load_proxies(self, use_proxy_choice: bool):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/refs/heads/main/proxies/http.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    logger.error(f"File {filename} Not Found.")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                logger.error("No Proxies Found.")
                return

            logger.info(f"Proxies Total: {len(self.proxies)}")
        
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
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.RPC_URL, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
            
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
            logger.error(f"Get Token Balance Failed: {str(e)}")
            return None
    
    async def approving_token(self, account: str, address: str, spender_address: str, contract_address: str, amount_in: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            spender = web3.to_checksum_address(spender_address)
            token_contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=self.ERC20_CONTRACT_ABI)
            decimals = token_contract.functions.decimals().call()

            amount_to_wei = int(amount_in * (10 ** decimals))

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
                self.used_nonce[address] += 1
                
                explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
                
                logger.success("Approve Success")
                logger.action(f"Tx Hash: {tx_hash}")
                logger.actionSuccess(f"Explorer: {explorer}")
                await asyncio.sleep(10)
            
            return True
        except Exception as e:
            raise Exception(f"Approving Token Contract Failed: {str(e)}")

    async def perform_bridge(self, account: str, address: str, dest_chain_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            
            bridge_amount = web3.to_wei(self.bridge_amount, "ether")
            estimated_fees = int(0.5 * (10 ** 18))

            await self.approving_token(account, address, self.BRIDGE_CONTRACT_ADDRESS, self.HELIOS_CONTRACT_ADDRESS, self.bridge_amount + 0.5, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.BRIDGE_CONTRACT_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            bridge_data = token_contract.functions.sendToChain(
                dest_chain_id, address, self.HELIOS_CONTRACT_ADDRESS, bridge_amount, estimated_fees
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
            self.used_nonce[address] += 1

            return tx_hash
        except Exception as e:
            logger.error(f"Perform Bridge Failed: {str(e)}")
            return None
        
    async def perform_delegate(self, account: str, address: str, contract_address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.DELEGATE_CONTRACT_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            delegate_amount = web3.to_wei(self.delegate_amount, "ether")

            delegate_data = token_contract.functions.delegate(address, contract_address, delegate_amount, "ahelios")

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
            self.used_nonce[address] += 1

            return tx_hash
        except Exception as e:
            logger.error(f"Perform Delegate Failed: {str(e)}")
            return None
    
    async def perform_swap(self, account: str, address: str, token_in: str, token_out: str, swap_amount: float, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            await self.approving_token(account, address, self.SWAP_ROUTER_ADDRESS, token_in, swap_amount, use_proxy)
            
            amount_in = web3.to_wei(swap_amount, "ether")
            deadline = int(time.time()) + 600

            quote_token = await self.fetch_quote_token(address, token_in, token_out, amount_in, use_proxy)
            if not quote_token:
                raise Exception("Fetch Quote Token Failed")
            
            fee = quote_token["pool"]["fee"]
            amount_out = int(quote_token["amountOut"])

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.SWAP_ROUTER_ADDRESS), abi=self.SOLARISWAP_CONTRACT_ABI)

            swap_data = token_contract.functions.exactInputSingle((token_in, token_out, fee, address, deadline, amount_in, amount_out, 0))

            estimated_gas = swap_data.estimate_gas({"from": address, "value": amount_in})
            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = max_priority_fee

            swap_tx = swap_data.build_transaction({
                "from": address,
                "value": amount_in,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, swap_tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            self.used_nonce[address] += 1

            return tx_hash
        except Exception as e:
            logger.error(f"Perform Swap Failed: {str(e)}")
            return None
        
    async def fetch_quote_token(self, address: str, token_in: str, token_out: str, amount_in: int, use_proxy: bool, retries=5):
        url = f"{self.SOLARI_BASE_API}/quote?tokenIn={token_in}&tokenOut={token_out}&amountIn={amount_in}&mode=exactInput"
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.get(url=url, headers=self.HEADERS[address], proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                return None
    
    def generate_swap_option(self):
        swap_options = [
            ("HELIOS to WETH", "HLS", self.HELIOS_CONTRACT_ADDRESS, self.WETH_CONTRACT_ADDRESS, self.helios_amount),
            ("HELIOS to WBNB", "HLS", self.HELIOS_CONTRACT_ADDRESS, self.WBNB_CONTRACT_ADDRESS, self.helios_amount),
            ("WETH to HELIOS", "WETH", self.WETH_CONTRACT_ADDRESS, self.HELIOS_CONTRACT_ADDRESS, self.weth_amount),
            ("WETH to WBNB", "WETH", self.WETH_CONTRACT_ADDRESS, self.WBNB_CONTRACT_ADDRESS, self.weth_amount),
            ("WBNB to HELIOS", "WBNB", self.WBNB_CONTRACT_ADDRESS, self.HELIOS_CONTRACT_ADDRESS, self.wbnb_amount),
            ("WBNB to WETH", "WBNB", self.WBNB_CONTRACT_ADDRESS, self.WETH_CONTRACT_ADDRESS, self.wbnb_amount),
        ]
        return random.choice(swap_options)

    def print_bridge_question(self):
        while True:
            try:
                bridge_count = int(input(f"{Colors.GREEN}{Colors.BOLD}Bridge Count For Each Wallet:{Colors.RESET} ").strip())
                if bridge_count > 0:
                    self.bridge_count = bridge_count
                    break
                else:
                    logger.error("Bridge Count must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a number.")

        while True:
            try:
                bridge_amount = float(input(f"{Colors.GREEN}{Colors.BOLD}Enter Bridge Amount [1 or 0.01 or 0.001, etc in decimals]:{Colors.RESET} ").strip())
                if bridge_amount > 0:
                    self.bridge_amount = bridge_amount
                    break
                else:
                    logger.error("Bridge Amount must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a float or decimal number.")

    def print_delegate_question(self):
        while True:
            try:
                delegate_count = int(input(f"{Colors.GREEN}{Colors.BOLD}Delegate Count For Each Wallet:{Colors.RESET} ").strip())
                if delegate_count > 0:
                    self.delegate_count = delegate_count
                    break
                else:
                    logger.error("Delegate Count must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a number.")

        while True:
            try:
                delegate_amount = float(input(f"{Colors.GREEN}{Colors.BOLD}Enter Delegate Amount [1 or 0.01 or 0.001, etc in decimals]:{Colors.RESET} ").strip())
                if delegate_amount > 0:
                    self.delegate_amount = delegate_amount
                    break
                else:
                    logger.error("Delegate Amount must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a float or decimal number.")

    def print_swap_question(self):
        while True:
            try:
                swap_count = int(input(f"{Colors.GREEN}{Colors.BOLD}Swap Count For Each Wallet:{Colors.RESET} ").strip())
                if swap_count > 0:
                    self.swap_count = swap_count
                    break
                else:
                    logger.error("Swap Count must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a number.")

    def print_helios_question(self):
        while True:
            try:
                helios_amount = float(input(f"{Colors.GREEN}{Colors.BOLD}Enter HLS Amount:{Colors.RESET} ").strip())
                if helios_amount > 0:
                    self.helios_amount = helios_amount
                    break
                else:
                    logger.error("HLS Amount must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a float or decimal number.")
    
    def print_weth_question(self):
        while True:
            try:
                weth_amount = float(input(f"{Colors.GREEN}{Colors.BOLD}Enter WETH Amount:{Colors.RESET} ").strip())
                if weth_amount > 0:
                    self.weth_amount = weth_amount
                    break
                else:
                    logger.error("WETH Amount must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a float or decimal number.")
    
    def print_wbnb_question(self):
        while True:
            try:
                wbnb_amount = float(input(f"{Colors.GREEN}{Colors.BOLD}Enter WBNB Amount:{Colors.RESET} ").strip())
                if wbnb_amount > 0:
                    self.wbnb_amount = wbnb_amount
                    break
                else:
                    logger.error("WBNB Amount must be > 0.")
            except ValueError:
                logger.error("Invalid input. Enter a float or decimal number.")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Colors.YELLOW}{Colors.BOLD}Min Delay For Each Tx:{Colors.RESET} ").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    logger.error("Min Delay must be >= 0.")
            except ValueError:
                logger.error("Invalid input. Enter a number.")

        while True:
            try:
                max_delay = int(input(f"{Colors.YELLOW}{Colors.BOLD}Max Delay For Each Tx:{Colors.RESET} ").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    logger.error("Max Delay must be >= Min Delay.")
            except ValueError:
                logger.error("Invalid input. Enter a number.")
         
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            timestamp = datetime.now().astimezone(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S")
            print(
                f"{Colors.BRIGHT_BLACK}[{timestamp}]{Colors.RESET}"
                f"{Colors.WHITE}{Colors.BOLD} | {Colors.RESET}"
                f"{Colors.BLUE}{Colors.BOLD}Wait For{Colors.RESET}"
                f"{Colors.WHITE}{Colors.BOLD} {remaining} {Colors.RESET}"
                f"{Colors.BLUE}{Colors.BOLD}Seconds For Next Tx...{Colors.RESET}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)
        print(" " * 80, end="\r") # Clear the line after countdown

    def print_question(self):
        while True:
            try:
                print(f"{Colors.GREEN}{Colors.BOLD}Select Option:{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}1. Claim HLS Faucet{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}2. Bridge HLS{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}3. Delegate HLS{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}4. Swap Tokens{Colors.RESET}")
                print(f"{Colors.GREEN}{Colors.BOLD}5. Run All Features{Colors.RESET}")
                option = int(input(f"{Colors.WHITE}{Colors.BOLD}Choose [1/2/3/4/5]:{Colors.RESET} ").strip())

                if option in [1, 2, 3, 4, 5]:
                    option_type = (
                        "Claim HLS Faucet" if option == 1 else 
                        "Bridge HLS" if option == 2 else 
                        "Delegate HLS" if option == 3 else
                        "Swap Tokens" if option == 4 else
                        "Run All Features"
                    )
                    logger.success(f"{option_type} Selected.")
                    break
                else:
                    logger.error("Please enter either 1, 2, 3, 4 or 5.")
            except ValueError:
                logger.error("Invalid input. Enter a number (1, 2, 3, 4 or 5).")
        
        if option == 2:
            self.print_bridge_question()
            self.print_delay_question()

        elif option == 3:
            self.print_delegate_question()
            self.print_delay_question()
            
        elif option == 4:
            self.print_swap_question()
            self.print_helios_question()
            self.print_weth_question()
            self.print_wbnb_question()
            self.print_delay_question()
            
        elif option == 5:
            self.print_bridge_question()
            self.print_delegate_question()
            self.print_swap_question()
            self.print_helios_question()
            self.print_weth_question()
            self.print_wbnb_question()
            self.print_delay_question()

        while True:
            try:
                print(f"{Colors.WHITE}{Colors.BOLD}1. Run With Private Proxy{Colors.RESET}")
                print(f"{Colors.WHITE}{Colors.BOLD}2. Run Without Proxy{Colors.RESET}")
                choose = int(input(f"{Colors.WHITE}{Colors.BOLD}Choose [1/2]:{Colors.RESET} ").strip())

                if choose in [1, 2]:
                    proxy_type = (
                        "With Private" if choose == 1 else 
                        "Without"
                    )
                    logger.success(f"Run {proxy_type} Proxy Selected.")
                    break
                else:
                    logger.error("Please enter either 1 or 2.")
            except ValueError:
                logger.error("Invalid input. Enter a number (1 or 2).")

        rotate = False
        if choose == 1:
            while True:
                rotate = input(f"{Colors.BLUE}{Colors.BOLD}Rotate Invalid Proxy? [y/n]:{Colors.RESET} ").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    logger.error("Invalid input. Enter 'y' or 'n'.")

        return option, choose, rotate
    
    async def solve_cf_turnstile(self, retries=5):
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=60)) as session:

                    if self.CAPTCHA_KEY is None:
                        logger.warn("Turnstile Not Solved - 2Captcha Key Is None")
                        return None
                    
                    url = f"http://2captcha.com/in.php?key={self.CAPTCHA_KEY}&method=turnstile&sitekey={self.SITE_KEY}&pageurl={self.PAGE_URL}"
                    async with session.get(url=url) as response:
                        response.raise_for_status()
                        result = await response.text()

                        if 'OK|' not in result:
                            logger.warn(result)
                            await asyncio.sleep(5)
                            continue

                        request_id = result.split('|')[1]

                        logger.info(f"Req Id: {request_id}")

                        for _ in range(30):
                            res_url = f"http://2captcha.com/res.php?key={self.CAPTCHA_KEY}&action=get&id={request_id}"
                            async with session.get(url=res_url) as res_response:
                                res_response.raise_for_status()
                                res_result = await res_response.text()

                                if 'OK|' in res_result:
                                    turnstile_token = res_result.split('|')[1]
                                    return turnstile_token
                                elif res_result == "CAPCHA_NOT_READY":
                                    logger.warn("Captcha Not Ready")
                                    await asyncio.sleep(5)
                                    continue
                                else:
                                    break

            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Turnstile Not Solved - {str(e)}")
                return None
    
    async def check_connection(self, proxy_url=None):
        connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
        try:
            async with ClientSession(connector=connector, timeout=ClientTimeout(total=10)) as session:
                async with session.get(url="https://api.ipify.org?format=json", proxy=proxy, proxy_auth=proxy_auth) as response:
                    response.raise_for_status()
                    return True
        except (Exception, ClientResponseError) as e:
            logger.error(f"Connection Not 200 OK - {str(e)}")
            return None
        
    async def user_login(self, account: str, address: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/users/login"
        data = json.dumps(self.generate_payload(account, address))
        headers = {
            **self.HEADERS[address],
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Login request failed: {str(e)}")

        return None
    
    async def check_eligibility(self, address: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/faucet/check-eligibility"
        data = json.dumps({"token":"HLS", "chain":"helios-testnet"})
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"GET Eligibility Status Failed - {str(e)}")

        return None
    
    async def request_faucet(self, address: str, turnstile_token: str, use_proxy: bool, retries=5):
        url = f"{self.BASE_API}/faucet/request"
        data = json.dumps({"token":"HLS", "chain":"helios-testnet", "amount":1, "turnstileToken":turnstile_token})
        headers = {
            **self.HEADERS[address],
            "Authorization": f"Bearer {self.access_tokens[address]}",
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=url, headers=headers, data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Faucet Not Claimed - {str(e)}")

        return None
    
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
            logger.info(f"Proxy: {proxy}")

            is_valid = await self.check_connection(proxy)
            if not is_valid:
                if rotate_proxy:
                    proxy = self.rotate_proxy_for_account(address)
                    continue

                return False
            
            return True
    
    async def process_user_login(self, account: str, address: str, use_proxy: bool, rotate_proxy: bool):
        is_valid = await self.process_check_connection(address, use_proxy, rotate_proxy)
        if is_valid:
            login = await self.user_login(account, address, use_proxy)
            if login and login.get("success", False):
                self.access_tokens[address] = login["token"]

                logger.success("Login Success")
                return True

            logger.error("Login Failed")
            return False
        
    async def process_perform_bridge(self, account: str, address: str, dest_chain_id: int, use_proxy: bool):
        tx_hash = await self.perform_bridge(account, address, dest_chain_id, use_proxy)
        if tx_hash:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.success("Bridge Success")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error("Perform On-Chain Bridge Failed")

    async def process_perform_delegate(self, account: str, address: str, contract_address: str, use_proxy: bool):
        tx_hash = await self.perform_delegate(account, address, contract_address, use_proxy)
        if tx_hash:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.success("Delegate Success")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error("Perform On-Chain Delegate Failed")
    
    async def process_perform_swap(self, account: str, address: str, token_in: str, token_out: str, swap_amount: float, use_proxy: bool):
        tx_hash = await self.perform_swap(account, address, token_in, token_out, swap_amount, use_proxy)
        if tx_hash:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.success("Swap Success")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error("Perform On-Chain Swap Failed")

    async def process_option_1(self, address: str, use_proxy: bool):
        logger.step("Checking Faucet Eligibility...")
        check = await self.check_eligibility(address, use_proxy)
        if check and check.get("success", False):
            is_eligible = check.get("isEligible", False)

            if is_eligible:
                logger.loading("Solving Captcha Turnstile...")

                turnstile_token = await self.solve_cf_turnstile()
                if turnstile_token:
                    logger.info("Captcha Turnstile Solved Successfully")

                    request = await self.request_faucet(address, turnstile_token, use_proxy)
                    if request and request.get("success", False):
                        logger.success("1 HLS Faucet Claimed Successfully")
                    else:
                        logger.error("Faucet Claim Failed.")

            else:
                logger.warn("Not Eligible to Claim Faucet")
        else:
            logger.error("Failed to check faucet eligibility.")

    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        logger.step("Starting HLS Bridge...")

        for i in range(self.bridge_count):
            logger.info(f"Bridge transaction {i+1} of {self.bridge_count}")

            balance = await self.get_token_balance(address, self.HELIOS_CONTRACT_ADDRESS, use_proxy)

            destination = random.choice(self.DEST_TOKENS)
            ticker = destination["Ticker"]
            dest_chain_id = destination["ChainId"]
            estimated_fee = 0.5

            logger.action(f"Bridging Helios to {ticker}")
            logger.info(f"Balance: {balance} HLS")
            logger.info(f"Amount: {self.bridge_amount} HLS")
            logger.info(f"Estimated Fee: {estimated_fee} HLS")

            required = self.bridge_amount + estimated_fee

            if not balance or balance <= required:
                logger.warn("Insufficient HLS Token Balance for Bridge")
                return
            
            await self.process_perform_bridge(account, address, dest_chain_id, use_proxy)
            await self.print_timer()

    async def process_option_3(self, account: str, address: str, use_proxy: bool):
        logger.step("Starting HLS Delegate...")

        for i in range(self.delegate_count):
            logger.info(f"Delegate transaction {i+1} of {self.delegate_count}")

            validators = random.choice(self.VALIDATATORS)
            moniker = validators["Moniker"]
            contract_address = validators["Contract Address"]

            balance = await self.get_token_balance(address, self.HELIOS_CONTRACT_ADDRESS, use_proxy)

            logger.info(f"Balance: {balance} HLS")
            logger.info(f"Amount: {self.delegate_amount} HLS")
            logger.info(f"Validator: {moniker}")

            if not balance or balance <= self.delegate_amount:
                logger.warn("Insufficient HLS Token Balance for Delegate")
                return
            
            await self.process_perform_delegate(account, address, contract_address, use_proxy)
            await self.print_timer()
    
    async def process_option_4(self, account: str, address: str, use_proxy: bool):
        logger.step("Starting Token Swap...")

        for i in range(self.swap_count):
            logger.info(f"Swap transaction {i+1} of {self.swap_count}")

            swap_option, ticker, token_in, token_out, swap_amount = self.generate_swap_option()

            balance = await self.get_token_balance(address, token_in, use_proxy)

            logger.action(f"Swapping {swap_option}")
            logger.info(f"Balance: {balance} {ticker}")
            logger.info(f"Amount: {swap_amount} {ticker}")

            if not balance or balance <= swap_amount:
                logger.warn(f"Insufficient {ticker} Token Balance for Swap")
                continue
            
            await self.process_perform_swap(account, address, token_in, token_out, swap_amount, use_proxy)
            await self.print_timer()

    async def process_accounts(self, account: str, address: str, option: int, use_proxy_choice: bool, rotate_proxy: bool):
        logger.step(f"Processing Account: {self.mask_account(address)}")
        logined = await self.process_user_login(account, address, use_proxy_choice, rotate_proxy)
        if logined:
            web3 = await self.get_web3_with_check(address, use_proxy_choice)
            if not web3:
                logger.error("Web3 Not Connected")
                return
            
            self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")

            if option == 1:
                await self.process_option_1(address, use_proxy_choice)

            elif option == 2:
                await self.process_option_2(account, address, use_proxy_choice)

            elif option == 3:
                await self.process_option_3(account, address, use_proxy_choice)
            
            elif option == 4:
                await self.process_option_4(account, address, use_proxy_choice)

            else:
                await self.process_option_1(address, use_proxy_choice)
                await asyncio.sleep(5)

                await self.process_option_2(account, address, use_proxy_choice)
                await asyncio.sleep(5)
                
                await self.process_option_3(account, address, use_proxy_choice)
                await asyncio.sleep(5)
                
                await self.process_option_4(account, address, use_proxy_choice)
                await asyncio.sleep(5)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            capctha_key = self.load_2captcha_key()
            if capctha_key:
                self.CAPTCHA_KEY = capctha_key

            await display_welcome_screen()
            option, use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = False
            if use_proxy_choice == 1:
                use_proxy = True

            while True:
                self.clear_terminal()
                await display_welcome_screen()
                
                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                for account in accounts:
                    if account:
                        address = self.generate_address(account)

                        if not address:
                            logger.error("Invalid Private Key or Library Version Not Supported")
                            continue

                        self.HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://testnet.helioschain.network",
                            "Referer": "https://testnet.helioschain.network/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": FakeUserAgent().random
                        }

                        await self.process_accounts(account, address, option, use_proxy_choice, rotate_proxy)
                        await asyncio.sleep(3)

                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    timestamp = datetime.now().astimezone(pytz.timezone('Asia/Jakarta')).strftime("%H:%M:%S")
                    print(
                        f"{Colors.BRIGHT_BLACK}[{timestamp}]{Colors.RESET}"
                        f"{Colors.CYAN}{Colors.BOLD} | All Tasks Completed. Wait for {formatted_time} ... {Colors.RESET}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            logger.error("File 'accounts.txt' Not Found.")
            return
        except Exception as e:
            logger.error(f"Error: {e}")
            raise e

if __name__ == "__main__":
    try:
        bot = Helios()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        logger.info("[ EXIT ] Helios - BOT")
