"""COCO class labels: English (model order), German translation, emoji.

Index in COCO_CLASSES == class id coming out of the YOLO models that ship
with hailo-all.
"""

# (english, german, emoji)
COCO_CLASSES = [
    ("person", "Person", "🧍"),
    ("bicycle", "Fahrrad", "🚲"),
    ("car", "Auto", "🚗"),
    ("motorcycle", "Motorrad", "🏍️"),
    ("airplane", "Flugzeug", "✈️"),
    ("bus", "Bus", "🚌"),
    ("train", "Zug", "🚆"),
    ("truck", "LKW", "🚚"),
    ("boat", "Boot", "🚤"),
    ("traffic light", "Ampel", "🚦"),
    ("fire hydrant", "Hydrant", "🧯"),
    ("stop sign", "Stoppschild", "🛑"),
    ("parking meter", "Parkuhr", "🅿️"),
    ("bench", "Bank", "🪑"),
    ("bird", "Vogel", "🐦"),
    ("cat", "Katze", "🐱"),
    ("dog", "Hund", "🐶"),
    ("horse", "Pferd", "🐴"),
    ("sheep", "Schaf", "🐑"),
    ("cow", "Kuh", "🐮"),
    ("elephant", "Elefant", "🐘"),
    ("bear", "Bär", "🐻"),
    ("zebra", "Zebra", "🦓"),
    ("giraffe", "Giraffe", "🦒"),
    ("backpack", "Rucksack", "🎒"),
    ("umbrella", "Regenschirm", "☂️"),
    ("handbag", "Handtasche", "👜"),
    ("tie", "Krawatte", "👔"),
    ("suitcase", "Koffer", "🧳"),
    ("frisbee", "Frisbee", "🥏"),
    ("skis", "Ski", "🎿"),
    ("snowboard", "Snowboard", "🏂"),
    ("sports ball", "Ball", "⚽"),
    ("kite", "Drachen", "🪁"),
    ("baseball bat", "Baseballschläger", "🏏"),
    ("baseball glove", "Baseballhandschuh", "🥎"),
    ("skateboard", "Skateboard", "🛹"),
    ("surfboard", "Surfbrett", "🏄"),
    ("tennis racket", "Tennisschläger", "🎾"),
    ("bottle", "Flasche", "🍾"),
    ("wine glass", "Weinglas", "🍷"),
    ("cup", "Tasse", "☕"),
    ("fork", "Gabel", "🍴"),
    ("knife", "Messer", "🔪"),
    ("spoon", "Löffel", "🥄"),
    ("bowl", "Schüssel", "🥣"),
    ("banana", "Banane", "🍌"),
    ("apple", "Apfel", "🍎"),
    ("sandwich", "Sandwich", "🥪"),
    ("orange", "Orange", "🍊"),
    ("broccoli", "Brokkoli", "🥦"),
    ("carrot", "Karotte", "🥕"),
    ("hot dog", "Hotdog", "🌭"),
    ("pizza", "Pizza", "🍕"),
    ("donut", "Donut", "🍩"),
    ("cake", "Kuchen", "🍰"),
    ("chair", "Stuhl", "🪑"),
    ("couch", "Sofa", "🛋️"),
    ("potted plant", "Topfpflanze", "🪴"),
    ("bed", "Bett", "🛏️"),
    ("dining table", "Tisch", "🍽️"),
    ("toilet", "Toilette", "🚽"),
    ("tv", "Fernseher", "📺"),
    ("laptop", "Laptop", "💻"),
    ("mouse", "Computermaus", "🖱️"),
    ("remote", "Fernbedienung", "🎛️"),
    ("keyboard", "Tastatur", "⌨️"),
    ("cell phone", "Handy", "📱"),
    ("microwave", "Mikrowelle", "🔥"),
    ("oven", "Backofen", "🍞"),
    ("toaster", "Toaster", "🍞"),
    ("sink", "Spüle", "🚰"),
    ("refrigerator", "Kühlschrank", "🧊"),
    ("book", "Buch", "📖"),
    ("clock", "Uhr", "🕐"),
    ("vase", "Vase", "🏺"),
    ("scissors", "Schere", "✂️"),
    ("teddy bear", "Teddybär", "🧸"),
    ("hair drier", "Föhn", "💨"),
    ("toothbrush", "Zahnbürste", "🪥"),
]


def class_info(class_id: int):
    """Return (english, german, emoji) for a class id, with a safe fallback."""
    if 0 <= class_id < len(COCO_CLASSES):
        return COCO_CLASSES[class_id]
    return ("object", "Objekt", "❓")


_ASCII_MAP = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "Ä": "Ae",
                            "Ö": "Oe", "Ü": "Ue", "ß": "ss"})


def de_ascii(text: str) -> str:
    """cv2.putText can only draw ASCII — transliterate German umlauts."""
    return text.translate(_ASCII_MAP)
