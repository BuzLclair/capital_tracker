

def clean_pct_number(number, txt_before, txt_after):
    number_clean = round(100*number, 2)
    if number_clean < 0:
        number_as_txt = str(number_clean)
    else:
        number_as_txt = f'+{number_clean}'
    return f'{txt_before}{number_as_txt}{txt_after}'
