import os
import shutil
import subprocess
import signal
import gps
import time
import socket

# Server Configuration
HOST = '0.0.0.0'  # Accepts connections from any address
PORT = 8081  # Listening port

# Global variables
camera_process = None
gps_process = None
auxiliar = False    #MODIFIED to run without GPS signal

def stop_and_disable_serial_getty():
    # Stop and disable serial-getty on /dev/ttyS0 to avoid conflicts when reading GPS signal
    subprocess.run("sudo systemctl stop serial-getty@ttyS0.service", shell=True)
    subprocess.run("sudo systemctl disable serial-getty@ttyS0.service", shell=True)
    subprocess.run("sudo systemctl restart gpsd", shell=True)
    print("Servicios serial-getty y gpsd configurados correctamente.")

def open_camera_and_gps():
    global camera_process, gps_process

    if camera_process is None:
        print("Iniciando la grabacion de video y GPS...")

        # Start camera recording
        camera_process = subprocess.Popen("libcamera-vid -t 0 --vf -o /home/drone/Desktop/tflite1/grabacion.h264", shell=True, preexec_fn=os.setsid)

        # Start GPS in a separate process
        gps_process = subprocess.Popen("python3 /home/drone/Desktop/tflite1/gpsDrone.py", shell=True, preexec_fn=os.setsid)
        
        print("Camara y GPS iniciados.")

    else:
        print("La camara ya est en funcionamiento.")

def close_camera_and_gps():
    global camera_process, gps_process

    if camera_process is not None:
        print("Cerrando la camara y el GPS...")

        # Stop camera recording
        os.killpg(os.getpgid(camera_process.pid), signal.SIGTERM)
        camera_process = None
        print("Proceso de la camara detenido.")

        # Stop GPS process
        if gps_process is not None:
            os.killpg(os.getpgid(gps_process.pid), signal.SIGTERM)
            gps_process = None
            print("Proceso de GPS detenido.")

    else:
        print("La camara ya est cerrada.")

def convert_to_srt():
    #Convert GPS data to SRT file for subtitles.
    with open("/home/drone/Desktop/tflite1/coordenadas.txt", "r") as infile, open("/home/drone/Desktop/tflite1/coordenadas.srt", "w") as outfile:
        index = 1
        lines = infile.readlines()
        for i in range(len(lines)):
            if i < len(lines) - 1:
                start_time = lines[i].split("    ")[0]
                end_time = lines[i+1].split("    ")[0]
            else:
                start_time = lines[i].split("    ")[0]
                end_time = "99:59:59,999"

            coords = lines[i].split("    ")[1].strip()
            outfile.write(f"{index}\n")
            outfile.write(f"{start_time} --> {end_time}\n")
            outfile.write(f"{coords}\n\n")
            index += 1

def apply_subtitles_to_video():
    #Apply generated subtitles to a video using ffmpeg.
    print("Aplicando subti­tulos al video...")
    subprocess.run('ffmpeg -y -i /home/drone/Desktop/tflite1/grabacion.h264 -vf "subtitles=/home/drone/Desktop/tflite1/coordenadas.srt:force_style=\'FontSize=24,PrimaryColour=&HFFFFFF&\'" -c:a copy /home/drone/Desktop/tflite1/grabacionCoordenadas.h264', shell=True)
    print("Video con subti­tulos generado.")

def detect_objects():
    #Detect objects with Tensorflow Lite in recorded video.
    print("Iniciando detecciÃ³n de objetos en el video grabado...")
    subprocess.run("python3 /home/drone/Desktop/tflite1/TFLite_detection_video.py --modeldir /home/drone/Desktop/tflite1/Sample_TFLite_model --video /home/drone/Desktop/tflite1/grabacionCoordenadas.h264", shell=True)

def copy_video_to_usb():
    #Copy the generated video to a USB flash drive.
    video_name = "output_video.mp4"
    usb_path = "/media/drone/ESD-USB" # USB Path
    video_path = os.path.join('/home/drone/Desktop/tflite1', video_name)

    if os.path.exists(usb_path):
        shutil.copy(video_path, usb_path)
        print(f"El video {video_name} se ha copiado correctamente a la USB en {usb_path}.")
    else:
        print("La ruta de la USB no existe.")

def shutdown_raspberry_pi():
    #Shutdown Raspberry Pi.
    os.system("sudo shutdown -h now")
    
def gps_data():
	global auxiliar
	session = gps.gps(mode=gps.WATCH_ENABLE)
	print("buscando")
	estado = True
	while estado:
		print("sigo")
		report = session.next()
		if report['class'] == 'TPV':
			print ("coordenadas")
			estado = False
			auxiliar = False
			print (estado)
			send_gps_signal() #Send GPS signal ready
		else: 
				estado = True
				print (estado)
	print ("saliendo")
    
def send_gps_signal():
	try:
		esp_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
		esp_socket.connect(('192.168.4.200',8081))
		esp_socket.sendall(b'gps_ready')
		esp_socket.close()
		print("Mensaje de GPS listo enviado a ESP8266.")
	except Exception as e:
		print(f"Error enviando mensaje a ESP8266: {e}")

def process_command(command):
    #Processes received commands to open/close the camera and GPS.
    global gps_thread
    if command == "button1" and camera_process is None:
        open_camera_and_gps()
        return "Grabacion iniciada"
    elif command == "button1" and camera_process is not None:
        close_camera_and_gps()
        convert_to_srt()
        apply_subtitles_to_video()
        return "Grabacion finalizada"
    elif command == "button2":
        detect_objects()
        return "Deteccion finalizada"
    elif command == "button3":
        copy_video_to_usb()
        return "Video copiado a USB"
    elif command == "button0":
        shutdown_raspberry_pi()
        return "Raspberry apagada"
    elif (command == "gps" and auxiliar == False):
	    return "GPS listo"
    else:
        print (f"Comando desconocido: {command}")

def start_server():
    #Starts the server to receive button commands.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print("Servidor iniciado y esperando conexiones...")
    gps_data()		#MODIFIED to run without GPS signal
    while True:
        client_socket, address = server_socket.accept()
        print(f"Conexion recibida de {address}")
        command = client_socket.recv(1024).decode('utf-8')
        if command:
            print(f"Comando recibido: {command}")
            response = process_command(command)
            if response:
                client_socket.sendall(response.encode('utf-8'))
        client_socket.close()

if __name__ == "__main__":
    stop_and_disable_serial_getty()  # Configure the necessary services
    start_server()  # Start the server