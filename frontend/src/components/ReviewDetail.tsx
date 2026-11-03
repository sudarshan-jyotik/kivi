import React, { useState } from 'react';
import { ReviewResponse, Discrepancy } from '../types';
import {
  ArrowLeft,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  FileDown,
  Quote,
  ShieldCheck,
  Building2,
  Calendar,
  CreditCard,
  FileText,
  Send,
  Loader2,
  ExternalLink
} from 'lucide-react';
import { api } from '../services/api';

interface ReviewDetailProps {
  review: ReviewResponse;
  onBack: () => void;
  onDecisionUpdated: (updatedReview: ReviewResponse) => void;
}

export const ReviewDetail: React.FC<ReviewDetailProps> = ({
  review,
  onBack,
  onDecisionUpdated,
}) => {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [notes, setNotes] = useState(review.human_notes || '');
  const [actionError, setActionError] = useState<string | null>(null);

  const handleDecision = async (decision: 'APPROVE' | 'REJECT' | 'REVIEW') => {
    setIsSubmitting(true);
    setActionError(null);
    try {
      const updated = await api.submitDecision(review.id, decision, notes);
      onDecisionUpdated(updated);
    } catch (err: any) {
      setActionError(err.message || 'Failed to submit decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getSeverityBadge = (severity: string) => {
    switch (severity) {
      case 'high':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-rose-100 text-rose-800 border border-rose-200">
            HIGH
          </span>
        );
      case 'medium':
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-amber-100 text-amber-800 border border-amber-200">
            MEDIUM
          </span>
        );
      default:
        return (
          <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-sky-100 text-sky-800 border border-sky-200">
            LOW
          </span>
        );
    }
  };

  const currentDecision = review.human_decision || review.system_decision || 'REVIEW';
  const isApproved = currentDecision === 'APPROVE';
  const isRejected = currentDecision === 'REJECT';

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Top Bar Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="flex items-center space-x-2 text-xs font-semibold text-slate-600 hover:text-slate-900 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to All Audits</span>
        </button>

        <a
          href={api.getReportDownloadUrl(review.id)}
          className="flex items-center space-x-2 px-4 py-2 rounded-xl text-xs font-semibold bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 shadow-xs transition-all hover:scale-[1.02]"
        >
          <FileDown className="w-4 h-4 text-sky-600" />
          <span>Download PDF Audit Report</span>
        </a>
      </div>

      {/* Decision Banner */}
      <div
        className={`rounded-2xl p-6 border shadow-sm transition-all ${
          isApproved
            ? 'bg-emerald-50/90 border-emerald-200 text-emerald-950'
            : isRejected
            ? 'bg-rose-50/90 border-rose-200 text-rose-950'
            : 'bg-amber-50/90 border-amber-200 text-amber-950'
        }`}
      >
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start space-x-4">
            <div
              className={`p-3 rounded-xl mt-0.5 text-white ${
                isApproved ? 'bg-emerald-600' : isRejected ? 'bg-rose-600' : 'bg-amber-600'
              }`}
            >
              {isApproved ? (
                <CheckCircle2 className="w-7 h-7" />
              ) : isRejected ? (
                <XCircle className="w-7 h-7" />
              ) : (
                <AlertTriangle className="w-7 h-7" />
              )}
            </div>

            <div>
              <div className="flex items-center space-x-2.5">
                <span className="text-xl font-bold tracking-tight">
                  {review.system_decision || 'REVIEW'} RECOMMENDED
                </span>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-white/80 shadow-xs">
                  Rule Score: {review.rule_score.toFixed(0)}/100
                </span>
                {review.human_decision && (
                  <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-slate-900 text-white">
                    Human Approved: {review.human_decision}
                  </span>
                )}
              </div>
              <p className="text-xs font-medium mt-1.5 opacity-90 leading-relaxed max-w-3xl">
                {review.rationale || 'No automated rationale provided.'}
              </p>
            </div>
          </div>

          <div className="text-right text-xs shrink-0">
            <p className="font-semibold">Review ID</p>
            <p className="font-mono text-slate-500">{review.id.slice(0, 13)}...</p>
          </div>
        </div>
      </div>

      {/* Human Decision Form */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Human Auditor Determination</h3>
            <p className="text-xs text-slate-500">Record your final approval, rejection, or request for manual review</p>
          </div>
          {review.human_decision && (
            <span className="text-xs font-medium text-slate-600">
              Decided on {new Date(review.human_decided_at || '').toLocaleString()}
            </span>
          )}
        </div>

        {actionError && (
          <p className="text-xs text-rose-600 bg-rose-50 p-2.5 rounded-lg border border-rose-200">
            {actionError}
          </p>
        )}

        <div className="space-y-3">
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="Add reviewer notes, reason for override, or adjustment justification..."
            rows={2}
            className="w-full text-xs rounded-xl border border-slate-200 p-3 bg-slate-50/50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-sky-500/20 focus:border-sky-500"
          />

          <div className="flex flex-wrap items-center justify-end gap-2.5">
            <button
              onClick={() => handleDecision('APPROVE')}
              disabled={isSubmitting}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm disabled:opacity-50"
            >
              <CheckCircle2 className="w-3.5 h-3.5" />
              <span>Approve Invoice</span>
            </button>

            <button
              onClick={() => handleDecision('REVIEW')}
              disabled={isSubmitting}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white transition-all shadow-sm disabled:opacity-50"
            >
              <AlertTriangle className="w-3.5 h-3.5" />
              <span>Request Clarification</span>
            </button>

            <button
              onClick={() => handleDecision('REJECT')}
              disabled={isSubmitting}
              className="flex items-center space-x-1.5 px-4 py-2 rounded-xl text-xs font-bold bg-rose-600 hover:bg-rose-500 text-white transition-all shadow-sm disabled:opacity-50"
            >
              <XCircle className="w-3.5 h-3.5" />
              <span>Reject Invoice</span>
            </button>
          </div>
        </div>
      </div>

      {/* Discrepancies & Evidence Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Audit Findings ({review.discrepancies.length} Discrepanc{review.discrepancies.length === 1 ? 'y' : 'ies'})
            </h3>
            <p className="text-xs text-slate-500">Deterministic rule check results with source citations</p>
          </div>
        </div>

        {review.discrepancies.length === 0 ? (
          <div className="p-8 text-center text-slate-500 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
            <p className="font-semibold text-slate-800">Perfect 2-Way Match!</p>
            <p className="text-slate-500 mt-0.5">All line items, quantities, rates, and totals agree with Purchase Order.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {review.discrepancies.map((d: Discrepancy) => (
              <div key={d.id} className="p-5 hover:bg-slate-50/50 transition-colors space-y-3">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start space-x-3">
                    {getSeverityBadge(d.severity)}
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">{d.title}</h4>
                      <p className="text-xs text-slate-600 mt-0.5">{d.description}</p>
                    </div>
                  </div>

                  <div className="text-right text-xs font-mono shrink-0">
                    <span className="text-slate-400">Type: </span>
                    <span className="font-medium text-slate-700">{d.type}</span>
                  </div>
                </div>

                {/* Expected vs Actual Comparison Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pl-8">
                  <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 text-xs">
                    <span className="font-semibold text-slate-500 block text-[10px] uppercase">
                      Expected (from Purchase Order):
                    </span>
                    <span className="font-medium text-slate-800 mt-0.5 block">
                      {String(d.expected_value ?? 'N/A')}
                    </span>
                  </div>

                  <div className="bg-rose-50/50 border border-rose-200/60 rounded-xl p-3 text-xs">
                    <span className="font-semibold text-rose-600 block text-[10px] uppercase">
                      Actual (from Invoice):
                    </span>
                    <span className="font-medium text-rose-950 mt-0.5 block">
                      {String(d.actual_value ?? 'N/A')}
                    </span>
                  </div>
                </div>

                {/* Evidence Snippet */}
                {d.evidence && (
                  <div className="pl-8">
                    <div className="flex items-start space-x-2 text-[11px] bg-sky-50/60 border border-sky-100 rounded-xl p-2.5 text-sky-950">
                      <Quote className="w-3.5 h-3.5 text-sky-600 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-semibold text-sky-800">
                          Evidence ({d.evidence.source_document}, Page {d.evidence.page_number}):
                        </span>{' '}
                        <span className="italic">"{d.evidence.text_snippet}"</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Side-by-Side Extracted Document Comparison */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Invoice Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-sky-600" />
              <h3 className="font-bold text-sm text-slate-900">Extracted Invoice</h3>
            </div>
            <span className="text-xs text-slate-400 truncate max-w-[150px]">{review.invoice_filename}</span>
          </div>

          {review.invoice_data ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400 block text-[10px]">Vendor</span>
                  <span className="font-semibold text-slate-800">{review.invoice_data.vendor_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Invoice Number</span>
                  <span className="font-semibold text-slate-800">{review.invoice_data.document_number}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Date</span>
                  <span className="text-slate-700">{review.invoice_data.date}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">GSTIN</span>
                  <span className="font-mono text-slate-700">{review.invoice_data.gstin || 'Not provided'}</span>
                </div>
              </div>

              {/* Items Table */}
              <div className="border border-slate-100 rounded-xl overflow-hidden mt-2">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-50 text-slate-500 font-semibold">
                    <tr>
                      <th className="p-2">Item</th>
                      <th className="p-2 text-right">Qty</th>
                      <th className="p-2 text-right">Rate</th>
                      <th className="p-2 text-right">GST</th>
                      <th className="p-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {review.invoice_data.line_items.map((it, idx) => (
                      <tr key={idx}>
                        <td className="p-2 font-medium text-slate-800">{it.description}</td>
                        <td className="p-2 text-right">{it.quantity}</td>
                        <td className="p-2 text-right">₹{it.unit_price.toFixed(2)}</td>
                        <td className="p-2 text-right">{it.tax_rate}%</td>
                        <td className="p-2 text-right font-semibold">₹{it.line_total.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Totals Summary */}
              <div className="bg-slate-50 rounded-xl p-3 space-y-1 text-slate-600 text-[11px]">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>₹{review.invoice_data.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Tax (GST):</span>
                  <span>₹{review.invoice_data.total_tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-slate-900 border-t border-slate-200 pt-1 text-xs">
                  <span>Grand Total:</span>
                  <span>₹{review.invoice_data.grand_total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400">No invoice data available.</p>
          )}
        </div>

        {/* PO Card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <Building2 className="w-4 h-4 text-indigo-600" />
              <h3 className="font-bold text-sm text-slate-900">Extracted Purchase Order</h3>
            </div>
            <span className="text-xs text-slate-400 truncate max-w-[150px]">{review.po_filename}</span>
          </div>

          {review.po_data ? (
            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-2">
                <div>
                  <span className="text-slate-400 block text-[10px]">Vendor</span>
                  <span className="font-semibold text-slate-800">{review.po_data.vendor_name}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">PO Number</span>
                  <span className="font-semibold text-slate-800">{review.po_data.document_number}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Date</span>
                  <span className="text-slate-700">{review.po_data.date}</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">GSTIN</span>
                  <span className="font-mono text-slate-700">{review.po_data.gstin || 'Not provided'}</span>
                </div>
              </div>

              {/* PO Items Table */}
              <div className="border border-slate-100 rounded-xl overflow-hidden mt-2">
                <table className="w-full text-left text-[11px]">
                  <thead className="bg-slate-50 text-slate-500 font-semibold">
                    <tr>
                      <th className="p-2">Item</th>
                      <th className="p-2 text-right">Qty</th>
                      <th className="p-2 text-right">Rate</th>
                      <th className="p-2 text-right">GST</th>
                      <th className="p-2 text-right">Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {review.po_data.line_items.map((it, idx) => (
                      <tr key={idx}>
                        <td className="p-2 font-medium text-slate-800">{it.description}</td>
                        <td className="p-2 text-right">{it.quantity}</td>
                        <td className="p-2 text-right">₹{it.unit_price.toFixed(2)}</td>
                        <td className="p-2 text-right">{it.tax_rate}%</td>
                        <td className="p-2 text-right font-semibold">₹{it.line_total.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* PO Totals Summary */}
              <div className="bg-slate-50 rounded-xl p-3 space-y-1 text-slate-600 text-[11px]">
                <div className="flex justify-between">
                  <span>Subtotal:</span>
                  <span>₹{review.po_data.subtotal.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Tax (GST):</span>
                  <span>₹{review.po_data.total_tax.toFixed(2)}</span>
                </div>
                <div className="flex justify-between font-bold text-slate-900 border-t border-slate-200 pt-1 text-xs">
                  <span>Grand Total:</span>
                  <span>₹{review.po_data.grand_total.toFixed(2)}</span>
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-400">No purchase order data available.</p>
          )}
        </div>
      </div>
    </div>
  );
};
