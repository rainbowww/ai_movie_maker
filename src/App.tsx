import React, { useEffect, useState } from 'react';
import { api, mediaUrl } from './api';
import { PreviewPlayer } from './components/PreviewPlayer';
import { SceneCard } from './components/SceneCard';
import type { Project, RenderResult, Scene } from './types';

export default function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [current, setCurrent] = useState<Project | null>(null);
  const [geminiReady, setGeminiReady] = useState<boolean | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [renderResult, setRenderResult] = useState<RenderResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then((h) => setGeminiReady(h.gemini_key_configured))
      .catch(() => setGeminiReady(false));
    api
      .listProjects()
      .then((list) => {
        setProjects(list);
        if (list.length) setCurrent(list[0]);
      })
      .catch((e) => setError(String(e)));
  }, []);

  function updateScene(updated: Scene) {
    if (!current) return;
    setCurrent({ ...current, scenes: current.scenes.map((s) => (s.id === updated.id ? updated : s)) });
  }

  async function saveCurrent(project: Project) {
    const saved = await api.saveProject(project);
    setCurrent(saved);
    setProjects((prev) => prev.map((p) => (p.id === saved.id ? saved : p)));
    return saved;
  }

  async function generateScene(scene: Scene) {
    if (!current) return;
    setBusy(`장면 ${scene.order + 1} 생성 중…`);
    setError(null);
    try {
      await saveCurrent(current);
      await api.generateScene(current.id, scene.id, true);
      const fresh = await api.getProject(current.id);
      setCurrent(fresh);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function generateAll() {
    if (!current) return;
    setError(null);
    try {
      await saveCurrent(current);
      // The backend generates a few scenes per call so no single request
      // outlives its timeout; keep going until it reports nothing left.
      let guard = 0;
      for (;;) {
        const batch = await api.generateAll(current.id, false);
        const done = batch.total_scenes - batch.remaining;
        setBusy(`생성 중… ${done}/${batch.total_scenes} 장면`);
        const fresh = await api.getProject(current.id);
        setCurrent(fresh);
        if (batch.remaining === 0 || batch.processed === 0) break;
        if (batch.succeeded === 0) {
          // Every scene in that batch failed the same way — retrying the
          // rest would just repeat it. Surface the reason instead.
          const first = batch.results[0] as { errors?: Record<string, string> } | undefined;
          const reason = first?.errors ? Object.values(first.errors).join(' / ') : '알 수 없는 오류';
          throw new Error(`생성 실패 — ${reason}`);
        }
        if (++guard > 200) break;
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function renderVideo() {
    if (!current) return;
    setBusy('영상 렌더링 중…');
    setError(null);
    setRenderResult(null);
    try {
      const result = await api.renderProject(current.id);
      setRenderResult(result);
      const fresh = await api.getProject(current.id);
      setCurrent(fresh);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  if (!current) {
    return (
      <div className="shell">
        <p className="empty-state">
          {projects.length === 0
            ? '프로젝트가 없습니다. backend/scripts/seed_demo_project.py 를 실행해 예시 프로젝트를 만드세요.'
            : '불러오는 중…'}
        </p>
      </div>
    );
  }

  const readyImages = current.scenes.filter((s) => s.image_path).length;
  const readyAudio = current.scenes.filter((s) => s.audio_path).length;
  const total = current.scenes.length;

  return (
    <div className="shell">
      <header className="topbar">
        <div>
          <span className="kicker">AI 무비 메이커 · Python + Gemini</span>
          <h1>{current.title}</h1>
          {projects.length > 1 && (
            <select
              className="project-switch"
              value={current.id}
              onChange={(e) => {
                const next = projects.find((p) => p.id === e.target.value);
                if (next) {
                  setCurrent(next);
                  setRenderResult(null);
                }
              }}
            >
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.title}
                </option>
              ))}
            </select>
          )}
        </div>
        <div className={`badge ${geminiReady ? 'ok' : 'warn'}`}>
          {geminiReady === null ? '확인 중…' : geminiReady ? 'Gemini API 연결됨' : 'GEMINI_API_KEY 미설정'}
        </div>
      </header>

      {error && <div className="error-banner">{error}</div>}

      <section className="controls">
        <div className="stat">
          이미지 {readyImages}/{total}
        </div>
        <div className="stat">
          음성 {readyAudio}/{total}
        </div>
        <button onClick={generateAll} disabled={!!busy || !geminiReady}>
          전체 생성
        </button>
        <button onClick={renderVideo} disabled={!!busy || readyImages < total}>
          영상 렌더링
        </button>
        {busy && <span className="busy">{busy}</span>}
      </section>

      {!geminiReady && (
        <p className="hint">
          backend/.env 에 GEMINI_API_KEY를 설정하고 백엔드를 재시작하면 생성 버튼이 활성화됩니다.
        </p>
      )}

      {renderResult && (
        <div className="render-result">
          완성: {renderResult.duration_seconds.toFixed(1)}초
          {renderResult.subtitles_burned && ' · 한글 자막 번인됨'} —{' '}
          <a href={mediaUrl(current.video_path)} download>
            영상 다운로드
          </a>
          {renderResult.srt_path && (
            <>
              {' · '}
              <a href={mediaUrl(renderResult.srt_path)} download>
                자막(.srt) 다운로드
              </a>
            </>
          )}
        </div>
      )}
      {current.video_path && !renderResult && (
        <div className="render-result">
          이전 렌더 결과 —{' '}
          <a href={mediaUrl(current.video_path)} download>
            영상 다운로드
          </a>
        </div>
      )}

      <PreviewPlayer scenes={current.scenes} />

      <section className="scene-list">
        {[...current.scenes]
          .sort((a, b) => a.order - b.order)
          .map((scene) => (
            <SceneCard
              key={scene.id}
              scene={scene}
              onChange={updateScene}
              onGenerate={() => generateScene(scene)}
              busy={!!busy}
            />
          ))}
      </section>
    </div>
  );
}
