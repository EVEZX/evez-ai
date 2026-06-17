const { Client, GatewayIntentBits, SlashCommandBuilder, REST, EmbedBuilder } = require('discord.js');
const BASE_URL = "https://evez-api2.fly.dev/v1";

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.MessageContent, GatewayIntentBits.GuildMessages]
});

const commands = [
  new SlashCommandBuilder().setName('ask').setDescription('Ask EVEZ AI anything')
    .addStringOption(o => o.setName('prompt').setDescription('Your question').setRequired(true))
    .addStringOption(o => o.setName('model').setDescription('Model to use')
      .addChoices(
        { name: 'Smart (best)', value: 'evez-smart' },
        { name: 'Code', value: 'evez-code' },
        { name: 'Fast', value: 'evez-fast' },
        { name: 'Vision', value: 'evez-vision' }
      )),
  new SlashCommandBuilder().setName('models').setDescription('List available models'),
].map(c => c.toJSON());

const rest = new REST().setToken(process.env.DISCORD_TOKEN);
(async () => {
  try {
    await rest.put(`/applications/${process.env.DISCORD_APP_ID}/commands`, { body: commands });
    console.log('Slash commands registered');
  } catch(e) { console.error(e); }
})();

client.on('interactionCreate', async (interaction) => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'models') {
    return interaction.reply({ embeds: [new EmbedBuilder()
      .setTitle('EVEZ AI Models')
      .setColor('#6c5ce7')
      .addFields(
        { name: 'evez-smart', value: 'GLM-5.1 - Best overall', inline: true },
        { name: 'evez-code', value: 'DeepSeek V3.2 - Code & reasoning', inline: true },
        { name: 'evez-fast', value: 'MiniMax M2.5 - Quick & balanced', inline: true },
        { name: 'evez-vision', value: 'Kimi K2.5 - Multimodal', inline: true },
      )
      .setFooter({ text: 'Get your own API key at evez-api2.fly.dev/signup' })
    ]});
  }

  if (interaction.commandName === 'ask') {
    await interaction.deferReply();
    const prompt = interaction.options.getString('prompt');
    const model = interaction.options.getString('model') || 'evez-smart';
    
    try {
      const resp = await fetch(`${BASE_URL}/chat/completions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${process.env.EVEZ_API_KEY}` },
        body: JSON.stringify({ model, messages: [{ role: 'user', content: prompt }], max_tokens: 2048 })
      });
      const data = await resp.json();
      const reply = data.choices?.[0]?.message?.content || 'No response';
      const truncated = reply.length > 2000 ? reply.slice(0, 1997) + '...' : reply;
      await interaction.editReply(truncated);
    } catch(e) {
      await interaction.editReply('Error: ' + e.message);
    }
  }
});

client.on('messageCreate', async (msg) => {
  if (msg.author.bot) return;
  if (!msg.mentions.has(client.user)) return;
  
  const prompt = msg.content.replace(/<@!\d+>/, '').trim();
  if (!prompt) return;
  
  try {
    const resp = await fetch(`${BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${process.env.EVEZ_API_KEY}` },
      body: JSON.stringify({ model: 'evez-smart', messages: [{ role: 'user', content: prompt }], max_tokens: 2048 })
    });
    const data = await resp.json();
    const reply = data.choices?.[0]?.message?.content || 'No response';
    const truncated = reply.length > 2000 ? reply.slice(0, 1997) + '...' : reply;
    msg.reply(truncated);
  } catch(e) { msg.reply('Error: ' + e.message); }
});

client.login(process.env.DISCORD_TOKEN);
