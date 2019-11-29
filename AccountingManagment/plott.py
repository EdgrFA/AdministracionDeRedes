import json
import pandas as pd
import matplotlib.pyplot as plt, mpld3
from mpld3 import plugins

with open('graficarJson.json') as file:
    data = json.load(file)
plt.figure(figsize=(15, 5))
plt.subplot(132)
# fig = plt.figure()

for info in data['consumodia']:
    day = info['day']
    bytes = info['paquetes']
    print(int(day), int(bytes))
    plt.scatter(int(day), int(bytes))
    # html_graph = mpld3.fig_to_html(fig)
    plt.xlabel('Dias')
    plt.ylabel('Bytes')
    # plt.savefig('plot.png')
    # fig.savefig('plot.png')

plt.savefig("hola.png")
# mpld3.show(fig)
# encoded = base64.b64encode(tmpfile.getvalue()).decode('utf-8')


plt.suptitle('Consumo por dia')
plt.show()
