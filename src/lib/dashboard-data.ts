// Typed mock data for the $GROWTH B2B dashboard. In production these would
// be hydrated from the backend API (FastAPI) via a server component or route
// handler. Kept here as a single, typed source of truth for the UI.

export interface KpiStat {
  key: string;
  label: string;
  value: string;
  subtext: string;
  delta?: { value: string; positive: boolean };
}

export interface SpreadPoint {
  time: string;
  raydium: number;
  meteora: number;
}

export interface ManagedToken {
  id: string;
  name: string;
  symbol: string;
  mintAddress: string;
  spreadBps: number;
  isActive: boolean;
  liquiditySavedSol: number;
}

export const kpiStats: KpiStat[] = [
  {
    key: "volume",
    label: "Total Volume Balanced",
    value: "$4.82M",
    subtext: "12,940 SOL routed",
    delta: { value: "+18.2%", positive: true },
  },
  {
    key: "liquidity",
    label: "Total Liquidity Saved",
    value: "$1.14M",
    subtext: "3,112 SOL retained",
    delta: { value: "+9.4%", positive: true },
  },
  {
    key: "tokens",
    label: "Active Guarded Tokens",
    value: "27",
    subtext: "9 venues covered",
  },
];

export const treasuryBalance = {
  sol: 3.42,
  threshold: 5.0,
  usdApprox: "$493.12",
};

// 24 x 5-minute buckets (2 hours) of price spread divergence (in bps) between
// Raydium and Meteora for the selected token.
export const spreadSeries: SpreadPoint[] = [
  { time: "00:00", raydium: 12, meteora: 9 },
  { time: "00:05", raydium: 14, meteora: 10 },
  { time: "00:10", raydium: 13, meteora: 11 },
  { time: "00:15", raydium: 18, meteora: 12 },
  { time: "00:20", raydium: 22, meteora: 13 },
  { time: "00:25", raydium: 19, meteora: 14 },
  { time: "00:30", raydium: 25, meteora: 15 },
  { time: "00:35", raydium: 31, meteora: 16 },
  { time: "00:40", raydium: 28, meteora: 18 },
  { time: "00:45", raydium: 35, meteora: 17 },
  { time: "00:50", raydium: 42, meteora: 19 },
  { time: "00:55", raydium: 38, meteora: 21 },
  { time: "01:00", raydium: 33, meteora: 20 },
  { time: "01:05", raydium: 29, meteora: 22 },
  { time: "01:10", raydium: 26, meteora: 19 },
  { time: "01:15", raydium: 24, meteora: 18 },
  { time: "01:20", raydium: 21, meteora: 17 },
  { time: "01:25", raydium: 17, meteora: 15 },
  { time: "01:30", raydium: 15, meteora: 14 },
  { time: "01:35", raydium: 19, meteora: 13 },
  { time: "01:40", raydium: 23, meteora: 15 },
  { time: "01:45", raydium: 27, meteora: 16 },
  { time: "01:50", raydium: 24, meteora: 14 },
  { time: "01:55", raydium: 20, meteora: 12 },
];

export const managedTokens: ManagedToken[] = [
  {
    id: "tok-1",
    name: "Growth Protocol",
    symbol: "GROWTH",
    mintAddress: "GrowT...x8K2pQ",
    spreadBps: 42,
    isActive: true,
    liquiditySavedSol: 184.2,
  },
  {
    id: "tok-2",
    name: "Solana Rocket",
    symbol: "SRKT",
    mintAddress: "SRkt2...9Jq7Wm",
    spreadBps: 18,
    isActive: true,
    liquiditySavedSol: 96.7,
  },
  {
    id: "tok-3",
    name: "Meteora Mint",
    symbol: "MTRX",
    mintAddress: "MtrXa...3LmN4p",
    spreadBps: 61,
    isActive: false,
    liquiditySavedSol: 41.9,
  },
  {
    id: "tok-4",
    name: "Raydium Reserve",
    symbol: "RAYR",
    mintAddress: "RayR1...6BvC2s",
    spreadBps: 27,
    isActive: true,
    liquiditySavedSol: 312.5,
  },
  {
    id: "tok-5",
    name: "Pulse Swap",
    symbol: "PLSE",
    mintAddress: "PlsE9...2ZkH8t",
    spreadBps: 9,
    isActive: true,
    liquiditySavedSol: 58.3,
  },
];

/** Human-readable, truncated contract address display helper. */
export function shortAddress(address: string): string {
  if (address.length <= 12) return address;
  return `${address.slice(0, 6)}…${address.slice(-4)}`;
}
