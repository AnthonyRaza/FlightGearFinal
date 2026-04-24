import socket
import time
import psycopg2
import math

def get_positions():
    s = socket.socket()
    s.connect(('127.0.0.1', 5001))
    s.send(b'list\r\n')
    data = s.recv(16384).decode()
    s.close()
    players = []
    for line in data.split('\n'):
        if '@LOCAL:' in line:
            parts = line.split()
            callsign = parts[0].split('@')[0]
            lat = float(parts[4])
            lon = float(parts[5])
            heading = math.degrees(float(parts[7])) % 360
            players.append((callsign, lat, lon, heading))
    return players

conn = psycopg2.connect(dbname="flightgear", user="fguser", password="fgpassword123", host="localhost")
print("Tracker démarré !")

while True:
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM aircraft_position WHERE updated_at < NOW() - INTERVAL '10 seconds'")
        players = get_positions()
        for callsign, lat, lon, heading in players:
            cursor.execute("""
                INSERT INTO aircraft_position (callsign, latitude, longitude, heading, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (callsign) DO UPDATE SET
                latitude = %s, longitude = %s, heading = %s, updated_at = NOW()
            """, (callsign, lat, lon, heading, lat, lon, heading))
        conn.commit()
        print(f"{len(players)} joueurs trackés")
    except Exception as e:
        print(f"Erreur : {e}")
        try:
            conn.rollback()
        except:
            conn = psycopg2.connect(dbname="flightgear", user="fguser", password="fgpassword123", host="localhost")
