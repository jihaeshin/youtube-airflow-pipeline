# YouTube Airflow Pipeline

유튜브 채널/재생목록의 영상 정보를 수집하여 Supabase에 적재하는 Apache Airflow 파이프라인입니다.

## 프로젝트 개요

This project automates the process of fetching YouTube video metadata from a specific playlist and loading it into a Supabase database. The pipeline uses Apache Airflow to orchestrate the workflow.

### 파이프라인 구성
1. **YouTube API** - 영상 데이터 수집
2. **Airflow DAG** - 워크플로우 오케스트레이션
3. **Supabase** - 데이터 저장소

## 전제조건

- Python 3.8 이상
- pip 또는 conda
- Supabase 계정 (기존 프로젝트 생성 완료)
- YouTube Data API 활성화 및 API 키 발급 (기존 완료)

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/jihaeshin/youtube-airflow-pipeline.git
cd youtube-airflow-pipeline
```

### 2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\\Scripts\\activate  # Windows
```

### 3. 필수 패키지 설치

```bash
pip install -r requirements.txt
```

## 환경 설정

### 1. .env 파일 생성

`.env.example`을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

### 2. 환경변수 설정

`.env` 파일을 열어 다음 값들을 입력합니다:

#### YouTube API Configuration
```
YOUTUBE_API_KEY=AIzaSyD5prc5qQKqpXTXV_L1enxHUCnauKlUMHi
YOUTUBE_CHANNEL_ID=your_channel_id
```

#### Supabase Configuration
```
SUPABASE_URL=https://ozcrpbqxsfnxhahabnnu.supabase.co
SUPABASE_KEY=your_supabase_api_key
```

#### Airflow Configuration
```
AIRFLOW_CORE_DAGS_FOLDER=/opt/airflow/dags
AIRFLOW_CORE_PLUGINS_FOLDER=/opt/airflow/plugins
AIRFLOW_CORE_EXECUTOR=LocalExecutor
AIRFLOW_CORE_SQL_ALCHEMY_CONN=sqlite:////opt/airflow/airflow.db
```

#### Antigravity Configuration (선택사항)
```
ANTIGRAVITY_API_KEY=your_antigravity_key
ANTIGRAVITY_WORKSPACE_ID=your_workspace_id
```

## Airflow 설정 및 실행

### 1. Airflow 초기화

```bash
# Airflow 홈 디렉토리 설정
export AIRFLOW_HOME=$(pwd)

# Airflow 데이터베이스 초기화
airflow db init
```

### 2. Airflow 유저 생성 (필요 시)

```bash
airflow users create \
    --username admin \
    --firstname Admin \
    --lastname User \
    --role Admin \
    --email admin@example.com \
    --password admin
```

### 3. Airflow 웹 서버 및 스케줄러 시작

다른 터미널 창에서 각각 실행:

```bash
# 터미널 1: Airflow 웹 서버
airflow webserver --port 8080

# 터미널 2: Airflow 스케줄러
airflow scheduler
```

### 4. Airflow 웹 UI 접속

http://localhost:8080 에 접속하여 admin / admin 로 로그인합니다.

## DAG 실행

### Airflow UI를 통한 실행

1. Airflow 웹 UI에서 DAG 목록 조회
2. `youtube_playlist_to_supabase` DAG 선택
3. "Trigger DAG" 버튼 클릭
4. 실행 완료 대기

### CLI를 통한 실행

```bash
# 즉시 실행
airflow dags test youtube_playlist_to_supabase

# 또는 트리거
airflow dags trigger youtube_playlist_to_supabase
```

## 데이터 확인

### Supabase 대시보드에서 확인

1. [Supabase 대시보드](https://supabase.com/dashboard) 접속
2. 프로젝트 선택
3. "Table Editor" → `youtube_videos` 테이블 선택
4. 수집된 영상 데이터 확인

### SQL 쿼리로 확인

```sql
SELECT * FROM youtube_videos ORDER BY published_at DESC LIMIT 10;
```

## 구성

### youtube_videos 테이블 스키마

| Column | Type | 설명 |
|--------|------|------|
| id | int8 (PK) | 자동증가 ID |
| video_id | text (UNIQUE) | YouTube 영상 ID |
| title | text | 영상 제목 |
| description | text | 영상 설명 |
| channel_id | text | 채널 ID |
| channel_title | text | 채널명 |
| published_at | timestamp | 발행 날짜 |
| view_count | int4 | 조회수 |
| like_count | int4 | 좋아요 수 |
| comment_count | int4 | 댓글 수 |

## 문제해결

### Airflow 관련 에러

**문제**: `ModuleNotFoundError: No module named 'airflow'`
- **해결**: `pip install -r requirements.txt` 재실행

**문제**: 포트 8080이 이미 사용 중
- **해결**: `airflow webserver --port 8081` 처럼 다른 포트 지정

### YouTube API 에러

**문제**: `HttpError 403: The user has exceeded their YouTube API quota`
- **해결**: YouTube API 할당량 검토 및 필요시 증량 신청

### Supabase 연결 에러

**문제**: `PostgresError: permission denied for schema public`
- **해결**: Supabase API 키의 권한 확인, `youtube_videos` 테이블 존재 확인

## 라이선스

MIT
