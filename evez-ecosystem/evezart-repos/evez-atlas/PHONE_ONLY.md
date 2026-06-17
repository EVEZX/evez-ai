# 📱 Phone-only: Codespaces Playbook

You do **not** need a computer.

## 1) Create a Codespace (on your phone)

1. Open the repo in your mobile browser: https://github.com/EvezArt/Evez666
2. Tap **Code**
3. Tap **Codespaces**
4. Tap **Create codespace on main**

The repo includes a devcontainer that auto-starts the Atlas spine server and forwards port 7777.

## 2) Open the game

After the Codespace is ready:

1. Tap the **Ports** tab
2. Find **7777**
3. Tap the globe/open icon to open the forwarded URL

You should see **Atlas v3 Immutable Game**.

## 3) Verify immutability

In the browser, open:

- `/verify` → should show `{ "ok": true }`
- `/events` → should show the append-only event chain

## 4) Play

On the home page:

1. Tap **Start** (creates match)
2. Tap **Join** (creates player)
3. Tap arrows to move

Every move is an append-only `game` event; the on-screen state is derived by replaying the chain.

## 5) If something looks stuck

Open `/verify` first.

If `ok` is false, copy the JSON and paste it into chat.
