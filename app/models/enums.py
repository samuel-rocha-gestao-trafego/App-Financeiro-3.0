from enum import Enum as PyEnum


class PaymentMethod(PyEnum):
    """Meio de pagamento de um lançamento financeiro."""
    DINHEIRO = 'DINHEIRO'
    PIX = 'PIX'
    DEBITO = 'DEBITO'
    BOLETO = 'BOLETO'
    TRANSFERENCIA = 'TRANSFERENCIA'
    CARTAO_CREDITO = 'CARTAO_CREDITO'
    OUTROS = 'OUTROS'

    @classmethod
    def choices(cls):
        return [(m.value, m.name.replace('_', ' ').title()) for m in cls]

    @classmethod
    def from_form(cls, value: str) -> 'PaymentMethod':
        mapping = {
            'Pix / Dinheiro': cls.PIX,
            'Cartão de Crédito': cls.CARTAO_CREDITO,
            'Débito': cls.DEBITO,
            'Boleto': cls.BOLETO,
            'Outros': cls.OUTROS,
        }
        return mapping.get(value, cls.OUTROS)


class EntryStatus(PyEnum):
    """Status de previsão/realização de um lançamento."""
    PREVISTO = 'PREVISTO'
    REALIZADO = 'REALIZADO'
    CANCELADO = 'CANCELADO'


class InvoiceStatus(PyEnum):
    """Ciclo de vida da fatura do cartão de crédito."""
    ABERTA = 'ABERTA'
    FECHADA = 'FECHADA'
    PAGA = 'PAGA'
    ATRASADA = 'ATRASADA'


class Frequency(PyEnum):
    """Frequência de recorrência."""
    MENSAL = 'MENSAL'
    SEMANAL = 'SEMANAL'
    ANUAL = 'ANUAL'
    ÚNICA = 'UNICA'
