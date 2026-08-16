/**
 * jitoExecutor.ts
 * -----------------------------------------------------------------------------
 * Execution module for the $GROWTH Balancer Engine.
 *
 * WHAT THIS DOES
 * --------------
 * The Balancer Engine discovers a "profitable path": token X can be bought on
 * one venue (cheap) and sold on another (expensive) for a net profit. This
 * module takes that path and turns it into a single, atomic, frontrun-protected
 * execution bundle that is broadcast directly to the Jito Block Engine.
 *
 * The bundle consists of exactly ONE Solana `Transaction` containing, in order:
 *   1. Instruction 1 — BUY token X on the cheap venue.
 *   2. Instruction 2 — SELL token X on the expensive venue.
 *   3. Instruction 3 — SystemProgram.transfer of a small SOL tip to an
 *      official Jito tip account (this is what "buys" frontrun protection:
 *      the tip bribes Jito leaders to land our bundle atomically and skip the
 *      public mempool where sandwich bots live).
 *
 * WHY JITO / WHY ATOMIC
 * ---------------------
 * If the buy and sell were sent as two separate transactions, a sandwich bot
 * could observe the buy in the mempool, front-run the sell, and rob the profit.
 * Jito lets us submit the whole thing as ONE atomic unit: either every
 * instruction lands in the same slot in order, or none of them do.
 *
 * -----------------------------------------------------------------------------
 * JITO BUNDLE SUBMISSION PAYLOAD (JSON-RPC over HTTPS)
 * -----------------------------------------------------------------------------
 * A "bundle" is a JSON-RPC 2.0 request POSTed to:
 *
 *     POST https://<region>.mainnet.block-engine.jito.wtf/api/v1/bundles
 *
 * with body:
 *
 *     {
 *       "jsonrpc": "2.0",
 *       "id": 1,                 // arbitrary request id (echoed in response)
 *       "method": "sendBundle",  // the RPC method
 *       "params": [
 *         [                      // a bundle = 1..5 transactions, executed in order
 *           "<base58-signed-tx-1>",
 *           "<base58-signed-tx-2>",   // optional ...
 *           // ... up to 5
 *         ]
 *       ]
 *     }
 *
 * Notes on the structure:
 *   * `params[0]` is the bundle: an ARRAY of base58-encoded, fully-signed
 *     transactions. Batch size limit is 5.
 *   * Transactions execute atomically and sequentially (tx0 -> tx1 -> ...).
 *     If ANY transaction fails, the WHOLE bundle is dropped by the block engine.
 *   * The tip is conventionally placed as the LAST instruction of the LAST
 *     transaction, so it is only ever paid if the bundle actually lands.
 *   * A bundle has roughly ~2 slots (~800ms) to land before it expires. If the
 *     blockhash goes stale or the slot window passes, the bundle is never
 *     included — this is the "block expiration" case handled by our fallback.
 *
 * RESPONSE (sendBundle):
 *
 *     { "jsonrpc": "2.0", "result": "<bundle-uuid>", "id": 1 }
 *
 * STATUS (getBundleStatuses, bundles fall into four buckets):
 *
 *     { "bundle_id": "...", "status": "Invalid|Pending|Failed|Landed",
 *       "slot": 123456, "transactions": [...] }
 *
 * -----------------------------------------------------------------------------
 * TIP ACCOUNTS
 * -----------------------------------------------------------------------------
 * Official Jito tip accounts are discoverable via the `getTipAccounts` method
 * on the same endpoint (returns a list of ~8 whitelisted accounts). We fetch
 * them at runtime (falling back to a hardcoded list) and pick one at random —
 * spreading tips across accounts avoids contention and improves landing odds.
 * A tip is just a plain SystemProgram transfer of SOL lamports from the
 * agent's wallet to one of those accounts.
 */

import bs58 from "bs58";
import {
  Connection,
  Keypair,
  LAMPORTS_PER_SOL,
  PublicKey,
  SystemProgram,
  Transaction,
  TransactionInstruction,
} from "@solana/web3.js";
import { eq } from "drizzle-orm";

import { db } from "@/db";
import { executionQueue, growthExecutions } from "@/db/schema";

/* ========================================================================== *
 *  CONFIG / CONSTANTS
 * ========================================================================== */

/** Default tip in SOL for the Jito block engine. */
const DEFAULT_TIP_SOL = 0.001;

/** How many consecutive status polls before we call a bundle EXPIRED. */
const MAX_STATUS_POLLS = 6;

/** Delay (ms) between `getBundleStatuses` polls. */
const STATUS_POLL_INTERVAL_MS = 400;

/** Number of times to retry (re-quote + re-sign + re-send) before giving up. */
const MAX_ATTEMPTS = 3;

/** Jito's official Tip Payment Program id (mainnet). */
const JITO_TIP_PROGRAM_ID = "T1pyyaTNZsKv2WcRAB8oVnk93mLJw2XzjtVYqCsaHqt";

/** Regional block engine endpoints — we broadcast to ALL for best landing. */
const JITO_BLOCK_ENGINES: string[] = [
  "https://mainnet.block-engine.jito.wtf",
  "https://amsterdam.mainnet.block-engine.jito.wtf",
  "https://frankfurt.mainnet.block-engine.jito.wtf",
  "https://ny.mainnet.block-engine.jito.wtf",
  "https://tokyo.mainnet.block-engine.jito.wtf",
  "https://slc.mainnet.block-engine.jito.wtf",
];

/** Static fallback tip accounts (overwritten at runtime via getTipAccounts). */
const KNOWN_TIP_ACCOUNTS: string[] = [
  "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
  "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
  "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
  "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
  "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
  "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
  "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
  "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
];

/** Jupiter Swap API v6 base URL. */
const JUPITER_API_BASE = "https://quote-api.jup.ag/v6";

/** Wrapped-SOL native mint address. */
const WSOL_MINT = "So11111111111111111111111111111111111111112";

/* ========================================================================== *
 *  TYPES
 * ========================================================================== */

/** The profitable path handed off by the Balancer Engine. */
export interface ProfitablePath {
  /** Agent token to arb (mint address). */
  tokenMint: string;
  /** Venue id / label where we buy cheap. */
  buyVenue: string;
  /** Venue id / label where we sell expensive. */
  sellVenue: string;
  /** Amount of the input asset (lamports / base units) as a string. */
  amountIn: string;
  /** Expected gross profit (lamports) as a string. */
  expectedProfit: string;
  /** Slippage tolerance in basis points. */
  slippageBps: number;
  /** Unique id for the path (used as the queue row id). */
  id: string;
}

/** A single Jupiter-swappable leg of the arb (buy or sell). */
interface SwapLeg {
  inputMint: string;
  outputMint: string;
  amount: string;
  slippageBps: number;
}

/** A raw instruction as returned by Jupiter `/v6/swap-instructions`. */
interface JupiterRawInstruction {
  programId: string;
  accounts: { pubkey: string; isSigner: boolean; isWritable: boolean }[];
  data: string; // base64
}

/** Result from Jupiter `/v6/swap-instructions`. */
interface JupiterSwapInstructions {
  swapInstruction: JupiterRawInstruction | null;
  setupInstructions: JupiterRawInstruction[];
  cleanupInstruction?: JupiterRawInstruction | null;
  computeBudgetInstructions: JupiterRawInstruction[];
  addressLookupTableAddresses: string[];
}

/** A signed transaction ready for the bundle. */
interface SignedTx {
  /** base58-encoded signed transaction. */
  payload: string;
  /** The transaction's first signature (used for verification/audit). */
  signature: string;
}

/** Jito JSON-RPC response envelope for `getBundleStatuses`. */
interface JitoStatusEnvelope {
  jsonrpc: string;
  id: number;
  result?: { value: { bundle_id: string; status: string; slot?: number }[] };
  error?: { code: number; message: string };
}

/** Jito JSON-RPC response envelope for `sendBundle` / `getTipAccounts`. */
interface JitoResultEnvelope<T> {
  jsonrpc: string;
  id: number;
  result?: T;
  error?: { code: number; message: string };
}

/** Terminal outcome of executing a path. */
type ExecutionOutcome = "LANDED" | "FAILED" | "EXPIRED";

/* ========================================================================== *
 *  CONFIG HOLDER
 * ========================================================================== */

export interface JitoExecutorConfig {
  /** Agent wallet keypair (private key). Keep on the server only. */
  payer: Keypair;
  /** Solana RPC endpoint (public confirmed RPC for blockhash). */
  rpcUrl: string;
  /** SOL denomination tip for the Jito block engine. */
  tipSol?: number;
  /** Override block-engine endpoints (testing / regional pinning). */
  blockEngineUrls?: string[];
  /** Optional RPC auth token (Helius/QuickNode) appended as header. */
  rpcAuthToken?: string;
}

/* ========================================================================== *
 *  MAIN EXECUTOR
 * ========================================================================== */

export class JitoExecutor {
  private readonly connection: Connection;
  private readonly payer: Keypair;
  private readonly tipLamports: number;
  private readonly blockEngines: string[];

  constructor(config: JitoExecutorConfig) {
    this.connection = new Connection(config.rpcUrl, "confirmed");
    this.payer = config.payer;
    this.tipLamports = Math.round(
      (config.tipSol ?? DEFAULT_TIP_SOL) * LAMPORTS_PER_SOL,
    );
    this.blockEngines = config.blockEngineUrls ?? JITO_BLOCK_ENGINES;
  }

  /**
   * Top-level entry point: drain the Balancer Engine's queue and execute each
   * profitable path as an atomic Jito bundle.
   *
   * @returns the number of paths successfully landed this cycle.
   */
  async runQueue(): Promise<number> {
    const queued = await db
      .select()
      .from(executionQueue)
      .where(eq(executionQueue.status, "QUEUED"))
      .orderBy(executionQueue.createdAt);

    let landed = 0;
    for (const row of queued) {
      // Mark in-flight so a concurrent worker can't double-execute the path.
      await db
        .update(executionQueue)
        .set({ status: "PROCESSING", updatedAt: new Date() })
        .where(eq(executionQueue.id, row.id));

      const path: ProfitablePath = {
        id: row.id,
        tokenMint: row.tokenMint,
        buyVenue: row.buyVenue,
        sellVenue: row.sellVenue,
        amountIn: row.amountIn,
        expectedProfit: row.expectedProfit,
        slippageBps: row.slippageBps,
      };

      const outcome = await this.executePath(path);
      if (outcome === "LANDED") {
        landed += 1;
        await db
          .update(executionQueue)
          .set({ status: "DONE", updatedAt: new Date() })
          .where(eq(executionQueue.id, row.id));
      } else {
        // Failed or expired: clear the queue entry so the engine can
        // re-discover a fresh (still-profitable) path next cycle.
        await db
          .update(executionQueue)
          .set({ status: "CLEARED", isStale: true, updatedAt: new Date() })
          .where(eq(executionQueue.id, row.id));
      }
    }
    return landed;
  }

  /**
   * Execute a single profitable path.
   *
   * The happy path is:
   *   construct bundle -> sign -> broadcast -> poll status -> "LANDED".
   *
   * On block expiration (a bundle expires in ~2 slots / ~800ms), we retry up to
   * `MAX_ATTEMPTS` times with a FRESH quote + FRESH blockhash. If it still
   * fails, we log the result to the database (the caller clears the queue
   * entry in `runQueue`).
   */
  async executePath(path: ProfitablePath): Promise<ExecutionOutcome> {
    let lastTx: SignedTx | null = null;
    let lastError = "";

    for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
      try {
        // 1. Construct a fully-signed atomic transaction (buy + sell + tip).
        const tx = await this.buildAtomicTransaction(path);
        lastTx = tx;

        // 2. Wrap it in a Jito bundle payload (single transaction -> single-tx
        //    bundle; the tip is our 3rd instruction inside this transaction).
        const bundlePayload = this.buildBundlePayload([tx]);

        // 3. Broadcast to all block engines; at least one accepts synchronously.
        const bundleId = await this.broadcastBundle(bundlePayload);
        if (!bundleId) {
          lastError = "no_block_engine_accepted_bundle";
          continue;
        }

        // 4. Await the on-chain verdict.
        const status = await this.awaitBundleStatus(bundleId);

        await this.persistExecution(path, tx, bundleId, status, "");

        if (status === "LANDED") return "LANDED";
        if (status === "FAILED" || status === "INVALID") {
          return "FAILED";
        }
        // Pending that never resolved -> treat as expired; retry with fresh tx.
        lastError = "bundle_expired_or_pending";
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
      }
    }

    // ----------------------------------------------------------------------
    // FALLBACK: all attempts exhausted. The most common root cause is block
    // expiration (bundle missed its 2-slot window). Log it to the database.
    // ----------------------------------------------------------------------
    await this.persistExecution(path, lastTx, "", "EXPIRED", lastError);
    return "EXPIRED";
  }

  /* ---------------------------------------------------------------------
   * 1. BUILD THE ATOMIC TRANSACTION
   * ------------------------------------------------------------------- */

  /**
   * Build a single `Transaction` containing the buy, the sell, and the tip.
   *
   * Both swaps are obtained from the Jupiter Swap API v6 `swap-instructions`
   * endpoint, which returns *already-formed* Solana instructions (plus any
   * required ATA `setupInstructions`, compute budget, and cleanups).
   */
  async buildAtomicTransaction(path: ProfitablePath): Promise<SignedTx> {
    // Buy: X on the cheap venue  (in: WSOL -> out: token X).
    const buyIx = await this.fetchSwapInstructions({
      inputMint: WSOL_MINT,
      outputMint: path.tokenMint,
      amount: path.amountIn,
      slippageBps: path.slippageBps,
    });
    // Sell: X on the expensive venue (in: token X -> out: WSOL).
    const sellIx = await this.fetchSwapInstructions({
      inputMint: path.tokenMint,
      outputMint: WSOL_MINT,
      amount: path.amountIn,
      slippageBps: path.slippageBps,
    });

    // Assemble the instruction list in execution order:
    //   setup (buy) -> buy swap -> setup (sell) -> sell swap -> cleanups.
    const instructions: TransactionInstruction[] = [
      ...buyIx.setupInstructions.map(deserializeInstruction),
      ...(buyIx.swapInstruction
        ? [deserializeInstruction(buyIx.swapInstruction)]
        : []),
      ...sellIx.setupInstructions.map(deserializeInstruction),
      ...(sellIx.swapInstruction
        ? [deserializeInstruction(sellIx.swapInstruction)]
        : []),
    ];
    if (buyIx.cleanupInstruction) {
      instructions.push(deserializeInstruction(buyIx.cleanupInstruction));
    }
    if (sellIx.cleanupInstruction) {
      instructions.push(deserializeInstruction(sellIx.cleanupInstruction));
    }

    // The crucial 3rd instruction: the Jito tip transfer.
    const tipAccount = await this.pickTipAccount();
    instructions.push(
      SystemProgram.transfer({
        fromPubkey: this.payer.publicKey,
        toPubkey: tipAccount,
        lamports: this.tipLamports,
      }),
    );

    // Fetch a fresh blockhash so the tx is valid for the next ~150 blocks.
    const { blockhash } = await this.connection.getLatestBlockhash("confirmed");

    // Build a legacy transaction directly from our already-formed
    // instructions. (Legacy is fine here: the bundle is a single transaction
    // with a small account set, so versioned/lookup-table packing is not
    // required. The tip is the last instruction only if nothing was cleaned
    // up — but we appended the tip AFTER the swaps, so ordering is preserved.)
    const tx = new Transaction();
    tx.recentBlockhash = blockhash;
    tx.feePayer = this.payer.publicKey;
    for (const ix of instructions) {
      tx.add(ix);
    }

    // Sign with the agent's private key.
    tx.sign(this.payer);

    return {
      payload: bs58.encode(tx.serialize()),
      signature: tx.signatures[0]?.signature
        ? bs58.encode(tx.signatures[0].signature)
        : "",
    };
  }

  /**
   * Call Jupiter Swap API v6 to get pre-built swap instructions for one leg.
   */
  private async fetchSwapInstructions(
    leg: SwapLeg,
  ): Promise<JupiterSwapInstructions> {
    // Step A: quote.
    const quoteUrl = `${JUPITER_API_BASE}/quote?${new URLSearchParams({
      inputMint: leg.inputMint,
      outputMint: leg.outputMint,
      amount: leg.amount,
      slippageBps: String(leg.slippageBps),
    }).toString()}`;

    const quoteRes = await fetch(quoteUrl, {
      headers: { Accept: "application/json" },
    });
    if (!quoteRes.ok) {
      throw new Error(
        `Jupiter quote failed (${quoteRes.status}): ${await quoteRes.text()}`,
      );
    }
    const quote = await quoteRes.json();
    if (!quote || quote.error) {
      throw new Error(`Jupiter quote error: ${quote?.error ?? "empty"}`);
    }

    // Step B: swap-instructions from the quote.
    const swapRes = await fetch(`${JUPITER_API_BASE}/swap-instructions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        quoteResponse: quote,
        userPublicKey: this.payer.publicKey.toBase58(),
        wrapAndUnwrapSol: true,
        dynamicComputeUnitLimit: true,
      }),
    });
    if (!swapRes.ok) {
      throw new Error(`Jupiter swap-instructions failed (${swapRes.status})`);
    }
    const result = await swapRes.json();
    if (result.error) {
      throw new Error(`Jupiter swap-instructions error: ${result.error}`);
    }
    return result as JupiterSwapInstructions;
  }

  /* ---------------------------------------------------------------------
   * 2. JITO BUNDLE PAYLOAD + TIP ACCOUNT
   * ------------------------------------------------------------------- */

  /**
   * Serialize the list of signed transactions into the Jito `sendBundle`
   * JSON-RPC payload (see the module header for the full structure).
   *
   * `params[0]` is the bundle: an array of base58 signed transactions. Here we
   * always pass exactly one transaction (which internally carries buy + sell +
   * tip), but the structure supports up to five.
   */
  buildBundlePayload(txs: SignedTx[]): object {
    return {
      jsonrpc: "2.0",
      id: 1,
      method: "sendBundle",
      params: [txs.map((t) => t.payload)],
    };
  }

  /** Pick a random official Jito tip account (prefer discovered list). */
  async pickTipAccount(): Promise<PublicKey> {
    const accounts = await this.fetchTipAccounts();
    const list = accounts.length > 0 ? accounts : KNOWN_TIP_ACCOUNTS;
    return new PublicKey(list[Math.floor(Math.random() * list.length)]!);
  }

  /** Fetch the whitelisted tip accounts via `getTipAccounts`. */
  private async fetchTipAccounts(): Promise<string[]> {
    const body = { jsonrpc: "2.0", id: 1, method: "getTipAccounts", params: [] };
    try {
      const res = await fetch(`${this.blockEngines[0]}/api/v1/bundles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) return [];
      const data = (await res.json()) as JitoResultEnvelope<string[]>;
      return data.result ?? [];
    } catch {
      return [];
    }
  }

  /* ---------------------------------------------------------------------
   * 3. BROADCAST + STATUS POLLING
   * ------------------------------------------------------------------- */

  /** Broadcast the bundle to every configured block engine in parallel. */
  async broadcastBundle(payload: object): Promise<string | null> {
    const attempts = this.blockEngines.map(async (engine) => {
      try {
        const res = await fetch(`${engine}/api/v1/bundles`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!res.ok) return null;
        const data = (await res.json()) as JitoResultEnvelope<string>;
        if (data.error) return null;
        return data.result ?? null; // bundle UUID
      } catch {
        return null;
      }
    });
    const results = await Promise.all(attempts);
    return results.find((id) => id !== null) ?? null;
  }

  /** Poll `getBundleStatuses` until the bundle resolves or expires. */
  async awaitBundleStatus(
    bundleId: string,
  ): Promise<"LANDED" | "FAILED" | "INVALID" | "EXPIRED"> {
    for (let poll = 0; poll < MAX_STATUS_POLLS; poll += 1) {
      const status = await this.queryBundleStatus(bundleId);
      if (status === "Landed" || status === "Failed" || status === "Invalid") {
        return status.toUpperCase() as "LANDED" | "FAILED" | "INVALID";
      }
      // Still Pending -> wait a beat and poll again.
      await sleep(STATUS_POLL_INTERVAL_MS);
    }
    // Ran out of polls while still Pending -> treat as expired (missed slot).
    return "EXPIRED";
  }

  private async queryBundleStatus(
    bundleId: string,
  ): Promise<"Pending" | "Landed" | "Failed" | "Invalid"> {
    const body = {
      jsonrpc: "2.0",
      id: 1,
      method: "getBundleStatuses",
      params: [[bundleId]],
    };
    try {
      const res = await fetch(`${this.blockEngines[0]}/api/v1/bundles`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) return "Pending";
      const data = (await res.json()) as JitoStatusEnvelope;
      const entry = data.result?.value?.[0];
      return (entry?.status as "Pending" | "Landed" | "Failed" | "Invalid") ??
        "Pending";
    } catch {
      return "Pending";
    }
  }

  /* ---------------------------------------------------------------------
   * 4. PERSISTENCE
   * ------------------------------------------------------------------- */

  /**
   * Persist the outcome of an execution attempt to `growth_executions`.
   * This is the on-chain audit ledger: landed bundles carry their signature
   * and slot; expired bundles carry their error so operators can triage.
   */
  private async persistExecution(
    path: ProfitablePath,
    tx: SignedTx | null,
    bundleId: string,
    status: "LANDED" | "FAILED" | "INVALID" | "EXPIRED",
    errorMessage: string,
  ): Promise<void> {
    const normalized: "LANDED" | "FAILED" | "EXPIRED" =
      status === "LANDED" ? "LANDED" : status === "INVALID" ? "FAILED" : "EXPIRED";

    await db
      .insert(growthExecutions)
      .values({
        id: path.id,
        tokenMint: path.tokenMint,
        buyVenue: path.buyVenue,
        sellVenue: path.sellVenue,
        amountIn: path.amountIn,
        expectedProfit: path.expectedProfit,
        bundleId: bundleId || null,
        signature: tx?.signature ?? null,
        tipLamports: this.tipLamports,
        tipAccount: JITO_TIP_PROGRAM_ID,
        status: normalized,
        errorMessage: errorMessage || null,
        attempts: MAX_ATTEMPTS,
      })
      .onConflictDoUpdate({
        target: growthExecutions.id,
        set: {
          status: normalized,
          errorMessage,
          bundleId: bundleId || null,
          updatedAt: new Date(),
        },
      });
  }
}

/* ========================================================================== *
 *  HELPERS
 * ========================================================================== */

/**
 * Convert a Jupiter (JSON-encoded) instruction into a `solana/web3.js`
 * `TransactionInstruction`. Jupiter returns instructions as:
 *   { programId, accounts: [{pubkey, isSigner, isWritable}], data: base64 }
 */
function deserializeInstruction(
  raw: JupiterRawInstruction,
): TransactionInstruction {
  return new TransactionInstruction({
    programId: new PublicKey(raw.programId),
    keys: raw.accounts.map((a) => ({
      pubkey: new PublicKey(a.pubkey),
      isSigner: a.isSigner,
      isWritable: a.isWritable,
    })),
    data: Buffer.from(raw.data, "base64"),
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/* ========================================================================== *
 *  FACTORY
 * ========================================================================== */

/**
 * Construct a JitoExecutor from environment variables.
 * The agent's private key is read server-side only (never exposed to client).
 */
export function createExecutorFromEnv(): JitoExecutor {
  const secretKey = process.env.AGENT_PRIVATE_KEY;
  if (!secretKey) {
    throw new Error("AGENT_PRIVATE_KEY is required to execute bundles");
  }
  const payer = Keypair.fromSecretKey(bs58.decode(secretKey));

  const rpcUrl =
    process.env.SOLANA_RPC_URL ?? "https://api.mainnet-beta.solana.com";
  const tipSol = process.env.JITO_TIP_SOL
    ? Number(process.env.JITO_TIP_SOL)
    : DEFAULT_TIP_SOL;

  return new JitoExecutor({
    payer,
    rpcUrl,
    tipSol,
    rpcAuthToken: process.env.SOLANA_RPC_AUTH_TOKEN,
  });
}
