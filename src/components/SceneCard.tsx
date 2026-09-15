import React from 'react';
import { mediaUrl } from '../api';
import type { Scene } from '../types';

const SPEAKER_LABEL: Record<Scene['speaker'], string> = { m: '남 진행자', f: '여 진행자' };

export function SceneCard({
  scene,
  onChange,
  onGenerate,
  busy,
}: {
  scene: Scene;
  onChange: (s: Scene) => void;
  onGenerate: () => void;
  busy: boolean;
}) {
  const imgUrl = mediaUrl(scene.image_path);
  const audUrl = mediaUrl(scene.audio_path);

  return (
    <article className={`scene-card sp-${scene.speaker}`}>
      <div className="scene-head">
        <span className="scene-index">#{scene.order + 1}</span>
        <span className="chapter">{scene.chapter}</span>
        <select
          value={scene.speaker}
          onChange={(e) => onChange({ ...scene, speaker: e.target.value as Scene['speaker'] })}
        >
          <option value="m">남 진행자</option>
          <option value="f">여 진행자</option>
        </select>
      </div>

      <div className="scene-body">
        <div className="scene-preview">
          {imgUrl ? <img src={imgUrl} alt={`장면 ${scene.order + 1}`} /> : <div className="placeholder">이미지 없음</div>}
        </div>

        <div className="scene-fields">
          <label htmlFor={`caption-${scene.id}`}>대사 ({SPEAKER_LABEL[scene.speaker]})</label>
          <textarea
            id={`caption-${scene.id}`}
            value={scene.caption}
            onChange={(e) => onChange({ ...scene, caption: e.target.value })}
          />

          <label htmlFor={`prompt-${scene.id}`}>이미지 프롬프트</label>
          <textarea
            id={`prompt-${scene.id}`}
            value={scene.image_prompt}
            onChange={(e) => onChange({ ...scene, image_prompt: e.target.value })}
          />

          <div className="cue-row">
            <label htmlFor={`cue-enabled-${scene.id}`}>
              <input
                id={`cue-enabled-${scene.id}`}
                type="checkbox"
                checked={scene.cue.enabled}
                onChange={(e) => onChange({ ...scene, cue: { ...scene.cue, enabled: e.target.checked } })}
              />
              빨간 원 클릭 강조
            </label>
            {scene.cue.enabled && (
              <div className="cue-inputs">
                <span>x</span>
                <input
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={scene.cue.x}
                  onChange={(e) => onChange({ ...scene, cue: { ...scene.cue, x: Number(e.target.value) } })}
                />
                <span>y</span>
                <input
                  type="number"
                  step={0.01}
                  min={0}
                  max={1}
                  value={scene.cue.y}
                  onChange={(e) => onChange({ ...scene, cue: { ...scene.cue, y: Number(e.target.value) } })}
                />
                <span>r</span>
                <input
                  type="number"
                  step={0.01}
                  min={0.02}
                  max={0.5}
                  value={scene.cue.r}
                  onChange={(e) => onChange({ ...scene, cue: { ...scene.cue, r: Number(e.target.value) } })}
                />
              </div>
            )}
          </div>

          <div className="scene-actions">
            <button onClick={onGenerate} disabled={busy}>
              이미지·음성 생성
            </button>
            {audUrl && <audio controls src={audUrl} />}
          </div>
        </div>
      </div>
    </article>
  );
}
