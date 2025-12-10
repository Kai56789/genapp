import streamlit as st
from PIL import Image
import os
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-flash-lite-latest")

st.set_page_config(page_title="AIストーリーメーカー", layout="wide")

st.markdown(
    """
    <style>
    .full-width-textarea .stTextArea textarea {
        width: 100% !important;
        max-width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    """
    <h1 style="text-align:center; color:#4B3F72; font-family:'Georgia';">
        📘 AIストーリーメーカー 📘
    </h1>
    """,
    unsafe_allow_html=True
)

st.info(
    "画像をアップロードすると物語を作成できます。\n\n"
    "違う画像でストーリーを作成したい場合は、再度アップロードしてください。"
)

if "uploaded_image" not in st.session_state:
    st.session_state["uploaded_image"] = None

uploaded_image = st.file_uploader(
    "🏞️ 画像をアップロードしてください",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=False
)

if uploaded_image:
    img = Image.open(uploaded_image)
    st.session_state["uploaded_image"] = img

if st.session_state["uploaded_image"]:
    img = st.session_state["uploaded_image"]

    st.markdown(
        "<h3 style='text-align:center; font-family:Georgia;'>アップロードされた画像</h3>",
        unsafe_allow_html=True
    )
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(img, width=600)
else:
    st.stop()

story_style = st.selectbox(
    "物語の雰囲気を選んでください 🔽",
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
    "小説風（デフォルト）": "情緒的で文学的。一人称または三人称の自然な語り口。",
    "優しい絵本風": "幼い読者にも優しく語りかける、温かく柔らかい文体。",
    "ダーク・ミステリー風": "不穏で謎めいた雰囲気。少し影のある語り口。",
    "冒険物語": "ワクワクする展開、主人公の行動や発見を中心に。",
    "ロマンチック": "美しい情景と心情描写。柔らかいロマンチックな文体。",
    "コメディ調": "ユーモアを交えた明るく楽しい語り口。",
    "ポエム（詩的）": "詩のようなリズムと比喩を多用した芸術的表現。"
}

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("📝 画像の描写（キャプション）を生成", use_container_width=True):
        with st.spinner("画像から情景描写を生成しています..."):
            prompt = "この画像を文学的に表現した情景描写を40〜60文字で作ってください。日本語。"
            response = model.generate_content([prompt, img])
            st.session_state["caption"] = response.text
        st.success("キャプション生成完了！")

    if "caption" in st.session_state:
        st.markdown(
            f"<div style='padding:15px; background:#faf5e6; border-radius:12px; font-size:16px;'>{st.session_state['caption']}</div>",
            unsafe_allow_html=True
        )

if "caption" in st.session_state:
    col1, col2, col3 = st.columns([0.2, 3, 0.2])
    with col2:
        if st.button("📖 ストーリーを生成", use_container_width=True):
            with st.spinner("ストーリーを生成しています..."):
                selected_style = style_prompts[story_style]
                prompt = f"""
以下の情景描写から物語を生成してください。

● 文体の雰囲気：
{selected_style}

● 文字数：
500〜900文字

● 情景描写：
{st.session_state['caption']}
"""
                response = model.generate_content(prompt)
                st.session_state["story"] = response.text
            st.success("ストーリーが完成しました！")

        if "story" in st.session_state:
            st.markdown('<div class="full-width-textarea">', unsafe_allow_html=True)
            st.text_area(
                "📖 生成されたストーリー",
                st.session_state["story"],
                height=500,
                key="story_box"
            )
            st.markdown('</div>', unsafe_allow_html=True)

if "story" in st.session_state:
    bgm_files = {
        "小説風（デフォルト）": "bgm/gentle.mp3",
        "優しい絵本風": "bgm/gentle.mp3",
        "ダーク・ミステリー風": "bgm/mystery.mp3",
        "冒険物語": "bgm/adventure.mp3",
        "ロマンチック": "bgm/romantic.mp3",
        "コメディ調": "bgm/funny.mp3",
        "ポエム（詩的）": "bgm/poem.mp3"
    }

    col1, col2, col3 = st.columns([0.2, 3, 0.2])
    with col2:
        st.markdown("### 🎧 物語の雰囲気に合わせたBGM")
        bgm_path = bgm_files.get(story_style)
        if bgm_path and os.path.exists(bgm_path):
            st.audio(bgm_path)
        else:
            st.info("現在、BGMファイルは利用できません。")