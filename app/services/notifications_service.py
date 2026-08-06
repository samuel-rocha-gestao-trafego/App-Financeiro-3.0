"""
Serviço de Notificações (Esqueleto para integração futura)

Pode ser expandido para:
- Email (via Flask-Mail)
- Push notifications
- Webhooks
- Telegram/WhatsApp bot
"""


class NotificationsService:
    """Serviço de notificações do sistema."""

    @staticmethod
    def notify_bill_due(user_id, bill_description, amount, due_day):
        """Notifica sobre conta recorrente próxima do vencimento."""
        # TODO: Implementar envio de notificação
        pass

    @staticmethod
    def notify_budget_warning(user_id, category_name, percentage):
        """Notifica quando orçamento atinge percentual crítico."""
        # TODO: Implementar envio de notificação
        pass

    @staticmethod
    def notify_monthly_summary(user_id):
        """Envia resumo mensal para o utilizador."""
        # TODO: Implementar envio de notificação
        pass
