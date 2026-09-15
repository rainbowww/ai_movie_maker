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
    setBusy('전체 장면 생성 중… (장면 수에 따라 수 분 소요될 수 있습니다)');
    setError(null);
    try {
      await saveCurrent(current);
      await api.generateAll(current.id, false);
      const fresh = await api.getProject(current.id);
      setCurrent(fresh);
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
          완성: {renderResult.duration_seconds.toFixed(1)}초 —{' '}
          <a href={mediaUrl(current.video_path)} download>
            영상 다운로드
          </a>
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
