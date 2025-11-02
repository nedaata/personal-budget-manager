import streamlit as st
from datetime import datetime
import uuid

# إعداد بسيط للتطبيق بدون Supabase
st.set_page_config(page_title="مدير الميزانية", page_icon="💵")

# تهيئة الجلسة
if 'المعاملات' not in st.session_state:
    st.session_state.المعاملات = []
if 'الرصيد' not in st.session_state:
    st.session_state.الرصيد = 0.0

st.title("💵 مدير الميزانية الشخصية")

# إضافة معاملة
with st.form("معاملة"):
    نوع = st.radio("النوع:", ["دخل 💵", "مصروف 💰"])
    مبلغ = st.number_input("المبلغ:", min_value=0.0)
    وصف = st.text_input("الوصف:")
    
    if st.form_submit_button("إضافة معاملة"):
        if مبلغ > 0 and وصف:
            معاملة = {
                "id": str(uuid.uuid4())[:8],
                "النوع": "دخل" if نوع == "دخل 💵" else "مصروف",
                "المبلغ": مبلغ,
                "الوصف": وصف,
                "التاريخ": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            st.session_state.المعاملات.append(معاملة)
            
            if نوع == "دخل 💵":
                st.session_state.الرصيد += مبلغ
            else:
                st.session_state.الرصيد -= مبلغ
            
            st.success("تمت الإضافة!")

# عرض البيانات
st.metric("الرصيد الحالي", f"{st.session_state.الرصيد:,.2f} د.ل")

for trans in reversed(st.session_state.المعاملات):
    st.write(f"{'💵' if trans['النوع']=='دخل' else '💰'} {trans['الوصف']} - {trans['المبلغ']:,.2f} د.ل")