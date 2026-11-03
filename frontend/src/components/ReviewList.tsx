import React, { useState } from 'react';
import { ReviewSummary } from '../types';
import { Search, Filter, CheckCircle2, AlertTriangle, XCircle, Clock, ChevronRight, FileDown, ShieldAlert } from 'lucide-react';
import { api } from '../services/api';

interface ReviewListProps {
  reviews: ReviewSummary[];
  onSelectReview: (id: string) => void;
  isLoading: boolean;
  onRefresh: () => void;
}

export const ReviewList: React.FC<ReviewListProps> = ({
  reviews,
  onSelectReview,
  isLoading,
}) => {
  const [filterStatus, setFilterStatus] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const filteredReviews = reviews.filter((r) => {
    const matchesStatus = filterStatus === 'ALL' || r.status === filterStatus;
    const q = searchQuery.toLowerCase();
    const matchesSearch =
      !searchQuery ||
      (r.vendor_name?.toLowerCase().includes(q) ?? false) ||
      (r.invoice_number?.toLowerCase().includes(q) ?? false) ||
      (r.po_number?.toLowerCase().includes(q) ?? false);
    return matchesStatus && matchesSearch;
  });

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'APPROVED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100/80 text-emerald-800 border border-emerald-200">
            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
            <span>APPROVE</span>
          </span>
        );
      case 'REJECTED':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-100/80 text-rose-800 border border-rose-200">
            <XCircle className="w-3 h-3 text-rose-600" />
            <span>REJECT</span>
          </span>
        );
      case 'REVIEW':
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-100/80 text-amber-800 border border-amber-200">
            <AlertTriangle className="w-3 h-3 text-amber-600" />
            <span>REVIEW</span>
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
            <Clock className="w-3 h-3 text-slate-500" />
            <span>PENDING</span>
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header Controls */}
      <div className="p-4 sm:p-6 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Audit History & Records</h2>
          <p className="text-xs text-slate-500 mt-0.5">Track automated invoice verifications and human decisions</p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Search vendor, invoice..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 pr-3.5 py-1.5 text-xs rounded-xl border border-slate-200 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500 w-48 sm:w-60"
            />
          </div>

          {/* Status Filter Buttons */}
          <div className="flex items-center rounded-xl border border-slate-200 bg-slate-50/70 p-0.5 text-xs">
            {['ALL', 'APPROVED', 'REVIEW', 'REJECTED'].map((status) => (
              <button
                key={status}
                onClick={() => setFilterStatus(status)}
                className={`px-3 py-1 rounded-lg font-medium transition-all ${
                  filterStatus === status
                    ? 'bg-white text-slate-900 shadow-xs font-semibold'
                    : 'text-slate-500 hover:text-slate-900'
                }`}
              >
                {status}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table Content */}
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="bg-slate-50/80 text-slate-500 uppercase tracking-wider font-semibold border-b border-slate-100">
              <th className="px-6 py-3.5">Status</th>
              <th className="px-6 py-3.5">Vendor / Document</th>
              <th className="px-6 py-3.5">Invoice # / PO #</th>
              <th className="px-6 py-3.5">Amount (INR)</th>
              <th className="px-6 py-3.5">Audit Flags</th>
              <th className="px-6 py-3.5">Date</th>
              <th className="px-6 py-3.5 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {isLoading && reviews.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                  Loading audit logs...
                </td>
              </tr>
            ) : filteredReviews.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-400">
                  No audits found matching the selected filters.
                </td>
              </tr>
            ) : (
              filteredReviews.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => onSelectReview(r.id)}
                  className="hover:bg-slate-50/80 cursor-pointer transition-colors group"
                >
                  <td className="px-6 py-4 font-medium whitespace-nowrap">
                    {getStatusBadge(r.status)}
                  </td>
                  <td className="px-6 py-4">
                    <div className="font-semibold text-slate-900 group-hover:text-sky-600 transition-colors">
                      {r.vendor_name || 'Unknown Vendor'}
                    </div>
                    <div className="text-[11px] text-slate-400">ID: {r.id.slice(0, 8)}...</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-slate-800 font-medium">Inv: {r.invoice_number || 'N/A'}</div>
                    <div className="text-[11px] text-slate-400">PO: {r.po_number || 'N/A'}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="font-semibold text-slate-900">
                      ₹{r.invoice_total != null ? r.invoice_total.toLocaleString('en-IN', { minimumFractionDigits: 2 }) : '0.00'}
                    </div>
                    {r.po_total != null && (
                      <div className="text-[11px] text-slate-400">
                        PO: ₹{r.po_total.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    {r.discrepancy_count === 0 ? (
                      <span className="text-emerald-700 font-medium text-[11px] flex items-center space-x-1">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                        <span>Clean match</span>
                      </span>
                    ) : (
                      <div className="flex items-center space-x-1.5">
                        <span className="px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 font-semibold border border-amber-200">
                          {r.discrepancy_count} issue{r.discrepancy_count > 1 ? 's' : ''}
                        </span>
                        {r.high_severity_count > 0 && (
                          <span className="px-1.5 py-0.5 rounded-md bg-rose-50 text-rose-700 font-bold border border-rose-200 flex items-center space-x-0.5">
                            <ShieldAlert className="w-3 h-3 text-rose-600" />
                            <span>{r.high_severity_count} high</span>
                          </span>
                        )}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 text-slate-500 whitespace-nowrap text-[11px]">
                    {new Date(r.created_at).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </td>
                  <td className="px-6 py-4 text-right whitespace-nowrap">
                    <div className="flex items-center justify-end space-x-2">
                      <a
                        href={api.getReportDownloadUrl(r.id)}
                        onClick={(e) => e.stopPropagation()}
                        className="p-1.5 rounded-lg text-slate-400 hover:text-sky-600 hover:bg-sky-50 transition-colors"
                        title="Download PDF Report"
                      >
                        <FileDown className="w-4 h-4" />
                      </a>
                      <div className="p-1.5 text-slate-400 group-hover:text-slate-600">
                        <ChevronRight className="w-4 h-4" />
                      </div>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

