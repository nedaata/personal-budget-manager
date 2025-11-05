import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
from supabase import create_client, Client

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانيةالشخصية",
    page_icon="💵",
    layout="wide"
)

# تهيئة Supabase
@st.cache_resource
def init_supabase():
    try:
        supabase_client = create_client(
            st.secrets["SUPABASE_URL"],
            st.secrets["SUPABASE_KEY"]
        )
        return supabase_client
    except:
        st.error("❌ تأكد من إعداد Supabase بشكل صحيح")
        st.stop()

supabase = init_supabase()

# تهيئة session state
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""
if 'balance' not in st.session_state:
    st.session_state.balance = 0.0
if 'transactions' not in st.session_state:
    st.session_state.transactions = []

# التصميم البسيط
st.markdown("""
<style>
    .main-title {
        text-align: center;
        color: #2E86AB;
        font-size: 2.5rem;
        margin-bottom: 2rem;
    }
    .stats-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin: 20px 0;
    }
    .stat-card {
        flex: 1;
        background: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 2px solid #dee2e6;
    }
    .transaction-income {
        background: #d4edda;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-right: 4px solid #28a745;
    }
    .transaction-expense {
        background: #f8d7da;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-right: 4px solid #dc3545;
    }
</style>
""", unsafe_allow_html=True)

# الدوال الأساسية
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user_id(username):
    return hashlib.md5(username.strip().encode()).hexdigest()[:12]

def check_username_available(username):
    try:
        response = supabase.table('users').select('user_id').eq('user_name', username).execute()
        return len(response.data) == 0
    except:
        return False

def create_user(username, password):
    try:
        user_id = create_user_id(username)
        password_hash = hash_password(password)
        
        user_data = {
            'user_id': user_id,
            'user_name': username,
            'password_hash': password_hash,
            'balance': 0.0
        }
        
        supabase.table('users').insert(user_data).execute()
        return user_id
    except Exception as e:
        st.error(f"خطأ في إنشاء الحساب: {e}")
        return None

def verify_login(username, password):
    try:
        response = supabase.table('users').select('*').eq('user_name', username).execute()
        if response.data:
            user = response.data[0]
            if user['password_hash'] == hash_password(password):
                return user['user_id'], user['balance']
        return None, 0.0
    except Exception as e:
        st.error(f"خطأ في تسجيل الدخول: {e}")
        return None, 0.0

def get_user_transactions(user_id):
    try:
        response = supabase.table('transactions').select('*').eq('user_id', user_id).order('date', desc=True).execute()
        return response.data
    except Exception as e:
        st.error(f"خطأ في جلب المعاملات: {e}")
        return []

def add_transaction(user_id, trans_type, amount, description):
    try:
        # إضافة المعاملة
        transaction_data = {
            'id': str(uuid.uuid4())[:8],
            'user_id': user_id,
            'type': trans_type,
            'amount': amount,
            'description': description,
            'date': datetime.now().isoformat()
        }
        supabase.table('transactions').insert(transaction_data).execute()
        
        # تحديث الرصيد
        current_balance = st.session_state.balance
        new_balance = current_balance + amount if trans_type == "دخل" else current_balance - amount
        
        supabase.table('users').update({'balance': new_balance}).eq('user_id', user_id).execute()
        st.session_state.balance = new_balance
        
        return True
    except Exception as e:
        st.error(f"خطأ في إضافة المعاملة: {e}")
        return False

def calculate_stats(transactions):
    total_income = sum(t['amount'] for t in transactions if t['type'] == 'دخل')
    total_expenses = sum(t['amount'] for t in transactions if t['type'] == 'مصروف')
    
    return {
        'total_income': total_income,
        'total_expenses': total_expenses
    }

# شاشة التسجيل والدخول
def show_auth_screen():
    st.markdown("<h1 class='main-title'>💰 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 تسجيل الدخول", "🚀 إنشاء حساب"])
    
    with tab1:
        st.subheader("تسجيل الدخول")
        with st.form("login_form"):
            username = st.text_input("اسم المستخدم")
            password = st.text_input("كلمة المرور", type="password")
            login_btn = st.form_submit_button("دخول")
            
            if login_btn:
                if username and password:
                    user_id, balance = verify_login(username, password)
                    if user_id:
                        st.session_state.user_id = user_id
                        st.session_state.user_name = username
                        st.session_state.balance = balance
                        st.session_state.transactions = get_user_transactions(user_id)
                        st.success("✅ تم تسجيل الدخول بنجاح!")
                        st.rerun()
                    else:
                        st.error("❌ اسم المستخدم أو كلمة المرور غير صحيحة")
                else:
                    st.error("❌ يرجى إدخال جميع البيانات")
    
    with tab2:
        st.subheader("إنشاء حساب جديد")
        with st.form("register_form"):
            new_user = st.text_input("اسم المستخدم الجديد")
            new_pass = st.text_input("كلمة المرور", type="password")
            confirm_pass = st.text_input("تأكيد كلمة المرور", type="password")
            register_btn = st.form_submit_button("إنشاء حساب")
            
            if register_btn:
                if new_user and new_pass and confirm_pass:
                    if new_pass == confirm_pass:
                        if check_username_available(new_user):
                            user_id = create_user(new_user, new_pass)
                            if user_id:
                                st.success("✅ تم إنشاء الحساب بنجاح! يمكنك الآن تسجيل الدخول")
                            else:
                                st.error("❌ فشل في إنشاء الحساب")
                        else:
                            st.error("❌ اسم المستخدم موجود مسبقاً")
                    else:
                        st.error("❌ كلمات المرور غير متطابقة")
                else:
                    st.error("❌ يرجى إدخال جميع البيانات")

# الشاشة الرئيسية
def show_main_app():
    st.markdown("<h1 class='main-title'>💰 مدير الميزانية البسيط</h1>", unsafe_allow_html=True)
    
    # الإحصائيات بجانب بعض
    stats = calculate_stats(st.session_state.transactions)
    
    st.markdown(f"""
    <div class='stats-container'>
        <div class='stat-card'>
            <h3>💳 الرصيد الحالي</h3>
            <h2 style='color: {'#28a745' if st.session_state.balance >= 0 else '#dc3545'};'>
                {st.session_state.balance:,.2f} د.ل
            </h2>
        </div>
        <div class='stat-card'>
            <h3>💰 إجمالي الدخل</h3>
            <h2 style='color: #28a745;'>{stats['total_income']:,.2f} د.ل</h2>
        </div>
        <div class='stat-card'>
            <h3>💸 إجمالي المصروف</h3>
            <h2 style='color: #dc3545;'>{stats['total_expenses']:,.2f} د.ل</h2>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write(f"مرحباً بك **{st.session_state.user_name}**")
    
    # إضافة معاملة جديدة
    st.subheader("➕ إضافة معاملة جديدة")
    with st.form("add_transaction"):
        col1, col2 = st.columns(2)
        
        with col1:
            trans_type = st.radio("نوع المعاملة:", ["دخل 💰", "مصروف 💸"])
            amount = st.number_input("المبلغ (د.ل):", min_value=0.0, step=100.0)
        
        with col2:
            description = st.text_input("وصف المعاملة:", placeholder="مثال: راتب أو سوق")
        
        submit_btn = st.form_submit_button("إضافة المعاملة 💾")
        
        if submit_btn:
            if amount > 0 and description.strip():
                success = add_transaction(
                    st.session_state.user_id,
                    "دخل" if trans_type == "دخل 💰" else "مصروف",
                    amount,
                    description.strip()
                )
                if success:
                    st.success("✅ تم إضافة المعاملة بنجاح!")
                    st.session_state.transactions = get_user_transactions(st.session_state.user_id)
                    st.rerun()
                else:
                    st.error("❌ فشل في إضافة المعاملة")
            else:
                st.error("❌ يرجى إدخال المبلغ والوصف")
    
    # سجل المعاملات
    st.subheader("📋 سجل المعاملات")
    
    if st.session_state.transactions:
        for trans in st.session_state.transactions:
            trans_class = "transaction-income" if trans['type'] == 'دخل' else "transaction-expense"
            trans_icon = "💰" if trans['type'] == 'دخل' else "💸"
            trans_sign = "+" if trans['type'] == 'دخل' else "-"
            
            # تحويل التاريخ إلى تنسيق مقروء
            date_obj = datetime.fromisoformat(trans['date'].replace('Z', '+00:00'))
            formatted_date = date_obj.strftime("%Y-%m-%d %H:%M")
            
            st.markdown(f"""
            <div class='{trans_class}'>
                <strong>{trans_icon} {trans['description']}</strong>
                <div style='display: flex; justify-content: space-between;'>
                    <small>📅 {formatted_date}</small>
                    <strong>{trans_sign}{trans['amount']:,.2f} د.ل</strong>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("📝 لا توجد معاملات حتى الآن. ابدأ بإضافة معاملاتك!")
    
    # تسجيل الخروج
    st.markdown("---")
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# التشغيل الرئيسي
def main():
    if st.session_state.user_id:
        show_main_app()
    else:
        show_auth_screen()
   
if __name__ == "__main__":

    main()
