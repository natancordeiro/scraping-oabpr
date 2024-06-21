from bot import Bot
from ext.functions import create_excel_file

bot = Bot(False)
bot.open_oab()

create_excel_file()

total_paginas = bot.get_last_page()
total_advogados = total_paginas / 15


for pagina in total_paginas:
    bot.process_page(pagina)
