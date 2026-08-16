// Type-safe accessors for the $GROWTH frontend environment.
//
// Only `NEXT_PUBLIC_*` variables are available on the client. Anything
// secret (API keys, etc.) must live server-side and be reached through
// an API route proxy — never through a NEXT_PUBLIC_* variable.
//
// The `typedEnv` helper throws at startup when a required variable is
// missing, so misconfiguration surfaces immediately in dev instead of
// as an opaque runtime error deep in a component.

function required(name: string): string {
  const value = process.env[name];
  if (!value) {
    throw new Error(`Missing required environment variable: ${name}`);
  }
  return value;
}

function optional(name: string): string | undefined {
  const value = process.env[name];
  return value && value.length > 0 ? value : undefined;
}

export const typedEnv = {
  /** Origin of the FastAPI backend (e.g. http://localhost:8000). */
  apiUrl: required("NEXT_PUBLIC_API_URL"),

  /** Public Solana RPC endpoint consumed by @solana/web3.js in the browser. */
  solanaRpcUrl: required("NEXT_PUBLIC_SOLANA_RPC_URL"),

  /** Base58 mint addresses of the tokens being grown (comma separated). */
  targetTokens: (optional("NEXT_PUBLIC_TARGET_TOKENS") ?? "")
    .split(",")
    .map((t) => t.trim())
    .filter(Boolean),
} as const;

export type TypedEnv = typeof typedEnv;
