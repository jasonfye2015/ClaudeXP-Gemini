"""A small offline gazetteer for the Furry Proximity Locator: place name -> (latitude, longitude).

Text in a resident's Location is matched against these names (whole words, case and accents ignored). The most
specific kind wins (a city beats a state, a state beats a country); ties go to the longer name. Nothing here is
looked up online, and a place that isn't listed is simply not pinned."""
import re
import unicodedata

CITIES = """
new york city|40.71|-74.01
nyc|40.71|-74.01
brooklyn|40.65|-73.95
los angeles|34.05|-118.24
chicago|41.88|-87.63
houston|29.76|-95.37
phoenix|33.45|-112.07
philadelphia|39.95|-75.17
san antonio|29.42|-98.49
san diego|32.72|-117.16
dallas|32.78|-96.80
fort worth|32.76|-97.33
san jose|37.34|-121.89
austin|30.27|-97.74
jacksonville|30.33|-81.66
san francisco|37.77|-122.42
oakland|37.80|-122.27
seattle|47.61|-122.33
tacoma|47.25|-122.44
spokane|47.66|-117.43
denver|39.74|-104.99
boulder|40.01|-105.27
boston|42.36|-71.06
las vegas|36.17|-115.14
portland|45.52|-122.68
portland maine|43.66|-70.26
detroit|42.33|-83.05
nashville|36.16|-86.78
memphis|35.15|-90.05
atlanta|33.75|-84.39
miami|25.76|-80.19
orlando|28.54|-81.38
tampa|27.95|-82.46
new orleans|29.95|-90.07
minneapolis|44.98|-93.27
saint paul|44.95|-93.09
st paul|44.95|-93.09
st louis|38.63|-90.20
saint louis|38.63|-90.20
kansas city|39.10|-94.58
topeka|39.05|-95.68
wichita|37.69|-97.34
lawrence|38.97|-95.24
omaha|41.26|-95.93
des moines|41.59|-93.62
salt lake city|40.76|-111.89
albuquerque|35.08|-106.65
tucson|32.22|-110.97
pittsburgh|40.44|-80.00
cleveland|41.50|-81.69
columbus|39.96|-83.00
cincinnati|39.10|-84.51
indianapolis|39.77|-86.16
milwaukee|43.04|-87.91
madison|43.07|-89.40
baltimore|39.29|-76.61
washington dc|38.91|-77.04
washington d c|38.91|-77.04
raleigh|35.78|-78.64
charlotte|35.23|-80.84
richmond|37.54|-77.44
buffalo|42.89|-78.88
rochester|43.16|-77.61
syracuse|43.05|-76.15
albany|42.65|-73.76
ithaca|42.44|-76.50
anchorage|61.22|-149.90
honolulu|21.31|-157.86
oklahoma city|35.47|-97.52
tulsa|36.15|-95.99
little rock|34.75|-92.29
louisville|38.25|-85.76
boise|43.62|-116.20
sacramento|38.58|-121.49
providence|41.82|-71.41
hartford|41.76|-72.67
toronto|43.65|-79.38
montreal|45.50|-73.57
vancouver|49.28|-123.12
calgary|51.05|-114.07
edmonton|53.55|-113.49
ottawa|45.42|-75.70
winnipeg|49.90|-97.14
halifax|44.65|-63.57
mexico city|19.43|-99.13
london|51.51|-0.13
manchester|53.48|-2.24
birmingham|52.49|-1.89
liverpool|53.41|-2.98
leeds|53.80|-1.55
sheffield|53.38|-1.47
nottingham|52.95|-1.15
bristol|51.45|-2.59
newcastle|54.98|-1.62
edinburgh|55.95|-3.19
glasgow|55.86|-4.25
cardiff|51.48|-3.18
belfast|54.60|-5.93
dublin|53.35|-6.26
paris|48.86|2.35
berlin|52.52|13.40
munich|48.14|11.58
hamburg|53.55|9.99
madrid|40.42|-3.70
barcelona|41.39|2.17
rome|41.90|12.50
milan|45.46|9.19
amsterdam|52.37|4.90
brussels|50.85|4.35
vienna|48.21|16.37
zurich|47.38|8.54
stockholm|59.33|18.07
oslo|59.91|10.75
copenhagen|55.68|12.57
helsinki|60.17|24.94
reykjavik|64.15|-21.94
warsaw|52.23|21.01
prague|50.08|14.44
budapest|47.50|19.04
moscow|55.76|37.62
lisbon|38.72|-9.14
athens|37.98|23.73
istanbul|41.01|28.98
tokyo|35.68|139.69
osaka|34.69|135.50
seoul|37.57|126.98
beijing|39.90|116.41
shanghai|31.23|121.47
hong kong|22.32|114.17
taipei|25.03|121.57
bangkok|13.76|100.50
singapore|1.35|103.82
manila|14.60|120.98
mumbai|19.08|72.88
delhi|28.61|77.21
dubai|25.20|55.27
tel aviv|32.09|34.78
sydney|-33.87|151.21
melbourne|-37.81|144.96
brisbane|-27.47|153.03
perth|-31.95|115.86
adelaide|-34.93|138.60
canberra|-35.28|149.13
auckland|-36.85|174.76
wellington|-41.29|174.78
christchurch|-43.53|172.64
sao paulo|-23.55|-46.63
rio de janeiro|-22.91|-43.17
buenos aires|-34.60|-58.38
santiago|-33.45|-70.67
lima|-12.05|-77.04
bogota|4.71|-74.07
cairo|30.04|31.24
johannesburg|-26.20|28.05
cape town|-33.92|18.42
lagos|6.52|3.38
nairobi|-1.29|36.82
"""

REGIONS = """
alabama|32.8|-86.8
alaska|64.2|-149.5
arizona|34.2|-111.7
arkansas|34.9|-92.4
california|37.2|-119.5
colorado|39.0|-105.5
connecticut|41.6|-72.7
delaware|39.0|-75.5
florida|28.6|-82.4
georgia|32.7|-83.4
hawaii|20.8|-156.3
idaho|44.4|-114.6
illinois|40.0|-89.2
indiana|39.9|-86.3
iowa|42.0|-93.5
kansas|38.5|-98.4
kentucky|37.5|-85.3
louisiana|31.0|-92.0
maine|45.3|-69.2
maryland|39.0|-76.8
massachusetts|42.3|-71.8
michigan|44.3|-85.4
minnesota|46.3|-94.3
mississippi|32.7|-89.7
missouri|38.4|-92.5
montana|47.0|-109.6
nebraska|41.5|-99.8
nevada|39.3|-116.6
new hampshire|43.7|-71.6
new jersey|40.1|-74.7
new mexico|34.4|-106.1
new york|42.9|-75.5
north carolina|35.6|-79.4
north dakota|47.5|-100.5
ohio|40.3|-82.8
oklahoma|35.6|-97.5
oregon|43.9|-120.6
pennsylvania|40.9|-77.8
rhode island|41.7|-71.5
south carolina|33.9|-80.9
south dakota|44.4|-100.2
tennessee|35.8|-86.3
texas|31.5|-99.3
utah|39.3|-111.7
vermont|44.0|-72.7
virginia|37.5|-78.8
washington state|47.4|-120.5
washington|47.4|-120.5
west virginia|38.6|-80.6
wisconsin|44.6|-89.9
wyoming|43.0|-107.5
upstate new york|43.2|-75.4
long island|40.8|-73.2
midwest|41.5|-93.0
new england|43.5|-71.5
pacific northwest|46.5|-122.0
bay area|37.6|-122.2
silicon valley|37.4|-122.0
southern california|34.0|-117.5
northern california|39.5|-121.5
deep south|32.5|-88.5
ontario|50.0|-85.0
quebec|52.0|-71.8
british columbia|54.0|-125.0
alberta|54.5|-115.0
manitoba|55.0|-98.0
saskatchewan|54.0|-106.0
nova scotia|45.0|-63.0
new brunswick|46.5|-66.2
newfoundland|53.0|-60.0
prince edward island|46.4|-63.3
england|52.8|-1.5
scotland|56.8|-4.2
wales|52.4|-3.7
northern ireland|54.6|-6.7
new south wales|-32.0|147.0
victoria australia|-37.0|144.5
queensland|-22.5|144.5
western australia|-26.0|121.5
south australia|-30.0|135.0
tasmania|-42.0|146.6
bavaria|48.9|11.4
catalonia|41.8|1.6
"""

COUNTRIES = """
usa|39.8|-98.6
u s a|39.8|-98.6
united states|39.8|-98.6
united states of america|39.8|-98.6
america|39.8|-98.6
canada|56.1|-106.3
mexico|23.6|-102.5
brazil|-10.0|-52.0
argentina|-34.0|-64.0
chile|-33.0|-71.0
peru|-9.2|-75.0
colombia|4.6|-74.1
united kingdom|54.0|-2.5
uk|54.0|-2.5
u k|54.0|-2.5
great britain|54.0|-2.5
britain|54.0|-2.5
ireland|53.2|-8.0
france|46.6|2.4
germany|51.1|10.4
spain|40.2|-3.7
portugal|39.6|-8.0
italy|42.8|12.5
netherlands|52.2|5.3
holland|52.2|5.3
belgium|50.6|4.6
switzerland|46.8|8.2
austria|47.6|14.1
sweden|62.0|15.0
norway|61.0|9.0
finland|64.0|26.0
denmark|56.0|9.5
iceland|64.9|-18.6
poland|52.1|19.4
czech republic|49.8|15.5
hungary|47.2|19.5
russia|60.0|90.0
ukraine|49.0|31.4
turkey|39.0|35.0
greece|39.0|22.0
egypt|26.8|30.0
south africa|-29.0|24.0
nigeria|9.1|8.7
kenya|0.2|37.9
israel|31.5|34.9
india|21.0|78.0
china|35.0|103.0
japan|36.2|138.3
south korea|36.5|127.9
korea|36.5|127.9
taiwan|23.7|121.0
thailand|15.1|101.0
vietnam|16.0|107.0
philippines|12.9|122.8
indonesia|-2.5|118.0
malaysia|4.2|102.0
new zealand|-41.5|172.5
australia|-25.7|134.5
"""


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii").lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text).split())


def _table(block, rank):
    out = {}
    for line in block.strip().splitlines():
        name, lat, lon = line.split("|")
        out[normalize(name)] = (float(lat), float(lon), rank)
    return out


PLACES = {**_table(COUNTRIES, 1), **_table(REGIONS, 2), **_table(CITIES, 3)}
_COORDS = re.compile(r"(-?\d{1,2}(?:\.\d+)?)\s*[,;/ ]\s*(-?\d{1,3}(?:\.\d+)?)")


def find(text):
    """(lat, lon, matched name) for a free-text location, or None when nothing in it is a known place.
    'lat, lon' written out as numbers works too, e.g. '39.05, -95.68'."""
    if not text or not str(text).strip():
        return None
    m = _COORDS.fullmatch(str(text).strip())
    if m and abs(float(m.group(1))) <= 90 and abs(float(m.group(2))) <= 180:
        return float(m.group(1)), float(m.group(2)), "coordinates"
    padded = f" {normalize(text)} "
    best = None
    for name, (lat, lon, rank) in PLACES.items():
        if f" {name} " in padded and (best is None or (rank, len(name)) > (best[3], len(best[2]))):
            best = (lat, lon, name, rank)
    return None if best is None else (best[0], best[1], best[2])
