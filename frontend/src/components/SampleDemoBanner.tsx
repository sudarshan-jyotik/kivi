import React from 'react';
import { Sparkles, CheckCircle2, AlertTriangle, XCircle, Loader2 } from 'lucide-react';

interface SampleDemoBannerProps {
  onRunDemo: (sampleNumber: number) => void;
  isLoading: boolean;
  activeDemoNumber: number | null;
}

export const SampleDemoBanner: React.FC<SampleDemoBannerProps> = ({
  onRunDemo,
  isLoading,
  activeDemoNumber,
}) => {
  return (
    <div className="bg-gradient-to-r from-sky-50 via-indigo-50/50 to-purple-50 border border-sky-100/80 rounded-2xl p-5 mb-8 shadow-sm">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-start space-x-3.5">
          <div className="p-2.5 rounded-xl bg-sky-600 text-white shadow-sm mt-0.5">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 text-base">Quick Demo: 3-Way Match Samples</h3>
            <p className="text-xs text-slate-600 mt-0.5 leading-relaxed max-w-xl">
              Don't have PDFs handy? Test AP Agent instantly against sample Indian GST invoices and purchase orders.
            </p>
          </div>
        </div>

        {/* Demo Buttons */}
        <div className="flex flex-wrap items-center gap-2">
          {/* Sample 1 */}
          <button
            onClick={() => onRunDemo(1)}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-emerald-200 text-emerald-800 hover:bg-emerald-50/80 shadow-sm transition-all hover:scale-[1.02] disabled:opacity-50"
          >
            {isLoading && activeDemoNumber === 1 ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-600" />
            ) : (
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            )}
            <span>Sample 1: Clean Match (APPROVE)</span>
          </button>

          {/* Sample 2 */}
          <button
            onClick={() => onRunDemo(2)}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-rose-200 text-rose-800 hover:bg-rose-50/80 shadow-sm transition-all hover:scale-[1.02] disabled:opacity-50"
          >
            {isLoading && activeDemoNumber === 2 ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-rose-600" />
            ) : (
              <XCircle className="w-3.5 h-3.5 text-rose-600" />
            )}
            <span>Sample 2: Price/Qty/Tax (REJECT)</span>
          </button>

          {/* Sample 3 */}
          <button
            onClick={() => onRunDemo(3)}
            disabled={isLoading}
            className="flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold bg-white border border-amber-200 text-amber-800 hover:bg-amber-50/80 shadow-sm transition-all hover:scale-[1.02] disabled:opacity-50"
          >
            {isLoading && activeDemoNumber === 3 ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin text-amber-600" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            )}
            <span>Sample 3: Extra Item (REVIEW)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
