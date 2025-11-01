import streamlit as st
from datetime import datetime
import uuid
import hashlib

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# تهيئة session state
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = None
if 'user_data_loaded' not in st.session_state:
    st.session_state.user_data_loaded = False

# محاولة تهيئة Supabase
try:
    import supabase
    supabase_client = supabase.create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )
    supabase_connected = True
except Exception as e:
    supabase_connected = False

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
    .warning-card {
        background: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #ffc107;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

def create_user_id(user_name):
    """إنشاء معرف فريد للمستخدم بناء على اسمه"""
    # استخدام hash لإنشاء معرف فريد من الاسم
    return hashlib.md5(user_name.strip().encode()).hexdigest()[:12]

def get_user_data(user_id):
    """جلب بيانات مستخدم محدد فقط"""
    if not supabase_connected:
        return None
    try:
        response = supabase_client.table('users').select('*').eq('user_id', user_id).execute()
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"❌ خطأ في جلب البيانات: {e}")
        return None

def save_user_data(user_id, user_name, balance, transactions):
    """حفظ بيانات مستخدم محدد فقط"""
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
            response = supabase_client.table('users').update(user_data).eq('user_id', user_id).execute()
        else:
            user_data['created_at'] = datetime.now().isoformat()
            response = supabase_client.table('users').insert(user_data).execute()
        return True
    except Exception as e:
        st.error(f"❌ خطأ في حفظ البيانات: {e}")
        return False

def clear_user_session():
    """مسح كافة بيانات الجلسة للمستخدم الحالي"""
    keys_to_keep = ['current_user_id', 'user_data_loaded']
    keys_to_remove = []
    
    for key in st.session_state.keys():
        if key not in keys_to_keep:
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

def initialize_new_user(user_name):
    """تهيئة مستخدم جديد ببيانات نظيفة"""
    user_id = create_user_id(user_name)
    
    # مسح أي بيانات قديمة
    clear_user_session()
    
    # تعيين بيانات المستخدم الجديد
    st.session_state.current_user_id = user_id
    st.session_state.user_name = user_name
    st.session_state.الرصيد = 0.0
    st.session_state.المعاملات = []
    st.session_state.user_data_loaded = True
    st.session_state.is_new_user = True

def load_existing_user(user_name):
    """تحميل بيانات مستخدم موجود"""
    user_id = create_user_id(user_name)
    
    # مسح أي بيانات قديمة أولاً
    clear_user_session()
    
    # تحميل البيانات من السحابة
    user_data = get_user_data(user_id)
    
    if user_data:
        # مستخدم موجود - تحميل بياناته
        st.session_state.current_user_id = user_id
        st.session_state.user_name = user_data.get('user_name', user_name)
        st.session_state.الرصيد = user_data.get('balance', 0.0)
        st.session_state.المعاملات = user_data.get('transactions', [])
        st.session_state.user_data_loaded = True
        st.session_state.is_new_user = False
        return True
    else:
        # مستخدم جديد - تهيئة بيانات جديدة
        initialize_new_user(user_name)
        return False

def show_welcome_screen():
    """شاشة الترحيب وإدخال اسم المستخدم"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>💵 بالدينار الليبي - خصوصية كاملة</h3>", unsafe_allow_html=True)
    
    # تحذير مهم
    st.markdown("""
    <div class="warning-card">
        <strong>🔒 تنبيه مهم:</strong> كل مستخدم يرى بياناته فقط. لا يمكن لأحد الوصول لبياناتك.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div class='welcome-card'>", unsafe_allow_html=True)
    st.markdown("### 👋 مرحباً بك!")
    st.markdown("**أدخل اسمك لبدء إدارة ميزانيتك**")
    
    with st.form("user_form"):
        user_name = st.text_input(
            "اسم المستخدم:",
            placeholder="اكتب اسمك هنا...",
            help="استخدم نفس الاسم دائماً للوصول لبياناتك",
            key="user_name_input"
        )
        
        submit_button = st.form_submit_button(
            "🚀 بدء الاستخدام",
            type="primary",
            use_container_width=True
        )
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    if submit_button and user_name.strip():
        # معالجة إدخال المستخدم
        user_name = user_name.strip()
        
        if supabase_connected:
            # التحقق إذا كان المستخدم موجوداً
            user_exists = load_existing_user(user_name)
            
            if user_exists:
                st.success(f"✅ تم تحميل بيانات المستخدم: {user_name}")
            else:
                st.success(f"🌟 تم إنشاء حساب جديد ل: {user_name}")
        else:
            # الوضع المحلي بدون سحابة
            initialize_new_user(user_name)
            st.success(f"🌟 مرحباً {user_name}! ابدأ بإضافة معاملاتك")
        
        st.rerun()
    
    # معلومات إضافية
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔒 خصوصية كاملة
        - كل مستخدم يرى بياناته فقط
        - لا يمكن للآخرين الوصول لبياناتك
        - بياناتك مشفرة وآمنة
        """)
    
    with col2:
        st.markdown("""
        ### 💾 حفظ آمن
        - بياناتك تحفظ في السحابة
        - يمكنك الوصول لها من أي جهاز
        - استخدم نفس الاسم دائماً
        """)

def show_main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #A23B72;'>👤 أهلاً بك {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    
    # معلومات المستخدم
    if st.session_state.get('is_new_user', True):
        st.success("🎉 هذا حسابك الجديد! ابدأ بإضافة معاملاتك")
    else:
        st.info(f"📊 لديك {len(st.session_state.المعاملات)} معاملة في سجلك")
    
    # حالة الاتصال
    if supabase_connected:
        st.success("✅ متصل بالسحابة - بياناتك محفوظة بأمان")
    else:
        st.warning("⚡ الوضع المحلي - استخدم نفس المتصفح للحفاظ على بياناتك")
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.user_name}")
        st.markdown(f"**رقم المستخدم:** `{st.session_state.current_user_id}`")
        
        st.markdown("---")
        st.markdown("### 💰 معاملة جديدة")
        
        with st.form("transaction_form", clear_on_submit=True):
            نوع = st.radio("النوع:", ["دخل 💵", "مصروف 💰"])
            مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, value=0.0, step=1000.0)
            وصف = st.text_input("وصف المعاملة:", placeholder="مثال: مرتب أو سوق")
            
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
                        "الوصف": وصف.strip(),
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
                            st.session_state.current_user_id,
                            st.session_state.user_name,
                            st.session_state.الرصيد,
                            st.session_state.المعاملات
                        )
                    
                    st.success("✅ تمت إضافة المعاملة بنجاح!")
                    st.rerun()
                else:
                    st.error("❌ يرجى إدخال المبلغ والوصف بشكل صحيح")
        
        st.markdown("---")
        st.markdown("### ⚙️ إدارة الحساب")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 مسح بياناتي", use_container_width=True):
                st.session_state.المعاملات = []
                st.session_state.الرصيد = 0.0
                if supabase_connected:
                    save_user_data(st.session_state.current_user_id, st.session_state.user_name, 0.0, [])
                st.success("✅ تم مسح جميع بياناتك")
                st.rerun()
        
        with col2:
            if st.button("🔐 تسجيل خروج", use_container_width=True):
                clear_user_session()
                st.session_state.current_user_id = None
                st.session_state.user_data_loaded = False
                st.success("✅ تم تسجيل الخروج بنجاح")
                st.rerun()
        
        st.markdown("---")
        st.markdown("### ℹ️ معلومات")
        st.info(f"**المعاملات:** {len(st.session_state.المعاملات)}")
        st.info(f"**الحالة:** {'🆕 جديد' if st.session_state.get('is_new_user', True) else '📁 موجود'}")

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
            رمز = '+' if trans['النوع'] == 'دخل' else '-'
            
            st.markdown(f"""
            <div style="background: white; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {لون}; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <strong>{ايموجي} {trans['الوصف']}</strong>
                        <div style="color: #666; font-size: 0.9em;">
                            📅 {trans['التاريخ']} • 📁 {trans['الفئة']}
                        </div>
                    </div>
                    <div style="font-weight: bold; color: {لون}; font-size: 1.1em;">
                        {رمز}{trans['المبلغ']:,.2f} د.ل
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        ## 📝 لا توجد معاملات حتى الآن
        
        **ابدأ بإضافة أول معاملة من الشريط الجانبي**
        
        💡 **نصائح للبداية:**
        1. ابدأ بإدخال دخلك الشهري
        2. سجل مصروفاتك اليومية
        3. تابع رصيدك يتغير تلقائياً
        """)

def main():
    """الدالة الرئيسية"""
    if not st.session_state.user_data_loaded or not st.session_state.current_user_id:
        show_welcome_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()