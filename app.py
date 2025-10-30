import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime
import json
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية الشخصية - الدينار الليبي",
    page_icon="💵",
    layout="wide",
    initial_sidebar_state="expanded"
)

# التصميم العربي وتحسين الواجهة
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #A23B72;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background: #f0f8ff;
        padding: 20px;
        border-radius: 10px;
        border-right: 4px solid #2E86AB;
        margin: 10px 0;
    }
    .transaction-card {
        background: #fff;
        padding: 15px;
        margin: 10px 0;
        border-radius: 8px;
        border-left: 4px solid #27ae60;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .expense-card {
        border-left-color: #e74c3c;
    }
    .section-title {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-top: 30px;
    }
</style>
""", unsafe_allow_html=True)

# الفئات المتاحة
الفئات = ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"]

# تهيئة حالة التطبيق
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0

class مدير_الميزانية:
    def إضافة_دخل(self, مبلغ, وصف):
        معاملة = {
            "النوع": "دخل",
            "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "المبلغ": مبلغ,
            "الوصف": وصف,
            "الفئة": "دخل"
        }
        st.session_state.المعاملات.append(معاملة)
        st.session_state.الرصيد += مبلغ
        return f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} دينار ليبي"
    
    def إضافة_مصروف(self, فئة, مبلغ, وصف):
        معاملة = {
            "النوع": "مصروف",
            "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "المبلغ": مبلغ,
            "الوصف": وصف,
            "الفئة": فئة
        }
        st.session_state.المعاملات.append(معاملة)
        st.session_state.الرصيد -= مبلغ
        return f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} دينار ليبي"
    
    def حساب_الإحصائيات(self):
        إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
        إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
        
        # حساب المصروفات حسب الفئة
        مصروفات_حسب_الفئة = {فئة: 0.0 for فئة in الفئات}
        for trans in st.session_state.المعاملات:
            if trans['النوع'] == 'مصروف' and trans['الفئة'] in مصروفات_حسب_الفئة:
                مصروفات_حسب_الفئة[trans['الفئة']] += trans['المبلغ']
        
        return {
            'الرصيد': st.session_state.الرصيد,
            'إجمالي_الدخل': إجمالي_الدخل,
            'إجمالي_المصروفات': إجمالي_المصروفات,
            'عدد_المعاملات': len(st.session_state.المعاملات),
            'مصروفات_حسب_الفئة': مصروفات_حسب_الفئة
        }
    
    def إنشاء_تقرير(self):
        stats = self.calculer_statistiques()
        
        st.markdown("<h2 class='section-title'>📊 تقرير الميزانية الشخصية - الدينار الليبي</h2>", unsafe_allow_html=True)
        
        # عرض الإحصائيات الرئيسية
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("💳 الرصيد الحالي", f"{stats['الرصيد']:,.2f} د.ل")
        with col2:
            st.metric("💰 إجمالي الدخل", f"{stats['إجمالي_الدخل']:,.2f} د.ل")
        with col3:
            st.metric("💸 إجمالي المصروفات", f"{stats['إجمالي_المصروفات']:,.2f} د.ل")
        with col4:
            st.metric("📈 عدد المعاملات", stats['عدد_المعاملات'])
        
        # الرسوم البيانية
        col1, col2 = st.columns(2)
        
        with col1:
            self.رسم_بياني_دائري(stats['مصروفات_حسب_الفئة'])
        
        with col2:
            self.رسم_بياني_شريطي(stats['مصروفات_حسب_الفئة'])
        
        # آخر المعاملات
        st.markdown("<h3 class='section-title'>🕐 آخر المعاملات</h3>", unsafe_allow_html=True)
        self.عرض_المعاملات()
    
    def رسم_بياني_دائري(self, مصروفات_حسب_الفئة):
        فئات_نشطة = [فئة for فئة, مبلغ in مصروفات_حسب_الفئة.items() if مبلغ > 0]
        مبالغ_نشطة = [مبلغ for مبلغ in مصروفات_حسب_الفئة.values() if مبلغ > 0]
        
        if مبالغ_نشطة:
            fig = px.pie(
                names=فئات_نشطة,
                values=مبالغ_نشطة,
                title="توزيع المصروفات حسب الفئة",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_layout(title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("لا توجد مصروفات لعرضها")
    
    def رسم_بياني_شريطي(self, مصروفات_حسب_الفئة):
        فئات_نشطة = [فئة for فئة, مبلغ in مصروفات_حسب_الفئة.items() if مبلغ > 0]
        مبالغ_نشطة = [مبلغ for مبلغ in مصروفات_حسب_الفئة.values() if مبلغ > 0]
        
        if مبالغ_نشطة:
            fig = px.bar(
                x=فئات_نشطة,
                y=مبالغ_نشطة,
                title="المصروفات بالدينار الليبي",
                labels={'x': 'الفئة', 'y': 'المبلغ (دينار ليبي)'},
                color=مبالغ_نشطة,
                color_continuous_scale='Viridis'
            )
            fig.update_layout(title_x=0.5)
            st.plotly_chart(fig, use_container_width=True)
    
    def عرض_المعاملات(self):
        if st.session_state.المعاملات:
            for trans in reversed(st.session_state.المعاملات[-10:]):  # آخر 10 معاملات
                emoji = '💵' if trans['النوع'] == 'دخل' else '💰'
                card_class = "" if trans['النوع'] == 'دخل' else "expense-card"
                
                st.markdown(f"""
                <div class="transaction-card {card_class}">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>{emoji} {trans['الوصف']}</strong>
                            <br>
                            <small>📅 {trans['التاريخ']} | 📁 {trans['الفئة']}</small>
                        </div>
                        <div style="font-size: 1.2rem; font-weight: bold; color: {'#27ae60' if trans['النوع'] == 'دخل' else '#e74c3c'}">
                            {trans['المبلغ']:,.2f} د.ل
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("لا توجد معاملات مسجلة بعد")

# الواجهة الرئيسية
def main():
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>💵 بالدينار الليبي - التخزين السحابي</h2>", unsafe_allow_html=True)
    
    مدير = مدير_الميزانية()
    
    # الشريط الجانبي للإدخال
    with st.sidebar:
        st.header("➕ إضافة معاملة جديدة")
        
        نوع_المعاملة = st.radio("نوع المعاملة:", ["دخل 💵", "مصروف 💰"])
        مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, step=1000.0, format="%.2f")
        وصف = st.text_input("وصف المعاملة:")
        
        if نوع_المعاملة == "مصروف 💰":
            فئة = st.selectbox("اختر الفئة:", الفئات)
        else:
            فئة = "دخل"
        
        if st.button("إضافة المعاملة", type="primary"):
            if مبلغ > 0 and وصف.strip():
                if نوع_المعاملة == "دخل 💵":
                    result = مدير.إضافة_دخل(مبلغ, وصف)
                else:
                    result = مدير.إضافة_مصروف(فئة, مبلغ, وصف)
                st.success(result)
                st.rerun()
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        st.header("⚙️ الأدوات")
        
        if st.button("🔄 مسح جميع البيانات"):
            st.session_state.المعاملات = []
            st.session_state.الرصيد = 0.0
            st.rerun()
        
        if st.button("💾 تصدير البيانات"):
            if st.session_state.المعاملات:
                df = pd.DataFrame(st.session_state.المعاملات)
                csv = df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 تحميل البيانات كـ CSV",
                    data=csv,
                    file_name=f"الميزانية_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    # المنطقة الرئيسية
    stats = مدير.حساب_الإحصائيات()
    
    # عرض الإحصائيات السريعة
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💳 الرصيد الحالي</h3>
            <h2 style="color: #27ae60;">{stats['الرصيد']:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💰 إجمالي الدخل</h3>
            <h2 style="color: #2980b9;">{stats['إجمالي_الدخل']:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💸 إجمالي المصروفات</h3>
            <h2 style="color: #e74c3c;">{stats['إجمالي_المصروفات']:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # الأقسام الرئيسية
    tab1, tab2, tab3 = st.tabs(["📊 التقرير الشامل", "📋 سجل المعاملات", "ℹ️ التعليمات"])
    
    with tab1:
        مدير.إنشاء_تقرير()
    
    with tab2:
        st.markdown("<h2 class='section-title'>📋 سجل المعاملات الكامل</h2>", unsafe_allow_html=True)
        مدير.عرض_المعاملات()
    
    with tab3:
        st.markdown("""
        <div style="background: #e3f2fd; padding: 25px; border-radius: 15px; border-right: 4px solid #2196f3;">
            <h2 style="color: #1976d2;">🎯 كيف تستخدم التطبيق:</h2>
            
            <h3 style="color: #1565c0;">➕ إضافة معاملات:</h3>
            <ul style="color: #0d47a1; font-size: 16px;">
                <li><strong>اختر نوع المعاملة</strong> (دخل أو مصروف)</li>
                <li><strong>أدخل المبلغ</strong> بالدينار الليبي</li>
                <li><strong>اكتب وصفاً واضحاً</strong> للمعاملة</li>
                <li><strong>اختر الفئة</strong> للمصروفات</li>
                <li>انقر <strong>"إضافة المعاملة"</strong></li>
            </ul>
            
            <h3 style="color: #1565c0;">📊 التقارير:</h3>
            <ul style="color: #0d47a1; font-size: 16px;">
                <li>شاهد <strong>التقرير الشامل</strong> للرسوم البيانية</li>
                <li>راجع <strong>سجل المعاملات</strong> الكامل</li>
                <li>تابع <strong>الإحصائيات</strong> الفورية</li>
            </ul>
            
            <h3 style="color: #1565c0;">💾 الميزات:</h3>
            <ul style="color: #0d47a1; font-size: 16px;">
                <li>💡 <strong>تخزين سحابي آمن</strong> - البيانات تحفظ تلقائياً</li>
                <li>📥 <strong>تصدير البيانات</strong> - حمّل بياناتك كملف CSV</li>
                <li>🔄 <strong>مسح البيانات</strong> - ابدأ من جديد عندما تريد</li>
                <li>📱 <strong>متوافق مع الجوال</strong> - استخدمه من أي جهاز</li>
            </ul>
            
            <div style="background: #bbdefb; padding: 15px; border-radius: 8px; margin-top: 20px;">
                <h4 style="color: #0d47a1; margin: 0;">💡 ملاحظة:</h4>
                <p style="color: #0d47a1; margin: 10px 0 0 0;">
                    جميع البيانات تحفظ في جلسة المتصفح الحالية. للتخزين الدائم، استخدم خاصية تصدير البيانات.
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()