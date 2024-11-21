from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import requests

app = Flask(__name__)

# رابط التشفير
ENCRYPTION_API = "https://api-ghost.vercel.app/FFcrypto/"

# قاعدة بيانات داخلية لحفظ الأكواد
keys_db = {}

# دالة للتحقق من صلاحية الكود وحذفه إذا انتهت صلاحيته
def check_and_cleanup_keys():
    now = datetime.now()
    keys_to_delete = [key for key, value in keys_db.items() if datetime.strptime(value["expires_at"], "%Y-%m-%d %H:%M:%S") < now]

    for key in keys_to_delete:
        del keys_db[key]

# فحص المفتاح
@app.route('/check_key', methods=['GET'])
def check_key():
    encrypted_key = request.args.get('key')  # فحص بالكود المشفر

    # التحقق من صلاحية الكود قبل إجراء الفحص
    check_and_cleanup_keys()

    if encrypted_key in keys_db:
        return jsonify({
            "status": "exists",
            "encrypted_key": encrypted_key,
            "created_at": keys_db[encrypted_key]["created_at"],
            "expires_at": keys_db[encrypted_key]["expires_at"]
        })
    return jsonify({"status": "not_found"})

# إضافة مفتاح
@app.route('/add_key', methods=['GET'])
def add_key():
    key = request.args.get('key')
    duration_days = int(request.args.get('duration_days', 30))  # الافتراضي 30 يومًا

    if not key:
        return jsonify({"status": "error", "message": "Key is required"}), 400

    # إرسال الكود للتشفير باستخدام API
    try:
        response = requests.get(f"{ENCRYPTION_API}{key}")
        if response.status_code != 200:
            return jsonify({"status": "error", "message": "Failed to encrypt the key"}), 500
        encrypted_key = response.text.strip()  # الكود المُشفر الذي تم إرجاعه
    except Exception as e:
        return jsonify({"status": "error", "message": f"Encryption API error: {str(e)}"}), 500

    # تحقق من وجود الكود المشفر مسبقًا
    if encrypted_key in keys_db:
        return jsonify({"status": "error", "message": "Key already exists"}), 400

    created_at = datetime.now()
    expires_at = created_at + timedelta(days=duration_days)

    # تخزين البيانات في الذاكرة
    keys_db[encrypted_key] = {
        "original_key": key,
        "created_at": created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "expires_at": expires_at.strftime("%Y-%m-%d %H:%M:%S")
    }

    return jsonify({
        "status": "success",
        "key": key,
        "encrypted_key": encrypted_key,
        "created_at": keys_db[encrypted_key]["created_at"],
        "expires_at": keys_db[encrypted_key]["expires_at"]
    })

# تشغيل التطبيق
if __name__ == '__main__':
    app.run(debug=True)
