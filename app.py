import asyncio
import asyncpraw
from flask import Flask, jsonify, render_template
from aiohttp import ClientTimeout
from environs import Env
import random
import os

env = Env()
env.read_env()

app = Flask(__name__)

# 存储已发送的图片
sent_images = []

def get_random_subreddits(subreddits):
    return random.sample(subreddits, env.int('SUBREDDITS_COUNT'))

async def get_hot_posts(subreddits, limit=200):
    reddit = asyncpraw.Reddit(
        client_id=env.str('REDDIT_CLIENT_ID'),
        client_secret=env.str('REDDIT_CLIENT_SECRET'),
        user_agent=env.str('REDDIT_USER_AGENT'),
        requestor_kwargs={'timeout': ClientTimeout(total=30)}  
    )
    
    hot_posts = []
    for subreddit in subreddits:
        subreddit_instance = await reddit.subreddit(subreddit)
        all_posts = []
        async for post in subreddit_instance.hot(limit=limit):
            all_posts.append(post)
        
        # 随机选择一条帖子
        if all_posts:
            post = random.choice(all_posts)
            title = post.title
            preview_image_url = None

            if hasattr(post, 'preview') and post.preview and 'images' in post.preview:
                images = post.preview['images']
                if images:
                    preview_image_url = images[0]['source']['url']
            
            if preview_image_url:
                sent_images.append(preview_image_url)

    return hot_posts

@app.route('/')
def index():
    return render_template('index.html', images=sent_images)

@app.route('/fetch-posts')
async def fetch_posts():
    subreddits = env.list('SUBREDDITS')
    random_subreddits = get_random_subreddits(subreddits)
    await get_hot_posts(random_subreddits)
    return jsonify(sent_images)

if __name__ == "__main__":
    asyncio.run(app.run(debug=True))
