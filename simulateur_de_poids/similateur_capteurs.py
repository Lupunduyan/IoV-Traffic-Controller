import requests
import time
import random

# Define the API endpoints for each sensor
api_endpoint_hx711 = "http://127.0.0.1:5000/send_hx711_data"
api_endpoint_fc51 = "http://127.0.0.1:5000/send_fc51_data"
api_endpoint_lm35 = "http://127.0.0.1:5000/send_lm35_data"
api_endpoint_tcs230 = "http://127.0.0.1:5000/send_tcs230_data"

# Define the sensor IDs
capteur_hx711_id = "capteur-12635"
capteur_fc51_id = "capteur-12636"
capteur_lm35_id = "capteur-12637"
capteur_tcs230_id = "capteur-12638"

# Function to send simulated data for all sensors
def send_sensor_data():
    while True:
        # HX711 (Weight) Data
        poids = random.randint(100, 1500)
        limit_ = 1020
        hx711_params = {
            "capteur": capteur_hx711_id,
            "status": "ok",
            "poids": poids,
            "limit_": limit_
        }

        # FC51 (Obstacle) Data
        obstacle_gauche = random.choice([0, 1])  # 0: no obstacle, 1: obstacle
        obstacle_droite = random.choice([0, 1])  # 0: no obstacle, 1: obstacle
        obstacle_devant = random.choice([0, 1])  # 0: no obstacle, 1: obstacle
        obstacle_deriere = random.choice([0, 1])  # 0: no obstacle, 1: obstacle
        fc51_params = {
            "capteur": capteur_fc51_id,
            "status": "ok",
            "obstacle_gauche": obstacle_gauche,
            "obstacle_droite": obstacle_droite,
            "obstacle_devant": obstacle_devant,
            "obstacle_deriere": obstacle_deriere
        }

        # LM35 (Temperature) Data
        temperature = random.uniform(15.0, 45.0)  # Simulated temperature range
        lm35_params = {
            "capteur": capteur_lm35_id,
            "status": "ok",
            "temperature": temperature
        }

        # TCS230 (Color Detection) Data
        red = random.randint(0, 1)
        green = 0 if red ==1 else 1
        blue = random.randint(0, 1)
        tcs230_params = {
            "capteur": capteur_tcs230_id,
            "status": "ok",
            "red": red,
            "green": green,
            "blue": blue
        }

        # Send data for each sensor to its respective API endpoint
        try:
            # Send HX711 data
            hx711_response = requests.get(api_endpoint_hx711, params=hx711_params)
            if hx711_response.status_code == 200:
                print(f"HX711: Successfully sent weight: {poids} kg")
            else:
                print(f"HX711: Failed to send data. Status code: {hx711_response.status_code}")

            # Send FC51 data
            fc51_response = requests.get(api_endpoint_fc51, params=fc51_params)
            if fc51_response.status_code == 200:
                obstacle_msg = ""

                if obstacle_gauche == 1:
                    obstacle_msg += "Obstacle détecté à gauche. \n"

                if obstacle_droite == 1:
                    obstacle_msg += "Obstacle détecté à droite. \n"

                if obstacle_devant == 1:
                    obstacle_msg += "Obstacle détecté devant. \n"

                if obstacle_deriere == 1:
                    obstacle_msg += "Obstacle détecté derrière. \n"

                # Si aucun obstacle n'est détecté
                if not obstacle_msg:
                    obstacle_msg = "Aucun obstacle détecté."

                print(f"FC51: Successfully sent obstacle status: {obstacle_msg}")
            else:
                print(f"FC51: Failed to send data. Status code: {fc51_response.status_code}")

            # Send LM35 data
            lm35_response = requests.get(api_endpoint_lm35, params=lm35_params)
            if lm35_response.status_code == 200:
                print(f"LM35: Successfully sent temperature: {temperature:.2f} °C")
            else:
                print(f"LM35: Failed to send data. Status code: {lm35_response.status_code}")

            # Send TCS230 data
            tcs230_response = requests.get(api_endpoint_tcs230, params=tcs230_params)
            if tcs230_response.status_code == 200:
                print(f"TCS230: Successfully sent color data - Red: {red}, Green: {green}, Blue: {blue}")
            else:
                print(f"TCS230: Failed to send data. Status code: {tcs230_response.status_code}")

        except requests.exceptions.RequestException as e:
            print(f"Error while sending request: {e}")

        # Wait for 2 seconds before sending the next update
        time.sleep(2)

# Start the simulation
if __name__ == "__main__":
    send_sensor_data()
