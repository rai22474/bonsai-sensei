import random
from datetime import datetime

_PROCESSING_MESSAGES = [
    "⏳ Meditando sobre tu petición...",
    "🌱 Consultando con los espíritus del jardín...",
    "🍃 Las hojas susurran... un momento...",
    "🧘 El sensei está en profunda contemplación...",
    "🌿 Afilando los utensilios...",
    "🎋 Consultando el libro de los bambúes...",
    "🍵 Preparando el té mientras reflexiono...",
    "🌸 La paciencia es la esencia del bonsái...",
    "⏳ Siguiendo el camino del agua...",
    "🌳 Los árboles crecen despacio, pero seguro...",
    "🪴 Podando ideas innecesarias...",
    "🌺 Los pétalos caen, la respuesta llega...",
    "🌾 El viento entre las ramas... un instante...",
    "⛩️ Pidiendo consejo al oráculo del jardín...",
    "🪨 Encontrando el equilibrio perfecto...",
]


def random_processing_message() -> str:
    return random.choice(_PROCESSING_MESSAGES)


def format_date(date_value) -> str:
    if isinstance(date_value, str):
        date_value = datetime.strptime(date_value, "%Y-%m-%d").date()
    return date_value.strftime("%d/%m/%Y")
