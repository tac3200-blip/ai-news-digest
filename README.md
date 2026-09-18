# 📱 AI Daily Digest (完全無料・毎朝自動更新)

毎朝7時に自動で最新のAIニュース（PIVOT、ITmedia、TechCrunch等）を取得し、Google Gemini API（無料枠）で要約してスマホ最適化サイトに配信する完全無料の仕組みです。

---

## ✨ このアプリの特徴

- **完全無料運用**: クレジットカード不要！GitHub Actions + GitHub Pages + Gemini API無料枠で動きます。
- **配信元を自由に変更可能**: `sources.json` を書き換えるだけで、好きなニュースサイトやYouTubeチャンネルを追加・削除できます。
- **スマホ最適化デザイン**: ダークモード対応。通勤中にサクッと読める要約フォーマット。

---

## 🚀 3ステップで始める設定ガイド

### ステップ 1: Gemini APIキーを取得（無料・3分）

1. [Google AI Studio](https://aistudio.google.com/) にアクセスし、Googleアカウントでログイン。
2. **「Get API key」** ボタンをクリック。
3. **「Create API key」** を押して発行された文字列（`AIzaSy...` で始まるキー）をコピー。

---

### ステップ 2: GitHubリポジトリを作成＆設定

1. [GitHub](https://github.com/) にログインし、新しい**Public（公開）**リポジトリを作成します。
2. このフォルダのファイルをすべてリポジトリにプッシュ（アップロード）します。
3. リポジトリの **Settings** タブを開きます。
4. 左メニューの **Secrets and variables** > **Actions** を選択。
5. **「New repository secret」** をクリックし、以下のように登録します：
   - **Name**: `GEMINI_API_KEY`
   - **Secret**: （ステップ1でコピーしたAPIキー）
6. 次に、左メニューの **Pages** を開き：
   - **Source**: `Deploy from a branch`
   - **Branch**: `main` / `(root)` を選択して **Save**。

これで、数分後にあなたのサイトURL（`https://<ユーザー名>.github.io/<リポジトリ名>/`）が発行されます！

---

### ステップ 3: 手動で初回テスト実行

1. GitHubリポジトリの **Actions** タブを開く。
2. 左側の **Daily AI News Summarizer** をクリック。
3. 右側の **Run workflow** ボタンをクリックして実行！
4. 成功すると、`data/news.json` が生成され、Webサイトにニュースが表示されます。

---

## 🛠️ ニュースサイトの追加・変更方法

`sources.json` を直接編集するだけで、取得先を自由に増やせます！

```json
[
  {
    "name": "PIVOT (YouTube)",
    "category": "ビジネス・AI",
    "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCC55C_F8iH32h59_548O-8A"
  },
  {
    "name": "お好きなサイト名",
    "category": "カテゴリ名",
    "url": "https://example.com/rss.xml"
  }
]
```

### 💡 おすすめのフィード取得例
- **YouTubeチャンネル**: `https://www.youtube.com/feeds/videos.xml?channel_id=【チャンネルID】`
- **note**: `https://note.com/【ユーザーID】/rss`
- **Qiita / Zenn**: 各サイトのRSS URL

---

## 📱 iPhoneでサクッと読む（ホーム画面に追加）

1. 発行された GitHub Pages のURLを Safari で開く。
2. 画面下部の **共有ボタン（□に↑のアイコン）** をタップ。
3. **「ホーム画面に追加」** を選択。
4. ホーム画面に専用アイコンが作成され、毎朝タップ1つで最新AIニュースが読めるようになります！
