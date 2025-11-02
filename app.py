import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
import time

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# تهيئة session state بشكل كامل
if 'current_user_id' not in st.session_state:
    st.session_state.current_user_id = None
if 'user_data_loaded' not in st.session_state:
    st.session_state.user_data_loaded = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = 0
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'show_main_app' not in st.session_state:
    st.session_state.show_main_app = False
if 'force_rerun' not in st.session_state:
    st.session_state.force_rerun = False

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
    st.warning("⚠️ الوضع غير متصل - البيانات محفوظة محلياً فقط")

# التصميم العربي
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
    }
    .login-card {
        background: #f8f9fa;
        padding: 30px;
        border-radius: 15px;
        margin: 20px auto;
        border: 2px solid #dee2e6;
        max-width: 500px;
    }
    .security-alert {
        background: #fff3cd;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #ffc107;
        color: #856404;
        margin: 10px 0;
    }
    .user-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

def hash_password(password):
    """تشفير كلمة المرور"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_id(user_name):
    """إنشاء معرف فريد للمستخدم"""
    return hashlib.md5(user_name.strip().encode()).hexdigest()[:12]

def validate_password(password):
    """التحقق من قوة كلمة المرور"""
    if len(password) < 6:
        return False, "❌ كلمة المرور يجب أن تكون 6 أحرف على الأقل"
    
    if not re.search(r"[A-Za-z]", password):
        return False, "❌ كلمة المرور يجب أن تحتوي على أحرف"
    
    if not re.search(r"\d", password):
        return False, "❌ كلمة المرور يجب أن تحتوي على أرقام"
    
    return True, "✅ كلمة المرور قوية"

def check_username_available(user_name):
    """التحقق إذا كان اسم المستخدم متاح"""
    if not supabase_connected:
        return True
    
    try:
        user_id = create_user_id(user_name)
        response = supabase_client.table('users').select('user_id').eq('user_id', user_id).execute()
        return len(response.data) == 0
    except:
        return False

def get_user_data(user_id):
    """جلب بيانات المستخدم"""
    if not supabase_connected:
        return None
    try:
        response = supabase_client.table('users').select('*').eq('user_id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        st.error(f"خطأ في جلب البيانات: {e}")
        return None

def create_user_account(user_id, user_name, password_hash):
    """إنشاء حساب مستخدم جديد"""
    if not supabase_connected:
        # في حالة عدم الاتصال، نستخدم التخزين المحلي
        st.session_state.current_user_id = user_id
        st.session_state.user_name = user_name
        st.session_state.الرصيد = 0.0
        st.session_state.المعاملات = []
        st.session_state.user_data_loaded = True
        st.session_state.show_main_app = True
        return True
    
    try:
        user_data = {
            'user_id': user_id,
            'user_name': user_name,
            'password_hash': password_hash,
            'balance': 0.0,
            'transactions': [],
            'created_at': datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat()
        }
        
        response = supabase_client.table('users').insert(user_data).execute()
        
        # تهيئة الجلسة بعد إنشاء الحساب
        st.session_state.current_user_id = user_id
        st.session_state.user_name = user_name
        st.session_state.الرصيد = 0.0
        st.session_state.المعاملات = []
        st.session_state.user_data_loaded = True
        st.session_state.show_main_app = True
        
        return True
    except Exception as e:
        st.error(f"خطأ في إنشاء الحساب: {e}")
        return False

def update_user_data(user_id, balance, transactions):
    """تحديث بيانات المستخدم"""
    if not supabase_connected:
        return True  # في الوضع غير المتصل، نعتبر أن الحفظ ناجح
    
    try:
        user_data = {
            'balance': float(balance),
            'transactions': transactions,
            'last_updated': datetime.now().isoformat()
        }
        
        response = supabase_client.table('users').update(user_data).eq('user_id', user_id).execute()
        return True
    except Exception as e:
        st.error(f"خطأ في حفظ البيانات: {e}")
        return False

def verify_password(user_id, password):
    """التحقق من كلمة المرور"""
    if not supabase_connected:
        # في الوضع غير المتصل، نستخدم بيانات الجلسة المحلية
        return st.session_state.current_user_id == user_id
    
    user_data = get_user_data(user_id)
    if not user_data:
        return False
    
    stored_hash = user_data.get('password_hash')
    if not stored_hash:
        return False
    
    return stored_hash == hash_password(password)

def show_login_screen():
    """شاشة تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>🔐 نظام آمن بكلمة مرور فريدة</h3>", unsafe_allow_html=True)
    
    # معلومات النظام
    st.markdown("""
    <div class="security-alert">
        <strong>🎯 المميزات الجديدة:</strong><br>
        • كل مستخدم يحتاج اسم وكلمة مرور فريدة<br>
        • لا يمكن تكرار اسم المستخدم<br>
        • بياناتك محفوظة بشكل منفصل وآمن<br>
        • يمكنك الوصول لبياناتك من أي جهاز
    </div>
    """, unsafe_allow_html=True)
    
    # تبويبات للتسجيل/الدخول
    tab1, tab2 = st.tabs(["🚀 إنشاء حساب جديد", "🔐 تسجيل الدخول"])
    
    with tab1:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("### 🆕 إنشاء حساب جديد")
        
        with st.form("register_form"):
            new_username = st.text_input(
                "اسم المستخدم الجديد:",
                placeholder="اختر اسم مستخدم فريد...",
                help="هذا الاسم لا يمكن لأحد آخر استخدامه"
            )
            
            new_password = st.text_input(
                "كلمة المرور:",
                type="password",
                placeholder="كلمة مرور قوية...",
                help="6 أحرف على الأقل، تحتوي على أحرف وأرقام"
            )
            
            confirm_password = st.text_input(
                "تأكيد كلمة المرور:",
                type="password",
                placeholder="أعد كتابة كلمة المرور..."
            )
            
            register_button = st.form_submit_button(
                "🎯 إنشاء حسابي الجديد",
                use_container_width=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if register_button:
            if not new_username.strip():
                st.error("❌ يرجى إدخال اسم المستخدم")
            elif not new_password:
                st.error("❌ يرجى إدخال كلمة المرور")
            elif new_password != confirm_password:
                st.error("❌ كلمتا المرور غير متطابقتين")
            else:
                # التحقق من قوة كلمة المرور
                is_valid, message = validate_password(new_password)
                if not is_valid:
                    st.error(message)
                else:
                    # التحقق من توفر اسم المستخدم
                    if not check_username_available(new_username):
                        st.error("❌ اسم المستخدم موجود مسبقاً، اختر اسماً آخر")
                    else:
                        # إنشاء الحساب
                        user_id = create_user_id(new_username.strip())
                        password_hash = hash_password(new_password)
                        
                        success = create_user_account(user_id, new_username.strip(), password_hash)
                        
                        if success:
                            st.success("🎉 تم إنشاء حسابك بنجاح!")
                            st.balloons()
                            # بدلاً من rerun، نستخدم علامة للتحويل للواجهة الرئيسية
                            st.session_state.show_main_app = True
                            time.sleep(1)
                            st.experimental_rerun()
                        else:
                            st.error("❌ فشل في إنشاء الحساب، حاول مرة أخرى")
    
    with tab2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("### 🔐 تسجيل الدخول لحسابك")
        
        with st.form("login_form"):
            username = st.text_input(
                "اسم المستخدم:",
                placeholder="أدخل اسم المستخدم..."
            )
            
            password = st.text_input(
                "كلمة المرور:",
                type="password",
                placeholder="أدخل كلمة المرور..."
            )
            
            login_button = st.form_submit_button(
                "🚀 الدخول إلى حسابي",
                use_container_width=True
            )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        if login_button:
            if not username.strip() or not password:
                st.error("❌ يرجى إدخال اسم المستخدم وكلمة المرور")
            else:
                user_id = create_user_id(username.strip())
                
                if verify_password(user_id, password):
                    # تسجيل الدخول الناجح
                    user_data = get_user_data(user_id)
                    
                    if not user_data and supabase_connected:
                        st.error("❌ حساب غير موجود")
                    else:
                        # تهيئة الجلسة
                        st.session_state.current_user_id = user_id
                        st.session_state.user_name = username.strip()
                        
                        if user_data:
                            st.session_state.الرصيد = user_data.get('balance', 0.0)
                            st.session_state.المعاملات = user_data.get('transactions', [])
                        else:
                            st.session_state.الرصيد = 0.0
                            st.session_state.المعاملات = []
                            
                        st.session_state.user_data_loaded = True
                        st.session_state.login_attempts = 0
                        st.session_state.show_main_app = True
                        
                        st.success(f"✅ تم تسجيل الدخول بنجاح! أهلاً بك {username.strip()}")
                        time.sleep(1)
                        st.experimental_rerun()
                else:
                    st.session_state.login_attempts += 1
                    remaining_attempts = 5 - st.session_state.login_attempts
                    
                    if st.session_state.login_attempts >= 5:
                        st.error("🚫 تم تجاوز عدد المحاولات المسموح بها")
                    else:
                        st.error(f"❌ بيانات الدخول غير صحيحة. محاولات متبقية: {remaining_attempts}")

def show_main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #A23B72;'>👤 أهلاً بك {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    
    # بطاقة المستخدم
    st.markdown(f"""
    <div class="user-card">
        <h3>👤 {st.session_state.user_name}</h3>
        <p>🆔 المعرف: {st.session_state.current_user_id}</p>
        <p>📊 {len(st.session_state.المعاملات)} معاملة محفوظة</p>
    </div>
    """, unsafe_allow_html=True)
    
    # الشريط الجانبي
    with st.sidebar:
        st.markdown("### 💰 معاملة جديدة")
        
        with st.form("transaction_form", clear_on_submit=True):
            نوع = st.radio("النوع:", ["دخل 💵", "مصروف 💰"])
            مبلغ = st.number_input("المبلغ (دينار ليبي):", min_value=0.0, value=0.0, step=1000.0)
            وصف = st.text_input("وصف المعاملة:", placeholder="مثال: مرتب أو سوق")
            
            if نوع == "مصروف 💰":
                فئة = st.selectbox("الفئة:", ["الطعام", "المواصلات", "الفواتير", "التسوق", "الترفيه", "الصحة", "أخرى"])
            else:
                فئة = "دخل"
            
            submitted = st.form_submit_button("💾 إضافة المعاملة", use_container_width=True)
            
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
                        st.success(f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} د.ل")
                    else:
                        st.session_state.الرصيد -= مبلغ
                        st.success(f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} د.ل")
                    
                    # حفظ البيانات
                    if supabase_connected:
                        if update_user_data(st.session_state.current_user_id, st.session_state.الرصيد, st.session_state.المعاملات):
                            st.success("💾 تم حفظ البيانات في السحابة")
                    
                    # لا نحتاج لإعادة التحميل هنا
                    
                else:
                    st.error("❌ يرجى إدخال المبلغ والوصف")
        
        st.markdown("---")
        st.markdown("### ⚙️ إدارة الحساب")
        
        if st.button("🔄 مسح جميع بياناتي", use_container_width=True):
            st.session_state.المعاملات = []
            st.session_state.الرصيد = 0.0
            if supabase_connected:
                update_user_data(st.session_state.current_user_id, 0.0, [])
            st.success("✅ تم مسح جميع بياناتك")
        
        if st.button("🔐 تسجيل خروج", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['login_attempts']:
                    del st.session_state[key]
            st.session_state.show_main_app = False
            st.success("✅ تم تسجيل الخروج بنجاح")
            time.sleep(1)
            st.experimental_rerun()

    # الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("💳 الرصيد الحالي", f"{st.session_state.الرصيد:,.2f} د.ل")
    
    with col2:
        st.metric("💰 إجمالي الدخل", f"{إجمالي_الدخل:,.2f} د.ل")
    
    with col3:
        st.metric("💸 إجمالي المصروفات", f"{إجمالي_المصروفات:,.2f} د.ل")
    
    # سجل المعاملات
    st.markdown("---")
    st.markdown("### 📋 سجل المعاملات")
    
    if st.session_state.المعاملات:
        for trans in reversed(st.session_state.المعاملات):
            ايموجي = '💵' if trans['النوع'] == 'دخل' else '💰'
            لون = '#27ae60' if trans['النوع'] == 'دخل' else '#e74c3c'
            
            st.markdown(f"""
            <div style="background: white; padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid {لون};">
                <strong>{ايموجي} {trans['الوصف']}</strong><br>
                <small>📅 {trans['التاريخ']} • 📁 {trans['الفئة']}</small>
                <div style="text-align: right; font-weight: bold; color: {لون};">
                    {trans['المبلغ']:,.2f} د.ل
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        ## 📝 لا توجد معاملات بعد
        
        **💡 ابدأ بإضافة معاملاتك:**
        1. استخدم الشريط الجانبي لإضافة معاملة
        2. بياناتك تحفظ تلقائياً في حسابك
        3. يمكنك العودة في أي وقت وستجد كل شيء محفوظ
        """)

def main():
    """الدالة الرئيسية"""
    # استخدام علامة show_main_app لتحديد الواجهة المعروضة
    if st.session_state.show_main_app and st.session_state.user_data_loaded and st.session_state.current_user_id:
        show_main_app()
    else:
        show_login_screen()

if __name__ == "__main__":
    main()