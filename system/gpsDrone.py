import gps
import time
from datetime import datetime

def get_gps_data():
    session = gps.gps(mode=gps.WATCH_ENABLE)
    with open("/home/drone/Desktop/tflite1/coordenadas.txt", "w") as file:
        start_time = datetime.now()
        iteration = 0  # Iteration counter to see progress
        try:
            while True:  # Infinite loop to continue receiving data
                print(f"Iteración {iteration}: esperando datos GPS...")

                # Get GPS data
                session.next()
                if session.fix.mode >= 2:  # Check that the GPS signal is fixed
                    latitude = session.fix.latitude
                    longitude = session.fix.longitude
                else:
                    # If there is no valid GPS data, use "nodata"
                    latitude = "nodata"
                    longitude = "nodata"

                elapsed_time = datetime.now() - start_time
                seconds = elapsed_time.total_seconds()

                # Format time
                formatted_time = f"{int(seconds // 3600):02}:{int(seconds % 3600 // 60):02}:{int(seconds % 60):02},{int((seconds % 1) * 1000):03d}"
                # Write to file and console
                line = f"{formatted_time}    {latitude}, {longitude}\n"
                file.write(line)
                file.flush()
                print(f"Escribiendo en coordenadas.txt: {line.strip()}")

                iteration += 1
                time.sleep(1)  # Wait a second before the next reading

        except Exception as e:
            print(f"Error en la función get_gps_data: {e}")
        finally:
            session.close()  # Close GPS session

if __name__ == "__main__":
    get_gps_data()
