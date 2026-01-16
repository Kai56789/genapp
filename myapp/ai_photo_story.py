import streamlit as st
from PIL import Image
import os
import re
import uuid
from datetime import datetime
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")

st.set_page_config(page_title="AIストーリーメーカー", layout="wide")

defaults = {
    "mode": "create",
    "uploaded_image": None,
    "caption": "",
    "story": "",
    "story_title": "",
    "stories": [],
    "saved_flag": False,
    "selected_story": None,
    "uploader_key": 0,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

st.sidebar.title("📚 保存されたストーリー")

if st.sidebar.button("📚 新しいストーリー"):
    st.session_state["mode"] = "create"
    st.session_state["uploader_key"] += 1
    st.session_state["uploaded_image"] = None
    st.session_state["caption"] = ""
    st.session_state["story"] = ""
    st.session_state["story_title"] = ""
    st.session_state["saved_flag"] = False
    st.session_state["selected_story"] = None

st.sidebar.markdown("---")

if st.session_state["stories"]:
    for s in st.session_state["stories"]:
        if st.sidebar.button(f"📖 {s['title']}", key=s["id"]):
            st.session_state["selected_story"] = s
            st.session_state["mode"] = "view"
else:
    st.sidebar.info("まだ保存されたストーリーはありません")

if st.session_state["mode"] == "create":
    st.markdown(
        "<h1 style='text-align: center;'>📖 AIストーリーメーカー 📖</h1>",
        unsafe_allow_html=True
    )

if st.session_state["mode"] == "create":

    uploaded_file = st.file_uploader(
        "🏞️ 画像をアップロードしてください",
        type=["jpg", "jpeg", "png"],
        key=f"uploader_{st.session_state['uploader_key']}"
    )

    if uploaded_file:
        st.session_state["uploaded_image"] = Image.open(uploaded_file)

    if st.session_state["uploaded_image"] is None:
        st.stop()

    st.subheader("📷 アップロードされた画像")
    st.image(st.session_state["uploaded_image"], width=600)

    story_style = st.selectbox(
        "物語の雰囲気",
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
        with st.spinner("📝 情景描写を生成中..."):
            prompt = "この画像を文学的に40〜60文字で描写してください。日本語。"
            res = model.generate_content([prompt, st.session_state["uploaded_image"]])
            st.session_state["caption"] = res.text

    if st.session_state["caption"]:
        st.subheader("情景描写")
        st.write(st.session_state["caption"])

        if st.button("📖 ストーリー＆タイトル生成"):
            with st.spinner("📖 ストーリーを生成中..."):
                story_prompt = f"""
以下の情景描写から物語を作成してください。

文体：
{style_prompts[story_style]}

文字数：
500〜900文字

情景描写：
{st.session_state["caption"]}
"""
                story_res = model.generate_content(story_prompt)
                story_text = story_res.text.strip()
                st.session_state["story"] = story_text

            with st.spinner("🏷️ タイトルを生成中..."):
                title_prompt = f"""
以下の物語に合う日本語タイトルを20文字以内で1つだけ付けてください。
物語：
{story_text}
"""
                title_res = model.generate_content(title_prompt)
                title_line = title_res.text.split("\n")[0]
                st.session_state["story_title"] = re.sub(r"^\d+\.?\s*", "", title_line)[:20]

            st.session_state["saved_flag"] = False

    if st.session_state["story"]:
        st.markdown(
            f"<h2 style='text-align: center;'>📖 {st.session_state['story_title']}</h2>",
            unsafe_allow_html=True
        )
        st.text_area("ストーリー", st.session_state["story"], height=400)

        if not st.session_state["saved_flag"]:
            if st.button("📥 2回クリックするとサイドメニューに保存されます"):
                st.session_state["stories"].append({
                    "id": str(uuid.uuid4()),
                    "title": st.session_state["story_title"],
                    "story": st.session_state["story"],
                    "image": st.session_state["uploaded_image"],
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M")
                })
                st.session_state["saved_flag"] = True
                st.success("保存しました")

elif st.session_state["mode"] == "view":

    s = st.session_state["selected_story"]

    if s is None:
        st.info("サイドバーからストーリーを選択してください")
        st.stop()

    st.markdown(
        f"<h2 style='text-align: center;'>📖 {s['title']}</h2>",
        unsafe_allow_html=True
    )
    st.image(s["image"], width=600)
    st.caption(s["created_at"])
    st.text_area("内容", s["story"], height=500)