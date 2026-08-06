"""
Serviço de Bot Telegram (Esqueleto para integração futura).

Dependência necessária: python-telegram-bot

Para implementar:
1. Instalar: pip install python-telegram-bot
2. Criar bot via @BotFather no Telegram
3. Configurar TOKEN no .env como TELEGRAM_BOT_TOKEN
4. Implementar os handlers abaixo

Funcionalidades planeadas:
- /resumo - Resumo financeiro do mês atual
- /saldo - Saldo total de todas as contas
- /lancamento - Registar novo lançamento por chat
- /alertas - Configurção de alertas de orçamento
"""

import os


class TelegramBotService:
    """Serviço de integração com Telegram para notificações e comandos financeiros."""

    def __init__(self):
        """Inicializa o serviço com o token do bot."""
        # TODO: Carregar TOKEN do .env
        # self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.token = None

    async def start(self):
        """Inicia o bot Telegram com os handlers configurados."""
        # TODO: Implementar com python-telegram-bot
        # from telegram import Update
        # from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
        #
        # application = ApplicationBuilder().token(self.token).build()
        # application.add_handler(CommandHandler("start", self.cmd_start))
        # application.add_handler(CommandHandler("resumo", self.cmd_resumo))
        # application.add_handler(CommandHandler("saldo", self.cmd_saldo))
        # application.add_handler(CommandHandler("lancamento", self.cmd_lancamento))
        # await application.run_polling()
        pass

    async def cmd_start(self, update, context):
        """Handler para /start - Boas-vindas ao utilizador."""
        # TODO: Implementar
        pass

    async def cmd_resumo(self, update, context):
        """Handler para /resumo - Envia resumo financeiro do mês."""
        # TODO: Implementar
        # - Buscar MonthlySummary do mês atual
        # - Formatar e enviar como mensagem
        pass

    async def cmd_saldo(self, update, context):
        """Handler para /saldo - Envia saldo total de todas as contas."""
        # TODO: Implementar
        # - Usar AccountService.get_total_balance(user_id)
        # - Enviar como mensagem formatada
        pass

    async def cmd_lancamento(self, update, context):
        """Handler para /lancamento - Regista novo lançamento via chat."""
        # TODO: Implementar
        # - Perguntar tipo, descrição, valor
        # - Criar via TransactionService.create_transaction()
        pass

    @staticmethod
    def send_notification(user_chat_id: int, message: str):
        """Envia notificação push para o utilizador via Telegram."""
        # TODO: Implementar envio direto de mensagem
        pass
