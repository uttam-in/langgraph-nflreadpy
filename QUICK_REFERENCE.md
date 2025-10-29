# 🏈 NFL Chatbot - Quick Reference Card

## 🚀 Start the Bot

```bash
# Web Interface (Recommended)
chainlit run app.py

# Interactive Mode
python test_bot_with_nflreadpy.py interactive

# Quick Demo
python demo_nflreadpy.py quick

# Quick Test
python quick_bot_test.py
```

## 💬 Sample Queries

```
"What were Patrick Mahomes' passing yards in week 10 of 2024?"
"Show me Travis Kelce's receiving stats for the 2024 season"
"Compare Patrick Mahomes and Josh Allen passing yards in 2024"
"How many touchdowns did Christian McCaffrey score this season?"
```

## 📊 Available Stats

**Passing**: yards, TDs, completions, attempts, interceptions
**Rushing**: yards, TDs, carries, fumbles
**Receiving**: yards, TDs, receptions, targets
**Advanced**: EPA, CPOE, air yards, fantasy points

## ⚡ Performance

- First query: ~2-3 seconds
- Cached: ~1.5-2 seconds
- Repeated: <100ms

## 🔧 Quick Fixes

**Missing pyarrow?**
```bash
pip install pyarrow
```

**Player not found?**
- Use full names: "Patrick Mahomes"
- Check spelling
- Verify 2024 season

## 📖 Documentation

- [Integration Guide](NFLREADPY_INTEGRATION_GUIDE.md)
- [Sample Queries](SAMPLE_QUERIES.md) - 50+ examples
- [Final Summary](FINAL_SUMMARY.md)

## ✅ Status

🟢 **FULLY OPERATIONAL** - Ready to use!
