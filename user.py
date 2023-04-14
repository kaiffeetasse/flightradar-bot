class User:
    def __init__(self, telegram_id, latitude, longitude, radius_km):
        self.telegram_id = telegram_id
        self.latitude = latitude
        self.longitude = longitude
        self.radius_km = radius_km

    def __str__(self):
        return f"User {self.telegram_id} at ({self.latitude}, {self.longitude}) with radius {self.radius_km}km"
