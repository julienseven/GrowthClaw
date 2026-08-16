import { ArrowDownRight, ArrowUpRight, Fuel, Layers, ShieldCheck, Wallet } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { kpiStats, treasuryBalance, type KpiStat } from "@/lib/dashboard-data";
import { cn } from "@/lib/utils";

const iconFor = (key: string) => {
  switch (key) {
    case "volume":
      return <Layers className="h-4 w-4" />;
    case "liquidity":
      return <ShieldCheck className="h-4 w-4" />;
    case "tokens":
      return <Wallet className="h-4 w-4" />;
    default:
      return <Layers className="h-4 w-4" />;
  }
};

const treasuryIsLow = treasuryBalance.sol < treasuryBalance.threshold;

function StatCard({ stat }: { stat: KpiStat }) {
  return (
    <Card className="bg-card/70">
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            <span className="text-primary/80">{iconFor(stat.key)}</span>
            {stat.label}
          </span>
        </div>
        <div className="mt-3 flex items-end justify-between">
          <span className="text-2xl font-semibold tabular-nums tracking-tight">
            {stat.value}
          </span>
          {stat.delta && (
            <span
              className={cn(
                "flex items-center gap-0.5 text-xs font-medium",
                stat.delta.positive ? "text-emerald-400" : "text-red-400",
              )}
            >
              {stat.delta.positive ? (
                <ArrowUpRight className="h-3.5 w-3.5" />
              ) : (
                <ArrowDownRight className="h-3.5 w-3.5" />
              )}
              {stat.delta.value}
            </span>
          )}
        </div>
        <p className="mt-1 text-xs text-muted-foreground">{stat.subtext}</p>
      </CardContent>
    </Card>
  );
}

function TreasuryCard() {
  return (
    <Card
      className={cn(
        "bg-card/70",
        treasuryIsLow && "border-amber-500/40",
      )}
    >
      <CardContent className="p-5">
        <div className="flex items-center justify-between">
          <span className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            <Fuel className="h-4 w-4 text-amber-400" />
            Agent Treasury Gas
          </span>
          {treasuryIsLow ? (
            <Badge variant="warning" className="px-2 py-0.5">
              Low Balance
            </Badge>
          ) : (
            <Badge variant="success" className="px-2 py-0.5">
              Healthy
            </Badge>
          )}
        </div>
        <div className="mt-3 flex items-baseline gap-2">
          <span className="text-2xl font-semibold tabular-nums tracking-tight">
            {treasuryBalance.sol.toFixed(2)} SOL
          </span>
          <span className="text-xs text-muted-foreground">
            ≈ {treasuryBalance.usdApprox}
          </span>
        </div>
        <p className="mt-1 text-xs text-muted-foreground">
          {treasuryIsLow
            ? `Below ${treasuryBalance.threshold.toFixed(1)} SOL threshold — top up to keep guards running`
            : `${treasuryBalance.threshold.toFixed(1)} SOL reserve threshold`}
        </p>
      </CardContent>
    </Card>
  );
}

export function KpiCards() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {kpiStats.map((stat) => (
        <StatCard key={stat.key} stat={stat} />
      ))}
      <TreasuryCard />
    </div>
  );
}
