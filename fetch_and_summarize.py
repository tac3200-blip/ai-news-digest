import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
import feedparser
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

# Google GenAI SDK (インストールされていない/キーがない場合はフォールバック)
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

def summarize_article(client, title, content, source_name):
    """Gemini APIを使用して記事を日本語で要約する"""
    if not client:
        # APIキーが無い場合の簡易フォールバック要約
        clean_text = clean_html(content)[:150]
        return f"【概要】{title}\n{clean_text}..."

    prompt = f"""あなたはプロのIT・ビジネスニュース編集者です。
以下の記事（ソース: {source_name}）を読み、スマホでサクッと読めるように要約してください。

タイトル: {title}
内容本文: {clean_html(content)[:1500]}

【出力フォーマット規約】
- **タイトル翻訳**: 英語タイトルなら自然で魅力的な日本語に直してください。
- **要約文**: 結論・要点を箇条書きで3行（1行30文字程度）でまとめてください。
- **カテゴリー**: ["LLM・生成AI", "AIビジネス", "AI研究", "新ツール・製品", "トレンド"] の中から最も適切なものを1つ選んでください。

出力フォーマット（JSON形式のみ出力してください）:
{{
  "japanese_title": "日本語のタイトル",
  "summary": ["要点1", "要点2", "要点3"],
  "category": "カテゴリー名"
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
        return res_json
    except Exception as e:
        print(f"Gemini API要約失敗 ({title[:20]}...): {e}")
        return {
            "japanese_title": title,
            "summary": [clean_html(content)[:100] + "..."],
            "category": "ニュース"
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
    else:
        print("GEMINI_API_KEY が未設定、またはライブラリ未インストールのためフォールバックモードで実行します。")

    all_articles = []
    
    for source in sources:
        name = source.get("name")
        url = source.get("url")
        default_category = source.get("category", "AIニュース")
        
        print(f"取得中: {name} ({url})")
        feed = feedparser.parse(url)
        
        # 各ソースから最新3件を取得
        for entry in feed.entries[:3]:
            title = entry.get("title", "無題")
            link = entry.get("link", "#")
            
            # 本文または概要の取得
            content = ""
            if "content" in entry:
                content = entry.content[0].value
            elif "summary" in entry:
                content = entry.summary
            elif "description" in entry:
                content = entry.description
            
            # 日付の取得
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

            # 要約処理
            res = summarize_article(client, title, content, name)
            
            japanese_title = res.get("japanese_title", title)
            summary_list = res.get("summary", [clean_html(content)[:100]])
            category = res.get("category", default_category)

            all_articles.append({
                "original_title": title,
                "title": japanese_title,
                "summary": summary_list,
                "category": category,
                "source_name": name,
                "link": link,
                "published": parsed_date
            })

    # 出力用JSONの作成
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "news.json")
    
    output_data = {
        "updated_at": datetime.now(timezone(timedelta(hours=9))).strftime("%Y-%m-%d %H:%M"),
        "total_count": len(all_articles),
        "articles": all_articles
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"正常完了! {len(all_articles)} 件の記事を {output_path} に書き出しました。")

if __name__ == "__main__":
    fetch_all_news()
