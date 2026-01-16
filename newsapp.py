from flask import Flask, request, jsonify
import requests
from datetime import datetime
from collections import Counter
import html
import time

app = Flask(__name__)

# News API configuration
NEWS_API_KEY = 'YOUR_API_KEY_HERE'  # Get free key at https://newsapi.org
NEWS_API_URL = 'https://newsapi.org/v2/everything'

# Source bias mapping with confidence scores
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

# Stopwords to filter out meaningless common words
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

# Simple rate limiting (in-memory, resets on restart)
last_request_time = {}
RATE_LIMIT_SECONDS = 3

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NewsLens - Reveal What Each Side Chooses NOT to Emphasize</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }

        h1 {
            font-size: 3em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }

        .tagline {
            font-size: 1.2em;
            opacity: 0.9;
            margin-bottom: 5px;
        }

        .secret {
            font-size: 0.95em;
            opacity: 0.85;
            font-style: italic;
        }

        .search-box {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            margin-bottom: 30px;
        }

        .search-input {
            width: 100%;
            padding: 15px 20px;
            font-size: 1.1em;
            border: 2px solid #ddd;
            border-radius: 8px;
            margin-bottom: 15px;
            transition: border 0.3s;
        }

        .search-input:focus {
            outline: none;
            border-color: #667eea;
        }

        .search-btn {
            width: 100%;
            padding: 15px;
            font-size: 1.1em;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: transform 0.2s;
        }

        .search-btn:hover {
            transform: translateY(-2px);
        }

        .search-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        .loading {
            text-align: center;
            color: white;
            font-size: 1.3em;
            margin: 40px 0;
            display: none;
        }

        .insights-section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: none;
        }

        .insights-section h3 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.4em;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }

        .insight-card {
            padding: 15px;
            border-radius: 8px;
            background: #f8f9fa;
        }

        .insight-card.left {
            border-left: 4px solid #3b82f6;
        }

        .insight-card.center {
            border-left: 4px solid #10b981;
        }

        .insight-card.right {
            border-left: 4px solid #ef4444;
        }

        .insight-label {
            font-weight: 700;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
            opacity: 0.7;
        }

        .insight-themes {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
        }

        .theme-tag {
            background: white;
            padding: 6px 12px;
            border-radius: 15px;
            font-size: 0.85em;
            font-weight: 500;
            color: #555;
            border: 1px solid #e0e0e0;
        }

        .common-themes {
            background: #fffbeb;
            padding: 15px;
            border-radius: 8px;
            border: 2px solid #fbbf24;
        }

        .common-themes h4 {
            color: #92400e;
            margin-bottom: 10px;
            font-size: 1.1em;
        }

        .results-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 40px;
        }

        .bias-column {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .bias-column.left {
            border-top: 4px solid #3b82f6;
        }

        .bias-column.center {
            border-top: 4px solid #10b981;
        }

        .bias-column.right {
            border-top: 4px solid #ef4444;
        }

        .bias-header {
            font-size: 1.2em;
            font-weight: 700;
            margin-bottom: 5px;
            text-align: center;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .bias-confidence {
            text-align: center;
            font-size: 0.75em;
            opacity: 0.6;
            margin-bottom: 15px;
            font-style: italic;
        }

        .bias-column.left .bias-header {
            color: #3b82f6;
        }

        .bias-column.center .bias-header {
            color: #10b981;
        }

        .bias-column.right .bias-header {
            color: #ef4444;
        }

        .article {
            margin-bottom: 20px;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
        }

        .article:last-child {
            border-bottom: none;
            margin-bottom: 0;
        }

        .article-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
            line-height: 1.4;
        }

        .article-source {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }

        .article-description {
            font-size: 0.9em;
            color: #555;
            line-height: 1.5;
            margin-bottom: 10px;
        }

        .read-more {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
            font-size: 0.9em;
        }

        .read-more:hover {
            text-decoration: underline;
        }

        .no-results {
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }

        .error-message {
            background: #fee;
            color: #c33;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            display: none;
        }

        @media (max-width: 968px) {
            .results-grid, .insight-grid {
                grid-template-columns: 1fr;
            }

            h1 {
                font-size: 2em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📰 NewsLens</h1>
            <p class="tagline">See what each side chooses NOT to emphasize</p>
            <p class="secret">The secret: Media bias isn't just what they say—it's what they ignore.</p>
        </header>

        <div class="search-box">
            <input 
                type="text" 
                class="search-input" 
                id="topicInput" 
                placeholder="Enter a news topic (e.g., 'climate change', 'immigration', 'economy')..."
            >
            <button class="search-btn" id="searchBtn">Reveal Coverage Gaps</button>
        </div>

        <div class="error-message" id="errorMessage"></div>
        <div class="loading" id="loading">🔍 Analyzing what each political group emphasizes...</div>

        <div class="insights-section" id="insights">
            <h3>🧠 What Each Side Emphasizes</h3>
            <div class="insight-grid" id="insightGrid"></div>
            <div class="common-themes" id="commonThemes">
                <h4>✅ What Everyone Agrees On:</h4>
                <div class="insight-themes" id="commonTags"></div>
            </div>
        </div>

        <div class="results-grid" id="results"></div>
    </div>

    <script>
        const searchBtn = document.getElementById('searchBtn');
        const topicInput = document.getElementById('topicInput');
        const loading = document.getElementById('loading');
        const results = document.getElementById('results');
        const insights = document.getElementById('insights');
        const insightGrid = document.getElementById('insightGrid');
        const commonThemes = document.getElementById('commonThemes');
        const commonTags = document.getElementById('commonTags');
        const errorMessage = document.getElementById('errorMessage');

        searchBtn.addEventListener('click', searchNews);
        topicInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchNews();
        });

        async function searchNews() {
            const topic = topicInput.value.trim();
            
            if (!topic) {
                showError('Please enter a topic to search');
                return;
            }

            searchBtn.disabled = true;
            searchBtn.textContent = 'Analyzing...';
            loading.style.display = 'block';
            results.innerHTML = '';
            insights.style.display = 'none';
            errorMessage.style.display = 'none';

            try {
                const response = await fetch('/search', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ topic })
                });

                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Search failed');
                }

                displayResults(data);
            } catch (error) {
                showError(error.message || 'Failed to fetch news. Please try again.');
                console.error('Error:', error);
            } finally {
                searchBtn.disabled = false;
                searchBtn.textContent = 'Reveal Coverage Gaps';
                loading.style.display = 'none';
            }
        }

        function displayResults(data) {
            const { results: newsResults, themes_by_bias, common_themes, avg_confidence } = data;

            // Display insights section
            if (themes_by_bias) {
                const biases = ['left', 'center', 'right'];
                const biasLabels = {
                    left: 'Left Emphasizes',
                    center: 'Center Emphasizes',
                    right: 'Right Emphasizes'
                };

                insightGrid.innerHTML = biases.map(bias => {
                    const themes = themes_by_bias[bias] || [];
                    return `
                        <div class="insight-card ${bias}">
                            <div class="insight-label">${biasLabels[bias]}</div>
                            <div class="insight-themes">
                                ${themes.slice(0, 5).map(t => `<span class="theme-tag">${t}</span>`).join('') || '<span style="opacity: 0.5">No unique themes</span>'}
                            </div>
                        </div>
                    `;
                }).join('');

                if (common_themes && common_themes.length > 0) {
                    commonTags.innerHTML = common_themes
                        .map(theme => `<span class="theme-tag">${theme}</span>`)
                        .join('');
                } else {
                    commonThemes.style.display = 'none';
                }

                insights.style.display = 'block';
            }

            // Display articles by bias
            const biases = ['left', 'center', 'right'];
            const biasLabels = {
                left: 'Left-Leaning',
                center: 'Center/Neutral',
                right: 'Right-Leaning'
            };

            results.innerHTML = biases.map(bias => {
                const articles = newsResults[bias] || [];
                const confidence = avg_confidence[bias] || 0;
                
                const articlesHTML = articles.length > 0
                    ? articles.map(article => `
                        <div class="article">
                            <div class="article-title">${escapeHtml(article.title)}</div>
                            <div class="article-source">📰 ${escapeHtml(article.source.name)} ${article.bias_confidence ? `(${Math.round(article.bias_confidence * 100)}% confidence)` : ''}</div>
                            <div class="article-description">${escapeHtml(article.description || 'No description available')}</div>
                            <a href="${article.url}" target="_blank" rel="noopener noreferrer" class="read-more">Read full article →</a>
                        </div>
                    `).join('')
                    : '<div class="no-results">No articles found from these sources</div>';

                return `
                    <div class="bias-column ${bias}">
                        <div class="bias-header">${biasLabels[bias]}</div>
                        <div class="bias-confidence">Bias classification estimated (avg. ${Math.round(confidence * 100)}% confidence)</div>
                        ${articlesHTML}
                    </div>
                `;
            }).join('');
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        function showError(message) {
            errorMessage.textContent = message;
            errorMessage.style.display = 'block';
        }
    </script>
</body>
</html>
'''

def fetch_news(topic):
    """Fetch news from all sources at once (single API call)"""
    all_sources = ','.join(BIAS_SOURCES.keys())
    
    params = {
        'q': topic,
        'sources': all_sources,
        'language': 'en',
        'sortBy': 'relevancy',
        'pageSize': 30,  # Get more articles, sort locally
        'apiKey': NEWS_API_KEY
    }
    
    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('articles', [])
        elif response.status_code == 401:
            raise Exception('Invalid API key. Please check your News API key.')
        elif response.status_code == 426:
            raise Exception('API upgrade required. Please check your News API plan.')
        else:
            raise Exception(f'API error: {response.status_code}')
    except requests.Timeout:
        raise Exception('Request timed out. Please try again.')
    except Exception as e:
        raise Exception(f'Failed to fetch news: {str(e)}')

def categorize_articles(articles):
    """Sort articles into bias groups locally"""
    categorized = {
        'left': [],
        'center': [],
        'right': []
    }
    
    for article in articles:
        source_id = article.get('source', {}).get('id')
        if source_id in BIAS_SOURCES:
            bias_info = BIAS_SOURCES[source_id]
            bias_group = bias_info['bias']
            
            # Add bias metadata to article
            article['bias_category'] = bias_group
            article['bias_confidence'] = bias_info['confidence']
            
            categorized[bias_group].append(article)
    
    # Limit to top 3 per bias
    for bias in categorized:
        categorized[bias] = categorized[bias][:3]
    
    return categorized

def extract_themes(text):
    """Extract meaningful keywords from text"""
    words = text.lower().split()
    
    # Filter: remove stopwords, non-alpha, short words
    meaningful_words = [
        word.strip('.,!?;:()[]{}"\'-')
        for word in words
        if len(word) > 4 
        and word.lower() not in STOPWORDS
        and word.isalpha()
    ]
    
    return meaningful_words

def analyze_themes_by_bias(categorized_articles):
    """Find what each bias group emphasizes"""
    themes_by_bias = {}
    
    for bias, articles in categorized_articles.items():
        all_themes = []
        
        for article in articles:
            # Extract from title AND description
            title = article.get('title', '')
            description = article.get('description', '')
            
            all_themes.extend(extract_themes(title))
            all_themes.extend(extract_themes(description))
        
        # Count and sort
        theme_counts = Counter(all_themes)
        top_themes = [theme for theme, count in theme_counts.most_common(10)]
        
        themes_by_bias[bias] = top_themes
    
    return themes_by_bias

def find_common_themes(themes_by_bias):
    """Find themes that appear across ALL bias groups"""
    if not all(themes_by_bias.values()):
        return []
    
    # Get intersection of all bias groups
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
    # Simple rate limiting
    client_ip = request.remote_addr
    current_time = time.time()
    
    if client_ip in last_request_time:
        time_since_last = current_time - last_request_time[client_ip]
        if time_since_last < RATE_LIMIT_SECONDS:
            return jsonify({'error': f'Please wait {RATE_LIMIT_SECONDS - int(time_since_last)} seconds before searching again'}), 429
    
    last_request_time[client_ip] = current_time
    
    topic = request.json.get('topic', '').strip()
    
    if not topic:
        return jsonify({'error': 'Please enter a topic'}), 400
    
    if len(topic) > 100:
        return jsonify({'error': 'Topic is too long (max 100 characters)'}), 400
    
    try:
        # Fetch all articles in ONE API call
        articles = fetch_news(topic)
        
        if not articles:
            return jsonify({'error': 'No articles found. Try a different topic.'}), 404
        
        # Sort locally by bias
        categorized = categorize_articles(articles)
        
        # Analyze themes per bias
        themes_by_bias = analyze_themes_by_bias(categorized)
        
        # Find common themes
        common_themes = find_common_themes(themes_by_bias)
        
        # Calculate average confidence per bias group
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
    print("🚀 NewsLens starting...")
    print("📌 Remember to add your News API key on line 10!")
    print("🌐 Open http://127.0.0.1:5000 in your browser")
    app.run(debug=True, port=5000)