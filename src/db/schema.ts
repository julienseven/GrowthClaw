import {
  bigint,
  boolean,
  index,
  integer,
  pgEnum,
  pgTable,
  text,
  timestamp,
} from "drizzle-orm/pg-core";

/**
 * Execution outcome status tracked by the Jito executor.
 *  - PENDING   -> bundle submitted, awaiting block-engine verdict.
 *  - LANDED    -> bundle included in a slot successfully.
 *  - FAILED    -> bundle rejected (e.g. failed simulation, bad txs).
 *  - EXPIRED   -> bundle missed its ~2-slot window and never landed.
 */
export const executionStatusEnum = pgEnum("execution_status", [
  "PENDING",
  "LANDED",
  "FAILED",
  "EXPIRED",
]);

/**
 * The on-chain execution ledger for the Balancer Engine's profitable paths.
 *
 * Every path that the Jito executor attempts is recorded here so that:
 *   * landed bundles are auditable (signature -> slot),
 *   * failed/expired bundles can be surfaced and retried (or discarded),
 *   * the execution queue can be cleared deterministically on expiry.
 */
export const growthExecutions = pgTable("growth_executions", {
  id: text("id").primaryKey(), // unique job id (uuid)

  // The token being traded (mint address).
  tokenMint: text("token_mint").notNull(),

  // Venue info — the "cheap" venue we bought on vs the "expensive" we sold on.
  buyVenue: text("buy_venue").notNull(),
  sellVenue: text("sell_venue").notNull(),

  // Trade sizing captured at execution time.
  amountIn: text("amount_in").notNull(), // raw integer string (lamports/base units)
  expectedProfit: text("expected_profit").notNull(), // raw integer string (lamports)

  // Bundle identifiers.
  bundleId: text("bundle_id"), // UUID returned by Jito block engine
  signature: text("signature"), // first transaction signature (for RPC lookup)

  // Tip metadata.
  tipLamports: bigint("tip_lamports", { mode: "number" }).notNull(),
  tipAccount: text("tip_account").notNull(),

  status: executionStatusEnum("status").notNull().default("PENDING"),

  // Outcome detail / serialized error message for debugging.
  errorMessage: text("error_message"),

  // Retry accounting.
  attempts: integer("attempts").notNull().default(0),

  slot: bigint("slot", { mode: "number" }),

  createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
  updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
});

export const executionQueueStatusEnum = pgEnum("execution_queue_status", [
  "QUEUED",
  "PROCESSING",
  "DONE",
  "EXPIRED",
  "CLEARED",
]);

/**
 * The Balancer Engine's execution queue: profitable paths waiting to be
 * packaged and broadcast by the Jito executor. The executor drains QUEUED
 * rows; on block-expiration of a bundle it marks the path CLEARED so the
 * engine can re-discover a fresh path on the next cycle.
 */
export const executionQueue = pgTable(
  "execution_queue",
  {
    id: text("id").primaryKey(), // unique path id (uuid)

    tokenMint: text("token_mint").notNull(),
    buyVenue: text("buy_venue").notNull(),
    sellVenue: text("sell_venue").notNull(),

    // Raw trade inputs, serialized as strings to avoid precision loss.
    amountIn: text("amount_in").notNull(),
    expectedProfit: text("expected_profit").notNull(),

    // Slippage tolerance in basis points (e.g. 50 = 0.5%).
    slippageBps: integer("slippage_bps").notNull().default(50),

    status: executionQueueStatusEnum("status").notNull().default("QUEUED"),

    // Marks a path whose previous bundle expired -> skip until re-discovered.
    isStale: boolean("is_stale").notNull().default(false),

    createdAt: timestamp("created_at", { withTimezone: true }).notNull().defaultNow(),
    updatedAt: timestamp("updated_at", { withTimezone: true }).notNull().defaultNow(),
  },
  (table) => ({
    statusIdx: index("execution_queue_status_idx").on(table.status),
  }),
);
