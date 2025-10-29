# Sample Queries for NFL Chatbot

## Quick Start Examples

Try these queries to see the bot in action with live 2024 NFL data!

## 🏈 Basic Player Statistics

### Quarterbacks
```
"What were Patrick Mahomes' passing yards in week 10 of 2024?"
"Show me Josh Allen's passing stats for the 2024 season"
"How many touchdowns did Lamar Jackson throw this season?"
"What is Brock Purdy's completion percentage in 2024?"
"Show me Dak Prescott's interceptions this year"
```

### Running Backs
```
"How many rushing yards did Christian McCaffrey have in 2024?"
"Show me Derrick Henry's rushing stats this season"
"What are Josh Jacobs' carries and yards in 2024?"
"How many touchdowns did Saquon Barkley score?"
"Show me Tony Pollard's yards per carry"
```

### Wide Receivers & Tight Ends
```
"Show me Travis Kelce's receiving stats for 2024"
"What are Tyreek Hill's receiving yards this season?"
"How many receptions did CeeDee Lamb have in 2024?"
"Show me Justin Jefferson's targets this year"
"What are Stefon Diggs' touchdown catches in 2024?"
```

## 📊 Comparisons

### Same Position
```
"Compare Patrick Mahomes and Josh Allen passing yards in 2024"
"Who has more rushing yards, Derrick Henry or Christian McCaffrey?"
"Compare Travis Kelce and George Kittle receiving stats"
"Who has more touchdowns, Tyreek Hill or CeeDee Lamb?"
"Compare Lamar Jackson and Jalen Hurts passing touchdowns"
```

### Team Comparisons
```
"Compare the Chiefs and Bills quarterbacks in 2024"
"Show me 49ers vs Eagles running backs stats"
"Compare Cowboys and Eagles receivers"
```

## 📅 Time-Based Queries

### Specific Weeks
```
"How did Patrick Mahomes perform in week 10?"
"Show me Travis Kelce's stats from week 15"
"What were Lamar Jackson's passing yards in week 5?"
"How many touchdowns did Josh Allen throw in week 12?"
```

### Recent Performance
```
"How did Christian McCaffrey perform last week?"
"Show me Tyreek Hill's stats from the last game"
"What are Patrick Mahomes' stats in the last 3 weeks?"
```

### Season Totals
```
"Show me Patrick Mahomes' total passing yards for 2024"
"What are Travis Kelce's season totals?"
"How many touchdowns has Lamar Jackson thrown this season?"
```

## 🎯 Advanced Queries

### Multiple Statistics
```
"Show me Patrick Mahomes' passing yards, touchdowns, and interceptions"
"What are Travis Kelce's receptions, yards, and touchdowns?"
"Show me Christian McCaffrey's rushing and receiving stats"
```

### Advanced Metrics
```
"What is Patrick Mahomes' EPA this season?"
"Show me Josh Allen's completion percentage above expectation"
"What are the Chiefs' offensive EPA stats?"
```

### Situational Stats
```
"How did Patrick Mahomes perform against the Bills?"
"Show me Travis Kelce's home vs away stats"
"What are Lamar Jackson's stats in close games?"
```

## 🏆 Rankings & Leaders

```
"Who has the most passing yards in 2024?"
"Which running back has the most touchdowns this season?"
"Who leads the league in receptions?"
"Show me the top 5 quarterbacks by passing yards"
"Which tight end has the most receiving yards?"
```

## 👥 Team-Based Queries

```
"How are the Chiefs quarterbacks performing this season?"
"Show me all 49ers running backs stats"
"What are the Bills receivers' stats in 2024?"
"Show me the Cowboys offensive stats"
"How is the Eagles offense performing?"
```

## 🔄 Follow-Up Queries

After asking about a player, you can ask follow-ups:

```
Initial: "Show me Patrick Mahomes' stats"
Follow-up: "How does that compare to last season?"
Follow-up: "What about Josh Allen?"
Follow-up: "Show me his stats against the Chiefs"
```

## 💡 Tips for Best Results

### ✅ DO:
- Use full player names: "Patrick Mahomes" not "Mahomes"
- Specify the season: "in 2024" or "this season"
- Be specific about stats: "passing yards" not just "yards"
- Use proper team names: "Kansas City Chiefs" or "Chiefs"

### ❌ DON'T:
- Use only last names (may be ambiguous)
- Ask about future games (no predictions)
- Request stats for players who haven't played
- Mix incompatible positions in comparisons

## 🎮 Interactive Mode

Try the interactive mode for a conversation:

```bash
python test_bot_with_nflreadpy.py interactive
```

Example conversation:
```
You: Show me Patrick Mahomes' stats
Bot: [Shows 2024 season stats]

You: How does that compare to Josh Allen?
Bot: [Shows comparison]

You: What about their performance in week 10?
Bot: [Shows week 10 specific stats]
```

## 🚀 Quick Test

Run these commands to test the bot:

```bash
# Quick test with 3 queries
python test_bot_with_nflreadpy.py quick

# Full test with all sample queries
python test_bot_with_nflreadpy.py

# Interactive mode
python test_bot_with_nflreadpy.py interactive

# Web interface
chainlit run app.py
```

## 📈 Performance Notes

- **First query**: ~2-3 seconds (loads data)
- **Cached queries**: ~1.5-2 seconds
- **Repeated queries**: <100ms (instant)

## 🔧 Troubleshooting

### "Player not found"
- Check spelling: "Patrick Mahomes" not "Pat Mahomes"
- Verify player played in 2024
- Try full first and last name

### "No data available"
- Player may be injured/inactive
- Check if player is on active roster
- Verify correct season year

### Slow response
- First query loads full season data (normal)
- Subsequent queries are much faster
- Check internet connection

## 📚 More Information

- [NFLReadPy Integration Guide](NFLREADPY_INTEGRATION_GUIDE.md)
- [Test Results](NFLREADPY_TEST_RESULTS.md)
- [Main README](README.md)

## 🎯 Challenge Yourself

Try creating complex queries:

```
"Compare the top 3 quarterbacks by passing yards in 2024"
"Show me all Chiefs offensive players with over 500 yards"
"Which running back has the best yards per carry with at least 100 attempts?"
"Compare Patrick Mahomes' home and away performance"
"Show me the trend of Travis Kelce's targets over the season"
```

Happy querying! 🏈
