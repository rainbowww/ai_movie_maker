import React, { useEffect, useRef, useState } from 'react';
import { mediaUrl } from '../api';
import type { Scene } from '../types';

export function PreviewPlayer({ scenes }: { scenes: Scene[] }) {
  const ordered = [...scenes].sort((a, b) => a.order - b.order);
  const [cur, setCur] = useState(0);
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const scene = ordered[Math.min(cur, ordered.length - 1)];
  const imgUrl = scene ? mediaUrl(scene.image_path) : undefined;
  const audUrl = scene ? mediaUrl(scene.audio_path) : undefined;

  useEffect(() => {
    if (playing && audioRef.current && audUrl) {
      audioRef.current.play().catch(() => setPlaying(false));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [cur, audUrl]);

  function handleEnded() {
    if (cur < ordered.length - 1) setCur(cur + 1);
    else setPlaying(false);
  }

  function togglePlay() {
    if (!audUrl) return;
    if (playing) {
      audioRef.current?.pause();
      setPlaying(false);
    } else {
      setPlaying(true);
    }
  }

  if (!scene) return null;

  return (
    <section className="preview">
      <div className="preview-stage">
        {imgUrl ? <img src={imgUrl} alt="" /> : <div className="placeholder">이미지 없음</div>}
      </div>
      <div className="preview-caption">
        <span className={`nameplate sp-${scene.speaker}`}>
          {scene.speaker === 'm' ? '남 진행자' : '여 진행자'}
        </span>
        <p>{scene.caption || '(대사 없음)'}</p>
      </div>
      <div className="preview-controls">
        <button onClick={() => setCur(Math.max(0, cur - 1))} aria-label="이전 장면">
          ⏮
        </button>
        <button onClick={togglePlay} disabled={!audUrl} aria-label={playing ? '일시정지' : '재생'}>
          {playing ? '⏸' : '▶'}
        </button>
        <button onClick={() => setCur(Math.min(ordered.length - 1, cur + 1))} aria-label="다음 장면">
          ⏭
        </button>
        <span className="preview-counter">
          {cur + 1} / {ordered.length}
        </span>
      </div>
      {audUrl && <audio ref={audioRef} src={audUrl} onEnded={handleEnded} />}
    </section>
  );
}
