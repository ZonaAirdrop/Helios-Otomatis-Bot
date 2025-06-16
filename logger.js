// logger.js
export function log(msg, type = "info") {
  const timestamp = new Date().toISOString();
  const icons = {
    info: "ℹ️",
    success: "✅",
    error: "❌",
    warn: "⚠️"
  };
  const icon = icons[type] || "";
  console.log(`[${timestamp}] ${icon} ${msg}`);
}

export function logDivider() {
  console.log("=".repeat(50));
}