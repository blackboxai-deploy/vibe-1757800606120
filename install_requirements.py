#!/usr/bin/env python3
"""
سكربت تثبيت المتطلبات لأداة OSINT
"""

import subprocess
import sys
import os

def run_command(command, description):
    """تنفيذ أمر مع معالجة الأخطاء"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - تم بنجاح")
        if result.stdout:
            print(f"📋 الخرج: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - فشل")
        print(f"🔥 الخطأ: {e.stderr}")
        return False

def install_python_requirements():
    """تثبيت متطلبات Python"""
    print("\n=== تثبيت متطلبات Python ===")
    
    # ترقية pip
    run_command(f"{sys.executable} -m pip install --upgrade pip", "ترقية pip")
    
    # تثبيت المتطلبات
    if os.path.exists("requirements.txt"):
        success = run_command(f"{sys.executable} -m pip install -r requirements.txt", "تثبيت المتطلبات من requirements.txt")
        if not success:
            print("⚠️ بعض المكتبات قد لا تكون متوفرة، سيتم المتابعة...")
    else:
        print("❌ ملف requirements.txt غير موجود")

def install_external_tools():
    """تثبيت الأدوات الخارجية"""
    print("\n=== تثبيت الأدوات الخارجية ===")
    
    external_tools = {
        "sherlock": "pip install sherlock-project",
        "maigret": "pip install maigret", 
        "holehe": "pip install holehe",
        "socialscan": "pip install socialscan"
    }
    
    for tool_name, install_cmd in external_tools.items():
        print(f"\n🔧 تثبيت {tool_name}...")
        success = run_command(install_cmd, f"تثبيت {tool_name}")
        if success:
            print(f"✅ {tool_name} تم تثبيته بنجاح")
        else:
            print(f"⚠️ فشل تثبيت {tool_name} - ستحتاج لتثبيته يدوياً")

def create_directories():
    """إنشاء المجلدات المطلوبة"""
    print("\n=== إنشاء المجلدات ===")
    
    directories = [
        "reports",
        "logs", 
        "static",
        "static/css",
        "static/js"
    ]
    
    for directory in directories:
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ تم إنشاء مجلد: {directory}")
        except Exception as e:
            print(f"❌ فشل في إنشاء مجلد {directory}: {e}")

def check_system_requirements():
    """فحص متطلبات النظام"""
    print("\n=== فحص متطلبات النظام ===")
    
    # فحص إصدار Python
    python_version = sys.version_info
    print(f"🐍 إصدار Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ يتطلب Python 3.8 أو أحدث")
        return False
    
    print("✅ إصدار Python مدعوم")
    
    # فحص pip
    try:
        subprocess.run([sys.executable, "-m", "pip", "--version"], check=True, capture_output=True)
        print("✅ pip متوفر")
    except subprocess.CalledProcessError:
        print("❌ pip غير متوفر")
        return False
    
    return True

def setup_environment():
    """إعداد البيئة"""
    print("\n=== إعداد البيئة ===")
    
    # إنشاء ملف .env إذا لم يكن موجود
    if not os.path.exists(".env"):
        if os.path.exists(".env.example"):
            try:
                with open(".env.example", "r", encoding="utf-8") as example_file:
                    content = example_file.read()
                with open(".env", "w", encoding="utf-8") as env_file:
                    env_file.write(content)
                print("✅ تم إنشاء ملف .env من .env.example")
                print("⚠️ يرجى تحديث مفاتيح API في ملف .env")
            except Exception as e:
                print(f"❌ فشل في إنشاء ملف .env: {e}")
        else:
            print("⚠️ ملف .env.example غير موجود")
    else:
        print("ℹ️ ملف .env موجود بالفعل")

def main():
    """الدالة الرئيسية"""
    print("🚀 بدء تثبيت أداة OSINT المتقدمة")
    print("=" * 50)
    
    # فحص متطلبات النظام
    if not check_system_requirements():
        print("❌ فحص متطلبات النظام فشل. يرجى إصلاح المشاكل والمحاولة مرة أخرى.")
        sys.exit(1)
    
    # إنشاء المجلدات
    create_directories()
    
    # إعداد البيئة
    setup_environment()
    
    # تثبيت متطلبات Python
    install_python_requirements()
    
    # تثبيت الأدوات الخارجية
    install_external_tools()
    
    print("\n" + "=" * 50)
    print("🎉 تم الانتهاء من التثبيت!")
    print("\n📝 الخطوات التالية:")
    print("1. قم بتحديث مفاتيح API في ملف .env")
    print("2. شغّل التطبيق باستخدام: python app.py")
    print("3. افتح المتصفح على: http://localhost:3000")
    print("\n⚠️ تذكر: استخدم الأداة بطريقة قانونية ومشروعة فقط!")

if __name__ == "__main__":
    main()