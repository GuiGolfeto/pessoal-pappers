# pessoal-pappers

Scraper diário de papers de IA que coleta publicações do arXiv (cs.AI e cs.LG) e do HuggingFace Daily Papers, traduz os resumos para português e envia um e-mail formatado automaticamente ao ligar o PC.

## Como funciona

1. Ao iniciar a sessão, o script `scraper.py` é executado automaticamente via autostart do GNOME.
2. Verifica no banco de dados se o e-mail já foi enviado hoje — se sim, encerra sem fazer nada.
3. Busca até 3 papers novos de cada fonte (arXiv cs.AI, arXiv cs.LG, HuggingFace).
4. Traduz títulos e resumos para PT-BR via Google Translate.
5. Monta um e-mail HTML responsivo com os papers agrupados por fonte.
6. Envia para o próprio e-mail via Gmail SMTP e salva os papers no banco para evitar repetição.
7. Exibe uma notificação desktop com o resultado.

## Fontes

| Fonte | Feed |
|---|---|
| arXiv cs.AI | `https://rss.arxiv.org/rss/cs.AI` |
| arXiv cs.LG | `https://rss.arxiv.org/rss/cs.LG` |
| HuggingFace Daily Papers | `https://huggingface.co/api/daily_papers` |

## Requisitos

- Python 3.10+
- PostgreSQL (Neon, Supabase, Railway ou local)
- Conta Gmail com [senha de app](https://myaccount.google.com/apppasswords) habilitada

## Instalação

```bash
git clone <repo>
cd pessoal-pappers

# Copie e preencha as variáveis de ambiente
cp .env_example .env
# Edite .env com seu DATABASE_URL e EMAIL_PASSWORD

# Instala dependências e registra no autostart do GNOME
bash setup.sh
```

## Variáveis de ambiente

Crie um arquivo `.env` baseado em `.env_example`:

```env
# Banco de dados PostgreSQL (ex: Neon, Supabase, Railway)
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require

# Email para envio dos papers (Gmail)
EMAIL_FROM=seuemail@gmail.com

# Senha de app do Gmail (gerada em: Conta Google > Segurança > Senhas de app)
EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
```

## Execução manual

```bash
.venv/bin/python scraper.py
```

## Banco de dados

O script cria as tabelas automaticamente na primeira execução:

- `sent_papers` — papers já enviados (evita duplicatas entre dias)
- `daily_log` — registro de datas em que o e-mail foi enviado (garante envio único por dia)

## Dependências

```
feedparser
requests
python-dotenv
psycopg2-binary
deep-translator
```
