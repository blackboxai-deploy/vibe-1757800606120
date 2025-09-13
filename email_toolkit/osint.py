"""
أداة OSINT المتقدمة - الوحدة الأساسية
نسخة محسنة ومطورة لجمع المعلومات من مصادر مفتوحة
"""

import os
import re
import json
import time
import asyncio
import aiohttp
import requests
import subprocess
import validators
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse
import logging

# إعداد الـ logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OSINTValidator:
    """فئة للتحقق من صحة البيانات المدخلة"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """التحقق من صحة عنوان البريد الإلكتروني"""
        return validators.email(email) if email else False
    
    @staticmethod
    def validate_username(username: str) -> bool:
        """التحقق من صحة اسم المستخدم"""
        if not username or len(username) < 3:
            return False
        return re.match(r'^[a-zA-Z0-9_.-]+
, username) is not None
    
    @staticmethod
    def sanitize_input(input_str: str) -> str:
        """تنظيف المدخلات من الأحرف الضارة"""
        if not input_str:
            return ""
        # إزالة الأحرف الخطيرة
        dangerous_chars = ['<', '>', '"', "'", '&', '|', ';', '
, '`']
        sanitized = input_str
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        return sanitized.strip()

class OSINTReporter:
    """فئة لإنشاء التقارير وحفظها"""
    
    def __init__(self, reports_dir: str = "./reports"):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def generate_report(self, target: str, results: Dict) -> Dict:
        """إنشاء تقرير شامل للنتائج"""
        report = {
            "target": target,
            "timestamp": datetime.now().isoformat(),
            "summary": self._generate_summary(results),
            "detailed_results": results,
            "metadata": {
                "total_sources": len(results),
                "successful_sources": len([r for r in results.values() if 'error' not in r]),
                "failed_sources": len([r for r in results.values() if 'error' in r])
            }
        }
        return report
    
    def _generate_summary(self, results: Dict) -> Dict:
        """إنشاء ملخص للنتائج"""
        summary = {
            "risk_level": "low",
            "breaches_found": False,
            "social_accounts": 0,
            "email_reputation": "unknown"
        }
        
        # تحليل النتائج وتحديد مستوى المخاطر
        if 'haveibeenpwned' in results and results['haveibeenpwned']:
            if isinstance(results['haveibeenpwned'], list) and len(results['haveibeenpwned']) > 0:
                summary["breaches_found"] = True
                summary["risk_level"] = "high" if len(results['haveibeenpwned']) > 3 else "medium"
        
        return summary
    
    def save_report(self, report: Dict, filename: Optional[str] = None) -> str:
        """حفظ التقرير إلى ملف"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"osint_report_{report['target'].replace('@', '_').replace('.', '_')}_{timestamp}.json"
        
        filepath = os.path.join(self.reports_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"تم حفظ التقرير: {filepath}")
        return filepath

class EnhancedOSINT:
    """فئة OSINT المحسنة مع ميزات متقدمة"""
    
    def __init__(self):
        self.validator = OSINTValidator()
        self.reporter = OSINTReporter()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def haveibeenpwned(self, email: str) -> Dict[str, Any]:
        """فحص تسريب البيانات - HaveIBeenPwned"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        try:
            api_key = os.environ.get("HIBP_API_KEY")
            if not api_key:
                return {"error": "مفتاح API مطلوب لـ HaveIBeenPwned"}
            
            headers = {
                "hibp-api-key": api_key, 
                "User-Agent": "OSINT-Toolkit/2.0"
            }
            
            url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}?truncateResponse=false"
            resp = self.session.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                breaches = resp.json()
                return {
                    "status": "found",
                    "breach_count": len(breaches),
                    "breaches": breaches,
                    "last_breach": max(breaches, key=lambda x: x.get('BreachDate', ''))['Name'] if breaches else None
                }
            elif resp.status_code == 404:
                return {"status": "clean", "breach_count": 0, "message": "لم يتم العثور على تسريبات"}
            else:
                return {"error": f"خطأ API: {resp.status_code} - {resp.text}"}
                
        except requests.exceptions.Timeout:
            return {"error": "انتهت مهلة الاتصال"}
        except Exception as e:
            logger.error(f"خطأ في haveibeenpwned: {str(e)}")
            return {"error": f"خطأ غير متوقع: {str(e)}"}

    def hunterio(self, email: str) -> Dict[str, Any]:
        """التحقق من صحة البريد الإلكتروني - Hunter.io"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        try:
            api_key = os.environ.get("HUNTER_API_KEY")
            if not api_key:
                return {"error": "مفتاح API مطلوب لـ Hunter.io"}
            
            params = {"email": email, "api_key": api_key}
            resp = self.session.get("https://api.hunter.io/v2/email-verifier", 
                                  params=params, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                if 'data' in data:
                    result = data['data']
                    return {
                        "status": result.get('status', 'unknown'),
                        "result": result.get('result', 'unknown'),
                        "score": result.get('score', 0),
                        "mx_records": result.get('mx_records', False),
                        "smtp_server": result.get('smtp_server', False),
                        "sources": result.get('sources', [])
                    }
            
            return {"error": f"خطأ API: {resp.status_code}"}
            
        except Exception as e:
            logger.error(f"خطأ في hunterio: {str(e)}")
            return {"error": f"خطأ غير متوقع: {str(e)}"}

    def leakcheck(self, email: str) -> Dict[str, Any]:
        """فحص التسريبات - LeakCheck"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        try:
            api_key = os.environ.get("LEAKCHECK_API_KEY")
            if not api_key:
                return {"error": "مفتاح API مطلوب لـ LeakCheck"}
            
            params = {"key": api_key, "check": email, "type": "email"}
            resp = self.session.get("https://leakcheck.io/api/public", 
                                  params=params, timeout=15)
            
            if resp.status_code == 200:
                return resp.json()
            
            return {"error": f"خطأ API: {resp.status_code}"}
            
        except Exception as e:
            logger.error(f"خطأ في leakcheck: {str(e)}")
            return {"error": f"خطأ غير متوقع: {str(e)}"}

    def emailrep(self, email: str) -> Dict[str, Any]:
        """فحص سمعة البريد الإلكتروني - EmailRep"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        try:
            resp = self.session.get(f"https://emailrep.io/{email}", timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "reputation": data.get('reputation', 'unknown'),
                    "suspicious": data.get('suspicious', False),
                    "references": data.get('references', 0),
                    "blacklisted": data.get('blacklisted', False),
                    "malicious_activity": data.get('malicious_activity', False),
                    "credentials_leaked": data.get('credentials_leaked', False),
                    "first_seen": data.get('first_seen', None),
                    "last_seen": data.get('last_seen', None)
                }
            elif resp.status_code == 404:
                return {"status": "not_found", "message": "لم يتم العثور على معلومات"}
            
            return {"error": f"خطأ API: {resp.status_code}"}
            
        except Exception as e:
            logger.error(f"خطأ في emailrep: {str(e)}")
            return {"error": f"خطأ غير متوقع: {str(e)}"}

    def clearbit(self, email: str) -> Dict[str, Any]:
        """الحصول على معلومات الأشخاص - Clearbit"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        try:
            api_key = os.environ.get("CLEARBIT_API_KEY")
            if not api_key:
                return {"error": "مفتاح API مطلوب لـ Clearbit"}
            
            headers = {"Authorization": f"Bearer {api_key}"}
            url = f"https://person.clearbit.com/v2/people/find?email={email}"
            resp = self.session.get(url, headers=headers, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "name": f"{data.get('name', {}).get('givenName', '')} {data.get('name', {}).get('familyName', '')}".strip(),
                    "location": data.get('geo', {}).get('city', ''),
                    "company": data.get('employment', {}).get('name', ''),
                    "title": data.get('employment', {}).get('title', ''),
                    "linkedin": data.get('linkedin', {}).get('handle', ''),
                    "twitter": data.get('twitter', {}).get('handle', ''),
                    "github": data.get('github', {}).get('handle', '')
                }
            elif resp.status_code == 404:
                return {"status": "not_found", "message": "لم يتم العثور على معلومات"}
            
            return {"error": f"خطأ API: {resp.status_code} - {resp.text}"}
            
        except Exception as e:
            logger.error(f"خطأ في clearbit: {str(e)}")
            return {"error": f"خطأ غير متوقع: {str(e)}"}

    def safe_subprocess_call(self, cmd: List[str], timeout: int = 60) -> Dict[str, Any]:
        """تنفيذ آمن للأوامر الخارجية"""
        try:
            # التحقق من وجود الأمر
            if not self._command_exists(cmd[0]):
                return {"error": f"الأمر غير متوفر: {cmd[0]}"}
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                check=False
            )
            
            if result.returncode == 0:
                return {"output": result.stdout, "status": "success"}
            else:
                return {"error": result.stderr or "فشل في تنفيذ الأمر", "status": "failed"}
                
        except subprocess.TimeoutExpired:
            return {"error": f"انتهت مهلة تنفيذ الأمر ({timeout} ثانية)"}
        except FileNotFoundError:
            return {"error": f"الأمر غير موجود: {cmd[0]}"}
        except Exception as e:
            return {"error": f"خطأ في التنفيذ: {str(e)}"}

    def _command_exists(self, command: str) -> bool:
        """التحقق من وجود أمر في النظام"""
        try:
            subprocess.run([command, "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def socialscan(self, email: str) -> Dict[str, Any]:
        """فحص الشبكات الاجتماعية - SocialScan"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        return self.safe_subprocess_call(["socialscan", email], timeout=120)

    def holehe(self, email: str) -> Dict[str, Any]:
        """فحص الحسابات - Holehe"""
        if not self.validator.validate_email(email):
            return {"error": "عنوان بريد إلكتروني غير صحيح"}
        
        return self.safe_subprocess_call(["holehe", email], timeout=120)

    def sherlock(self, username: str) -> Dict[str, Any]:
        """البحث عن اسم المستخدم - Sherlock"""
        if not self.validator.validate_username(username):
            return {"error": "اسم مستخدم غير صحيح"}
        
        username = self.validator.sanitize_input(username)
        return self.safe_subprocess_call(["sherlock", username, "--print-found"], timeout=180)

    def maigret(self, username: str) -> Dict[str, Any]:
        """البحث المتقدم عن اسم المستخدم - Maigret"""
        if not self.validator.validate_username(username):
            return {"error": "اسم مستخدم غير صحيح"}
        
        username = self.validator.sanitize_input(username)
        return self.safe_subprocess_call(["maigret", username, "--print-found"], timeout=180)

    async def async_osint_search(self, target: str, sources: List[str] = None) -> Dict[str, Any]:
        """بحث OSINT غير متزامن لتحسين الأداء"""
        if sources is None:
            sources = ['haveibeenpwned', 'hunterio', 'emailrep', 'leakcheck']
        
        results = {}
        tasks = []
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            for source in sources:
                if hasattr(self, source):
                    task = asyncio.create_task(self._async_source_call(source, target, session))
                    tasks.append((source, task))
            
            for source, task in tasks:
                try:
                    results[source] = await task
                except Exception as e:
                    results[source] = {"error": f"خطأ في {source}: {str(e)}"}
        
        return results

    async def _async_source_call(self, source: str, target: str, session: aiohttp.ClientSession):
        """استدعاء مصدر معين بشكل غير متزامن"""
        # هذه الدالة تحتاج تطوير إضافي لتحويل الدوال إلى async
        # في الوقت الحالي، سنستخدم الدوال المتزامنة
        method = getattr(self, source)
        return method(target)

    def comprehensive_search(self, target: str, target_type: str = "auto") -> Dict[str, Any]:
        """بحث شامل مع تحليل النتائج"""
        
        # تحديد نوع الهدف تلقائياً
        if target_type == "auto":
            if self.validator.validate_email(target):
                target_type = "email"
            elif self.validator.validate_username(target):
                target_type = "username"
            else:
                return {"error": "نوع الهدف غير مدعوم"}
        
        results = {}
        
        try:
            if target_type == "email":
                # البحث في المصادر المناسبة للبريد الإلكتروني
                email_sources = {
                    'haveibeenpwned': self.haveibeenpwned,
                    'hunterio': self.hunterio,
                    'leakcheck': self.leakcheck,
                    'emailrep': self.emailrep,
                    'clearbit': self.clearbit,
                    'holehe': self.holehe,
                    'socialscan': self.socialscan
                }
                
                for source_name, source_func in email_sources.items():
                    try:
                        logger.info(f"جاري البحث في {source_name}...")
                        results[source_name] = source_func(target)
                        time.sleep(1)  # تأخير قصير لتجنب Rate Limiting
                    except Exception as e:
                        results[source_name] = {"error": f"خطأ في {source_name}: {str(e)}"}
            
            elif target_type == "username":
                # البحث في المصادر المناسبة لاسم المستخدم
                username_sources = {
                    'sherlock': self.sherlock,
                    'maigret': self.maigret
                }
                
                for source_name, source_func in username_sources.items():
                    try:
                        logger.info(f"جاري البحث في {source_name}...")
                        results[source_name] = source_func(target)
                    except Exception as e:
                        results[source_name] = {"error": f"خطأ في {source_name}: {str(e)}"}
            
            # إنشاء التقرير الشامل
            report = self.reporter.generate_report(target, results)
            
            # حفظ التقرير
            report_path = self.reporter.save_report(report)
            
            return {
                "target": target,
                "target_type": target_type,
                "results": results,
                "report": report,
                "report_saved_to": report_path,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"خطأ في البحث الشامل: {str(e)}")
            return {"error": f"خطأ في البحث الشامل: {str(e)}"}

# إنشاء كائن OSINT عام للاستخدام
osint = EnhancedOSINT()

# الدوال المرجعية للتوافق مع الكود القديم
def haveibeenpwned(email: str) -> Dict[str, Any]:
    return osint.haveibeenpwned(email)

def hunterio(email: str) -> Dict[str, Any]:
    return osint.hunterio(email)

def leakcheck(email: str) -> Dict[str, Any]:
    return osint.leakcheck(email)

def emailrep(email: str) -> Dict[str, Any]:
    return osint.emailrep(email)

def clearbit(email: str) -> Dict[str, Any]:
    return osint.clearbit(email)

def socialscan(email: str) -> Dict[str, Any]:
    return osint.socialscan(email)

def holehe(email: str) -> Dict[str, Any]:
    return osint.holehe(email)

def sherlock(username: str) -> Dict[str, Any]:
    return osint.sherlock(username)

def maigret(username: str) -> Dict[str, Any]:
    return osint.maigret(username)

def comprehensive_search(target: str, target_type: str = "auto") -> Dict[str, Any]:
    """دالة البحث الشامل الجديدة"""
    return osint.comprehensive_search(target, target_type)
