import asyncio
import logging
import sys
import time
from colorama import Fore, Style
import requests
import ipinfo

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackContext, CallbackQueryHandler, CommandHandler

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token de tu bot
TOKEN = '7121217645:AAHc6ixQa_qglg9NEj3bOk02CTAs8DkF53E'
# ID de chat
CHAT_ID = 1001949353956  # Asegúrate de que este ID es correcto y el bot tiene acceso a este chat

# Función que maneja el botón
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text="Botón presionado")
    # Aquí reenviamos el mensaje a un enlace
    await context.bot.send_message(chat_id=query.message.chat_id, text="Mensaje reenviado a un enlace")

# Función que envía mensajes periódicamente cada 2 minutos
async def periodic_message(context: CallbackContext) -> None:
    button = InlineKeyboardButton("Presióname", callback_data='button_pressed')
    keyboard = InlineKeyboardMarkup([[button]])
    # Enviar mensaje al chat específico
    await context.bot.send_message(chat_id=CHAT_ID, text='Por favor, presiona el botón', reply_markup=keyboard)

# Función para manejar el comando personalizado /ip
async def custom_command(update: Update, context: CallbackContext) -> None:
    job_queue = context.job_queue
    # Eliminar trabajos anteriores si hay alguno para evitar duplicaciones
    job_queue.stop()
    job_queue.run_repeating(periodic_message, interval=120, first=0)

    # Obtener la IP del mensaje de comando
    ip = update.message.text.split(" ", 1)[1].strip() if len(update.message.text.split(" ", 1)) > 1 else None

    if ip:
        access_token = "6b1f42952f063e"
        handler = ipinfo.getHandler(access_token)

        try:
            for i in range(11):
                time.sleep(0.1)
                color = Fore.RED if i % 3 == 0 else (Fore.YELLOW if i % 3 == 1 else Fore.BLUE)
                sys.stdout.write(f"\rObteniendo información de la IP... [{color}{'='*i}{Style.RESET_ALL}{' '*(10-i)}] {Fore.GREEN}{i*10}%{Style.RESET_ALL}")
                sys.stdout.flush()

            print("\n")

            # Obtener datos de la primera fuente (ipinfo)
            details = handler.getDetails(ip)
            data1 = details.all

            # Obtener datos de la segunda fuente (ipapi.co)
            response = requests.get(f"https://ipapi.co/{ip}/json/")
            if response.status_code == 200:
                data2 = response.json()
            else:
                data2 = {}

            # Obtener datos de la tercera fuente (ip2location.io)
            response = requests.get(f"https://api.ip2location.io/?key=3C93D50C65D44735DF3C48A56FFD9899&ip={ip}")
            if response.status_code == 200:
                data3 = response.json()
            else:
                data3 = {}

            # Combinar datos de las tres fuentes
            combined_data = {**data1, **data2, **data3}

            # Mostrar la información combinada
            ip_info_text = format_ip_info(combined_data)
            await update.message.reply_text(ip_info_text)

        except ipinfo.exceptions.RequestQuotaExceededError:
            await update.message.reply_text("Se ha excedido el límite de solicitudes de la API.")
        except ipinfo.exceptions.AuthenticationError:
            await update.message.reply_text("Error de autenticación. Asegúrate de que tu token de acceso sea válido.")
        except Exception as e:
            await update.message.reply_text(f"Error: {str(e)}")
    else:
        await update.message.reply_text("Por favor, proporciona una dirección IP después del comando /ip.")

def format_ip_info(data):
    def get_nested(data, keys, default="No disponible"):
        for key in keys:
            if isinstance(data, dict):
                data = data.get(key, default)
            else:
                return default
        return data

    asn = data.get('asn', "No disponible")
    asn_url = f"https://ipinfo.io/AS{asn}" if asn != "No disponible" else "No disponible"

    ip_info_text = f'''
    🏝️ País: {data.get('country_name', "No disponible")}
    🗺️ Región: {data.get('region', data.get('region_name', "No disponible"))}
    🌆 Ciudad: {data.get('city', data.get('city_name', "No disponible"))}
    📮 Código postal: {data.get('postal', data.get('zip_code', "No disponible"))}
    🌍 Latitud: {data.get('latitude', "No disponible")}
    🌍 Longitud: {data.get('longitude', "No disponible")}
    ⏰ Zona horaria: {data.get('timezone', data.get('time_zone', "No disponible"))}
    ⏰ Zona horaria (olson): {get_nested(data, ['time_zone_info', 'olson'])}
    ⏰ Hora actual: {get_nested(data, ['time_zone_info', 'current_time'])}
    ⏰ GMT offset: {get_nested(data, ['time_zone_info', 'gmt_offset'])}
    ⏰ DST: {"Sí" if get_nested(data, ['time_zone_info', 'is_dst'], False) else "No"}
    🌅 Amanecer: {get_nested(data, ['time_zone_info', 'sunrise'])}
    🌇 Atardecer: {get_nested(data, ['time_zone_info', 'sunset'])}
    💼 ISP: {data.get('org', data.get('isp', "No disponible"))}
    📞 Código de llamada de país: {data.get('country_calling_code', data.get('idd_code', "No disponible"))}
    🌐 Lenguaje: {data.get('languages', get_nested(data, ['country', 'language', 'name']))}
    📊 Código ISO 3166-1 alfa-2: {data.get('country_code', get_nested(data, ['country', 'alpha2_code']))}
    📊 Código ISO 3166-1 alfa-3: {data.get('country_code_iso3', get_nested(data, ['country', 'alpha3_code']))}
    🔒 Código postal seguro: {"Sí" if data.get('in_eu', False) else "No"}
    📡 ASN: {asn} (URL: {asn_url})
    📶 Tipo de conexión: {data.get('connection_type', data.get('net_speed', "No disponible"))}
    🌐 Dominio: {data.get('domain', "No disponible")}
    🛡️ Utiliza VPN: {"Sí" if data.get('vpn', data.get('is_proxy', False)) else "No"}
    ☎️ Código de área: {data.get('area_code', "No disponible")}
    📶 Código de red móvil: {data.get('mobile', data.get('mcc', "No disponible"))}
    🖥️ Tipo de dispositivo: {data.get('device_type', "No disponible")}
    🌐 Tipo de navegador: {data.get('browser', "No disponible")}
    🇪🇺 Región de la Unión Europea: {"Sí" if data.get('in_eu', False) else "No"}
    🏙️ Ciudad en la Unión Europea: {data.get('eu_city', data.get('city_name', "No disponible"))}
    🏙️ Código postal en la Unión Europea: {data.get('eu_postal', data.get('zip_code', "No disponible"))}
    ☎️ Código de área telefónica: {data.get('area_code', "No disponible")}
    🏢 Tipo de uso: {data.get('usage_type', "No disponible")}
    🌍 IPv4: {data.get('ip', "No disponible")}
    🌍 Versión de IP: {data.get('version', "No disponible")}
    🌍 Tipo de IP: {data.get('type', data.get('address_type', "No disponible"))}
    🌍 Clase de IP: {data.get('ip_class', "No disponible")}
    🌐 Proxy: {"Sí" if data.get('proxy', data.get('is_proxy', False)) else "No"}
    🏢 Dominio secundario: {data.get('domain_secondary', "No disponible")}
    🔢 Número de bloque de IP: {data.get('ip_block', "No disponible")}
    🔒 Secure Proxy: {"Sí" if data.get('secure_proxy', False) else "No"}
    🛡️ Seguridad: {data.get('security', "No disponible")}
    🌐 Velocidad de conexión: {data.get('connection_speed', "No disponible")}
    📶 Tipo de red móvil: {data.get('mobile_type', "No disponible")}
    🎯 Propósito de uso de la IP: {data.get('ip_purpose', "No disponible")}
    📅 Fecha y hora de la consulta: {data.get('request_time', "No disponible")}
    ⏰ Hora local: {data.get('localtime', get_nested(data, ['time_zone_info', 'current_time']))}
    🏢 Organización: {data.get('org', data.get('isp', "No disponible"))}
    📡 Carrier móvil: {data.get('carrier', "No disponible")}
    🏢 Proveedor de Hosting: {data.get('hosting', "No disponible")}
    🏪 Tipo de mercado: {data.get('market', "No disponible")}
    🏪 Descripción del mercado: {data.get('market_description', "No disponible")}
    🌐 URL: {data.get('url', "No disponible")}
    '''

    return ip_info_text

# Función para obtener el ID del chat
async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    await update.message.reply_text(f'Bot Bsz Scrapea Tu ID de chat es {chat_id}')

# Función principal para iniciar el bot
async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Configurar manejadores
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ip", custom_command))  
    # Comando personalizado /ip

    # Iniciar el bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Mantener el bot corriendo
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Detener el bot si se interrumpe con Ctrl+C
        pass

if __name__ == '__main__':
    asyncio.run(main())
