import streamlit as st
import os
import asyncio
from pyzerox import zerox
from pyzerox.core.types import ZeroxOutput
import traceback

st.title("PDF OCR + Gemini 処理アプリ")

# APIキー入力
api_key = st.text_input("GEMINI_API_KEYを入力してください", type="password")
if not api_key:
    st.warning("APIキーを入力してください。")
    st.stop()
os.environ['GEMINI_API_KEY'] = api_key

# モデルと設定
model = "gemini/gemini-2.0-flash"
custom_system_prompt = None

# PDFファイルアップロード
uploaded_file = st.file_uploader("PDFファイルをアップロードしてください", type=["pdf"])

# ページ番号指定（カンマ区切り）
page_input = st.text_input("処理するページ番号をカンマ区切りで指定（例: 1,3,5）。空欄で全ページ処理")

def parse_pages(text):
    if not text.strip():
        return None
    try:
        pages = [int(p.strip()) for p in text.split(",") if p.strip().isdigit()]
        return pages if pages else None
    except:
        return None

select_pages = parse_pages(page_input)

output_dir = "./output_webapp"
os.makedirs(output_dir, exist_ok=True)

if uploaded_file and st.button("実行"):

    # ファイルサイズの確認
    file_size = uploaded_file.getbuffer().nbytes
    st.write(f"アップロードされたファイル名: {uploaded_file.name}")
    st.write(f"ファイルサイズ: {file_size} バイト")
    if file_size == 0:
        st.error("アップロードされたファイルが空です。処理を中止します。")
        st.stop()

    file_path = os.path.join(output_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    async def process_file():
        try:
            result: ZeroxOutput = await zerox(
                file_path=file_path,
                model=model,
                output_dir=output_dir,
                custom_system_prompt=custom_system_prompt,
                select_pages=select_pages
            )
            return result
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.text_area("詳細エラー情報", traceback.format_exc(), height=300)
            return None

    with st.spinner("処理中...しばらくお待ちください"):
        try:
            result = asyncio.run(process_file())
        except Exception as e:
            st.error(f"非同期処理で例外が発生しました: {e}")
            st.text_area("詳細エラー情報", traceback.format_exc(), height=300)
            result = None

    # デバッグ用にresult全体の内容を表示（かなり長いので必要に応じてコメントアウト可）
    st.write("zerox() の返却値 (result):")
    st.write(result)

    if result is not None and hasattr(result, "pages") and result.pages:
        st.success(f"処理完了！{len(result.pages)}ページ分の内容を表示します。")
        for i, page in enumerate(result.pages, start=1):
            st.markdown(f"### ページ {i}")
            st.text_area(f"ページ{i}の内容", page.content, height=300)
    else:
        st.warning("処理結果が取得できませんでした。")
