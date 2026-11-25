#!/usr/bin/env python3
"""
Skrypt tworzy bazę danych "F1" w MongoDB z 3 kolekcjami zawierającymi
dane zagnieżdżone (embedded documents), na podstawie plików CSV (sezon 2023):

  1. races        - wyścig -> zagnieżdżony tor (circuit)
                    -> tablica wyników (results[]), a w każdym wyniku
                       zagnieżdżeni kierowca (driver) i konstruktor (constructor)
  2. drivers      - kierowca -> tablica występów (race_results[])
  3. constructors - konstruktor -> tablica kierowców (drivers[])
                    -> tablica wyników per wyścig (race_results[])

Uruchomienie:  python3 create_f1_db.py
Wymaga:       pip install pymongo   oraz działającego mongod na localhost:27017
"""

import csv
import os
from collections import defaultdict

from pymongo import MongoClient

# ---------------------------------------------------------------- konfiguracja
MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = "F1"
SEASON = None                      # None = wszystkie sezony, lub np. 2023
DATA_DIR = os.path.dirname(os.path.abspath(__file__))


# ------------------------------------------------------------------ pomocnicze
def load_csv(filename):
    """Wczytuje plik CSV do listy słowników; wartość \\N zamienia na None."""
    path = os.path.join(DATA_DIR, filename)
    with open(path, newline="", encoding="utf-8") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append({k: (None if v in ("\\N", "") else v) for k, v in row.items()})
        return rows


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ------------------------------------------------------------------- wczytywanie
def load_data():
    all_races = load_csv("races.csv")
    races = all_races if SEASON is None else [
        r for r in all_races if to_int(r["year"]) == SEASON
    ]
    race_ids = {to_int(r["raceId"]) for r in races}

    results = [r for r in load_csv("results.csv") if to_int(r["raceId"]) in race_ids]
    drivers = load_csv("drivers.csv")
    constructors = load_csv("constructors.csv")
    circuits = load_csv("circuits.csv")

    return races, results, drivers, constructors, circuits


# ------------------------------------------------------------ budowa dokumentów
def build_races(races, results, drivers, constructors, circuits):
    """Kolekcja `races`: dokument wyścigu z zagnieżdżonym torem i wynikami."""
    driver_by_id = {to_int(d["driverId"]): d for d in drivers}
    constr_by_id = {to_int(c["constructorId"]): c for c in constructors}
    circuit_by_id = {to_int(c["circuitId"]): c for c in circuits}
    results_by_race = defaultdict(list)
    for r in results:
        results_by_race[to_int(r["raceId"])].append(r)

    docs = []
    for race in sorted(races, key=lambda r: to_int(r["round"])):
        rid = to_int(race["raceId"])
        circuit = circuit_by_id.get(to_int(race["circuitId"]), {})

        embedded_results = []
        for res in sorted(results_by_race.get(rid, []),
                          key=lambda r: to_int(r["positionOrder"]) or 999):
            drv = driver_by_id.get(to_int(res["driverId"]), {})
            con = constr_by_id.get(to_int(res["constructorId"]), {})
            embedded_results.append({
                "resultId": to_int(res["resultId"]),
                "grid": to_int(res["grid"]),
                "position": to_int(res["position"]),
                "positionText": res["positionText"],
                "points": to_float(res["points"]),
                "laps": to_int(res["laps"]),
                "time": res["time"],
                "fastestLap": {
                    "lap": to_int(res["fastestLap"]),
                    "time": res["fastestLapTime"],
                    "speedKmh": to_float(res["fastestLapSpeed"]),
                },
                # --- dane zagnieżdżone: kierowca i konstruktor w wyniku ---
                "driver": {
                    "driverId": to_int(drv.get("driverId")),
                    "code": drv.get("code"),
                    "forename": drv.get("forename"),
                    "surname": drv.get("surname"),
                    "dob": drv.get("dob"),
                    "nationality": drv.get("nationality"),
                },
                "constructor": {
                    "constructorId": to_int(con.get("constructorId")),
                    "name": con.get("name"),
                    "nationality": con.get("nationality"),
                },
            })

        docs.append({
            "raceId": rid,
            "year": to_int(race["year"]),
            "round": to_int(race["round"]),
            "name": race["name"],
            "date": race["date"],
            "time": race["time"],
            # --- dane zagnieżdżone: tor ---
            "circuit": {
                "circuitId": to_int(circuit.get("circuitId")),
                "name": circuit.get("name"),
                "location": circuit.get("location"),
                "country": circuit.get("country"),
                "lat": to_float(circuit.get("lat")),
                "lng": to_float(circuit.get("lng")),
            },
            # --- dane zagnieżdżone: pełna lista wyników wyścigu ---
            "results": embedded_results,
        })
    return docs


def build_drivers(races, results, constructors):
    """Kolekcja `drivers`: kierowca z zagnieżdżoną listą jego występów."""
    race_by_id = {to_int(r["raceId"]): r for r in races}
    constr_by_id = {to_int(c["constructorId"]): c for c in constructors}
    results_by_driver = defaultdict(list)
    for res in results:
        results_by_driver[to_int(res["driverId"])].append(res)

    docs = []
    for drv in load_csv("drivers.csv"):
        did = to_int(drv["driverId"])
        entries = []
        for res in results_by_driver.get(did, []):
            race = race_by_id.get(to_int(res["raceId"]), {})
            con = constr_by_id.get(to_int(res["constructorId"]), {})
            entries.append({
                "raceId": to_int(res["raceId"]),
                "raceName": race.get("name"),
                "date": race.get("date"),
                "round": to_int(race.get("round")),
                "constructor": con.get("name"),
                "grid": to_int(res["grid"]),
                "position": to_int(res["position"]),
                "points": to_float(res["points"]),
                "fastestLapTime": res["fastestLapTime"],
            })
        entries.sort(key=lambda e: (e["date"] or ""))
        if not entries:          # kierowca bez wyników w tym sezonie -> pomiń
            continue
        docs.append({
            "driverId": did,
            "driverRef": drv.get("driverRef"),
            "code": drv.get("code"),
            "forename": drv.get("forename"),
            "surname": drv.get("surname"),
            "dob": drv.get("dob"),
            "nationality": drv.get("nationality"),
            "racesCount": len(entries),
            # --- dane zagnieżdżone: historia występów kierowcy ---
            "raceResults": entries,
        })
    return docs


def build_constructors(races, results, drivers):
    """Kolekcja `constructors`: konstruktor z kierowcami i wynikami per wyścig."""
    race_by_id = {to_int(r["raceId"]): r for r in races}
    driver_by_id = {to_int(d["driverId"]): d for d in drivers}
    by_constructor = defaultdict(lambda: {"drivers": {}, "races": defaultdict(list)})

    for res in results:
        cid = to_int(res["constructorId"])
        did = to_int(res["driverId"])
        rid = to_int(res["raceId"])
        drv = driver_by_id.get(did, {})
        by_constructor[cid]["drivers"][did] = {
            "driverId": did,
            "code": drv.get("code"),
            "forename": drv.get("forename"),
            "surname": drv.get("surname"),
            "nationality": drv.get("nationality"),
        }
        by_constructor[cid]["races"][rid].append({
            "driverId": did,
            "driverCode": drv.get("code"),
            "grid": to_int(res["grid"]),
            "position": to_int(res["position"]),
            "points": to_float(res["points"]),
        })

    docs = []
    for con in load_csv("constructors.csv"):
        cid = to_int(con["constructorId"])
        data = by_constructor.get(cid)
        if not data:
            continue
        race_entries = []
        for rid, res_list in data["races"].items():
            race = race_by_id.get(rid, {})
            res_list.sort(key=lambda r: r["position"] or 999)
            race_entries.append({
                "raceId": rid,
                "raceName": race.get("name"),
                "date": race.get("date"),
                # --- dane zagnieżdżone: wyniki kierowców tego zespołu ---
                "results": res_list,
            })
        race_entries.sort(key=lambda e: e["date"] or "")
        docs.append({
            "constructorId": cid,
            "constructorRef": con.get("constructorRef"),
            "name": con.get("name"),
            "nationality": con.get("nationality"),
            # --- dane zagnieżdżone: kierowcy zespołu ---
            "drivers": sorted(data["drivers"].values(),
                              key=lambda d: d["surname"] or ""),
            # --- dane zagnieżdżone: wyniki zespołu w każdym wyścigu ---
            "raceResults": race_entries,
        })
    return docs


def bulk_rows(filename, race_year, transform):
    """Generator czytający duży CSV porcjami (bez trzymania wszystkiego w pamięci).
    Do każdego dokumentu dokłada pole `year` (z mapy raceId -> rok wyścigu)."""
    path = os.path.join(DATA_DIR, filename)
    batch = []
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            d = {k: (None if v in ("\\N", "") else v) for k, v in row.items()}
            d["year"] = race_year.get(to_int(d.get("raceId")))
            batch.append(transform(d))
            if len(batch) >= 10000:
                yield batch
                batch = []
    if batch:
        yield batch


# ------------------------------------------------------------------------ main
def main():
    print(f"Łączenie z MongoDB: {MONGO_URI} ...")
    client = MongoClient(MONGO_URI)
    client.admin.command("ping")

    db = client[DB_NAME]
    client.drop_database(DB_NAME)

    races, results, drivers, constructors, circuits = load_data()

    races_docs = build_races(races, results, drivers, constructors, circuits)
    drivers_docs = build_drivers(races, results, constructors)
    constructors_docs = build_constructors(races, results, drivers)

    db.races.insert_many(races_docs)
    db.drivers.insert_many(drivers_docs)
    db.constructors.insert_many(constructors_docs)

    db.races.create_index("raceId", unique=True)
    db.drivers.create_index("driverId", unique=True)
    db.constructors.create_index("constructorId", unique=True)

    race_year = {to_int(r["raceId"]): to_int(r["year"]) for r in races}

    for batch in bulk_rows("pit_stops.csv", race_year, lambda d: {
            "raceId": to_int(d["raceId"]), "driverId": to_int(d["driverId"]),
            "year": d["year"], "stop": to_int(d["stop"]), "lap": to_int(d["lap"]),
            "time": d["time"], "duration": d["duration"],
            "milliseconds": to_int(d["milliseconds"])}):
        db.pitStops.insert_many(batch)
    db.pitStops.create_index([("raceId", 1), ("driverId", 1)])

    for batch in bulk_rows("lap_times.csv", race_year, lambda d: {
            "raceId": to_int(d["raceId"]), "driverId": to_int(d["driverId"]),
            "year": d["year"], "lap": to_int(d["lap"]),
            "position": to_int(d["position"]), "time": d["time"],
            "milliseconds": to_int(d["milliseconds"])}):
        db.lapTimes.insert_many(batch)
    db.lapTimes.create_index("driverId")
    db.lapTimes.create_index("raceId")

    print("\nGotowe! Podsumowanie bazy 'F1':")
    for name in ("races", "drivers", "constructors", "pitStops", "lapTimes"):
        coll = db[name]
        sample = coll.find_one()
        print(f"  - {name}: {coll.count_documents({})} dokumentów")
        if sample:
            nested = [k for k, v in sample.items()
                      if isinstance(v, (list, dict)) and k != "_id"]
            print(f"    pola zagnieżdżone: {', '.join(nested)}")

    print("\nPrzykład dokumentu z kolekcji 'races' (skrócony):")
    import json
    ex = db.races.find_one({}, {"results": {"$slice": 2}})
    print(json.dumps(ex, indent=2, ensure_ascii=False, default=str)[:1500])

    client.close()


if __name__ == "__main__":
    main()
