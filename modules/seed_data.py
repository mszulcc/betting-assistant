"""
Seed data for the BetAssist AI Knowledge Base.

Run this module once to populate the SQLite database with:
  - 20 betting strategies
  - 50 betting terms
  - 12 league insights
  - 15 FAQ entries

It is safe to run multiple times — INSERT OR IGNORE prevents duplicates.
Called automatically from app.py via init_db() on first startup.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from modules.knowledge_base import _get_conn


# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------

STRATEGIES = [
    # --- Value betting ---
    {
        "name": "Value Betting",
        "description": "Identify bets where the bookmaker's implied probability is lower than your estimated true probability. The core of long-term profitable betting.",
        "risk_level": "medium",
        "category": "value",
        "example": "Bookmaker gives 3.0 on a team you assess has 40% chance (true odds 2.5). EV = 0.4×3.0 − 1 = +0.2. Bet has positive expected value.",
    },
    {
        "name": "Expected Value (EV) Betting",
        "description": "Only place bets with a positive expected value: EV = (probability × decimal_odds) − 1. Over many bets, positive EV guarantees long-run profit.",
        "risk_level": "low",
        "category": "value",
        "example": "EV = (0.55 × 2.10) − 1 = 0.155. A 15.5% edge per bet compounded over 100 bets is very significant.",
    },
    {
        "name": "Arbitrage Betting (Arbing)",
        "description": "Cover all outcomes of an event across different bookmakers to guarantee a profit regardless of the result, exploiting differing odds.",
        "risk_level": "low",
        "category": "value",
        "example": "Bookie A: Team A wins @ 2.10. Bookie B: Team B wins @ 2.05. Stake ratio 52/48 locks in ~2.5% guaranteed profit.",
    },
    {
        "name": "Matched Betting",
        "description": "Use free bets and promotions offered by bookmakers to guarantee a profit by placing a back bet at the bookie and a lay bet at a betting exchange.",
        "risk_level": "low",
        "category": "value",
        "example": "Bookie gives £20 free bet. Back the selection for £20 (free), lay it at Betfair exchange for £19. Lock in ~£17 profit regardless of outcome.",
    },
    # --- Bankroll management ---
    {
        "name": "Kelly Criterion",
        "description": "Optimal stake sizing formula: stake = (bp − q) / b, where b = decimal odds − 1, p = win probability, q = 1 − p. Maximises long-run bankroll growth.",
        "risk_level": "medium",
        "category": "bankroll",
        "example": "Odds 2.50, win probability 45%: b=1.5, p=0.45, q=0.55. Kelly = (1.5×0.45 − 0.55)/1.5 = 0.083. Stake 8.3% of bankroll.",
    },
    {
        "name": "Flat Staking",
        "description": "Always bet the same fixed amount (e.g. 1–2% of bankroll) regardless of confidence level. Simple, protects against variance.",
        "risk_level": "low",
        "category": "bankroll",
        "example": "£1000 bankroll, 1% flat stake = £10 per bet. After 100 bets you can review performance without catastrophic loss.",
    },
    {
        "name": "Percentage Staking",
        "description": "Bet a fixed percentage of your current bankroll each time. Stakes grow when winning and shrink when losing, adapting to bankroll size.",
        "risk_level": "low",
        "category": "bankroll",
        "example": "2% of £1000 = £20 first bet. If bankroll grows to £1050, next stake = £21.",
    },
    # --- Match analysis ---
    {
        "name": "Over/Under Goals Betting",
        "description": "Bet on whether total goals in a match will be Over or Under a line (e.g. 2.5). Uses team scoring averages, defensive records, and match context.",
        "risk_level": "medium",
        "category": "match_analysis",
        "example": "Both teams average 1.8 goals per game. Combined expected goals ~3.6. Over 2.5 looks value if priced above 2.0.",
    },
    {
        "name": "Asian Handicap Betting",
        "description": "A handicap is applied to eliminate the draw, giving one team a virtual head start. Common lines: -0.5, -1, -1.5, +0.5, +1. Reduces house edge significantly.",
        "risk_level": "medium",
        "category": "match_analysis",
        "example": "Man City −1.5 AH vs Burnley. City must win by 2+ goals for your bet to win. If City win 1-0, bet loses.",
    },
    {
        "name": "Both Teams To Score (BTTS)",
        "description": "Bet on whether both teams will score at least one goal. Best for matches between two attacking sides with leaky defences.",
        "risk_level": "medium",
        "category": "match_analysis",
        "example": "Arsenal vs Liverpool: both average 1.7 goals scored, 1.3 conceded. BTTS Yes at 1.75 offers value.",
    },
    {
        "name": "Draw No Bet (DNB)",
        "description": "Bet on a team to win. If the match is a draw, stake is returned. Removes the draw outcome at a cost to the odds.",
        "risk_level": "low",
        "category": "match_analysis",
        "example": "Back Man United DNB at 1.60. If United win, collect winnings. If draw, get stake back. Only lose if opponent wins.",
    },
    {
        "name": "Double Chance",
        "description": "Cover two of the three possible outcomes (1X, X2, or 12). Safer but lower odds. Useful when backing a slight favourite or strong away side.",
        "risk_level": "low",
        "category": "match_analysis",
        "example": "Man City vs Chelsea, bet 1X (City win or draw) at 1.30. Only lose if Chelsea win.",
    },
    {
        "name": "Half-Time/Full-Time (HT/FT)",
        "description": "Predict the result at both half-time and full-time. High-odds market with good value if team patterns are well researched.",
        "risk_level": "high",
        "category": "match_analysis",
        "example": "Strong favourite often concedes early, then dominates. Back Draw/Home at 4.0 — profitable pattern for certain teams.",
    },
    # --- Advanced ---
    {
        "name": "Correct Score Betting",
        "description": "Predict the exact final score. Very high odds, very high risk. Best approached with Poisson distribution modelling of expected goals.",
        "risk_level": "high",
        "category": "advanced",
        "example": "Expected goals: 1.8 vs 0.9. Poisson predicts 1-0 at 19% probability. Bet is value at odds > 5.26.",
    },
    {
        "name": "Lay Betting (Betting Exchange)",
        "description": "Act as the bookmaker — bet against an outcome using a betting exchange. Profitable when the market overestimates a team's probability.",
        "risk_level": "high",
        "category": "advanced",
        "example": "Lay a heavy favourite at 1.30. If they draw or lose (likely ~20% of the time), you win the back stake.",
    },
    {
        "name": "Accumulator (Parlay) Betting",
        "description": "Combine multiple selections into one bet — all must win. Odds multiply but so does variance. Usually poor expected value due to bookie margin compounding.",
        "risk_level": "high",
        "category": "accumulator",
        "example": "4 selections at 1.80 each: combined odds = 1.8^4 = 10.5. True probability ~8%. Expected value is typically negative.",
    },
    {
        "name": "Trixie",
        "description": "3 selections forming 4 bets: 3 doubles + 1 treble. Returns if at least 2 selections win.",
        "risk_level": "high",
        "category": "accumulator",
        "example": "3 selections A, B, C. Bets: AB, AC, BC, ABC. Costs 4 units. Returns profit if any 2 win.",
    },
    {
        "name": "Goalscorer Betting",
        "description": "Bet on which player scores: Anytime, First, Last, or Brace. Requires knowledge of player xG, penalty duties, and tactical role.",
        "risk_level": "medium",
        "category": "player",
        "example": "Striker averages 0.6 xG per game. Anytime scorer at 2.50 implies 40% — higher than xG-derived 45%. Value bet.",
    },
    {
        "name": "In-Play (Live) Betting",
        "description": "Bet during the match as odds shift with events. Requires quick decision-making and a clear pre-match model to spot market overreactions.",
        "risk_level": "high",
        "category": "live",
        "example": "Favourite goes 1-0 down early. Their draw odds swing from 3.5 to 2.0 despite no change in underlying quality. Back the draw.",
    },
    {
        "name": "Line Shopping",
        "description": "Compare odds across multiple bookmakers and always bet at the best available price. Even 0.05 difference compounded over 1000 bets is substantial.",
        "risk_level": "low",
        "category": "value",
        "example": "Bookie A: 2.10. Bookie B: 2.18. Bookie C: 2.25. Always take 2.25. Over 500 bets at £20 this saves ~£500.",
    },
]


TERMS = [
    ("Odds", "general", "The ratio reflecting the probability of an outcome, expressed as decimal (2.50), fractional (3/2), or American (+150).", "Decimal odds of 3.0 mean a £10 bet returns £30 (£20 profit)."),
    ("Decimal Odds", "general", "The most common format in Europe. Stake × decimal odds = total return (including stake).", "Odds of 2.50 on a £10 bet = £25 total return, £15 profit."),
    ("Fractional Odds", "general", "Traditional UK format. Numerator/denominator = profit per unit staked.", "3/1 means £3 profit for every £1 staked. Total return = £4."),
    ("American Odds (Moneyline)", "general", "US format. Positive (+150) = profit on £100 stake. Negative (−130) = stake required to profit £100.", "+200 means bet £100 to win £200 profit. −150 means bet £150 to win £100."),
    ("Implied Probability", "general", "Probability implied by the odds: 1/decimal_odds × 100%. Bookmaker margin pushes this above 100%.", "Odds 2.50 → implied probability = 1/2.50 = 40%."),
    ("Bookmaker Margin (Vig/Juice)", "general", "The percentage the bookmaker takes from every bet, built into the odds. Also called overround.", "1X2 market: home 40% + draw 30% + away 30% = 100%. With margin: 43%+32%+33% = 108%. 8% is the vig."),
    ("Handicap", "match", "A virtual head start or deficit applied to a team to level the playing field and create a more balanced betting market.", "Arsenal −1 handicap vs Burnley. Arsenal must win by 2+ for bet to win."),
    ("Asian Handicap", "match", "Eliminates the draw by using quarter-goal and half-goal handicaps, offering refunds on pushes.", "−0.75 AH: half stake on −0.5, half on −1. Win both halves if team wins by 2+."),
    ("Over/Under (Totals)", "match", "A line set for total goals (or corners, cards) in a match. Bet on whether the actual total goes over or under that line.", "Over 2.5 goals: bet wins if 3+ goals are scored."),
    ("BTTS (Both Teams To Score)", "match", "A market predicting whether both teams will score at least one goal each.", "BTTS Yes wins if the final score is 1-1, 2-1, 1-2, 2-2, etc."),
    ("Draw No Bet (DNB)", "match", "A bet where the draw outcome is removed. Stake is returned if the match ends level.", "Back Liverpool DNB @ 1.60. If draw: stake returned. If Liverpool win: profit."),
    ("Double Chance", "match", "A bet covering two of three outcomes: Home/Draw (1X), Away/Draw (X2), or Home/Away (12).", "1X at 1.25 — only loses if the away team wins."),
    ("Accumulator", "strategy", "Multiple selections combined into one bet. All must win. Odds multiply. Variance is very high.", "4 selections at 2.0 each = combined odds 16.0. All must win."),
    ("Parlay", "strategy", "American term for an accumulator — multiple bets combined where all must win.", "3-team parlay on NFL games. Typical odds 6.0 for favourites."),
    ("Lay Bet", "exchange", "Betting against an outcome via an exchange (Betfair). You act as the bookmaker and profit if the selection loses.", "Lay Man United at 2.0. If they draw or lose, you win the backer's stake."),
    ("Back Bet", "exchange", "A standard bet that a selection will win, placed at a bookmaker or exchange.", "Back Spain to win at 2.50."),
    ("Betting Exchange", "exchange", "A platform where bettors trade bets against each other rather than a bookmaker. Betfair is the largest.", "Betfair Exchange, Betdaq, Smarkets."),
    ("Expected Goals (xG)", "analytics", "A statistical metric measuring the quality of goal-scoring chances. Higher xG means more dangerous attack.", "A team with 2.5 xG against 0.8 xG should win comfortably in the long run."),
    ("Expected Value (EV)", "analytics", "The average outcome of a bet repeated many times: EV = (probability × odds) − 1.", "EV = (0.45 × 2.5) − 1 = 0.125. Positive EV is a good bet."),
    ("Kelly Criterion", "bankroll", "A formula for optimal stake sizing to maximise long-term growth: f = (bp − q) / b.", "Win prob 50%, odds 2.10: b=1.1, f=(1.1×0.5−0.5)/1.1=0.045. Stake 4.5%."),
    ("Bankroll", "bankroll", "The total amount of money set aside exclusively for betting. Never bet more than you can afford to lose.", "A £500 bankroll with 2% flat stakes = £10 per bet."),
    ("Unit", "bankroll", "A standardised measure of betting activity. One unit = your standard stake (e.g. 1% of bankroll).", "5-unit win on a 100-unit bankroll = 5% growth."),
    ("Stake", "bankroll", "The amount wagered on a single bet.", "Stake £25 on Spain to win at 2.0, potential return £50."),
    ("Return", "bankroll", "Total amount received if a bet wins, including the original stake.", "Stake £20 at odds 3.0: return = £60 (£40 profit + £20 stake)."),
    ("Profit/Loss (P&L)", "bankroll", "Net profit or loss from a bet or a series of bets.", "Won 3 bets (£30 profit) and lost 2 (£20 loss) = £10 net profit."),
    ("ROI (Return on Investment)", "analytics", "Profit as a percentage of total amount staked. Key long-term performance metric.", "Staked £1000 total, profit £80 → ROI = 8%."),
    ("CLV (Closing Line Value)", "analytics", "Comparing the odds you bet at vs the final closing odds. Consistently beating CLV is the strongest indicator of a profitable bettor.", "Bet at 3.20, closed at 2.90. Positive CLV of ~10%."),
    ("Arbitrage", "value", "Exploiting differing odds at different bookmakers to guarantee profit regardless of outcome.", "Bet Home @ 2.15 at Bookie A, Away @ 2.10 at Bookie B. Covered for profit."),
    ("Sure Bet", "value", "Another term for arbitrage — a bet that guarantees profit. Rare but real.", "Requires arb percentage < 100%."),
    ("Steam Move", "live", "A rapid, sharp odds movement across multiple bookmakers — usually caused by sharp bettors hitting the market hard.", "Odds drop from 2.50 to 2.10 in minutes across all books — a steam move."),
    ("Line Movement", "live", "How odds change from opening to closing. Sharp movement against public money signals sharp bettor action.", "Public bets 70% on favourite, but odds drift — sharp money on underdog."),
    ("Sharp Bettor (Sharp)", "general", "A professional, sophisticated bettor with a long-term edge, whose bets move markets.", "Sharps typically have ROI > 5% over thousands of bets."),
    ("Square Bettor (Public)", "general", "A recreational bettor who bets emotionally, typically on favourites and well-known teams.", "Squares drive the Man United or Barcelona bias in many markets."),
    ("Fade the Public", "strategy", "Bet against the majority of public money, exploiting the bookmaker's need to shade lines toward the popular side.", "If 80% of bets are on the favourite, the underdog may offer value."),
    ("Closing Odds", "general", "The final odds available just before an event starts — generally the most efficient market price.", "Bet at 3.0, closed at 2.6. You captured significant value."),
    ("Opening Odds", "general", "The initial odds set by the bookmaker when the market opens. Often less efficient than closing odds.", "Opening line 2.10, closes 1.85 as money pours in on favourite."),
    ("Push", "general", "When a bet results in a tie/draw exactly at the handicap line, and the stake is returned.", "Bet team −1 AH, they win exactly 1-0. Half stake refunded (on −0.75)."),
    ("Void Bet", "general", "A bet cancelled by the bookmaker (e.g. match abandoned, player didn't play). Stake is returned.", "Bet on first goalscorer, player subbed off before kick-off — bet voided."),
    ("Each-Way Bet", "general", "A two-part bet: win and place. Common in horse racing and golf. Pays reduced odds if selection places but doesn't win.", "Back a golfer each-way at 20/1. 1/5 odds for top-5 finish."),
    ("Ante-Post Betting", "general", "Betting long before an event takes place — e.g. season outright winner markets.", "Back England to win the World Cup at 8.0 before the tournament."),
    ("Outright Betting", "general", "Betting on the winner of a competition or tournament rather than a single match.", "Back Real Madrid to win the Champions League at 4.50."),
    ("Correct Score", "match", "Predicting the exact final scoreline. High odds, requires Poisson modelling for edge.", "Predict 2-1 at 8.0. Poisson model gives 15% probability → value."),
    ("Fixture", "general", "A scheduled match between two teams.", "The Premier League fixture list is announced in June each year."),
    ("Form", "analytics", "A team's recent performance history, typically last 5 or 6 matches.", "Man City in form: WWWDW. Liverpool: LWDLW. City are in better form."),
    ("H2H (Head-to-Head)", "analytics", "Historical record between two specific teams.", "England vs Germany H2H: 36 played, England 13 wins, Germany 15 wins, 8 draws."),
    ("Clean Sheet", "match", "When a team concedes zero goals in a match.", "Man City kept 22 clean sheets in 38 PL games — outstanding defensive record."),
    ("First Half Goals (FHG)", "match", "Goals scored in the first 45 minutes. Some teams are known for slow or fast starts.", "Liverpool score 40% of goals in the first 30 minutes — early goal bet value."),
    ("Total Corners", "match", "A market betting on the total number of corners in a match. Less affected by late goals/red cards than goallines.", "Bet Over 10 corners in a tight Premier League game between pressing teams."),
    ("Relegation Betting", "general", "Betting on which teams will be relegated at the end of a season.", "Newly promoted sides average 35% chance of immediate relegation — back before season at value."),
    ("Asian Total", "match", "Similar to Over/Under but uses quarter-goal lines (e.g. 2.25, 2.75) to allow half-win/half-loss outcomes.", "Over 2.25: if exactly 2 goals, half stake refunded, other half loses."),
]


LEAGUE_INSIGHTS = [
    {
        "league_name": "Premier League",
        "key_stats": "Avg 2.8 goals/game. Home win rate ~45%. Top 6 teams cover ~60% of H2H wins. Avg corners 10.2/game.",
        "trends": "High-pressing teams dominate. Late goals common — 25% scored after 75'. VAR reduces obvious red cards but increases injury time goals.",
        "betting_tips": "BTTS Yes hits ~55% of games. Away wins undervalued in big-6 away fixtures. Over 2.5 profitable for top-6 home games.",
        "season": "2025/26",
    },
    {
        "league_name": "Bundesliga",
        "key_stats": "Avg 3.1 goals/game (highest of Big 5). Home win rate ~47%. Bayern dominance skews outright markets.",
        "trends": "High xG values throughout. Sehr offensiv — BTTS Yes in ~62% of fixtures. Low draw rate (~22%) compared to other leagues.",
        "betting_tips": "Over 2.5 goals hits ~65% of games. BTTS Yes very reliable. Avoid Bayern heavy favourites in cups (upset prone).",
        "season": "2025/26",
    },
    {
        "league_name": "Serie A",
        "key_stats": "Avg 2.6 goals/game. Lowest average in Big 5. High draw rate ~28%. Strong defensive traditions.",
        "trends": "Tactical, low-scoring games. Late goals due to tired legs. Top teams dominate possession but convert inefficiently.",
        "betting_tips": "Under 2.5 goals profitable in mid-table fixtures. Draw has high hit rate (~28%). DNB on strong home favourites offers safety.",
        "season": "2025/26",
    },
    {
        "league_name": "La Liga",
        "key_stats": "Avg 2.7 goals/game. Barcelona & Real Madrid dominate possession stats. High average xG discrepancy for top teams.",
        "trends": "Possession football. Large xG gaps between top and bottom teams. Relegation battle fixtures are low-scoring and hard to predict.",
        "betting_tips": "Lay bottom-half teams at short odds vs top-6. Over 2.5 profitable for El Clasico. Asian Handicap value in mid-table clashes.",
        "season": "2025/26",
    },
    {
        "league_name": "Ligue 1",
        "key_stats": "Avg 2.7 goals/game. PSG historically dominant. Post-PSG era opens competition. High home win rate ~48%.",
        "trends": "Physical game, high aerial duels. Monaco and Lyon emerging as contenders. Pace of counter-attacks high.",
        "betting_tips": "Away teams undervalued when PSG not involved. BTTS Yes ~52% hit rate. Under 2.5 in cup ties involving lower-division opponents.",
        "season": "2025/26",
    },
    {
        "league_name": "Champions League",
        "key_stats": "Avg 2.9 goals/game. Group stage sees most upsets. Knockout stage heavily favours big clubs. Away goals rule abolished.",
        "trends": "High-profile managers prefer 0-0 in aways legs (conservative approach). Second legs — goals arrive early when trailing. Emotional crowds drive first-half performance.",
        "betting_tips": "BTTS Yes ~58% across all rounds. Under 2.5 in first knockout legs. Over 2.5 in second legs when one team is behind on aggregate.",
        "season": "2025/26",
    },
    {
        "league_name": "FIFA World Cup",
        "key_stats": "Avg 2.7 goals/game at WC 2022. Draw rate ~22% in group stage. Knockout stages: 30% go to extra time.",
        "trends": "Group stage has many conservative games — teams avoid losing. Knockout rounds: high-pressure creates more goals overall. Penalties decide ~15% of knockout games.",
        "betting_tips": "Under 2.5 goals in first group games (teams cautious). Asian Handicap +0.5 for underdogs in group stage. BTTS No reliable in knockout opener legs.",
        "season": "2026",
    },
    {
        "league_name": "European Championship",
        "key_stats": "Avg 2.4 goals/game at Euro 2024. Very low draw rate in knockouts. National rivalries create high-pressure low-scoring games.",
        "trends": "Defensive setups in group stage. Hosts historically perform above ELO expectations. Penalty shootouts common.",
        "betting_tips": "Under 2.5 in group games. Avoid backing short-priced favourites in knockouts. Host nation each-way at tournament start.",
        "season": "2024",
    },
    {
        "league_name": "Eredivisie",
        "key_stats": "Avg 3.2 goals/game — among highest in Europe. Ajax, PSV, Feyenoord dominate. Very high home win rate ~52%.",
        "trends": "End-to-end football. Defensive frailties even in top clubs. Goalfests common in mid-table clashes.",
        "betting_tips": "Over 2.5 goals hits ~70%. BTTS Yes ~65%. Great league for goal-based markets. Avoid heavy handicaps on lower-table home teams.",
        "season": "2025/26",
    },
    {
        "league_name": "Primeira Liga",
        "key_stats": "Avg 2.6 goals/game. Porto, Benfica, Sporting dominate. Strong home advantage, especially in the north.",
        "trends": "Physical, direct football. Top teams rotate for European commitments — upsets possible in domestic cups.",
        "betting_tips": "Top-3 away handicap value is poor. Under 2.5 in cup ties. Look for BTTS Yes in mid-table rivalry games.",
        "season": "2025/26",
    },
    {
        "league_name": "Championship",
        "key_stats": "Avg 2.5 goals/game. Very competitive — 12 teams can realistically reach playoffs. Most played league in Europe (46 games).",
        "trends": "High variance due to fixture congestion. Form streaks common due to tired squads. Promotion contenders often lose ground late in season.",
        "betting_tips": "Fade teams on 3+ game winning streaks (congestion effect). Under 2.5 in top-of-table clashes. Play-off final historically goes to the team that finished higher.",
        "season": "2025/26",
    },
    {
        "league_name": "Série A",
        "key_stats": "Brazilian top flight. Avg 2.4 goals/game. High home win rate ~50%. Very unpredictable — form volatile due to travel.",
        "trends": "Long travel distances affect away performance. Crowd atmosphere extreme. July-December most competitive period.",
        "betting_tips": "Home teams underpriced in early rounds. Under 2.5 for long-distance away fixtures. Avoid cup markets — lineups heavily rotated.",
        "season": "2025",
    },
]


FAQ = [
    {
        "question": "What is value betting?",
        "answer": "Value betting means finding bets where the bookmaker's odds offer higher probability than the true probability of the outcome. If a team has a 50% chance to win but the odds imply only 40%, there is 10% positive expected value. Over many bets, value betting leads to long-term profit.",
        "category": "strategy",
    },
    {
        "question": "How do I calculate expected value (EV)?",
        "answer": "EV = (Your probability estimate × Decimal odds) − 1. Example: You estimate 55% win probability (0.55), odds are 2.10. EV = (0.55 × 2.10) − 1 = 0.155. A positive EV means the bet is profitable long-term.",
        "category": "strategy",
    },
    {
        "question": "What is Asian Handicap?",
        "answer": "Asian Handicap removes the draw by applying fractional handicaps to both teams. For example, Team A at −1 AH means they must win by 2+ goals. At −0.5 AH, they just need to win. Quarter-goal handicaps (−0.75, −1.25) split the stake between two lines, allowing half-wins and half-losses.",
        "category": "markets",
    },
    {
        "question": "What is the Kelly Criterion?",
        "answer": "Kelly Criterion is an optimal stake sizing formula: stake fraction = (b×p − q) / b, where b = decimal odds − 1, p = your win probability, q = 1 − p. It maximises long-term bankroll growth but can suggest large stakes. Many bettors use half-Kelly (divide result by 2) for safety.",
        "category": "bankroll",
    },
    {
        "question": "How does matched betting work?",
        "answer": "Matched betting uses a bookmaker's free bet promotion. You place a back bet at the bookmaker (using the free bet) and a lay bet at a betting exchange covering the opposite outcome. This locks in a profit regardless of the result, as the two bets offset each other.",
        "category": "strategy",
    },
    {
        "question": "What is implied probability?",
        "answer": "Implied probability is the win probability suggested by the odds: IP = 1 / decimal_odds. Odds of 2.50 imply 40% probability. The sum of all outcomes' IPs exceeds 100% — the extra percentage is the bookmaker's margin (vig).",
        "category": "general",
    },
    {
        "question": "What does BTTS mean?",
        "answer": "BTTS stands for Both Teams To Score. The bet wins if both the home and away team score at least one goal each, regardless of who wins or what the final score is. It loses if either team fails to score.",
        "category": "markets",
    },
    {
        "question": "What is an accumulator and is it profitable?",
        "answer": "An accumulator (parlay) combines multiple selections into one bet. All must win. Odds multiply, creating potentially large payouts. However, the bookmaker's margin compounds with each leg, making accumulators typically poor expected value. Professional bettors generally avoid them.",
        "category": "strategy",
    },
    {
        "question": "What is CLV (Closing Line Value)?",
        "answer": "CLV measures the difference between the odds you bet at and the closing odds just before the event. Consistently getting better odds than the close (positive CLV) is the strongest long-term indicator of a profitable bettor, independent of short-term results.",
        "category": "analytics",
    },
    {
        "question": "How should I manage my bankroll?",
        "answer": "Best practices: (1) Set aside a dedicated bankroll you can afford to lose. (2) Use flat staking (1-2% per bet) or Kelly Criterion. (3) Never chase losses. (4) Keep detailed records. (5) Review performance monthly. Most professionals use 1-3% of bankroll per bet.",
        "category": "bankroll",
    },
    {
        "question": "What is arbitrage betting?",
        "answer": "Arbitrage (arbing) exploits different odds at different bookmakers to guarantee a profit regardless of the result. You cover all outcomes at combined odds that sum to less than 100% implied probability. Profit is typically 1-5%. Bookmakers actively limit arbers.",
        "category": "strategy",
    },
    {
        "question": "Is betting profitable long-term?",
        "answer": "For most recreational bettors, no — bookmaker margins ensure average losses of 5-10% of turnover. However, disciplined bettors who focus on value, CLV, and bankroll management can achieve long-term profit. Professional bettors typically achieve 3-8% ROI, requiring large volume and sharp market analysis.",
        "category": "general",
    },
    {
        "question": "What is xG (expected goals)?",
        "answer": "Expected Goals (xG) measures the quality of goal-scoring chances on a scale from 0 to 1, based on historical data about similar shots. A penalty = ~0.76 xG. An open-play header from 6 yards = ~0.55 xG. Teams with consistently high xG but few goals will likely regress to score more.",
        "category": "analytics",
    },
    {
        "question": "What does Draw No Bet mean?",
        "answer": "Draw No Bet (DNB) removes the draw option from 1X2. If you back a team DNB and the match is a draw, your stake is returned. You only lose if the other team wins. DNB odds are lower than regular 1 or 2 odds but provide a safety net against the draw.",
        "category": "markets",
    },
    {
        "question": "How do I read Asian Handicap lines?",
        "answer": "Common AH lines: −0.5 (must win), −1 (must win by 2+), −1.5 (must win by 2+, half stake on −2), +0.5 (win or draw), +1 (win, draw, or lose by 1), +1.5 (win, draw, or lose by 1, half stake on +2). Quarter-line handicaps (e.g. −0.75) split the stake between the two adjacent whole/half lines.",
        "category": "markets",
    },
]


# ---------------------------------------------------------------------------
# Seeding function
# ---------------------------------------------------------------------------

def seed_knowledge_base(force: bool = False) -> dict:
    """
    Populate the knowledge base with starter data.

    Args:
        force: If True, re-inserts all data (using INSERT OR REPLACE).
               If False (default), skips existing records (INSERT OR IGNORE).

    Returns:
        dict with counts of inserted records per table.
    """
    conn = _get_conn()
    cursor = conn.cursor()
    counts = {"strategies": 0, "terms": 0, "league_insights": 0, "faq": 0}

    insert_mode = "INSERT OR REPLACE" if force else "INSERT OR IGNORE"

    # Strategies
    for s in STRATEGIES:
        cursor.execute(
            f"{insert_mode} INTO betting_strategies (name, description, risk_level, category, example) VALUES (?,?,?,?,?)",
            (s["name"], s["description"], s["risk_level"], s["category"], s["example"]),
        )
        if cursor.rowcount > 0:
            counts["strategies"] += 1

    # Terms
    for term, category, definition, example in TERMS:
        cursor.execute(
            f"{insert_mode} INTO betting_terms (term, definition, example_usage, category) VALUES (?,?,?,?)",
            (term, definition, example, category),
        )
        if cursor.rowcount > 0:
            counts["terms"] += 1

    # League insights
    for li in LEAGUE_INSIGHTS:
        cursor.execute(
            f"{insert_mode} INTO league_insights (league_name, key_stats, trends, betting_tips, season) VALUES (?,?,?,?,?)",
            (li["league_name"], li["key_stats"], li["trends"], li["betting_tips"], li["season"]),
        )
        if cursor.rowcount > 0:
            counts["league_insights"] += 1

    # FAQ
    for faq in FAQ:
        cursor.execute(
            f"{insert_mode} INTO faq (question, answer, category) VALUES (?,?,?)",
            (faq["question"], faq["answer"], faq["category"]),
        )
        if cursor.rowcount > 0:
            counts["faq"] += 1

    conn.commit()
    conn.close()
    return counts


def is_seeded() -> bool:
    """Return True if the knowledge base already contains seed data."""
    conn = _get_conn()
    count = conn.execute("SELECT COUNT(*) FROM betting_strategies").fetchone()[0]
    conn.close()
    return count >= len(STRATEGIES)


if __name__ == "__main__":
    print("Seeding knowledge base...")
    result = seed_knowledge_base()
    print(f"Inserted: {result}")
