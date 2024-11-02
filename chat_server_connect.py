# Imports necessary libraries 
import network
import socket
from machine import Pin, I2C
import ssd1306
import ure as re
from time import sleep

# Lists for known client IP addresses; Blocked and Allowed
BLOCKED_IPS = ['']
ALLOWED_IPS = ['']

# Initialise I2C and OLED display
i2c = I2C(0, scl=Pin(17), sda=Pin(16))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

oled.fill(0)

# Function to connect to Wi-Fi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        oled.text("Connecting to", 0, 0)
        oled.text("Wi-Fi...", 0, 10)
        oled.show()
    print('Connected to Wi-Fi')
    oled.fill(0)
    oled.text("Connected!", 0, 0)
    sleep(1.5)
    return wlan.ifconfig()[0]

# Set Wi-Fi credentials
wifi_ssid = 'SSID' # Insert your own SSID here!!
wifi_password = 'PASSWORD' # Insert your own password (PSK) here!!

# Connect to Wi-Fi and get server IP
global server_ip
server_ip = connect_wifi(wifi_ssid, wifi_password)

# Print IP address to the console
print('IP Address To Connect to:: ' + server_ip)

# Display server IP on the OLED screen
oled.fill(0)
oled.text("Server IP:", 0, 0)
oled.text(server_ip, 0, 10)
oled.show()

# Set up server socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('', 80))
s.listen(5)

# Initialise chat history and set admin password
chat_history = []
admin_password = 'admin123210' # Change this password if you want to

# Function to load chat history from file
def load_chat_history():
    try:
        with open('chat_history.txt', 'r') as file:
            return file.readlines()
    except OSError:
        return []

# Function to save chat history to file
def save_chat_history():
    with open('chat_history.txt', 'w') as file:
        file.write("".join(chat_history))

# Function to generate HTML and CSS for the webpage
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
                    background-color: #ffffff;
                    border: 1px solid #cccccc;
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
                    border: 1px solid #cccccc;
                    border-radius: 5px;
                    font-size: 16px;
                }}
                input[type="submit"] {{
                    padding: 10px;
                    border: none;
                    border-radius: 5px;
                    background-color: #007BFF;
                    color: #ffffff;
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
                <input type="password" name="password" placeholder="Admin password pls" required/>
                <input type="submit" value="Clear Chat (Admin)" />
            </form>
        </body>
    </html>
    """
    return html

# Function to get cookie value from headers
def get_cookie_value(headers, name):
    match = re.search(f'{name}=([^;]+)', headers)
    if match:
        return match.group(1)
    return ""

# Load chat history from file
chat_history = load_chat_history()

# Function to parse form data from request
def parse_form_data(data):
    parsed_data = {}
    for item in data.split('&'):
        if '=' in item:
            key, value = item.split('=', 1)
            parsed_data[key] = value.replace('+', ' ')
    return parsed_data

while True:
    # Accept incoming connections
    conn, addr = s.accept()
    client_ip = str(addr[0])
    print('Got a connection from %s' % client_ip)
    request = conn.recv(1024)
    request = request.decode()

    # Block or allow client IPs based on lists
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

    # Split headers and body from request
    if '\r\n\r\n' in request:
        headers, body = request.split('\r\n\r\n', 1)
    else:
        headers, body = request, ''

    name = get_cookie_value(headers, 'name')
    
    # Clear chat history if admin password is correct
    if "POST /clear" in request:
        form_data = parse_form_data(body)
        password = form_data.get('password', '')
        if password == admin_password:
            chat_history = []
            save_chat_history()
    # Add new message to chat history
    elif "POST /" in request:
        form_data = parse_form_data(body)
        name = form_data.get('name', '')
        msg = form_data.get('msg', '')
        if name and msg:
            chat_history.append(f"{name}: {msg}\n")
            save_chat_history()

    # Generate and send HTML response
    response = web_page(name)
    http_response = f"HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=UTF-8\r\nSet-Cookie: name={name}; Path=/\r\n\r\n{response}"
    conn.sendall(http_response.encode('utf-8'))
    conn.close()
