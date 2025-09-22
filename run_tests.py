#!/usr/bin/env python3
"""
سكريبت تشغيل الاختبارات لخدمة عداد الزوار
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """تشغيل أمر وطباعة النتيجة"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("تحذيرات:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ خطأ في تشغيل الأمر: {e}")
        print(f"الخرج: {e.stdout}")
        print(f"الأخطاء: {e.stderr}")
        return False

def install_test_requirements():
    """تثبيت متطلبات الاختبار"""
    return run_command(
        "pip install -r requirements-test.txt",
        "تثبيت متطلبات الاختبار"
    )

def run_unit_tests():
    """تشغيل الاختبارات الوحدة"""
    return run_command(
        "pytest tests/test_models.py tests/test_services.py -v",
        "تشغيل اختبارات الوحدة (Models & Services)"
    )

def run_api_tests():
    """تشغيل اختبارات API"""
    return run_command(
        "pytest tests/test_api.py -v",
        "تشغيل اختبارات API"
    )

def run_performance_tests():
    """تشغيل اختبارات الأداء"""
    return run_command(
        "pytest tests/test_performance.py -v -m performance",
        "تشغيل اختبارات الأداء"
    )

def run_all_tests():
    """تشغيل جميع الاختبارات"""
    return run_command(
        "pytest tests/ -v",
        "تشغيل جميع الاختبارات"
    )

def run_coverage_report():
    """إنشاء تقرير التغطية"""
    return run_command(
        "pytest tests/ --cov=src --cov-report=html --cov-report=term",
        "إنشاء تقرير تغطية الكود"
    )

def run_quick_tests():
    """تشغيل الاختبارات السريعة فقط"""
    return run_command(
        'pytest tests/ -v -m "not slow and not performance"',
        "تشغيل الاختبارات السريعة"
    )

def main():
    parser = argparse.ArgumentParser(description="تشغيل اختبارات خدمة عداد الزوار")
    parser.add_argument(
        "--type", 
        choices=["unit", "api", "performance", "all", "coverage", "quick"],
        default="quick",
        help="نوع الاختبارات المراد تشغيلها"
    )
    parser.add_argument(
        "--install", 
        action="store_true",
        help="تثبيت متطلبات الاختبار أولاً"
    )
    
    args = parser.parse_args()
    
    # التأكد من وجود مجلد المشروع
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🧪 مرحباً بك في نظام اختبار خدمة عداد الزوار")
    print(f"📁 مجلد المشروع: {project_root}")
    
    success = True
    
    # تثبيت المتطلبات إذا طُلب ذلك
    if args.install:
        success = install_test_requirements()
        if not success:
            print("❌ فشل في تثبيت متطلبات الاختبار")
            return 1
    
    # تشغيل الاختبارات حسب النوع المطلوب
    if args.type == "unit":
        success = run_unit_tests()
    elif args.type == "api":
        success = run_api_tests()
    elif args.type == "performance":
        success = run_performance_tests()
    elif args.type == "all":
        success = run_all_tests()
    elif args.type == "coverage":
        success = run_coverage_report()
    elif args.type == "quick":
        success = run_quick_tests()
    
    # النتيجة النهائية
    if success:
        print(f"\n✅ تم تشغيل اختبارات '{args.type}' بنجاح!")
        if args.type == "coverage":
            print("📊 يمكنك مراجعة تقرير التغطية في مجلد htmlcov/index.html")
        return 0
    else:
        print(f"\n❌ فشل في تشغيل اختبارات '{args.type}'")
        return 1

if __name__ == "__main__":
    sys.exit(main())
