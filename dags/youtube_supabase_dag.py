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
CHANNEL_ID = os.getenv('YOUTUBE_CHANNEL_ID', 'UCsgM_PJxQ-k4gHdaYUE4E-A')  # 무한도전 채널 ID

# Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_youtube_videos(**context):
    """Fetch videos from YouTube channel"""
    print(f"Fetching videos from channel: {CHANNEL_ID}")
    
    youtube_url = "https://www.googleapis.com/youtube/v3/search"
    
    params = {
        "key": YOUTUBE_API_KEY,
        "channelId": CHANNEL_ID,
        "part": "snippet",
        "maxResults": 50,
        "order": "date",
        "type": "video"
    }
    
    response = requests.get(youtube_url, params=params)
    data = response.json()
    
    videos = []
    for item in data.get('items', []):
        video_id = item['id']['videoId']
        snippet = item['snippet']
        videos.append({
            'video_id': video_id,
            'title': snippet['title'],
            'description': snippet['description'],
            'channel_id': snippet['channelId'],
            'channel_title': snippet['channelTitle'],
            'thumbnail_url': snippet['thumbnails']['default']['url'],
            'video_url': f"https://www.youtube.com/watch?v={video_id}",
            'published_at': snippet['publishedAt']
        })
    
    # Push to XCom for next task
    context['task_instance'].xcom_push(key='videos', value=videos)
    print(f"Fetched {len(videos)} videos")
    return len(videos)

def load_to_supabase(**context):
    """Load videos to Supabase"""
    # Get videos from previous task
    videos = context['task_instance'].xcom_pull(task_ids='fetch_youtube_videos', key='videos')
    
    if not videos:
        print("No videos to load")
        return
    
    print(f"Loading {len(videos)} videos to Supabase")
    
    for video in videos:
        try:
            # Check if video already exists
            existing = supabase.table('youtube_videos').select('*').eq('video_id', video['video_id']).execute()
            
            if not existing.data:
                supabase.table('youtube_videos').insert(video).execute()
                print(f"✅ Inserted: {video['title']}")
            else:
                print(f"⏭️  Already exists: {video['title']}")
        except Exception as e:
            print(f"❌ Error inserting {video['title']}: {str(e)}")
    
    print(f"Completed loading {len(videos)} videos to Supabase")

# Define DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'youtube_to_supabase',
    default_args=default_args,
    description='Fetch YouTube videos and load to Supabase',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
)

# Tasks
fetch_task = PythonOperator(
    task_id='fetch_youtube_videos',
    python_callable=fetch_youtube_videos,
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
