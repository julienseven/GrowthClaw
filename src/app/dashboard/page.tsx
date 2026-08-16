import { Bell, Rocket, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { KpiCards } from "@/components/dashboard/kpi-cards";
import { SpreadChart } from "@/components/dashboard/spread-chart";
import { TokenTable } from "@/components/dashboard/token-table";

export const metadata = {
  title: "Dashboard · $GROWTH",
  description: "Balancer engine analytics and token guard management.",
};

export default function DashboardPage() {
  return (
    <main className="min-h-screen">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Page header */}
        <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <Rocket className="h-5 w-5" />
            </span>
            <div>
              <h1 className="text-xl font-semibold tracking-tight">Growth Engine</h1>
              <p className="mt-0.5 text-sm text-muted-foreground">
                Autonomous liquidity balancing &amp; spread protection
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Badge variant="outline" className="gap-1.5 text-muted-foreground">
              <Sparkles className="h-3 w-3 text-primary" />
              Agent Online
            </Badge>
            <Button variant="outline" size="icon" aria-label="Notifications">
              <Bell className="h-4 w-4" />
            </Button>
          </div>
        </header>

        {/* KPI metric cards */}
        <section className="mt-6">
          <KpiCards />
        </section>

        {/* Chart + table layout */}
        <section className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-3">
          <SpreadChart />
          <div className="lg:col-span-1">
            <TokenTable />
          </div>
        </section>
      </div>
    </main>
  );
}
