from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField, IntegerField, TextAreaField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Optional, NumberRange, Length


class AccountForm(FlaskForm):
    name = StringField('Nome da Conta', validators=[DataRequired(), Length(max=80)])
    account_type = SelectField('Tipo de Conta', choices=[
        ('Banco', 'Banco'),
        ('Carteira', 'Carteira'),
        ('Dinheiro', 'Dinheiro'),
        ('Pix', 'Pix'),
        ('Mercado Pago', 'Mercado Pago'),
        ('Nubank', 'Nubank'),
        ('Outros', 'Outros')
    ], validators=[DataRequired()])
    initial_balance = DecimalField('Saldo Inicial', default=0.0, validators=[Optional()])
    color = StringField('Cor (Hex)', default='#0d6efd', validators=[DataRequired(), Length(max=7)])
    icon = StringField('Ícone (Bootstrap Icons)', default='bi-wallet2', validators=[DataRequired()])
    submit = SubmitField('Salvar Conta')


class CategoryForm(FlaskForm):
    name = StringField('Nome da Categoria', validators=[DataRequired(), Length(max=80)])
    type = SelectField('Tipo', choices=[('RECEITA', 'Receita'), ('DESPESA', 'Despesa')], validators=[DataRequired()])
    color = StringField('Cor', default='#6c757d', validators=[DataRequired(), Length(max=7)])
    icon = StringField('Ícone', default='bi-tag', validators=[DataRequired()])
    monthly_limit = DecimalField('Limite Mensal (Opcional)', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Salvar Categoria')


class TransactionForm(FlaskForm):
    type = SelectField('Tipo de Lançamento', choices=[
        ('RECEITA', 'Receita'),
        ('DESPESA', 'Despesa'),
        ('TRANSFERENCIA', 'Transferência')
    ], validators=[DataRequired()])
    description = StringField('Descrição', validators=[DataRequired(), Length(max=150)])
    amount = DecimalField('Valor (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    date = DateField('Data', validators=[DataRequired()])
    account_id = SelectField('Conta', coerce=int, validators=[DataRequired()])
    category_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    status = SelectField('Status', choices=[('PAGO', 'Pago / Concluído'), ('PENDENTE', 'Pendente')], validators=[DataRequired()])
    notes = TextAreaField('Observações', validators=[Optional()])
    submit = SubmitField('Salvar Lançamento')


class CreditCardForm(FlaskForm):
    name = StringField('Nome do Cartão', validators=[DataRequired(), Length(max=80)])
    bank = StringField('Banco Emissor', validators=[DataRequired(), Length(max=80)])
    credit_limit = DecimalField('Limite Total (R$)', validators=[DataRequired(), NumberRange(min=0)])
    closing_day = IntegerField('Dia do Fechamento', validators=[DataRequired(), NumberRange(min=1, max=31)])
    due_day = IntegerField('Dia do Vencimento', validators=[DataRequired(), NumberRange(min=1, max=31)])
    color = StringField('Cor', default='#000000', validators=[DataRequired(), Length(max=7)])
    submit = SubmitField('Salvar Cartão')


class CardPurchaseForm(FlaskForm):
    description = StringField('Descrição da Compra', validators=[DataRequired(), Length(max=150)])
    total_amount = DecimalField('Valor Total (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    installments_count = IntegerField('Número de Parcelas', default=1, validators=[DataRequired(), NumberRange(min=1, max=72)])
    purchase_date = DateField('Data da Compra', validators=[DataRequired()])
    category_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    submit = SubmitField('Registrar Compra')


class GoalForm(FlaskForm):
    name = StringField('Nome da Meta', validators=[DataRequired(), Length(max=100)])
    target_amount = DecimalField('Valor Objetivo (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    current_amount = DecimalField('Valor Já Acumulado (R$)', default=0.0, validators=[Optional()])
    target_date = DateField('Data Prevista', validators=[DataRequired()])
    description = TextAreaField('Descrição', validators=[Optional()])
    submit = SubmitField('Salvar Meta')


class RecurringBillForm(FlaskForm):
    description = StringField('Descrição da Conta', validators=[DataRequired(), Length(max=150)])
    amount = DecimalField('Valor (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    frequency = SelectField('Periodicidade', choices=[('MENSAL', 'Mensal'), ('SEMANAL', 'Semanal'), ('ANUAL', 'Anual')], validators=[DataRequired()])
    due_day = IntegerField('Dia do Vencimento', validators=[DataRequired(), NumberRange(min=1, max=31)])
    start_date = DateField('Data Inicial', validators=[DataRequired()])
    category_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    account_id = SelectField('Conta Padrão', coerce=int, validators=[Optional()])
    submit = SubmitField('Salvar Conta Recorrente')


class BudgetForm(FlaskForm):
    category_id = SelectField('Categoria', coerce=int, validators=[DataRequired()])
    month = IntegerField('Mês', validators=[DataRequired(), NumberRange(min=1, max=12)])
    year = IntegerField('Ano', validators=[DataRequired(), NumberRange(min=2020, max=2100)])
    planned_amount = DecimalField('Valor Planejado (R$)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Definir Orçamento')