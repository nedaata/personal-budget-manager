import streamlit as st
from datetime import datetime
import uuid
import hashlib
import re
from supabase import create_client, Client
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

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

# التصميم العربي المحسن
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
    
    .stats-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 5px;
        border-radius: 20px;
        margin: 20px 0;
    }
    
    .stats-inner {
        background: white;
        padding: 25px;
        border-radius: 15px;
    }
    
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin: 10px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        text-align: center;
        border: 2px solid transparent;
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.2);
    }
    
    .metric-income {
        border-color: #27ae60;
        border-left: 5px solid #27ae60;
    }
    
    .metric-expense {
        border-color: #e74c3c;
        border-left: 5px solid #e74c3c;
    }
    
    .metric-balance {
        border-color: #3498db;
        border-left: 5px solid #3498db;
    }
    
    .metric-net {
        border-color: #9b59b6;
        border-left: 5px solid #9b59b6;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        margin: 10px 0;
    }
    
    .metric-label {
        font-size: 1.1rem;
        color: #666;
        font-weight: 600;
    }
    
    .positive {
        color: #27ae60;
    }
    
    .negative {
        color: #e74c3c;
    }
    
    .neutral {
        color: #3498db;
    }
    
    .chart-container {
        background: white;
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    
    .progress-bar {
        height: 8px;
        background: #ecf0f1;
        border-radius: 4px;
        margin: 10px 0;
        overflow: hidden;
    }
    
    .progress-fill {
        height: 100%;
        border-radius: 4px;
        transition: width 0.3s ease;
    }
    
    .progress-income {
        background: linear-gradient(90deg, #27ae60, #2ecc71);
    }
    
    .progress-expense {
        background: linear-gradient(90deg, #e74c3c, #c0392b);
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
            .select('balance')\\
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

def calculate_financial_stats(transactions):
    """حساب الإحصائيات المالية"""
    إجمالي_الدخل = sum(trans['المبلغ'] for trans in transactions if trans['النوع'] == 'دخل')
    إجمالي_المصروفات = sum(trans['المبلغ'] for trans in transactions if trans['النوع'] == 'مصروف')
    صافي_الدخل = إجمالي_الدخل - إجمالي_المصروفات
    الرصيد_الحالي = st.session_state.الرصيد
    
    # حساب النسب المئوية
    total = إجمالي_الدخل + إجمالي_المصروفات
    نسبة_الدخل = (إجمالي_الدخل / total * 100) if total > 0 else 0
    نسبة_المصروف = (إجمالي_المصروفات / total * 100) if total > 0 else 0
    
    return {
        'إجمالي_الدخل': إجمالي_الدخل,
        'إجمالي_المصروفات': إجمالي_المصروفات,
        'صافي_الدخل': صافي_الدخل,
        'الرصيد_الحالي': الرصيد_الحالي,
        'نسبة_الدخل': نسبة_الدخل,
        'نسبة_المصروف': نسبة_المصروف,
        'عدد_المعاملات': len(transactions)
    }

def create_financial_charts(stats, transactions):
    """إنشاء الرسوم البيانية للإحصائيات المالية"""
    charts = {}
    
    # مخطط الدائري للدخل والمصروف
    if stats['إجمالي_الدخل'] > 0 or stats['إجمالي_المصروفات'] > 0:
        fig_pie = go.Figure(data=[
            go.Pie(
                labels=['الدخل', 'المصروفات'],
                values=[stats['إجمالي_الدخل'], stats['إجمالي_المصروفات']],
                hole=.4,
                marker=dict(colors=['#27ae60', '#e74c3c'])
            )
        ])
        fig_pie.update_layout(
            title_text='📊 توزيع الدخل والمصروفات',
            title_x=0.5,
            showlegend=True,
            height=400
        )
        charts['pie'] = fig_pie
    
    # مخطط الأعمدة للمقارنة
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(
        name='الدخل',
        x=['الإجمالي'],
        y=[stats['إجمالي_الدخل']],
        marker_color='#27ae60',
        text=[f"{stats['إجمالي_الدخل']:,.0f} د.ل"],
        textposition='auto',
    ))
    fig_bar.add_trace(go.Bar(
        name='المصروفات',
        x=['الإجمالي'],
        y=[stats['إجمالي_المصروفات']],
        marker_color='#e74c3c',
        text=[f"{stats['إجمالي_المصروفات']:,.0f} د.ل"],
        textposition='auto',
    ))
    fig_bar.update_layout(
        title_text='💰 مقارنة الدخل والمصروفات',
        title_x=0.5,
        barmode='group',
        height=400,
        showlegend=True
    )
    charts['bar'] = fig_bar
    
    # مخطط المصروفات حسب الفئة
    df = pd.DataFrame(transactions)
    expenses = df[df['النوع'] == 'مصروف']
    if not expenses.empty:
        expense_by_category = expenses.groupby('الفئة')['المبلغ'].sum().reset_index()
        fig_expenses = px.pie(
            expense_by_category,
            values='المبلغ',
            names='الفئة',
            title='💸 توزيع المصروفات حسب الفئة',
            color_discrete_sequence=px.colors.sequential.Reds
        )
        fig_expenses.update_layout(title_x=0.5, height=400)
        charts['expenses'] = fig_expenses
    
    return charts

def show_financial_statistics():
    """عرض الإحصائيات المالية المحسنة"""
    
    # حساب الإحصائيات
    stats = calculate_financial_stats(st.session_state.المعاملات)
    
    st.markdown("---")
    st.markdown("### 📈 الإحصائيات المالية الشاملة")
    
    # بطاقات المقاييس الرئيسية
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card metric-balance">
            <div class="metric-label">💳 الرصيد الحالي</div>
            <div class="metric-value neutral">{stats['الرصيد_الحالي']:,.2f} د.ل</div>
            <div class="progress-bar">
                <div class="progress-fill progress-income" style="width: 100%"></div>
            </div>
            <div style="font-size: 0.9rem; color: #666;">رصيدك المتاح حالياً</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card metric-income">
            <div class="metric-label">💰 إجمالي الدخل</div>
            <div class="metric-value positive">+{stats['إجمالي_الدخل']:,.2f} د.ل</div>
            <div class="progress-bar">
                <div class="progress-fill progress-income" style="width: {min(stats['نسبة_الدخل'], 100)}%"></div>
            </div>
            <div style="font-size: 0.9rem; color: #666;">{stats['نسبة_الدخل']:.1f}% من إجمالي التدفقات</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card metric-expense">
            <div class="metric-label">💸 إجمالي المصروفات</div>
            <div class="metric-value negative">-{stats['إجمالي_المصروفات']:,.2f} د.ل</div>
            <div class="progress-bar">
                <div class="progress-fill progress-expense" style="width: {min(stats['نسبة_المصروف'], 100)}%"></div>
            </div>
            <div style="font-size: 0.9rem; color: #666;">{stats['نسبة_المصروف']:.1f}% من إجمالي التدفقات</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        net_color_class = "positive" if stats['صافي_الدخل'] >= 0 else "negative"
        net_icon = "📈" if stats['صافي_الدخل'] >= 0 else "📉"
        net_text = "فائض" if stats['صافي_الدخل'] >= 0 else "عجز"
        
        st.markdown(f"""
        <div class="metric-card metric-net">
            <div class="metric-label">{net_icon} صافي الدخل</div>
            <div class="metric-value {net_color_class}">{stats['صافي_الدخل']:,.2f} د.ل</div>
            <div class="progress-bar">
                <div class="progress-fill {'progress-income' if stats['صافي_الدخل'] >= 0 else 'progress-expense'}" 
                     style="width: {min(abs(stats['صافي_الدخل']) / max(stats['إجمالي_الدخل'], 1) * 100, 100)}%"></div>
            </div>
            <div style="font-size: 0.9rem; color: #666;">حالة مالية: {net_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    # مخططات إضافية
    if st.session_state.المعاملات:
        charts = create_financial_charts(stats, st.session_state.المعاملات)
        
        # عرض المخططات في أعمدة
        if 'pie' in charts and 'bar' in charts:
            col1, col2 = st.columns(2)
            with col1:
                st.plotly_chart(charts['pie'], use_container_width=True)
            with col2:
                st.plotly_chart(charts['bar'], use_container_width=True)
        
        if 'expenses' in charts:
            st.plotly_chart(charts['expenses'], use_container_width=True)
    
    # ملخص مالي
    st.markdown("---")
    st.markdown("### 📋 الملخص المالي")
    
    summary_col1, summary_col2 = st.columns(2)
    
    with summary_col1:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid #3498db;">
            <h4 style="margin: 0 0 15px 0; color: #2c3e50;">💡 نصائح مالية</h4>
            <ul style="color: #555; line-height: 1.6;">
                <li>حافظ على نسبة ادخار لا تقل عن 20% من دخلك</li>
                <li>راجع مصروفاتك الشهرية بانتظام</li>
                <li>حدد ميزانية واقعية لكل فئة من المصروفات</li>
                <li>استثمر الفائض المالي لبناء ثروة مستقبلية</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    with summary_col2:
        # تحليل بسيط للأداء المالي
        if stats['صافي_الدخل'] > 0:
            analysis = "🎉 أداء مالي ممتاز! لديك فائض يمكن استثماره."
            color = "#27ae60"
        elif stats['صافي_الدخل'] == 0:
            analysis = "⚖️ اتزان مالي! دخلك يساوي مصروفاتك بالضبط."
            color = "#f39c12"
        else:
            analysis = "⚠️ انتبه! لديك عجز مالي يحتاج لمراجعة المصروفات."
            color = "#e74c3c"
        
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px; border-left: 4px solid {color};">
            <h4 style="margin: 0 0 15px 0; color: #2c3e50;">📊 تحليل الأداء</h4>
            <p style="color: #555; line-height: 1.6; margin: 0;">{analysis}</p>
            <div style="margin-top: 15px; font-size: 0.9rem; color: #666;">
                <div>• عدد المعاملات: <strong>{stats['عدد_المعاملات']}</strong></div>
                <div>• متوسط الدخل الشهري: <strong>{stats['إجمالي_الدخل']/max(len(st.session_state.المعاملات), 1):.2f} د.ل</strong></div>
                <div>• نسبة الادخار: <strong>{max(stats['صافي_الدخل'], 0)/max(stats['إجمالي_الدخل'], 1)*100:.1f}%</strong></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

def show_login_screen():
    """شاشة تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #A23B72;'>☁️ نظام سحابي متكامل</h3>", unsafe_allow_html=True)
    
    # ... (نفس كود تسجيل الدخول السابق)

def show_main_app():
    """التطبيق الرئيسي بعد تسجيل الدخول"""
    st.markdown("<h1 class='main-header'>🌐 مدير الميزانية الشخصية</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #A23B72;'>👤 أهلاً بك {st.session_state.user_name}</h3>", unsafe_allow_html=True)
    
    # عرض الإحصائيات المالية
    show_financial_statistics()
    
    # الشريط الجانبي (نفس الكود السابق)
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
        
        # ... (بقية الشريط الجانبي)

def main():
    """الدالة الرئيسية"""
    if not st.session_state.user_data_loaded or not st.session_state.current_user_id:
        show_login_screen()
    else:
        show_main_app()

if __name__ == "__main__":
    main()