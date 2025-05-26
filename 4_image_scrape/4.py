from flask import Flask, request, render_template_string
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Bild-Kollage von {{ url }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background: #f9f9f9;
        }
        h1 {
            font-size: 1.5rem;
            margin-bottom: 20px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 10px;
        }
        .grid img {
            width: 100%;
            height: auto;
            border-radius: 6px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            object-fit: cover;
        }
    </style>
</head>
<body>
    <h1>Bilder von <a href="{{ url }}" target="_blank">{{ url }}</a></h1>
    {% if images %}
    <div class="grid">
        {% for img in images %}
            <img src="{{ img }}" alt="Bild" loading="lazy" />
        {% endfor %}
    </div>
    {% else %}
        <p>Keine Bilder gefunden oder Fehler beim Abrufen der Seite.</p>
    {% endif %}
</body>
</html>
"""


@app.route("/site/")
def site():
    target_url = request.args.get("url")
    if not target_url:
        return "Fehler: Bitte eine URL als Parameter 'url' angeben.", 400

    # Stelle sicher, dass die URL ein Schema hat
    if not target_url.startswith(("http://", "https://")):
        target_url = "http://" + target_url

    try:
        resp = requests.get(target_url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        images = []
        for img in soup.find_all("img"):
            src = img.get("src")
            if not src:
                continue
            # Absolut-URL generieren
            img_url = urljoin(target_url, src)
            images.append(img_url)

        # Duplikate entfernen
        images = list(dict.fromkeys(images))

    except Exception as e:
        images = []

    return render_template_string(HTML_TEMPLATE, url=target_url, images=images)


if __name__ == "__main__":
    app.run(port=8000, debug=True)
