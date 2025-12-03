import os
from flask import Flask, render_template, abort
import markdown

app = Flask(__name__)

# CONFIGURATION
CONTENT_DIR = 'content'

@app.route('/')
def index():
    # List all markdown files in the folder to make an index page
    files = [f for f in os.listdir(CONTENT_DIR) if f.endswith('.md')]
    posts = []
    for f in files:
        # Minimal parsing to get a title (assumes first line is # Title)
        with open(os.path.join(CONTENT_DIR, f), 'r') as file_handle:
            first_line = file_handle.readline().strip().replace('#', '').strip()
            slug = f.replace('.md', '')
            posts.append({'title': first_line or slug, 'slug': slug})
    return render_template('index.html', posts=posts)

@app.route('/<slug>')
def page(slug):
    filepath = os.path.join(CONTENT_DIR, f"{slug}.md")
    if not os.path.exists(filepath):
        abort(404)
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Convert Markdown to HTML with R/Python syntax highlighting
    html_content = markdown.markdown(content, extensions=['fenced_code', 'codehilite'])
    
    return render_template('post.html', content=html_content, title=slug)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)