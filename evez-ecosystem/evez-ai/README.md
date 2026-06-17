# evez-ai

```js
const EvezAI = require('evez-ai');

const evez = new EvezAI('evez-your-api-key');

const response = await evez.chat.completions.create({
  model: EvezAI.MODELS.SMART,
  messages: [{ role: 'user', content: 'Hello!' }]
});

console.log(response.choices[0].message.content);
```

Get your free API key at [evez-api2.fly.dev/signup](https://evez-api2.fly.dev/signup)
