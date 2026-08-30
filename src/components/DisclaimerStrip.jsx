import React from 'react';
import { Info } from 'lucide-react';

export default function DisclaimerStrip() {
  return (
    <div className="bg-trust-light/70 border-b border-trust-tint/50 text-trust py-2 px-4 text-center text-xs sm:text-sm font-medium flex items-center justify-center space-x-2">
      <Info className="w-4 h-4 text-trust shrink-0" />
      <span>You're getting legal awareness guidance, not legal advice.</span>
    </div>
  );
}
