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
  /** What the viewer reads on screen. */
  caption: string;
  /** What the engine says, when it must differ from the caption. Empty means
   *  "derive it from the caption" (see backend/app/services/speech_text.py). */
  speech_text: string;
  image_prompt: string;
  /** Names the locally drawn mockup used by the zero-cost path. */
  visual_key: string;
  cue: CueCircle;
  /** Matching beat in the source video, e.g. "0:14-0:16". */
  source_timecode: string;
  /** How long to hold a scene with no narration. */
  hold_seconds: number | null;
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
