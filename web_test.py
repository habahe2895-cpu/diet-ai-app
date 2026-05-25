import streamlit as st

st.title("🚀 我的第一个网页应用")
st.write("兄弟，这玩意儿比写 GUI 简单多了！")

name = st.text_input("输入你的名字：")
if st.button("点我"):
    st.success(f"你好，{name}！欢迎来到 Web 时代。")
