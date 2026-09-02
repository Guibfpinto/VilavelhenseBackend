from datetime import datetime

def calcular_idade(data_nasc_str, data_base_str=None):
    if not data_nasc_str:
        return None
    try:
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
            try:
                nasc = datetime.strptime(str(data_nasc_str).strip(), fmt)
                break
            except:
                continue
        else:
            return None
        if data_base_str:
            for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y"):
                try:
                    base = datetime.strptime(str(data_base_str).strip(), fmt)
                    break
                except:
                    continue
            else:
                base = datetime.now()
        else:
            base = datetime.now()
        idade = base.year - nasc.year - ((base.month, base.day) < (nasc.month, nasc.day))
        return idade
    except:
        return None