import streamlit as st
from datetime import datetime
import uuid

# إعداد الصفحة - يجب أن يكون في البداية
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# تهيئة session state - يجب أن يكون قبل أي استخدام لـ st
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'app_initialized' not in st.session_state:
    st.session_state.app_initialized = False

# محاولة تهيئة Supabase (بعد تهيئة session state)
try:
    import supabase
    supabase_client = supabase.create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    # اختبار الاتصال
    test_response = supabase_client.table('users').select('*').limit(1).execute()
    supabase_connected = True
except Exception as e:
    supabase_connected = False
    st.warning(f"⚡ الوضع المحلي: {e}")

# التصميم العربي
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .welcome-card {
        background: #f0f8ff;
        padding: 30px;
        border-radius: 15px;
        margin: 20px 0;
        border: 2px solid #2E86AB;
        text-align: center;
    }
    .stats-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# دوال إدارة البيانات
def get_user_data(user_id):
    if not supabase_connected:
        return None
    try:
        response = supabase_client.table('users').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    except:
        return None

def save_user_data(user_id, user_name, balance, transactions):
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
        
        existing = get_user_data(user_id)
        if existing:
            supabase_client.table('users').update(user_data).eq('user_id', user_id).execute()
        else:
            user_data['created_at'] = datetime.now().isoformat()
            supabase_client.table('users').insert(user_data).execute()
        return True
    except:
        return False

def show_welcome_screen():
    """عرض شاشة الترحيب وإدخال اسم المستخدم"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>💵 بالدينار الليبي</h3>", unsafe_allow_html=True)
    
    st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
    st.markdown("### 👋 مرحباً بك!")
    st.markdown("**أدخل اسمك لبدء إدارة ميزانيتك**")
    
    # استخدام form لتجنب مشاكل session state
    with st.form("user_form"):
        user_name = st.text_input(
            "اسم المستخدم:",
            placeholder="اكتب اسمك هنا...",
            key="user_name_input"
        )
        
        submit_button = st.form_submit_button(
            "🚀 بدء الاستخدام",
            type="primary",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submit_button and user_name.strip():
        # إنشاء معرف فريد للمستخدم
        st.session_state.user_id = str(uuid.uuid4())[:8]
        st.session_state.user_name = user_name.strip()
        st.session_state.app_initialized = True
        
        # تحميل البيانات إذا كانت موجودة
        if supabase_connected:
            user_data = get_user_data(st.session_state.user_id)
            if user_data:
                st.session_state.الرصيد = user_data.get('balance', 0.0)
                st.session_state.المعاملات = user_data.get('transactions', [])
        
        st.rerun()
    
    # عرض معلومات إضافية
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 💡 لماذا تدخل اسمك؟
        - **حفظ آمن** في السحابة
        - **وصول دائم** لبياناتك
        - **خصوصية كاملة**
        """)
    
    with col2:
        st.markdown("""
        ### 🌟 المميزات
        - تتبع الدخل والمصروفات
        - تقارير ذكية
        - تخزين سحابي
        """)

def show_main_app():
    """عرض التطبيق الرئيسي بعد إدخال اسم المستخدم"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #A23B72;'>👤 أهلاً بك {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    
    # حالة الاتصال
    if supabase_connected:
        st.success("✅ متصل بالسحابة - بياناتك محفوظة")
    else:
        st.warning("⚡ الوضع المحلي - البيانات مؤقتة")
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        
        st.markdown("---")
        st.markdown("### 💰 معاملة جديدة")
        
        # استخدام form للمعاملات
        with st.form("transaction_form"):
            نوع = st.radio("النوع:", ["دخل 💵", "مصروف 💰"])
            مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, value=0.0)
            وصف = st.text_input("وصف المعاملة:")
            
            if نوع == "مصروف 💰":
                فئة = st.selectbox("الفئة:", ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"])
            else:
                فئة = "دخل"
            
            submitted = st.form_submit_button("✅ إضافة المعاملة", type="primary")
            
            if submitted:
                if مبلغ > 0 and وصف.strip():
                    معاملة = {
                        "id": str(uuid.uuid4())[:8],
                        "النوع": "دخل" if نوع == "دخل 💵" else "مصروف",
                        "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "المبلغ": مبلغ,
                        "الوصف": وصف,
                        "الفئة": فئة
                    }
                    
                    st.session_state.المعاملات.append(معاملة)
                    
                    if نوع == "دخل 💵":
                        st.session_state.الرصيد += مبلغ
                    else:
                        st.session_state.الرصيد -= مبلغ
                    
                    # حفظ في السحابة
                    if supabase_connected:
                        save_user_data(
                            st.session_state.user_id, 
                            st.session_state.user_name, 
                            st.session_state.الرصيد, 
                            st.session_state.المعاملات
                        )
                    
                    st.success("✅ تمت إضافة المعاملة بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ يرجى إدخال المبلغ والوصف")
        
        st.markdown("---")
        st.markdown("### ⚙️ الأدوات")
        
        if st.button("🔄 مسح جميع البيانات", use_container_width=True):
            st.session_state.المعاملات = []
            st.session_state.الرصيد = 0.0
            if supabase_connected:
                save_user_data(st.session_state.user_id, st.session_state.user_name, 0.0, [])
            st.success("✅ تم مسح جميع البيانات")
            st.rerun()
        
        if st.button("🔙 تغيير المستخدم", use_container_width=True):
            st.session_state.user_name = ""
            st.session_state.app_initialized = False
            st.rerun()
    
    # الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💳 الرصيد الحالي</h3>
            <h2>{st.session_state.الرصيد:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💰 إجمالي الدخل</h3>
            <h2>{إجمالي_الدخل:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="stats-card">
            <h3>💸 إجمالي المصروفات</h3>
            <h2>{إجمالي_المصروفات:,.2f} د.ل</h2>
        </div>
        """, unsafe_allow_html=True)
    
    # سجل المعاملات
    st.markdown("---")
    st.markdown("### 📋 سجل المعاملات")
    
    if st.session_state.المعاملات:
        for trans in reversed(st.session_state.المعاملات):
            ايموجي = '💵' if trans['النوع'] == 'دخل' else '💰'
            لون = '#27ae60' if trans['النوع'] == 'دخل' else '#e74c3c'
            
            st.markdown(f"""
            <div style="background: white; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {لون};">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong>{ايموجي} {trans['الوصف']}</strong>
                        <div style="color: #666; font-size: 0.9em;">
                            📅 {trans['التاريخ']} • 📁 {trans['الفئة']}
                        </div>
                    </div>
                    <div style="font-weight: bold; color: {لون}; font-size: 1.1em;">
                        {trans['المبلغ']:,.2f} د.ل
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        ## 📝 لا توجد معاملات حتى الآن
        
        **ابدأ بإضافة أول معاملة من الشريط الجانبي:**
        1. اختر نوع المعاملة (دخل أو مصروف)
        2. أدخل المبلغ بالدينار الليبي
        3. اكتب وصفاً للمعاملة
        4. انقر "إضافة المعاملة"
        
        💡 **نصيحة**: ابدأ بإدخال دخلك الشهري أولاً
        """)

def main():
    """الدالة الرئيسية التي تتحكم في تدفق التطبيق"""
    if not st.session_state.app_initialized or not st.session_state.user_name:
        show_welcome_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()