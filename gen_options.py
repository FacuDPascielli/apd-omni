import unicodedata

raw_list = [
    "9 de Julio", "25 de Mayo", "A. Alsina", "Adolfo Gonzales Chaves", "Alberti", "A. Brown", "Arrecifes", "Avellaneda", "Ayacucho", "Azul", "B. Blanca", "Balcarce", "Baradero", "Berazategui", "Berisso", "Bolívar", "Bragado", "Campana", "Ca#uelas", "C. Sarmiento", "C. Casares", "C. Tejedor", "C. de Areco", "Castelli", "Chacabuco", "Chascomús", "Chivilcoy", "Colón", "Coronel Brandsen", "C. Dorrego", "C. Pringles", "C. Rosales", "C. Suárez", "Daireaux", "Dolores", "Ensenada", "Escobar", "E. Echeverría", "E. de la Cruz", "Ezeiza", "F. Ameghino", "F. Varela", "G. Alvarado", "G. Alvear", "G. Arenales", "G. Belgrano", "G. Chaves", "G. Guido", "G. LaMadrid", "G. Las Heras", "G. Lavalle", "G. Madariaga", "G. Paz", "G. Pinto", "G. Pueyrredón", "G. Rodríguez", "G. San Martín", "G. Sarmiento", "G. Viamonte", "G. Villegas", "Guaminí", "H. Yrigoyen", "Hurlingham", "Ituzaingó", "José C. Paz", "Junín", "L. N. Alem", "La Costa", "La Matanza", "La Plata", "Lanús", "Laprida", "Las Flores", "Leandro N. Alem", "Lincoln", "Lobería", "Lobos", "L de Zamora", "Luján", "Magdalena", "Maipú", "Malvinas Arg.", "M. Chiquita", "Marcos Paz", "Mercedes", "Merlo", "Monte", "M. Hermoso", "Moreno", "Morón", "Navarro", "Necochea", "Olavarría", "Pehuajó", "Pellegrini", "Pergamino", "Pila", "Pilar", "Pinamar", "Pte. Perón", "Puan", "Punta Indio", "Quilmes", "Ramallo", "Rauch", "Rivadavia", "Rojas", "R. Pérez", "Saavedra", "Saladillo", "Salliqueló", "Salto", "S. A. de Giles", "S. A. de Areco", "San Cayetano", "San Fernando", "San Isidro", "San Miguel", "San Nicolás", "San Pedro", "San Vicente", "Suipacha", "Tandil", "Tapalqué", "Tigre", "Tordillo", "Tornquist", "T. Lauquen", "Tres Arroyos", "T. de Febrero", "Tres Lomas", "V. Gesell", "Villarino", "V. López", "Zárate"
]

def clean_value(s):
    s = s.upper().replace(".", "")
    mapping = {
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U"
    }
    for k, v in mapping.items():
        s = s.replace(k, v)
    return s.strip()

options = []
for item in raw_list:
    display = item
    if display == "A. Brown": display = "Almirante Brown"
    elif display == "E. Echeverría": display = "Esteban Echeverría"
    elif display == "F. Varela": display = "Florencio Varela"
    elif display == "Pte. Perón": display = "Presidente Perón"
    elif display == "L de Zamora": display = "Lomas de Zamora"
    elif display == "Ca#uelas": display = "Cañuelas"
    elif display == "T. de Febrero": display = "Tres de Febrero"
    
    val = clean_value(item)
    options.append(f'                        <option value="{val}">{display}</option>')

with open("options_mapped.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(options))
print("done")
