import gradio as gr
import requests
import pandas as pd
from utils import BACKEND_URL

def load_posts(token):
    if not token:
        return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/community/posts", headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df = df[["id", "author", "content", "timestamp", "likes", "comment_count", "user_liked"]]
                df.columns = ["ID", "Author", "Content", "Time", "❤️", "💬", "Liked"]
                return df
    except:
        pass
    return pd.DataFrame()

def create_post(content, token):
    if not content.strip() or not token:
        return load_posts(token)
    try:
        res = requests.post(f"{BACKEND_URL}/community/posts",
                            json={"content": content.strip()},
                            headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("✅ Post created!")
        else:
            gr.Warning("❌ Failed to create post")
    except:
        pass
    return load_posts(token)

def delete_post(post_id, token):
    if not post_id or not token:
        return load_posts(token)
    try:
        res = requests.delete(f"{BACKEND_URL}/community/posts/{int(post_id)}",
                              headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            gr.Info("🗑️ Post deleted")
        else:
            gr.Warning("❌ Not allowed")
    except:
        pass
    return load_posts(token)

def like_post(post_id, token):
    if not post_id or not token:
        return load_posts(token)
    try:
        res = requests.post(f"{BACKEND_URL}/community/posts/{int(post_id)}/like",
                            headers={"Authorization": f"Bearer {token}"})
    except:
        pass
    return load_posts(token)

def load_comments_for_post(post_id, token):
    if not post_id or not token:
        return pd.DataFrame()
    try:
        res = requests.get(f"{BACKEND_URL}/community/posts/{int(post_id)}/comments",
                           headers={"Authorization": f"Bearer {token}"})
        if res.status_code == 200:
            data = res.json()
            if data:
                df = pd.DataFrame(data)
                df = df[["id", "author", "content", "timestamp", "likes", "user_liked"]]
                df.columns = ["ID", "Author", "Comment", "Time", "❤️", "Liked"]
                return df
    except:
        pass
    return pd.DataFrame()

def add_comment_to_post(post_id, content, token):
    if not post_id or not content.strip() or not token:
        return load_comments_for_post(post_id, token)
    try:
        res = requests.post(f"{BACKEND_URL}/community/posts/{int(post_id)}/comments",
                            json={"content": content.strip()},
                            headers={"Authorization": f"Bearer {token}"})
    except:
        pass
    return load_comments_for_post(post_id, token)

def delete_comment(comment_id, post_id, token):
    if not comment_id or not token:
        return load_comments_for_post(post_id, token)
    try:
        res = requests.delete(f"{BACKEND_URL}/community/comments/{int(comment_id)}",
                              headers={"Authorization": f"Bearer {token}"})
    except:
        pass
    return load_comments_for_post(post_id, token)

def like_comment(comment_id, post_id, token):
    if not comment_id or not token:
        return load_comments_for_post(post_id, token)
    try:
        res = requests.post(f"{BACKEND_URL}/community/comments/{int(comment_id)}/like",
                            headers={"Authorization": f"Bearer {token}"})
    except:
        pass
    return load_comments_for_post(post_id, token)