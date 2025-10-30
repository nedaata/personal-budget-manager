import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="centered"
)

# التصميم العربي البسيط
st.markdown("""
<style>
    .main-title { 
        font-size: 2.5rem; 
        color: #2E86AB; 
        text-align: center; 
        margin-bottom: 1rem; 
    }
    .stats-card { 
        background: #f0f8ff; 
        padding: 15px; 
        border-radius: 10px; 
        margin: 10px 0; 
        border-right: 4px solid #2E86AB; 
    }
</style>
""", unsafe_allow_html=True)

# الفئات
الفئات = ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"]

# تهيئة الحالة
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0

def main():
    st.markdown("<h1 class='main-title'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72; margin-bottom: 30px;'>💵 بالدينار الليبي</h3>", unsafe_allow_html=True)
    
    # الشريط الجانبي للإدخال
    with st.sidebar:
        st.header("➕ إضافة معاملة جديدة")
        
        نوع_المعاملة = st.radio("نوع المعاملة:", ["دخل 💵", "مصروف 💰"])
        مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, step=1000.0, value=0.0)
        وصف = st.text_input("وصف المعاملة:", placeholder="مثال: مرتب شهر يناير")
        
        if نوع_المعاملة == "مصروف 💰":
            فئة = st.selectbox("اختر الفئة:", الفئات)
        else:
            فئة = "دخل"
        
        if st.button("إضافة المعاملة", type="primary", use_container_width=True):
            if مبلغ > 0 and وصف.strip():
                if نوع_المعاملة == "دخل 💵":
                    st.session_state.المعاملات.append({
                        "النوع": "دخل",
                        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "المبلغ": مبلغ,
                        "الوصف": وصف,
                        "الفئة": "دخل"
                    })
                    st.session_state.الرصيد += مبلغ
                    st.success(f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} دينار ليبي")
                    st.rerun()
                else:
                    st.session_state.المعاملات.append({
                        "النوع": "مصروف",
                        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "المبلغ": مبلغ,
                        "الوصف": وصف,
                        "الفئة": فئة
                    })
                    st.session_state.الرصيد -= مبلغ
                    st.success(f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} دينار ليبي")
                    st.rerun()
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        if st.button("🔄 مسح جميع البيانات", use_container_width=True):
            st.session_state.المعاملات = []
            st.session_state.الرصيد = 0.0
            st.success("✅ تم مسح جميع البيانات")
            st.rerun()
    
    # حساب الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    # عرض الإحصائيات
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h4>💳 الرصيد الحالي</h4>
            <h3 style="color: #27ae60; margin: 0;">{st.session_state.الرصيد:,.2f} د.ل</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h4>💰 إجمالي الدخل</h4>
            <h3 style="color: #2980b9; margin: 0;">{إجمالي_الدخل:,.2f} د.ل</h3>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h4>💸 إجمالي المصروفات</h4>
            <h3 style="color: #e74c3c; margin: 0;">{إجمالي_المصروفات:,.2f} د.ل</h3>
        </div>
        """, unsafe_allow_html=True)
    
    # عرض المعاملات
    st.markdown("---")
    st.subheader("📋 آخر المعاملات")
    
    if st.session_state.المعاملات:
        for trans in reversed(st.session_state.المعاملات[-10:]):
            emoji = '💵' if trans['النوع'] == 'دخل' else '💰'
            color = '#27ae60' if trans['النوع'] == 'دخل' else '#e74c3c'
            st.markdown(f"""
            <div style="background: white; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {color}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{emoji} {trans['الوصف']}</strong><br>
                        <small style="color: #666;">📅 {trans['التاريخ']} | 📁 {trans['الفئة']}</small>
                    </div>
                    <div style="font-weight: bold; color: {color}; font-size: 1.1rem;">
                        {trans['المبلغ']:,.2f} د.ل
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        🎯 **ابدأ بإدارة ميزانيتك:**
        1. استخدم الشريط الجانبي لإضافة معاملة
        2. أدخل دخلك الشهري أولاً
        3. ثم أضف مصروفاتك اليومية
        4. تابع إحصائياتك تلقائياً
        """)

if __name__ == "__main__":
    main()