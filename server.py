from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import os
import traceback

app = Flask(__name__)
CORS(app)

# Raspberry Pi'nin URL'si
RASPBERRY_PI_URL = os.environ.get('RASPBERRY_PI_URL')

if not RASPBERRY_PI_URL:
    print("HATA: RASPBERRY_PI_URL ortam değişkeni ayarlanmamış!")
    print("Örnek: http://your-raspberry-pi-ip:5000")

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Render LED Kontrol API Gateway Çalışıyor'
    })

@app.route('/led/<action>', methods=['POST'])
def control_led(action):
    if RASPBERRY_PI_URL is None:
         return jsonify({'status': 'error', 'message': 'Sunucu yapılandırma hatası: Raspberry Pi adresi belirlenmemiş.'}), 500

    target_status = None
    if action.lower() == 'on':
        target_status = True
    elif action.lower() == 'off':
        target_status = False
    else:
        return jsonify({'status': 'error', 'message': 'Geçersiz aksiyon. Sadece /led/on veya /led/off desteklenir.'}), 400

    try:
        # Raspberry Pi'ye istek gönder
        payload = {'status': target_status}
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{RASPBERRY_PI_URL}/led", json=payload, headers=headers, timeout=10)

        if response.status_code == 200:
            return jsonify({
                'status': 'success',
                'message': f'LED {action} komutu Raspberry Piye iletildi.',
                'pi_response': response.json()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'Raspberry Pi LED kontrol sırasında hata döndürdü: Durum Kodu {response.status_code}',
                'pi_response': response.json()
            }), response.status_code

    except requests.exceptions.Timeout:
        return jsonify({
            'status': 'error',
            'message': 'Raspberry Piye bağlanılamadı: İstek zaman aşımına uğradı.'
        }), 504

    except requests.exceptions.ConnectionError as e:
        return jsonify({
            'status': 'error',
            'message': f'Raspberry Piye bağlanılamadı: Bağlantı hatası ({e})'
        }), 503

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': 'Render sunucusunda dahili hata.',
            'error_details': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000) 
