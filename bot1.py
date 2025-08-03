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
        self.deploy_count = 0
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
        
    def generate_raw_token(self):
        numbers = random.randint(0, 99999)
        token_name = f"Token{numbers}"
        token_symbol = f"T{numbers}"
        raw_supply = random.randint(1000, 1_000_000)
        total_supply = raw_supply * (10 ** 18)

        return token_name, token_symbol, raw_supply, total_supply
        
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
                logger.warn(f" [Attempt {attempt + 1}] Send TX Error: {str(e)}")
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
                logger.warn(f" [Attempt {attempt + 1}] Wait for Receipt Error: {str(e)}")
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
            logger.error(f"{str(e)}")
            return None
        
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
            self.used_nonce[address] += 1

            return tx_hash
        except Exception as e:
            logger.error(f"{str(e)}")
            return None
        
    async def perform_vote_proposal(self, account: str, address: str, proposal_id: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.PROPOSAL_ROUTER_ADDRESS), abi=self.HELIOS_CONTRACT_ABI)

            metadata = f"Vote on proposal {proposal_id}"

            vote_data = token_contract.functions.vote(address, proposal_id, 1, metadata)

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
            self.used_nonce[address] += 1

            return tx_hash
        except Exception as e:
            logger.error(f"{str(e)}")
            return None
        
    async def perform_deploy_contract(self, account: str, address: str, token_name: str, token_symbol: str, total_supply: int, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            source_code = f'''
            // SPDX-License-Identifier: MIT
            pragma solidity ^0.8.20;

            contract MyToken {{
                string public name = "{token_name}";
                string public symbol = "{token_symbol}";
                uint8 public decimals = 18;
                uint256 public totalSupply;

                mapping(address => uint256) public balanceOf;
                mapping(address => mapping(address => uint256)) public allowance;

                event Transfer(address indexed from, address indexed to, uint256 value);
                event Approval(address indexed owner, address indexed spender, uint256 value);

                constructor() {{
                    totalSupply = {total_supply};
                    balanceOf[msg.sender] = totalSupply;
                    emit Transfer(address(0), msg.sender, totalSupply);
                }}

                function transfer(address to, uint256 value) public returns (bool) {{
                    require(balanceOf[msg.sender] >= value, "Insufficient balance");
                    balanceOf[msg.sender] -= value;
                    balanceOf[to] += value;
                    emit Transfer(msg.sender, to, value);
                    return true;
                }}

                function approve(address spender, uint256 value) public returns (bool) {{
                    allowance[msg.sender][spender] = value;
                    emit Approval(msg.sender, spender, value);
                    return true;
                }}

                function transferFrom(address from, address to, uint256 value) public returns (bool) {{
                    require(balanceOf[from] >= value, "Insufficient balance");
                    require(allowance[from][msg.sender] >= value, "Allowance exceeded");
                    balanceOf[from] -= value;
                    balanceOf[to] += value;
                    allowance[from][msg.sender] -= value;
                    emit Transfer(from, to, value);
                    return true;
                }}
            }}
            '''

            compiled_sol = compile_source(source_code, output_values=["abi", "bin"])
            contract_id, contract_interface = compiled_sol.popitem()
            abi = contract_interface['abi']
            bytecode = contract_interface['bin']
            TokenContract = web3.eth.contract(abi=abi, bytecode=bytecode)

            max_priority_fee = web3.to_wei(1.111, "gwei")
            max_fee = max_priority_fee

            tx = TokenContract.constructor().build_transaction({
                "from": address,
                "gas": 3000000,
                "maxFeePerGas": max_fee,
                "maxPriorityFeePerGas": max_priority_fee,
                "nonce": self.used_nonce[address],
                "chainId": web3.eth.chain_id
            })

            tx_hash = await self.send_raw_transaction_with_retries(account, web3, tx)
            receipt = await self.wait_for_receipt_with_retries(web3, tx_hash)
            contract_address = receipt.contractAddress
            self.used_nonce[address] += 1

            return tx_hash, contract_address

        except Exception as e:
            logger.error(f"{str(e)}")
            return None, None
        
    def print_deploy_question(self):
        while True:
            try:
                deploy_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}Deploy Contract Count For Each Wallet -> {Style.RESET_ALL}").strip())
                if deploy_count > 0:
                    self.deploy_count = deploy_count
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Deploy Contract Count must be > 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

    def print_delay_question(self):
        while True:
            try:
                min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if min_delay >= 0:
                    self.min_delay = min_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay For Each Tx -> {Style.RESET_ALL}").strip())
                if max_delay >= min_delay:
                    self.max_delay = max_delay
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Max Delay must be >= Min Delay.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")
         
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%H:%M:%S')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.YELLOW + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.GREEN + Style.BRIGHT}1. Claim Delegate Rewards{Style.RESET_ALL}")
                print(f"{Fore.GREEN + Style.BRIGHT}2. Vote Governance Proposal{Style.RESET_ALL}")
                print(f"{Fore.GREEN + Style.BRIGHT}3. Deploy Token Contract{Style.RESET_ALL}")
                print(f"{Fore.GREEN + Style.BRIGHT}4. Run All Features{Style.RESET_ALL}")
                option = int(input(f"{Fore.WHITE + Style.BRIGHT}Choose [1/2/3/4] -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4]:
                    option_type = (
                        "Claim Delegate Rewards" if option == 1 else 
                        "Vote Governance Proposal" if option == 2 else 
                        "Deploy Token Contract" if option == 3 else 
                        "Run All Features"
                    )
                    print(f"{Fore.YELLOW + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, or 4.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, or 4).{Style.RESET_ALL}")
            
        if option == 3:
            self.print_deploy_question()
            self.print_delay_question()
            
        elif option == 4:
            self.print_deploy_question()
            self.print_delay_question()

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.WHITE + Style.BRIGHT}Choose [1/2] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2]:
                    proxy_type = (
                        "With Private" if choose == 1 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1 or 2.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1 or 2).{Style.RESET_ALL}")

        rotate = False
        if choose == 1:
            while True:
                rotate = input(f"{Fore.BLUE + Style.BRIGHT}Rotate Invalid Proxy? [y/n] -> {Style.RESET_ALL}").strip()

                if rotate in ["y", "n"]:
                    rotate = rotate == "y"
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter 'y' or 'n'.{Style.RESET_ALL}")

        return option, choose, rotate
    
    async def solve_cf_turnstile(self, retries=5):
        for attempt in range(retries):
            try:
                async with ClientSession(timeout=ClientTimeout(total=60)) as session:

                    if self.CAPTCHA_KEY is None:
                        logger.error(f"Turnstile Not Solved - 2Captcha Key Is None")
                        return None
                    
                    url = f"http://2captcha.com/in.php?key={self.CAPTCHA_KEY}&method=turnstile&sitekey={self.SITE_KEY}&pageurl={self.PAGE_URL}"
                    async with session.get(url=url) as response:
                        response.raise_for_status()
                        result = await response.text()

                        if 'OK|' not in result:
                            logger.warn(f"Message: {result}")
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
                                    logger.warn(f"Message: Captcha Not Ready")
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
            **self.BASE_HEADERS[address],
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
                logger.error(f"{str(e)}")

        return None
    
    async def proposal_lists(self, address: str, use_proxy: bool, retries=5):
        data = json.dumps({
            "jsonrpc":"2.0",
            "method":"eth_getProposalsByPageAndSize",
            "params":["0x1","0x14"],
            "id":1
        })
        for attempt in range(retries):
            proxy_url = self.get_next_proxy_for_account(address) if use_proxy else None
            connector, proxy, proxy_auth = self.build_proxy_config(proxy_url)
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=self.RPC_URL, headers=self.PORTAL_HEADERS[address], data=data, proxy=proxy, proxy_auth=proxy_auth) as response:
                        response.raise_for_status()
                        return await response.json()
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                logger.error(f"Fetch Proposal Lists Failed - {str(e)}")

        return None
        
    async def process_perform_claim_rewards(self, account: str, address: str, use_proxy: bool):
        tx_hash = await self.perform_claim_rewards(account, address, use_proxy)
        if tx_hash:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.actionSuccess(f"Success")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error(f"Perform On-Chain Failed")


    async def process_perform_vote_proposal(self, account: str, address: str, proposal_id: int, use_proxy: bool):
        tx_hash = await self.perform_vote_proposal(account, address, proposal_id, use_proxy)
        if tx_hash:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.actionSuccess(f"Success")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error(f"Perform On-Chain Failed")

    async def process_perform_deploy_contract(self, account: str, address: str, token_name: str, token_symbol: str, total_supply: int, use_proxy: bool):
        tx_hash, contract_address = await self.perform_deploy_contract(account, address, token_name, token_symbol, total_supply, use_proxy)
        if tx_hash and contract_address:
            explorer = f"https://explorer.helioschainlabs.org/tx/{tx_hash}"
            logger.actionSuccess(f"Success")
            logger.action(f"Contract: {contract_address}")
            logger.action(f"Tx Hash: {tx_hash}")
            logger.actionSuccess(f"Explorer: {explorer}")
        else:
            logger.error(f"Perform On-Chain Failed")

    async def process_fetch_proposal(self, address: str, use_proxy: bool):
        propsal_lists = await self.proposal_lists(address, use_proxy)
        if not propsal_lists: return False

        proposals = propsal_lists.get("result", [])
        
        live_proposals = [
            p for p in proposals
            if p.get("status") == "VOTING_PERIOD"
        ]

        if not live_proposals: 
            logger.warn("No Available Proposals")
            return False

        used_proposals = random.choice(live_proposals)

        return used_proposals
        
    async def process_check_connection(self, address: str, use_proxy: bool, rotate_proxy: bool):
        while True:
            proxy = self.get_next_proxy_for_account(address) if use_proxy else None
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
                logger.success(f"Login Success")
                return True
            logger.error(f"Login Failed")
            return False
        
    async def process_option_1(self, account: str, address: str, use_proxy: bool):
        logger.step(f"Claiming Rewards")
        await self.process_perform_claim_rewards(account, address, use_proxy)
        await self.print_timer()

    async def process_option_2(self, account: str, address: str, use_proxy: bool):
        logger.step(f"Voting on Proposal")
        proposals = await self.process_fetch_proposal(address, use_proxy)
        if not proposals: return
        proposal_id = proposals["id"]
        title = proposals["title"]
        proposer = proposals["proposer"]
        logger.info(f"Prop. Id: {proposal_id}")
        logger.info(f"Title: {title}")
        logger.info(f"Proposer: {proposer}")
        await self.process_perform_vote_proposal(account, address, proposal_id, use_proxy)
        await self.print_timer()

    async def process_option_3(self, account: str, address: str, use_proxy: bool):
        logger.step(f"Deploying Contract")
        for i in range(self.deploy_count):
            logger.info(f"{i+1} of {self.deploy_count}")
            token_name, token_symbol, raw_supply, total_supply = self.generate_raw_token()
            logger.info(f"Name: {token_name}")
            logger.info(f"Symbol: {token_symbol}")
            logger.info(f"Decimals: 18")
            logger.info(f"Supply: {raw_supply}")
            await self.process_perform_deploy_contract(account, address, token_name, token_symbol, total_supply, use_proxy)
            await self.print_timer()

    async def process_accounts(self, account: str, address: str, option: int, use_proxy: bool, rotate_proxy: bool):
        logined = await self.process_user_login(account, address, use_proxy, rotate_proxy)
        if logined:
            web3 = await self.get_web3_with_check(address, use_proxy)
            if not web3:
                logger.error(f"Web3 Not Connected")
                return
            self.used_nonce[address] = web3.eth.get_transaction_count(address, "pending")
            if option == 1:
                await self.process_option_1(account, address, use_proxy)
            elif option == 2:
                await self.process_option_2(account, address, use_proxy)
            elif option == 3:
                await self.process_option_3(account, address, use_proxy)
            elif option == 4:
                await self.process_option_1(account, address, use_proxy)
                await asyncio.sleep(5)
                await self.process_option_2(account, address, use_proxy)
                await asyncio.sleep(5)
                await self.process_option_3(account, address, use_proxy)
                await asyncio.sleep(5)

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]

            capctha_key = self.load_2captcha_key()
            if capctha_key:
                self.CAPTCHA_KEY = capctha_key

            option, use_proxy_choice, rotate_proxy = self.print_question()

            use_proxy = True if use_proxy_choice == 1 else False

            while True:
                self.clear_terminal()
                self.welcome()
                logger.info(f"Account's Total: {len(accounts)}")

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                for account in accounts:
                    if account:
                        address = self.generate_address(account)
                        
                        logger.step(f"Processing Account: {self.mask_account(address)}")

                        if not address:
                            logger.error(f"Invalid Private Key or Library Version Not Supported")
                            continue

                        user_agent = FakeUserAgent().random

                        self.BASE_HEADERS[address] = {
                            "Accept": "application/json, text/plain, */*",
                            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
                            "Origin": "https://testnet.helioschain.network",
                            "Referer": "https://testnet.helioschain.network/",
                            "Sec-Fetch-Dest": "empty",
                            "Sec-Fetch-Mode": "cors",
                            "Sec-Fetch-Site": "same-site",
                            "User-Agent": user_agent
                        }

                        self.PORTAL_HEADERS[address] = {
                            "Content-Type": "application/json",
                            "Referer": "https://portal.helioschain.network/",
                            "User-Agent": user_agent
                        }

                        await self.process_accounts(account, address, option, use_proxy, rotate_proxy)
                        await asyncio.sleep(3)

                logger.info(f"All Accounts Have Been Processed.")
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT} ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All All Task Completeed.{Style.RESET_ALL}",
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

if __name__ == "__main__":
    try:
        bot = Helios()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().strftime('%H:%M:%S')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Helios - BOT{Style.RESET_ALL}                                       "                              
        )
