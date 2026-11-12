# UWAGA! Nie robiłem polarsa. 

# UV

`uv init`

`uv add <pakiet>`

`uv run <skrypt.py>`

`uv add ipykernel` - aby jupiter notebook działał VSC

`!pip install <pakiet>` - instalacja pakietu w colabie

# Listy i tabele

```python
import numpy as np

lista = [0,1,2,3]

numpy_lista = np.array(lista) #ndarray

numpy_lista.mean()
numpy_lista.std()
numpy_lista.shape()
# ...

numpy_lista * 2 # 0, 2, 4, 6

# ndarray pozwala wykonywać obliczenia na całej strukturze, operacje wektorowe itd

import pandas as pd

df = pd.Dataframe({
  "col1": ["el1", "el2"],
  "col2": [0,1]
})

series = pd.Series(["tekst", "tekst2", "tekst3"], name="losowe")

# Series przechowuje dane jako jednokolumnowa tabela
# DataFrame to tabela, kolumny i wiersze, różne typy danych. Każda kolumna to Series. 
```


# Czytanie danych

```python
# csv

df = pd.read_csv("data/plik.csv")

# można też po URL

url = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/penguins.csv"
df_url = pd.read_csv(url)

# można też z seaborn gotowy dataset

df_seaborn = sns.load_dataset("penguins")
```

# Pandas

```python
df.info() # info o strukturze DF, typy, kolumny, itd
df.describe() # statystyki opisowe, liczba obserwacji, średnia, std

df.isnull() # czy wartość w komórce jest pusta
df.isnull().sum() # zsumowanie komórek, daje informacje ile wartości pustych w kolumnie

df["test"] # pobranie kolumny test 
df[
  ["test1", "test2"] # pobranie 2 kolumn (wymaga tablicy w [])
] 

df.loc[0:4, # 0:4 pobierze wiersze od etykiet 0 do 4 
  ["test1", "test2"] # i kolumny test1 i test2
]

df["test"].nunique() # liczba unikatowych wartości
df["test"].value_counts() # zliczenie wartości w kolumnie

df.iloc[
  0:5, # wybieranie wierszy od 0 do 5, pierwsze 5 wiersze
  0:2 # wybieranie kolumn od 0 do 2, pierwsze 2 kolumny
]
```

## Operacje Pandas

```python
temp = df[ 
  df["test"] > 100 # warunek, który tworzy maskę T/F
] # zwróci te kolumny, które spełniają zadany warunek

temp2 = df[
  df["test"] == "x" & df["test2"] == "y" # warunek, wartości w kolumnach test1 i test2 mają mieć odpowiednio x i y 
]

df.sort_values("kolumna", ascending=False) # sortwanie malejąco po wartościach w kolumnie "kolumna"

df.groupby("kolumna") # grupowanie po kolumnie "kolumna"
  ["test1"].mean() # obliczenie średniej dla kolumny test1 po pogrupwowaniu

df.groupby("kolumna").agg(
  nowa_kolumna_agregacji = ("stara_kolumna", "<funkcja>") #utworzenie nowej kolumny, która jest wynikiem agreagacji
  zliczenie = ("test1", "count") # zliczenie wartości w kolumnie "test1", po pogrupowaniu
)
# tutaj została utworzona nowa kolumna "nowa_kolumna_agregacji", która powstaje po pogrupowaniu wartości po kolumnie "kolumna", następnie wykonanie <funkcja> (np. mean, median, count) na kolumnie "stara_kolumna"

df["tej_kolumny_nie_bylo"] = df["test1"] / 100 # utworzenie nowej kolumny na podstawie istniejącej kolumny
df["duch"] = df["test1"] * df["test2"] # utworzenie kolumny na podstawie 2 innych kolumn!

mediana_test1 = df["test1"].median() #zapisanie mediany do zmiennej

df["seria"] = np.where( # funkcja posiada warunek, potem wpisuje jedną z podanych dalej wartości na podstawie wyniku
  df["test1"] > mediana_test1, "wieksza-od-mediany", "mniejsza-od-mediany"
)
```

## Ocena jakości danych

Typowe błędy danych: 
- braki (NaN, null w komórkach)
- duplikaty (takie same kolumny/wiersze)
- wartości odstające (niemożliwe, błędy, ...)
- niespójne typy (string w kolumnie liczbowej itd)
- wartośći spoza zakresu (znowu, niemożliwe wartości)

```python
df_kopia = df.copy() # wykonanie kopi DF
df_kopia.loc[3, "temp1"] = "test" # w wierszy o indeksie 3, w kolumnie "temp1" zostanie wstawiona wartość "test" (w komórce)

pd.concat( # łączy 2 dataframe
  [
    df1, # dataframe 1, zwykły
    df1.iloc[[0]] # wskazany wiersz z dataframe 1
  ]
) # powoduje duplikacje wiersza

df.dtypes() # weryfikacja zmiennych kategorycznych
df.duplicated().sum() # ile jest zduplikowanych wartości 
```

### Wartości odstające

IQR = Q3 - Q1, obliczenie Q1 i Q3 (kwartyl 1 i 3, odpowiednio 25% wartości i 75% wartości) Q2 to mediana i oznacza kwartyl 50%. 

```python

Q1, Q3 = df["kolumna"].quantile([0.25, 0.75])

IQR = Q3 - Q1 # rozstęp

lower, upper = Q1 - 1.5 * IQR, Q3 + 1.5 * IQR # granice reguły

odstajace = df[(df["kolumna"] < lower) | (df["kolumna"] > upper)] # zawarte są tylko wartosci odstajace

```

### Czyszczenie danych

Niepoprawne dane to błędne wyniki, można usunąć obserwację w całości albo próbować naprawić dane w wierszu/kolumnie.

```python

df["test"] = df["test"].replace("brak", np.nan) # tutaj, wpis "brak" zostaje zamieniony na NaN z numpy
df.loc[df["test"] < 0, "test"] = np.nan # ujemne pomiary w kolumnie "test", zamieniamy na NaN

# zamieniamy na NaN bo łatwiej takie wartości znaleźć i naprawić:

print(df.isnull().sum())

df.dropna() # usunięcie wartości NaN

df.drop_duplicates() # usunięcie kolumn które się powtarzają

# Imputacja - uzupełnianie braków

from sklearn.impute import SimpleImputer

imputer_median = SimpleImputer(strategy="median") # Imputacja przez medianę
df["kolumna"] = imputer_median.fit_transform(df["kolumna"]) # Wypełnienie wartości pustych poprzez medianę

imputer_mode = SimpleImputer(strategy="most_frequent") # Imputacja przez dominantę
df_imputed[["sex"]] = imputer_mode.fit_transform(df_imputed[["sex"]])

print(df_imputed.isnull().sum().sum()) # 0 oznacza zbiór kompletny

mean_mass = df_experiment["body_mass_g"].mean() # obliczenie średniej
df_experiment["body_mass_g"] = df_experiment["body_mass_g"].fillna(mean_mass) # w puste wartości wstawiamy średnią
```

### Standaryzacja

```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler

skaler_std = StandardScaler() # Utworzenie skalera standaryzującego cechy
X_std = pd.DataFrame(skaler_std.fit_transform(X), columns=X.columns) # Standaryzacja cech i utworzenie nowej ramki danych

skaler_mm = MinMaxScaler() # Utworzenie skalera normalizującego wartości do zakresu 0-1
X_mm = pd.DataFrame(skaler_mm.fit_transform(X), columns=X.columns) # Normalizacja cech i utworzenie nowej ramki danych
```

### Kategorie na liczby

```python
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

# One Hot wstawia tyle kolumn ile jest unikalnych wartości w kolumnie, wartość która akurat występuje w tym wierszu ma w odpowiadającej kolumnie 1, reszta 0

encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False) # Utworzenie kodera
encoded = encoder.fit_transform(df.dropna()[["island", "sex"]]) # Zakodowanie zmiennych kategorycznych

# Ordinal wstawia wartości w kolumnie zamiast stringu na 0 do n - 1, n to ilość unikalnych wartości w kolumnie

encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=False) # Utworzenie kodera
encoded = encoder.fit_transform(df.dropna()[["island", "sex"]]) # Zakodowanie zmiennych kategorycznych
```

## PCA 

```python
scaler = StandardScaler()
X_standardized = scaler.fit_transform(X_numeric) # Standaryzacja cech przed zastosowaniem PCA
pca = PCA(n_components=4)
X_pca = pca.fit_transform(X_standardized) # Przekształcenie danych do nowych składowych

print(pca.explained_variance_ratio_.round(3)) # Wyświetlenie udziału wariancji wyjaśnianej przez każdą składową -> [0.688 0.193 0.091 0.027]
```

## Pipeline i ColumnTransformer

```python

# Podejście dobre, ale prymitywne
X_train_num, X_test_num = train_test_split(X_complete, random_state=42)
scaler = StandardScaler().fit(X_train_num) # Dopasowanie tylko na danych treningowych
X_train_num_scaled = scaler.transform(X_train_num) # Przeskalowanie zbioru treningowego
X_test_num_scaled = scaler.transform(X_test_num) # Te same parametry zastosowane do testu


from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

categorical_columns = ["island", "sex"]

numeric_pipeline = Pipeline([ # tworzenie pipeline
  ("imputer", SimpleImputer(strategy="median")), # Najpierw uzupełnienie brakujących wartości
  ("scaler", StandardScaler()), # Potem standaryzacja cech liczbowych
])

categorical_pipeline = Pipeline([
  ("imputer", SimpleImputer(strategy="most_frequent")), # Uzupełnienie braków dominantą
  ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False)), # Zakodowanie kategorii
])

# ColumnTransformer przypisuje odpowiednie przekształcenia do konkretnych kolumn
# (numeric_pipeline do cech liczbowych, a categorical_pipeline do kategorycznych)

preprocessor = ColumnTransformer([ # ColumnTransformer pozwala zastosować Pipeline, 
  ("numeric", numeric_pipeline, numeric_columns),
  ("categorical", categorical_pipeline, categorical_columns),
])

X_train_processed = preprocessor.fit_transform(X_train) # Dopasowanie przetwarzania wyłącznie na danych treningowych
X_test_processed = preprocessor.transform(X_test) # Zastosowanie tych samych parametrów do danych testowych

pca_pipeline = Pipeline([
  ("preprocessing", preprocessor), # Wykonanie przygotowania danych z poprzedniego ćwiczenia
  ("pca", PCA(n_components=2)), # Redukcja liczby wymiarów do dwóch składowych
])

X_train_2d = pca_pipeline.fit_transform(X_train) # Dopasowanie potoku i przekształcenie danych treningowych
```

## SQL -> Pandas

```sql
SELECT species, AVG(body_mass_g) AS mean_mass
FROM penguins
GROUP BY species
HAVING AVG(body_mass_g) > 4000
``` 

```python

summary = df.groupby("species") # GROUP BY species
  .agg(mean_mass="body_mass_g", "mean") # SELECT species, AVG(body_mass_g) AS mean_mass

result = summary[summary["mean_mass"] > 4000] # HAVING AVG(body_mass_g) > 4000
```

```sql
SELECT
  species,
  island,
  AVG(body_mass_g) AS mean_mass,
  MAX(body_mass_g) AS max_mass,
  COUNT(body_mass_g) AS count
FROM penguins
GROUP BY species, island
HAVING COUNT(body_mass_g) >= 10;
```

```python
summary = df.groupby(["species, island"]) # GROUP BY species, island
  .agg(
    mean_mass=("body_mass_g", "mean"), # AVG(body_mass_g) AS mean_mass,
    max_mass=("body_mass_g", "max"), # MAX(body_mass_g) AS max_mass,
    count=("body_mass_g", "count"), # COUNT(body_mass_g) AS count
  )

result = summary[summary["count"] >= 10] # HAVING COUNT(body_mass_g) >= 10;
```

# SciKit Learn

```python

from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
  X, # dane trenigowe wejściowe
  y, # dane treningowe wyjściowe
  test_size = 0.2, # 80% treningowe, 20% testowe
  random_state=42 
)

```

# Seaborn

```python
plt.figure(figsize=(8, 5)) # Ustalenie rozmiaru wykresu
sns.histplot(data=df, x="body_mass_g", bins=20) # Utworzenie histogramu masy ciała (bins dzieli zakres mas na 20 przedziałów)
plt.title("Rozkład masy ciała pingwinów") # Tytuł wykresu
plt.xlabel("Masa ciała [g]") # Opis osi X
plt.ylabel("Liczba obserwacji") # Opis osi Y
plt.show() # Wyświetlenie wykresu

plt.figure(figsize=(8, 5)) # Ustalenie rozmiaru wykresu
sns.boxplot(data=df, x="species", y="body_mass_g", color="green") # Utworzenie wykresu pudełkowego w kolorze zielonym
plt.title("Masa ciała według gatunku") # Tytuł wykresu
plt.xlabel("Gatunek") # Opis osi X
plt.ylabel("Masa ciała [g]") # Opis osi Y
plt.show() # Wyświetlenie wykresu

plt.figure(figsize=(8, 5)) # Ustawienie rozmiaru wykresu
sns.scatterplot(data=df, x="bill_length_mm", y="bill_depth_mm", hue="species") # Utworzenie wykresu punktowego z podziałem na gatunki
plt.title("Wymiary dzioba według gatunku") # Tytuł wykresu
plt.xlabel("Długość dzioba [mm]") # Opis osi X
plt.ylabel("Głębokość dzioba [mm]") # Opis osi Y
plt.legend(title="Gatunek") # Dodanie tytułu legendy
plt.show() # Wyświetlenie wykresu

matrix = df.corr(numeric_only=True) # Obliczenie macierzy korelacji dla zmiennych liczbowych
plt.figure(figsize=(7, 5)) # Ustalenie rozmiaru wykresu
sns.heatmap(matrix, annot=True) # Utworzenie mapy korelacji z
wyświetleniem wartości liczbowych
plt.title("Mapa korelacji cech liczbowych") # Tytuł wykresu
plt.show() # Wyświetlenie wykresu
```

# Zapis wartości 

```python
import os 
os.makedirs("output", exist_ok=True) # utworzenie katalogu
df.to_csv("output/data.csv", index=False) # zapisanie DataFrame do csv w ścieżce
plt.savefig("output/masa_wg_gatunku.png", dpi=150, bbox_inches="tight") #zapisanie wykresu do .png

# pipeline do pliku
import joblib
joblib.dump(preprocessor, "output/preprocessor.joblib") # Zapisanie potoku przetwarzania do pliku
loaded_preprocessor = joblib.load("output/preprocessor.joblib") # Wczytanie zapisanego potoku
```

# Pandera

Biblioteka Pandera pozwala zapisać wymagania wobec danych jako schmeat w kodzie i automatycznie przy każdym wczytaniu walidować dane. 

```python
# przykład walidacji z Pandera

import pandera.pandas as pa
from pandera.pandas import Column, Check, DataFrameSchema

schemat = DataFrameSchema({
  "species": Column(str, Check.isin(["Adelie", "Chinstrap", "Gentoo"])),
  "island": Column(str, Check.isin(["Torgersen", "Biscoe", "Dream"])),
  "bill_length_mm": Column(float, Check.in_range(30, 62), nullable=True), 
  "bill_depth_mm": Column(float, Check.in_range(13, 22), nullable=True), 
  "flipper_length_mm": Column(float, Check.in_range(170, 235), nullable=True), 
  "body_mass_g": Column(float, Check.in_range(2500, 6500), nullable=True), 
  "sex": Column(str, Check.isin(["Male", "Female"]), nullable=True), 
})
validated = schemat.validate(df) # Walidacja danych na podstawie kryteriów
print("Walidacja zakończona powodzeniem, wymiary:", validated.shape) 
# Walidacja zakończona powodzeniem, wymiary: (344, 7)

# Wypisanie jak walidacja nie przejdzie

try:
  schemat.validate(df_dirty, lazy=True)
  print("Walidacja zakończona powodzeniem")
except pa.errors.SchemaErrors as err:
  print(err.failure_cases)
```

## Augumentacja danych (?)

```python
rng = np.random.default_rng(42) # Generator z ziarnem
train_data = X_train.dropna().copy() # Kopia zbioru uczącego bez brakujących wartości
train_data["species"] = y_train.loc[train_data.index] # Dołączenie etykiet gatunków
augmented_data = train_data.copy()
feature_std = train_data[numeric_columns].std() # Obliczenie odchylenia standardowego każdej cechy
noise = rng.normal(loc=0, scale=0.02 * feature_std.values, size=train_data[numeric_columns].shape) # Wygenerowanie szumu o wartości 2% odchylenia standardowego cechy
augmented_data[numeric_columns] = (train_data[numeric_columns] + noise) # Utworzenie zaszumionych kopii cech przy zachowaniu etykiet
augmented_train_data = pd.concat([train_data, augmented_data], ignore_index=True) # Połączenie danych oryginalnych i rozszerzonych
print(train_data.shape, "->", augmented_train_data.shape) # (264, 7) -> (528, 7)
```

# Przetwarzanie obrazów

## Wczytywanie, wyświetlanie i zapisywanie obrazów

```python
image = data.coffee() # Wczytanie przykładowego obrazu wbudowanego w scikit-image

print("Kształt tablicy:", image.shape) # (400, 600, 3)
print("Typ danych:", image.dtype) # uint8
print("Zakres wartości:", image.min(), "-", image.max()) # 0 - 255
print("Liczba wartości:", image.size) # 720000
red = image[:, :, 0] # Wybranie kanału czerwonego
green = image[:, :, 1] # Wybranie kanału zielonego
blue = image[:, :, 2] # Wybranie kanału niebieskiego

# wykres jako wyświetlenie obrazu

fig, axes = plt.subplots(1, 4, figsize=(14, 4)) # Cztery wykresy obok siebie
axes[0].imshow(image) # Wyświetlenie obrazu w kolorze
axes[0].set_title("Oryginał (RGB)")
for ax, channel, name in zip(axes[1:], [red, green, blue], ["R", "G", "B"]):
  ax.imshow(channel, cmap="gray") # Wyświetlenie kanału w skali szarości
  ax.set_title(f"Kanał {name}")
for ax in axes:
  ax.axis("off") # Ukrycie osi
plt.tight_layout()
plt.show()

# zapisanie obrazu

os.makedirs("data", exist_ok=True) # Utworzenie katalogu na dane wejściowe, jeśli jeszcze nie istnieje
io.imsave("data/coffee.png", image) # Zapis obrazu do pliku PNG

# wczytanime obrazu biblioteką Pillow
pil_image = Image.open("data/coffee.png") # Wczytanie pliku biblioteką Pillow
print("Pillow:", type(pil_image)) # <class 'PIL.PngImagePlugin.PngImageFile'>
pil_array = np.array(pil_image) # Konwersja obiektu Pillow do tablicy NumPy
print("Pillow == scikit-image:", np.array_equal(pil_array, sk_image)) # True


cv_image = cv2.imread("data/coffee.png") # Wczytanie biblioteką OpenCV
print("OpenCV:", type(cv_image), cv_image.shape) # <class 'numpy.ndarray'> (400, 600, 3)
rgb_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB) # Konwersja przestrzeni barw BGR na RGB

sk_image = io.imread("data/coffee.png") # Wczytanie biblioteką scikit-image
print("scikit-image:", type(sk_image), sk_image.shape) # <class 'numpy.ndarray'> (400, 600, 3)

print("OpenCV == scikit-image:", np.array_equal(cv_image, sk_image)) # False
print("OpenCV po konwersji:", np.array_equal(rgb_image, sk_image)) # True

# wyświetlenie obrazów

fig, axes = plt.subplots(1, 2, figsize=(10, 4))
axes[0].imshow(cv_image) # Wyświetlenie danych BGR tak, jakby były RGB
axes[0].set_title("OpenCV bez konwersji (BGR)")
axes[1].imshow(rgb_image)
axes[1].set_title("OpenCV po konwersji (RGB)")
for ax in axes:
  ax.axis("off")
plt.tight_layout()
plt.show()
io.imsave("data/coffee.jpg", image) # Zapis obrazu do formatu JPG
png_size = os.path.getsize("data/coffee.png") / 1024 # Rozmiar pliku PNG w KB
jpg_size = os.path.getsize("data/coffee.jpg") / 1024 # Rozmiar pliku JPG w KB
print(f"PNG: {png_size:.0f} KB, JPG: {jpg_size:.0f} KB") # PNG: 449 KB, JPG: 41 KB
```

## Transformacje geometryczne i operacje na pixelach

```python
resized = transform.resize(image, (224, 224), anti_aliasing=True) # Zmiana rozmiaru do 224x224
resized = (resized * 255).astype(np.uint8) # Funkcja resize zwraca float 0-1, powrót do uint8

print("Po zmianie rozmiaru:", resized.shape) # (224, 224, 3)

cropped = image[50:350, 150:450] # Przycięcie fragmentu przez wycinanie tablicy
flipped = image[:, ::-1] # Odbicie poziome przez odwrócenie kolejności kolumn
gray = color.rgb2gray(image) # Konwersja do skali szarości (wynik float w zakresie 0-1)

print("Skala szarości:", gray.shape, gray.dtype) # (400, 600) float64

wrong_brighter = image + 60 # Przepełnienie zakresu typu uint8!
brighter = np.clip(image.astype(np.int16) + 60, 0, 255).astype(np.uint8) # Rozjaśnienie z kontrolą zakresu
higher_contrast = np.clip((image.astype(np.float32) - 128) * 1.5 + 128, 0, 255).astype(np.uint8) # Kontrast
overflow = (wrong_brighter < image).sum() # Liczba wartości, które po dodaniu 60 zmalały

print("Piksele z przepełnieniem:", overflow) # 94427
```

## Filtrowanie i detekcja krawędzi

```python
from skimage import filters

# (Filtrowanie)
blurred = filters.gaussian(image, sigma=3, channel_axis=-1) # Rozmycie Gaussa (argument sigma określa siłę rozmycia) 

# (Detekcja krawędzi)
edges = filters.sobel(gray) # Filtr Sobela na obrazie w skali szarości 
```

## Augumentacja 

```python
import albumentations as A

pipeline = A.Compose([
  A.HorizontalFlip(p=0.5), # Odbicie poziome w 50% przypadków
  A.Rotate(limit=25, p=0.5), # Obrót o losowy kąt z zakresu +/- 25 stopni
  A.RandomBrightnessContrast(p=0.3), # Losowa zmiana jasności i kontrastu
  A.GaussianBlur(blur_limit=(3, 7), p=0.2), # Rozmycie Gaussa o losowej sile
])
```

## Przekształcanie w wektor

```python

# Podobieństwo kosinusowe

def cosine_similarity(a, b):
  return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


vector = image.astype(np.float32).flatten() # Spłaszczenie obrazu do jednego długiego wektora

shifted = np.roll(image, shift=15, axis=1) # Przesunięcie zawartości obrazu o 15 pikseli w prawo
darker = np.clip(image.astype(np.int16) - 40, 0, 255).astype(np.uint8) # Przyciemnienie obrazu

cat = data.chelsea() # Drugi obraz wbudowany w scikit-image
cat_resized = (transform.resize(cat, image.shape[:2], anti_aliasing=True) * 255).astype(np.uint8)

shifted_vector = shifted.astype(np.float32).flatten() # Wektor obrazu przesuniętego
darker_vector = darker.astype(np.float32).flatten() # Wektor obrazu przyciemnionego
cat_vector = cat_resized.astype(np.float32).flatten() # Wektor innego obrazu

print("Oryginał vs oryginał:", round(cosine_similarity(vector, vector), 4)) # 1.0
print("Oryginał vs przesunięty:", round(cosine_similarity(vector, shifted_vector), 4)) # 0.9314
print("Oryginał vs przyciemniony:", round(cosine_similarity(vector, darker_vector), 4)) # 0.9846
print("Oryginał vs inny obraz (kot):", round(cosine_similarity(vector, cat_vector), 4)) # 0.8121

```

# Zadania samodzielne 

## Lab 1

## Lab 2

## Lab 3