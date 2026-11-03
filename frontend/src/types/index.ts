export interface LineItem {
  description: string;
  quantity: number;
  unit_price: number;
  tax_rate: number;
  line_total: number;
  hsn_sac?: string | null;
}

export interface DocumentData {
  document_type?: string;
  vendor_name: string;
  document_number: string;
  date: string;
  gstin?: string | null;
  currency: string;
  subtotal: number;
  tax_details?: Record<string, number>;
  total_tax: number;
  grand_total: number;
  line_items: LineItem[];
}

export interface DiscrepancyEvidence {
  source_document: string;
  page_number: number;
  text_snippet: string;
}

export interface Discrepancy {
  id: string;
  type: string;
  severity: 'high' | 'medium' | 'low';
  title: string;
  description: string;
  expected_value: any;
  actual_value: any;
  evidence?: DiscrepancyEvidence | null;
}

export interface ReviewSummary {
  id: string;
  created_at: string;
  status: 'APPROVED' | 'REVIEW' | 'REJECTED' | 'PENDING';
  system_decision?: 'APPROVE' | 'REVIEW' | 'REJECT' | null;
  human_decision?: 'APPROVE' | 'REVIEW' | 'REJECT' | null;
  vendor_name?: string | null;
  invoice_number?: string | null;
  po_number?: string | null;
  invoice_total?: number | null;
  po_total?: number | null;
  currency: string;
  discrepancy_count: number;
  high_severity_count: number;
}

export interface ReviewResponse {
  id: string;
  created_at: string;
  status: 'APPROVED' | 'REVIEW' | 'REJECTED' | 'PENDING';
  system_decision?: 'APPROVE' | 'REVIEW' | 'REJECT' | null;
  rule_score: number;
  rationale?: string | null;
  human_decision?: 'APPROVE' | 'REVIEW' | 'REJECT' | null;
  human_notes?: string | null;
  human_decided_at?: string | null;
  vendor_name?: string | null;
  invoice_number?: string | null;
  po_number?: string | null;
  invoice_total?: number | null;
  po_total?: number | null;
  currency: string;
  invoice_filename?: string | null;
  po_filename?: string | null;
  invoice_data?: DocumentData | null;
  po_data?: DocumentData | null;
  discrepancies: Discrepancy[];
}

