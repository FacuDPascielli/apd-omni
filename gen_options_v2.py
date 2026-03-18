import unicodedata
import re

raw_list = [
    "9 de Julio", "25 de Mayo", "A. Alsina", "Adolfo Gonzales Chaves", "Alberti", "A. Brown", "Arrecifes", "Avellaneda", "Ayacucho", "Azul", "B. Blanca", "Balcarce", "Baradero", "Berazategui", "Berisso", "Bolívar", "Bragado", "Campana", "Ca#uelas", "C. Sarmiento", "C. Casares", "C. Tejedor", "C. de Areco", "Castelli", "Chacabuco", "Chascomús", "Chivilcoy", "Colón", "Coronel Brandsen", "C. Dorrego", "C. Pringles", "C. Rosales", "C. Suárez", "Daireaux", "Dolores", "Ensenada", "Escobar", "E. Echeverría", "E. de la Cruz", "Ezeiza", "F. Ameghino", "F. Varela", "G. Alvarado", "G. Alvear", "G. Arenales", "G. Belgrano", "G. Chaves", "G. Guido", "G. LaMadrid", "G. Las Heras", "G. Lavalle", "G. Madariaga", "G. Paz", "G. Pinto", "G. Pueyrredón", "G. Rodríguez", "G. San Martín", "G. Sarmiento", "G. Viamonte", "G. Villegas", "Guaminí", "H. Yrigoyen", "Hurlingham", "Ituzaingó", "José C. Paz", "Junín", "L. N. Alem", "La Costa", "La Matanza", "La Plata", "Lanús", "Laprida", "Las Flores", "Leandro N. Alem", "Lincoln", "Lobería", "Lobos", "L de Zamora", "Luján", "Magdalena", "Maipú", "Malvinas Arg.", "M. Chiquita", "Marcos Paz", "Mercedes", "Merlo", "Monte", "M. Hermoso", "Moreno", "Morón", "Navarro", "Necochea", "Olavarría", "Pehuajó", "Pellegrini", "Pergamino", "Pila", "Pilar", "Pinamar", "Pte. Perón", "Puan", "Punta Indio", "Quilmes", "Ramallo", "Rauch", "Rivadavia", "Rojas", "R. Pérez", "Saavedra", "Saladillo", "Salliqueló", "Salto", "S. A. de Giles", "S. A. de Areco", "San Cayetano", "San Fernando", "San Isidro", "San Miguel", "San Nicolás", "San Pedro", "San Vicente", "Suipacha", "Tandil", "Tapalqué", "Tigre", "Tordillo", "Tornquist", "T. Lauquen", "Tres Arroyos", "T. de Febrero", "Tres Lomas", "V. Gesell", "Villarino", "V. López", "Zárate"
]

def limpiar_texto_abc(texto):
    if not texto:
        return ""
    texto = str(texto).strip().upper()
    texto = re.sub(r'CA[^A-Z0-9]?UELAS', 'CANUELAS', texto)
    texto = texto.replace("CAÑUELAS", "CANUELAS")
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.encode('ascii', 'ignore').decode("utf-8")
    if texto == "9 DE JULIO":
        texto = "N DE JULIO"
    elif "JOSE C" in texto and "PAZ" in texto:
        texto = "JOSE C PAZ"
    texto = texto.replace(".", " ").replace(",", " ")
    texto = re.sub(r'\s+', ' ', texto).strip()
    texto = texto.replace("CANUELAS", "CAÑUELAS")
    return texto

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
    
    val = limpiar_texto_abc(item)
    options.append(f'                        <option value="{val}">{display}</option>')

with open("options_mapped_v2.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(options))
print("done v2")
