import React, { useState, useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, X, Loader2, ArrowRight } from 'lucide-react';
import { api } from '../services/api';
import { ReviewResponse } from '../types';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess: (review: ReviewResponse) => void;
}

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const [invoiceFile, setInvoiceFile] = useState<File | null>(null);
  const [poFile, setPoFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>('');
  const [error, setError] = useState<string | null>(null);

  const invoiceInputRef = useRef<HTMLInputElement>(null);
  const poInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const validateFile = (file: File): string | null => {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF documents are supported.';
    }
    if (file.size > MAX_FILE_SIZE) {
      return `File exceeds 10MB limit (${(file.size / (1024 * 1024)).toFixed(1)}MB).`;
    }
    return null;
  };

  const handleInvoiceSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const err = validateFile(file);
      if (err) {
        setError(err);
      } else {
        setError(null);
        setInvoiceFile(file);
      }
    }
  };

  const handlePoSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      const err = validateFile(file);
      if (err) {
        setError(err);
      } else {
        setError(null);
        setPoFile(file);
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!invoiceFile || !poFile) {
      setError('Please select both an Invoice PDF and a Purchase Order PDF.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      setCurrentStep('Extracting PDF text with PyMuPDF...');
      await new Promise(r => setTimeout(r, 400));
      
      setCurrentStep('Querying Sarvam AI for structured JSON extraction...');
      const review = await api.createReview(invoiceFile, poFile);
      
      setCurrentStep('Audit complete!');
      onSuccess(review);
    } catch (err: any) {
      setError(err.message || 'Audit analysis failed. Please verify the files and try again.');
    } finally {
      setIsLoading(false);
      setCurrentStep('');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-white rounded-2xl max-w-2xl w-full shadow-2xl border border-slate-200 overflow-hidden">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 bg-slate-50/50">
          <div>
            <h2 className="text-lg font-bold text-slate-900">Upload Audit Documents</h2>
            <p className="text-xs text-slate-500">Provide an Invoice and PO (PDF, max 10MB each)</p>
          </div>
          <button
            onClick={onClose}
            disabled={isLoading}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {error && (
            <div className="flex items-start space-x-3 p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-rose-600" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Invoice Upload Card */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2">
                1. Vendor Invoice (PDF)
              </label>
              <input
                ref={invoiceInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handleInvoiceSelect}
                disabled={isLoading}
              />
              <div
                onClick={() => invoiceInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
                  invoiceFile
                    ? 'border-emerald-300 bg-emerald-50/40 text-emerald-900'
                    : 'border-slate-300 hover:border-sky-500 hover:bg-sky-50/30 text-slate-600'
                }`}
              >
                {invoiceFile ? (
                  <div className="space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-600" />
                    <p className="text-xs font-semibold truncate max-w-[200px] mx-auto">{invoiceFile.name}</p>
                    <p className="text-[10px] text-emerald-700 font-medium">
                      {(invoiceFile.size / 1024).toFixed(0)} KB • Click to change
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <Upload className="w-8 h-8 mx-auto text-slate-400" />
                    <p className="text-xs font-medium">Click or drag & drop Invoice</p>
                    <p className="text-[10px] text-slate-400">PDF up to 10MB</p>
                  </div>
                )}
              </div>
            </div>

            {/* PO Upload Card */}
            <div>
              <label className="block text-xs font-semibold uppercase tracking-wider text-slate-700 mb-2">
                2. Purchase Order (PDF)
              </label>
              <input
                ref={poInputRef}
                type="file"
                accept=".pdf,application/pdf"
                className="hidden"
                onChange={handlePoSelect}
                disabled={isLoading}
              />
              <div
                onClick={() => poInputRef.current?.click()}
                className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all ${
                  poFile
                    ? 'border-emerald-300 bg-emerald-50/40 text-emerald-900'
                    : 'border-slate-300 hover:border-sky-500 hover:bg-sky-50/30 text-slate-600'
                }`}
              >
                {poFile ? (
                  <div className="space-y-2">
                    <CheckCircle2 className="w-8 h-8 mx-auto text-emerald-600" />
                    <p className="text-xs font-semibold truncate max-w-[200px] mx-auto">{poFile.name}</p>
                    <p className="text-[10px] text-emerald-700 font-medium">
                      {(poFile.size / 1024).toFixed(0)} KB • Click to change
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <FileText className="w-8 h-8 mx-auto text-slate-400" />
                    <p className="text-xs font-medium">Click or drag & drop PO</p>
                    <p className="text-[10px] text-slate-400">PDF up to 10MB</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Loading Progress State */}
          {isLoading && (
            <div className="bg-sky-50/70 border border-sky-100 rounded-xl p-4 space-y-2 text-center">
              <div className="flex items-center justify-center space-x-2 text-sky-800 font-medium text-sm">
                <Loader2 className="w-4 h-4 animate-spin text-sky-600" />
                <span>Auditing Documents...</span>
              </div>
              <p className="text-xs text-sky-600 animate-pulse">{currentStep}</p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              disabled={isLoading}
              className="px-4 py-2 rounded-lg text-xs font-medium text-slate-600 hover:bg-slate-100 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isLoading || !invoiceFile || !poFile}
              className="flex items-center space-x-2 px-5 py-2.5 rounded-lg text-xs font-semibold bg-sky-600 hover:bg-sky-500 disabled:bg-slate-200 disabled:text-slate-400 text-white shadow-sm transition-all shadow-sky-600/30"
            >
              <span>Run Automated Audit</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

