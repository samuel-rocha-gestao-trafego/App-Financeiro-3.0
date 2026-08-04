"""
Serviço Google Gemini AI (Esqueleto para integração futura).

Dependência necessária: google-generativeai

Para implementar:
1. Instalar: pip install google-generativeai
2. Configurar chave API no .env como GEMINI_API_KEY
3. Implementar os métodos abaixo

Funcionalidades planeadas:
- Análise inteligente de padrões de gastos
- Sugestões de orçamento baseadas em histórico
- Alertas proativos sobre anomalias financeiras
- Relatórios semanais/mensais gerados por IA
"""

import os


class GeminiService:
    """Serviço de análise financeira inteligente via Google Gemini AI."""

    def __init__(self):
        """Inicializa o serviço com a chave API."""
        # TODO: Carregar API_KEY do .env
        # self.api_key = os.getenv('GEMINI_API_KEY')
        # import google.generativeai as genai
        # genai.configure(api_key=self.api_key)
        # self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.api_key = None

    def analyze_spending_patterns(self, user_id: int) -> str:
        """
        Analisa padrões de gastos do utilizador e gera insights.

        Args:
            user_id: ID do utilizador para buscar transações.

        Returns:
            Texto com análise de padrões e recomendações.
        """
        # TODO: Implementar
        # 1. Buscar transações dos últimos 3 meses
        # 2. Agrupar por categoria e calcular médias
        # 3. Montar prompt para Gemini com dados agregados
        # 4. Enviar para API e retornar resposta formatada
        pass

    def generate_budget_suggestions(self, user_id: int) -> dict:
        """
        Gera sugestões de orçamento baseadas no histórico financeiro.

        Args:
            user_id: ID do utilizador.

        Returns:
            Dict com categorias e valores sugeridos para o orçamento.
        """
        # TODO: Implementar
        # 1. Analisar histórico de gastos por categoria
        # 2. Calcular médias e tendências
        # 3. Solicitar ao Gemini sugestões de limites por categoria
        # 4. Retornar como dict {categoria: valor_sugerido}
        pass

    def detect_anomalies(self, user_id: int) -> list:
        """
        Detecta anomalias nos gastos (transações atípicas).

        Args:
            user_id: ID do utilizador.

        Returns:
            Lista de transações identificadas como anomalias.
        """
        # TODO: Implementar
        # 1. Buscar transações recentes
        # 2. Calcular médias por categoria
        # 3. Identificar transações que excedem significativamente a média
        # 4. Usar Gemini para contextualizar anomalias
        # 5. Retornar lista formatada
        pass

    def generate_monthly_report(self, user_id: int, month: int, year: int) -> str:
        """
        Gera relatório mensal completo com análise de IA.

        Args:
            user_id: ID do utilizador.
            month: Mês do relatório.
            year: Ano do relatório.

        Returns:
            Texto formatado com relatório completo.
        """
        # TODO: Implementar
        # 1. Buscar todas as transações do mês
        # 2. Calcular totais por categoria
        # 3. Comparar com mês anterior
        # 4. Montar prompt completo para Gemini
        # 5. Retornar relatório gerado
        pass
