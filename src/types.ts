export type Speaker = 'm' | 'f';

export interface CueCircle {
  x: number;
  y: number;
  r: number;
  enabled: boolean;
}

export interface Scene {
  id: string;
  order: number;
  chapter: string;
  speaker: Speaker;
  caption: string;
  image_prompt: string;
  cue: CueCircle;
  image_path: string | null;
  audio_path: string | null;
  audio_seconds: number | null;
}

export interface Project {
  id: string;
  title: string;
  voice_m: string;
  voice_f: string;
  scenes: Scene[];
  video_path: string | null;
}

export interface HealthStatus {
  ok: boolean;
  gemini_key_configured: boolean;
}

export interface RenderResult {
  video_path: string;
  srt_path: string | null;
  duration_seconds: number;
  subtitles_burned: boolean;
}

export interface GenerateAllResult {
  processed: number;
  succeeded: number;
  remaining: number;
  total_scenes: number;
  results: unknown[];
}
