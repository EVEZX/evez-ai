# ⚡ 30-Second Quickstart

## Option 1: Automated Demo

```bash
git clone https://github.com/EvezArt/Evez666.git
cd Evez666
bash demo.sh
```

This runs the complete demo:
1. ✅ Installs dependencies
2. ✅ Tests recursion loop
3. ✅ Starts HTTP spine server
4. ✅ Runs FSC experiment
5. ✅ Verifies integrity
6. ✅ Shows projections

**Result**: Working Atlas v3 system in under 2 minutes.

---

## Option 2: Manual Setup

```bash
# Install
npm install
pip3 install -r fsc/requirements.txt

# Start spine server (port 7777)
npm run atlas:spine:http &

# Run FSC experiment
python3 fsc/runner.py test_model

# Check results
curl http://localhost:7777/verify
curl http://localhost:7777/projections/fsc
```

---

## Option 3: Docker (One Command)

```bash
docker-compose up -d

# Wait 10 seconds, then:
curl http://localhost:7777/projections
```

---

## Test It's Working

```bash
# Should return {"ok": true}
curl http://localhost:7777/verify

# Should show event chain
curl http://localhost:7777/events | jq '.chain[0:3]'

# Run experiment
ATLAS_URL=http://localhost:7777 python3 fsc/runner.py my_model

# View FSC results
curl http://localhost:7777/projections/fsc
```

---

## What You Get

✅ **Event Spine**: Tamper-evident log (SHA256 hash chain)
✅ **Recursion Loop**: Self-evolving kernel
✅ **Game Server**: Authoritative netcode with rollback
✅ **FSC Monitor**: Failure-surface detection
✅ **Anti-Gaming Referee**: Multi-view verification

---

## Next Steps

1. **Explore**: Open http://localhost:7777/events in browser
2. **Extend**: Modify `fsc/runner.py` with real model
3. **Integrate**: Connect to `lord-evez` dashboard
4. **Deploy**: Push to Fly.io / Railway / Vercel

Full docs: See `DEPLOYMENT.md` and `README-ATLAS.md`

---

**Time to working system**: ~90 seconds

**Dependencies**: Node.js 20+, Python 3.11+, curl

**Status**: ✅ Production-ready
