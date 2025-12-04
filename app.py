import os
from flask import Flask, render_template, abort
import markdown

app = Flask(__name__)

# CONFIGURATION
CONTENT_DIR = 'content'

def get_posts():
    """Helper function to get list of posts."""
    try:
        files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    except FileNotFoundError:
        return []
    
    posts = []
    for f in files:
        # Use utf-8 to prevent Windows crash
        with open(os.path.join(CONTENT_DIR, f), 'r', encoding='utf-8') as file_handle:
            first_line = file_handle.readline().strip().replace('#', '').strip()
            slug = f.replace('.md', '')
            posts.append({'title': first_line or slug, 'slug': slug})
    return posts

# AUTOMATION: This runs before every template render
@app.context_processor
def inject_posts():
    return dict(sidebar_posts=get_posts())

@app.route('/')
def index():
    # We don't need to pass posts here anymore, the context_processor does it
    return render_template('index.html')

@app.route('/<slug>')
def page(slug):
    filepath = os.path.join(CONTENT_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        abort(404)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    html_content = markdown.markdown(content, extensions=['fenced_code', 'codehilite'])
    
    return render_template('post.html', content=html_content, title=slug)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)