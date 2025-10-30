import streamlit as st
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# التصميم العربي البسيط
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stats-card {
        background: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 4px solid #2E86AB;
    }
</style>
""", unsafe_allow_html=True)

# الفئات الأساسية
الفئات = ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"]

# تهيئة البيانات - الطريقة البسيطة
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0

def main():
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72; margin-bottom: 30px;'>💵 بالدينار الليبي</h3>", unsafe_allow_html=True)

    # الشريط الجانبي للإدخال
    with st.sidebar:
        st.header("➕ إضافة معاملة جديدة")
        
        # إدخال البيانات الأساسية
        نوع_المعاملة = st.radio("نوع المعاملة:", ["دخل 💵", "مصروف 💰"])
        مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, step=1000.0, value=0.0)
        وصف = st.text_input("وصف المعاملة:")
        
        if نوع_المعاملة == "مصروف 💰":
            فئة = st.selectbox("اختر الفئة:", الفئات)
        else:
            فئة = "دخل"
        
        # زر الإضافة
        if st.button("إضافة المعاملة", type="primary"):
            if مبلغ > 0 and وصف.strip():
                # إضافة المعاملة
                معاملة_جديدة = {
                    "النوع": "دخل" if نوع_المعاملة == "دخل 💵" else "مصروف",
                    "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "المبلغ": مبلغ,
                    "الوصف": وصف,
                    "الفئة": فئة
                }
                
                st.session_state.المعاملات.append(معاملة_جديدة)
                
                # تحديث الرصيد
                if نوع_المعاملة == "دخل 💵":
                    st.session_state.الرصيد += مبلغ
                    st.success(f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} دينار ليبي")
                else:
                    st.session_state.الرصيد -= مبلغ
                    st.success(f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} دينار ليبي")
                
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        st.header("الأدوات")
        
        # زر مسح البيانات
        if st.button("مسح جميع البيانات"):
            st.session_state.المعاملات = []
            st.session_state.الرصيد = 0.0
            st.success("✅ تم مسح جميع البيانات")

    # حساب الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    # عرض الإحصائيات
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💳 الرصيد الحالي</h3>
            <h2 style="color: #27ae60;">{st.session_state.الرصيد:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💰 إجمالي الدخل</h3>
            <h2 style="color: #2980b9;">{إجمالي_الدخل:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💸 إجمالي المصروفات</h3>
            <h2 style="color: #e74c3c;">{إجمالي_المصروفات:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)

    # عرض المعاملات الحديثة
    st.markdown("---")
    st.subheader("📋 آخر المعاملات")
    
    if st.session_state.المعاملات:
        for i, trans in enumerate(reversed(st.session_state.المعاملات[-5:]), 1):
            ايموجي = '💵' if trans['النوع'] == 'دخل' else '💰'
            لون = '#27ae60' if trans['النوع'] == 'دخل' else '#e74c3c'
            
            st.write(f"""
            <div style="background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid {لون}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{ايموجي} {trans['الوصف']}</strong><br>
                        <small style="color: #666;">{trans['التاريخ']} • {trans['الفئة']}</small>
                    </div>
                    <div style="font-weight: bold; color: {لون}; font-size: 1.1rem;">
                        {trans['المبلغ']:,.2f} د.ل
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("لا توجد معاملات مسجلة بعد. ابدأ بإضافة معاملة من الشريط الجانبي.")

if __name__ == "__main__":
    main()