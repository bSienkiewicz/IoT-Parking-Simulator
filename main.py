import random
import time
import datetime
import numpy as np

total_parking_spots = 300
entrance_spots = [100,200,300]
cars_spawn_min, cars_spawn_max = 0, 0
car_park_time_min, car_park_time_max = 15, 140
sim_time = "9:49AM"
hour_ranges = {
    range(0, 7): (0, 0),
    range(7, 9): (0, 3),
    range(9, 13): (0, 2),
    range(13, 15): (0, 3),
    range(15, 18): (2, 6),
    range(18, 20): (0, 3),
    range(20, 23): (0, 2),
    range(23, 25): (0, 0)
}
car_brands = ["BMW", "Peugeot", "Toyota", "Ford", "Volkswagen", "Opel", "Citroen", "Seat", "Renault", "Audi", "Honda", "Nissan", "Mercedes-Benz", 
              "Hyundai", "Kia", "Mazda", "Lexus", "Jeep", "Volvo", "Fiat", "Mitsubishi", "Jeep", "Mini", "Dodge", "Cadillac", "Chrysler", "Dacia", 
              "Suzuki", "Alfa Romeo", "Rolls-Royce", "Maserati", "Porsche", "Volvo", "Jaguar", "Bentley", "Ferrari", "Lamborghini", "Bugatti"]
car_colors = ["Red", "Blue", "Green", "Yellow", "Black", "White", "Silver", "Gray", "Brown", "Orange", "Purple"]
brand_luxury_ranges = {
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
    "Cadillac" : (70, 90),
}

class Car:
    def __init__(self, brand, color, luxury, exit_time):
        self.brand = brand
        self.color = color
        self.luxury = luxury
        self.exit_time = exit_time
        self.is_good_parking = np.random.choice([True, False], p=[0.8, 0.2])
        
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
      
      self.spots[spot] = car
      self.popularity[spot] += 1
      print(f"\033[92m→ {car} parked at spot {spot}\033[0m")
        
    def remove(self, spot):
        car = self.spots[spot]
        self.spots[spot] = None
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
                cars_to_remove.append(i)
            elif car is not None:
                car.exit_time -= 1
        for i in reversed(cars_to_remove):
            self.remove(i)
            
    def __repr__(self):
        return f"Parking lot with {self.num_spots} spots, {sum(spot is not None for spot in self.spots)} cars parked"

# Create parking lot
parking_lot = ParkingLot(total_parking_spots)

# Simulate parking for 600 ticks (each tick represents 1 second)
tick_count = 0
while True:
    
    print(f"\n{sim_time} {'-' * 48}")
    # Increment time by 1 minute (1 second of simulation time)
    sim_time = (datetime.datetime.strptime(sim_time, "%I:%M%p") + datetime.timedelta(minutes=1)).strftime("%I:%M%p") 
    
    # Determine rush hours and adjust car spawn rate accordingly
    for hour_range, (cars_spawn_min, cars_spawn_max) in hour_ranges.items():
        if datetime.datetime.strptime(sim_time, "%I:%M%p").hour in hour_range:
            break
        
    # Allow cars to enter the parking lot
    num_spots_to_fill = min(random.randint(cars_spawn_min, cars_spawn_max), parking_lot.num_spots - sum(spot is not None for spot in parking_lot.spots))
    for i in range(num_spots_to_fill):
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

    # Print status of parking lot every 10 seconds
    if tick_count % 10 == 0:
      occupancy = ["\033[91m-\033[0m" if spot is None else "\033[92mX\033[0m" for spot in parking_lot.spots]
      for i in range(0, len(occupancy), 100):
          print("".join(occupancy[i:i+100]))
      print(parking_lot)
      # print(f"Popularity: {parking_lot.popularity}")
      print()

    # Decrement exit time and tick counter
    parking_lot.tick()
    tick_count += 1
    time.sleep(1)