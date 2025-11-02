import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
from supabase import create_client, Client

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# تهيئة Supabase
@st.cache_resource
def init_supabase():
    try:
        supabase_client: Client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
        # اختبار الاتصال
        supabase_client.table("users").select("count", count="exact").execute()
        return supabase_client
    except Exception as e:
        st.error(f"❌ فشل في الاتصال بـ Supabase: {e}")
        st.stop()

# محاولة الاتصال بـ Supabase
try:
    supabase = init_supabase()
    st.sidebar.success("✅ متصل بـ Supabase")
except Exception as e:
    st.error("""
    ❌ لا يمكن الاتصال بـ Supabase. تأكد من:
    1. إعداد ملف secrets.toml بشكل صحيح
    2. أن الجداول موجودة في Supabase
    3. اتصال الإنترنت يعمل
    """)
    st.stop()

# تهيئة session state
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

# التصميم العربي
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Tajawal:wght@300;400;500;700;800&display=swap');
    
    * {
        font-family: 'Tajawal', sans-serif;
    }
    
    .main-header {
        font-size: 3rem;
        color: #2E86AB;
        text-align: center;
        margin-bottom: 1rem;
        font-weight: 800;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .login-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 40px;
        border-radius: 20px;
        margin: 20px auto;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        max-width: 500px;
        color: white;
    }
    
    .security-alert {
        background: rgba(255, 255, 255, 0.9);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        backdrop-filter: blur(10px);
        border-left: 5px solid #ffc107;
    }
    
    .user-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 15px;
        margin: 15px 0;
        color: white;
        text-align: center;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-left: 5px solid #2E86AB;
        text-align: center;
    }
    
    .transaction-income {
        background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
        color: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .transaction-expense {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    
    .stButton button {
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    
    .status-cloud {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
        margin: 10px 0;
        font-weight: bold;
    }
    
    .empty-state {
        text-align: center;
        padding: 40px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        color: white;
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
    try:
        response = supabase.table('users')\
            .select('user_id')\
            .eq('user_name', user_name.strip())\
            .execute()
        return len(response.data) == 0
    except Exception as e:
        st.error(f"خطأ في التحقق من اسم المستخدم: {e}")
        return False

def create_user_account(user_id, user_name, password_hash):
    """إنشاء حساب مستخدم جديد"""
    try:
        user_data = {
            'user_id': user_id,
            'user_name': user_name.strip(),
            'password_hash': password_hash,
            'balance': 0.0,
            'created_at': datetime.now().isoformat()
        }
        response = supabase.table('users').insert(user_data).execute()
        
        if response.data:
            return True
        else:
            st.error("فشل في إنشاء الحساب")
            return False
    except Exception as e:
        st.error(f"خطأ في إنشاء الحساب: {e}")
        return False

def verify_password(user_name, password):
    """التحقق من كلمة المرور"""
    try:
        response = supabase.table('users')\
            .select('user_id, password_hash')\
            .eq('user_name', user_name.strip())\
            .execute()
        
        if response.data:
            user_data = response.data[0]
            stored_hash = user_data['password_hash']
            user_id = user_data['user_id']
            return stored_hash == hash_password(password), user_id
        return False, None
    except Exception as e:
        st.error(f"خطأ في التحقق من كلمة المرور: {e}")
        return False, None

def get_user_balance(user_id):
    """جلب رصيد المستخدم"""
    try:
        response = supabase.table('users')\
            .select('balance')\
            .eq('user_id', user_id)\
            .execute()
        return response.data[0]['balance'] if response.data else 0.0
    except Exception as e:
        st.error(f"خطأ في جلب الرصيد: {e}")
        return 0.0

def get_user_transactions(user_id):
    """جلب معاملات المستخدم"""
    try:
        response = supabase.table('transactions')\
            .select('*')\
            .eq('user_id', user_id)\
            .order('date', desc=True)\
            .execute()
        
        transactions = []
        for row in response.data:
            transactions.append({
                "id": row['id'],
                "النوع": row['type'],
                "المبلغ": row['amount'],
                "الوصف": row['description'],
                "الفئة": row['category'],
                "التاريخ": row['date']
            })
        return transactions
    except Exception as e:
        st.error(f"خطأ في جلب المعاملات: {e}")
        return []

def add_transaction(user_id, transaction_type, amount, description, category):
    """إضافة معاملة جديدة"""
    try:
        transaction_id = str(uuid.uuid4())[:8]
        transaction_data = {
            'id': transaction_id,
            'user_id': user_id,
            'type': transaction_type,
            'amount': amount,
            'description': description.strip(),
            'category': category,
            'date': datetime.now().isoformat()
        }
        
        # إضافة المعاملة
        supabase.table('transactions').insert(transaction_data).execute()
        
        # تحديث الرصيد
        current_balance = get_user_balance(user_id)
        new_balance = current_balance + amount if transaction_type == "دخل" else current_balance - amount
        
        supabase.table('users')\
            .update({'balance': new_balance})\
            .eq('user_id', user_id)\
            .execute()
        
        return True
    except Exception as e:
        st.error(f"خطأ في إضافة المعاملة: {e}")
        return False

def delete_all_user_data(user_id):
    """حذف جميع بيانات المستخدم"""
    try:
        # حذف جميع المعاملات
        supabase.table('transactions')\
            .delete()\
            .eq('user_id', user_id)\
            .execute()
        
        # إعادة تعيين الرصيد
        supabase.table('users')\
            .update({'balance': 0.0})\
            .eq('user_id', user_id)\
            .execute()
        
        return True
    except Exception as e:
        st.error(f"خطأ في حذف البيانات: {e}")
        return False

def show_login_screen():
    """شاشة تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>☁️ نظام سحابي متكامل</h3>", unsafe_allow_html=True)
    
    # حالة النظام
    st.markdown("<div class='status-cloud'>☁️ التطبيق يعمل على Supabase - بياناتك آمنة في السحابة</div>", unsafe_allow_html=True)
    
    # معلومات النظام
    st.markdown("""
    <div class="security-alert">
        <strong>🎯 مميزات النظام السحابي:</strong><br>
        • بياناتك محفوظة في سحابة Supabase الآمنة<br>
        • الوصول لبياناتك من أي جهاز في العالم<br>
        • نسخ احتياطي تلقائي ومستمر<br>
        • أداء عالي واستقرار 99.9%<br>
        • مزامنة فورية بين جميع أجهزتك<br>
        • أمان متقدم وحماية من الاختراق
    </div>
    """, unsafe_allow_html=True)
    
    # تبويبات للتسجيل/الدخول
    tab1, tab2 = st.tabs(["🚀 إنشاء حساب جديد", "🔐 تسجيل الدخول"])
    
    with tab1:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: white; text-align: center;'>🎯 انضم إلينا اليوم</h3>", unsafe_allow_html=True)
        
        with st.form("register_form"):
            new_username = st.text_input(
                "👤 اسم المستخدم الجديد:",
                placeholder="اختر اسم مستخدم فريد...",
                help="هذا الاسم لا يمكن لأحد آخر استخدامه"
            )
            
            new_password = st.text_input(
                "🔒 كلمة المرور:",
                type="password",
                placeholder="كلمة مرور قوية...",
                help="6 أحرف على الأقل، تحتوي على أحرف وأرقام"
            )
            
            confirm_password = st.text_input(
                "✅ تأكيد كلمة المرور:",
                type="password",
                placeholder="أعد كتابة كلمة المرور..."
            )
            
            register_button = st.form_submit_button(
                "🎉 إنشاء حسابي الجديد",
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
                            st.markdown("""
                            <div style="background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%); 
                                        padding: 30px; border-radius: 15px; text-align: center; color: white; margin: 20px 0;">
                                <h3>🎊 مرحباً بك في عائلتنا!</h3>
                                <p>حسابك جاهز الآن. انتقل لتبويب تسجيل الدخول لبدء رحلتك المالية</p>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.error("❌ فشل في إنشاء الحساب، حاول مرة أخرى")
    
    with tab2:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h3 style='color: white; text-align: center;'>🔐 أهلاً بعودتك</h3>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            username = st.text_input(
                "👤 اسم المستخدم:",
                placeholder="أدخل اسم المستخدم..."
            )
            
            password = st.text_input(
                "🔒 كلمة المرور:",
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
                is_valid, user_id = verify_password(username.strip(), password)
                
                if is_valid and user_id:
                    # تسجيل الدخول الناجح
                    st.session_state.current_user_id = user_id
                    st.session_state.user_name = username.strip()
                    st.session_state.الرصيد = get_user_balance(user_id)
                    st.session_state.المعاملات = get_user_transactions(user_id)
                    st.session_state.user_data_loaded = True
                    st.session_state.login_attempts = 0
                    
                    st.success(f"✅ تم تسجيل الدخول بنجاح! أهلاً بك {username.strip()}")
                    st.rerun()
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
    
    # حالة النظام
    st.markdown("<div class='status-cloud'>☁️ متصل بـ Supabase - البيانات آمنة في السحابة</div>", unsafe_allow_html=True)
    
    # بطاقة المستخدم
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="user-card">
            <h3>👤 {st.session_state.user_name}</h3>
            <p>المستخدم النشط</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="user-card">
            <h3>📊 {len(st.session_state.المعاملات)}</h3>
            <p>معاملة محفوظة</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="user-card">
            <h3>☁️ Supabase</h3>
            <p>التخزين السحابي</p>
        </div>
        """, unsafe_allow_html=True)
    
    # الإحصائيات
    st.markdown("---")
    st.markdown("### 📈 الإحصائيات المالية")
    
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    صافي_الدخل = إجمالي_الدخل - إجمالي_المصروفات
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h3>💳 {st.session_state.الرصيد:,.2f} د.ل</h3>
            <p>الرصيد الحالي</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #27ae60;">💰 {إجمالي_الدخل:,.2f} د.ل</h3>
            <p>إجمالي الدخل</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: #e74c3c;">💸 {إجمالي_المصروفات:,.2f} د.ل</h3>
            <p>إجمالي المصروفات</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = "#27ae60" if صافي_الدخل >= 0 else "#e74c3c"
        st.markdown(f"""
        <div class="metric-card">
            <h3 style="color: {color};">📊 {صافي_الدخل:,.2f} د.ل</h3>
            <p>صافي الدخل</p>
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
                    transaction_type = "دخل" if نوع == "دخل 💵" else "مصروف"
                    
                    success = add_transaction(
                        st.session_state.current_user_id,
                        transaction_type,
                        مبلغ,
                        وصف.strip(),
                        فئة
                    )
                    
                    if success:
                        # تحديث البيانات المحلية
                        st.session_state.الرصيد = get_user_balance(st.session_state.current_user_id)
                        st.session_state.المعاملات = get_user_transactions(st.session_state.current_user_id)
                        
                        st.success(f"✅ تم إضافة {transaction_type}: {وصف} - {مبلغ:,.2f} د.ل")
                        st.rerun()
                    else:
                        st.error("❌ فشل في إضافة المعاملة")
                else:
                    st.error("❌ يرجى إدخال المبلغ والوصف")
        
        st.markdown("---")
        st.markdown("### ⚙️ إدارة الحساب")
        
        if st.button("🔄 تحديث البيانات", use_container_width=True):
            st.session_state.الرصيد = get_user_balance(st.session_state.current_user_id)
            st.session_state.المعاملات = get_user_transactions(st.session_state.current_user_id)
            st.success("✅ تم تحديث البيانات من السحابة")
            st.rerun()
        
        if st.button("🗑️ مسح جميع بياناتي", use_container_width=True):
            if st.checkbox("⚠️ تأكيد المسح - هذه العملية لا يمكن التراجع عنها"):
                if delete_all_user_data(st.session_state.current_user_id):
                    st.session_state.الرصيد = 0.0
                    st.session_state.المعاملات = []
                    st.success("✅ تم مسح جميع بياناتك من السحابة")
                    st.rerun()
                else:
                    st.error("❌ فشل في مسح البيانات")
        
        if st.button("🔐 تسجيل خروج", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ تم تسجيل الخروج بنجاح")
            st.rerun()
    
    # سجل المعاملات
    st.markdown("---")
    st.markdown("### 📋 سجل المعاملات الحديثة")
    
    if st.session_state.المعاملات:
        # عرض آخر 10 معاملات فقط
        recent_transactions = st.session_state.المعاملات[:10]
        
        for trans in recent_transactions:
            if trans['النوع'] == 'دخل':
                st.markdown(f"""
                <div class="transaction-income">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0;">💵 {trans['الوصف']}</h4>
                            <small>📅 {trans['التاريخ']} • 📁 {trans['الفئة']}</small>
                        </div>
                        <div style="text-align: right;">
                            <h3 style="margin: 0;">+{trans['المبلغ']:,.2f} د.ل</h3>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="transaction-expense">
                    <div style="display: flex; justify-content: between; align-items: center;">
                        <div style="flex: 1;">
                            <h4 style="margin: 0;">💰 {trans['الوصف']}</h4>
                            <small>📅 {trans['التاريخ']} • 📁 {trans['الفئة']}</small>
                        </div>
                        <div style="text-align: right;">
                            <h3 style="margin: 0;">-{trans['المبلغ']:,.2f} د.ل</h3>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        if len(st.session_state.المعاملات) > 10:
            st.info(f"📖 عرض {len(recent_transactions)} من أصل {len(st.session_state.المعاملات)} معاملة.")
    else:
        st.markdown("""
        <div class="empty-state">
            <h3>📝 لا توجد معاملات بعد</h3>
            <p>ابدأ رحلتك المالية بإضافة أول معاملة لك باستخدام النموذج في الشريط الجانبي</p>
            <div style="font-size: 4rem; margin-top: 20px;">💸</div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """الدالة الرئيسية"""
    if not st.session_state.user_data_loaded or not st.session_state.current_user_id:
        show_login_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()