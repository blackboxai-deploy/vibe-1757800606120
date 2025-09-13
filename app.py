"""
تطبيق أداة OSINT المتقدمة - الخادم الرئيسي
"""

import os
import json
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from flask_caching import Cache
from werkzeug.exceptions import BadRequest, InternalServerError
import logging

from config import config
from email_toolkit.osint import comprehensive_search, osint

# إعداد الـ logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app(config_name='default'):
    """إنشاء وتكوين تطبيق Flask"""
    app = Flask(__name__)
    
    # تحميل الإعدادات
    app.config.from_object(config[config_name])
    
    # إعداد CORS
    if app.config.get('ENABLE_CORS'):
        CORS(app, origins=app.config.get('ALLOWED_ORIGINS', ['*']))
    
    # إعداد Cache
    cache = Cache(app)
    
    # إعداد Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[
            f"{app.config.get('RATELIMIT_PER_MINUTE', 30)} per minute",
            f"{app.config.get('RATELIMIT_PER_HOUR', 500)} per hour"
        ]
    )
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """معالج تجاوز حد الطلبات"""
        return jsonify({
            "error": "تم تجاوز حد الطلبات المسموح",
            "message": "يرجى المحاولة لاحقاً",
            "retry_after": e.retry_after
        }), 429
    
    @app.errorhandler(400)
    def bad_request_handler(e):
        """معالج الطلبات غير الصحيحة"""
        return jsonify({
            "error": "طلب غير صحيح",
            "message": str(e.description)
        }), 400
    
    @app.errorhandler(500)
    def internal_error_handler(e):
        """معالج الأخطاء الداخلية"""
        logger.error(f"خطأ داخلي: {str(e)}")
        return jsonify({
            "error": "خطأ داخلي في الخادم",
            "message": "حدث خطأ غير متوقع، يرجى المحاولة لاحقاً"
        }), 500
    
    # ==== الصفحة الرئيسية ====
    @app.route('/')
    def index():
        """الصفحة الرئيسية للتطبيق"""
        return render_template('index.html')
    
    @app.route('/api/status')
    def api_status():
        """حالة API"""
        return jsonify({
            "status": "active",
            "version": "2.0",
            "timestamp": datetime.now().isoformat(),
            "features": [
                "email_osint",
                "username_osint", 
                "comprehensive_search",
                "report_generation",
                "async_processing"
            ]
        })
    
    # ==== APIs الأساسية ====
    
    @app.route('/api/search', methods=['POST'])
    @limiter.limit("10 per minute")
    def api_search():
        """API البحث الشامل"""
        try:
            data = request.get_json()
            if not data or 'target' not in data:
                raise BadRequest("الهدف مطلوب")
            
            target = data['target'].strip()
            target_type = data.get('type', 'auto')
            
            if not target:
                raise BadRequest("الهدف لا يمكن أن يكون فارغاً")
            
            # التحقق من طول الهدف
            if len(target) > 100:
                raise BadRequest("الهدف طويل جداً")
            
            logger.info(f"بدء البحث عن: {target}")
            
            # تنفيذ البحث الشامل
            results = comprehensive_search(target, target_type)
            
            if 'error' in results:
                return jsonify({
                    "success": False,
                    "error": results['error']
                }), 400
            
            return jsonify({
                "success": True,
                "data": results
            })
            
        except BadRequest as e:
            return jsonify({
                "success": False,
                "error": str(e.description)
            }), 400
        except Exception as e:
            logger.error(f"خطأ في API البحث: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ غير متوقع في البحث"
            }), 500
    
    @app.route('/api/email/check', methods=['POST'])
    @limiter.limit("20 per minute")
    def api_email_check():
        """فحص بريد إلكتروني محدد"""
        try:
            data = request.get_json()
            if not data or 'email' not in data:
                raise BadRequest("البريد الإلكتروني مطلوب")
            
            email = data['email'].strip().lower()
            sources = data.get('sources', ['haveibeenpwned', 'emailrep'])
            
            if not osint.validator.validate_email(email):
                raise BadRequest("عنوان بريد إلكتروني غير صحيح")
            
            results = {}
            
            for source in sources:
                if hasattr(osint, source):
                    try:
                        method = getattr(osint, source)
                        results[source] = method(email)
                    except Exception as e:
                        results[source] = {"error": f"خطأ في {source}: {str(e)}"}
            
            return jsonify({
                "success": True,
                "email": email,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            
        except BadRequest as e:
            return jsonify({
                "success": False,
                "error": str(e.description)
            }), 400
        except Exception as e:
            logger.error(f"خطأ في فحص البريد: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في فحص البريد الإلكتروني"
            }), 500
    
    @app.route('/api/username/search', methods=['POST'])
    @limiter.limit("5 per minute") 
    def api_username_search():
        """البحث عن اسم مستخدم"""
        try:
            data = request.get_json()
            if not data or 'username' not in data:
                raise BadRequest("اسم المستخدم مطلوب")
            
            username = data['username'].strip()
            sources = data.get('sources', ['sherlock'])
            
            if not osint.validator.validate_username(username):
                raise BadRequest("اسم مستخدم غير صحيح")
            
            results = {}
            
            for source in sources:
                if hasattr(osint, source):
                    try:
                        method = getattr(osint, source)
                        results[source] = method(username)
                    except Exception as e:
                        results[source] = {"error": f"خطأ في {source}: {str(e)}"}
            
            return jsonify({
                "success": True,
                "username": username,
                "results": results,
                "timestamp": datetime.now().isoformat()
            })
            
        except BadRequest as e:
            return jsonify({
                "success": False,
                "error": str(e.description)
            }), 400
        except Exception as e:
            logger.error(f"خطأ في البحث عن اسم المستخدم: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في البحث عن اسم المستخدم"
            }), 500
    
    # ==== إدارة التقارير ====
    
    @app.route('/api/reports')
    def api_list_reports():
        """قائمة التقارير المحفوظة"""
        try:
            reports_dir = app.config.get('REPORTS_DIRECTORY', './reports')
            if not os.path.exists(reports_dir):
                return jsonify({"reports": []})
            
            reports = []
            for filename in os.listdir(reports_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(reports_dir, filename)
                    stat = os.stat(filepath)
                    reports.append({
                        "filename": filename,
                        "size": stat.st_size,
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # ترتيب حسب تاريخ الإنشاء (الأحدث أولاً)
            reports.sort(key=lambda x: x['created'], reverse=True)
            
            return jsonify({
                "success": True,
                "reports": reports,
                "total": len(reports)
            })
            
        except Exception as e:
            logger.error(f"خطأ في قائمة التقارير: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في جلب قائمة التقارير"
            }), 500
    
    @app.route('/api/reports/<filename>')
    def api_get_report(filename):
        """جلب تقرير محدد"""
        try:
            # التحقق من أمان اسم الملف
            if not filename.endswith('.json') or '/' in filename or '\\' in filename:
                raise BadRequest("اسم ملف غير صحيح")
            
            reports_dir = app.config.get('REPORTS_DIRECTORY', './reports')
            filepath = os.path.join(reports_dir, filename)
            
            if not os.path.exists(filepath):
                return jsonify({
                    "success": False,
                    "error": "التقرير غير موجود"
                }), 404
            
            with open(filepath, 'r', encoding='utf-8') as f:
                report_data = json.load(f)
            
            return jsonify({
                "success": True,
                "report": report_data
            })
            
        except BadRequest as e:
            return jsonify({
                "success": False,
                "error": str(e.description)
            }), 400
        except Exception as e:
            logger.error(f"خطأ في جلب التقرير: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في جلب التقرير"
            }), 500
    
    @app.route('/api/reports/<filename>/download')
    def api_download_report(filename):
        """تحميل تقرير"""
        try:
            # التحقق من أمان اسم الملف
            if not filename.endswith('.json') or '/' in filename or '\\' in filename:
                raise BadRequest("اسم ملف غير صحيح")
            
            reports_dir = app.config.get('REPORTS_DIRECTORY', './reports')
            filepath = os.path.join(reports_dir, filename)
            
            if not os.path.exists(filepath):
                return jsonify({
                    "success": False,
                    "error": "التقرير غير موجود"
                }), 404
            
            return send_file(
                filepath,
                as_attachment=True,
                download_name=filename,
                mimetype='application/json'
            )
            
        except Exception as e:
            logger.error(f"خطأ في تحميل التقرير: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في تحميل التقرير"
            }), 500
    
    # ==== معلومات النظام ====
    
    @app.route('/api/system/info')
    def api_system_info():
        """معلومات النظام والإحصائيات"""
        try:
            reports_dir = app.config.get('REPORTS_DIRECTORY', './reports')
            reports_count = 0
            total_size = 0
            
            if os.path.exists(reports_dir):
                for filename in os.listdir(reports_dir):
                    if filename.endswith('.json'):
                        reports_count += 1
                        filepath = os.path.join(reports_dir, filename)
                        total_size += os.path.getsize(filepath)
            
            return jsonify({
                "success": True,
                "system": {
                    "version": "2.0",
                    "uptime": "N/A",  # يمكن إضافة حساب الـ uptime لاحقاً
                    "reports_count": reports_count,
                    "reports_total_size": total_size,
                    "supported_sources": [
                        "HaveIBeenPwned",
                        "Hunter.io",
                        "LeakCheck",
                        "EmailRep",
                        "Clearbit",
                        "SocialScan",
                        "Holehe",
                        "Sherlock",
                        "Maigret"
                    ],
                    "rate_limits": {
                        "per_minute": app.config.get('RATELIMIT_PER_MINUTE', 30),
                        "per_hour": app.config.get('RATELIMIT_PER_HOUR', 500)
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"خطأ في معلومات النظام: {str(e)}")
            return jsonify({
                "success": False,
                "error": "خطأ في جلب معلومات النظام"
            }), 500
    
    return app

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    # تحديد بيئة التطبيق
    env = os.environ.get('FLASK_ENV', 'development')
    
    # إنشاء التطبيق
    app = create_app(env)
    
    # إنشاء مجلد التقارير
    reports_dir = app.config.get('REPORTS_DIRECTORY', './reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # تشغيل التطبيق
    host = app.config.get('FLASK_HOST', '0.0.0.0')
    port = app.config.get('FLASK_PORT', 3000)
    debug = env == 'development'
    
    logger.info(f"بدء تشغيل أداة OSINT على {host}:{port}")
    logger.info(f"البيئة: {env}")
    logger.info(f"وضع التطوير: {debug}")
    
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )

if __name__ == '__main__':
    main()