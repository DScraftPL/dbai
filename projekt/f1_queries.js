// ============================================================================
// Zapytania MongoDB do bazy "F1" — uruchomienie:
//   mongosh F1 f1_queries.js
// lub pojedynczo:  mongosh F1 --eval "load('f1_queries.js'); q1()"
//
// Struktura bazy:
//   races        { raceId, year, round, name, date, circuit: {...},
//                  results: [ { position, points, fastestLap: {time,...},
//                               driver: {...}, constructor: {...} } ] }
//   drivers      { driverId, code, forename, surname, raceResults: [...] }
//   constructors { constructorId, name, drivers: [...], raceResults: [...] }
//   pitStops     { raceId, driverId, year, stop, lap, duration, milliseconds }
//   lapTimes     { raceId, driverId, year, lap, position, time, milliseconds }
// ============================================================================

// ---------------------------------------------------------------------------
// Q1: Którzy kierowcy ścigali się w poszczególnych latach?
// ---------------------------------------------------------------------------
function q1() {
  return db.races.aggregate([
    { $unwind: "$results" },
    // code może być null (starsi kierowcy) -> fallback na imię + nazwisko
    { $addFields: { kierowca: { $ifNull: ["$results.driver.code",
        { $concat: ["$results.driver.forename", " ", "$results.driver.surname"] }] } } },
    { $group: {
        _id: "$year",
        kierowcy: { $addToSet: "$kierowca" },
        kierowcyId: { $addToSet: "$results.driver.driverId" }
    }},
    { $project: {
        _id: 0,
        rok: "$_id",
        liczbaKierowcow: { $size: "$kierowcyId" },
        kierowcy: { $sortArray: { input: "$kierowcy", sortBy: 1 } }
    }},
    { $sort: { rok: 1 } }
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Q2: Którzy twórcy pojazdów (konstruktorzy) osiągali najlepsze wyniki?
//     (suma punktów, zwycięstwa, podia — TOP 10)
// ---------------------------------------------------------------------------
function q2() {
  return db.races.aggregate([
    { $unwind: "$results" },
    { $group: {
        _id: "$results.constructor.name",
        punkty:     { $sum: "$results.points" },
        zwyciestwa: { $sum: { $cond: [{ $eq: ["$results.position", 1] }, 1, 0] } },
        podia:      { $sum: { $cond: [{ $lte: ["$results.position", 3] }, 1, 0] } },
        wyscigi:    { $sum: 1 }
    }},
    { $project: {
        _id: 0,
        konstruktor: "$_id",
        punkty: 1, zwyciestwa: 1, podia: 1, wyscigi: 1,
        punktyNaWyscig: { $round: [{ $divide: ["$punkty", "$wyscigi"] }, 2] }
    }},
    { $sort: { punkty: -1 } },
    { $limit: 10 }
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Q3a: Czy ilość pit stopów wpływała na wynik kierowcy w wyścigu?
//      Średnia pozycja końcowa i punkty w zależności od liczby pit stopów.
// ---------------------------------------------------------------------------
function q3a() {
  return db.pitStops.aggregate([
    // liczba pit stopów kierowcy w danym wyścigu
    { $group: { _id: { raceId: "$raceId", driverId: "$driverId" }, pitStopy: { $sum: 1 } } },
    // dobierz wynik tego kierowcy z wyścigu (z zagnieżdżonych results)
    { $lookup: { from: "races", localField: "_id.raceId", foreignField: "raceId", as: "wyścig" } },
    { $unwind: "$wyścig" },
    { $unwind: "$wyścig.results" },
    { $match: { $expr: { $eq: ["$wyścig.results.driver.driverId", "$_id.driverId"] } } },
    // agregacja po liczbie pit stopów
    { $group: {
        _id: "$pitStopy",
        sredniaPozycja:  { $avg: "$wyścig.results.position" },
        sredniePunkty:   { $avg: "$wyścig.results.points" },
        liczbaPrzypadkow: { $sum: 1 }
    }},
    { $project: {
        _id: 0,
        liczbaPitStopow: "$_id",
        sredniaPozycja: { $round: ["$sredniaPozycja", 2] },
        sredniePunkty:  { $round: ["$sredniePunkty", 2] },
        liczbaPrzypadkow: 1
    }},
    { $sort: { liczbaPitStopow: 1 } }
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Q3b: To samo w przekroju pojedynczych kierowców — kto miał najwięcej
//      pit stopów i jaką średnią pozycję osiągał (TOP 15 najlepszych).
// ---------------------------------------------------------------------------
function q3b() {
  return db.pitStops.aggregate([
    { $group: { _id: { raceId: "$raceId", driverId: "$driverId" }, pitStopy: { $sum: 1 } } },
    { $lookup: { from: "races", localField: "_id.raceId", foreignField: "raceId", as: "wyścig" } },
    { $unwind: "$wyścig" },
    { $unwind: "$wyścig.results" },
    { $match: { $expr: { $eq: ["$wyścig.results.driver.driverId", "$_id.driverId"] } } },
    // odrzuć wyniki bez pozycji (np. dyskwalifikacje / niezaklasyfikowani)
    { $match: { "wyścig.results.position": { $ne: null } } },
    // agregacja po kierowcy
    { $group: {
        _id: "$_id.driverId",
        sredniaPitStopow: { $avg: "$pitStopy" },
        sredniaPozycja:   { $avg: "$wyścig.results.position" },
        wyscigi:          { $sum: 1 }
    }},
    { $lookup: { from: "drivers", localField: "_id", foreignField: "driverId", as: "kierowca" } },
    { $project: {
        _id: 0,
        kierowca: { $concat: [
            { $arrayElemAt: ["$kierowca.forename", 0] }, " ",
            { $arrayElemAt: ["$kierowca.surname", 0] } ] },
        sredniaPitStopow: { $round: ["$sredniaPitStopow", 2] },
        sredniaPozycja:   { $round: ["$sredniaPozycja", 2] },
        wyscigi: 1
    }},
    { $sort: { sredniaPozycja: 1 } },
    { $limit: 15 }
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Q4: Jakie były najlepsze czasy (najszybsze okrążenia) w poszczególnych
//     dekadach? — z kolekcji lapTimes (pole milliseconds).
// ---------------------------------------------------------------------------
function q4() {
  return db.lapTimes.aggregate([
    { $match: { milliseconds: { $gt: 0 } } },
    { $addFields: { dekada: { $multiply: [{ $floor: { $divide: ["$year", 10] } }, 10] } } },
    { $sort: { milliseconds: 1 } },           // od najszybszego okrążenia
    { $group: {
        _id: "$dekada",
        najlepszyCzasMs: { $first: "$milliseconds" },
        rok:      { $first: "$year" },
        raceId:   { $first: "$raceId" },
        driverId: { $first: "$driverId" },
        okrazenie: { $first: "$lap" }
    }},
    { $lookup: { from: "races",   localField: "raceId",   foreignField: "raceId",   as: "wyścig" } },
    { $lookup: { from: "drivers", localField: "driverId", foreignField: "driverId", as: "kierowca" } },
    { $project: {
        _id: 0,
        dekada: "$_id",
        najlepszyCzasMs: 1,
        rok: 1, okrazenie: 1,
        wyścig:   { $arrayElemAt: ["$wyścig.name", 0] },
        kierowca: { $concat: [
            { $arrayElemAt: ["$kierowca.forename", 0] }, " ",
            { $arrayElemAt: ["$kierowca.surname", 0] } ] }
    }},
    { $sort: { dekada: 1 } }
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Q5: Najlepszy czas (najszybsze okrążenie) każdego kierowcy z podziałem
//     na konstruktorów (dla których jeździł). Czas "m:ss.mmm" parsowany
//     do sekund, żeby sortowanie/minimum było liczbowe.
// ---------------------------------------------------------------------------
function q5() {
  return db.races.aggregate([
    { $unwind: "$results" },
    { $match: { "results.fastestLap.time": { $nin: [null, ""] } } },
    // "1:36.236" -> sekundy (float)
    { $addFields: { fl: { $split: ["$results.fastestLap.time", ":"] } } },
    { $addFields: { flSec: { $add: [
        { $multiply: [{ $toDouble: { $arrayElemAt: ["$fl", 0] } }, 60] },
        { $toDouble: { $arrayElemAt: ["$fl", 1] } }
    ] } } },
    { $sort: { flSec: 1 } },                  // najpierw najszybsze
    // code może być null -> fallback na imię + nazwisko
    { $addFields: { kierowca: { $ifNull: ["$results.driver.code",
        { $concat: ["$results.driver.forename", " ", "$results.driver.surname"] }] } } },
    { $group: {
        _id: { kierowca: "$kierowca", konstruktor: "$results.constructor.name" },
        najlepszyCzas: { $first: "$results.fastestLap.time" },
        sekundy:       { $first: "$flSec" },
        wyścig:        { $first: "$name" },
        rok:           { $first: "$year" }
    }},
    { $project: {
        _id: 0,
        kierowca: "$_id.kierowca",
        konstruktor: "$_id.konstruktor",
        najlepszyCzas: 1, sekundy: 1, wyścig: 1, rok: 1
    }},
    { $sort: { kierowca: 1, sekundy: 1 } },
    { $limit: 40 }                            // zdejmij $limit, aby zobaczyć wszystkich
  ]).toArray();
}

// ---------------------------------------------------------------------------
// Demo: uruchomienie wszystkich zapytań
// ---------------------------------------------------------------------------
if (typeof print !== "undefined") {
  print("\n===== Q1: kierowcy w poszczególnych latach (pierwsze 5 lat) =====");
  printjson(q1().slice(0, 5));
  print("... razem lat: " + q1().length);

  print("\n===== Q2: najlepsi konstruktorzy (TOP 10) =====");
  printjson(q2());

  print("\n===== Q3a: liczba pit stopów a średni wynik =====");
  printjson(q3a());

  print("\n===== Q3b: średnia liczba pit stopów vs średnia pozycja (TOP 15) =====");
  printjson(q3b());

  print("\n===== Q4: najlepsze czasy w dekadach =====");
  printjson(q4());

  print("\n===== Q5: najlepszy czas kierowcy per konstruktor (pierwsze 40) =====");
  printjson(q5());
}
