import streamlit as st
from datetime import datetime
import supabase
import uuid
import json

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# 🔍 فحص شامل للاتصال
st.markdown("## 🔍 تقرير حالة النظام")

try:
    # محاولة الاتصال بـ Supabase
    supabase_client = supabase.create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    
    # اختبار الاتصال
    test_response = supabase_client.table('users').select('*').limit(1).execute()
    
    st.success("🎉 ✅ تم الاتصال بنجاح بقاعدة البيانات السحابية!")
    st.info(f"📊 تم العثور على {len(test_response.data)} مستخدم في النظام")
    
    supabase_connected = True
    
except Exception as e:
    st.error(f"❌ فشل الاتصال بقاعدة البيانات: {str(e)}")
    st.warning("⚡ التطبيق يعمل بالوضع المحلي فقط")
    supabase_connected = False

# ✨ تصميم عربي محسن
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #A23B72;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .user-card {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        color: white;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .transaction-income {
        background: #e8f5e8;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        border-left: 5px solid #27ae60;
    }
    .transaction-expense {
        background: #ffeaea;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        border-left: 5px solid #e74c3c;
    }
</style>
""", unsafe_allow_html=True)

# 📊 دوال إدارة البيانات
def get_user_data(user_id):
    """جلب بيانات المستخدم من السحابة"""
    if not supabase_connected:
        return None
    
    try:
        response = supabase_client.table('users').select('*').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            st.success("📥 تم تحميل بياناتك من السحابة بنجاح!")
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"❌ خطأ في جلب البيانات: {e}")
        return None

def save_user_data(user_id, user_name, balance, transactions):
    """حفظ بيانات المستخدم في السحابة"""
    if not supabase_connected:
        return False
    
    try:
        user_data = {
            'user_id': user_id,
            'user_name': user_name,
            'balance': float(balance),
            'transactions': transactions,
            'last_updated': datetime.now().isoformat()
        }
        
        # التحقق من وجود المستخدم
        existing_user = get_user_data(user_id)
        
        if existing_user:
            # تحديث البيانات الموجودة
            response = supabase_client.table('users').update(user_data).eq('user_id', user_id).execute()
            st.success("💾 تم تحديث بياناتك في السحابة")
        else:
            # إنشاء مستخدم جديد
            user_data['created_at'] = datetime.now().isoformat()
            response = supabase_client.table('users').insert(user_data).execute()
            st.success("🌟 تم إنشاء حساب جديد وحفظ بياناتك في السحابة")
        
        return True
    except Exception as e:
        st.error(f"❌ خطأ في حفظ البيانات: {e}")
        return False

def main():
    # 🎯 الواجهة الرئيسية
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h2 class='sub-header'>💵 بالدينار الليبي - التخزين السحابي المتقدم</h2>", unsafe_allow_html=True)
    
    # 🔄 إدارة حالة المستخدم
    if 'user_id' not in st.session_state:
        st.session_state.user_id = str(uuid.uuid4())[:8]
        st.session_state.الرصيد = 0.0
        st.session_state.المعاملات = []
        st.info("🆕 تم إنشاء جلسة مستخدم جديدة")

    # 👤 قسم إدارة المستخدم
    st.markdown("<div class='user-card'>", unsafe_allow_html=True)
    st.markdown("### 👤 إدارة حسابك السحابي")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        user_name = st.text_input(
            "**اسم المستخدم:**", 
            placeholder="أدخل اسمك لحفظ بياناتك في السحابة",
            key="user_name_input"
        )
    
    with col2:
        if st.button("💾 حفظ البيانات", use_container_width=True, key="save_cloud"):
            if user_name.strip():
                if supabase_connected:
                    save_user_data(st.session_state.user_id, user_name, st.session_state.الرصيد, st.session_state.المعاملات)
                else:
                    st.error("❌ غير متصل بالسحابة")
            else:
                st.error("❌ يرجى إدخال اسم المستخدم")
    
    with col3:
        if st.button("🔄 تحميل البيانات", use_container_width=True, key="load_cloud"):
            if user_name.strip() and supabase_connected:
                user_data = get_user_data(st.session_state.user_id)
                if user_data:
                    st.session_state.الرصيد = user_data.get('balance', 0.0)
                    st.session_state.المعاملات = user_data.get('transactions', [])
                    st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)

    # 📥 تحميل البيانات التلقائي
    if user_name.strip() and supabase_connected:
        user_data = get_user_data(st.session_state.user_id)
        if user_data and not st.session_state.get('data_loaded', False):
            st.session_state.الرصيد = user_data.get('balance', 0.0)
            st.session_state.المعاملات = user_data.get('transactions', [])
            st.session_state.data_loaded = True

    # 💰 الشريط الجانبي للإدخال
    with st.sidebar:
        st.markdown("### 💰 إدارة المعاملات")
        
        نوع_المعاملة = st.radio(
            "**نوع المعاملة:**", 
            ["دخل 💵", "مصروف 💰"], 
            key="transaction_type"
        )
        
        مبلغ = st.number_input(
            "**المبلغ (دينار ليبي):**", 
            min_value=0.0, 
            step=1000.0, 
            value=0.0,
            key="amount_input"
        )
        
        وصف = st.text_input(
            "**وصف المعاملة:**", 
            placeholder="مثال: مرتب شهر يناير أو سوق أسبوعي",
            key="description_input"
        )
        
        if نوع_المعاملة == "مصروف 💰":
            فئة = st.selectbox(
                "**اختر الفئة:**", 
                ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"],
                key="category_select"
            )
        else:
            فئة = "دخل"
        
        if st.button("✅ إضافة المعاملة", type="primary", use_container_width=True, key="add_transaction"):
            if مبلغ > 0 and وصف.strip():
                # إنشاء معاملة جديدة
                معاملة_جديدة = {
                    "id": str(uuid.uuid4())[:8],
                    "النوع": "دخل" if نوع_المعاملة == "دخل 💵" else "مصروف",
                    "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "المبلغ": float(مبلغ),
                    "الوصف": وصف,
                    "الفئة": فئة
                }
                
                # تحديث البيانات المحلية
                st.session_state.المعاملات.append(معاملة_جديدة)
                
                if نوع_المعاملة == "دخل 💵":
                    st.session_state.الرصيد += مبلغ
                    st.success(f"✅ تم إضافة دخل: **{وصف}** - {مبلغ:,.2f} دينار ليبي")
                else:
                    st.session_state.الرصيد -= مبلغ
                    st.success(f"✅ تم إضافة مصروف: **{وصف}** - {مبلغ:,.2f} دينار ليبي")
                
                # الحفظ التلقائي في السحابة
                if user_name.strip() and supabase_connected:
                    save_user_data(st.session_state.user_id, user_name, st.session_state.الرصيد, st.session_state.المعاملات)
                
                st.rerun()
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        st.markdown("### ⚙️ الأدوات المتقدمة")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 مسح الكل", use_container_width=True, key="clear_all"):
                st.session_state.المعاملات = []
                st.session_state.الرصيد = 0.0
                if user_name.strip() and supabase_connected:
                    save_user_data(st.session_state.user_id, user_name, 0.0, [])
                st.success("✅ تم مسح جميع البيانات")
                st.rerun()
        
        with col2:
            if st.button("📊 تحديث", use_container_width=True, key="refresh_app"):
                st.rerun()

    # 📈 عرض الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    st.markdown("## 📊 لوحة التحكم المالية")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💳 الرصيد الحالي</h3>
            <h2>{st.session_state.الرصيد:,.2f} د.ل</h2>
            <p>إجمالي ما تملكه حالياً</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💰 إجمالي الدخل</h3>
            <h2>{إجمالي_الدخل:,.2f} د.ل</h2>
            <p>مجموع دخلك الشهري</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💸 إجمالي المصروفات</h3>
            <h2>{إجمالي_المصروفات:,.2f} د.ل</h2>
            <p>مجموع إنفاقك الشهري</p>
        </div>
        """, unsafe_allow_html=True)

    # 📋 سجل المعاملات
    st.markdown("## 📋 السجل المالي")
    
    if st.session_state.المعاملات:
        for trans in reversed(st.session_state.المعاملات):
            if trans['النوع'] == 'دخل':
                st.markdown(f"""
                <div class="transaction-income">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <strong>💵 {trans['الوصف']}</strong>
                            <div style="color: #666; font-size: 0.9em;">
                                📅 {trans['التاريخ']} • 📁 {trans['الفئة']}
                            </div>
                        </div>
                        <div style="font-weight: bold; color: #27ae60; font-size: 1.2em;">
                            +{trans['المبلغ']:,.2f} د.ل
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="transaction-expense">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div style="flex: 1;">
                            <strong>💰 {trans['الوصف']}</strong>
                            <div style="color: #666; font-size: 0.9em;">
                                📅 {trans['التاريخ']} • 📁 {trans['الفئة']}
                            </div>
                        </div>
                        <div style="font-weight: bold; color: #e74c3c; font-size: 1.2em;">
                            -{trans['المبلغ']:,.2f} د.ل
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("""
        ## 🎯 مرحباً بك في نظام الميزانية المتقدم!
        
        ### 💡 كيف تبدأ:
        1. **أدخل اسمك** فوق لحفظ بياناتك في السحابة
        2. **أضف معاملة** من الشريط الجانبي
        3. **شاهد إحصائياتك** تلقائياً
        
        ### 🌟 الميزات الجديدة:
        - ✅ **تخزين سحابي آمن** - بياناتك محفوظة للأبد
        - ✅ **وصول من أي جهاز** - تابع ميزانيتك من أي مكان
        - ✅ **نسخ احتياطي تلقائي** - لا تفقد بياناتك أبداً
        - ✅ **واجهة عربية محسنة** - تجربة استخدام أفضل
        
        **جرب إضافة أول معاملة الآن!** 🚀
        """)

if __name__ == "__main__":
    main()