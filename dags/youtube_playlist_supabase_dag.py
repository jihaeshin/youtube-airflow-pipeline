from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
import requests
from supabase import create_client, Client
import os

# Environment Variables
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Playlist ID 무한도전 재생목록
PLAYLIST_ID = os.getenv('YOUTUBE_PLAYLIST_ID', 'PL1FPDVeoyuPfSTmRCEjr2GGOTnNqE_mnn')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_playlist_videos(**context):
    """
    YouTube 재생목록에서 모든 영상 메타데이터 추출
    API 페이냈 쉜옄
    """
    print(f"\n[LOG] 재생목록 ID: {PLAYLIST_ID} - 데이터 추출 중...")
    
    youtube_url = "https://www.googleapis.com/youtube/v3/playlistItems"
    
    videos = []
    next_page_token = None
    page_count = 0
    
    while True:
        page_count += 1
        print(f"[LOG] {page_count} 페이지 요청 중...")
        
        params = {
            "key": YOUTUBE_API_KEY,
            "playlistId": PLAYLIST_ID,
            "part": "snippet,contentDetails",
            "maxResults": 50,
            "pageToken": next_page_token
        }
        
        try:
            response = requests.get(youtube_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data:
                print(f"[ERROR] YouTube API 에러: {data['error']}")
                break
            
            for item in data.get('items', []):
                try:
                    video_id = item['contentDetails']['videoId']
                    snippet = item['snippet']
                    
                    video_data = {
                        'video_id': video_id,
                        'title': snippet['title'],
                        'description': snippet['description'],
                        'channel_id': snippet['channelId'],
                        'channel_title': snippet['channelTitle'],
                        'thumbnail_url': snippet['thumbnails']['default']['url'],
                        'video_url': f"https://www.youtube.com/watch?v={video_id}",
                        'published_at': snippet['publishedAt'],
                        'playlist_id': PLAYLIST_ID,
                        'position': item['snippet']['position']
                    }
                    videos.append(video_data)
                except KeyError as e:
                    print(f"[WARN] 데이터 파싱 실패: {e}")
                    continue
            
            print(f"[LOG] {len(data.get('items', []))} 개 영상 추출")
            
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
                
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] API 식생 실패: {e}")
            break
    
    context['task_instance'].xcom_push(key='videos', value=videos)
    print(f"[SUCCESS] 총 {len(videos)} 개 영상 추출")
    return len(videos)

def load_to_supabase(**context):
    """
    추출된 데이터를 Supabase로 로드
    """
    videos = context['task_instance'].xcom_pull(task_ids='fetch_playlist_videos', key='videos')
    
    if not videos:
        print("[WARN] 로드할 데이터가 없습니다")
        return
    
    print(f"\n[LOG] Supabase로 {len(videos)} 개 데이터 로드 중...")
    
    inserted = 0
    skipped = 0
    errors = 0
    
    for idx, video in enumerate(videos, 1):
        try:
            # 중복 메타데이터 여부 확인
            existing = supabase.table('youtube_videos').select('*').eq('video_id', video['video_id']).execute()
            
            if not existing.data:
                supabase.table('youtube_videos').insert(video).execute()
                inserted += 1
                print(f"[{idx}] ✅ 등록: {video['title'][:50]}")
            else:
                skipped += 1
                print(f"[{idx}] ⏭️  이미 존재: {video['title'][:50]}")
                
        except Exception as e:
            errors += 1
            print(f"[{idx}] ❌ 로드 실패: {video['title'][:50]} - {str(e)[:50]}")
    
    print(f"\n[SUMMARY] 등록: {inserted}, 스킵: {skipped}, 실패: {errors}")

# DAG 정의
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'youtube_playlist_to_supabase',
    default_args=default_args,
    description='YouTube 재생목록 데이터 추출 및 Supabase 로드',
    schedule_interval='0 0 * * 0',  # 매 주 일식
    catchup=False,
)

# Tasks
fetch_task = PythonOperator(
    task_id='fetch_playlist_videos',
    python_callable=fetch_playlist_videos,
    provide_context=True,
    dag=dag,
)

load_task = PythonOperator(
    task_id='load_to_supabase',
    python_callable=load_to_supabase,
    provide_context=True,
    dag=dag,
)

# Dependencies
fetch_task >> load_task
