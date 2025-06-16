// commands.js
import { generateWallets, signMessage } from "./services.js";
import { log, logDivider } from "./logger.js";

export async function runHeliosClaim() {
  logDivider();
  log("Starting Helios claim process...", "info");

  const wallets = generateWallets();
  for (const account of wallets) {
    try {
      log(`Signing message for ${account.address}`, "info");

      const signature = signMessage(account, "Login to Helios");
      log(`Signature: ${signature.signature}`, "success");

      // Simulasi: Kirim ke server (diisi sesuai endpoint asli)
      log(`Simulated sending to API with address: ${account.address}`, "info");

    } catch (e) {
      log(`Failed for ${account.address}: ${e.message}`, "error");
    }
    logDivider();
  }
}