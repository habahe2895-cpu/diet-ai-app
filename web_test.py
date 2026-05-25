"""
私人 AI 营养师 v10.0 PRO
作者：AI 民工日记
特色：根据用户身高体重定制方案、清晰展示 BMR/TDEE/缺口、AI 自动估算热量
"""

import streamlit as st
from openai import OpenAI
import json

# ============================================
# 配置区
# ============================================
# ⚠️ 部署到云端时，API Key 请使用 Streamlit Secrets，本地测试可写在这里
API_KEY = st.secrets["API_KEY"]
BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

# ============================================
# 页面设置
# ============================================
st.set_page_config(page_title="AI 私人营养师", page_icon="🥗", layout="wide")

st.title("🥗 AI 私人营养师")
st.caption("由 AI 民工日记 出品 · 输入你的身体数据，AI 帮你定制减脂方案")

# ============================================
# Session State 初始化（用来记住用户的数据）
# ============================================
if "profile_done" not in st.session_state:
    st.session_state.profile_done = False
if "bmr" not in st.session_state:
    st.session_state.bmr = 0
if "tdee" not in st.session_state:
    st.session_state.tdee = 0
if "target_intake" not in st.session_state:
    st.session_state.target_intake = 0

# ============================================
# 第一步：用户身体数据录入
# ============================================
with st.sidebar:
    st.header("👤 你的身体数据")
    st.caption("第一次使用，请填写以下信息")
    
    gender = st.radio("性别", ["男", "女"], horizontal=True)
    age = st.number_input("年龄", min_value=10, max_value=80, value=20)
    height = st.number_input("身高 (cm)", min_value=140, max_value=220, value=170)
    weight = st.number_input("当前体重 (kg)", min_value=30.0, max_value=200.0, value=60.0, step=0.1)
    target_weight = st.number_input("目标体重 (kg)", min_value=30.0, max_value=200.0, value=55.0, step=0.1)
    
    activity_level = st.selectbox(
        "日常活动水平",
        ["久坐 (办公室/学生)", "轻度 (每周运动1-3次)", "中度 (每周运动3-5次)", "高强度 (每周运动6-7次)"]
    )
    
    if st.button("🚀 生成我的专属方案", type="primary", use_container_width=True):
        # Mifflin-St Jeor 公式（最权威的 BMR 计算公式）
        if gender == "男":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        # TDEE 计算
        activity_factor = {
            "久坐 (办公室/学生)": 1.2,
            "轻度 (每周运动1-3次)": 1.375,
            "中度 (每周运动3-5次)": 1.55,
            "高强度 (每周运动6-7次)": 1.725
        }
        tdee = bmr * activity_factor[activity_level]
        
        # 减脂目标摄入（缺口 500 大卡，安全减脂）
        target_intake = tdee - 500
        # 设置最低摄入下限（防止用户饿到伤身）
        min_intake = 1200 if gender == "女" else 1500
        if target_intake < min_intake:
            target_intake = min_intake
        
        st.session_state.bmr = round(bmr)
        st.session_state.tdee = round(tdee)
        st.session_state.target_intake = round(target_intake)
        st.session_state.weight = weight
        st.session_state.target_weight = target_weight
        st.session_state.profile_done = True
        st.rerun()

# ============================================
# 第二步：展示个人方案
# ============================================
if not st.session_state.profile_done:
    st.info("👈 请先在左侧填写你的身体数据，AI 将为你定制专属减脂方案。")
    st.markdown("---")
    st.markdown("""
    ### 💡 这个工具能帮你做什么？
    - 📊 **精确计算**：根据你的身体数据，算出基础代谢（BMR）和每日总消耗（TDEE）。
    - 🎯 **定制目标**：给出一个安全、科学的每日热量摄入目标。
    - 🤖 **AI 算热量**：你只需要输入今天吃了什么，AI 自动估算热量。
    - 🔥 **实时缺口**：清晰看到今天还能吃多少，或者已经超标多少。
    - 📅 **预测时间**：告诉你按当前节奏，多久能达到目标体重。
    """)
else:
    # 顶部展示个人代谢数据
    st.subheader("📊 你的代谢档案")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🔥 基础代谢 (BMR)", f"{st.session_state.bmr} 大卡", help="躺着不动一天也会消耗的热量")
    col2.metric("⚡ 每日消耗 (TDEE)", f"{st.session_state.tdee} 大卡", help="加上日常活动后的总消耗")
    col3.metric("🎯 推荐摄入", f"{st.session_state.target_intake} 大卡", help="每天吃这么多，能稳定减脂")
    
    weight_to_lose = st.session_state.weight - st.session_state.target_weight
    if weight_to_lose > 0:
        # 每天 500 缺口 = 一周减约 0.5kg
        weeks_needed = round(weight_to_lose / 0.5)
        col4.metric("⏳ 预计减脂周期", f"{weeks_needed} 周", help=f"从 {st.session_state.weight}kg 到 {st.session_state.target_weight}kg")
    else:
        col4.metric("✅ 状态", "已达标", help="你已经达到目标体重啦")
    
    st.markdown("---")
    
    # ============================================
    # 第三步：今日饮食运动记录
    # ============================================
    st.subheader("📝 今日饮食运动记录")
    
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        bf = st.text_area("🍳 早餐", placeholder="例如：2个包子，1杯豆浆", height=100)
    with col_b:
        lunch = st.text_area("🍛 午餐", placeholder="例如：黄焖鸡米饭", height=100)
    with col_c:
        dinner = st.text_area("🥗 晚餐", placeholder="例如：轻食沙拉", height=100)
    
    snack = st.text_input("🍎 加餐/零食 (可选)", placeholder="例如：1个苹果，1把坚果")
    exercise = st.text_input("🏃 今日运动 (可选)", placeholder="例如：跑步30分钟，打羽毛球1小时")
    
    if st.button("🤖 召唤 AI 计算今日热量", type="primary", use_container_width=True):
        if not bf and not lunch and not dinner and not snack:
            st.warning("⚠️ 请至少填写一顿饭的内容！")
        else:
            with st.spinner("AI 正在帮你估算热量..."):
                prompt = f"""你是一个专业的营养师。请帮我估算以下饮食和运动的热量。
用户信息：{gender}，{age}岁，{height}cm，{weight}kg。

早餐：{bf or '未吃'}
午餐：{lunch or '未吃'}
晚餐：{dinner or '未吃'}
加餐：{snack or '无'}
运动：{exercise or '无'}

请严格按以下 JSON 格式输出（不要任何其他废话）：
{{
    "早餐热量": 300,
    "午餐热量": 600,
    "晚餐热量": 400,
    "加餐热量": 100,
    "总摄入": 1400,
    "运动消耗": 300,
    "净摄入": 1100,
    "餐食评价": "用一句话点评今天的饮食结构（高/低蛋白？油盐如何？）"
}}"""
                try:
                    response = client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=300,
                    )
                    result_str = response.choices[0].message.content.strip()
                    
                    if result_str.startswith("```json"):
                        result_str = result_str[7:-3].strip()
                    elif result_str.startswith("```"):
                        result_str = result_str[3:-3].strip()
                        
                    data = json.loads(result_str)
                    
                    st.success("✅ 计算完成！")
                    st.markdown("---")
                    
                    # ============================================
                    # 核心结果展示：缺口分析
                    # ============================================
                    st.subheader("🎯 今日缺口分析")
                    
                    total_intake = data.get("总摄入", 0)
                    burned = data.get("运动消耗", 0)
                    net_intake = total_intake - burned
                    
                    # 与目标对比
                    gap = st.session_state.target_intake - net_intake
                    
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("总摄入", f"{total_intake} 大卡")
                    c2.metric("运动消耗", f"-{burned} 大卡")
                    c3.metric("净摄入", f"{net_intake} 大卡")
                    
                    if gap > 0:
                        c4.metric("✅ 还能吃", f"{gap} 大卡", delta=f"距离目标还差 {gap}")
                    elif gap < 0:
                        c4.metric("⚠️ 已超标", f"{abs(gap)} 大卡", delta=f"超出 {abs(gap)}", delta_color="inverse")
                    else:
                        c4.metric("🎯 完美", "0 大卡", delta="刚好达标")
                    
                    # ============================================
                    # 智能建议
                    # ============================================
                    st.markdown("### 💡 AI 教练建议")
                    
                    # 计算实际热量缺口（与TDEE比）
                    real_deficit = st.session_state.tdee - net_intake
                    
                    if real_deficit > 800:
                        st.error(f"🚨 今天缺口 **{real_deficit} 大卡**，太大了！长期这样会掉肌肉、降代谢。建议加一杯牛奶或一个鸡蛋。")
                    elif 300 <= real_deficit <= 800:
                        st.success(f"✅ 今天缺口 **{real_deficit} 大卡**，完美减脂区间！按这个节奏，脂肪稳稳燃烧。")
                    elif 0 <= real_deficit < 300:
                        st.warning(f"⚠️ 今天缺口 **{real_deficit} 大卡**，偏小。今天减脂效果一般，明天可以稍微少吃点或多动动。")
                    else:
                        st.error(f"🚨 今天反而盈余 **{abs(real_deficit)} 大卡**！今天会长肉，明天必须管住嘴迈开腿。")
                    
                    st.info(f"📝 **餐食点评**：{data.get('餐食评价', '无')}")
                    
                    # 各餐细节
                    with st.expander("🔍 查看各餐热量明细"):
                        st.write(f"- 早餐：{data.get('早餐热量', 0)} 大卡")
                        st.write(f"- 午餐：{data.get('午餐热量', 0)} 大卡")
                        st.write(f"- 晚餐：{data.get('晚餐热量', 0)} 大卡")
                        st.write(f"- 加餐：{data.get('加餐热量', 0)} 大卡")
                    
                except Exception as e:
                    st.error(f"❌ AI 计算失败：{e}")

# 页脚
st.markdown("---")
st.caption("Made with ❤️ by AI民工日记 · 仅供参考，不能替代专业医疗建议")
