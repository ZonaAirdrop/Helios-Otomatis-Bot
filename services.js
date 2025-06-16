// services.js
import Web3 from "web3";
import fs from "fs";

// Load RPC from environment
const RPC_URL = process.env.RPC_URL || "https://rpc.sepolia.org";
export const web3 = new Web3(new Web3.providers.HttpProvider(RPC_URL));

// Load private keys from accounts.txt
export function loadPrivateKeys(file = "accounts.txt") {
  try {
    const lines = fs.readFileSync(file, "utf-8").split("\n").filter(Boolean);
    return lines.map((key) => key.trim());
  } catch (error) {
    console.error("❌ Failed to read accounts.txt:", error.message);
    return [];
  }
}

// Generate wallet instances
export function generateWallets() {
  const keys = loadPrivateKeys();
  return keys.map((key) => web3.eth.accounts.privateKeyToAccount(key));
}

// Get wallet address from private key
export function getAddressFromPrivateKey(privateKey) {
  try {
    return web3.eth.accounts.privateKeyToAccount(privateKey).address;
  } catch (e) {
    console.error("Invalid private key:", privateKey);
    return null;
  }
}

// Sign message
export function signMessage(account, message) {
  return account.sign(message);
}

// Sign typed transaction
export async function signAndSendTx(account, txData) {
  try {
    const signedTx = await account.signTransaction(txData);
    const receipt = await web3.eth.sendSignedTransaction(signedTx.rawTransaction);
    return receipt;
  } catch (e) {
    console.error("❌ Failed to sign/send transaction:", e.message);
    return null;
  }
}