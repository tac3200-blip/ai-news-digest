/**
 * VoiceFlow TTS - Google Apps Script サーバー
 * 
 * 【デプロイ手順】
 * 1. このコードを Google Apps Script に貼り付ける
 * 2. 「デプロイ」→「新しいデプロイ」→「種類: ウェブアプリ」
 * 3. 実行ユーザー: 「自分 (自分のメールアドレス)」
 *    アクセスできるユーザー: 「全員 (Anyone)」
 * 4. 「デプロイ」ボタンを押し、表示されたURLを index.html に設定する
 */

function doGet(e) {
  // CORSヘッダーを設定してローカルからのアクセスを許可
  var output = ContentService.createTextOutput();
  output.setMimeType(ContentService.MimeType.JSON);

  try {
    var text = e.parameter.text || "こんにちは";

    // テキストが長すぎる場合は切り詰める (Google翻訳TTSの制限)
    if (text.length > 200) {
      text = text.substring(0, 200);
    }

    // Google 翻訳の読み上げ音声エンドポイントからMP3を取得
    var url = "https://translate.google.com/translate_tts"
            + "?ie=UTF-8"
            + "&tl=ja"
            + "&client=tw-ob"
            + "&q=" + encodeURIComponent(text);

    var response = UrlFetchApp.fetch(url, {
      muteHttpExceptions: true,
      headers: {
        "User-Agent": "Mozilla/5.0"
      }
    });

    var responseCode = response.getResponseCode();
    if (responseCode !== 200) {
      output.setContent(JSON.stringify({
        error: "音声取得に失敗しました。HTTPステータス: " + responseCode
      }));
      return output;
    }

    // MP3バイナリをBase64エンコードしてJSONで返す
    var blob = response.getBlob();
    var base64Audio = Utilities.base64Encode(blob.getBytes());

    output.setContent(JSON.stringify({
      audio: base64Audio,
      text: text
    }));

  } catch (err) {
    output.setContent(JSON.stringify({
      error: err.toString()
    }));
  }

  return output;
}
