import asyncio
import asyncpraw
from flask import Flask, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from aiohttp import ClientTimeout
from environs import Env
import random

env = Env()
env.read_env()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///images.db'  # 使用SQLite数据库
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义Image模型
class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)

# 创建数据库表
with app.app_context():
    db.create_all()

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
        
        if all_posts:
            post = random.choice(all_posts)
            preview_image_url = None

            if hasattr(post, 'preview') and post.preview and 'images' in post.preview:
                images = post.preview['images']
                if images:
                    preview_image_url = images[0]['source']['url']
            
            if preview_image_url:
                # 存储到数据库
                new_image = Image(url=preview_image_url)
                db.session.add(new_image)
                db.session.commit()
                hot_posts.append(preview_image_url)

    return hot_posts

@app.route('/')
def index():
    images = Image.query.all()  # 查询所有图片
    return render_template('index.html', images=[img.url for img in images])

@app.route('/fetch-posts')
async def fetch_posts():
    subreddits = env.list('SUBREDDITS')
    random_subreddits = get_random_subreddits(subreddits)
    new_images = await get_hot_posts(random_subreddits)
    return jsonify(new_images)

if __name__ == "__main__":
    asyncio.run(app.run(debug=True))
