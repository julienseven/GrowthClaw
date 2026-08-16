/**
 * Header component for $GROWTH application.
 * Main navigation and branding.
 */

import { ZapOff } from "lucide-react";

export function Header() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-2">
          <ZapOff className="h-8 w-8 text-green-600" />
          <h1 className="text-2xl font-bold text-gray-900">$GROWTH</h1>
        </div>
        <p className="text-sm text-gray-600">
          Autonomous Marketing Growth Hacker on Solana
        </p>
      </div>
    </header>
  );
}
