import os
from flask import Flask, render_template, abort, send_from_directory
import markdown
from markdown.extensions.toc import TocExtension

app = Flask(__name__)

# CONFIGURATION
CONTENT_DIR = 'content'
CITATIONS_DIR = 'citations'

# CATEGORY META (No changes here)
CATEGORY_META = {
    'publications': {
        'title': 'Publications', 
        'desc': 'Formal frameworks, technical papers, and finished studies.'
    },
    'observations': {
        'title': 'Working Papers', 
        'desc': 'Hypotheses, observations, and ongoing field notes.'
    },
    'research': {
        'title': 'Resources', 
        'desc': 'Curated signals, external literature and significant datasets.'
    },
    'commentary': {
        'title': 'Commentary', 
        'desc': 'Critical analysis, essays, and dialectics on the field and relevant subject matters.'
    },
    'tools': {
        'title': 'Tools', 
        'desc': 'Software, scripts, tools, algorithms, and computational utilities.'
    }
}

def get_categories():
    """Returns a list of active categories found in the content dir."""
    cats = []
    if not os.path.exists(CONTENT_DIR):
        return []
    for slug, meta in CATEGORY_META.items():
        if os.path.isdir(os.path.join(CONTENT_DIR, slug)):
            cats.append({'slug': slug, 'title': meta['title'], 'desc': meta['desc']})
    return cats

def extract_metadata(filepath):
    """
    Reads a markdown file and extracts:
    1. Title (First line)
    2. Summary (First non-empty line after title) - RENDERED AS HTML
    """
    title = "Untitled"
    summary = ""
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
            # 1. Get Title (First Line)
            if lines:
                title = lines[0].replace('#', '').strip()
            
            # 2. Get Summary (Scan for first text block)
            for line in lines[1:]:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith('#'):
                    # Truncate raw text first to prevent huge blobs
                    if len(clean_line) > 200: 
                        clean_line = clean_line[:200] + "..."
                    
                    # RENDER MARKDOWN TO HTML
                    # We use the module-level markdown function for a quick convert
                    html_snippet = markdown.markdown(clean_line)
                    
                    # CRITICAL: Strip the <p> tags so it fits your template's styling
                    if html_snippet.startswith('<p>') and html_snippet.endswith('</p>'):
                        html_snippet = html_snippet[3:-4]
                    
                    summary = html_snippet
                    break
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")
        
    return title, summary

def get_all_posts():
    """Scans ALL category folders to build the Homepage Feed."""
    all_posts = []
    for cat_slug in CATEGORY_META:
        cat_path = os.path.join(CONTENT_DIR, cat_slug)
        if os.path.exists(cat_path):
            for f in os.listdir(cat_path):
                if f.endswith('.md'):
                    slug = f.replace('.md', '')
                    title, summary = extract_metadata(os.path.join(cat_path, f))
                    
                    all_posts.append({
                        'title': title,
                        'summary': summary, # NEW FIELD
                        'slug': slug,
                        'category_slug': cat_slug,
                        'category_title': CATEGORY_META[cat_slug]['title']
                    })
    return all_posts

def get_posts_in_category(category_slug):
    """Get posts only for a specific category."""
    cat_path = os.path.join(CONTENT_DIR, category_slug)
    if not os.path.exists(cat_path):
        return []
    
    posts = []
    for f in os.listdir(cat_path):
        if f.endswith('.md'):
            slug = f.replace('.md', '')
            title, summary = extract_metadata(os.path.join(cat_path, f))
            
            posts.append({
                'title': title, 
                'summary': summary, 
                'slug': slug, 
                'category_slug': category_slug
            })
    return posts


@app.context_processor
def inject_globals():
    return dict(categories=get_categories())

@app.route('/')
def index():
    posts = get_all_posts()
    return render_template('index.html', posts=posts)

@app.route('/<category>')
def category_index(category):
    if category not in CATEGORY_META:
        abort(404)
    posts = get_posts_in_category(category)
    meta = CATEGORY_META[category].copy()
    meta['slug'] = category
    return render_template('category.html', posts=posts, meta=meta)

@app.route('/citations/<category>/<filename>')
def citation(category, filename):
    # Validate category
    if category not in CATEGORY_META:
        abort(404)

    citation_path = os.path.join(CITATIONS_DIR, category)

    if not os.path.exists(os.path.join(citation_path, filename)):
        abort(404)

    return send_from_directory(
        citation_path,
        filename,
        as_attachment=True
    )

@app.route('/<category>/<slug>')
def post(category, slug):
    filepath = os.path.join(CONTENT_DIR, category, f"{slug}.md")
    if not os.path.exists(filepath):
        abort(404)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    md = markdown.Markdown(
        extensions=[
            'fenced_code', 
            'codehilite',
            'tables', 
            'attr_list', 
            'footnotes', 
            'admonition', 
            'def_list', 
            'abbr', 
            'pymdownx.tasklist',
            'pymdownx.betterem',
            'pymdownx.tilde', 
            TocExtension(baselevel=2)
        ]
        #,
        #extension_configs={
        #    'pymdownx.tasklist': {
        #        'clickable_checkbox': True
        #    }
        #}
    )
    html_content = md.convert(text)
    
    return render_template('post.html', content=html_content, title=slug, toc=md.toc, category=category)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)