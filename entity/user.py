class User:
    def __init__(self, telegram_id, latitude, longitude, radius_km, altitude_min_m, altitude_max_m):
        self.telegram_id = telegram_id
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km
        self.altitude_min_m = altitude_min_m
        self.altitude_max_m = altitude_max_m

    def __str__(self):
        return f"User {self.telegram_id} at ({self.latitude}, {self.longitude}) " \
               f"with radius {self.radius_km}km and altitude {self.altitude_min_m}m - {self.altitude_max_m}m"
