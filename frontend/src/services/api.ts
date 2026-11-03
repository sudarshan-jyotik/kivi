import { ReviewResponse, ReviewSummary } from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '');

export const api = {
  async checkHealth(): Promise<{ status: string; app: string }> {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error('Backend health check failed');
    return res.json();
  },

  async listReviews(status?: string, search?: string): Promise<ReviewSummary[]> {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (search) params.append('search', search);

    const qs = params.toString() ? `?${params.toString()}` : '';
    const res = await fetch(`${API_BASE_URL}/api/reviews${qs}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch reviews list');
    }
    return res.json();
  },

  async getReview(id: string): Promise<ReviewResponse> {
    const res = await fetch(`${API_BASE_URL}/api/reviews/${id}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to fetch review details');
    }
    return res.json();
  },

  async createReview(invoiceFile: File, poFile: File): Promise<ReviewResponse> {
    const formData = new FormData();
    formData.append('invoice', invoiceFile);
    formData.append('po', poFile);

    const res = await fetch(`${API_BASE_URL}/api/reviews`, {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Audit processing failed');
    }
    return res.json();
  },

  async submitDecision(id: string, decision: 'APPROVE' | 'REJECT' | 'REVIEW', notes?: string): Promise<ReviewResponse> {
    const res = await fetch(`${API_BASE_URL}/api/reviews/${id}/decision`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ decision, notes }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to save review decision');
    }
    return res.json();
  },

  async runDemo(sampleNumber: number): Promise<ReviewResponse> {
    const res = await fetch(`${API_BASE_URL}/api/demo/${sampleNumber}`, {
      method: 'POST',
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Failed to run Demo Sample #${sampleNumber}`);
    }
    return res.json();
  },

  getReportDownloadUrl(id: string): string {
    return `${API_BASE_URL}/api/reviews/${id}/report`;
  }
};
