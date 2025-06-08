from agent.research_agent import format_products

mock_products = [
    {
        "title": "La Roche-Posay Hydraphase Intense Riche",
        "price": "159 kr.",
        "store": "Matas",
        "link": "https://matas.dk/la-roche-posay-hydraphase-intense-riche"
    },
    {
        "title": "Vichy Aqualia Thermal Rich",
        "price": "149 kr.",
        "store": "Apopro",
        "link": "https://apopro.dk/vichy-aqualia-thermal-rich"
    },
    {
        "title": "Avene Hydrance Rich",
        "price": "135 kr.",
        "store": "Apoteket",
        "link": "https://apoteket.dk/avene-hydrance-rich"
    }
]

print("🧪 Mock-produkt-output:\n")
print(format_products(mock_products))
