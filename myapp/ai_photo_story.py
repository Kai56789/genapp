import streamlit as st
from PIL import Image
import os
import tempfile
import traceback
from gtts import gTTS
import google.generativeai as genai

st.set_page_config(page_title="AIフォトストーリーブック", layout="wide")
st.title("📘 AIフォトストーリーブック")

# Gemini API Setup
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.error("🚨 GEMINI_API_KEY が設定されていません。環境変数を確認してください。")
    st.stop()

try:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-flash-lite-latest")
except Exception as e:
    st.error("Gemini API の初期化に失敗しました。\n" + str(e))
    st.stop()

uploaded_images = st.file_uploader(
    "画像を複数アップロードしてください",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True
)

if uploaded_images:
    st.subheader("📎 アップロードされた画像")
    for img in uploaded_images:
        st.image(img, width=250)

    if st.button("📝 画像の描写（キャプション）を生成"):
        captions = []
        st.info("画像キャプション生成中...")
        for img in uploaded_images:
            try:
                with Image.open(img) as image:
                    prompt = "この画像の内容を短い物語的描写のキャプションにしてください。50文字以内、日本語。"
                    try:
                        response = model.generate_content([prompt, image])
                        captions.append(response.text)
                    except Exception as e:
                        st.error(f"画像のキャプション生成に失敗しました: {e}")
                        captions.append("(生成エラー)")
            except Exception as img_e:
                st.error(f"画像の読み込みに失敗しました: {img_e}")
                captions.append("(読み込みエラー)")
        st.session_state["captions"] = captions
        st.success("キャプション生成完了！")
        for i, cap in enumerate(captions):
            st.write(f"**画像 {i+1}:** {cap}")

    if "captions" in st.session_state and st.button("📖 物語を生成"):
        with st.spinner("物語生成中..."):
            prompt = f"""
次の画像キャプションの順番に沿って短いストーリーを作成してください。
章立て（第1章, 第2章…）で、児童書の語り口、日本語、400〜900文字。

キャプション:
{chr(10).join(st.session_state['captions'])}
"""
            try:
                response = model.generate_content(prompt)
                story = response.text
            except Exception as e:
                st.error("物語生成に失敗しました: " + str(e))
                story = ""

        st.session_state["story"] = story

        if story:
            st.success("物語生成完了！")

            # 章立て分割表示
            chapters = story.split("第")
            for chap in chapters:
                chap = chap.strip()
                if chap:
                    chap_title = "第" + chap[:3]
                    chap_content = chap[3:].strip()
                    with st.expander(chap_title):
                        st.write(chap_content)
        else:
            st.warning("物語は生成されませんでした。ログを確認してください。")

    if "story" in st.session_state and st.button("🔊 ナレーション音声を生成"):
        if not st.session_state["story"]:
            st.warning("音声化するストーリーが空です。まず物語を生成してください。")
        else:
            with st.spinner("gTTS で音声生成中..."):
                try:
                    tts = gTTS(st.session_state["story"], lang="ja")
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                        tmp_path = tmp.name
                    tts.save(tmp_path)
                    with open(tmp_path, "rb") as f:
                        audio_bytes = f.read()
                    st.session_state["audio_bytes"] = audio_bytes
                except Exception as e:
                    st.error("音声生成に失敗しました: " + str(e))
                    st.error(traceback.format_exc())
                    audio_bytes = None
                    tmp_path = None
                finally:
                    try:
                        if 'tmp_path' in locals() and tmp_path and os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass

            if audio_bytes:
                st.success("音声生成完了！下で再生できます👇")
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button(
                    label="📥 音声をダウンロード",
                    data=audio_bytes,
                    file_name="story.mp3",
                    mime="audio/mp3"
                )

# ==== サイドバー：ストーリーの保存・閲覧機能 ====

# saved_stories はタイトル→内容の辞書で管理
if "saved_stories" not in st.session_state:
    st.session_state["saved_stories"] = {}

sidebar = st.sidebar
sidebar.title("📚 ストーリー管理")

if "story" in st.session_state and st.session_state["story"]:
    # タイトル抽出：「第1章 ○○○」から章タイトル部分だけ抜き出し
    first_chapter_title = None
    for line in st.session_state["story"].splitlines():
        if line.startswith("第1章"):
            first_chapter_title = line.replace("第1章", "").strip()
            break
    if not first_chapter_title:
        first_chapter_title = "無題ストーリー"

    # ストーリー保存ボタン
    if sidebar.button("💾 今のストーリーを保存"):
        # 保存（上書き含む）
        st.session_state["saved_stories"][first_chapter_title] = st.session_state["story"]
        sidebar.success(f"『{first_chapter_title}』を保存しました。")

# 保存済みタイトルリスト
saved_titles = list(st.session_state["saved_stories"].keys())

if saved_titles:
    selected_title = sidebar.selectbox("保存済みストーリー一覧", saved_titles)

    if selected_title:
        sidebar.markdown(f"### 『{selected_title}』")
        story_text = st.session_state["saved_stories"][selected_title]

        # ストーリー全文表示（スクロール可）
        sidebar.text_area("ストーリー全文", story_text, height=300, key="saved_story_text")

        # ダウンロードボタン
        sidebar.download_button(
            label="📥 ストーリーをテキストでダウンロード",
            data=story_text,
            file_name=f"{selected_title}.txt",
            mime="text/plain"
        )
else:
    sidebar.info("保存されたストーリーはまだありません。")