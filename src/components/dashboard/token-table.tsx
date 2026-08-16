"use client";

import { useState } from "react";
import { Coins, Plus, Search } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { managedTokens, shortAddress, type ManagedToken } from "@/lib/dashboard-data";
import { cn } from "@/lib/utils";

function spreadTone(bps: number): "success" | "warning" | "destructive" {
  if (bps < 20) return "success";
  if (bps < 40) return "warning";
  return "destructive";
}

export function TokenTable() {
  const [tokens, setTokens] = useState<ManagedToken[]>(managedTokens);
  const [query, setQuery] = useState("");

  const filtered = tokens.filter((t) => {
    const q = query.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) ||
      t.symbol.toLowerCase().includes(q) ||
      t.mintAddress.toLowerCase().includes(q)
    );
  });

  const toggleToken = (id: string) => {
    setTokens((prev) =>
      prev.map((t) => (t.id === id ? { ...t, isActive: !t.isActive } : t)),
    );
  };

  return (
    <Card>
      <CardHeader className="flex flex-row items-start justify-between gap-4">
        <div className="space-y-1">
          <CardTitle className="flex items-center gap-2 text-base">
            <Coins className="h-4 w-4 text-primary" />
            Guarded Tokens
          </CardTitle>
          <CardDescription>
            Client-registered tokens under active spread protection
          </CardDescription>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search token…"
              className="h-8 w-44 rounded-md border bg-transparent pl-8 pr-3 text-xs text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-ring"
            />
          </div>
          <Button size="sm">
            <Plus className="h-3.5 w-3.5" />
            Register
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-xs uppercase tracking-wide text-muted-foreground">
                <th className="pb-3 pr-4 font-medium">Token</th>
                <th className="pb-3 pr-4 font-medium">Contract Address</th>
                <th className="pb-3 pr-4 font-medium">Pool Spread</th>
                <th className="pb-3 pr-4 font-medium">Status</th>
                <th className="pb-3 pr-4 text-right font-medium">Action</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((token) => (
                <tr
                  key={token.id}
                  className={cn(
                    "border-b border-border/60 last:border-0",
                    !token.isActive && "opacity-60",
                  )}
                >
                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2.5">
                      <span
                        className={cn(
                          "flex h-8 w-8 items-center justify-center rounded-md text-xs font-bold",
                          token.isActive
                            ? "bg-primary/10 text-primary"
                            : "bg-muted text-muted-foreground",
                        )}
                      >
                        {token.symbol.slice(0, 2)}
                      </span>
                      <div className="leading-tight">
                        <p className="font-medium">{token.name}</p>
                        <p className="text-xs text-muted-foreground">{token.symbol}</p>
                      </div>
                    </div>
                  </td>

                  <td className="py-3 pr-4">
                    <span className="font-mono text-xs text-muted-foreground">
                      {shortAddress(token.mintAddress)}
                    </span>
                  </td>

                  <td className="py-3 pr-4">
                    <Badge variant={spreadTone(token.spreadBps)} className="tabular-nums">
                      {token.spreadBps} bps
                    </Badge>
                  </td>

                  <td className="py-3 pr-4">
                    <div className="flex items-center gap-2">
                      <Switch
                        checked={token.isActive}
                        onCheckedChange={() => toggleToken(token.id)}
                        aria-label={`Toggle ${token.symbol}`}
                      />
                      <span className="text-xs text-muted-foreground">
                        {token.isActive ? "Active" : "Paused"}
                      </span>
                    </div>
                  </td>

                  <td className="py-3 text-right">
                    <Button size="sm" variant="outline" className="tabular-nums">
                      Top Up Gas
                    </Button>
                  </td>
                </tr>
              ))}

              {filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-sm text-muted-foreground">
                    No tokens match your search.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}
