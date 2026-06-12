export type OpsStatus =
  | 'ok'
  | 'running'
  | 'stale'
  | 'error'
  | 'none'
  | 'missing'
  | 'outdated'
  | 'too_long'
  | 'sent'
  | 'not_sent'
  | 'no_report'
  | 'empty'
  | 'inactive';

export interface OpsIssue {
  title: string;
  severity: 'info' | 'warning' | 'error';
  message: string;
  source_id?: number;
  key?: string;
}

export interface SourceHealthItem {
  source_id: number;
  name: string;
  platform: string;
  source_type: string;
  source_url: string;
  active: boolean;
  priority_score: number;
  post_count: number;
  latest_collected_at: string | null;
  latest_posted_at: string | null;
  health_status: 'ok' | 'empty' | 'stale' | 'inactive';
  reason: string;
}

export interface SavedIdeaSummaryItem {
  id: number;
  title: string | null;
  status: 'saved' | 'used';
  idea_number: number | null;
  created_at: string | null;
  used_at: string | null;
}

export interface ProductionCheck {
  key: string;
  label: string;
  configured: boolean;
  kind?: string;
}

export interface OpsSummary {
  latest_job: {
    status: OpsStatus;
    name: string | null;
    started_at: string | null;
    finished_at: string | null;
    error: string | null;
  };
  sources: {
    total: number;
    ok: number;
    empty: number;
    stale: number;
    inactive: number;
    items: SourceHealthItem[];
  };
  report: {
    status: OpsStatus;
    report_date: string | null;
    message_length: number;
    top_posts_count: number;
    sent_at?: string | null;
  };
  telegram: {
    status: OpsStatus;
    sent_at: string | null;
  };
  saved_ideas: {
    total: number;
    saved: number;
    used: number;
    items: SavedIdeaSummaryItem[];
  };
  production: {
    checks: ProductionCheck[];
  };
  top_issues: OpsIssue[];
}
