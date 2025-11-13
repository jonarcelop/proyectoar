import sys
from zipfile import ZipFile
import xml.etree.ElementTree as ET

def docx_to_text(path):
    texts = []
    with ZipFile(path) as z:
        if 'word/document.xml' not in z.namelist():
            return ''
        xml = z.read('word/document.xml')
    tree = ET.fromstring(xml)
    # Word XML uses namespace; find all text elements
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    for node in tree.findall('.//w:t', ns):
        texts.append(node.text)
    return ''.join(t for t in texts if t)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python extract_docx.py path/to/file.docx')
        sys.exit(1)
    path = sys.argv[1]
    txt = docx_to_text(path)
    print(txt)
