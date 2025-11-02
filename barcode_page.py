# barcode_page.py
import streamlit as st
import qrcode
import io

def show_barcode_page():
    st.set_page_config(page_title="باركود التطبيق", page_icon="📱", layout="centered")
    
    st.title("📱 باركود تطبيق مدير الميزانية")
    
    # رابط التطبيق
    app_url = st.text_input("أدخل رابط التطبيق:", "https://your-budget-app.streamlit.app/")
    
    if app_url:
        # إنشاء QR Code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(app_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # تحويل الصورة إلى Bytes
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        buffer.seek(0)
        
        # عرض الصورة
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(buffer, caption="باركود التطبيق", use_column_width=True)
            
            # زر التحميل
            st.download_button(
                label="📥 حفظ الباركود",
                data=buffer.getvalue(),
                file_name="budget_app_qrcode.png",
                mime="image/png"
            )
        
        with col2:
            st.markdown(f"""
            ### تعليمات الاستخدام:
            
            1. **افتح الكاميرا على هاتفك**
            2. **صور الباركود**
            3. **انقر على الرابط الذي يظهر**
            4. **استخدم التطبيق مباشرة**
            
            **الرابط:** `{app_url}`
            
            💡 **لإضافة التطبيق إلى شاشة الهاتف الرئيسية:**
            - Chrome: ⋮ → **Add to Home Screen**
            - Safari: 📤 → **Add to Home Screen**
            """)