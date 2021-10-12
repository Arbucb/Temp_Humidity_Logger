import time
import datetime
import board
import adafruit_dht
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from influxdb import InfluxDBClient

dbClient  = InfluxDBClient('localhost', 8086, 'rasppi', 'rasppi010673', 'TempHumid')


from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
 
# Initiate the dht device, with data pin connected to:
# dhtDevice = adafruit_dht.DHT22(board.D4)
 
# you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
# This may be necessary on a Linux single board computer like the Raspberry Pi,
# but it will not work in CircuitPython.
dhtDevice = adafruit_dht.DHT11(board.D4, use_pulseio=False)
 
# Raspberry Pi pin configuration:
RST = None     # on the PiOLED this pin isnt used
# Note the following are only used with SPI:
DC = 23
SPI_PORT = 0
SPI_DEVICE = 0

# Beaglebone Black pin configuration:
# RST = 'P9_12'
# Note the following are only used with SPI:
# DC = 'P9_15'
# SPI_PORT = 1
# SPI_DEVICE = 0

# 128x32 display with hardware I2C:
#disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)

# 128x64 display with hardware I2C:
disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST)

# Note you can change the I2C address by passing an i2c_address parameter like:
#disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, i2c_address=0x3C)

# Alternatively you can specify an explicit I2C bus number, for example
# with the 128x32 display you would use:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, i2c_bus=2)

# 128x32 display with hardware SPI:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# 128x64 display with hardware SPI:
# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST, dc=DC, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=8000000))

# Alternatively you can specify a software SPI implementation by providing
# digital GPIO pin numbers for all the required display pins.  For example
# on a Raspberry Pi with the 128x32 display you might use:
# disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST, dc=DC, sclk=18, din=25, cs=22)

# Initialize library.
disp.begin()

# Clear display.
disp.clear()
disp.display()

# Create blank image for drawing.
# Make sure to create image with mode '1' for 1-bit color.
width = disp.width
height = disp.height
image = Image.new('1', (width, height))

# Get drawing object to draw on image.
draw = ImageDraw.Draw(image)

# Draw a black filled box to clear the image.
draw.rectangle((0,0,width,height), outline=0, fill=0)

# Draw some shapes.
# First define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
# Move left to right keeping track of the current x position for drawing shapes.
x = 0

# Load default font.
#font = ImageFont.load_default()

# Alternatively load a TTF font.  Make sure the .ttf font file is in the same directory as the python script!
# Some other nice fonts to try: http://www.dafont.com/bitmap.php
# font = ImageFont.truetype('Minecraftia.ttf', 8)

#Calc vertical spacing using number of lines being printed and the display height
nlines = 4
text_size = 16
spacing = ((height - (text_size * nlines)) / nlines + text_size )
print("Spacing: ", spacing)
font = ImageFont.truetype('/usr/share/fonts/truetype/piboto/Piboto-Regular.ttf', text_size)

while True:
    try:
        # Acquire the values from the DHT
        # This is a fix for an un-returned value from the DHT
        temperature_c = None
        max_retries = 50
        attempts = 0
        while temperature_c is None and attempts < max_retries:
            temperature_c = dhtDevice.temperature
            time.sleep(0.1)
            attempts = attempts + 1
            if attempts == max_retries:
                raise Exception("Exceeded max retries ({}) retrieving data from DHT, check connection and re-try".format(max_retries)) 
                dhtDevice.exit()
		
        temperature_f = float(temperature_c) * (9 / 5) + 32
        humidity = dhtDevice.humidity
        print(
            "Temp: {:.1f} F / {:.1f} C    Humidity: {}% ".format(
                temperature_f, temperature_c, humidity
            )
        )
 # This creates an entry into the influx DB referenced earlier.
        dbdata = [{"measurement":"Temp and Humidity",
        "tags": {
            "Address": "86 Old Rod Rd",
            "City": "Colchester",
            "State": "Connecticut",
            "Zipcode": "06415",
            "Location": "Pool Room",
            "Outside": "N"
        },
        "fields":
        {
        "Temperature F":"{:.1f}".format(temperature_f),
        "Humidity %":"{}".format(humidity)
        }       
        }        
        ]

        dbClient.write_points(dbdata)

        # Draw a black filled box to clear the image.
        draw.rectangle((0,0,width,height), outline=0, fill=0)

        now = datetime.datetime.now()

	# Write two lines of text.
        draw.text((x, top),       "Temp: {:.1f} F".format(temperature_f),  font=font, fill=255)
        draw.text((x, top+spacing),     "Humidity: {}%".format(humidity), font=font, fill=255)
        draw.text((x, top+spacing*2),    "Date: {}".format(now.strftime("%Y-%m-%d")),  font=font, fill=255)
        draw.text((x, top+spacing*3),    "Time: {}".format(now.strftime("%H:%M:%S")),  font=font, fill=255)

        # Display image.
        disp.image(image)
        disp.display()
        time.sleep(0.5)


    except RuntimeError as error:
        # Errors happen fairly often, DHT's are hard to read, just keep going
        # print(error.args[0])
        time.sleep(0.5)
        continue
    except Exception as error:
        dhtDevice.exit()
        raise error
 
    time.sleep(5.0)