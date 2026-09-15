<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# AI 무비 메이커

이미지 생성 + TTS(음성합성)를 결합해 **한국어 사용설명서 스타일 영상**을 만드는 도구입니다.
씬(장면) 단위로 대사·이미지 프롬프트·클릭 강조(빨간 원)를 편집하고, 각 씬을 Gemini로
생성한 뒤 ffmpeg으로 **한글 자막이 구워진 하나의 mp4**로 합칩니다.

이전에 이 저장소에 있던 "Gemini ID 증명사진 생성기" 데모는 이 도구로 교체되었습니다
(git 히스토리에는 남아 있습니다).

## 두 가지 컨셉이 기본 제공됩니다

| 프로젝트 | 컨셉 | 장면 | 화자 |
|---|---|---|---|
| `demo-2host` | 두 사람 진행 (남/여 대화체) | 13 | 남·여 두 목소리 |
| `demo-solo` | 1인칭 단독 진행 (원본 영상과 같은 화법) | 28 | 한 목소리 |

같은 워크플로(Treblo → Claude → Google Flow → CapCut)를 서로 다른 화법으로 담았습니다.
UI 상단 드롭다운으로 두 프로젝트를 오갈 수 있습니다.

## 자막과 싱크

- 각 장면 클립의 길이 = 그 장면 내레이션 오디오의 길이입니다. 따라서 음성과 자막이
  **구조적으로 어긋날 수 없습니다.**
- 긴 대사는 글자 수에 비례해 여러 자막으로 자동 분할되고, 분할 지점은 문장 끝 →
  쉼표 → 띄어쓰기 순으로 선택돼 말이 끊기는 자리에 자연스럽게 걸립니다.
- 영상은 그림 영역(1280×720) 아래에 **자막 전용 띠(96px)** 를 덧붙인 1280×816으로
  출력됩니다. 자막이 그림이나 빨간 원을 가리는 일이 없습니다.
- 번인 자막은 해상도를 명시한 ASS로 그려지고(픽셀 단위 정확도), 배포용 `.srt`가
  mp4 옆에 함께 저장됩니다(유튜브 업로드·번역에 재사용 가능).

## 아키텍처

```
├── src/                 프런트엔드 (React + Vite + TypeScript)
├── backend/             백엔드 (Python + FastAPI)
│   ├── app/
│   │   ├── main.py          FastAPI 앱, CORS, 정적 미디어 서빙
│   │   ├── models.py        Project/Scene 데이터 모델 + JSON 파일 저장소
│   │   ├── routers/         projects / generate / render 엔드포인트
│   │   └── services/
│   │       ├── gemini_image.py   Gemini 이미지 생성
│   │       ├── gemini_tts.py     Gemini TTS (PCM → WAV 변환 포함)
│   │       ├── overlay.py        Pillow로 빨간 원 클릭 강조 합성
│   │       └── video_render.py   ffmpeg로 이미지+오디오 → mp4 합성
│   ├── scripts/          seed_demo_project.py, smoke_test_gemini.py
│   ├── tests/            pytest (렌더 파이프라인, 네트워크 불필요)
│   └── storage/          생성물 저장 위치 (git에 커밋되지 않음)
├── package.json          프런트엔드 의존성 (node_modules는 저장소 최상위에 위치)
└── vite.config.ts        /api, /media 를 백엔드(:8000)로 프록시
```

**왜 이 구조인가:** 이미지·음성 생성처럼 비용이 드는 외부 API 호출과 비밀키는
백엔드(Python)에만 두고, 프런트엔드는 순수 UI/상태 관리만 담당합니다.
렌더링(ffmpeg 합성)은 네트워크나 API 키 없이 로컬에서 항상 재현 가능해야 하므로
별도 서비스 모듈로 분리했고, `backend/tests/test_render.py`가 합성 테스트용
이미지·무음 오디오만으로 실제 mp4 생성을 검증합니다.

## 빠른 시작

### 1. 백엔드

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# .env를 열어 GEMINI_API_KEY 입력 (https://aistudio.google.com/apikey 에서 발급)

python -m scripts.seed_demo_project   # 컨셉 1: 두 사람 진행 (13장면)
python -m scripts.seed_solo_project   # 컨셉 2: 1인칭 단독 진행 (28장면)
uvicorn app.main:app --reload --port 8000
```

키를 넣기 전에도 서버는 정상 기동하며, 생성 관련 엔드포인트만 명확한 한국어
오류를 반환합니다 (`GEMINI_API_KEY가 설정되지 않았습니다.`).

키를 넣은 뒤에는 실제 API 호출이 되는지 먼저 확인하세요 (이 코드는 저장소를
만든 샌드박스에 API 키가 없어 실제 호출로 검증하지 못했습니다):

```bash
python -m scripts.smoke_test_gemini
```

### 2. 프런트엔드 (새 터미널)

```bash
npm install     # 저장소 최상위에 node_modules 생성
npm run dev     # http://localhost:5173, /api·/media는 :8000으로 프록시
```

### 3. 돈 쓰기 전에 완성본 먼저 보기 (0원, 명령 하나)

API 키도 크레딧도 서버도 없이, 완성된 영상을 통째로 만들어 볼 수 있습니다.

```bash
sudo apt install espeak-ng ffmpeg fonts-nanum     # 한 번만
python -m scripts.make_free_cut demo-solo         # 35장면 · 약 2분 소요
python -m scripts.make_free_cut demo-2host        # 13장면 · 약 40초
```

이 한 줄이 화면을 그리고, 한국어 내레이션을 만들고, 자막을 구워 mp4까지 뽑습니다.

- **화면**: `app/services/mockups.py`가 27종을 직접 그립니다. 이미지 모델에게는
  "생성 버튼을 여기 그려라"를 시킬 수 없어서, 클릭 강조가 의미를 가지려면 레이아웃을
  아는 쪽이 그려야 합니다. 그래서 빨간 원이 버튼 "근처"가 아니라 "위"에 얹힙니다.
- **음성**: espeak-ng(오프라인). 화자에 따라 목소리와 피치가 갈리고, EQ·컴프레서·
  룸·라우드니스 정규화를 거칩니다. 사람 목소리는 아니지만 10분을 들을 수는 있습니다.
- **한계**: 화면은 도식이고 목소리는 합성음입니다. 구조·타이밍·자막을 확인하는 용도입니다.

여기까지 마음에 들면 키를 넣고 "전체 생성"으로 품질만 올리면 됩니다. 렌더 단계는
그대로 재사용됩니다.

### 4. 사용

1. 브라우저에서 `http://localhost:5173` 접속 — 예시 프로젝트가 보입니다.
2. 각 씬 카드에서 대사·이미지 프롬프트·빨간 원 위치(x, y, r)를 수정합니다.
3. "전체 생성" — 씬마다 Gemini로 이미지+음성을 생성합니다. 35장면이면 호출이 70번이라
   한 번의 요청으로는 타임아웃이 나므로, 백엔드가 몇 장면씩 끊어 처리하고 프런트엔드가
   `remaining`이 0이 될 때까지 이어서 호출합니다. 장면마다 저장되니 중간에 끊겨도
   진행분은 남고, 다시 눌러도 이미 끝난 장면은 건너뜁니다. 한 묶음이 통째로 실패하면
   (키 누락·쿼터 소진) 재시도를 반복하지 않고 그 자리에서 사유를 띄웁니다.
4. "영상 렌더링" — 모든 씬의 이미지가 준비되면 ffmpeg으로 하나의 mp4를 합성합니다
   (음성이 없는 씬은 3초간 무음으로 채워지므로, 일부만 생성된 상태에서도 가편집본을
   미리 볼 수 있습니다).
5. 완성된 영상을 다운로드합니다.

## 비용 예상 및 요금제 추천

이번 프로젝트 규모(대사 약 2,500자, 이미지 13장, 영상 1편) 기준입니다.
**정확한 최신 단가는 반드시 [Google AI 요금 안내](https://ai.google.dev/pricing)에서 재확인하세요** —
아래는 이 저장소를 만들 때 기준으로 추정한 값이며 예고 없이 바뀔 수 있습니다.

| 방식 | 월 구독 | 이번 프로젝트 1편당 예상 비용 | 비고 |
|---|---|---|---|
| **Gemini API (이번 선택)** | 없음 (종량제) | **약 $1~2** | 이미지+TTS 모두 한 계정. 무료 크레딧 소진 전엔 사실상 $0 |
| ElevenLabs(TTS)+Gemini(이미지) | $0~5/월 | 약 $0.6~2.6 | 한국어 음성이 더 자연스러움. 무료 1만 자/월 내에서 해결될 수도 있음 |
| Higgsfield 구독 (이전 검토, 미채택) | $49~129/월 | 구독료 전액 | MCP 도구 중심이라 이 백엔드 구조에 직접 통합 부적합 |

**추천:** 지금 구성대로 Gemini API 단일 사용을 유지하세요. 별도 구독 없이
API 키 하나로 이미지·음성을 모두 처리하고, 이번 규모 기준 영상 1편에 커피 한 잔
값 이하입니다. 트래픽이 늘어 종량제 비용이 부담되면 그때 Gemini 유료
등급(더 높은 처리량)이나 ElevenLabs 병행을 검토하세요.

## 알려진 한계 (정직 기록)

- 이 저장소를 만든 환경에는 `GEMINI_API_KEY`가 없어 **`gemini_image.py`/`gemini_tts.py`의
  실제 API 응답 형식을 라이브로 검증하지 못했습니다.** `google-genai` SDK 공식 문서 기준으로
  작성했으나, 키를 넣은 뒤 `python -m scripts.smoke_test_gemini`로 가장 먼저 확인하세요.
- `voice_m`/`voice_f`에 넣은 "Puck"/"Kore"는 Gemini TTS 프리셋 음성 이름 예시입니다.
  실제 음색(성별 느낌 포함)은 [Google AI Studio 음성 갤러리](https://ai.google.dev/gemini-api/docs/speech-generation)에서
  직접 들어보고 프로젝트별로 원하는 이름으로 바꾸세요.
- 빨간 원 클릭 강조는 실제 서비스 화면을 캡처한 것이 아니라, Gemini가 생성한
  목업 이미지 위에 지정한 정규화 좌표(0~1)로 그려집니다. 원본 튜토리얼 영상의
  실제 클릭 좌표와 픽셀 단위로 일치하지 않습니다.
- 씬 저장은 프로젝트당 JSON 파일 하나입니다(`backend/storage/<project_id>/project.json`).
  다중 사용자·동시 편집이 필요해지면 실제 DB로 교체하세요.
- `Scene` 모델에 필드를 추가했다면 **실행 중인 uvicorn을 반드시 재시작**하세요.
  구버전 모델을 들고 있는 프로세스가 프로젝트를 저장하면 새 필드가 조용히 사라집니다
  (`--reload` 없이 띄웠다면 특히). `make_free_cut`은 서버를 거치지 않아 이 문제가 없습니다.

## 테스트

```bash
cd backend && source .venv/bin/activate
python -m pytest tests/ -v
```

렌더 파이프라인 테스트는 Gemini 없이(합성 이미지+무음 오디오로) ffmpeg 합성을
검증하므로 네트워크나 API 키 없이 항상 실행할 수 있습니다.
