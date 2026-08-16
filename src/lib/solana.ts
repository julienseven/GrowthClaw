/**
 * Solana Web3.js client wrapper for frontend.
 * Provides utilities for wallet connections and blockchain interactions.
 */

import { Connection, PublicKey } from "@solana/web3.js";

const SOLANA_RPC_URL =
  process.env.NEXT_PUBLIC_SOLANA_RPC_URL ||
  "https://api.mainnet-beta.solana.com";

/**
 * Get configured Solana RPC connection
 */
export function getSolanaConnection(): Connection {
  return new Connection(SOLANA_RPC_URL, "confirmed");
}

/**
 * Validate if string is valid Solana address
 */
export function isValidSolanaAddress(address: string): boolean {
  try {
    new PublicKey(address);
    return true;
  } catch {
    return false;
  }
}

/**
 * Get account balance in SOL
 */
export async function getAccountBalance(address: string): Promise<number> {
  const connection = getSolanaConnection();
  const publicKey = new PublicKey(address);
  const balance = await connection.getBalance(publicKey);
  return balance / 1e9; // Convert lamports to SOL
}
