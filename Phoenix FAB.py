import discord
from discord.ext import commands
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.dm_messages = True
intents.message_content = True

# Initialize bot with case_insensitive=True
bot = commands.Bot(command_prefix='phc!', intents=intents, case_insensitive=True)

# Remove the default help command to replace it with our own
bot.remove_command('help')

# Global dictionaries and variables
submissions = {}
submission_messages = {}
submission_log = []
malware_blacklist = ['badlink.com', 'malicious.com']  # Example of blacklisted URLs

# Channel IDs as per the instructions
fan_art_channel_id = 123
confirmation_channel_id = 123
main_server_channel_id = 123
archive_channel_id = 123

# Dictionary to store user language preferences
user_language = {}

# Helper function to check if a link is valid (starts with https)
def is_valid_link(link):
    return link.startswith("https://") and all(bad_link not in link for bad_link in malware_blacklist)

# Ensure user has selected language; block other commands if language not selected
def check_language_selected(ctx):
    # Allow the 'Start' command to bypass the language check
    if ctx.command.name == 'Start':
        return True
    return ctx.author.id in user_language

@bot.check
async def ensure_language_selected(ctx):
    if not check_language_selected(ctx):
        await ctx.send("Please select your language first using `phc!Start` / لطفاً ابتدا زبان خود را با دستور `phc!Start` انتخاب کنید.", ephemeral=True)
        return False
    return True

# Function to add reactions and create a thread
async def add_reactions_and_thread(message):
    await message.add_reaction('👍')
    await message.add_reaction('👎')
    thread = await message.create_thread(name=f"Discussion: {message.id}", auto_archive_duration=60)
    await thread.send("You can discuss the fan art here! / می‌توانید درباره این فن آرت اینجا بحث کنید!")

# Advanced language selection with help commands
@bot.command(name='Start')
async def start_command(ctx):
    if ctx.author.id in user_language:
        language = user_language.get(ctx.author.id, 'EN')
        if language == 'FA':
            await ctx.send("شما قبلاً زبان خود را انتخاب کرده‌اید. لطفاً برای تغییر زبان، ابتدا از دستور `phc!Cancel` استفاده کنید.", ephemeral=True)
        else:
            await ctx.send("You have already selected a language. Please use `phc!Cancel` to reset your language selection before changing it.", ephemeral=True)
        return

    embed = discord.Embed(
        title="🔰 Language Selection & Bot Commands",
        description="Please choose your preferred language / لطفاً زبان خود را انتخاب کنید:\n"
                    "🇬🇧 - English\n"
                    "🇮🇷 - فارسی",
        color=0x00ff00
    )

    # English help commands
    english_help = (
        "🖼️ `phc!Submission` - Submit your fan art\n"
        "🔄 `phc!Swap` - Replace your submitted fan art\n"
        "🗑️ `phc!Delete` - Delete your submission\n"
        "🛑 `phc!Cancel` - Cancel any ongoing process\n"
        "🔍 `phc!Status` - Check the status of your submission\n"
        "📜 `phc!StatusLog` - View the last 10 submissions"
    )

    # Persian help commands
    persian_help = (
        "🖼️ `phc!Submission` - ارسال فن آرت شما\n"
        "🔄 `phc!Swap` - جایگزینی فن آرت ارسال شده\n"
        "🗑️ `phc!Delete` - حذف فن آرت شما\n"
        "🛑 `phc!Cancel` - لغو هر فرآیند جاری\n"
        "🔍 `phc!Status` - بررسی وضعیت اثر ارسالی شما\n"
        "📜 `phc!StatusLog` - مشاهده ۱۰ ارسال اخیر"
    )

    # Add English and Persian help commands as fields
    embed.add_field(name="🇬🇧 English Help Commands:", value=english_help, inline=False)
    embed.add_field(name="🇮🇷 دستورات فارسی:", value=persian_help, inline=False)
    embed.set_footer(text="Created By Patch_Note | Supported By Phoenix Client Team")

    await ctx.send(embed=embed, ephemeral=True)

    message = await ctx.send("Please react with 🇬🇧 for English or 🇮🇷 for فارسی", ephemeral=True)
    await message.add_reaction("🇬🇧")
    await message.add_reaction("🇮🇷")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["🇬🇧", "🇮🇷"]

    try:
        reaction, _ = await bot.wait_for('reaction_add', timeout=30.0, check=check)
        if str(reaction.emoji) == "🇬🇧":
            user_language[ctx.author.id] = 'EN'
            await ctx.send("You have selected English.", ephemeral=True)
        elif str(reaction.emoji) == "🇮🇷":
            user_language[ctx.author.id] = 'FA'
            await ctx.send("شما زبان فارسی را انتخاب کردید.", ephemeral=True)
    except asyncio.TimeoutError:
        await ctx.send("Time out. Please try again. / زمان به پایان رسید. لطفاً دوباره تلاش کنید.", ephemeral=True)

# Custom help command
@bot.command(name='help')
async def custom_help_command(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if language == 'FA':
        embed = discord.Embed(
            title="راهنمای دستورات ربات",
            description=(
                "در اینجا چند دستور موجود است:\n"
                "🖼️ `phc!Submission` - ارسال فن آرت شما\n"
                "🔄 `phc!Swap` - جایگزینی فن آرت ارسال شده\n"
                "🗑️ `phc!Delete` - حذف فن آرت شما\n"
                "🛑 `phc!Cancel` - لغو هر فرآیند جاری\n"
                "🔍 `phc!Status` - بررسی وضعیت اثر ارسالی شما\n"
                "📜 `phc!StatusLog` - مشاهده ۱۰ ارسال اخیر"
            ),
            color=0x00ff00
        )
    else:
        embed = discord.Embed(
            title="Bot Commands Help",
            description=(
                "Here are some commands you can use:\n"
                "🖼️ `phc!Submission` - Submit your fan art\n"
                "🔄 `phc!Swap` - Replace your submitted fan art\n"
                "🗑️ `phc!Delete` - Delete your submission\n"
                "🛑 `phc!Cancel` - Cancel any ongoing process\n"
                "🔍 `phc!Status` - Check the status of your submission\n"
                "📜 `phc!StatusLog` - View the last 10 submissions"
            ),
            color=0x00ff00
        )

    embed.set_footer(text="Created By Patch_Note | Supported By Phoenix Client Team")
    await ctx.send(embed=embed)

# Command to display copyright guidelines
@bot.command(name='Guide')
async def guide_command(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if language == 'FA':
        await ctx.send("این ربات توسط Patch_Note ساخته شده و توسط تیم Phoenix Client پشتیبانی می‌شود.", ephemeral=True)
    else:
        await ctx.send("This bot is created by Patch_Note and supported by the Phoenix Client Team.", ephemeral=True)

# Command to cancel the ongoing process
@bot.command(name='Cancel')
async def cancel_command(ctx):
    user_id = ctx.author.id
    if user_id in submissions or user_id in submission_messages or user_id in user_language:
        # Clear any ongoing submission process
        if user_id in submissions:
            del submissions[user_id]
        if user_id in submission_messages:
            confirmation_msg, submission_msg = submission_messages[user_id]
            if confirmation_msg:
                await confirmation_msg.delete()
            await submission_msg.delete()
            del submission_messages[user_id]
        # Clear user language preference
        if user_id in user_language:
            del user_language[user_id]

        language = user_language.get(ctx.author.id, 'EN')
        if language == 'FA':
            await ctx.send("فرآیند شما لغو شد.", ephemeral=True)
        else:
            await ctx.send("Your process has been cancelled.", ephemeral=True)
    else:
        language = user_language.get(ctx.author.id, 'EN')
        if language == 'FA':
            await ctx.send("شما فرآیندی در حال اجرا ندارید.", ephemeral=True)
        else:
            await ctx.send("You don't have any ongoing process to cancel.", ephemeral=True)

# Correct command spelling issue and the submission dropdown function
class FanArtSubmitMenu(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="آپلود تصویر", description="آپلود تصویر فن آرت"),
            discord.SelectOption(label="ارسال لینک", description="ارسال لینک فن آرت")
        ]
        super().__init__(placeholder="روش ارسال خود را انتخاب کنید... / Choose your submission method...", min_values=1,
                         max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        language = user_language.get(interaction.user.id, 'EN')
        if self.values[0] == "آپلود تصویر":
            if language == 'FA':
                await interaction.response.send_message("لطفاً تصویر فن آرت خود را آپلود کنید.", ephemeral=True)
            else:
                await interaction.response.send_message("Please upload your fan art image.", ephemeral=True)

            def check(m):
                return m.author == interaction.user and m.attachments

            try:
                message = await bot.wait_for('message', timeout=60.0, check=check)
                if message.attachments:
                    art = message.attachments[0].url
                    submissions[interaction.user.id] = {'submission': art, 'approved': False,
                                                        'submitter': interaction.user}
                    submission_messages[interaction.user.id] = (None, message)
                    submission_log.append((interaction.user.name, art, "در انتظار / Pending"))
                    if language == 'FA':
                        await interaction.followup.send("فن آرت شما ارسال شد و منتظر تأیید است.", ephemeral=True)
                    else:
                        await interaction.followup.send("Your fan art has been submitted and is awaiting approval.",
                                                        ephemeral=True)

                    # Send to confirmation channel
                    confirmation_channel = bot.get_channel(confirmation_channel_id)
                    embed = discord.Embed(title="فن آرت جدید / New Fan Art",
                                          description=f"ارسال شده توسط / Submitted by: {interaction.user.name}")
                    embed.add_field(name="اثر / Art", value=art)
                    embed.set_footer(
                        text="برای تایید ✅ و برای رد ❌ واکنش دهید. / React with ✅ to approve or ❌ to reject.")
                    msg = await confirmation_channel.send(embed=embed)
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')

                    submission_messages[interaction.user.id] = (msg, message)
                else:
                    if language == 'FA':
                        await interaction.followup.send("هیچ تصویری آپلود نشد. لطفاً دوباره تلاش کنید.", ephemeral=True)
                    else:
                        await interaction.followup.send("No image was uploaded. Please try again.", ephemeral=True)
            except asyncio.TimeoutError:
                if language == 'FA':
                    await interaction.followup.send("زمان ارسال تصویر به پایان رسید. لطفاً دوباره تلاش کنید.",
                                                    ephemeral=True)
                else:
                    await interaction.followup.send("Time to upload the image ran out. Please try again.",
                                                    ephemeral=True)

        elif self.values[0] == "ارسال لینک":
            if language == 'FA':
                await interaction.response.send_message("لطفاً لینک فن آرت خود را ارسال کنید (شروع با https):",
                                                        ephemeral=True)
            else:
                await interaction.response.send_message("Please send a link to your fan art (starting with https):",
                                                        ephemeral=True)

            def check(m):
                return m.author == interaction.user and is_valid_link(m.content)

            try:
                message = await bot.wait_for('message', timeout=60.0, check=check)
                if is_valid_link(message.content):
                    link = message.content
                    submissions[interaction.user.id] = {'submission': link, 'approved': False,
                                                        'submitter': interaction.user}
                    submission_messages[interaction.user.id] = (None, message)
                    submission_log.append((interaction.user.name, link, "در انتظار / Pending"))
                    if language == 'FA':
                        await interaction.followup.send("لینک فن آرت شما ارسال شد و منتظر تأیید است.", ephemeral=True)
                    else:
                        await interaction.followup.send(
                            "Your fan art link has been submitted and is awaiting approval.", ephemeral=True)

                    # Send to confirmation channel
                    confirmation_channel = bot.get_channel(confirmation_channel_id)
                    embed = discord.Embed(title="فن آرت جدید / New Fan Art",
                                          description=f"ارسال شده توسط / Submitted by: {interaction.user.name}")
                    embed.add_field(name="اثر / Art", value=link)
                    embed.set_footer(
                        text="برای تایید ✅ و برای رد ❌ واکنش دهید. / React with ✅ to approve or ❌ to reject.")
                    msg = await confirmation_channel.send(embed=embed)
                    await msg.add_reaction('✅')
                    await msg.add_reaction('❌')

                    submission_messages[interaction.user.id] = (msg, message)
                else:
                    if language == 'FA':
                        await interaction.followup.send("لینک نامعتبر است. لطفاً دوباره تلاش کنید.", ephemeral=True)
                    else:
                        await interaction.followup.send("Invalid link. Please try again.", ephemeral=True)
            except asyncio.TimeoutError:
                if language == 'FA':
                    await interaction.followup.send("زمان ارسال لینک به پایان رسید. لطفاً دوباره تلاش کنید.",
                                                    ephemeral=True)
                else:
                    await interaction.followup.send("Time to send the link ran out. Please try again.", ephemeral=True)

# Event listener to handle reactions for approving or rejecting fan art
@bot.event
async def on_reaction_add(reaction, user):
    if reaction.message.channel.id == confirmation_channel_id and user != bot.user:
        if str(reaction.emoji) == '✅':  # Approval
            embed = reaction.message.embeds[0]
            submitter_name = embed.description.split(": ")[1]

            for user_id, (msg, _) in submission_messages.items():
                if msg == reaction.message:
                    submissions[user_id]['approved'] = True
                    submission_log.append((submitter_name, submissions[user_id]['submission'], "تأیید شده / Approved"))
                    await reaction.message.channel.send(
                        f"اثر {submitter_name} تأیید شد. / Art by {submitter_name} has been approved.")

                    main_channel = bot.get_channel(main_server_channel_id)
                    submitter = submissions[user_id]['submitter']
                    main_message = await main_channel.send(
                        f"فن آرت تأیید شده از {submitter.mention}: {submissions[user_id]['submission']} / Approved fan art from {submitter.mention}: {submissions[user_id]['submission']}")
                    await add_reactions_and_thread(main_message)  # Add reactions and create thread

                    try:
                        await submitter.send(
                            f"فن آرت شما تأیید و در کانال اصلی ارسال شد: {submissions[user_id]['submission']} / Your fan art has been approved and posted in the main channel: {submissions[user_id]['submission']}")
                    except discord.Forbidden:
                        await reaction.message.channel.send(
                            f"نتوانستم به {submitter_name} پیام ارسال کنم، اما اثر تأیید شد. / Could not send a message to {submitter_name}, but the art was approved.")
                    break

        elif str(reaction.emoji) == '❌':  # Rejection
            embed = reaction.message.embeds[0]
            submitter_name = embed.description.split(": ")[1]

            for user_id, (msg, _) in submission_messages.items():
                if msg == reaction.message:
                    submissions[user_id]['approved'] = False
                    submission_log.append((submitter_name, submissions[user_id]['submission'], "رد شده / Rejected"))
                    await reaction.message.channel.send(
                        f"اثر {submitter_name} رد شد. / Art by {submitter_name} has been rejected.")

                    archive_channel = bot.get_channel(archive_channel_id)
                    submitter = submissions[user_id]['submitter']
                    await archive_channel.send(
                        f"اثر رد شده از {submitter.mention}: {submissions[user_id]['submission']} / Rejected fan art from {submitter.mention}: {submissions[user_id]['submission']}")

                    try:
                        await submitter.send(
                            f"فن آرت شما رد شد و به آرشیو ارسال شد. / Your fan art has been rejected and sent to the archive.")
                    except discord.Forbidden:
                        await reaction.message.channel.send(
                            f"نتوانستم به {submitter_name} پیام ارسال کنم، اما اثر رد شد. / Could not send a message to {submitter_name}, but the art was rejected.")
                    break

# Command to open the submission popup menu (using dropdowns)
@bot.command(name='Submission')
async def submission(ctx):
    view = discord.ui.View()
    view.add_item(FanArtSubmitMenu())
    language = user_language.get(ctx.author.id, 'EN')
    if language == 'FA':
        await ctx.send("لطفاً روش ارسال فن آرت خود را انتخاب کنید:", view=view, ephemeral=True)
    else:
        await ctx.send("Please choose your fan art submission method:", view=view, ephemeral=True)

# Command to swap the submitted fan art (with message updates in both channels)
@bot.command(name='Swap')
async def swap(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if ctx.author.id in submissions:
        if ctx.author.id in submission_messages:
            confirmation_msg, submission_msg = submission_messages[ctx.author.id]
            if confirmation_msg:
                await confirmation_msg.delete()
            await submission_msg.delete()

        if language == 'FA':
            await ctx.send("لطفاً اثر جدید خود را ارسال کنید تا جایگزین اثر قبلی شود (تصویر یا لینک):", ephemeral=True)
        else:
            await ctx.send("Please send your new submission to replace the previous one (image or link):",
                           ephemeral=True)

        def check(m):
            return m.author == ctx.author and (m.attachments or is_valid_link(m.content))

        try:
            message = await bot.wait_for('message', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            if language == 'FA':
                await ctx.send("زمان جایگزینی به پایان رسید. لطفاً دوباره تلاش کنید.", ephemeral=True)
            else:
                await ctx.send("Time to replace has run out. Please try again.", ephemeral=True)
            return

        if message.attachments:
            submissions[ctx.author.id]['submission'] = message.attachments[0].url
            submission_messages[ctx.author.id] = (None, message)
            if language == 'FA':
                await ctx.send("اثر شما جایگزین شد و منتظر تأیید است.", ephemeral=True)
            else:
                await ctx.send("Your submission has been replaced and is awaiting approval.", ephemeral=True)

            confirmation_channel = bot.get_channel(confirmation_channel_id)
            embed = discord.Embed(title="اثر به‌روزرسانی‌شده / Updated Submission",
                                  description=f"ارسال شده توسط / Submitted by: {ctx.author.name}")
            embed.add_field(name="اثر / Art", value=submissions[ctx.author.id]['submission'])
            msg = await confirmation_channel.send(embed=embed)
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')

            submission_messages[ctx.author.id] = (msg, message)

        elif is_valid_link(message.content):
            submissions[ctx.author.id]['submission'] = message.content
            submission_messages[ctx.author.id] = (None, message)
            if language == 'FA':
                await ctx.send("اثر شما جایگزین شد و منتظر تأیید است.", ephemeral=True)
            else:
                await ctx.send("Your submission has been replaced and is awaiting approval.", ephemeral=True)

            confirmation_channel = bot.get_channel(confirmation_channel_id)
            embed = discord.Embed(title="اثر به‌روزرسانی‌شده / Updated Submission",
                                  description=f"ارسال شده توسط / Submitted by: {ctx.author.name}")
            embed.add_field(name="اثر / Art", value=submissions[ctx.author.id]['submission'])
            msg = await confirmation_channel.send(embed=embed)
            await msg.add_reaction('✅')
            await msg.add_reaction('❌')

            submission_messages[ctx.author.id] = (msg, message)
    else:
        if language == 'FA':
            await ctx.send("شما اثری برای جایگزینی ندارید.", ephemeral=True)
        else:
            await ctx.send("You have no submission to swap.", ephemeral=True)

# Command to delete the submission (removing it from storage and both channels)
@bot.command(name='Delete')
async def delete(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if ctx.author.id in submissions:
        if ctx.author.id in submission_messages:
            confirmation_msg, submission_msg = submission_messages[ctx.author.id]
            if confirmation_msg:
                await confirmation_msg.delete()
            await submission_msg.delete()

        del submissions[ctx.author.id]
        del submission_messages[ctx.author.id]
        if language == 'FA':
            await ctx.send("اثر شما حذف شد.", ephemeral=True)
        else:
            await ctx.send("Your submission has been deleted.", ephemeral=True)
    else:
        if language == 'FA':
            await ctx.send("شما اثری برای حذف ندارید.", ephemeral=True)
        else:
            await ctx.send("You have no submission to delete.", ephemeral=True)

# Command to check the latest submission status
@bot.command(name='Status')
async def status(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if ctx.author.id in submissions:
        latest_submission = submissions[ctx.author.id]
        status = "تأیید شده / Approved" if latest_submission['approved'] else "در انتظار / Pending"
        if language == 'FA':
            await ctx.send(f"آخرین اثر شما در حال حاضر: {status}", ephemeral=True)
        else:
            await ctx.send(f"Your latest submission is currently: {status}", ephemeral=True)
    else:
        if language == 'FA':
            await ctx.send("شما هیچ اثری ارسال نکرده‌اید.", ephemeral=True)
        else:
            await ctx.send("You have not submitted any art.", ephemeral=True)

# Command to check the last 10 submissions and their status
@bot.command(name='StatusLog')
async def status_log(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if submission_log:
        if language == 'FA':
            embed = discord.Embed(title="گزارش وضعیت ارسال", description="آخرین ۱۰ اثر ارسال شده:")
        else:
            embed = discord.Embed(title="Submission Status Log", description="Last 10 submissions:")
        for i, (user, art, status) in enumerate(submission_log[-10:], start=1):
            emoji = "✅" if status in ["تأیید شده", "Approved"] else "❌" if status in ["رد شده", "Rejected"] else "🕒"
            if language == 'FA':
                embed.add_field(name=f"#{i} - {user}", value=f"{emoji} {art} - {status}", inline=False)
            else:
                embed.add_field(name=f"#{i} - {user}", value=f"{emoji} {art} - {status}", inline=False)
        await ctx.send(embed=embed, ephemeral=True)
    else:
        if language == 'FA':
            await ctx.send("هیچ اثری در گزارش یافت نشد.", ephemeral=True)
        else:
            await ctx.send("No submissions found in the log.", ephemeral=True)

# Easter egg command
@bot.command(name='ShahabPN123')
async def easter_egg(ctx):
    language = user_language.get(ctx.author.id, 'EN')
    if language == 'FA':
        await ctx.send("شهاب پورنصیری!!! شما یک ایستر اگ پیدا کردید این لینک را باز کنید تا ببینیدش : https://youtube.com/shorts/SXHMnicI6Pg?si=wBmmei3MDN9k_jkL 🎉", ephemeral=True)
    else:
        await ctx.send("Shahab Pournasiri!!! You found an easter egg! Open this link to see it: https://youtube.com/shorts/SXHMnicI6Pg?si=wBmmei3MDN9k_jkL 🎉", ephemeral=True)

# Run the bot
bot.run('token')
