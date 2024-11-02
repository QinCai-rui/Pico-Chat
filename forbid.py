HTML_FOR_403 = '''
<!DOCTYPE HTML>
<html>
    <head>
        <title>403 Forbidden</title>
    </head>
    <body>
        <h1>403 Forbidden</h1>
        <p>You don't have permission to access this resource.</p>
        <hr>
        <address>MicroPython (RP2040) Server at {server_ip} Port 80</address>
    </body>
</html>
'''

HTML_FOR_401 = '''
<!DOCTYPE HTML>
<html>
    <head>
        <title>401 Unauthorised</title>
    </head>
    <body>
        <h1>401 Unauthorised</h1>
        <p>You don't have permission to access this resource. Please contact application owner for more information or for access.</p>
        <hr>
        <address>MicroPython (RP2040) Server at {server_ip} Port 80</address>
    </body>
</html>
'''
