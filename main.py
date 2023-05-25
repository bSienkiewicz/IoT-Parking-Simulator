import random
import time
import datetime
from datetime import datetime as dt
import numpy as np
import json
import pytz
import requests
import paho.mqtt.client as mqtt

mqtt_endpoint = "iot.imei.uz.zgora.pl"
mqtt_port = 1883
mqtt_client_id = "030201zul"
mqtt_topic = "v1/devices/zulqtt"
mqtt_publish_delay = 5 # Co ile sekund publikować dane do brokera

total_parking_spots = 200 # Liczba miejsc parkingowych
entrance_spots = [0, 100, 200] # Miejsca interesujące dla klientów
cars_spawn_min, cars_spawn_max = 0, 0 
car_park_time_min, car_park_time_max = 15, 140 # Czas parkowania w minutach

timezone = pytz.timezone('Europe/Warsaw')

hour_ranges = {
    range(0, 25): (0, 1)
}
car_brands = ["BMW", "Peugeot", "Toyota", "Ford", "Volkswagen", "Opel", "Citroen", "Seat", "Renault", "Audi", "Honda",
              "Nissan", "Mercedes-Benz",
              "Hyundai", "Kia", "Mazda", "Lexus", "Jeep", "Volvo", "Fiat", "Mitsubishi", "Jeep", "Mini", "Dodge",
              "Cadillac", "Chrysler", "Dacia",
              "Suzuki", "Alfa Romeo", "Rolls-Royce", "Maserati", "Porsche", "Volvo", "Jaguar", "Bentley", "Ferrari",
              "Lamborghini", "Bugatti"]
car_colors = ["Red", "Blue", "Green", "Yellow", "Black", "White", "Silver", "Gray", "Brown", "Orange", "Purple"]
brand_luxury_ranges = { # Zakresy luksusowości dla poszczególnych marek
    "BMW": (70, 100),
    "Mercedes-Benz": (80, 100),
    "Audi": (70, 90),
    "Lexus": (75, 95),
    "Rolls-Royce": (90, 100),
    "Maserati": (80, 95),
    "Porsche": (75, 90),
    "Jaguar": (70, 85),
    "Bentley": (85, 100),
    "Ferrari": (90, 100),
    "Lamborghini": (90, 100),
    "Bugatti": (95, 100),
    "Cadillac": (70, 90),
}

cars_arrived = []
cars_removed = []

class Car:
    def __init__(self, brand, color, luxury, exit_time):
        self.brand = brand
        self.color = color
        self.luxury = luxury
        self.exit_time = exit_time
        self.time_desired = exit_time
        self.is_good_parking = np.random.choice([1,0], p=[0.8, 0.2])

    def __repr__(self):
        return f"{self.color} {self.brand} ({self.luxury}% luxury, {self.exit_time} minutes left, {'good' if self.is_good_parking else 'bad'} parking)"

class ParkingLot:
    def __init__(self, num_spots: int) -> None:
        self.num_spots = num_spots
        self.spots = [None] * num_spots
        self.popularity = [0] * num_spots
        self.entrance_spots = entrance_spots

    def is_full(self):
        return all(spot is not None for spot in self.spots)

    def park(self, car):
        if self.is_full():
            raise Exception("Parking lot is full")

        # Calculate distance of each spot from entrance
        distances = [abs(i - self.entrance_spots[0]) for i in range(len(self.spots))]
        for entrance_spot in self.entrance_spots[1:]:
            distances = [min(abs(i - entrance_spot), d) for i, d in enumerate(distances)]

        # Calculate weights for each spot based on distance and floor number
        weights = [1 / (d + 1) * (1 / (spot // 100 + 1)) for spot, d in zip(range(len(self.spots)), distances)]

        # Select a random spot with weighted probability, ensuring it is not already occupied
        available_spots = [i for i, spot in enumerate(self.spots) if spot is None]
        if not available_spots:
            raise Exception("No available spots")
        total_weight = sum(weights[i] for i in available_spots)
        selection = random.uniform(0, total_weight)
        weight_sum = 0
        for i in available_spots:
            weight_sum += weights[i]
            if weight_sum >= selection:
                spot = i
                break

        self.spots[spot] = car # Park car at spot
        self.popularity[spot] += 1 # Increase popularity of spot 
        cars_arrived.append(car) # Add car to arrived cars list
        print(f"\033[92m→ {car} parked at spot {spot}\033[0m")

    def remove(self, spot):
        car = self.spots[spot] # Get car from spot
        self.spots[spot] = None # Remove car from spot
        cars_removed.append(car) # Add car to removed cars list
        print(f"\033[91m← {car} removed from spot {spot}\033[0m")
        return car

    def is_spot_occupied(self, spot):
        return self.spots[spot] is not None

    def get_occupied_spots(self):
        return [self.is_spot_occupied(spot) for spot in range(self.num_spots)]

    def tick(self):
        cars_to_remove = [] 
        for i, car in enumerate(self.spots):
            if car is not None and car.exit_time <= 0:
                cars_to_remove.append(i) # Add car to list of cars to remove if it has no time left
            elif car is not None:
                car.exit_time -= 1 # Decrease time left for car to leave
        for i in reversed(cars_to_remove):
            self.remove(i) # Remove cars from list of cars to remove

    def __repr__(self):
        return f"Parking lot with {self.num_spots} spots, {sum(spot is not None for spot in self.spots)} cars parked"


# Create parking lot
parking_lot = ParkingLot(total_parking_spots)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    client.publish(mqtt_topic, json.dumps({'time_connected': str(dt.now())}), 0, True);

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

client = mqtt.Client()
client.username_pw_set("030201zul")
client.on_connect = on_connect
client.on_message = on_message

client.connect(mqtt_endpoint, mqtt_port, 60)

# send post request to http://iot.imei.uz.zgora.pl/api/v1/030201zul/telemetry with json data of "money_time" : 0
requests.post("http://iot.imei.uz.zgora.pl/api/v1/030201zul/telemetry", json={"money_total": 0})

previous_time = datetime.datetime.now().strftime("%I:%M%p")
previous_time = datetime.datetime.strptime(previous_time, "%I:%M%p") - datetime.timedelta(minutes=1)

client.loop_start()

previous_time = ""

while True:
    current_time = datetime.datetime.now(timezone).strftime("%H:%M:%S")
    if current_time != previous_time:  # Check if the time has changed
        print(current_time)
        previous_time = current_time
        # every 10 seconds check if there are any cars to remove and add new cars
        if int(current_time.split(":")[2]) % 10 == 0:
            # Allow cars to enter the parking lot based on the hour range
            hour = datetime.datetime.now(timezone).hour
            for hour_range, (cars_spawn_min, cars_spawn_max) in hour_ranges.items():
                if hour in hour_range:
                    num_spots_to_fill = min(random.randint(cars_spawn_min, cars_spawn_max),
                                            parking_lot.num_spots - sum(spot is not None for spot in parking_lot.spots))
                    for i in range(num_spots_to_fill):
                        # Generate cars and park them
                        brand = random.choice(car_brands)
                        brand_luxury_range = brand_luxury_ranges.get(brand, (20, 100))
                        exit_time = random.randint(car_park_time_min, car_park_time_max)
                        color = random.choice(car_colors)

                        # Set luxury based on brand
                        if brand in brand_luxury_ranges:
                            luxury_min, luxury_max = brand_luxury_ranges[brand]
                            luxury = random.randint(luxury_min, luxury_max)
                        else:
                            # For non-luxury brands, set luxury randomly between 0 and 50
                            luxury = random.randint(0, 50)

                        car = Car(brand, color, luxury, exit_time)
                        try:
                            parking_lot.park(car)
                        except:
                            print("Parking lot is full, car couldn't be parked")
                    break

            # Publish MQTT message every minute
            json_parking = {
                "parked_cars": [],
                "popularity": parking_lot.popularity,
                "cars_arrived": [],
                "cars_removed": [],
                "time": str(current_time)
            }
            for spot in range(len(parking_lot.spots)):
                # Gather information about parked cars
                if parking_lot.spots[spot] is not None:
                    json_parking['parked_cars'].append({
                        "brand": parking_lot.spots[spot].brand,
                        "color": parking_lot.spots[spot].color,
                        "luxury": int(parking_lot.spots[spot].luxury),
                        "spot": int(spot),
                        "is_good_parking": bool(parking_lot.spots[spot].is_good_parking),
                        "exit_time": int(parking_lot.spots[spot].exit_time),
                        "time_desired": int(parking_lot.spots[spot].time_desired)
                    })
                    json_parking['cars_arrived'] = [{"brand": car.brand, "color": car.color, "luxury": car.luxury, "spot": int(spot), "spent_time" : int(car.time_desired)} for car in cars_arrived]
                    json_parking['cars_removed'] = [{"brand": car.brand, "color": car.color, "luxury": car.luxury, "spot": int(spot), "spent_time" : int(car.time_desired)} for car in cars_removed]
            client.publish(mqtt_topic, json.dumps(json_parking), 0, True)
            cars_arrived = []
            cars_removed = []
    # every minute tick the parking lot
    if int(current_time.split(":")[2]) % 60 == 0:
        parking_lot.tick()
        time.sleep(1)