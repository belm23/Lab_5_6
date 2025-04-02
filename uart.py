import RPi.GPIO as GPIO
import serial
from time import sleep

# Pines de control del motor
IN1 = 17
IN2 = 27
ENA = 12  # PWM
BOTON = 19  # <-- Aquí conectas tu botón

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(IN1, GPIO.OUT)
GPIO.setup(IN2, GPIO.OUT)
GPIO.setup(ENA, GPIO.OUT)
GPIO.setup(BOTON, GPIO.IN, pull_up_down=GPIO.PUD_UP)  

# Inicializar PWM
pwm = GPIO.PWM(ENA, 1000)
pwm.start(0)

# Dirección fija: adelante
GPIO.output(IN1, GPIO.LOW)
GPIO.output(IN2, GPIO.HIGH)

# Función para leer duty desde archivo
def leer_duty_cycle():
    try:
        with open("dutycycle.txt", "r") as file:
            duty = int(file.read().strip())
            if 0 <= duty <= 100:
                return duty
            else:
                print("Valor fuera de rango (0-100)")
                return 50
    except:
        print("Error leyendo el archivo.")
        return 50

# UART
ser = serial.Serial('/dev/ttyACM0', 9600, timeout=1)
ser.reset_input_buffer()
sleep(2)
print("UART conectado en /dev/ttyACM0")

# Bandera para control de dirección del motor 2
motor2_direccion = GPIO.HIGH  # Comienza hacia adelante

try:
    while True:
        # Enviar "buzzer" si se presiona el botón
        if GPIO.input(BOTON) == GPIO.LOW:
            print("Botón presionado, enviando 'buzzer'")
            ser.write("buzzer\n".encode('utf-8'))
            sleep(0.5)  # evitar múltiples envíos por rebote

        # Leer desde Tiva
        if ser.in_waiting > 0:
            raw = ser.readline()
            try:
                value = raw.decode('utf-8').strip()
                print(f"Tiva dice: {value}")

                if value == "motor1":
                    duty = leer_duty_cycle()
                    pwm.ChangeDutyCycle(duty)
                    print(f"Motor 1 activado con {duty}%")

                elif value == "motor2":
                    # Cambiar la dirección del motor 2
                    if motor2_direccion == GPIO.HIGH:
                        GPIO.output(IN1, GPIO.LOW)
                        GPIO.output(IN2, GPIO.HIGH)
                        motor2_direccion = GPIO.LOW
                        print("Motor 2 cambiado a dirección opuesta")
                    else:
                        GPIO.output(IN1, GPIO.HIGH)
                        GPIO.output(IN2, GPIO.LOW)
                        motor2_direccion = GPIO.HIGH
                        print("Motor 2 cambiado a dirección inicial")
                    sleep(1)  # Detener motor 2 por 1 segundo antes de cambiar la dirección

            except UnicodeDecodeError:
                print(f"Bytes ilegibles: {raw}")
        
        sleep(0.1)

except KeyboardInterrupt:
    print("Programa terminado por el usuario.")

finally:
    pwm.stop()
    GPIO.cleanup()
    ser.close()
