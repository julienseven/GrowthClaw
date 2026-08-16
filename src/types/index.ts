/**
 * Global type definitions for $GROWTH frontend.
 */

export interface MarketData {
  tokenAddress: string;
  price: number;
  marketCap?: number;
  volume24h?: number;
  holdersCount?: number;
  liquidity?: number;
}

export interface StrategyRecommendation {
  strategyId: string;
  title: string;
  description: string;
  priority: "high" | "medium" | "low";
  confidenceScore: number;
  estimatedImpact?: string;
  actions: string[];
}

export interface TokenInfo {
  mintAddress: string;
  name: string;
  symbol: string;
  decimals: number;
  totalSupply?: number;
  currentHolders?: number;
}

export interface HealthStatus {
  status: string;
  environment: string;
  service: string;
}
