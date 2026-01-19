import csv
import random

# Dados de exemplo
colors = [
    ("Branco", "Branco"), ("Azul", "Azul"), ("Verde", "Verde"), ("Vermelho", "Vermelho"),
    ("Amarelo", "Amarelo"), ("Cinza", "Cinza"), ("Marrom", "Marrom"), ("Preto", "Preto"),
    ("Rosa", "Rosa"), ("Laranja", "Laranja")
]

surfaces = ["parede", "madeira", "azulejo", "metal"]
environments = ["interno", "externo", "ambos"]
finish_types = ["fosco", "acetinado", "brilhante", "semi-brilhante"]
lines = ["Premium", "Standard", "Economy"]

features_options = [
    "lavável", "sem odor", "anti-mofo", "alta cobertura", "resistente a manchas",
    "resistente a chuva e sol", "protege madeira", "resistente a ferrugem"
]

# Criar 100 tintas
paints = []
for i in range(1, 101):
    color_code, color_name = random.choice(colors)
    surface = random.choice(surfaces)
    environment = random.choice(environments)
    finish = random.choice(finish_types)
    line = random.choice(lines)
    features = ", ".join(random.sample(features_options, k=2))
    price = round(random.uniform(50, 130), 2)
    description = f"Tinta {finish} {color_name} para {surface} ({environment}), linha {line}."
    
    paints.append([
        i,  # id
        f"Suvinil {finish.capitalize()} {color_name} {i}",  # name
        color_code,
        color_name,
        surface,
        environment,
        finish,
        features,
        line,
        price,
        description,
        True  # is_active
    ])

# Salvar CSV
with open("paints_mock_100.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        "id","name","color","color_name","surface_type","environment",
        "finish_type","features","line","price","description","is_active"
    ])
    writer.writerows(paints)

print("Arquivo paints_mock_100.csv criado com 100 tintas mockadas!")
