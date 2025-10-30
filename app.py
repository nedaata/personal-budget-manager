import streamlit as st
from datetime import datetime

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",  # ✅ تصحيح: الليبي بدل اللهبي
    page_icon="💵",
    layout="wide"
)

# التصميم العربي المصحح
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
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-right: 4px solid #2E86AB;
    }
    .transaction-card {
        background: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 4px solid #27ae60;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .expense-card {
        border-left-color: #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# الفئات
الفئات = ["الطعام", "مواصلات", "فواتير", "تسوق", "ترفيه", "صحة", "أخرى"]

# تهيئة البيانات - ✅ تصحيح: استخدام أسماء متغيرات صحيحة
if 'معاملات' not in st.session_state:
    st.session_state.معاملات = []
if 'رصيد' not in st.session_state:
    st.session_state.رصيد = 0.0

def main():
    st.markdown("<h1 class='main-title'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72; margin-bottom: 30px;'>💵 بالدينار الليبي</h3>", unsafe_allow_html=True)  # ✅ تصحيح

    # الشريط الجانبي
    with st.sidebar:
        st.header("➕ إضافة معاملة جديدة")
        
        نوع = st.radio("نوع المعاملة:", ["دخل 💵", "مصروف 💰"])
        مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, step=1000.0, value=0.0)
        وصف = st.text_input("وصف المعاملة:", placeholder="مثال: مرتب شهر يناير")
        
        if نوع == "مصروف 💰":
            فئة = st.selectbox("اختر الفئة:", الفئات)
        else:
            فئة = "دخل"
        
        if st.button("إضافة المعاملة", type="primary", use_container_width=True):
            if مبلغ > 0 and وصف.strip():
                معاملة = {
                    "نوع": "دخل" if نوع == "دخل 💵" else "مصروف",
                    "تاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "مبلغ": مبلغ,
                    "وصف": وصف,
                    "فئة": فئة
                }
                st.session_state.معاملات.append(معاملة)
                
                if نوع == "دخل 💵":
                    st.session_state.رصيد += مبلغ
                    st.success(f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} دينار ليبي")
                else:
                    st.session_state.رصيد -= مبلغ
                    st.success(f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} دينار ليبي")
                
                st.rerun()
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        st.header("⚙️ الأدوات")
        
        if st.button("🔄 مسح جميع البيانات", use_container_width=True):  # ✅ تصحيح: مسح بدل منح
            st.session_state.معاملات = []
            st.session_state.رصيد = 0.0
            st.success("✅ تم مسح جميع البيانات")
            st.rerun()

    # حساب الإحصائيات - ✅ تصحيح: استخدام المتغيرات الصحيحة
    إجمالي_الدخل = sum(trans['مبلغ'] for trans in st.session_state.معاملات if trans['نوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['مبلغ'] for trans in st.session_state.معاملات if trans['نوع'] == 'مصروف')
    
    # ✅ تصحيح: الرصيد الحالي محسوب بشكل صحيح
    الرصيد_الحالي = st.session_state.رصيد
    
    # عرض الإحصائيات - ✅ تصحيح: استخدام المتغيرات الصحيحة
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💳 الرصيد الحالي</h3>  <!-- ✅ تصحيح: الرصيد بدل الزصيد -->
            <h2 style="color: #27ae60;">{الرصيد_الحالي:,.2f} د.ل</h2>
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

    # تقرير المصروفات حسب الفئة
    st.markdown("---")
    st.subheader("📊 التقرير الشامل")
    
    if st.session_state.معاملات:
        # حساب المصروفات حسب الفئة
        مصروفات_حسب_الفئة = {}
        for trans in st.session_state.معاملات:
            if trans['نوع'] == 'مصروف':
                فئة = trans['فئة']
                مصروفات_حسب_الفئة[فئة] = مصروفات_حسب_الفئة.get(فئة, 0) + trans['مبلغ']
        
        if مصروفات_حسب_الفئة:
            st.write("**المصروفات حسب الفئة:**")
            for فئة, مبلغ in مصروفات_حسب_الفئة.items():
                نسبة = (مبلغ / إجمالي_المصروفات) * 100 if إجمالي_المصروفات > 0 else 0
                st.write(f"📁 **{فئة}**: {مبلغ:,.2f} د.ل ({نسبة:.1f}%)")
        
        # عرض المعاملات
        st.markdown("---")
        st.subheader("📋 آخر المعاملات")  # ✅ تصحيح: آخر بدل أخر
        
        for trans in reversed(st.session_state.معاملات[-10:]):
            ايموجي = '💵' if trans['نوع'] == 'دخل' else '💰'
            لون = '#27ae60' if trans['نوع'] == 'دخل' else '#e74c3c'
            فئة_كلاس = "" if trans['نوع'] == 'دخل' else "expense-card"
            
            st.markdown(f"""
            <div class="transaction-card {فئة_كلاس}">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>{ايموجي} {trans['وصف']}</strong>
                        <br>
                        <small style="color: #666;">📅 {trans['تاريخ']} | 📁 {trans['فئة']}</small>
                    </div>
                    <div style="font-size: 1.2rem; font-weight: bold; color: {لون}">
                        {trans['مبلغ']:,.2f} د.ل
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        🎯 **مرحباً بك في مدير الميزانية الشخصية!**
        
        **كيف تبدأ:**
        1. 💵 **أدخل دخلك** من الشريط الجانبي
        2. 💰 **سجل مصروفاتك** اليومية  
        3. 📊 **شاهد التقارير** تلقائياً
        4. 💾 **البيانات تحفظ** خلال جلستك
        
        **مثال:**
        - دخل: 500,000 د.ل (مرتب)
        - مصروف: 150,000 د.ل (سوق - طعام)
        - مصروف: 80,000 د.ل (بنزين - مواصلات)
        """)

if __name__ == "__main__":
    main()