import math

from staticmap import StaticMap, CircleMarker


def get_y1_y2_x1_x2(latitude, longitude, radius_km):
    # https://stackoverflow.com/a/27943/1034395
    # 1 deg = 111.32 km
    y1 = latitude + radius_km / 111.32
    y2 = latitude - radius_km / 111.32
    x1 = longitude - radius_km / (111.32 * math.cos(latitude * math.pi / 180))
    x2 = longitude + radius_km / (111.32 * math.cos(latitude * math.pi / 180))

    return y1, y2, x1, x2


def create_map(latitude, longitude, radius_km):
    y1, y2, x1, x2 = get_y1_y2_x1_x2(latitude, longitude, radius_km)

    width = 300

    m = StaticMap(width, width)
    m.add_marker(CircleMarker((x1, y1), None, 1))
    m.add_marker(CircleMarker((x2, y2), None, 1))

    image = m.render()
    image.save('map.png')
