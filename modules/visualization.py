# modules/visualization.py

def formatar_moeda(valor):
    """
    Formata um número para o padrão monetário brasileiro (R$).
    Exemplo: 1234.56 -> R$ 1.234,56
    """
    if valor is None:
        return "R$ 0,00"
    # A mágica do replace é para trocar o ponto pela vírgula e vice-versa de forma segura.
    return f"R$ {valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".")
