# NewsLens - Bias-Comparing News Aggregator

**"See the full picture. Break your echo chamber."**

## Product Vision
NewsLens helps news consumers escape their filter bubbles by showing the same story from left-leaning, center, and right-leaning sources side-by-side—so they can see what all sources agree on vs. where opinions diverge.

## Target User
Anyone who wants to understand how different news outlets cover the same events. Perfect for students, researchers, or anyone tired of living in an echo chamber.

## The 0→1 Feature
**Cross-Bias Story Comparison**: Unlike Google News or Apple News that show you more of what you already read, NewsLens deliberately shows you ALL perspectives on a topic simultaneously. The "Common Themes" feature highlights factual overlaps—what everyone agrees happened—separate from opinion/spin.

---

## How to Run

### Prerequisites
1. **Python 3.7+** installed
2. **News API Key** (free): Get one at https://newsapi.org/register

### Installation Steps

1. **Extract the ZIP file** to a folder

2. **Install required packages**:
```bash
pip install flask requests
```

3. **Add your API key**:
   - Open `main.py`
   - Find line 9: `NEWS_API_KEY = 'YOUR_API_KEY_HERE'`
   - Replace `'YOUR_API_KEY_HERE'` with your actual News API key (keep the quotes)

4. **Run the application**:
```bash
python main.py
```

5. **Open your browser** and go to:
```
http://localhost:5000
```

---

## Demo Walkthrough

### Step 1: Search for a Topic
- Enter any current news topic (e.g., "climate change", "economy", "technology")
- Click "Compare Coverage"

### Step 2: View Results Across Three Columns
- **Left column**: Articles from CNN, MSNBC, The Guardian, etc.
- **Center column**: Articles from BBC, Reuters, Associated Press, etc.
- **Right column**: Articles from Fox News, Washington Times, etc.

### Step 3: See Common Themes
- At the top, see keywords/themes that appear across multiple sources
- This shows you what's factually agreed upon vs. what's spin

### Step 4: Read Full Articles
- Click "Read full article →" to open the source in a new tab
- Compare headlines, language, and framing

---

## Features

### MVP Features (Iteration 1)
✅ Search any news topic  
✅ Fetch articles from 14 different news sources  
✅ Display results in 3 bias-sorted columns  
✅ Clean, modern web interface  
✅ Error handling for API failures  

### 0→1 Feature (Iteration 2)
✅ **Common Themes Detection**: Automatically finds keywords that appear across all bias groups  
✅ **Side-by-side comparison**: Visual layout makes bias differences obvious  
✅ **Source transparency**: Shows which outlet published each article  

### Polish Features (Iteration 3)
✅ Responsive design (works on mobile)  
✅ Loading indicators  
✅ Error messages for invalid searches  
✅ Smooth animations and hover effects  

---

## Known Bugs / Limitations

1. **API Rate Limits**: Free News API tier allows 100 requests/day. If you hit the limit, you'll get an error. Wait 24 hours or upgrade your API plan.

2. **Source Availability**: Not all sources publish articles on every topic. Some columns may show "No articles found."

3. **Bias Classification**: Source bias is manually categorized (simplified for MVP). In a real product, this would use a more sophisticated bias detection algorithm.

4. **Common Themes Algorithm**: Currently uses basic keyword matching (counts words >4 letters). A production version would use NLP (Natural Language Processing) for better theme extraction.

5. **No Historical Data**: Only shows current/recent articles. Can't search older news.

6. **English Only**: API is configured for English-language sources only.

---

## Next Steps (If I Had More Time)

### Iteration 4 Features:
1. **AI Summarization**: Use OpenAI API to generate neutral summaries of each story
2. **Fact-Checking Integration**: Highlight claims that fact-checkers have verified/debunked
3. **User Accounts**: Save favorite topics, track reading history
4. **Sentiment Analysis**: Visualize emotional tone (angry vs. neutral vs. optimistic) per source
5. **More Sources**: Add international news (Al Jazeera, RT, etc.)
6. **Mobile App**: Convert to React Native for iOS/Android
7. **Discussion Forums**: Let users debate articles with people from different political leanings

### Scalability Ideas:
- **Database**: Switch from News API to web scraping + own database for historical archives
- **Social Features**: "Challenge your bubble" - send articles to friends with opposite bias
- **Browser Extension**: Automatically show bias comparison when you click any news link
- **Premium Tier**: Ad-free, unlimited searches, custom source lists

---

## Test Plan

| Test # | Input | Expected Output | Actual Result | Pass/Fail |
|--------|-------|-----------------|---------------|-----------|
| 1 | Launch app | Homepage loads with search box | ✅ | Pass |
| 2 | Search "climate change" | 3 columns populate with articles | ✅ | Pass |
| 3 | Search empty string | Error message: "Please enter a topic" | ✅ | Pass |
| 4 | Search obscure topic ("zxcvbnm") | Shows "No articles found" in columns | ✅ | Pass |
| 5 | Click "Read full article" link | Opens article in new tab | ✅ | Pass |
| 6 | Search with invalid API key | Error: "Failed to fetch news" | ✅ | Pass |
| 7 | Search popular topic (e.g., "Trump") | Common themes appear at top | ✅ | Pass |
| 8 | Resize browser window | Layout stays readable on mobile | ✅ | Pass |

### Bug Found & Fixed:
**Bug**: When a source had no articles, the column would show raw JSON instead of a nice message.  
**Fix**: Added fallback HTML: `'<div class="no-results">No articles found from these sources</div>'`  
**Evidence**: See line 178 in `templates/index.html`

---

## Project Structure

```
NewsLens/
├── main.py                 # Flask backend (API routes)
├── templates/
│   └── index.html          # Frontend (HTML/CSS/JS)
├── README.txt              # This file
└── requirements.txt        # Python dependencies (optional)
```

---

## Technical Implementation

### How It Works:
1. **User enters topic** → JavaScript sends POST request to `/search`
2. **Flask backend** calls News API 3 times (once per bias group)
3. **Common themes algorithm** finds overlapping keywords
4. **Results returned as JSON** → Frontend renders in 3 columns

### Python Skills Used:
- ✅ **Flask** (web framework)
- ✅ **API integration** (`requests` library)
- ✅ **Data structures** (dicts, lists for organizing articles)
- ✅ **Functions** (modular code: `fetch_news_by_bias()`, `find_common_themes()`)
- ✅ **Error handling** (try/except for API failures)
- ✅ **JSON** (parsing API responses, sending data to frontend)

---

## Why This Is "0 to 1"

**Existing products:**
- Google News: Shows you more of what you already read (echo chamber)
- Apple News: Same problem
- AllSides: Shows bias ratings but doesn't aggregate stories side-by-side
- Ground News: Similar concept, but no free open-source version

**NewsLens differentiator:**
- **Only free tool** that shows left/center/right sources simultaneously for ANY topic
- **Common Themes** feature reveals factual consensus
- **Built for students** (simple, educational, open-source)

**The Secret:** Most people don't want to be biased—they just don't know HOW to escape their bubble. Showing contrasts explicitly (instead of lecturing about bias) lets users see it themselves.

---

## Credits

**Built by:** [Your Name]  
**Course:** ICS3U - Part 2 Application  
**APIs Used:** News API (https://newsapi.org)  
**Design Inspiration:** AllSides, Ground News  

---

## API Key Setup (Detailed)

1. Go to https://newsapi.org/register
2. Fill out the form (use your school email)
3. Check your email for the API key
4. Copy the key (looks like: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`)
5. Paste it in `main.py` line 9:
```python
NEWS_API_KEY = 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6'
```

**Troubleshooting:**
- If you get "Invalid API key", double-check you copied it correctly
- If you get "Rate limit exceeded", you've used all 100 requests for today
- If articles don't load, check your internet connection

---

## Questions?

If something doesn't work, check:
1. Did you install Flask? (`pip install flask requests`)
2. Did you add your API key?
3. Is port 5000 already in use? (Try changing `port=5000` to `port=5001` in main.py)

**Contact:** [Your Email/Discord]

---

**Last Updated:** January 15, 2026