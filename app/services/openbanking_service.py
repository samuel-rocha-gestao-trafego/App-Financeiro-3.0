"""
Serviço Open Banking (Esqueleto para integração futura)

Pode ser expandido para:
- Consistência de saldo bancário via API
- Importação automática de extratos
- Conciliação automática de lançamentos
"""


class OpenBankingService:
    """Serviço de integração bancária via Open Banking."""

    @staticmethod
    def fetch_account_statement(user_id, account_id):
        """Busca extrato bancário via API Open Banking."""
        # TODO: Implementar integração com Open Banking
        return None

    @staticmethod
    def auto_reconcile_transactions(user_id, account_id):
        """Reconcilia automaticamente lançamentos com extrato bancário."""
        # TODO: Implementar reconciliação automática
        return None

    @staticmethod
    def get_available_banks():
        """Retorna lista de bancos disponíveis para integração."""
        return [
            {"code": "001", "name": "Banco do Brasil"},
            {"code": "237", "name": "Bradesco"},
            {"code": "341", "name": "Itaú"},
            {"code": "104", "name": "Caixa"},
            {"code": "260", "name": "Nubank"},
            {"code": "077", "name": "Banco Inter"},
        ]
