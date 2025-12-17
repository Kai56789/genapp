import streamlit as st
from PIL import Image
import os
import re
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")

st.set_page_config(page_title="AIストーリーメーカー", layout="wide")

if "uploaded_image" not in st.session_state:
    st.session_state["uploaded_image"] = None
if "caption" not in st.session_state:
    st.session_state["caption"] = ""
if "story" not in st.session_state:
    st.session_state["story"] = ""
if "story_title" not in st.session_state:
    st.session_state["story_title"] = ""
if "stories" not in st.session_state:
    st.session_state["stories"] = []
if "saved_flag" not in st.session_state:
    st.session_state["saved_flag"] = False
if "selected_story" not in st.session_state:
    st.session_state["selected_story"] = None
if "selected_story_title" not in st.session_state:
    st.session_state["selected_story_title"] = ""

st.sidebar.title("📚 保存されたストーリー")

titles = [s["title"] for s in st.session_state["stories"]]

selected_title = None
if titles:
    selected_title = st.sidebar.selectbox("ストーリーを選択", titles)
    if st.sidebar.button("📖 表示"):
        for s in st.session_state["stories"]:
            if s["title"] == selected_title:
                st.session_state["selected_story"] = s["story"]
                st.session_state["selected_story_title"] = s["title"]
                break
else:
    st.sidebar.info("まだストーリーはありません")

st.title("📘 AIストーリーメーカー")

uploaded_file = st.file_uploader(
    "🏞️ 画像をアップロードしてください",
    type=["jpg", "jpeg", "png"]
)
if uploaded_file:
    st.session_state["uploaded_image"] = Image.open(uploaded_file)

if not st.session_state["uploaded_image"]:
    st.stop()

st.subheader("📷 アップロードされた画像")
st.image(st.session_state["uploaded_image"], width=600)

story_style = st.selectbox(
    "物語の雰囲気を選んでください",
    [
        "小説風（デフォルト）",
        "優しい絵本風",
        "ダーク・ミステリー風",
        "冒険物語",
        "ロマンチック",
        "コメディ調",
        "ポエム（詩的）"
    ]
)

style_prompts = {
    "小説風（デフォルト）": "情緒的で文学的な文体。",
    "優しい絵本風": "子供にも優しい語り口。",
    "ダーク・ミステリー風": "不穏で謎めいた雰囲気。",
    "冒険物語": "躍動感ある冒険譚。",
    "ロマンチック": "美しくロマンチックな表現。",
    "コメディ調": "明るくユーモラス。",
    "ポエム（詩的）": "詩的で比喩的。"
}

if st.button("📝 画像の描写を生成"):
    with st.spinner("情景描写を生成中..."):
        prompt = "この画像を文学的に40〜60文字で描写してください。日本語。"
        response = model.generate_content([prompt, st.session_state["uploaded_image"]])
        st.session_state["caption"] = response.text

if st.session_state["caption"]:
    st.markdown("### 情景描写")
    st.write(st.session_state["caption"])

if st.session_state["caption"]:
    if st.button("📖 ストーリー＆タイトルを生成"):
        with st.spinner("ストーリー生成中..."):
            story_prompt = f"""
以下の情景描写から物語を作成してください。

文体：
{style_prompts[story_style]}

文字数：
500〜900文字

情景描写：
{st.session_state["caption"]}
"""
            story_response = model.generate_content(story_prompt)
            story_text = story_response.text.strip()
            st.session_state["story"] = story_text
            st.session_state["saved_flag"] = False

        with st.spinner("タイトル生成中..."):
            title_prompt = f"""
以下の物語に合うタイトルを日本語で20文字以内で1つだけ短く付けてください。  
複数候補や説明は不要です。

物語：
{story_text}
"""
            title_response = model.generate_content(title_prompt)
            title_raw = title_response.text.strip()

            title_line = title_raw.split("\n")[0].strip()
            title_clean = re.sub(r"^\d+\.?\s*", "", title_line)
            title_final = title_clean[:20]

            st.session_state["story_title"] = title_final

if st.session_state["story"]:
    st.markdown(f"### タイトル: **{st.session_state['story_title']}**")
    st.text_area(
        "📖 生成されたストーリー",
        st.session_state["story"],
        height=500
    )

    if not st.session_state["saved_flag"]:
        save_clicked = st.button("📥 2回押すと保存がされます")
        if save_clicked:
            titles = [s["title"] for s in st.session_state["stories"]]
            if st.session_state["story_title"] in titles:
                st.warning("同じタイトルのストーリーが既に保存されています。")
            else:
                st.session_state["stories"].append({
                    "title": st.session_state["story_title"],
                    "story": st.session_state["story"]
                })
                st.session_state["saved_flag"] = True
                st.success("ストーリーを保存しました！")
    else:
        st.info("このストーリーはすでに保存されています。")

if st.session_state["selected_story"]:
    st.markdown("---")
    st.markdown(f"## 📚 保存済みストーリー: **{st.session_state['selected_story_title']}**")
    st.text_area(
        "保存されたストーリー内容",
        st.session_state["selected_story"],
        height=400,
        key="selected_story_area"
    )