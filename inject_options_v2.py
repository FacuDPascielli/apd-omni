import re

with open("options_mapped_v2.txt", "r", encoding="utf-8") as f:
    options_html = f.read()

with open("index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Replace searchDistrito options
search_pattern = re.compile(r'(<select id="searchDistrito" class="form-control">\s*<option value="Todos">Todos los distritos</option>).*?(</select>)', re.DOTALL)
html_content = search_pattern.sub(r'\1\n' + options_html + r'\n                    \2', html_content)

# Replace freeDistrito options
free_pattern = re.compile(r'(<select id="freeDistrito" class="form-control" required>\s*<option value="" disabled selected>Selecciona un distrito</option>).*?(</select>)', re.DOTALL)
html_content = free_pattern.sub(r'\1\n' + options_html + r'\n                    \2', html_content)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(html_content)
print("replaced options v2 successfully")
