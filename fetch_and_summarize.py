import json
import os
import re
import sys
import hashlib
from datetime import datetime, timedelta, timezone
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

GEMINI_AVAILABLE = False
try:
    from google import genai
    from google.genai import types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

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

def summarize_article(client, title, content, source_name, default_category):
    """Gemini APIを使用して記事を日本語で要約し、指定されたカテゴリに正確に分類する"""
    
    clean_text = clean_html(content)[:1500]

    if not client:
        # APIキーが無い場合のフォールバック要約
        return {
            "japanese_title": title,
            "summary": [clean_text[:100] + "..."],
            "category": default_category
        }

    prompt = f"""あなたはプロのAI・ITニュース編集者です。
以下の記事（ソース: {source_name}）を読み、スマホ読者向けにわかりやすく日本語要約し、指定のカテゴリーに厳密に分類してください。

タイトル: {title}
本文: {clean_text}

【ルール】
1. **日本語タイトル**: 英語タイトルの場合は、日本の読者が惹かれる自然でわかりやすい日本語タイトルに翻訳してください。
2. **要約**: ポイントを要約して、短めの箇条書き2〜3行（1行30文字程度）で作成してください。
3. **カテゴリー分類**: 以下の3つのいずれかを必ず1つだけ厳密に選んでください：
   - "3大AI情報" (OpenAI, Anthropic, Google/Gemini などの主要3大AIベンダーの最新動向・重要モデル・海外主要発表)
   - "国内主要AI情報" (日本国内のAIニュース、ITmedia、GIGAZINE、PIVOT、企業のAI導入事例・トレンド)
   - "AIビジネス・トレンド" (上記以外のビジネス事例や一般AIツールニュース)

出力フォーマット（JSON形式のみ出力）:
{{
  "japanese_title": "日本語のタイトル",
  "summary": ["要点1", "要点2", "要点3"],
  "category": "3大AI情報 または 国内主要AI情報 または AIビジネス・トレンド"
}}
"""

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        res_json = json.loads(response.text)
        
        # カテゴリの正規化バリデーション
        cat = res_json.get("category", "")
        if "3大" in cat or "OpenAI" in cat or "Google" in cat or "Anthropic" in cat:
            res_json["category"] = "3大AI情報"
        elif "国内" in cat or "ITmedia" in source_name or "GIGAZINE" in source_name or "PIVOT" in source_name:
            res_json["category"] = "国内主要AI情報"
        else:
            res_json["category"] = default_category if default_category in ["3大AI情報", "国内主要AI情報"] else "国内主要AI情報"
            
        return res_json
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

    api_key = os.environ.get("GEMINI_API_KEY")
    client = None
    if GEMINI_AVAILABLE and api_key:
        try:
            client = genai.Client(api_key=api_key)
            print("Gemini APIクライアント初期化成功")
        except Exception as e:
            print(f"Gemini API初期化エラー: {e}")

    all_articles = []
    
    for source in sources:
        name = source.get("name")
        url = source.get("url")
        # 海外ソースは3大AI情報、日本ソースは国内主要AI情報をデフォルトとする
        default_category = "3大AI情報" if ("TechCrunch" in name or "Verge" in name) else "国内主要AI情報"
        
        print(f"取得中: {name} ({url})")
        feed = feedparser.parse(url)
        
        for entry in feed.entries[:3]:
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

            res = summarize_article(client, title, content, name, default_category)
            
            japanese_title = res.get("japanese_title", title)
            summary_list = res.get("summary", [clean_html(content)[:100]])
            category = res.get("category", default_category)

            all_articles.append({
                "id": generate_id(link, title),
                "original_title": title,
                "title": japanese_title,
                "summary": summary_list,
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
