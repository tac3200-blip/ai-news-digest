import json
import os
import re
import sys
import hashlib
from datetime import datetime, timedelta, timezone
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# Google GenAI SDK
GEMINI_AVAILABLE = False
genai_client = None

try:
    from google import genai
    from google.genai import types
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai_client = genai.Client(api_key=api_key)
        GEMINI_AVAILABLE = True
        print("Google GenAI (v2) クライアント初期化完了")
except Exception as e:
    print(f"GenAI SDK初期化エラー: {e}")

def clean_html(raw_html):
    """HTMLタグを除去して純粋なテキストを取り出す"""
    if not raw_html:
        return ""
    soup = BeautifulSoup(raw_html, "html.parser")
    text = soup.get_text(separator=" ")
    return re.sub(r'\s+', ' ', text).strip()

def generate_id(link, title):
    """記事の一意なIDを生成"""
    return hashlib.md5(f"{link}_{title}".encode('utf-8')).hexdigest()[:12]

def summarize_article(title, content, source_name, default_category):
    """Gemini APIを使用して英語記事を完全な日本語に翻訳・要約する"""
    clean_text = clean_html(content)[:1500]

    if not genai_client:
        return {
            "japanese_title": title,
            "summary": [clean_text[:100] + "..."],
            "category": default_category
        }

    prompt = f"""あなたは日本の一流IT・AI技術メディアのプロ編集長です。
以下のニュース記事（ニュースソース: {source_name}）を読み、日本の読者が通勤中にスマホで一目で理解できるように、必ず【完全な日本語】に翻訳・要約してください。

元のタイトル: {title}
本文テキスト: {clean_text}

【必須翻訳・要約ルール】
1. **日本語タイトル**: タイトルが英語の場合は、意味がすぐに伝わる自然で魅力的な日本語タイトルに必ず翻訳してください。英語のままでの出力は絶対に禁止です。
2. **分かりやすい日本語要約**: 記事の要点を、平易でわかりやすい日本語で2〜3行（箇条書き）でまとめてください。専門用語は噛み砕いて説明してください。英語の単語が混ざる場合は適切な日本語に訳してください。

出力フォーマット（JSON形式のみ出力してください）:
{{
  "japanese_title": "完全な日本語に翻訳されたタイトル",
  "summary": [
    "日本語要点1",
    "日本語要点2",
    "日本語要点3"
  ]
}}
"""

    try:
        response = genai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        text_resp = response.text
        # JSONコードブロック除去
        clean_json_str = re.sub(r'```json\s*|\s*```', '', text_resp).strip()
        res_json = json.loads(clean_json_str)
        
        japanese_title = res_json.get("japanese_title", title)
        summary = res_json.get("summary", [clean_text[:100]])
        
        return {
            "japanese_title": japanese_title,
            "summary": summary,
            "category": default_category
        }
    except Exception as e:
        print(f"Gemini API要約エラー ({title[:20]}...): {e}")
        return {
            "japanese_title": title,
            "summary": [clean_text[:100] + "..."],
            "category": default_category
        }

def fetch_all_news():
    sources_file = "sources.json"
    if not os.path.exists(sources_file):
        print("sources.json が見つかりません。")
        return

    with open(sources_file, "r", encoding="utf-8") as f:
        sources = json.load(f)

    all_articles = []
    
    for source in sources:
        name = source.get("name")
        url = source.get("url")
        group = source.get("group", "japan")
        category = source.get("category", "国内主要AI情報")
        
        print(f"取得中: {name} ({url})")
        feed = feedparser.parse(url)
        
        limit = 3 if group == "official" else 2
        
        for entry in feed.entries[:limit]:
            title = entry.get("title", "無題")
            link = entry.get("link", "#")
            
            content = ""
            if "content" in entry:
                content = entry.content[0].value
            elif "summary" in entry:
                content = entry.summary
            elif "description" in entry:
                content = entry.description
            
            pub_date = entry.get("published") or entry.get("updated") or ""
            parsed_date = ""
            if pub_date:
                try:
                    dt = date_parser.parse(pub_date)
                    parsed_date = dt.strftime("%Y-%m-%d %H:%M")
                except:
                    parsed_date = datetime.now().strftime("%Y-%m-%d %H:%M")
            else:
                parsed_date = datetime.now().strftime("%Y-%m-%d %H:%M")

            res = summarize_article(title, content, name, category)
            
            all_articles.append({
                "id": generate_id(link, title),
                "original_title": title,
                "title": res.get("japanese_title", title),
                "summary": res.get("summary", []),
                "group": group,
                "category": category,
                "source_name": name,
                "link": link,
                "published": parsed_date
            })

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "news.json")
    
    output_data = {
        "updated_at": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"),
        "total_count": len(all_articles),
        "articles": all_articles
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"正常完了! {len(all_articles)} 件の記事を出力しました。")

if __name__ == "__main__":
    fetch_all_news()
