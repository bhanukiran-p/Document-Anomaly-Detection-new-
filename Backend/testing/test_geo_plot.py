"""
Test script to verify geo plot coordinate generation
"""
import sys
sys.path.insert(0, 'c:\\Users\\bhanukaranP\\Desktop\\DAD New\\Backend')

from real_time.insights_generator import _pseudo_coordinates

# Test common cities
test_cities = [
    ('New York', 'USA'),
    ('New York', 'United States'),
    ('London', 'UK'),
    ('London', 'United Kingdom'),
    ('Tokyo', 'Japan'),
    ('Paris', 'France'),
    ('Singapore', 'Singapore'),
    ('Sydney', 'Australia'),
    ('Mumbai', 'India'),
    ('Dubai', 'UAE'),
    ('Hong Kong', 'China'),
    ('Toronto', 'Canada'),
    ('Unknown City', 'Unknown Country'),
    ('Random City', 'Random Country'),
]

print("=" * 80)
print("GEO PLOT COORDINATE TEST")
print("=" * 80)
print()

for city, country in test_cities:
    lat, lng = _pseudo_coordinates(city, country)
    valid = -90 <= lat <= 90 and -180 <= lng <= 180
    status = "[VALID]" if valid else "[INVALID]"
    print(f"{status} | {city:25s} | {country:20s} | Lat: {lat:8.2f}, Lng: {lng:8.2f}")

print()
print("=" * 80)
print("Test complete!")
print("=" * 80)
