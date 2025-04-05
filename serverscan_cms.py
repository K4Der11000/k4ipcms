from flask import Flask, render_template_string, request
import requests
import socket
import threading
import os
import sys
import signal
from datetime import datetime

app = Flask(__name__)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang=\"ar\">
<head>
    <meta charset=\"UTF-8\">
    <title>فحص السيرفر - ServerScan CMS</title>
    <link href=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css\" rel=\"stylesheet\">
</head>
<body class=\"bg-light text-center\">
    <div class=\"container py-5\">
        <h1 class=\"mb-4\">ServerScan CMS</h1>
        <h5 class=\"text-muted mb-4\">بواسطة kader11000 | التاريخ: {{ now }}</h5>
        
        {% if not proxies %}
        <div class=\"alert alert-warning alert-dismissible fade show\" role=\"alert\">
            لا توجد بروكسيات متاحة حالياً!
            <button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"alert\" aria-label=\"Close\"></button>
        </div>
        {% endif %}

        <form method=\"POST\" class=\"card card-body shadow-sm\">
            <input type=\"text\" name=\"domain\" class=\"form-control\" placeholder=\"أدخل رابط موقع أو IP\" required>
            <select name=\"proxy_speed\" class=\"form-select mt-2\">
                <option value=\"fast\">سريعة</option>
                <option value=\"all\">كل السرعات</option>
            </select>
            <button type=\"submit\" class=\"btn btn-primary mt-3\">بدء الفحص</button>
        </form>

        <form action=\"/shutdown\" method=\"post\" class=\"d-inline\">
            <button type=\"submit\" class=\"btn btn-danger mt-3\">إيقاف السيرفر</button>
        </form>
        <form action=\"/restart\" method=\"post\" class=\"d-inline\">
            <button type=\"submit\" class=\"btn btn-warning mt-3\">إعادة التشغيل</button>
        </form>

        {% if results %}
        <div class=\"mt-5 text-start\">
            <h4>نتائج الفحص:</h4>
            <ul class=\"list-group\">
                {% for res in results %}
                <li class=\"list-group-item\">
                    <strong>{{ res['site'] }}</strong><br>
                    IP: {{ res['ip'] }}<br>
                    CMS: {{ res['cms'] or 'غير معروف' }}
                </li>
                {% endfor %}
            </ul>
        </div>
        {% endif %}
    </div>
    <script src=\"https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js\"></script>
</body>
</html>"""

proxies = ['http://123.456.78.90:8080', 'http://111.222.333.444:3128']

def get_fast_proxies():
    return [proxy for proxy in proxies if "123" in proxy]

def get_sites_on_same_server(ip):
    return [f"site{i}.{ip.replace('.', '-')}.com" for i in range(1, 4)]

def detect_cms(domain):
    try:
        r = requests.get(f"http://{domain}", timeout=5)
        if 'wp-content' in r.text:
            return "WordPress"
        elif 'Joomla' in r.text:
            return "Joomla"
        elif 'Drupal' in r.text:
            return "Drupal"
    except:
        pass
    return None

def resolve_domain(domain):
    try:
        return socket.gethostbyname(domain)
    except:
        return None

def scan_domain(domain, use_fast_proxies=True):
    ip = resolve_domain(domain)
    if not ip:
        return []
    sites = get_sites_on_same_server(ip)
    results = []
    threads = []
    lock = threading.Lock()

    def worker(site):
        cms = detect_cms(site)
        with lock:
            results.append({\"site\": site, \"ip\": ip, \"cms\": cms})

    for site in sites:
        t = threading.Thread(target=worker, args=(site,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    return results

@app.route("/", methods=["GET", "POST"])
def index():
    results = []
    if request.method == "POST":
        domain = request.form['domain']
        speed = request.form.get('proxy_speed', 'fast')
        use_fast = speed == 'fast'
        results = scan_domain(domain, use_fast_proxies=use_fast)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template_string(HTML_TEMPLATE, results=results, proxies=proxies if proxies else [], now=now)

@app.route("/shutdown", methods=["POST"])
def shutdown():
    pid = os.getpid()
    os.kill(pid, signal.SIGTERM)
    return "تم إيقاف السيرفر نهائيًا."

@app.route("/restart", methods=["POST"])
def restart():
    python = sys.executable
    os.execl(python, python, *sys.argv)
    return "جارٍ إعادة تشغيل السيرفر..."

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)
