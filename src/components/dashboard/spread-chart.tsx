"use client";

import { useState } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Activity } from "lucide-react";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { spreadSeries } from "@/lib/dashboard-data";
import { cn } from "@/lib/utils";

const TOKEN_OPTIONS = ["GROWTH", "SRKT", "MTRX", "RAYR"] as const;
type Token = (typeof TOKEN_OPTIONS)[number];

// Deterministic per-token multiplier so each token renders a slightly
// different divergence profile in the demo. In production the series is
// fetched for the selected token from the backend.
const TOKEN_MULTIPLIER: Record<Token, number> = {
  GROWTH: 1.0,
  SRKT: 0.7,
  MTRX: 1.35,
  RAYR: 0.85,
};

const axisStroke = "rgba(148, 163, 184, 0.25)";
const tickStyle = { fill: "rgba(148, 163, 184, 0.7)", fontSize: 11 };

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-popover px-3 py-2 text-xs shadow-lg">
      <p className="mb-1 font-medium text-foreground">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center gap-2">
          <span
            className="h-2 w-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          <span className="text-muted-foreground">{entry.name}</span>
          <span className="ml-auto font-medium tabular-nums">
            {entry.value} bps
          </span>
        </div>
      ))}
    </div>
  );
}

export function SpreadChart() {
  const [selectedToken, setSelectedToken] = useState<Token>("GROWTH");

  const data = spreadSeries.map((p) => ({
    time: p.time,
    Raydium: Math.round(p.raydium * TOKEN_MULTIPLIER[selectedToken]),
    Meteora: Math.round(p.meteora * TOKEN_MULTIPLIER[selectedToken]),
  }));

  return (
    <Card className="col-span-1 lg:col-span-2">
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2 text-base">
            <Activity className="h-4 w-4 text-primary" />
            Price Spread Divergence
          </CardTitle>
          <CardDescription>
            Raydium vs Meteora spread over time · basis points
          </CardDescription>
        </div>

        <div className="flex flex-wrap gap-1.5">
          {TOKEN_OPTIONS.map((token) => (
            <button
              key={token}
              onClick={() => setSelectedToken(token)}
              className={cn(
                "rounded-md border px-2.5 py-1 text-xs font-medium transition-colors",
                selectedToken === token
                  ? "border-primary/40 bg-primary/10 text-primary"
                  : "border-transparent text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              {token}
            </button>
          ))}
        </div>
      </CardHeader>

      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={data} margin={{ top: 4, right: 4, bottom: 0, left: -14 }}>
              <defs>
                <linearGradient id="gradRaydium" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#22c55e" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="#22c55e" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="gradMeteora" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" stopOpacity={0.28} />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={axisStroke} vertical={false} />
              <XAxis
                dataKey="time"
                tick={tickStyle}
                axisLine={{ stroke: axisStroke }}
                tickLine={false}
              />
              <YAxis
                tick={tickStyle}
                axisLine={false}
                tickLine={false}
                width={44}
                unit=" bps"
              />
              <Tooltip content={<ChartTooltip />} cursor={{ stroke: axisStroke }} />
              <Area
                type="monotone"
                dataKey="Raydium"
                stroke="#22c55e"
                strokeWidth={2}
                fill="url(#gradRaydium)"
              />
              <Area
                type="monotone"
                dataKey="Meteora"
                stroke="#6366f1"
                strokeWidth={2}
                fill="url(#gradMeteora)"
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="mt-3 flex items-center gap-5 text-xs text-muted-foreground">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-green-500" />
            Raydium
          </span>
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-indigo-500" />
            Meteora
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
