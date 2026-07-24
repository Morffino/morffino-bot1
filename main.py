import asyncio
import discord
from discord import app_commands
from discord.ext import commands

# Инициализация бота
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)


# --- Модальное окно (Форма ввода) ---
class TicketModal(discord.ui.Modal):

    def __init__(self, category_name: str):
        super().__init__(title=f"Тикет: {category_name}")
        self.category_name = category_name

        self.steam_id = discord.ui.TextInput(
            label="Укажите ваш SteamID64",
            placeholder="Можно узнать тут: https://steamid.io",
            required=True,
            max_length=100,
        )

        self.nickname = discord.ui.TextInput(
            label="Ваш ник в игре",
            placeholder="Укажите игровой ник",
            required=False,
            max_length=100,
        )

        self.problem = discord.ui.TextInput(
            label="Кратко о проблеме",
            placeholder="До 30 символов",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=500,
        )

        self.add_item(self.steam_id)
        self.add_item(self.nickname)
        self.add_item(self.problem)

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        user = interaction.user

        # Права доступа к создаваемому каналу
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                read_messages=False
            ),
            user: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
            guild.me: discord.PermissionOverwrite(
                read_messages=True, send_messages=True
            ),
        }

        # Создание приватного канала тикета
        clean_username = user.name.lower().replace(" ", "-")
        channel_name = f"ticket-{clean_username}"

        ticket_channel = await guild.create_text_channel(
            name=channel_name, overwrites=overwrites, reason=f"Тикет от {user}"
        )

        # Содержимое первого сообщения в тикете
        embed = discord.Embed(
            title=f"Тикет: {self.category_name}",
            description=(
                f"**Создатель:** {user.mention}\n\n"
                f"**SteamID64:** `{self.steam_id.value}`\n"
                f"**Игровой ник:** `{self.nickname.value or 'Не указан'}`\n"
                f"**Описание проблемы:**\n{self.problem.value}"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(
            text="Ожидайте ответа администрации. Чтобы закрыть тикет, нажмите кнопку ниже."
        )

        await ticket_channel.send(
            content=f"{user.mention}, ваш тикет создан!",
            embed=embed,
            view=CloseTicketView(),
        )

        # Ответ пользователю, нажавшему на кнопку
        await interaction.response.send_message(
            f"✅ Ваш тикет успешно создан: {ticket_channel.mention}",
            ephemeral=True,
        )


# --- Кнопка закрытия тикета ---
class CloseTicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Закрыть тикет",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="close_ticket_btn",
    )
    async def close_ticket(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "🔒 Тикет будет удален через 5 секунд..."
        )
        await asyncio.sleep(5)
        await interaction.channel.delete()


# --- Главная панель с кнопками категорий ---
class TicketView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Общие вопросы",
        emoji="❓",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_general",
    )
    async def general_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(TicketModal("Общие вопросы"))

    @discord.ui.button(
        label="Восстановление вещей",
        emoji="📦",
        style=discord.ButtonStyle.success,
        custom_id="btn_restore",
    )
    async def restore_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            TicketModal("Восстановление вещей")
        )

    @discord.ui.button(
        label="Технические проблемы",
        emoji="🛠",
        style=discord.ButtonStyle.primary,
        custom_id="btn_tech",
    )
    async def tech_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            TicketModal("Технические проблемы")
        )

    @discord.ui.button(
        label="Жалоба на игрока/группировку",
        emoji="⚠️",
        style=discord.ButtonStyle.danger,
        custom_id="btn_player",
    )
    async def player_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            TicketModal("Жалоба на игрока/группировку")
        )

    @discord.ui.button(
        label="Жалоба на Администрацию",
        emoji="🛡",
        style=discord.ButtonStyle.secondary,
        custom_id="btn_admin",
    )
    async def admin_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            TicketModal("Жалоба на Администрацию")
        )


# --- События бота ---
@bot.event
async def on_ready():
    # Регистрация Views для поддержания работы кнопок после перезапуска
    bot.add_view(TicketView())
    bot.add_view(CloseTicketView())
    print(f"Бот {bot.user} успешно запущен и готов к работе!")


# --- Команда отправки интерактивного меню ---
@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx: commands.Context):
    """Команда для создания сообщения с тикетами (только для админов)"""
    embed = discord.Embed(
        title="HS TICKET | Центр поддержки",
        description=(
            "Нужна помощь, восстановление предметов или хотите подать жалобу?\n"
            "Выберите подходящую тему кнопкой ниже и заполните форму на обращение.\n\n"
            "**Важно:** создавайте тикет только по назначению — его увидит нужная команда.\n\n"
            "❓ **Общие вопросы**\nВопросы по серверу, правилам и игровому процессу.\n\n"
            "📦 **Восстановление вещей**\nПотеря имущества, откаты, спорные ситуации.\n\n"
            "🛠 **Технические проблемы**\nОшибки, вылеты, проблемы с подключением.\n\n"
            "⚠️ **Жалоба на игрока/группировку**\nНарушения игроков, группировок, правил.\n\n"
            "🛡 **Жалоба на Администрацию**\nОбращения по действиям администрации."
        ),
        color=discord.Color.dark_theme(),
    )
    embed.set_footer(text="HS TICKET")

    await ctx.send(embed=embed, view=TicketView())
    await ctx.message.delete()


# Токен вашего бота (ЗАМЕНИТЕ НА НОВЫЙ ТОКЕН ИЗ DISCORD DEVELOPER PORTAL)
TOKEN = "MTUzMDAwMTkxNzMxNTM4NzQ2Mw.GcmeH8.KFWgn8BscO7tx1CkA-WZ3uzoHhsdx_ZVsTyWI8"

if __name__ == "__main__":
    bot.run(TOKEN)
