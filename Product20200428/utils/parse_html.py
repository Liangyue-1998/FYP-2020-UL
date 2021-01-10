"""
Principle.htm 文件替换字符串
<link rel=File-List href="Principle_files/filelist.xml">
"""

import re


file_path = "Principle.htm"
with open(file_path) as f:
    text = f.read()

    results = re.findall(r'src="Principle_files/(.*?)"', text)
    for i in results:
        source = 'src="Principle_files/{}"'.format(i)
        fin = 'src="{% static ' + '\'Principle_files/{}\''.format(i) + ' %}"'
        text = text.replace(source, fin)

with open('new.html', 'w') as f:
    f.write(text)