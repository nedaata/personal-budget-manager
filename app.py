import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
import sqlite3
from supabase import create_client
import os
from contextlib import contextmanager

# إعداد الصفحة
st.set_page_config(
    page_title="مدير الميزانية - الدينار الليبي",
    page_icon="💵",
    layout="wide"
)

# محاولة الاتصال بـ Supabase
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    supabase_connected = True
    st.success("✅ متصل بـ Supabase")
except Exception as e:
    supabase_connected = False
    st.warning("⚠️ الوضع غير متصل - البيانات محفوظة محلياً فقط")

# تهيئة قاعدة البيانات المحلية (كاحتياطي)
def init_database():
    conn = sqlite3.connect('budget_manager.db', check_same_thread=False)
    cursor = conn.cursor()
    
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

# تهيئة قاعدة البيانات المحلية
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
    if supabase_connected:
        # التحقق في Supabase
        try:
            response = supabase_client.table('users')\
                .select('user_id')\
                .eq('user_name', user_name.strip())\
                .execute()
            return len(response.data) == 0
        except Exception as e:
            st.error(f"خطأ في التحقق من اسم المستخدم في السحابة: {e}")
            return False
    else:
        # التحقق في SQLite
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
    if supabase_connected:
        # استخدام Supabase
        try:
            user_data = {
                'user_id': user_id,
                'user_name': user_name.strip(),
                'password_hash': password_hash,
                'balance': 0.0,
                'created_at': datetime.now().isoformat()
            }
            response = supabase_client.table('users').insert(user_data).execute()
            return True
        except Exception as e:
            st.error(f"خطأ في إنشاء الحساب على السحابة: {e}")
            return False
    else:
        # استخدام SQLite
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
    if supabase_connected:
        # التحقق في Supabase
        try:
            response = supabase_client.table('users')\
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
            st.error(f"خطأ في التحقق من كلمة المرور في السحابة: {e}")
            return False, None
    else:
        # التحقق في SQLite
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
    if supabase_connected:
        # جلب من Supabase
        try:
            response = supabase_client.table('users')\
                .select('balance')\
                .eq('user_id', user_id)\
                .execute()
            return response.data[0]['balance'] if response.data else 0.0
        except Exception as e:
            st.error(f"خطأ في جلب الرصيد من السحابة: {e}")
            return 0.0
    else:
        # جلب من SQLite
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
    if supabase_connected:
        # جلب من Supabase
        try:
            response = supabase_client.table('transactions')\
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
            st.error(f"خطأ في جلب المعاملات من السحابة: {e}")
            return []
    else:
        # جلب من SQLite
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
    if supabase_connected:
        # إضافة إلى Supabase
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
            supabase_client.table('transactions').insert(transaction_data).execute()
            
            # تحديث الرصيد
            if transaction_type == "دخل":
                supabase_client.table('users')\
                    .update({'balance': get_user_balance(user_id) + amount})\
                    .eq('user_id', user_id)\
                    .execute()
            else:
                supabase_client.table('users')\
                    .update({'balance': get_user_balance(user_id) - amount})\
                    .eq('user_id', user_id)\
                    .execute()
            
            return True
        except Exception as e:
            st.error(f"خطأ في إضافة المعاملة إلى السحابة: {e}")
            return False
    else:
        # إضافة إلى SQLite
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
    if supabase_connected:
        # حذف من Supabase
        try:
            # حذف المعاملات
            supabase_client.table('transactions')\
                .delete()\
                .eq('user_id', user_id)\
                .execute()
            
            # إعادة تعيين الرصيد
            supabase_client.table('users')\
                .update({'balance': 0.0})\
                .eq('user_id', user_id)\
                .execute()
            
            return True
        except Exception as e:
            st.error(f"خطأ في حذف البيانات من السحابة: {e}")
            return False
    else:
        # حذف من SQLite
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

# باقي الكود (show_login_screen, show_main_app, main) يبقى كما هو...

def show_login_screen():
    """شاشة تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    
    if supabase_connected:
        st.markdown("<h3 style='text-align: center; color: #A23B72;'>☁️ نظام سحابي متكامل</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h3 style='text-align: center; color: #A23B72;'>💾 نظام محلي آمن</h3>", unsafe_allow_html=True)
    
    # معلومات النظام
    if supabase_connected:
        st.markdown("""
        <div class="security-alert">
            <strong>🎯 المميزات السحابية:</strong><br>
            • بياناتك محفوظة في السحابة الآمنة<br>
            • الوصول لبياناتك من أي جهاز<br>
            • نسخ احتياطي تلقائي<br>
            • أداء عالي واستقرار
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="security-alert">
            <strong>🎯 المميزات المحلية:</strong><br>
            • بياناتك محفوظة على جهازك فقط<br>
            • خصوصية وأمان كامل<br>
            • عمل بدون اتصال إنترنت<br>
            • سرعة عالية في الوصول
        </div>
        """, unsafe_allow_html=True)
    
    # باقي كود الشاشة يبقى كما هو...

# الدوال show_main_app و main تبقى كما هي...

def show_main_app():
    # ... (نفس الكود السابق)
    pass

def main():
    if not st.session_state.user_data_loaded or not st.session_state.current_user_id:
        show_login_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()