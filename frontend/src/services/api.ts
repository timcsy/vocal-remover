const API_BASE = '/api/v1';

export interface Job {
  id: string;
  source_type: 'youtube' | 'upload';
  status: 'pending' | 'downloading' | 'separating' | 'merging' | 'completed' | 'failed';
  progress: number;
  current_stage: string;
  error_message: string | null;
  created_at: string;
  expires_at: string;
}

export interface Result {
  original_duration: number;
  output_size: number;
  download_url: string;
}

export interface JobWithResult extends Job {
  result: Result | null;
}

export interface ApiError {
  code: string;
  message: string;
}

export interface HealthStatus {
  status: 'healthy' | 'unhealthy';
  redis: boolean;
  storage: boolean;
  version: string;
}

class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw error;
    }

    return response.json();
  }

  async createJobFromUrl(url: string): Promise<Job> {
    return this.request<Job>('/jobs', {
      method: 'POST',
      body: JSON.stringify({
        source_type: 'youtube',
        source_url: url,
      }),
    });
  }

  async createJobFromUpload(file: File): Promise<Job> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/jobs/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error: ApiError = await response.json();
      throw error;
    }

    return response.json();
  }

  async getJob(jobId: string): Promise<JobWithResult> {
    return this.request<JobWithResult>(`/jobs/${jobId}`);
  }

  getDownloadUrl(jobId: string): string {
    return `${API_BASE}/jobs/${jobId}/download`;
  }

  async healthCheck(): Promise<HealthStatus> {
    return this.request<HealthStatus>('/health');
  }
}

export const api = new ApiService();
