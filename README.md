# BarberFlow

Sistema web de gerenciamento de agendamentos para barbearias, desenvolvido com Django.

## Sobre o projeto

O BarberFlow permite que clientes realizem agendamentos e acompanhem seus horários, enquanto a equipe da barbearia pode gerenciar, confirmar, editar e cancelar os agendamentos.

## Funcionalidades

### Para clientes

- Criar agendamentos;
- Escolher serviço, barbeiro, data e horário;
- Visualizar os próprios agendamentos;
- Alterar data e horário de um agendamento;
- Cancelar um agendamento;
- Acompanhar o status do agendamento.

### Para a equipe

- Acessar o painel de agendamentos;
- Visualizar os agendamentos dos clientes;
- Confirmar agendamentos;
- Editar agendamentos;
- Cancelar agendamentos;
- Gerenciar serviços e barbeiros.

## Status dos agendamentos

- **Pendente:** aguardando confirmação da equipe;
- **Confirmado:** aprovado pela equipe;
- **Cancelado:** agendamento cancelado;
- **Concluído:** atendimento finalizado.

## Tecnologias utilizadas

- Python;
- Django;
- SQLite durante o desenvolvimento;
- HTML5;
- CSS3;
- Bootstrap;
- JavaScript;
- HTMX.

## Estrutura principal

```text
barberflow/
├── apps/
│   ├── agendamentos/
│   ├── profissionais/
│   └── servicos/
├── config/
├── static/
├── templates/
├── manage.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Como executar o projeto

### 1. Clone o repositório

```bash
git clone URL_DO_REPOSITORIO
cd barberflow
```

Substitua `URL_DO_REPOSITORIO` pelo endereço real do repositório.

### 2. Crie o ambiente virtual

No Windows:

```powershell
python -m venv venv
```

### 3. Ative o ambiente virtual

No PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Caso o ambiente virtual já esteja ativo, o terminal exibirá algo semelhante a:

```text
(venv) PS E:\barberflow>
```

### 4. Instale as dependências

```powershell
pip install -r requirements.txt
```

### 5. Execute as migrações

```powershell
python manage.py migrate
```

### 6. Crie um usuário administrador

```powershell
python manage.py createsuperuser
```

Informe o nome de usuário, e-mail e senha solicitados.

### 7. Verifique o projeto

```powershell
python manage.py check
```

### 8. Inicie o servidor

```powershell
python manage.py runserver
```

Acesse no navegador:

```text
http://127.0.0.1:8000/
```

O painel administrativo do Django fica disponível em:

```text
http://127.0.0.1:8000/admin/
```

## Desenvolvimento

Para atualizar as dependências instaladas no ambiente virtual:

```powershell
pip freeze > requirements.txt
```

Depois de alterar modelos, crie e aplique as migrações:

```powershell
python manage.py makemigrations
python manage.py migrate
```

## Testes

Para executar os testes do projeto:

```powershell
python manage.py test
```

## Segurança

Durante o desenvolvimento, algumas configurações podem utilizar valores locais. Antes de publicar o projeto em produção:

- Altere a `SECRET_KEY`;
- Desative `DEBUG`;
- Configure corretamente `ALLOWED_HOSTS`;
- Utilize variáveis de ambiente;
- Configure um banco de dados apropriado;
- Não publique senhas, tokens ou chaves de API;
- Mantenha o arquivo `.env` fora do Git.

## Status do projeto

Em desenvolvimento.

## Licença

Este projeto ainda não possui uma licença definida.
