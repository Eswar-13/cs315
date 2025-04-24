import json
import random
from datetime import datetime, timedelta

def generate_random_stations(num_stations=5):
    stations = [
        {"model": "search.station", "pk": f"STN_{i}", "fields": {
            "state": f"State_{i}",
            "latitude": round(random.uniform(20.0, 30.0), 4),
            "longitude": round(random.uniform(70.0, 80.0), 4)
        }} for i in range(1, num_stations + 1)
    ]
    return stations

def generate_random_trains(num_trains=3):
    trains = [
        {"model": "search.train", "pk": i, "fields": {
            "number": f"{random.randint(10000, 99999)}",
            "origin_date": "2025-04-25",
            "end_date": "2025-04-25",
            "seats_available": random.randint(100, 300)
        }} for i in range(1, num_trains + 1)
    ]
    return trains

def generate_random_schedule(trains, stations):
    schedule = []
    pk_counter = 1
    for train in trains:
        route = random.sample(stations, k=random.randint(2, len(stations)))
        stop_order = 1
        current_time = datetime.strptime("06:00", "%H:%M")
        for station in route:
            arrival_time = current_time if stop_order > 1 else None
            departure_time = current_time + timedelta(minutes=random.randint(10, 60)) if stop_order < len(route) else None
            schedule.append({
                "model": "search.schedule",
                "pk": pk_counter,
                "fields": {
                    "train": train["pk"],
                    "station": station["pk"],
                    "arrival_time": arrival_time.strftime("%Y-%m-%dT%H:%M:%S") if arrival_time else None,
                    "departure_time": departure_time.strftime("%Y-%m-%dT%H:%M:%S") if departure_time else None,
                    "distance_from_src": random.randint(0, 1500),
                    "stop_order": stop_order
                }
            })
            pk_counter += 1
            stop_order += 1
            current_time = departure_time if departure_time else current_time
    return schedule

def generate_test_data():
    stations = generate_random_stations()
    trains = generate_random_trains()
    schedule = generate_random_schedule(trains, stations)
    return stations + trains + schedule

if __name__ == "__main__":
    test_data = generate_test_data()
    with open("test/test.json", "w") as f:
        json.dump(test_data, f, indent=4)
    print("Generated test data saved to test.json")