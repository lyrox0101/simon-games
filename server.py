from flask import Flask, request, jsonify
import requests
import os
import traceback

app = Flask(__name__)

# Raspberry Pi'nin IP adresi ve portu (Render.com ortam değişkeninden alınacak)
# Render.com ayarlarına RASPBERRY_PI_URL adında bir ortam değişkeni ekleyin
# Değeri: http://<Raspberry_Pi_nizin_Yerel_IP_Adresi>:5000 (örn: http://192.168.1.49:5000)
# DİKKAT: Eğer Pi'nize internet üzerinden ulaşılacaksa bu adres Render'ın Pi'ye ulaşabildiği adres olmalı!
# Genellikle bu, port yönlendirme sonrası Pi'nin yerel IP + port kombinasyonu olur.
RASPBERRY_PI_URL = os.environ.get('RASPBERRY_PI_URL')

if not RASPBERRY_PI_URL:
    print("HATA: RASPBERRY_PI_URL ortam değişkeni ayarlanmamış!")
    # Render deploy sırasında hata verebilir veya runtime'da istek atınca hata alırsınız.

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'Render LED Kontrol API Gateway Çalışıyor',
        'raspberry_pi_target': RASPBERRY_PI_URL
    })

# Flutter uygulaması bu endpoint'e POST isteği gönderecek
@app.route('/led/<action>', methods=['POST'])
def control_led(action):
    if RASPBERRY_PI_URL is None:
         print("RASPBERRY_PI_URL ayarlı değil, istek gönderilemiyor.")
         return jsonify({'status': 'error', 'message': 'Sunucu yapılandırma hatası: Raspberry Pi adresi belirlenmemiş.'}), 500

    target_status = None
    if action.lower() == 'on':
        target_status = True
        print("LED açma isteği alındı.")
    elif action.lower() == 'off':
        target_status = False
        print("LED kapatma isteği alındı.")
    else:
        print(f"Geçersiz aksiyon: {action}")
        return jsonify({'status': 'error', 'message': 'Geçersiz aksiyon. Sadece /led/on veya /led/off desteklenir.'}), 400

    try:
        # Raspberry Pi'deki Flask sunucusuna HTTP POST isteği gönder
        # Body olarak {'status': True/False} göndermemiz gerekiyor
        payload = {'status': target_status}
        headers = {'Content-Type': 'application/json'}
        print(f"Raspberry Pi'ye istek gönderiliyor: {RASPBERRY_PI_URL}/led")
        response = requests.post(f"{RASPBERRY_PI_URL}/led", json=payload, headers=headers, timeout=10) # Timeout eklendi

        print(f"Raspberry Pi'den yanıt alındı: Durum Kodu {response.status_code}")
        # Pi'den gelen yanıtı istemciye döndür
        try:
            pi_response_json = response.json()
            print(f"Raspberry Pi Yanıt JSON: {pi_response_json}")
        except requests.exceptions.JSONDecodeError:
             pi_response_json = {"message": "Yanıt JSON formatında değil", "raw_response": response.text}
             print(f"Raspberry Pi Yanıtı (JSON değil): {pi_response_json}")


        if response.status_code == 200:
             # Pi 200 döndüyse başarılı say
             return jsonify({
                 'status': 'success',
                 'message': f'LED {action} komutu Raspberry Piye iletildi.',
                 'pi_response': pi_response_json
             }), 200
        else:
             # Pi hata döndüyse onu da istemciye bildir
             print(f"Raspberry Pi hata durumu döndürdü: {response.status_code}")
             return jsonify({
                 'status': 'error',
                 'message': f'Raspberry Pi LED kontrol sırasında hata döndürdü: Durum Kodu {response.status_code}',
                 'pi_response': pi_response_json
             }), response.status_code


    except requests.exceptions.Timeout:
        print("Raspberry Pi'ye istek zaman aşımına uğradı.")
        return jsonify({
            'status': 'error',
            'message': 'Raspberry Piye bağlanılamadı: İstek zaman aşımına uğradı.',
            'raspberry_pi_target': RASPBERRY_PI_URL
        }), 504 # Gateway Timeout

    except requests.exceptions.ConnectionError as e:
        print(f"Raspberry Pi'ye bağlantı hatası: {e}")
        # Bağlantı hatası genellikle Pi'ye ulaşılamadığını gösterir (port yönlendirme, IP hatası vb.)
        return jsonify({
            'status': 'error',
            'message': f'Raspberry Piye bağlanılamadı: Bağlantı hatası ({e}). IP adresini/portu ve port yönlendirmeyi kontrol edin.',
            'raspberry_pi_target': RASPBERRY_PI_URL
        }), 503 # Service Unavailable

    except Exception as e:
        print(f"Render sunucusunda beklenmeyen hata: {e}")
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': 'Render sunucusunda dahili hata.',
            'error_details': str(e)
        }), 500

# Render'ın servis durumunu kontrol etmek için (isteğe bağlı)
@app.route('/status', methods=['GET'])
def get_render_status():
    return jsonify({
        'status': 'online',
        'message': 'Render API Gateway çalışıyor',
        'raspberry_pi_target': RASPBERRY_PI_URL
    })


if __name__ == '__main__':
    # Render, portu OS ortam değişkeni olarak sağlar
    port = int(os.environ.get('PORT', 5000))
    print(f"Render sunucusu {port} portunda başlatılıyor...")
    # Gunicorn tarafından çalıştırılacağı için burada app.run'a gerek yok
    # app.run(host='0.0.0.0', port=port)
    # Lokal test için isterseniz bu yorum satırını kaldırabilirsiniz:
    # app.run(host='0.0.0.0', port=port, debug=True) 
