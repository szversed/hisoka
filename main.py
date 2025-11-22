# celestial.py
import discord
from discord.ext import commands
import json
import os
from flask import Flask
from threading import Thread

# Keep Alive Server
web_server = Flask('')

@web_server.route('/')
def home():
    return "✅ Celestial Bot Online - Desenvolvido para Discord"

def run_web():
    web_server.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run_web)
    t.daemon = True
    t.start()

# Bot Code
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

# -------------------------
# Configurações / dados
# -------------------------
gula_role_name = "gula"
cargos = {
    "preguiça": 50,
    "luxúria": 500,
    "avareza": 5500,
    "inveja": 40000
}

MENSAGENS_FILE = "mensagens.json"

if os.path.exists(MENSAGENS_FILE):
    with open(MENSAGENS_FILE, "r", encoding="utf-8") as f:
        try:
            mensagens = json.load(f)
        except Exception:
            mensagens = {}
else:
    mensagens = {}

# -------------------------
# Utilitárias
# -------------------------
def tem_cargo_soberba(member: discord.Member) -> bool:
    try:
        return discord.utils.get(member.roles, name="soberba") is not None
    except Exception:
        return False

async def aplicar_gula(member: discord.Member):
    role = discord.utils.get(member.guild.roles, name=gula_role_name)
    if role is None:
        try:
            role = await member.guild.create_role(name=gula_role_name, reason="Criando role inicial gula")
        except Exception:
            role = None
    if role and role not in member.roles:
        try:
            await member.add_roles(role)
        except Exception:
            pass

async def aplicar_cargos(member: discord.Member):
    if member.bot or tem_cargo_soberba(member):
        return
    user_count = mensagens.get(str(member.id), 0)
    for nome, quantidade in cargos.items():
        role = discord.utils.get(member.guild.roles, name=nome)
        if role is None:
            try:
                role = await member.guild.create_role(name=nome, reason="Criando role de milestone")
            except Exception:
                role = None
        if role and user_count >= quantidade and role not in member.roles:
            try:
                await member.add_roles(role)
            except Exception:
                pass
            canal = discord.utils.get(member.guild.text_channels, name="confessionário")
            if not canal and member.guild.text_channels:
                canal = member.guild.text_channels[0]
            if canal:
                embed = discord.Embed(
                    title="🎉 novo cargo conquistado!",
                    description=f"{member.mention} subiu para o cargo **{nome}**!",
                    color=discord.Color.green()
                )
                try:
                    await canal.send(embed=embed)
                except Exception:
                    pass

def salvar_mensagens():
    try:
        with open(MENSAGENS_FILE, "w", encoding="utf-8") as f:
            json.dump(mensagens, f)
    except Exception:
        pass

# -------------------------
# COMANDOS TRADICIONAIS (PREFIXO .)
# -------------------------
@bot.command(name="contador")
async def contador(ctx, usuario: discord.Member = None):
    """Mostra quantas mensagens um usuário enviou (ou você se omitido)."""
    if usuario is None:
        usuario = ctx.author
    count = mensagens.get(str(usuario.id), 0)
    embed = discord.Embed(
        title="📊 contador de mensagens",
        description=f"{usuario.mention} enviou **{count}** mensagens.",
        color=discord.Color.blurple()
    )
    await ctx.send(embed=embed)

@bot.command(name="rank")
async def rank(ctx):
    """Top 10 mensagens (apenas usuários presentes no servidor)."""
    # Filtra apenas usuários que estão no servidor
    ranking_filtrado = []

    for user_id, count in mensagens.items():
        member = ctx.guild.get_member(int(user_id))
        if member is not None and not member.bot:  # Apenas membros presentes e não bots
            ranking_filtrado.append((user_id, count, member.display_name))

    # Ordena por quantidade de mensagens
    ranking_filtrado.sort(key=lambda x: x[1], reverse=True)

    # Pega os top 10
    top_10 = ranking_filtrado[:10]

    embed = discord.Embed(title="🏆 Top 10 — mensagens", color=discord.Color.gold())

    if not top_10:
        embed.description = "nenhuma mensagem registrada ainda."
    else:
        texto = ""
        for i, (user_id, count, display_name) in enumerate(top_10, start=1):
            texto += f"{i}. **{display_name}** — {count} mensagens\n"
        embed.description = texto

        # Adiciona estatísticas no footer
        total_membros = len([m for m in ctx.guild.members if not m.bot])
        embed.set_footer(text=f"Mostrando {len(top_10)} de {len(ranking_filtrado)} membros ativos")

    await ctx.send(embed=embed)

@bot.command(name="limparinativos")
@commands.has_permissions(administrator=True)
async def limpar_inativos(ctx):
    """[ADMIN] Remove usuários que não estão mais no servidor do contador"""
    usuarios_removidos = 0

    # Cria uma cópia para iterar
    user_ids = list(mensagens.keys())

    for user_id in user_ids:
        member = ctx.guild.get_member(int(user_id))
        if member is None:  # Usuário não está mais no servidor
            del mensagens[user_id]
            usuarios_removidos += 1

    salvar_mensagens()

    embed = discord.Embed(
        title="🧹 Limpeza de Inativos",
        description=f"**{usuarios_removidos}** usuários removidos do contador.",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed)

# -------------------------
# Eventos
# -------------------------
@bot.event
async def on_ready():
    print(f"✅ {bot.user} está online (Celestial).")
    print(f"📝 Prefixo: .")
    print(f"🔧 Comandos disponíveis: .contador, .rank, .limparinativos")

    for guild in bot.guilds:
        for member in guild.members:
            try:
                await aplicar_gula(member)
                await aplicar_cargos(member)
            except Exception:
                pass

@bot.event
async def on_member_join(member: discord.Member):
    try:
        await aplicar_gula(member)
    except Exception:
        pass

@bot.event
async def on_member_remove(member: discord.Member):
    """Opcional: Remove usuário do contador quando sai do servidor"""
    # Se quiser remover automaticamente quando sair, descomente as linhas abaixo:
    # user_id = str(member.id)
    # if user_id in mensagens:
    #     del mensagens[user_id]
    #     salvar_mensagens()
    pass

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    user_id = str(message.author.id)
    mensagens[user_id] = mensagens.get(user_id, 0) + 1
    try:
        await aplicar_cargos(message.author)
    except Exception:
        pass
    salvar_mensagens()
    await bot.process_commands(message)

# -------------------------
# Run com Keep Alive
# -------------------------
if __name__ == "__main__":
    keep_alive()
    token = os.getenv("TOKEN")
    if not token:
        print("❌ ERRO: variável TOKEN não encontrada.")
    else:
        bot.run(token)
