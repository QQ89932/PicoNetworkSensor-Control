import rp2  # Import the rp2 module which contains functions and classes specifically for RP2040
import network  # Import the network module for connecting to WiFi
import ubinascii  # Import the ubinascii module for converting MAC address to hex string
import machine  # Import the machine module for GPIO control
import urequests as requests  # Import the urequests module for HTTP requests
import time  # Import the time module for delay
import socket  # Import the socket module for establishing sockets

# Set country code to avoid potential errors
# CN/US/DE/DK/GB/JP (country code: China/USA/Germany/Denmark/UK/Japan)
rp2.country('GB')  # Set the country code for Pico W to UK
wlan = network.WLAN(network.STA_IF)  # Create WLAN connection object
wlan.active(True)  # Activate WLAN interface

# Check the MAC address of Pico W board's wireless WiFi
# Get the MAC address and convert it to hex string
mac = ubinascii.hexlify(network.WLAN().config('mac'), ':').decode()
print('Pico W MAC address=' + mac)  # Display the hexadecimal MAC address of Pico W board

ssid = 'QiaoDong_SmartHome'  # Set the WiFi name (ssid: service set identifier)
psw = 'Qiaodong666'  # Set the WiFi password

wlan.connect(ssid, psw)  # Connect to the WiFi network

timeout = 10  # Set the maximum waiting time for connection to be 10 seconds
while timeout > 0:
    if wlan.status() < 0 or wlan.status() >= 3:  # If the WiFi connection succeeds or fails
        break  # Exit the loop
    timeout -= 1
    print('Waiting for connection!')
    time.sleep(1)  # Delay for 1 second


# Define function for flashing onboard LED of Pico W board
def onboard_led_blink(blink_numbers):
    onboard_led = machine.Pin('LED', machine.Pin.OUT)  # Create GPIO control object
    for i in range(blink_numbers):
        onboard_led.value(1)  # Turn on LED
        # onboard_led.on()  # Another way to turn on LED
        time.sleep(0.5)
        onboard_led.value(0)  # Turn off LED
        # onboard_led.off()  # Another way to turn off LED
        time.sleep(0.5)


wlan_status = wlan.status()  # Get the current WiFi connection status
onboard_led_blink(wlan_status)  # Control LED based on WiFi connection status

# Handle connection errors
if wlan_status != 3:  # If the WiFi connection fails
    raise RuntimeError('WiFi connection failed!')  # Raise an exception
else:
    print('WiFi connected...')
    status = wlan.ifconfig()  # Get the WiFi interface configuration information
    print('IP address=' + status[0])  # Output the IP address


# Define function for loading HTML page
def get_html(html_name):
    with open(html_name, 'r') as file:  # Open the HTML file
        html = file.read()  # Read the HTML content
    return html


# Open HTTP Web server socket
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]  # Get the IP address and port number
s = socket.socket()  # Create socket object
s.bind(addr)  # Bind the socket to the IP address and port number
# Start listening to the port number
s.listen(3)  # Allow up to 3 clients to connect

print('Listening on', addr)

onboard_led = machine.Pin('LED', machine.Pin.OUT)
adc = machine.ADC(26)
# Enter a loop to listen for connections
num = 666
while True:
    try:
        # Accept client connection and get the address
        cl, addr = s.accept()
        print('Client connection from', addr)
        # Receive client request message
        r = cl.recv(1024)
        r = str(r)
        # Search for the commands to turn on/off the LED in the request message
        onboard_led_on = r.find('?onboard_led=1')
        onboard_led_off = r.find('?onboard_led=0')
        newon = r.find('?onnew_vlaue=1')
        print('LED=', onboard_led_on)
        print('LED=', onboard_led_off)
        value = adc.read_u16()
        # Calculate voltage
        voltage = value * 3.3 / 65535
        # Calculate soil moisture
        humidity = str((voltage - 1.1) / 1.1 * 100)
        # If '?onboard_led=1' is found, turn on the LED
        if onboard_led_on > -1:
            print('LED on')
            onboard_led.value(1)
        # If '?onboard_led=0' is found, turn off the LED
        if onboard_led_off > -1:
            print('LED off')
            onboard_led.value(0)
        if newon > -1:
            response = humidity
            #response = get_html('index.html')
        else:
            # Get the content of the HTML file
            response = get_html('index.html')
        # Send HTTP response header
        if onboard_led_on > -1 or onboard_led_off > -1:
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            cl.close()
        else:
            cl.send('HTTP/1.0 200 OK\r\nContent-type: text/html\r\n\r\n')
            # Send the content of the HTML file
            cl.send(response)
            print('Sent:'+response)
            # Close the client socket
            cl.close()

    # If an OSError occurs, close the client socket and output relevant information
    except OSError as e:
        cl.close()
        print('Connection closed')
        print(repr(e))
