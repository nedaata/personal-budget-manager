import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
import sqlite3
import json
import os
from contextlib import contextmanager

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# تهيئة قاعدة البيانات
def init_database():
    conn = sqlite3.connect('budget_manager.db', check_same_thread=False)
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            user_name TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # جدول المعاملات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            category TEXT NOT NULL,
            date TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    return conn

# إدارة اتصال قاعدة البيانات
@contextmanager
def get_db_connection():
    conn = sqlite3.connect('budget_manager.db', check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()

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

# تهيئة قاعدة البيانات
init_database()

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
    .transaction-income {
        border-left: 4px solid #27ae60;
        background: white;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
    }
    .transaction-expense {
        border-left: 4px solid #e74c3c;
        background: white;
        padding: 12px;
        margin: 8px 0;
        border-radius: 8px;
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
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE user_name = ?", (user_name.strip(),))
            return cursor.fetchone() is None
    except Exception as e:
        st.error(f"خطأ في التحقق من اسم المستخدم: {e}")
        return False

def create_user_account(user_id, user_name, password_hash):
    """إنشاء حساب مستخدم جديد"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (user_id, user_name, password_hash, balance)
                VALUES (?, ?, ?, ?)
            ''', (user_id, user_name.strip(), password_hash, 0.0))
            conn.commit()
            return True
    except Exception as e:
        st.error(f"خطأ في إنشاء الحساب: {e}")
        return False

def verify_password(user_name, password):
    """التحقق من كلمة المرور"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT user_id, password_hash FROM users WHERE user_name = ?", 
                (user_name.strip(),)
            )
            result = cursor.fetchone()
            
            if result:
                user_id, stored_hash = result
                return stored_hash == hash_password(password), user_id
            return False, None
    except Exception as e:
        st.error(f"خطأ في التحقق من كلمة المرور: {e}")
        return False, None

def get_user_balance(user_id):
    """جلب رصيد المستخدم"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else 0.0
    except Exception as e:
        st.error(f"خطأ في جلب الرصيد: {e}")
        return 0.0

def get_user_transactions(user_id):
    """جلب معاملات المستخدم"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, type, amount, description, category, date 
                FROM transactions 
                WHERE user_id = ? 
                ORDER BY date DESC
            ''', (user_id,))
            
            transactions = []
            for row in cursor.fetchall():
                transactions.append({
                    "id": row[0],
                    "النوع": row[1],
                    "المبلغ": row[2],
                    "الوصف": row[3],
                    "الفئة": row[4],
                    "التاريخ": row[5]
                })
            return transactions
    except Exception as e:
        st.error(f"خطأ في جلب المعاملات: {e}")
        return []

def add_transaction(user_id, transaction_type, amount, description, category):
    """إضافة معاملة جديدة"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # إضافة المعاملة
            transaction_id = str(uuid.uuid4())[:8]
            cursor.execute('''
                INSERT INTO transactions (id, user_id, type, amount, description, category, date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (transaction_id, user_id, transaction_type, amount, description, category, datetime.now()))
            
            # تحديث رصيد المستخدم
            if transaction_type == "دخل":
                cursor.execute(
                    "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                    (amount, user_id)
                )
            else:
                cursor.execute(
                    "UPDATE users SET balance = balance - ? WHERE user_id = ?",
                    (amount, user_id)
                )
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"خطأ في إضافة المعاملة: {e}")
        return False

def delete_all_user_data(user_id):
    """حذف جميع بيانات المستخدم"""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # حذف جميع المعاملات
            cursor.execute("DELETE FROM transactions WHERE user_id = ?", (user_id,))
            
            # إعادة تعيين الرصيد
            cursor.execute("UPDATE users SET balance = 0.0 WHERE user_id = ?", (user_id,))
            
            conn.commit()
            return True
    except Exception as e:
        st.error(f"خطأ في حذف البيانات: {e}")
        return False

def show_login_screen():
    """شاشة تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>🔐 نظام آمن بحفظ دائم للبيانات</h3>", unsafe_allow_html=True)
    
    # معلومات النظام
    st.markdown("""
    <div class="security-alert">
        <strong>🎯 مميزات النظام:</strong><br>
        • كل مستخدم له حساب منفصل وآمن<br>
        • بياناتك محفوظة بشكل دائم في قاعدة بيانات محلية<br>
        • يمكنك الوصول لبياناتك في أي وقت<br>
        • تشفير آمن لكلمات المرور<br>
        • حفظ كامل لسجل المعاملات
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
                            st.info("💡 انتقل لتبويب 'تسجيل الدخول' وأدخل بياناتك للبدء")
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
    
    # بطاقة المستخدم
    st.markdown(f"""
    <div class="user-card">
        <h3>👤 {st.session_state.user_name}</h3>
        <p>🆔 المعرف: {st.session_state.current_user_id}</p>
        <p>📊 {len(st.session_state.المعاملات)} معاملة محفوظة</p>
        <p>💾 البيانات محفوظة بشكل دائم</p>
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
                        
                        if transaction_type == "دخل":
                            st.success(f"✅ تم إضافة دخل: {وصف} - {مبلغ:,.2f} د.ل")
                        else:
                            st.success(f"✅ تم إضافة مصروف: {وصف} - {مبلغ:,.2f} د.ل")
                        
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
            st.success("✅ تم تحديث البيانات")
            st.rerun()
        
        if st.button("🗑️ مسح جميع بياناتي", use_container_width=True):
            if delete_all_user_data(st.session_state.current_user_id):
                st.session_state.الرصيد = 0.0
                st.session_state.المعاملات = []
                st.success("✅ تم مسح جميع بياناتك")
                st.rerun()
            else:
                st.error("❌ فشل في مسح البيانات")
        
        if st.button("🔐 تسجيل خروج", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("✅ تم تسجيل الخروج بنجاح")
            st.rerun()

    # الإحصائيات
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in st.session_state.المعاملات if trans['النوع'] == 'مصروف')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💳 الرصيد الحالي", f"{st.session_state.الرصيد:,.2f} د.ل")
    
    with col2:
        st.metric("💰 إجمالي الدخل", f"{إجمالي_الدخل:,.2f} د.ل")
    
    with col3:
        st.metric("💸 إجمالي المصروفات", f"{إجمالي_المصروفات:,.2f} د.ل")
    
    with col4:
        st.metric("📊 عدد المعاملات", f"{len(st.session_state.المعاملات)}")
    
    # سجل المعاملات
    st.markdown("---")
    st.markdown("### 📋 سجل المعاملات")
    
    if st.session_state.المعاملات:
        for trans in st.session_state.المعاملات:
            ايموجي = '💵' if trans['النوع'] == 'دخل' else '💰'
            لون = 'transaction-income' if trans['النوع'] == 'دخل' else 'transaction-expense'
            
            st.markdown(f"""
            <div class="{لون}">
                <strong>{ايموجي} {trans['الوصف']}</strong><br>
                <small>📅 {trans['التاريخ']} • 📁 {trans['الفئة']}</small>
                <div style="text-align: right; font-weight: bold;">
                    {trans['المبلغ']:,.2f} د.ل
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("""
        ## 📝 لا توجد معاملات بعد
        
        **💡 ابدأ بإضافة معاملاتك:**
        1. استخدم الشريط الجانبي لإضافة معاملة
        2. بياناتك تحفظ تلقائياً في قاعدة البيانات
        3. يمكنك العودة في أي وقت وستجد كل شيء محفوظ
        """)

def main():
    """الدالة الرئيسية"""
    if not st.session_state.user_data_loaded or not st.session_state.current_user_id:
        show_login_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()