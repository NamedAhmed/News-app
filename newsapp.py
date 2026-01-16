from flask import Flask, request, jsonify
import requests
from datetime import datetime
from collections import Counter
import html
import time

app = Flask(__name__)

NEWS_API_KEY = '9ea183f30e2e486d989868fe3ca9470c'
NEWS_API_URL = 'https://newsapi.org/v2/everything'

BIAS_SOURCES = {
    'fox-news': {'bias': 'right', 'confidence': 0.9},
    'breitbart-news': {'bias': 'right', 'confidence': 0.95},
    'national-review': {'bias': 'right', 'confidence': 0.85},
    'the-washington-times': {'bias': 'right', 'confidence': 0.8},
    
    'cnn': {'bias': 'left', 'confidence': 0.85},
    'msnbc': {'bias': 'left', 'confidence': 0.9},
    'the-huffington-post': {'bias': 'left', 'confidence': 0.9},
    'the-guardian-us': {'bias': 'left', 'confidence': 0.8},
    'politico': {'bias': 'left', 'confidence': 0.7},
    
    'bbc-news': {'bias': 'center', 'confidence': 0.9},
    'reuters': {'bias': 'center', 'confidence': 0.95},
    'associated-press': {'bias': 'center', 'confidence': 0.95},
    'npr': {'bias': 'center', 'confidence': 0.8},
    'the-wall-street-journal': {'bias': 'center', 'confidence': 0.75}
}

STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
    'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
    'should', 'may', 'might', 'can', 'about', 'after', 'their', 'there',
    'this', 'that', 'these', 'those', 'it', 'its', 'they', 'them', 'what',
    'which', 'who', 'when', 'where', 'why', 'how', 'all', 'each', 'every',
    'both', 'few', 'more', 'most', 'other', 'some', 'such', 'only', 'own',
    'same', 'so', 'than', 'too', 'very', 'just', 'says', 'said'
}

last_request_time = {}
RATE_LIMIT_SECONDS = 3

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NewsLens</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: Georgia, 'Times New Roman', serif;
            background: #f5f5f0;
            color: #2a2a2a;
            line-height: 1.6;
            padding: 0;
        }

        .header-bar {
            background: #1a1a1a;
            border-bottom: 3px solid #c41e3a;
            padding: 12px 0;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }

        .site-title {
            color: #fff;
            font-size: 2.2em;
            font-weight: 700;
            letter-spacing: -0.5px;
            text-align: center;
        }

        .subtitle {
            color: #ccc;
            font-size: 0.95em;
            text-align: center;
            margin-top: 5px;
            font-style: italic;
            font-family: Arial, sans-serif;
        }

        .content-wrapper {
            background: white;
            margin: 30px auto;
            max-width: 1200px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }

        .search-area {
            padding: 35px 40px;
            border-bottom: 1px solid #ddd;
        }

        .search-label {
            font-size: 1.1em;
            color: #333;
            margin-bottom: 12px;
            font-weight: 600;
        }

        .search-input {
            width: 100%;
            padding: 12px 15px;
            font-size: 1em;
            border: 2px solid #ccc;
            font-family: Arial, sans-serif;
            margin-bottom: 12px;
        }

        .search-input:focus {
            outline: none;
            border-color: #666;
        }

        .search-btn {
            padding: 12px 30px;
            font-size: 1em;
            background: #1a1a1a;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            font-family: Arial, sans-serif;
        }

        .search-btn:hover {
            background: #333;
        }

        .search-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .status-msg {
            padding: 20px 40px;
            text-align: center;
            font-family: Arial, sans-serif;
            color: #666;
            display: none;
        }

        .error-box {
            background: #fff5f5;
            border: 1px solid #feb2b2;
            color: #c53030;
            padding: 15px 20px;
            margin: 20px 40px;
            display: none;
            font-family: Arial, sans-serif;
        }

        .themes-section {
            padding: 30px 40px;
            border-bottom: 1px solid #ddd;
            display: none;
        }

        .section-header {
            font-size: 1.4em;
            margin-bottom: 20px;
            color: #1a1a1a;
            font-weight: 700;
        }

        .themes-row {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
        }

        .theme-box {
            flex: 1;
            padding: 20px;
            background: #fafafa;
            border-left: 3px solid #999;
        }

        .theme-box.left { border-left-color: #4299e1; }
        .theme-box.center { border-left-color: #48bb78; }
        .theme-box.right { border-left-color: #f56565; }

        .theme-title {
            font-size: 0.85em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 12px;
            color: #666;
            font-family: Arial, sans-serif;
        }

        .keyword-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .keyword {
            background: white;
            padding: 5px 12px;
            font-size: 0.9em;
            border: 1px solid #ddd;
            color: #444;
            font-family: Arial, sans-serif;
        }

        .consensus-box {
            background: #fffaf0;
            padding: 20px;
            border: 1px solid #fbd38d;
        }

        .consensus-title {
            font-weight: 700;
            margin-bottom: 10px;
            color: #744210;
            font-family: Arial, sans-serif;
        }

        .articles-grid {
            display: flex;
            border-top: 1px solid #ddd;
        }

        .column {
            flex: 1;
            padding: 30px 25px;
            border-right: 1px solid #ddd;
        }

        .column:last-child {
            border-right: none;
        }

        .column-header {
            font-size: 1.1em;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
            padding-bottom: 8px;
            border-bottom: 2px solid #ddd;
            font-family: Arial, sans-serif;
        }

        .column.left .column-header { 
            color: #2c5282;
            border-bottom-color: #4299e1;
        }
        .column.center .column-header { 
            color: #276749;
            border-bottom-color: #48bb78;
        }
        .column.right .column-header { 
            color: #9b2c2c;
            border-bottom-color: #f56565;
        }

        .meta-info {
            font-size: 0.8em;
            color: #999;
            margin-bottom: 20px;
            font-family: Arial, sans-serif;
        }

        .article-item {
            margin-bottom: 25px;
            padding-bottom: 25px;
            border-bottom: 1px solid #eee;
        }

        .article-item:last-child {
            border-bottom: none;
        }

        .article-headline {
            font-size: 1.05em;
            font-weight: 600;
            margin-bottom: 8px;
            line-height: 1.4;
            color: #1a1a1a;
        }

        .article-source {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
            font-family: Arial, sans-serif;
        }

        .article-text {
            font-size: 0.95em;
            color: #444;
            margin-bottom: 10px;
            line-height: 1.5;
        }

        .article-link {
            color: #1a1a1a;
            text-decoration: underline;
            font-size: 0.9em;
            font-family: Arial, sans-serif;
        }

        .empty-state {
            text-align: center;
            padding: 30px;
            color: #999;
            font-style: italic;
        }

        @media (max-width: 900px) {
            .themes-row, .articles-grid {
                flex-direction: column;
            }

            .column {
                border-right: none;
                border-bottom: 1px solid #ddd;
            }

            .column:last-child {
                border-bottom: none;
            }
        }
    </style>
</head>
<body>
    <div class="header-bar">
        <div class="container">
            <h1 class="site-title">NewsLens</h1>
            <p class="subtitle">Compare news coverage across the political spectrum</p>
        </div>
    </div>

    <div class="content-wrapper">
        <div class="search-area">
            <div class="search-label">Search by topic:</div>
            <input 
                type="text" 
                class="search-input" 
                id="topicInput" 
                placeholder="e.g., climate change, healthcare, economy"
            >
            <button class="search-btn" id="searchBtn">Search</button>
        </div>

        <div class="error-box" id="errorBox"></div>
        <div class="status-msg" id="statusMsg">Searching...</div>

        <div class="themes-section" id="themesSection">
            <div class="section-header">Key Topics by Source</div>
            <div class="themes-row" id="themesRow"></div>
            <div class="consensus-box" id="consensusBox">
                <div class="consensus-title">Common Ground:</div>
                <div class="keyword-list" id="consensusList"></div>
            </div>
        </div>

        <div class="articles-grid" id="articlesGrid"></div>
    </div>

    <script>
        const searchBtn = document.getElementById('searchBtn');
        const topicInput = document.getElementById('topicInput');
        const statusMsg = document.getElementById('statusMsg');
        const errorBox = document.getElementById('errorBox');
        const themesSection = document.getElementById('themesSection');
        const themesRow = document.getElementById('themesRow');
        const consensusBox = document.getElementById('consensusBox');
        const consensusList = document.getElementById('consensusList');
        const articlesGrid = document.getElementById('articlesGrid');

        searchBtn.addEventListener('click', doSearch);
        topicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') doSearch();
        });

        async function doSearch() {
            const topic = topicInput.value.trim();
            
            if (!topic) {
                showError('Please enter a search term');
                return;
            }

            searchBtn.disabled = true;
            searchBtn.textContent = 'Searching...';
            statusMsg.style.display = 'block';
            articlesGrid.innerHTML = '';
            themesSection.style.display = 'none';
            errorBox.style.display = 'none';

            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ topic })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Search failed');
                }

                showResults(data);
            } catch (error) {
                showError(error.message || 'Something went wrong. Please try again.');
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Search';
                statusMsg.style.display = 'none';
            }
        }

        function showResults(data) {
            const { results, themes_by_bias, common_themes, avg_confidence } = data;

            if (themes_by_bias) {
                const groups = ['left', 'center', 'right'];
                const labels = {
                    left: 'Left-Leaning Sources',
                    center: 'Center Sources',
                    right: 'Right-Leaning Sources'
                };

                themesRow.innerHTML = groups.map(group => {
                    const themes = themes_by_bias[group] || [];
                    return `
                        <div class="theme-box ${group}">
                            <div class="theme-title">${labels[group]}</div>
                            <div class="keyword-list">
                                ${themes.slice(0, 6).map(t => `<span class="keyword">${t}</span>`).join('') || '<span style="color: #999">None found</span>'}
                            </div>
                        </div>
                    `;
                }).join('');

                if (common_themes && common_themes.length > 0) {
                    consensusList.innerHTML = common_themes.map(t => `<span class="keyword">${t}</span>`).join('');
                } else {
                    consensusBox.style.display = 'none';
                }

                themesSection.style.display = 'block';
            }

            const groups = ['left', 'center', 'right'];
            const labels = {
                left: 'Left-Leaning',
                center: 'Center',
                right: 'Right-Leaning'
            };

            articlesGrid.innerHTML = groups.map(group => {
                const articles = results[group] || [];
                const conf = avg_confidence[group] || 0;
                
                const articlesHTML = articles.length > 0
                    ? articles.map(a => `
                        <div class="article-item">
                            <div class="article-headline">${esc(a.title)}</div>
                            <div class="article-source">${esc(a.source.name)}</div>
                            <div class="article-text">${esc(a.description || 'No description available')}</div>
                            <a href="${a.url}" target="_blank" class="article-link">Read more</a>
                        </div>
                    `).join('')
                    : '<div class="empty-state">No articles found</div>';

                return `
                    <div class="column ${group}">
                        <div class="column-header">${labels[group]}</div>
                        <div class="meta-info">${articles.length} article${articles.length !== 1 ? 's' : ''}</div>
                        ${articlesHTML}
                    </div>
                `;
            }).join('');
        }

        function esc(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showError(msg) {
            errorBox.textContent = msg;
            errorBox.style.display = 'block';
        }
    </script>
</body>
</html>
'''

def fetch_news(topic):
    all_sources = ','.join(BIAS_SOURCES.keys())
    
    params = {
        'q': topic,
        'sources': all_sources,
        'language': 'en',
        'sortBy': 'relevancy',
        'pageSize': 30,
        'apiKey': NEWS_API_KEY
    }
    
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
        elif response.status_code == 401:
            raise Exception('Invalid API key')
        elif response.status_code == 426:
            raise Exception('API upgrade required')
        else:
            raise Exception(f'API error: {response.status_code}')
    except requests.Timeout:
        raise Exception('Request timed out')
    except Exception as e:
        raise Exception(f'Failed to fetch news: {str(e)}')

def categorize_articles(articles):
    categorized = {'left': [], 'center': [], 'right': []}
    
    for article in articles:
        source_id = article.get('source', {}).get('id')
        if source_id in BIAS_SOURCES:
            bias_info = BIAS_SOURCES[source_id]
            bias_group = bias_info['bias']
            
            article['bias_category'] = bias_group
            article['bias_confidence'] = bias_info['confidence']
            
            categorized[bias_group].append(article)
    
    for bias in categorized:
        categorized[bias] = categorized[bias][:3]
    
    return categorized

def extract_themes(text):
    words = text.lower().split()
    
    meaningful_words = [
        word.strip('.,!?;:()[]{}"\'-')
        for word in words
        if len(word) > 4 
        and word.lower() not in STOPWORDS
        and word.isalpha()
    ]
    
    return meaningful_words

def analyze_themes_by_bias(categorized_articles):
    themes_by_bias = {}
    
    for bias, articles in categorized_articles.items():
        all_themes = []
        
        for article in articles:
            title = article.get('title', '')
            description = article.get('description', '')
            
            all_themes.extend(extract_themes(title))
            all_themes.extend(extract_themes(description))
        
        theme_counts = Counter(all_themes)
        top_themes = [theme for theme, count in theme_counts.most_common(10)]
        
        themes_by_bias[bias] = top_themes
    
    return themes_by_bias

def find_common_themes(themes_by_bias):
    if not all(themes_by_bias.values()):
        return []
    
    left_set = set(themes_by_bias.get('left', []))
    center_set = set(themes_by_bias.get('center', []))
    right_set = set(themes_by_bias.get('right', []))
    
    common = left_set & center_set & right_set
    
    return list(common)[:5]

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/search', methods=['POST'])
def search():
    client_ip = request.remote_addr
    current_time = time.time()
    
    if client_ip in last_request_time:
        time_since_last = current_time - last_request_time[client_ip]
        if time_since_last < RATE_LIMIT_SECONDS:
            return jsonify({'error': f'Please wait {RATE_LIMIT_SECONDS - int(time_since_last)} seconds'}), 429
    
    last_request_time[client_ip] = current_time
    
    topic = request.json.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Please enter a topic'}), 400
    
    if len(topic) > 100:
        return jsonify({'error': 'Topic too long'}), 400
    
    try:
        articles = fetch_news(topic)
        
        if not articles:
            return jsonify({'error': 'No articles found'}), 404
        
        categorized = categorize_articles(articles)
        themes_by_bias = analyze_themes_by_bias(categorized)
        common_themes = find_common_themes(themes_by_bias)
        
        avg_confidence = {}
        for bias, articles in categorized.items():
            if articles:
                avg_confidence[bias] = sum(a.get('bias_confidence', 0) for a in articles) / len(articles)
            else:
                avg_confidence[bias] = 0
        
        return jsonify({
            'results': categorized,
            'themes_by_bias': themes_by_bias,
            'common_themes': common_themes,
            'avg_confidence': avg_confidence,
            'topic': html.escape(topic),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting NewsLens...")
    print("Add your API key on line 10")
    print("Open http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
