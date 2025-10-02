import random
import os
from flask import Flask, render_template, request, redirect, url_for, session
import redis

# Opret forbindelse til Upstash Redis
redis_url = os.environ.get("REDIS_URL")
r = redis.Redis.from_url(redis_url, decode_responses=True, ssl=True)

app = Flask(__name__)
app.secret_key = "hemmelig_nøgle"

# 8 spørgsmål med 4 svarmuligheder hver
questions = [
    {
        "question": "Hvad er din tilgang til forandring?",
        "options": [
            {"text": "Forandringer er uundgåelige men jeg passer på og bevarer de gamle traditioner", "house": "Yggdrasil"},
            {"text": "Jeg er nysgerrig og søger at opfinde og skabe ting der kan forbedre det nuværende hvis muligt", "house": "Freke"},
            {"text": "Jeg er interesseret i det ukendte og søger gerne svar der hvor andre ikke tør træde", "house": "Rimfaxe"},
            {"text": "Forandring er nødvendig for forbedring og jeg kæmper gerne for det", "house": "Fimbul"}
        ]
    },
    {
        "question": "Hvordan reagere du i en konflikt?",
        "options": [
            {"text": "Er nysgerrig på hvad der har startet den", "house": "Freke"},
            {"text": "Trækker på skulderne og blander mig udenom", "house": "Rimfaxe"},
            {"text": "Forsøger at mægle mellem parterne", "house": "Yggdrasil"},
            {"text": "Går straks ind og forsvarer min sag", "house": "Fimbul"}
        ]
    },
    {
        "question": "Hvilke egenskaber beskriver dig bedst?",
        "options": [
            {"text": "Opsøgende, Vis og Jordnær", "house": "Yggdrasil"},
            {"text": "Nysgerrig, Videnbegærlig og Legende", "house": "Freke"},
            {"text": "Mystisk, Drømmende og Hemmelig", "house": "Rimfaxe"},
            {"text": "Kaotisk, Stædig og Målrettet", "house": "Fimbul"}
        ]
    },
    {
        "question": "Du står foran en lukket dør, hvad gør du?",
        "options": [
            {"text": "Bruger rifa nidur til at springe den op", "house": "Fimbul"},
            {"text": "Går et par skridt tilbage og kigger efter en anden vej ind", "house": "Rimfaxe"},
            {"text": "Prøver at dirke låsen op", "house": "Freke"},
            {"text": "Tager i håndtaget", "house": "Yggdrasil"}
        ]
    },
    {
        "question": "Hvilket element føler du dig mest trukket til?",
        "options": [
            {"text": "Jord", "house": "Yggdrasil"},
            {"text": "Ild", "house": "Freke"},
            {"text": "Luft", "house": "Rimfaxe"},
            {"text": "Vand", "house": "Fimbul"}
        ]
    },
    {
        "question": "Hvad er din yndlingsfarve?",
        "options": [
            {"text": "Blå", "house": "Rimfaxe"},
            {"text": "Rød", "house": "Freke"},
            {"text": "Guld", "house": "Fimbul"},
            {"text": "Grøn", "house": "Yggdrasil"}
        ]
    },
    {
        "question": "Hvilket natursyn vil du helst stoppe op og beundre?",
        "options": [
            {"text": "En mægtig ulv der løber gennem skoven", "house": "Freke"},
            {"text": "Et stort prægtigt træ hvis rødder stikker dybt", "house": "Yggdrasil"},
            {"text": "En stjernehimmel fyldt med stjerner", "house": "Rimfaxe"},
            {"text": "Et frossent vandfald hvor alle istapper glitrer", "house": "Fimbul"}
        ]
    },
    {
        "question": "Hvad er din største drøm?",
        "options": [
            {"text": "At værne om det tabte", "house": "Yggdrasil"},
            {"text": "At opdage noget nyt", "house": "Freke"},
            {"text": "At guide folk", "house": "Rimfaxe"},
            {"text": "At gøre en forskel", "house": "Fimbul"}
        ]
    }
]

# Shuffle spørgsmål og svarmuligheder
random.shuffle(questions)
for q in questions:
    random.shuffle(q["options"])

# Husedata til resultatvisning
houses_info = {
    "Yggdrasil": {
        "logo": "yggdrasil.jpg",
        "description": "Hus Yggdrasil: Det ældste hus, grundlagt af Karen Brahe under den teknomagiske revolution i 1800-tallet, symboliserer begyndelsen på magisk praksis og historie. Yggdrasil er kendt for sin videnbegærlighed, visdom, jordnærhed og nysgerrighed. Husets fokus er at indsamle, beskytte og anvende viden med omhu."
    },
    "Freke": {
        "logo": "freke.jpg",
        "description": "Hus Freke: Grundlagt af opfinderen og teknomageren Thomas B. Thrige, er Freke kendt for sin opfindsomhed, nysgerrighed, kreativitet og legende tilgang. Hus Freke værner om viden og innovation, hvilket har bidraget til mange opdagelser, der muliggør magikeres sameksistens med fumlere."
    },
    "Rimfaxe": {
        "logo": "rimfaxe.jpg",
        "description": "Hus Rimfaxe: Det yngste hus i Nordheim, grundlagt af Maximilian Seligmann, balancerer Fimbuls og Frekes udviklingslyst med Yggdrasils værn om gammel magi. Rimfaxe er kendt for sin mystik, visdom, drømmende natur og hemmelighedsfuldhed. De specialiserer sig i spådomskunst, stjernesyn og gamle ritualer."
    },
    "Fimbul": {
        "logo": "fimbul.jpg",
        "description": "Hus Fimbul: Fimbul er kendt for at være stædige, kaotiske, passionerede og målrettede. Grundlagt af kvindenes fortaler Frida Schmidt, kæmper huset for lige rettigheder og for deres sag, uanset om det betyder at skille sig ud. De er altid klar til at kæmpe for det, de tror på."
    }
}

# Liste over indeks på “tunge” spørgsmål (0-baseret)
# Spørgsmål i denne liste får ekstra vægt i tilfælde af lighed
heavy_questions = [2]  # lige nu kun spørgsmål 3

# Flask-ruter
@app.route("/")
def index():
    # Opdater besøgstæller i Redis
    visits = r.incr("visits") # Tæller op med 1 hver gang nogen besøger siden
    # Nulstil session og start quiz
    session["current_q"] = 0
    session["scores"] = {h: 0 for h in houses_info.keys()}
    session["answers"] = {}
    return render_template("index.html")

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    current_q = session.get("current_q", 0)

    if current_q >= len(questions):
        return redirect(url_for("result"))

    question = questions[current_q]

    if request.method == "POST":
        selected_option = request.form.get("option")
        if selected_option:
            # Find huset for valget – brug default for at undgå StopIteration
            selected_house = next(
                (opt["house"] for opt in question["options"] if opt["text"] == selected_option),
                None
            )

            if selected_house:  # kun tilføj point hvis vi fandt et match
                # Gem brugerens valg pr. spørgsmål
                if "answers" not in session:
                    session["answers"] = {}
                session["answers"][str(current_q)] = selected_house
                # Tildel normal point
                session["scores"][selected_house] += 1

            # Gå til næste spørgsmål
            session["current_q"] = current_q + 1
            return redirect(url_for("quiz"))

    return render_template(
        "quiz.html",
        question=question,
        q_number=current_q + 1,
        total=len(questions)
    )


@app.route("/result")
def result():
    scores = session.get("scores", {})
    if not scores:
        return redirect(url_for("index"))

    # Find top-husene
    max_score = max(scores.values())
    top_houses = [house for house, pts in scores.items() if pts == max_score]

    # Tiebreaker: brug “tunge” spørgsmål hvis der er lighed
    if len(top_houses) > 1 and "answers" in session:
        for heavy_index in heavy_questions:
            heavy_choice = session["answers"].get(str(heavy_index))
            if heavy_choice and heavy_choice in top_houses:
                # Giv midlertidigt ekstra point
                scores[heavy_choice] += 1
                # Re-evaluer top-husene
                max_score = max(scores.values())
                top_houses = [house for house, pts in scores.items() if pts == max_score]
                # Stop tiebreaker hvis der nu kun er ét top-hus
                if len(top_houses) == 1:
                    break

    # Hvis der stadig er lighed, vælg tilfældigt
    house = random.choice(top_houses) if len(top_houses) > 1 else top_houses[0]

    # Gem resultatet i Redis
    r.incr(f"result:{house}")

    info = houses_info[house]
    return render_template(
        "result.html",
        house=house,
        logo=info["logo"],
        description=info["description"]
    )

@app.route("/admin")
def admin_dashboard():
    visits = int(r.get("visits") or 0)
    results = {house: int(r.get(f"result:{house}") or 0) for house in ["Yggdrasil", "Freke", "Rimfaxe", "Fimbul"]}

    html = f"""
    <html>
    <head>
        <title>Admin Dashboard</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f9f9f9; }}
            h1 {{ color: #333; }}
            table {{
                border-collapse: collapse;
                width: 50%;
                margin-top: 20px;
            }}
            th, td {{
                border: 1px solid #ccc;
                padding: 10px;
                text-align: left;
            }}
            th {{
                background-color: #eee;
            }}
            tr:nth-child(even) {{
                background-color: #f2f2f2;
            }}
        </style>
    </head>
    <body>
        <h1>Admin Dashboard</h1>
        <p><strong>Antal besøg:</strong> {visits}</p>
        <h2>Resultater</h2>
        <table>
            <tr><th>Hus</th><th>Antal</th></tr>
    """
    for house, count in results.items():
        html += f"<tr><td>{house}</td><td>{count}</td></tr>"

    html += """
        </table>
    </body>
    </html>
    """
    return html




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host ="0.0.0.0", port=port, debug=False)
