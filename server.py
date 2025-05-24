from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

# Raspberry Pi'nin IP adresi ve portu
RASPBERRY_PI_URL = "http://your-raspberry-pi-ip:5000"  # Raspberry Pi'nizin IP adresini buraya yazın

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'LED Kontrol Sunucusu Çalışıyor'
    })

@app.route('/status')
def status():
    return jsonify({
        'status': 'online',
        'led_status': False
    })

@app.route('/led/on', methods=['POST'])
def led_on():
    try:
        response = requests.post(f"{RASPBERRY_PI_URL}/led", json={'status': True})
        return jsonify({
            'status': 'success',
            'message': 'LED açıldı',
            'response': response.json()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/led/off', methods=['POST'])
def led_off():
    try:
        response = requests.post(f"{RASPBERRY_PI_URL}/led", json={'status': False})
        return jsonify({
            'status': 'success',
            'message': 'LED kapatıldı',
            'response': response.json()
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 