import network
import socket
from machine import Pin, I2C
import ssd1306
import ure as re

BLOCKED_IPS = ['']
ALLOWED_IPS = ['']

# Initialize I2C and OLED display
i2c = I2C(0, scl=Pin(17), sda=Pin(16))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Initialize Wi-Fi station
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
    print('Connected to Wi-Fi')
    return wlan.ifconfig()[0]

wifi_ssid = 'SSID'
wifi_password = 'PASSWORD'
global server_ip
server_ip = connect_wifi(wifi_ssid, wifi_password)

print('IP Address To Connect to:: ' + server_ip)

# Display server IP on OLED
oled.fill(0)
oled.text("Server IP:", 0, 0)
oled.text(server_ip, 0, 10)
oled.show()

# Set up socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

chat_history = []
admin_password = 'admin123'

def load_chat_history():
    try:
        with open('chat_history.txt', 'r') as file:
            return file.readlines()
    except OSError:
        return []

def save_chat_history():
    with open('chat_history.txt', 'w') as file:
        file.write("".join(chat_history))

def web_page(name):
    chat_html = "".join(f"<p>{msg.strip()}</p>" for msg in chat_history)
    html = f"""
    <html>
        <head>
            <title>Pico Chat</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f0f0f0;
                    margin: 0;
                    padding: 0;
                }}
                #chat {{
                    background-color: #fff;
                    border: 1px solid #ccc;
                    padding: 10px;
                    margin: 20px auto;
                    width: 90%;
                    max-width: 600px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                }}
                form {{
                    margin: 20px auto;
                    width: 90%;
                    max-width: 600px;
                    display: flex;
                    flex-direction: column;
                }}
                input[type="text"], input[type="password"] {{
                    padding: 10px;
                    margin-bottom: 10px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    font-size: 16px;
                }}
                input[type="submit"] {{
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    background-color: #007BFF;
                    color: #fff;
                    font-size: 16px;
                    cursor: pointer;
                }}
                input[type="submit"]:hover {{
                    background-color: #0056b3;
                }}
            </style>
        </head>
        <body>
            <h1 style="text-align:center;">Welcome to Pico Chat</h1>
            <div id="chat">
                {chat_html}
            </div>
            <form action="/" method="POST">
                <input type="text" name="name" placeholder="Enter your name" value="{name}" required/>
                <input type="text" name="msg" placeholder="Enter your message" required/>
                <input type="submit" value="Send" />
            </form>
            <form action="/clear" method="POST">
                <input type="password" name="password" placeholder="Admin password" required/>
                <input type="submit" value="Clear Chat (Admin)" />
            </form>
        </body>
    </html>
    """
    return html

def get_cookie_value(headers, name):
    match = re.search(f'{name}=([^;]+)', headers)
    if match:
        return match.group(1)
    return ""

chat_history = load_chat_history()

def parse_form_data(data):
    parsed_data = {}
    for item in data.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            parsed_data[key] = value.replace('+', ' ')
    return parsed_data

while True:
    conn, addr = s.accept()
    client_ip = str(addr[0])
    print('Got a connection from %s' % client_ip)
    request = conn.recv(1024)
    request = request.decode()

    if (client_ip not in BLOCKED_IPS) and (client_ip not in ALLOWED_IPS): 
        import forbid
        response = forbid.HTML_FOR_401
        http_response = f"HTTP/1.1 401 Unauthorised\r\nContent-Type: text/html; charset=UTF-8\r\n{response}"
        conn.sendall(http_response.encode('utf-8'))
        conn.close()
        continue
        
    if client_ip in BLOCKED_IPS:
        import forbid
        response = forbid.HTML_FOR_403
        http_response = f"HTTP/1.1 403 Forbidden\r\nContent-Type: text/html; charset=UTF-8\r\n{response}"
        conn.sendall(http_response.encode('utf-8'))
        conn.close()
        continue
    
    print('Content:')
    print(request.strip())

    if '\r\n\r\n' in request:
        headers, body = request.split('\r\n\r\n', 1)
    else:
        headers, body = request, ''

    name = get_cookie_value(headers, 'name')
    
    if "POST /clear" in request:
        form_data = parse_form_data(body)
        password = form_data.get('password', '')
        if password == admin_password:
            chat_history = []
            save_chat_history()
    elif "POST /" in request:
        form_data = parse_form_data(body)
        name = form_data.get('name', '')
        msg = form_data.get('msg', '')
        if name and msg:
            chat_history.append(f"{name}: {msg}\n")
            save_chat_history()

    response = web_page(name)
    http_response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nSet-Cookie: name={name}; Path=/\r\n\r\n{response}"
    conn.sendall(http_response.encode('utf-8'))
    conn.close()
